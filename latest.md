# Strategist report — 2026-11-20

- Data: Yahoo Finance via yfinance (adjusted daily bars), 2018-01-02 → 2026-11-19, 985 tickers with usable history, earnings dates for 985
- Insider data (SEC Form 4 data sets): {"quarters": 35, "missing": ["2026q4_form345.zip"], "tickers": 820, "last_filing": "2026-09-30"}
- In-sample: 2018-12-31 → 2024-03-19 · Out-of-sample: 2024-03-20 → 2026-11-19
- Variants tested tonight (counted for deflated Sharpe): 22
- Costs: 15 bps slippage per side, $0 commission · Capital $10,000 · risk 1.0%/trade
- Pass bar: score ≥ 18/25, ≥ 30 OOS trades, positive OOS expectancy, positive under stress

## Ranking (by out-of-sample strength)

| # | Strategy | Score | OOS Sharpe | DSR | OOS trades | Avg R | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | insider_cluster | 15/25 | 0.41 | 0.53 | 135 | +0.05 | FAIL |
| 2 | volume_breakout | 10/25 | 0.00 | 0.29 | 503 | -0.01 | FAIL |
| 3 | pullback_regime | 10/25 | -0.17 | 0.20 | 761 | -0.01 | FAIL |
| 4 | pullback_reversion | 10/25 | -0.24 | 0.17 | 863 | -0.01 | FAIL |
| 5 | earnings_drift | 9/25 | -0.87 | 0.02 | 280 | -0.11 | FAIL |

## insider_cluster — FAIL (15/25)

**Thesis:** Several officers/directors buying their own stock on the open market within days signals undervaluation; thinly covered small caps price it in slowly.
**Who's on the other side:** Sellers without the insiders' information; analysts slow to notice.

**Rules:** ENTRY: on a Form 4 filing date, >= 2 distinct Directors/Officers have filed open-market buys in the last 10 days totalling >= $100,000 (first crossing) -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"min_insiders": 2, "window_days": 10, "min_value": 100000, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -8.2% | +7.0% | +0.3% |
| Sharpe | -0.15 | 0.41 | 0.05 |
| Max drawdown | -16.3% | -7.0% | -12.6% |
| Trades | 258 | 135 | 137 |
| Win rate | 42% | 45% | 34% |
| Avg R (after costs) | -0.03 | +0.05 | +0.02 |
| Profit factor | 0.89 | 1.20 | 1.05 |

**Walk-forward:** 11 windows, Sharpe -0.03, return -1.6%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -5.8%, 95th-percentile -11.2%, worst -16.0%.
**Deflated Sharpe:** 0.53 probability the edge is real after 22 trials.
**2020:** return -6.6%, max DD -15.5%, 68 trades (in-sample).
**2022:** return -1.2%, max DD -5.6%, 49 trades (in-sample).
**Market condition that breaks it:** downtrend/low-vol

Score: OOS Sharpe 2 · Deflated Sharpe 2 · Max DD 5 · Trade count 4 · Edge after costs 2 = **15/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge more than halves with worse fills/timing.
- 2020: return -6.6%, max drawdown -15.5%.
- 2022: return -1.2%, max drawdown -5.6%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.53 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: downtrend/low-vol (avg R -0.53).

## volume_breakout — FAIL (10/25)

**Thesis:** New highs on 1.5x+ volume in an uptrend signal fresh demand.
**Who's on the other side:** Holders selling at 'resistance' and short-term faders.

**Rules:** ENTRY: close > prior 50-day high, volume >= 1.5x 50-day avg, close > 200SMA, 50SMA > 200SMA -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"lookback": 50, "vol_mult": 1.5, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -20.4% | -4.3% | -27.0% |
| Sharpe | -0.07 | 0.00 | -0.55 |
| Max drawdown | -50.0% | -30.0% | -32.8% |
| Trades | 930 | 503 | 506 |
| Win rate | 46% | 45% | 40% |
| Avg R (after costs) | -0.00 | -0.01 | -0.07 |
| Profit factor | 0.95 | 0.96 | 0.85 |

**Walk-forward:** 11 windows, Sharpe -0.43, return -52.1%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -22.7%, 95th-percentile -40.9%, worst -52.8%.
**Deflated Sharpe:** 0.29 probability the edge is real after 22 trials.
**2020:** return -18.1%, max DD -29.9%, 179 trades (in-sample).
**2022:** return -29.9%, max DD -30.2%, 167 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 2 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **10/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -18.1%, max drawdown -29.9%.
- 2022: return -29.9%, max drawdown -30.2%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.29 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.31).

