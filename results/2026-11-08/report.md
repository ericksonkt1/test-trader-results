# Strategist report — 2026-11-08

- Data: Yahoo Finance via yfinance (adjusted daily bars), 2018-01-02 → 2026-11-06, 985 tickers with usable history, earnings dates for 985
- Insider data (SEC Form 4 data sets): {"quarters": 0, "missing": ["2018q1_form345.zip", "2018q2_form345.zip", "2018q3_form345.zip", "2018q4_form345.zip", "2019q1_form345.zip", "2019q2_form345.zip", "2019q3_form345.zip", "2019q4_form345.zip", "2020q1_form345.zip", "2020q2_form345.zip", "2020q3_form345.zip", "2020q4_form345.zip", "2021q1_form345.zip", "2021q2_form345.zip", "2021q3_form345.zip", "2021q4_form345.zip", "2022q1_form345.zip", "2022q2_form345.zip", "2022q3_form345.zip", "2022q4_form345.zip", "2023q1_form345.zip", "2023q2_form345.zip", "2023q3_form345.zip", "2023q4_form345.zip", "2024q1_form345.zip", "2024q2_form345.zip", "2024q3_form345.zip", "2024q4_form345.zip", "2025q1_form345.zip", "2025q2_form345.zip", "2025q3_form345.zip", "2025q4_form345.zip", "2026q1_form345.zip", "2026q2_form345.zip", "2026q3_form345.zip", "2026q4_form345.zip"]}
- In-sample: 2018-12-31 → 2024-03-11 · Out-of-sample: 2024-03-12 → 2026-11-06
- Variants tested tonight (counted for deflated Sharpe): 20
- Costs: 15 bps slippage per side, $0 commission · Capital $10,000 · risk 1.0%/trade
- Pass bar: score ≥ 18/25, ≥ 30 OOS trades, positive OOS expectancy, positive under stress

## Ranking (by out-of-sample strength)

| # | Strategy | Score | OOS Sharpe | DSR | OOS trades | Avg R | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | insider_cluster | 9/25 | 0.00 | 0.00 | 0 | +0.00 | FAIL |
| 2 | volume_breakout | 9/25 | -0.23 | 0.17 | 504 | -0.03 | FAIL |
| 3 | pullback_reversion | 9/25 | -0.83 | 0.02 | 942 | -0.03 | FAIL |
| 4 | earnings_drift | 9/25 | -0.97 | 0.02 | 277 | -0.11 | FAIL |

## insider_cluster — FAIL (9/25)

**Thesis:** Several officers/directors buying their own stock on the open market within days signals undervaluation; thinly covered small caps price it in slowly.
**Who's on the other side:** Sellers without the insiders' information; analysts slow to notice.

**Rules:** ENTRY: on a Form 4 filing date, >= 2 distinct Directors/Officers have filed open-market buys in the last 10 days totalling >= $100,000 (first crossing) -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 5 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"min_insiders": 2, "window_days": 10, "min_value": 100000, "max_hold": 5, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | +0.0% | +0.0% | +0.0% |
| Sharpe | 0.00 | 0.00 | 0.00 |
| Max drawdown | 0.0% | 0.0% | 0.0% |
| Trades | 0 | 0 | 0 |
| Win rate | 0% | 0% | 0% |
| Avg R (after costs) | +0.00 | +0.00 | +0.00 |
| Profit factor | 0.00 | 0.00 | 0.00 |

**Walk-forward:** 11 windows, Sharpe 0.00, return +0.0%, 0% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown n/a, 95th-percentile n/a, worst n/a.
**Deflated Sharpe:** 0.00 probability the edge is real after 20 trials.
**2020:** return +0.0%, max DD 0.0%, 0 trades (in-sample).
**2022:** return +0.0%, max DD 0.0%, 0 trades (in-sample).
**Market condition that breaks it:** not enough trades to tell

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 5 · Trade count 1 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- Fewer than 60% of walk-forward windows were profitable.
- Only 0 out-of-sample trades, so the estimate is noisy.
- Deflated Sharpe 0.00 < 0.95 after counting 20 variants tried, so it could be luck.

