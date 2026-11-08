"""
Nightly Strategist run.

  python -m strategist.run --config /app/config.json            # real data
  python -m strategist.run --config /app/config.json --synthetic  # code test only

Pipeline:
 1. Universe + prices (+ earnings dates)
 2. Every parameter variant of every strategy -> full-history portfolio simulation
 3. Pick each strategy's best variant on IN-SAMPLE Sharpe only
 4. Judge it on OUT-OF-SAMPLE data: Sharpe, deflated Sharpe (counting every variant tried),
    drawdown, trade count, average R after costs -> 25-point scorecard
 5. Walk-forward, 1,000-run Monte Carlo drawdown, double slippage + one bar late,
    2020 and 2022, and the market regime that breaks it
 6. Write results/<date>/report.md + report.json + oos_trades_<strategy>.csv
"""
import argparse
import itertools
import json
import logging
import os
import shutil
import time
from datetime import datetime

import numpy as np
import pandas as pd

from . import data as D
from . import insiders as INS
from . import stats as S
from .engine import simulate
from .strategies import STRATEGIES, THESIS, describe_rules

log = logging.getLogger("strategist")


def expand_grid(grid):
    keys = list(grid)
    return [dict(zip(keys, vals)) for vals in itertools.product(*(grid[k] for k in keys))]


def build_signals(name, params, prices, earnings, cfg, universe, insiders=None):
    fn, out = STRATEGIES[name], {}
    side = insiders if name == "insider_cluster" else earnings
    bdays = cfg.get("earnings_blackout_days", 3)
    for t in universe:
        df = prices.get(t)
        if df is None or len(df) < 260:
            continue
        s = fn(df, params, cfg, (side or {}).get(t))
        if name != "earnings_drift" and t in earnings:
            # Desk Rule: never launch a position into that stock's earnings
            s["signal"] &= ~D.upcoming_earnings_mask(earnings[t], df.index, bdays).values
        out[t] = s
    return out


def regime_table(trades, bench):
    """Average R by small-cap regime at entry (known the day before entry)."""
    if trades is None or len(trades) == 0:
        return {}, None
    c = bench["close"]
    trend = (c > c.rolling(200).mean()).shift(1)
    vol = c.pct_change().rolling(20).std().shift(1)
    hi_vol = vol > vol.rolling(252).median()
    rows = []
    for _, tr in trades.iterrows():
        d = tr.entry_date
        if d not in trend.index or pd.isna(trend.get(d)):
            continue
        rows.append({"R": tr.R,
                     "regime": ("uptrend" if trend[d] else "downtrend") + "/"
                               + ("high-vol" if hi_vol.get(d, False) else "low-vol")})
    if not rows:
        return {}, None
    df = pd.DataFrame(rows).groupby("regime")["R"].agg(["mean", "count"])
    table = {k: {"avg_R": float(v["mean"]), "trades": int(v["count"])} for k, v in df.iterrows()}
    eligible = {k: v for k, v in table.items() if v["trades"] >= 5}
    worst = min(eligible, key=lambda k: eligible[k]["avg_R"]) if eligible else None
    return table, worst


def walk_forward(variant_returns, calendar, train, test, warmup):
    """Re-select the best variant on each train window, apply it to the next test window."""
    pieces, folds = [], []
    i = warmup
    while i + train + test <= len(calendar):
        tr0, tr1, te1 = calendar[i], calendar[i + train - 1], calendar[i + train + test - 1]
        best = max(variant_returns, key=lambda k: S.sharpe(variant_returns[k][tr0:tr1]))
        seg = variant_returns[best][calendar[i + train]:te1]
        pieces.append(seg)
        folds.append(float((1 + seg).prod() - 1))
        i += test
    if not pieces:
        return {"folds": 0}
    wf = pd.concat(pieces)
    return {"folds": len(folds), "sharpe": S.sharpe(wf), "total_return": float((1 + wf).prod() - 1),
            "pct_positive_folds": float(np.mean([f > 0 for f in folds]))}


