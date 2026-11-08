"""
Data layer for the Strategist.

- Universe: current S&P MidCap 400 (IJH) + SmallCap 600 (IJR) holdings from iShares,
  or your own universe.csv in the data folder (one column: ticker).
  WARNING: today's constituents = survivorship bias. Delisted losers are missing,
  which flatters backtests. The report says so every night.
- Prices: daily OHLCV from Yahoo via yfinance (split + dividend adjusted), cached as CSV.
- Earnings dates: yfinance, cached weekly. Used for the earnings-drift strategy and
  for the earnings blackout on the other strategies (scheduled dates are known in
  advance, so using them is not lookahead).
"""
import io
import logging
import os
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests

log = logging.getLogger("strategist.data")

ISHARES_URLS = {
    "IJH": "https://www.ishares.com/us/products/239763/ishares-core-sp-midcap-etf/"
           "1467271812596.ajax?fileType=csv&fileName=IJH_holdings&dataType=fund",
    "IJR": "https://www.ishares.com/us/products/239774/ishares-core-sp-smallcap-etf/"
           "1467271812596.ajax?fileType=csv&fileName=IJR_holdings&dataType=fund",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (strategist-backtester)"}


# --------------------------------------------------------------------------- universe
def _parse_ishares_csv(text):
    """iShares CSVs have ~9 preamble lines before the 'Ticker,' header row."""
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("Ticker,"))
    df = pd.read_csv(io.StringIO("\n".join(lines[start:])), on_bad_lines="skip")
    df = df[df.get("Asset Class", "Equity") == "Equity"]
    tickers = df["Ticker"].dropna().astype(str).str.strip()
    # Yahoo uses '-' for share classes (BRK.B -> BRK-B)
    return sorted({t.replace(".", "-") for t in tickers if t and t != "-"})


WIKI_PAGES = {"IJH": "List_of_S%26P_400_companies", "IJR": "List_of_S%26P_600_companies"}
WIKI_HEADERS = {"User-Agent": "Mozilla/5.0 (test-trader strategist; research backtest)"}


def _wikipedia_universe(funds):
    """Current S&P 400 / 600 members from Wikipedia (same indexes IJH / IJR track)."""
    tickers = set()
    for fund in funds:
        page = WIKI_PAGES[fund]
        r = requests.get("https://en.wikipedia.org/wiki/" + page, headers=WIKI_HEADERS, timeout=30)
        r.raise_for_status()
        found = None
        for df in pd.read_html(io.StringIO(r.text)):
            col = next((c for c in df.columns
                        if str(c).strip() in ("Symbol", "Ticker symbol", "Ticker")), None)
            if col is not None:
                found = {str(x).strip().replace(".", "-") for x in df[col]}
                break
        if not found:
            raise RuntimeError(f"no ticker table on {page}")
        log.info("Universe: %d tickers from Wikipedia %s", len(found), page)
        tickers |= found
    tickers = {t for t in tickers if t.replace("-", "").isalpha()}
    if len(tickers) < 500:
        raise RuntimeError(f"only {len(tickers)} tickers parsed; refusing to use it")
    return sorted(tickers)


def _ishares_universe(funds, data_dir):
    tickers = set()
    for fund in funds:
        try:
            r = requests.get(ISHARES_URLS[fund], headers=HEADERS, timeout=30)
            r.raise_for_status()
            tickers |= set(_parse_ishares_csv(r.text))
            log.info("Universe: %s holdings loaded", fund)
        except Exception as e:  # noqa: BLE001
            log.warning("Could not fetch %s holdings (%s). Put a universe.csv in %s.",
                        fund, e, data_dir)
    return sorted(tickers)


def load_universe(cfg):
    """
    universe.refresh: "wikipedia" (default) | "ishares" | "never".
    A refresh that fails falls back to the last good universe.csv.
    """
    data_dir = cfg["data_dir"]
    path = os.path.join(data_dir, "universe.csv")
    ucfg = cfg["universe"]
    exclude = {t.upper() for t in ucfg.get("exclude", [])}
    funds = ucfg.get("sources", ["IJH", "IJR"])
    mode = ucfg.get("refresh", "ishares" if ucfg.get("refresh_from_ishares") else "wikipedia")

    tickers = []
    if mode == "wikipedia":
        try:
            tickers = _wikipedia_universe(funds)
        except Exception as e:  # noqa: BLE001
            log.warning("Wikipedia universe refresh failed (%s); using last universe.csv", e)
    elif mode == "ishares":
        tickers = _ishares_universe(funds, data_dir)
    if tickers:
        pd.DataFrame({"ticker": tickers}).to_csv(path, index=False)
    elif os.path.exists(path):
        tickers = pd.read_csv(path)["ticker"].astype(str).str.upper().tolist()
    else:
        raise SystemExit(f"No universe. Create {path} with a 'ticker' column.")

    tickers = [t for t in tickers if t not in exclude]
    log.info("Universe size after exclusions: %d", len(tickers))
    return tickers


