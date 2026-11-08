"""
Performance statistics and the desk's 25-point scorecard.

Deflated Sharpe Ratio: Bailey & Lopez de Prado (2014). It asks how likely the observed
Sharpe is to be real after accounting for how many variants we tried (n_trials), the
variance of their Sharpes, and fat tails / skew in the returns.
"""
import numpy as np
import pandas as pd
from scipy.stats import kurtosis, norm, skew

EULER = 0.5772156649


def daily_returns(equity):
    return equity.pct_change().dropna()


def sharpe(ret, periods=252):
    ret = ret.dropna()
    if len(ret) < 20 or ret.std() == 0:
        return 0.0
    return float(ret.mean() / ret.std() * np.sqrt(periods))


def max_drawdown(equity):
    if len(equity) == 0:
        return 0.0
    peak = equity.cummax()
    return float((equity / peak - 1).min())


def deflated_sharpe(ret, sr_trials, n_trials):
    """
    ret: daily returns of the selected strategy (out of sample)
    sr_trials: per-period (non-annualized) Sharpes of ALL variants tried
    Returns the probability (0-1) that the true Sharpe is > 0 after deflation.
    """
    ret = ret.dropna()
    T = len(ret)
    if T < 30 or ret.std() == 0:
        return 0.0
    sr = ret.mean() / ret.std()
    var_sr = float(np.var(sr_trials, ddof=1)) if len(sr_trials) > 1 else 0.0
    n = max(int(n_trials), 2)
    sr0 = np.sqrt(var_sr) * ((1 - EULER) * norm.ppf(1 - 1 / n)
                             + EULER * norm.ppf(1 - 1 / (n * np.e)))
    g3, g4 = skew(ret), kurtosis(ret, fisher=False)
    denom = np.sqrt(max(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2, 1e-12))
    return float(norm.cdf((sr - sr0) * np.sqrt(T - 1) / denom))


def monte_carlo_dd(trade_rets, runs=1000, seed=42):
    """Resample trade returns (fraction of equity) with replacement -> drawdown distribution."""
    r = np.asarray(trade_rets, float)
    if len(r) < 5:
        return {"p50": None, "p95": None, "worst": None}
    rng = np.random.default_rng(seed)
    dds = np.empty(runs)
    for k in range(runs):
        path = np.cumprod(1 + rng.choice(r, size=len(r), replace=True))
        path = np.concatenate([[1.0], path])
        dds[k] = (path / np.maximum.accumulate(path) - 1).min()
    return {"p50": float(np.percentile(dds, 50)), "p95": float(np.percentile(dds, 5)),
            "worst": float(dds.min())}


def trade_summary(trades):
    if trades is None or len(trades) == 0:
        return {"n": 0, "win_rate": 0.0, "avg_R": 0.0, "expectancy_pct": 0.0,
                "profit_factor": 0.0, "avg_hold": 0.0}
    wins, losses = trades.loc[trades.pnl > 0, "pnl"].sum(), -trades.loc[trades.pnl < 0, "pnl"].sum()
    return {
        "n": int(len(trades)),
        "win_rate": float((trades.pnl > 0).mean()),
        "avg_R": float(trades.R.mean()),
        "expectancy_pct": float(trades.ret_equity.mean()),
        "profit_factor": float(wins / losses) if losses > 0 else float("inf"),
        "avg_hold": float(trades.held.mean()),
    }


def period_stats(equity, trades, start, end):
    e = equity[(equity.index >= start) & (equity.index <= end)]
    tr = trades[(trades.entry_date >= start) & (trades.entry_date <= end)] if len(trades) else trades
    ret = daily_returns(e)
    return {
        "start": str(pd.Timestamp(start).date()), "end": str(pd.Timestamp(end).date()),
        "total_return": float(e.iloc[-1] / e.iloc[0] - 1) if len(e) > 1 else 0.0,
        "sharpe": sharpe(ret), "max_dd": max_drawdown(e / e.iloc[0]) if len(e) else 0.0,
        **trade_summary(tr),
    }


# --------------------------------------------------------------------------- scorecard
def _bucket(x, edges):
    """edges ascending; returns 1..5."""
    return int(1 + sum(x > e for e in edges))


def scorecard(oos_sharpe, dsr, oos_maxdd, oos_trades, oos_avg_R):
    s = {
        "oos_sharpe": _bucket(oos_sharpe, [0.0, 0.5, 1.0, 1.5]),
        "deflated_sharpe": _bucket(dsr, [0.5, 0.8, 0.9, 0.95]),
        # smaller drawdown = higher score
        "max_drawdown": _bucket(-abs(oos_maxdd), [-0.30, -0.20, -0.15, -0.10]),
        "trade_count": _bucket(oos_trades, [29, 60, 100, 200]),   # <30 trades scores 1
        "edge_after_costs": _bucket(oos_avg_R, [0.0, 0.1, 0.2, 0.3]),
    }
    s["total"] = sum(s.values())
    return s
