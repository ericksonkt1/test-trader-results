"""
The three candidate edges. Every function only uses data up to and including bar t
to produce a signal at the CLOSE of bar t. The engine enters at the NEXT bar's open
(or later, for the one-bar-late stress test). That separation is the lookahead guard.

Each strategy returns a DataFrame aligned to the price index with:
  signal      bool   enter long at the next open
  stop_dist   float  $ distance from entry to stop (ATR-based, known at t)
  limit       float  highest acceptable entry price (limit order); skip if the open is above
  exit_sig    bool   if holding, exit at the next open
  priority    float  ranks competing signals on the same day (higher first)
  max_hold    int    sessions before a time exit
"""
import numpy as np
import pandas as pd

from .data import reaction_days


# --------------------------------------------------------------------------- indicators
def atr(df, n=14):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(),
                    (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def rsi(close, n=2):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def liquid(df, cfg):
    """Point-in-time liquidity filter (uses only trailing data)."""
    adv = (df["close"] * df["volume"]).rolling(20).mean()
    u = cfg["universe"]
    return (df["close"] >= u.get("min_price", 5)) & (adv >= u.get("min_adv_usd", 10e6))


def _frame(df, signal, stop_dist, limit, exit_sig, priority, max_hold):
    return pd.DataFrame({
        "signal": signal.fillna(False).astype(bool),
        "stop_dist": stop_dist,
        "limit": limit,
        "exit_sig": exit_sig.fillna(False).astype(bool),
        "priority": priority.fillna(0.0),
        "max_hold": int(max_hold),
    }, index=df.index)


# --------------------------------------------------------------------------- 1. earnings drift
def earnings_drift(df, p, cfg, earn=None):
    """
    Post-earnings drift. Thesis: investors under-react to earnings surprises,
    so a strong, high-volume gap that HOLDS into the close keeps drifting for days.
    Other side: slow holders selling into strength / analysts slow to revise.
    Event: reaction day gaps up >= gap_min, closes above its open, volume >= vol_mult x 50d avg.
    With earnings_source='gap_proxy' any such gap counts (no earnings dates needed) —
    reported as a proxy, not true PEAD.
    """
    a = atr(df)
    avgv = df["volume"].rolling(50).mean().shift(1)
    gap = df["open"] / df["close"].shift(1) - 1
    held = df["close"] > df["open"]
    volx = df["volume"] / avgv
    base = (gap >= p["gap_min"]) & held & (volx >= p["vol_mult"]) & liquid(df, cfg)
    if cfg["strategies"]["earnings_drift"].get("earnings_source") == "gap_proxy":
        ev = base
    else:
        flag, surprise = reaction_days(earn, df.index)
        ev = base & flag & ~(surprise < 0)  # skip known negative surprises
    stop = p["stop_atr"] * a
    limit = df["close"] * (1 + p.get("limit_buffer", 0.01))
    exit_sig = df["close"] < df["close"].rolling(p.get("exit_low", 10)).min().shift(1)
    return _frame(df, ev, stop, limit, exit_sig, volx, p["max_hold"])


# --------------------------------------------------------------------------- 2. volume breakout
def volume_breakout(df, p, cfg, earn=None):
    """
    Breakout on expanded volume inside an established uptrend.
    Thesis: new highs on heavy volume = fresh demand absorbing overhead supply.
    Other side: holders who sell at "resistance" and short-term faders.
    """
    a = atr(df)
    sma50, sma200 = df["close"].rolling(50).mean(), df["close"].rolling(200).mean()
    avgv = df["volume"].rolling(50).mean().shift(1)
    prior_high = df["close"].rolling(p["lookback"]).max().shift(1)
    volx = df["volume"] / avgv
    sig = (df["close"] > prior_high) & (volx >= p["vol_mult"]) & \
          (df["close"] > sma200) & (sma50 > sma200) & liquid(df, cfg)
    stop = p["stop_atr"] * a
    limit = df["close"] * (1 + p.get("limit_buffer", 0.01))
    exit_sig = df["close"] < df["close"].rolling(p.get("exit_low", 10)).min().shift(1)
    return _frame(df, sig, stop, limit, exit_sig, volx, p["max_hold"])


# --------------------------------------------------------------------------- 3. pullback reversion
def pullback_reversion(df, p, cfg, earn=None):
    """
    Short-term mean reversion after an overreaction, only inside an uptrend.
    Thesis: sharp 2-3 day selloffs in healthy uptrends are liquidity-driven and revert.
    Other side: weak-hand sellers and stop-loss cascades.
    Entry: close > 200SMA and RSI(2) < rsi_max. Exit: close > 5SMA, or time stop.
    """
    a = atr(df)
    sma200, sma5 = df["close"].rolling(200).mean(), df["close"].rolling(5).mean()
    r = rsi(df["close"], 2)
    sig = (df["close"] > sma200) & (r < p["rsi_max"]) & liquid(df, cfg)
    stop = p["stop_atr"] * a
    limit = df["close"] * (1 + p.get("limit_buffer", 0.0))  # buy at or below signal close
    exit_sig = df["close"] > sma5
    return _frame(df, sig, stop, limit, exit_sig, -r, p["max_hold"])


STRATEGIES = {
    "earnings_drift": earnings_drift,
    "volume_breakout": volume_breakout,
    "pullback_reversion": pullback_reversion,
}

THESIS = {
    "earnings_drift": ("Strong post-earnings gaps that hold on heavy volume keep drifting "
                       "as the market under-reacts.",
                       "Slow-to-update holders and analysts; sellers taking quick profits."),
    "volume_breakout": ("New highs on 1.5x+ volume in an uptrend signal fresh demand.",
                        "Holders selling at 'resistance' and short-term faders."),
    "pullback_reversion": ("Sharp 2-day selloffs in healthy uptrends are forced/emotional "
                           "selling that reverts within days.",
                           "Panic sellers and stop-loss cascades."),
}


def describe_rules(name, p):
    if name == "earnings_drift":
        return (f"ENTRY: on the earnings reaction day, gap up >= {p['gap_min']:.0%}, close > open, "
                f"volume >= {p['vol_mult']}x 50-day avg -> buy-limit next open at <= signal close "
                f"+{p.get('limit_buffer', 0.01):.0%}. STOP: entry - {p['stop_atr']} x ATR(14). "
                f"EXIT: close below {p.get('exit_low', 10)}-day low (next open) or after "
                f"{p['max_hold']} sessions.")
    if name == "volume_breakout":
        return (f"ENTRY: close > prior {p['lookback']}-day high, volume >= {p['vol_mult']}x 50-day "
                f"avg, close > 200SMA, 50SMA > 200SMA -> buy-limit next open at <= signal close "
                f"+{p.get('limit_buffer', 0.01):.0%}. STOP: entry - {p['stop_atr']} x ATR(14). "
                f"EXIT: close below {p.get('exit_low', 10)}-day low (next open) or after "
                f"{p['max_hold']} sessions.")
    return (f"ENTRY: close > 200SMA and RSI(2) < {p['rsi_max']} -> buy-limit next open at <= "
            f"signal close. STOP: entry - {p['stop_atr']} x ATR(14). EXIT: close > 5SMA "
            f"(next open) or after {p['max_hold']} sessions.")