# --------------------------------------------------------------------------- prices
def _fresh(path, max_age_hours):
    return os.path.exists(path) and \
        (time.time() - os.path.getmtime(path)) < max_age_hours * 3600


def load_prices(tickers, cfg, extra=("IWM", "SPY")):
    """Returns {ticker: DataFrame[open, high, low, close, volume]} indexed by date."""
    import yfinance as yf

    pdir = os.path.join(cfg["data_dir"], "prices")
    os.makedirs(pdir, exist_ok=True)
    all_t = list(dict.fromkeys(list(tickers) + list(extra)))
    stale = [t for t in all_t if not _fresh(os.path.join(pdir, f"{t}.csv"), 18)]
    log.info("Prices: %d cached, %d to download", len(all_t) - len(stale), len(stale))

    for i in range(0, len(stale), 100):
        chunk = stale[i:i + 100]
        try:
            raw = yf.download(chunk, start=cfg["start"], auto_adjust=True,
                              group_by="ticker", threads=True, progress=False)
        except Exception as e:  # noqa: BLE001
            log.warning("Download failed for chunk %d: %s", i, e)
            continue
        for t in chunk:
            try:
                df = raw[t] if isinstance(raw.columns, pd.MultiIndex) else raw
                df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
                df = df.dropna()
                if len(df) > 250:
                    df.to_csv(os.path.join(pdir, f"{t}.csv"))
            except Exception:  # noqa: BLE001
                pass
        time.sleep(2)  # be polite to Yahoo

    out = {}
    for t in all_t:
        p = os.path.join(pdir, f"{t}.csv")
        if os.path.exists(p):
            df = pd.read_csv(p, index_col=0, parse_dates=True)
            df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
            out[t] = df.sort_index()
    log.info("Prices loaded for %d tickers", len(out))
    return out


# --------------------------------------------------------------------------- earnings
def load_earnings(tickers, cfg):
    """
    Returns {ticker: DataFrame[reaction_date, surprise_pct]}.
    reaction_date = first session that trades on the news:
      announced before 09:30 ET -> same day; otherwise -> next trading day.
    """
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor

    edir = os.path.join(cfg["data_dir"], "earnings")
    os.makedirs(edir, exist_ok=True)
    ecfg = cfg.get("earnings", {})
    max_age_h = 24 * ecfg.get("refresh_days", 7)
    cap = ecfg.get("max_refresh_per_run", 250)
    workers = ecfg.get("workers", 2)

    def fetch(t, pause=0.3):
        """True = data saved; False = Yahoo has none (empty file saved); None = error, retry."""
        p = os.path.join(edir, f"{t}.csv")
        time.sleep(pause)
        try:
            ed = yf.Ticker(t).get_earnings_dates(limit=40)
        except Exception:  # noqa: BLE001
            return None  # no file written -> counted as missing and retried
        if ed is not None and len(ed):
            ed = ed.reset_index()
            ed.columns = [str(c) for c in ed.columns]
            ed.to_csv(p, index=False)
            return True
        if not os.path.exists(p):
            pd.DataFrame().to_csv(p, index=False)
        return False

    # Missing or empty files are always fetched. Stale ones are refreshed oldest-first, capped per run,
    # so the weekly refresh is spread over several nights instead of one 2-hour run.
    def _have(t):  # an empty file (no dates last time) is re-checked every run
        p = os.path.join(edir, f"{t}.csv")
        return os.path.exists(p) and os.path.getsize(p) > 2

    missing = [t for t in tickers if not _have(t)]
    miss_set = set(missing)
    stale = sorted((t for t in tickers if t not in miss_set
                    and not _fresh(os.path.join(edir, f"{t}.csv"), max_age_h)),
                   key=lambda t: os.path.getmtime(os.path.join(edir, f"{t}.csv")))
    todo = missing + stale[:max(0, cap - len(missing))]
    log.info("Earnings dates: %d missing, %d stale, fetching %d", len(missing), len(stale), len(todo))
    t0 = time.time()
    res = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for n, (t, r) in enumerate(zip(todo, ex.map(fetch, todo)), 1):
            res[t] = r
            if n % 100 == 0:
                log.info("Earnings dates: %d/%d fetched (%.0fs)", n, len(todo), time.time() - t0)
    # Second pass: errors and empty answers (often throttling) retried one at a time, slower.
    retry = [t for t, r in res.items() if not r]
    if retry:
        log.info("Earnings: retrying %d tickers slowly", len(retry))
        time.sleep(30)
        for t in retry:
            r = fetch(t, pause=1.0)
            if r is not None:
                res[t] = r
    if todo:
        vals = list(res.values())
        log.info("Earnings fetch done in %.0fs: %d with data, %d none on Yahoo, %d errors "
                 "(errors retried next run)", time.time() - t0, vals.count(True),
                 vals.count(False), vals.count(None))

    out = {}
    for t in tickers:
        p = os.path.join(edir, f"{t}.csv")
        if not os.path.exists(p):
            continue
        try:
            ed = pd.read_csv(p)
        except pd.errors.EmptyDataError:
            continue
        if ed.empty:
            continue
        dcol = ed.columns[0]
        ts = pd.to_datetime(ed[dcol], utc=True, errors="coerce").dt.tz_convert("America/New_York")
        before_open = (ts.dt.hour * 60 + ts.dt.minute) < 9 * 60 + 30
        day = ts.dt.tz_localize(None).dt.normalize()
        surprise = ed.get("Surprise(%)", pd.Series(np.nan, index=ed.index))
        out[t] = pd.DataFrame({"announce_day": day, "before_open": before_open,
                               "surprise_pct": pd.to_numeric(surprise, errors="coerce")}).dropna(
            subset=["announce_day"])
    log.info("Earnings dates available for %d tickers", len(out))
    return out