def why_it_could_fail(r, cfg):
    w = ["Survivorship bias: the universe is today's index members, so delisted losers are "
         "missing and results are flattered.",
         "Float and market-cap filters aren't applied point in time in the backtest. The live "
         "Scout applies them from Robinhood fundamentals."]
    b, st = r["oos"], r["stress"]
    if st["avg_R"] <= 0:
        w.append("Edge disappears with double slippage + one bar late, so it's too fill-sensitive.")
    elif b["avg_R"] > 0 and st["avg_R"] < 0.5 * b["avg_R"]:
        w.append("Edge more than halves with worse fills/timing.")
    for yr in ("2020", "2022"):
        y = r["regimes_years"].get(yr)
        if y and (y["total_return"] < 0 or y["max_dd"] < -0.20):
            w.append(f"{yr}: return {y['total_return']:+.1%}, max drawdown {y['max_dd']:.1%}.")
    if r["walk_forward"].get("pct_positive_folds", 1) < 0.6:
        w.append("Fewer than 60% of walk-forward windows were profitable.")
    if b["n"] < 60:
        w.append(f"Only {b['n']} out-of-sample trades, so the estimate is noisy.")
    if r["deflated_sharpe"] < 0.95:
        w.append(f"Deflated Sharpe {r['deflated_sharpe']:.2f} < 0.95 after counting "
                 f"{r['n_trials']} variants tried, so it could be luck.")
    if r["breaks_in"]:
        w.append(f"Weakest regime: {r['breaks_in']} (avg R "
                 f"{r['regime_table'][r['breaks_in']]['avg_R']:+.2f}).")
    return w


def fmt_pct(x):
    return "n/a" if x is None else f"{x:+.1%}"


