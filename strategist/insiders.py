"""
Insider purchases from the SEC's free Insider Transactions Data Sets (Forms 3/4/5, quarterly ZIPs).

Point-in-time rule: a purchase is only "known" on its FILING_DATE (Form 4 is due within 2 business
days of the trade). Strategies signal at the close of the filing date and the engine enters at the
next open, so nothing is used before the public could see it.

Kept: Form 4 (not amendments), transaction code P (open-market purchase), acquired, shares and
price > 0, filed by a Director or Officer (pure 10% owners / funds are dropped).
Tickers: issuer CIK mapped to today's ticker via SEC company_tickers.json (handles ticker changes),
falling back to the symbol as filed.

LIMIT: SEC posts these quarterly, so the current, not-yet-posted quarter is missing. Live trading
would need the daily EDGAR Form 4 feed.
"""
import io
import logging
import os
import time
import zipfile
from datetime import datetime

import numpy as np
import pandas as pd
import requests

log = logging.getLogger("strategist.insiders")

# SEC asks automated clients to identify themselves. Set SEC_USER_AGENT (repo variable) to override.
UA = os.environ.get("SEC_USER_AGENT") or "TestTrader research strategist-bot@users.noreply.github.com"
HEADERS = {"User-Agent": UA, "Accept-Encoding": "gzip, deflate"}
BASES = [
    "https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/",
    "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/",
]


def _quarters(start_year):
    now = datetime.utcnow()
    for y in range(start_year, now.year + 1):
        for q in range(1, 5):
            if (y, q) <= (now.year, (now.month - 1) // 3 + 1):
                yield y, q


def _download(name):
    for base in BASES:
        try:
            r = requests.get(base + name, headers=HEADERS, timeout=120)
        except Exception as e:  # noqa: BLE001
            log.warning("SEC %s: %s", name, e)
            continue
        if r.status_code == 200 and r.content[:2] == b"PK":
            return r.content
        log.warning("SEC %s%s -> HTTP %s, %d bytes, starts %r", base, name, r.status_code,
                    len(r.content), r.content[:80])
        time.sleep(0.5)
    return None


def _read(z, fname, cols):
    member = next(m for m in z.namelist() if m.upper().endswith(fname))
    with z.open(member) as f:
        return pd.read_csv(f, sep="\t", usecols=lambda c: c in cols, dtype=str,
                           quoting=3, on_bad_lines="skip", encoding="latin-1")


def _parse(content):
    z = zipfile.ZipFile(io.BytesIO(content))
    sub = _read(z, "SUBMISSION.TSV", {"ACCESSION_NUMBER", "FILING_DATE", "DOCUMENT_TYPE",
                                      "ISSUERCIK", "ISSUERTRADINGSYMBOL"})
    sub = sub[sub["DOCUMENT_TYPE"].str.strip() == "4"]
    own = _read(z, "REPORTINGOWNER.TSV", {"ACCESSION_NUMBER", "RPTOWNERCIK",
                                          "RPTOWNER_RELATIONSHIP"})
    rel = own["RPTOWNER_RELATIONSHIP"].fillna("").str.lower()
    own = own[rel.str.contains("director") | rel.str.contains("officer")]
    own = own.drop_duplicates("ACCESSION_NUMBER")  # one owner per filing is enough to count
    tx = _read(z, "NONDERIV_TRANS.TSV", {"ACCESSION_NUMBER", "TRANS_CODE", "TRANS_SHARES",
                                         "TRANS_PRICEPERSHARE", "TRANS_ACQUIRED_DISP_CD"})
    tx = tx[(tx["TRANS_CODE"].str.strip() == "P") & (tx["TRANS_ACQUIRED_DISP_CD"].str.strip() == "A")]
    tx = tx.assign(shares=pd.to_numeric(tx["TRANS_SHARES"], errors="coerce"),
                   price=pd.to_numeric(tx["TRANS_PRICEPERSHARE"], errors="coerce"))
    tx = tx[(tx.shares > 0) & (tx.price > 0)]
    tx["value"] = tx.shares * tx.price
    val = tx.groupby("ACCESSION_NUMBER")["value"].sum().rename("value").reset_index()
    df = sub.merge(own, on="ACCESSION_NUMBER").merge(val, on="ACCESSION_NUMBER")
    df["filing_date"] = pd.to_datetime(df["FILING_DATE"], format="mixed", dayfirst=True, errors="coerce")
    return pd.DataFrame({"filing_date": df["filing_date"],
                         "cik": pd.to_numeric(df["ISSUERCIK"], errors="coerce"),
                         "symbol": df["ISSUERTRADINGSYMBOL"].fillna("").str.strip().str.upper(),
                         "owner": df["RPTOWNERCIK"].str.strip(),
                         "value": df["value"]}).dropna(subset=["filing_date", "cik"])


def _cik_map(idir):
    p = os.path.join(idir, "company_tickers.json")
    try:
        r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=HEADERS, timeout=60)
        r.raise_for_status()
        open(p, "wb").write(r.content)
    except Exception as e:  # noqa: BLE001
        log.warning("company_tickers.json refresh failed (%s); using cached copy", e)
    if not os.path.exists(p):
        return {}
    js = pd.read_json(p, orient="index")
    return {int(c): str(t).upper().replace(".", "-") for c, t in zip(js["cik_str"], js["ticker"])}


