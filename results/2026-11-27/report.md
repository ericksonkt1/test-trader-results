# Strategist report — 2026-11-27

- Data: Yahoo Finance via yfinance (adjusted daily bars), 2018-01-02 → 2026-11-27, 985 tickers with usable history, earnings dates for 985
- Insider data (SEC Form 4 data sets): {"quarters": 35, "missing": ["2026q4_form345.zip"], "tickers": 820, "last_filing": "2026-09-30"}
- In-sample: 2018-12-31 → 2024-03-25 · Out-of-sample: 2024-03-26 → 2026-11-27
- Variants tested tonight (counted for deflated Sharpe): 22
- Costs: 15 bps slippage per side, $0 commission · Capital $10,000 · risk 1.0%/trade
- Pass bar: score ≥ 18/25, ≥ 30 OOS trades, positive OOS expectancy, positive under stress

## Ranking (by out-of-sample strength)

| # | Strategy | Score | OOS Sharpe | DSR | OOS trades | Avg R | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | insider_cluster | 15/25 | 0.40 | 0.50 | 135 | +0.05 | FAIL |
| 2 | pullback_reversion | 10/25 | -0.19 | 0.18 | 861 | -0.01 | FAIL |
| 3 | pullback_regime | 10/25 | -0.23 | 0.16 | 756 | -0.01 | FAIL |
| 4 | volume_breakout | 9/25 | -0.54 | 0.07 | 511 | -0.07 | FAIL |
| 5 | earnings_drift | 9/25 | -0.79 | 0.03 | 281 | -0.10 | FAIL |

## insider_cluster — FAIL (15/25)

**Thesis:** Several officers/directors buying their own stock on the open market within days signals undervaluation; thinly covered small caps price it in slowly.
**Who's on the other side:** Sellers without the insiders' information; analysts slow to notice.

**Rules:** ENTRY: on a Form 4 filing date, >= 2 distinct Directors/Officers have filed open-market buys in the last 10 days totalling >= $100,000 (first crossing) -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"min_insiders": 2, "window_days": 10, "min_value": 100000, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -7.6% | +6.7% | +1.3% |
| Sharpe | -0.14 | 0.40 | 0.11 |
| Max drawdown | -16.3% | -7.0% | -12.7% |
| Trades | 258 | 135 | 137 |
| Win rate | 42% | 45% | 34% |
| Avg R (after costs) | -0.03 | +0.05 | +0.02 |
| Profit factor | 0.89 | 1.20 | 1.04 |

**Walk-forward:** 11 windows, Sharpe -0.03, return -1.7%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -5.8%, 95th-percentile -11.3%, worst -16.1%.
**Deflated Sharpe:** 0.50 probability the edge is real after 22 trials.
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
- Deflated Sharpe 0.50 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: downtrend/low-vol (avg R -0.53).

## pullback_reversion — FAIL (10/25)

**Thesis:** Sharp 2-day selloffs in healthy uptrends are forced/emotional selling that reverts within days.
**Who's on the other side:** Panic sellers and stop-loss cascades.

**Rules:** ENTRY: close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 10, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -29.2% | -8.5% | -52.4% |
| Sharpe | -0.43 | -0.19 | -1.84 |
| Max drawdown | -36.6% | -28.7% | -53.9% |
| Trades | 1386 | 861 | 892 |
| Win rate | 59% | 59% | 53% |
| Avg R (after costs) | -0.02 | -0.01 | -0.09 |
| Profit factor | 0.87 | 0.94 | 0.60 |

**Walk-forward:** 11 windows, Sharpe -0.36, return -27.6%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -18.0%, 95th-percentile -32.0%, worst -44.2%.
**Deflated Sharpe:** 0.18 probability the edge is real after 22 trials.
**2020:** return -9.9%, max DD -28.7%, 247 trades (in-sample).
**2022:** return -18.2%, max DD -21.7%, 232 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 2 · Trade count 5 · Edge after costs 1 = **10/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -9.9%, max drawdown -28.7%.
- 2022: return -18.2%, max drawdown -21.7%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.18 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.05).

## pullback_regime — FAIL (10/25)

