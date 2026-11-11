# Strategist report — 2026-11-11

- Data: Yahoo Finance via yfinance (adjusted daily bars), 2018-01-02 → 2026-11-10, 985 tickers with usable history, earnings dates for 985
- Insider data (SEC Form 4 data sets): {"status": "SEC data unavailable, strategy skipped", "quarters_missing": 36}
- In-sample: 2018-12-31 → 2024-03-12 · Out-of-sample: 2024-03-13 → 2026-11-10
- Variants tested tonight (counted for deflated Sharpe): 16
- Costs: 15 bps slippage per side, $0 commission · Capital $10,000 · risk 1.0%/trade
- Pass bar: score ≥ 18/25, ≥ 30 OOS trades, positive OOS expectancy, positive under stress

## Ranking (by out-of-sample strength)

| # | Strategy | Score | OOS Sharpe | DSR | OOS trades | Avg R | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | volume_breakout | 10/25 | -0.03 | 0.25 | 505 | -0.00 | FAIL |
| 2 | earnings_drift | 10/25 | -0.81 | 0.03 | 233 | -0.11 | FAIL |
| 3 | pullback_reversion | 9/25 | -0.37 | 0.11 | 866 | -0.01 | FAIL |

## volume_breakout — FAIL (10/25)

**Thesis:** New highs on 1.5x+ volume in an uptrend signal fresh demand.
**Who's on the other side:** Holders selling at 'resistance' and short-term faders.

**Rules:** ENTRY: close > prior 50-day high, volume >= 1.5x 50-day avg, close > 200SMA, 50SMA > 200SMA -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"lookback": 50, "vol_mult": 1.5, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -17.0% | -5.4% | -22.3% |
| Sharpe | -0.03 | -0.03 | -0.42 |
| Max drawdown | -50.1% | -29.2% | -32.8% |
| Trades | 925 | 505 | 507 |
| Win rate | 46% | 46% | 40% |
| Avg R (after costs) | -0.00 | -0.00 | -0.06 |
| Profit factor | 0.95 | 0.97 | 0.89 |

**Walk-forward:** 11 windows, Sharpe -0.43, return -51.7%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -22.4%, 95th-percentile -38.7%, worst -53.9%.
**Deflated Sharpe:** 0.25 probability the edge is real after 16 trials.
**2020:** return -16.4%, max DD -29.2%, 178 trades (in-sample).
**2022:** return -30.0%, max DD -30.3%, 167 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 2 · Trade count 5 · Edge after costs 1 = **10/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -16.4%, max drawdown -29.2%.
- 2022: return -30.0%, max drawdown -30.3%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.25 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.32).

## earnings_drift — FAIL (10/25)

**Thesis:** Strong post-earnings gaps that hold on heavy volume keep drifting as the market under-reacts.
**Who's on the other side:** Slow-to-update holders and analysts; sellers taking quick profits.

**Rules:** ENTRY: on the earnings reaction day, gap up >= 3%, close > open, volume >= 3.0x 50-day avg -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"gap_min": 0.03, "vol_mult": 3.0, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -19.5% | -22.7% | -9.4% |
| Sharpe | -0.36 | -0.81 | -0.31 |
| Max drawdown | -34.5% | -29.2% | -29.8% |
| Trades | 349 | 233 | 195 |
| Win rate | 44% | 43% | 45% |
| Avg R (after costs) | -0.06 | -0.11 | -0.04 |
| Profit factor | 0.82 | 0.77 | 0.88 |

**Walk-forward:** 11 windows, Sharpe -0.56, return -28.2%, 45% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -26.2%, 95th-percentile -39.4%, worst -53.8%.
**Deflated Sharpe:** 0.03 probability the edge is real after 16 trials.
**2020:** return -17.7%, max DD -20.2%, 56 trades (in-sample).
**2022:** return -0.5%, max DD -11.5%, 64 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 2 · Trade count 5 · Edge after costs 1 = **10/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -17.7%, max drawdown -20.2%.
- 2022: return -0.5%, max drawdown -11.5%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.03 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.25).

## pullback_reversion — FAIL (9/25)

**Thesis:** Sharp 2-day selloffs in healthy uptrends are forced/emotional selling that reverts within days.
**Who's on the other side:** Panic sellers and stop-loss cascades.

**Rules:** ENTRY: close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 10, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -30.1% | -14.5% | -54.3% |
| Sharpe | -0.45 | -0.37 | -1.92 |
| Max drawdown | -37.5% | -30.0% | -55.5% |
| Trades | 1372 | 866 | 886 |
| Win rate | 59% | 59% | 52% |
| Avg R (after costs) | -0.02 | -0.01 | -0.09 |
| Profit factor | 0.86 | 0.91 | 0.58 |

**Walk-forward:** 11 windows, Sharpe -0.51, return -34.6%, 27% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -20.2%, 95th-percentile -34.4%, worst -46.0%.
**Deflated Sharpe:** 0.11 probability the edge is real after 16 trials.
**2020:** return -9.5%, max DD -28.3%, 245 trades (in-sample).
**2022:** return -17.5%, max DD -20.8%, 229 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -9.5%, max drawdown -28.3%.
- 2022: return -17.5%, max drawdown -20.8%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.11 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.08).