def reaction_days(earn_df, index):
    """Map announcement timestamps onto trading-day index -> Series(bool), Series(surprise)."""
    flag = pd.Series(False, index=index)
    surprise = pd.Series(np.nan, index=index)
    if earn_df is None or earn_df.empty:
        return flag, surprise
    for _, r in earn_df.iterrows():
        d = r["announce_day"]
        pos = index.searchsorted(d)
        if pos < len(index) and index[pos] == d and not r["before_open"]:
            pos += 1  # after-close report -> next session reacts
        if pos < len(index):
            flag.iloc[pos] = True
            surprise.iloc[pos] = r["surprise_pct"]
    return flag, surprise


def upcoming_earnings_mask(earn_df, index, days_ahead):
    """True on days that are within `days_ahead` sessions BEFORE a scheduled report."""
    mask = pd.Series(False, index=index)
    if earn_df is None or earn_df.empty or days_ahead <= 0:
        return mask
    flag, _ = reaction_days(earn_df, index)
    arr = flag.values
    m = np.zeros(len(index), dtype=bool)
    for i in np.where(arr)[0]:
        m[max(0, i - days_ahead):i + 1] = True
    return pd.Series(m, index=index)


# --------------------------------------------------------------------------- synthetic
def synthetic_prices(n_tickers=60, start="2018-01-01", end=None, seed=7):
    """Random-walk OHLCV for CODE TESTING ONLY. Never use for decisions."""
    rng = np.random.default_rng(seed)
    end = end or datetime.utcnow().strftime("%Y-%m-%d")
    idx = pd.bdate_range(start, end)
    out = {}
    for k in range(n_tickers + 2):
        t = "IWM" if k == n_tickers else "SPY" if k == n_tickers + 1 else f"SYN{k:03d}"
        r = rng.normal(0.0003, 0.022, len(idx))
        close = 30 * np.exp(np.cumsum(r))
        openp = close * np.exp(rng.normal(0, 0.008, len(idx)))
        gaps = rng.random(len(idx)) < 0.01
        openp[gaps] *= np.exp(rng.normal(0.04, 0.05, gaps.sum()))
        high = np.maximum(openp, close) * (1 + np.abs(rng.normal(0, 0.01, len(idx))))
        low = np.minimum(openp, close) * (1 - np.abs(rng.normal(0, 0.01, len(idx))))
        vol = rng.lognormal(13.5, 0.5, len(idx))
        vol[gaps] *= 4
        out[t] = pd.DataFrame({"open": openp, "high": high, "low": low,
                               "close": close, "volume": vol}, index=idx)
    return out
