"""
Portfolio simulator: daily bars, long-only, limit entries, hard stops.

Execution model (deliberately conservative):
- Signal at close t -> order for the open of t+1+delay (delay=1 is the "one bar late" test).
- Limit entry: if the open is above the limit, there's no fill (the trade is skipped).
- Fill = open x (1 + slippage). Exits = price x (1 - slippage).
- Stop: if the open gaps through the stop, the fill is at the open (worse than the stop).
  Otherwise, if the low touches the stop, the fill is at the stop. On the entry day the
  stop is also live (we assume the worst: hit).
- Exit signals and time exits fire at the close of t -> filled at the next open.
- Sizing: risk = equity x risk_per_trade; shares = risk / stop_dist, capped by
  max_position_pct of equity and available cash. No leverage, no shorts.
"""
import numpy as np
import pandas as pd


def _stack(prices, signals, calendar, delay):
    tick = list(signals.keys())
    N, T = len(tick), len(calendar)
    O = np.full((T, N), np.nan); H = O.copy(); L = O.copy(); C = O.copy()
    EF = np.zeros((T, N), bool); XS = np.zeros((T, N), bool)
    LIM = O.copy(); SD = O.copy(); PR = np.zeros((T, N)); MH = np.zeros(N, int)
    for j, t in enumerate(tick):
        px = prices[t].reindex(calendar)
        s = signals[t]
        # shift entry info forward along the ticker's OWN bars (1 + delay sessions)
        sh = s[["signal", "limit", "stop_dist", "priority"]].shift(1 + delay)
        sh = sh.reindex(calendar)
        O[:, j], H[:, j], L[:, j], C[:, j] = (px[c].values for c in ("open", "high", "low", "close"))
        EF[:, j] = sh["signal"].fillna(False).astype(bool).values
        LIM[:, j] = sh["limit"].values
        SD[:, j] = sh["stop_dist"].values
        PR[:, j] = sh["priority"].fillna(0).values
        XS[:, j] = s["exit_sig"].reindex(calendar).fillna(False).astype(bool).values
        MH[j] = int(s["max_hold"].iloc[0]) if len(s) else 10
    return tick, O, H, L, C, EF, XS, LIM, SD, PR, MH


def simulate(prices, signals, cfg, calendar, slip_mult=1.0, delay=0):
    slip = cfg["slippage_bps"] * slip_mult / 1e4
    cap0 = float(cfg["capital"])
    risk_frac = cfg["risk_per_trade"]
    max_pos = cfg["max_positions"]
    max_pct = cfg["max_position_pct"]

    tick, O, H, L, C, EF, XS, LIM, SD, PR, MH = _stack(prices, signals, calendar, delay)
    cash, equity_prev = cap0, cap0
    pos = {}                       # j -> dict
    trades, equity = [], np.empty(len(calendar))

    def close_pos(j, px, t, reason):
        nonlocal cash
        p = pos.pop(j)
        cash += p["sh"] * px
        trades.append({
            "ticker": tick[j], "entry_date": calendar[p["t0"]], "exit_date": calendar[t],
            "entry": p["px"], "exit": px, "shares": p["sh"], "stop_dist": p["sd"],
            "pnl": p["sh"] * (px - p["px"]), "R": (px - p["px"]) / p["sd"],
            "ret_equity": p["sh"] * (px - p["px"]) / p["eq0"],
            "held": p["held"], "reason": reason,
        })

    for t in range(len(calendar)):
        # 1) exits at/through the open, then intraday stops
        for j in list(pos):
            o = O[t, j]
            if np.isnan(o):
                continue
            p = pos[j]
            if p["pending"]:
                close_pos(j, o * (1 - slip), t, p["pending"])
            elif o <= p["stop"]:
                close_pos(j, o * (1 - slip), t, "stop_gap")
            elif L[t, j] <= p["stop"]:
                close_pos(j, p["stop"] * (1 - slip), t, "stop")

        # 2) entries (limit orders at the open), highest priority first
        cands = np.where(EF[t] & ~np.isnan(O[t]))[0]
        if len(cands) and len(pos) < max_pos:
            for j in cands[np.argsort(-PR[t, cands])]:
                if len(pos) >= max_pos or j in pos:
                    continue
                o, lim, sd = O[t, j], LIM[t, j], SD[t, j]
                if not (sd > 0) or np.isnan(lim) or o > lim:
                    continue
                px = o * (1 + slip)
                sh = int(min(equity_prev * risk_frac / sd,
                             equity_prev * max_pct / px, cash / px))
                if sh < 1:
                    continue
                cash -= sh * px
                pos[j] = {"px": px, "sd": sd, "stop": px - sd, "sh": sh, "t0": t,
                          "held": 0, "pending": None, "eq0": equity_prev, "last": px}
                if L[t, j] <= pos[j]["stop"]:  # stop hit on entry day (assume worst)
                    close_pos(j, pos[j]["stop"] * (1 - slip), t, "stop")

        # 3) end-of-day: update holding counters, queue exits for next open, mark to market
        mtm = 0.0
        for j, p in pos.items():
            c = C[t, j]
            if not np.isnan(c):
                p["last"] = c
                p["held"] += 1
                if XS[t, j]:
                    p["pending"] = "exit_signal"
                elif p["held"] >= MH[j]:
                    p["pending"] = "time"
            mtm += p["sh"] * p["last"]
        equity[t] = cash + mtm
        equity_prev = equity[t]

    for j in list(pos):  # close anything still open at the last mark
        close_pos(j, pos[j]["last"] * (1 - slip), len(calendar) - 1, "end_of_data")

    return pd.Series(equity, index=calendar), pd.DataFrame(trades)