**Thesis:** Same 2-day selloff reversion in uptrending stocks, but only while the small-cap market (IJR) is above its 200-day SMA; dips in a falling market keep falling.
**Who's on the other side:** Panic sellers and stop-loss cascades in an otherwise healthy market.

**Rules:** ENTRY: IJR close > IJR 200SMA and close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 10, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -24.1% | -9.1% | -46.3% |
| Sharpe | -0.47 | -0.23 | -1.61 |
| Max drawdown | -29.9% | -25.0% | -48.2% |
| Trades | 895 | 756 | 783 |
| Win rate | 59% | 58% | 53% |
| Avg R (after costs) | -0.03 | -0.01 | -0.08 |
| Profit factor | 0.83 | 0.93 | 0.63 |

**Walk-forward:** 11 windows, Sharpe -0.35, return -21.3%, 27% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -18.3%, 95th-percentile -31.5%, worst -39.6%.
**Deflated Sharpe:** 0.16 probability the edge is real after 22 trials.
**2020:** return -7.2%, max DD -19.5%, 171 trades (in-sample).
**2022:** return -12.1%, max DD -13.3%, 49 trades (in-sample).
**Market gate (IJR > 200SMA) open:** 55% of in-sample days, 84% of out-of-sample days.
**Market condition that breaks it:** uptrend/low-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 2 · Trade count 5 · Edge after costs 1 = **10/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -7.2%, max drawdown -19.5%.
- 2022: return -12.1%, max drawdown -13.3%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.16 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: uptrend/low-vol (avg R -0.04).

## volume_breakout — FAIL (9/25)

**Thesis:** New highs on 1.5x+ volume in an uptrend signal fresh demand.
**Who's on the other side:** Holders selling at 'resistance' and short-term faders.

**Rules:** ENTRY: close > prior 20-day high, volume >= 1.5x 50-day avg, close > 200SMA, 50SMA > 200SMA -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"lookback": 20, "vol_mult": 1.5, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -15.4% | -27.4% | -29.8% |
| Sharpe | -0.01 | -0.54 | -0.61 |
| Max drawdown | -50.4% | -32.0% | -38.4% |
| Trades | 949 | 511 | 519 |
| Win rate | 46% | 42% | 39% |
| Avg R (after costs) | +0.00 | -0.07 | -0.08 |
| Profit factor | 0.96 | 0.82 | 0.84 |

**Walk-forward:** 11 windows, Sharpe -0.47, return -54.8%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -35.4%, 95th-percentile -52.5%, worst -64.8%.
**Deflated Sharpe:** 0.07 probability the edge is real after 22 trials.
**2020:** return -20.6%, max DD -31.0%, 185 trades (in-sample).
**2022:** return -27.4%, max DD -29.6%, 176 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -20.6%, max drawdown -31.0%.
- 2022: return -27.4%, max drawdown -29.6%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.07 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.29).

## earnings_drift — FAIL (9/25)

**Thesis:** Strong post-earnings gaps that hold on heavy volume keep drifting as the market under-reacts.
**Who's on the other side:** Slow-to-update holders and analysts; sellers taking quick profits.

**Rules:** ENTRY: on the earnings reaction day, gap up >= 3%, close > open, volume >= 2.0x 50-day avg -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"gap_min": 0.03, "vol_mult": 2.0, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -20.9% | -24.0% | -24.0% |
| Sharpe | -0.33 | -0.79 | -0.74 |
| Max drawdown | -31.4% | -33.8% | -34.6% |
| Trades | 426 | 281 | 249 |
| Win rate | 46% | 42% | 43% |
| Avg R (after costs) | -0.05 | -0.10 | -0.11 |
| Profit factor | 0.85 | 0.77 | 0.73 |

**Walk-forward:** 11 windows, Sharpe -0.37, return -21.5%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -28.6%, 95th-percentile -42.3%, worst -51.1%.
**Deflated Sharpe:** 0.03 probability the edge is real after 22 trials.
**2020:** return -21.5%, max DD -23.0%, 78 trades (in-sample).
**2022:** return +6.4%, max DD -9.7%, 79 trades (in-sample).
**Market condition that breaks it:** uptrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -21.5%, max drawdown -23.0%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.03 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: uptrend/high-vol (avg R -0.12).