## volume_breakout — FAIL (9/25)

**Thesis:** New highs on 1.5x+ volume in an uptrend signal fresh demand.
**Who's on the other side:** Holders selling at 'resistance' and short-term faders.

**Rules:** ENTRY: close > prior 50-day high, volume >= 1.5x 50-day avg, close > 200SMA, 50SMA > 200SMA -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"lookback": 50, "vol_mult": 1.5, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -18.5% | -14.5% | -23.0% |
| Sharpe | -0.05 | -0.23 | -0.44 |
| Max drawdown | -50.2% | -34.1% | -32.9% |
| Trades | 926 | 504 | 507 |
| Win rate | 46% | 45% | 40% |
| Avg R (after costs) | -0.01 | -0.03 | -0.06 |
| Profit factor | 0.95 | 0.92 | 0.88 |

**Walk-forward:** 11 windows, Sharpe -0.39, return -49.7%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -25.3%, 95th-percentile -42.9%, worst -55.3%.
**Deflated Sharpe:** 0.17 probability the edge is real after 20 trials.
**2020:** return -17.3%, max DD -29.6%, 179 trades (in-sample).
**2022:** return -30.0%, max DD -30.3%, 167 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -17.3%, max drawdown -29.6%.
- 2022: return -30.0%, max drawdown -30.3%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.17 < 0.95 after counting 20 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.34).

## pullback_reversion — FAIL (9/25)

**Thesis:** Sharp 2-day selloffs in healthy uptrends are forced/emotional selling that reverts within days.
**Who's on the other side:** Panic sellers and stop-loss cascades.

**Rules:** ENTRY: close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 5 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 5, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -27.1% | -27.4% | -55.6% |
| Sharpe | -0.40 | -0.83 | -2.03 |
| Max drawdown | -34.9% | -36.1% | -56.4% |
| Trades | 1496 | 942 | 978 |
| Win rate | 58% | 56% | 51% |
| Avg R (after costs) | -0.02 | -0.03 | -0.09 |
| Profit factor | 0.88 | 0.84 | 0.59 |

**Walk-forward:** 11 windows, Sharpe -0.44, return -31.2%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -29.1%, 95th-percentile -43.0%, worst -54.1%.
**Deflated Sharpe:** 0.02 probability the edge is real after 20 trials.
**2020:** return -7.5%, max DD -28.5%, 267 trades (in-sample).
**2022:** return -18.5%, max DD -22.1%, 244 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -7.5%, max drawdown -28.5%.
- 2022: return -18.5%, max drawdown -22.1%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.02 < 0.95 after counting 20 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.11).

## earnings_drift — FAIL (9/25)

**Thesis:** Strong post-earnings gaps that hold on heavy volume keep drifting as the market under-reacts.
**Who's on the other side:** Slow-to-update holders and analysts; sellers taking quick profits.

**Rules:** ENTRY: on the earnings reaction day, gap up >= 3%, close > open, volume >= 2.0x 50-day avg -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"gap_min": 0.03, "vol_mult": 2.0, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -23.1% | -27.8% | -26.2% |
| Sharpe | -0.38 | -0.97 | -0.84 |
| Max drawdown | -33.5% | -34.2% | -34.6% |
| Trades | 421 | 277 | 247 |
| Win rate | 45% | 40% | 40% |
| Avg R (after costs) | -0.06 | -0.11 | -0.11 |
| Profit factor | 0.83 | 0.76 | 0.73 |

**Walk-forward:** 11 windows, Sharpe -0.56, return -28.6%, 45% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -30.8%, 95th-percentile -44.8%, worst -55.3%.
**Deflated Sharpe:** 0.02 probability the edge is real after 20 trials.
**2020:** return -21.8%, max DD -22.6%, 78 trades (in-sample).
**2022:** return +6.4%, max DD -9.9%, 79 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -21.8%, max drawdown -22.6%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.02 < 0.95 after counting 20 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.17).