def load_insiders(tickers, cfg):
    """Returns {ticker: DataFrame[filing_date, owner, value]} of Director/Officer open-market buys."""
    idir = os.path.join(cfg["data_dir"], "insiders")
    os.makedirs(idir, exist_ok=True)
    ua = os.environ.get("SEC_USER_AGENT") or cfg.get("sec_user_agent")
    if ua:
        HEADERS["User-Agent"] = ua
    start_year = int(cfg["start"][:4])
    frames, got, missing = [], 0, []
    qs = list(_quarters(start_year))
    for k, (y, q) in enumerate(qs):
        name = f"{y}q{q}_form345.zip"
        cache = os.path.join(idir, f"{y}q{q}.csv")
        recent = k >= len(qs) - 2  # newest quarters may be posted/revised after first try
        if os.path.exists(cache) and os.path.getsize(cache) <= 2:
            os.remove(cache)  # an earlier failed download; try again
        if os.path.exists(cache) and not (recent and time.time() - os.path.getmtime(cache) > 7 * 86400):
            frames.append(pd.read_csv(cache, parse_dates=["filing_date"]))
            got += 1
            continue
        content = _download(name)
        time.sleep(0.3)
        if content is None:
            missing.append(name)
            if len(missing) >= 3 and got == 0:
                log.warning("Insiders: first 3 quarters failed, SEC unreachable; skipping the rest")
                missing += [f"{yy}q{qq}_form345.zip" for yy, qq in qs[k + 1:]]
                break
            continue
        try:
            df = _parse(content)
        except Exception as e:  # noqa: BLE001  (schema change etc. must not kill the nightly run)
            log.warning("Insiders: could not parse %s (%s)", name, e)
            missing.append(name)
            continue
        df.to_csv(cache, index=False)
        frames.append(df)
        got += 1
        log.info("Insiders: %s -> %d director/officer purchase filings", name, len(df))
    log.info("Insider quarters loaded: %d, not available: %s", got, ", ".join(missing) or "none")
    if not frames:
        return {}, {"quarters": 0, "missing": missing}
    allf = pd.concat(frames, ignore_index=True)
    cmap = _cik_map(idir)
    allf["ticker"] = [cmap.get(int(c), s.replace(".", "-")) for c, s in zip(allf["cik"], allf["symbol"])]
    want = set(tickers)
    allf = allf[allf["ticker"].isin(want)]
    out = {t: g[["filing_date", "owner", "value"]].sort_values("filing_date").reset_index(drop=True)
           for t, g in allf.groupby("ticker")}
    last = allf["filing_date"].max()
    log.info("Insider purchases mapped to %d universe tickers; latest filing %s", len(out), last)
    return out, {"quarters": got, "missing": missing, "tickers": len(out),
                 "last_filing": str(pd.Timestamp(last).date()) if pd.notna(last) else None}


def synthetic_insiders(prices, seed=11):
    """Random insider buys for CODE TESTING ONLY."""
    rng = np.random.default_rng(seed)
    out = {}
    for t, df in prices.items():
        if not t.startswith("SYN"):
            continue
        n = rng.poisson(20)
        days = rng.choice(df.index, size=n)
        out[t] = pd.DataFrame({"filing_date": pd.to_datetime(days),
                               "owner": rng.integers(1, 6, n).astype(str),
                               "value": rng.lognormal(11.5, 1.0, n)}).sort_values("filing_date")
    return out