## pullback_regime — FAIL (10/25)

**Thesis:** Same 2-day selloff reversion in uptrending stocks, but only while the small-cap market (IJR) is above its 200-day SMA; dips in a falling market keep falling.
**Who's on the other side:** Panic sellers and stop-loss cascades in an otherwise healthy market.

**Rules:** ENTRY: IJR close > IJR 200SMA and close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 10, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -26.5% | -7.1% | -47.1% |
| Sharpe | -0.53 | -0.17 | -1.65 |
| Max drawdown | -31.2% | -23.5% | -48.6% |
| Trades | 894 | 761 | 783 |
| Win rate | 59% | 59% | 53% |
| Avg R (after costs) | -0.03 | -0.01 | -0.08 |
| Profit factor | 0.82 | 0.95 | 0.63 |

**Walk-forward:** 11 windows, Sharpe -0.32, return -20.1%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -16.6%, 95th-percentile -29.1%, worst -44.2%.
**Deflated Sharpe:** 0.20 probability the edge is real after 22 trials.
**2020:** return -7.8%, max DD -20.5%, 170 trades (in-sample).
**2022:** return -12.2%, max DD -12.8%, 48 trades (in-sample).
**Market gate (IJR > 200SMA) open:** 55% of in-sample days, 85% of out-of-sample days.
**Market condition that breaks it:** uptrend/low-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 2 · Trade count 5 · Edge after costs 1 = **10/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -7.8%, max drawdown -20.5%.
- 2022: return -12.2%, max drawdown -12.8%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.20 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: uptrend/low-vol (avg R -0.04).

## pullback_reversion — FAIL (10/25)

**Thesis:** Sharp 2-day selloffs in healthy uptrends are forced/emotional selling that reverts within days.
**Who's on the other side:** Panic sellers and stop-loss cascades.

**Rules:** ENTRY: close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 10, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -28.7% | -10.4% | -53.4% |
| Sharpe | -0.42 | -0.24 | -1.89 |
| Max drawdown | -36.1% | -29.3% | -54.5% |
| Trades | 1383 | 863 | 888 |
| Win rate | 59% | 59% | 52% |
| Avg R (after costs) | -0.02 | -0.01 | -0.09 |
| Profit factor | 0.87 | 0.93 | 0.59 |

**Walk-forward:** 11 windows, Sharpe -0.29, return -23.5%, 55% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -18.8%, 95th-percentile -32.9%, worst -45.5%.
**Deflated Sharpe:** 0.17 probability the edge is real after 22 trials.
**2020:** return -10.5%, max DD -29.3%, 245 trades (in-sample).
**2022:** return -17.0%, max DD -20.8%, 230 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 2 · Trade count 5 · Edge after costs 1 = **10/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -10.5%, max drawdown -29.3%.
- 2022: return -17.0%, max drawdown -20.8%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.17 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.08).

## earnings_drift — FAIL (9/25)

**Thesis:** Strong post-earnings gaps that hold on heavy volume keep drifting as the market under-reacts.
**Who's on the other side:** Slow-to-update holders and analysts; sellers taking quick profits.

**Rules:** ENTRY: on the earnings reaction day, gap up >= 3%, close > open, volume >= 2.0x 50-day avg -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"gap_min": 0.03, "vol_mult": 2.0, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -19.6% | -25.7% | -25.5% |
| Sharpe | -0.31 | -0.87 | -0.80 |
| Max drawdown | -29.9% | -33.8% | -35.2% |
| Trades | 423 | 280 | 250 |
| Win rate | 46% | 41% | 42% |
| Avg R (after costs) | -0.05 | -0.11 | -0.11 |
| Profit factor | 0.86 | 0.76 | 0.72 |

**Walk-forward:** 11 windows, Sharpe -0.40, return -22.3%, 45% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -29.0%, 95th-percentile -42.8%, worst -54.6%.
**Deflated Sharpe:** 0.02 probability the edge is real after 22 trials.
**2020:** return -20.7%, max DD -22.2%, 77 trades (in-sample).
**2022:** return +5.2%, max DD -9.7%, 80 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -20.7%, max drawdown -22.2%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.02 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.15).