def write_report(results, meta, out_dir):
    L = []
    if meta["synthetic"]:
        L += ["> **SYNTHETIC DATA. CODE TEST ONLY. These numbers mean nothing.**", ""]
    L += [f"# Strategist report — {meta['run_date']}", "",
          f"- Data: {meta['source']}, {meta['start']} → {meta['end']}, "
          f"{meta['universe_n']} tickers with usable history, earnings dates for "
          f"{meta.get('earnings_n', 0)}",
          f"- Insider data (SEC Form 4 data sets): {json.dumps(meta.get('insiders', {}))}",
          f"- In-sample: {meta['is_start']} → {meta['is_end']} · Out-of-sample: "
          f"{meta['oos_start']} → {meta['end']}",
          f"- Variants tested tonight (counted for deflated Sharpe): {meta['n_trials']}",
          f"- Costs: {meta['slippage_bps']} bps slippage per side, $0 commission · "
          f"Capital ${meta['capital']:,.0f} · risk {meta['risk']:.1%}/trade",
          f"- Pass bar: score ≥ {meta['min_score']}/25, ≥ {meta['min_trades']} OOS trades, "
          "positive OOS expectancy, positive under stress", "",
          "## Ranking (by out-of-sample strength)", "",
          "| # | Strategy | Score | OOS Sharpe | DSR | OOS trades | Avg R | Verdict |",
          "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(results, 1):
        L.append(f"| {i} | {r['name']} | {r['score']['total']}/25 | {r['oos']['sharpe']:.2f} | "
                 f"{r['deflated_sharpe']:.2f} | {r['oos']['n']} | {r['oos']['avg_R']:+.2f} | "
                 f"{'PASS' if r['passed'] else 'FAIL'} |")
    for r in results:
        i_, o, st = r["is"], r["oos"], r["stress"]
        mc, wf = r["monte_carlo"], r["walk_forward"]
        L += ["", f"## {r['name']} — {'PASS' if r['passed'] else 'FAIL'} "
                  f"({r['score']['total']}/25)", "",
              f"**Thesis:** {r['thesis']}", f"**Who's on the other side:** {r['other_side']}", "",
              f"**Rules:** {r['rules']}", "",
              f"**Sizing:** shares = (equity × {meta['risk']:.0%}) ÷ stop distance "
              f"({r['params']['stop_atr']} × ATR14), capped at "
              f"{meta['max_pct']:.0%} of equity and available cash. Max "
              f"{meta['max_pos']} open positions.", "",
              f"**Chosen variant (best in-sample):** `{json.dumps(r['params'])}`", "",
              "| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |",
              "|---|---|---|---|",
              f"| Total return | {fmt_pct(i_['total_return'])} | {fmt_pct(o['total_return'])} | "
              f"{fmt_pct(st['total_return'])} |",
              f"| Sharpe | {i_['sharpe']:.2f} | {o['sharpe']:.2f} | {st['sharpe']:.2f} |",
              f"| Max drawdown | {i_['max_dd']:.1%} | {o['max_dd']:.1%} | {st['max_dd']:.1%} |",
              f"| Trades | {i_['n']} | {o['n']} | {st['n']} |",
              f"| Win rate | {i_['win_rate']:.0%} | {o['win_rate']:.0%} | {st['win_rate']:.0%} |",
              f"| Avg R (after costs) | {i_['avg_R']:+.2f} | {o['avg_R']:+.2f} | {st['avg_R']:+.2f} |",
              f"| Profit factor | {i_['profit_factor']:.2f} | {o['profit_factor']:.2f} | "
              f"{st['profit_factor']:.2f} |", "",
              f"**Walk-forward:** {wf.get('folds', 0)} windows, Sharpe {wf.get('sharpe', 0):.2f}, "
              f"return {fmt_pct(wf.get('total_return'))}, "
              f"{wf.get('pct_positive_folds', 0):.0%} of windows profitable.",
              f"**Monte Carlo (1,000 resamples of OOS trades):** median drawdown "
              f"{fmt_pct(mc['p50'])}, 95th-percentile {fmt_pct(mc['p95'])}, worst {fmt_pct(mc['worst'])}.",
              f"**Deflated Sharpe:** {r['deflated_sharpe']:.2f} probability the edge is real "
              f"after {r['n_trials']} trials."]
        for yr in ("2020", "2022"):
            y = r["regimes_years"].get(yr)
            if y:
                L.append(f"**{yr}:** return {fmt_pct(y['total_return'])}, max DD "
                         f"{y['max_dd']:.1%}, {y['n']} trades "
                         f"({'out-of-sample' if y['start'] >= meta['oos_start'] else 'in-sample'}).")
        L.append(f"**Market condition that breaks it:** {r['breaks_in'] or 'not enough trades to tell'}")
        sc = r["score"]
        L += ["", f"Score: OOS Sharpe {sc['oos_sharpe']} · Deflated Sharpe {sc['deflated_sharpe']} · "
                  f"Max DD {sc['max_drawdown']} · Trade count {sc['trade_count']} · "
                  f"Edge after costs {sc['edge_after_costs']} = **{sc['total']}/25**", "",
              "**WHY THIS COULD FAIL**"] + [f"- {w}" for w in r["why_fail"]]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="/app/config.json")
    ap.add_argument("--synthetic", action="store_true", help="random data, code test only")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    cfg = json.load(open(args.config))
    cfg["data_dir"] = os.environ.get("DATA_DIR", cfg["data_dir"])  # GitHub Actions: ./data
    os.makedirs(cfg["data_dir"], exist_ok=True)
    t_start = time.time()

    # ---- 1. data
    if args.synthetic:
        prices = D.synthetic_prices(start=cfg["start"])
        universe = [t for t in prices if t.startswith("SYN")]
        earnings, source = {}, "SYNTHETIC random walk"
        insiders, ins_meta = INS.synthetic_insiders(prices), {"quarters": "synthetic"}
        cfg["strategies"]["earnings_drift"]["earnings_source"] = "gap_proxy"
    else:
        universe = D.load_universe(cfg)
        prices = D.load_prices(universe, cfg)
        need_earn = any(s.get("enabled") for s in cfg["strategies"].values())
        earnings = D.load_earnings([t for t in universe if t in prices], cfg) if need_earn else {}
        source = "Yahoo Finance via yfinance (adjusted daily bars)"
        insiders, ins_meta = {}, {}
        if cfg["strategies"].get("insider_cluster", {}).get("enabled"):
            insiders, ins_meta = INS.load_insiders([t for t in universe if t in prices], cfg)
    bench = prices.get("IWM")
    if bench is None:
        raise SystemExit("IWM benchmark missing; it's needed for the calendar and regimes.")
    calendar = bench.index[bench.index >= pd.Timestamp(cfg["start"])]
    usable = [t for t in universe if t in prices and len(prices[t]) >= 260]

    warmup = 250
    oos_i = int(len(calendar) * (1 - cfg["oos_fraction"]))
    is_start, is_end, oos_start, end = (calendar[warmup], calendar[oos_i - 1],
                                        calendar[oos_i], calendar[-1])

    # ---- 2. every variant
    runs = {}  # (strategy, idx) -> dict
    for name, scfg in cfg["strategies"].items():
        if not scfg.get("enabled"):
            continue
        for k, p in enumerate(expand_grid(scfg["grid"])):
            log.info("Simulating %s variant %d: %s", name, k, p)
            t0 = time.time()
            sig = build_signals(name, p, prices, earnings, cfg, usable, insiders)
            eq, tr = simulate(prices, sig, cfg, calendar)
            log.info("  %d trades, %.1fs", len(tr), time.time() - t0)
            ret = S.daily_returns(eq)
            runs[(name, k)] = {"params": p, "equity": eq, "trades": tr, "ret": ret,
                               "is_sharpe": S.sharpe(ret[is_start:is_end])}
    n_trials = len(runs)
    sr_trials = [r["ret"][is_start:is_end].mean() / r["ret"][is_start:is_end].std()
                 for r in runs.values() if r["ret"][is_start:is_end].std() > 0]

    # ---- 3-5. select on IS, judge on OOS
    results = []
    for name in {k[0] for k in runs}:
        variants = {k: v for k, v in runs.items() if k[0] == name}
        best_k = max(variants, key=lambda k: variants[k]["is_sharpe"])
        b = variants[best_k]
        oos_ret = b["ret"][oos_start:end]
        is_stats = S.period_stats(b["equity"], b["trades"], is_start, is_end)
        oos_stats = S.period_stats(b["equity"], b["trades"], oos_start, end)

        log.info("Stress test %s (2x slippage, 1 bar late)", name)
        sig = build_signals(name, b["params"], prices, earnings, cfg, usable, insiders)
        eq_s, tr_s = simulate(prices, sig, cfg, calendar, slip_mult=2.0, delay=1)
        stress = S.period_stats(eq_s, tr_s, oos_start, end)

        tr = b["trades"]
        oos_tr = tr[tr.entry_date >= oos_start] if len(tr) else tr
        dsr = S.deflated_sharpe(oos_ret, sr_trials, n_trials)
        mc = S.monte_carlo_dd(oos_tr["ret_equity"] if len(oos_tr) else [],
                              runs=cfg.get("monte_carlo_runs", 1000))
        wf = walk_forward({k: v["ret"] for k, v in variants.items()}, calendar,
                          cfg["walk_forward"]["train_days"], cfg["walk_forward"]["test_days"], warmup)
        years = {}
        for yr in ("2020", "2022"):
            s0, s1 = pd.Timestamp(f"{yr}-01-01"), pd.Timestamp(f"{yr}-12-31")
            if s0 >= is_start:
                years[yr] = S.period_stats(b["equity"], tr, s0, s1)
        table, worst = regime_table(oos_tr, bench)
        score = S.scorecard(oos_stats["sharpe"], dsr, oos_stats["max_dd"],
                            oos_stats["n"], oos_stats["avg_R"])
        passed = (score["total"] >= cfg["min_score"] and oos_stats["n"] >= cfg["min_oos_trades"]
                  and oos_stats["avg_R"] > 0 and stress["avg_R"] > 0)
        r = {"name": name, "params": b["params"], "rules": describe_rules(name, b["params"]),
             "thesis": THESIS[name][0], "other_side": THESIS[name][1],
             "is": is_stats, "oos": oos_stats, "stress": stress, "deflated_sharpe": dsr,
             "n_trials": n_trials, "monte_carlo": mc, "walk_forward": wf,
             "regimes_years": years, "regime_table": table, "breaks_in": worst,
             "score": score, "passed": bool(passed)}
        r["why_fail"] = why_it_could_fail(r, cfg)
        results.append(r)
        r["_oos_trades"] = oos_tr

    # Rank: passing first, then score, then OOS Sharpe ("boring with proof" beats exciting)
    results.sort(key=lambda r: (r["passed"], r["score"]["total"], r["oos"]["sharpe"]), reverse=True)

    # ---- 6. outputs
    run_date = datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join(cfg["data_dir"], "results", run_date)
    os.makedirs(out_dir, exist_ok=True)
    meta = {"run_date": run_date, "synthetic": args.synthetic, "source": source,
            "start": str(calendar[0].date()), "end": str(end.date()),
            "is_start": str(is_start.date()), "is_end": str(is_end.date()),
            "oos_start": str(oos_start.date()), "universe_n": len(usable), "n_trials": n_trials,
            "earnings_n": sum(1 for t in usable if t in earnings), "insiders": ins_meta,
            "slippage_bps": cfg["slippage_bps"], "capital": cfg["capital"],
            "risk": cfg["risk_per_trade"], "max_pct": cfg["max_position_pct"],
            "max_pos": cfg["max_positions"], "min_score": cfg["min_score"],
            "min_trades": cfg["min_oos_trades"]}
    for r in results:
        t = r.pop("_oos_trades")
        if len(t):
            t.to_csv(os.path.join(out_dir, f"oos_trades_{r['name']}.csv"), index=False)
    write_report(results, meta, out_dir)
    with open(os.path.join(out_dir, "report.json"), "w") as f:
        json.dump({"meta": meta, "results": results}, f, indent=2, default=str)
    latest = os.path.join(cfg["data_dir"], "results", "latest.md")
    shutil.copyfile(os.path.join(out_dir, "report.md"), latest)
    log.info("Done in %.1f min. Report: %s", (time.time() - t_start) / 60,
             os.path.join(out_dir, "report.md"))


if __name__ == "__main__":
    main()
