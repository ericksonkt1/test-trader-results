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


def load_universe(cfg):
    data_dir = cfg["data_dir"]
    path = os.path.join(data_dir, "universe.csv")
    ucfg = cfg["universe"]
    exclude = {t.upper() for t in ucfg.get("exclude", [])}

    if os.path.exists(path) and not ucfg.get("refresh_from_ishares", False):
        tickers = pd.read_csv(path)["ticker"].astype(str).str.upper().tolist()
    else:
        tickers = set()
        for fund in ucfg.get("sources", ["IJH", "IJR"]):
            try:
                r = requests.get(ISHARES_URLS[fund], headers=HEADERS, timeout=30)
                r.raise_for_status()
                tickers |= set(_parse_ishares_csv(r.text))
                log.info("Universe: %s holdings loaded", fund)
            except Exception as e:  # noqa: BLE001
                log.warning("Could not fetch %s holdings (%s). Put a universe.csv in %s.",
                            fund, e, data_dir)
        tickers = sorted(tickers)
        if not tickers:
            raise SystemExit("No universe. Create /data/universe.csv with a 'ticker' column.")
        pd.DataFrame({"ticker": tickers}).to_csv(path, index=False)

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

    edir = os.path.join(cfg["data_dir"], "earnings")
    os.makedirs(edir, exist_ok=True)
    out = {}
    for n, t in enumerate(tickers):
        p = os.path.join(edir, f"{t}.csv")
        if not _fresh(p, 24 * 7):
            try:
                ed = yf.Ticker(t).get_earnings_dates(limit=40)
                if ed is not None and len(ed):
                    ed = ed.reset_index()
                    ed.columns = [str(c) for c in ed.columns]
                    ed.to_csv(p, index=False)
                else:
                    pd.DataFrame().to_csv(p, index=False)
            except Exception:  # noqa: BLE001
                pd.DataFrame().to_csv(p, index=False)
            time.sleep(0.4)
            if n % 100 == 0:
                log.info("Earnings dates: %d/%d", n, len(tickers))
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
