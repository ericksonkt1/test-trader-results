# Strategist report — 2026-11-25

- Data: Yahoo Finance via yfinance (adjusted daily bars), 2018-01-02 → 2026-11-25, 985 tickers with usable history, earnings dates for 985
- Insider data (SEC Form 4 data sets): {"quarters": 35, "missing": ["2026q4_form345.zip"], "tickers": 820, "last_filing": "2026-09-30"}
- In-sample: 2018-12-31 → 2024-03-22 · Out-of-sample: 2024-03-25 → 2026-11-25
- Variants tested tonight (counted for deflated Sharpe): 22
- Costs: 15 bps slippage per side, $0 commission · Capital $10,000 · risk 1.0%/trade
- Pass bar: score ≥ 18/25, ≥ 30 OOS trades, positive OOS expectancy, positive under stress

## Ranking (by out-of-sample strength)

| # | Strategy | Score | OOS Sharpe | DSR | OOS trades | Avg R | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | insider_cluster | 14/25 | 0.39 | 0.49 | 135 | +0.05 | FAIL |
| 2 | pullback_regime | 10/25 | -0.27 | 0.13 | 762 | -0.01 | FAIL |
| 3 | pullback_reversion | 10/25 | -0.33 | 0.11 | 869 | -0.02 | FAIL |
| 4 | volume_breakout | 9/25 | -0.52 | 0.07 | 512 | -0.07 | FAIL |
| 5 | earnings_drift | 9/25 | -0.87 | 0.02 | 282 | -0.11 | FAIL |

## insider_cluster — FAIL (14/25)

**Thesis:** Several officers/directors buying their own stock on the open market within days signals undervaluation; thinly covered small caps price it in slowly.
**Who's on the other side:** Sellers without the insiders' information; analysts slow to notice.

**Rules:** ENTRY: on a Form 4 filing date, >= 2 distinct Directors/Officers have filed open-market buys in the last 10 days totalling >= $100,000 (first crossing) -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"min_insiders": 2, "window_days": 10, "min_value": 100000, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -7.9% | +6.5% | +1.3% |
| Sharpe | -0.14 | 0.39 | 0.11 |
| Max drawdown | -16.3% | -7.0% | -12.7% |
| Trades | 258 | 135 | 137 |
| Win rate | 42% | 45% | 34% |
| Avg R (after costs) | -0.03 | +0.05 | +0.02 |
| Profit factor | 0.89 | 1.20 | 1.04 |

**Walk-forward:** 11 windows, Sharpe -0.03, return -1.7%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -5.8%, 95th-percentile -11.3%, worst -16.1%.
**Deflated Sharpe:** 0.49 probability the edge is real after 22 trials.
**2020:** return -6.6%, max DD -15.5%, 68 trades (in-sample).
**2022:** return -1.2%, max DD -5.6%, 49 trades (in-sample).
**Market condition that breaks it:** downtrend/low-vol

Score: OOS Sharpe 2 · Deflated Sharpe 1 · Max DD 5 · Trade count 4 · Edge after costs 2 = **14/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge more than halves with worse fills/timing.
- 2020: return -6.6%, max drawdown -15.5%.
- 2022: return -1.2%, max drawdown -5.6%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.49 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: downtrend/low-vol (avg R -0.53).

## pullback_regime — FAIL (10/25)

**Thesis:** Same 2-day selloff reversion in uptrending stocks, but only while the small-cap market (IJR) is above its 200-day SMA; dips in a falling market keep falling.
**Who's on the other side:** Panic sellers and stop-loss cascades in an otherwise healthy market.

**Rules:** ENTRY: IJR close > IJR 200SMA and close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 10, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -25.5% | -10.3% | -46.9% |
| Sharpe | -0.51 | -0.27 | -1.64 |
| Max drawdown | -30.5% | -24.5% | -48.7% |
| Trades | 893 | 762 | 781 |
| Win rate | 59% | 59% | 53% |
| Avg R (after costs) | -0.03 | -0.01 | -0.08 |
| Profit factor | 0.82 | 0.93 | 0.62 |

**Walk-forward:** 11 windows, Sharpe -0.37, return -22.2%, 27% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -17.6%, 95th-percentile -30.5%, worst -42.4%.
**Deflated Sharpe:** 0.13 probability the edge is real after 22 trials.
**2020:** return -7.9%, max DD -20.5%, 169 trades (in-sample).
**2022:** return -10.5%, max DD -11.1%, 48 trades (in-sample).
**Market gate (IJR > 200SMA) open:** 55% of in-sample days, 84% of out-of-sample days.
**Market condition that breaks it:** uptrend/low-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 2 · Trade count 5 · Edge after costs 1 = **10/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -7.9%, max drawdown -20.5%.
- 2022: return -10.5%, max drawdown -11.1%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.13 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: uptrend/low-vol (avg R -0.05).

## pullback_reversion — FAIL (10/25)

**Thesis:** Sharp 2-day selloffs in healthy uptrends are forced/emotional selling that reverts within days.
**Who's on the other side:** Panic sellers and stop-loss cascades.

**Rules:** ENTRY: close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 10, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -29.0% | -13.2% | -53.4% |
| Sharpe | -0.42 | -0.33 | -1.89 |
| Max drawdown | -36.2% | -29.5% | -54.4% |
| Trades | 1387 | 869 | 890 |
| Win rate | 59% | 58% | 52% |
| Avg R (after costs) | -0.02 | -0.02 | -0.09 |
| Profit factor | 0.87 | 0.91 | 0.59 |

**Walk-forward:** 11 windows, Sharpe -0.60, return -38.5%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -20.4%, 95th-percentile -34.6%, worst -44.3%.
**Deflated Sharpe:** 0.11 probability the edge is real after 22 trials.
**2020:** return -9.7%, max DD -28.9%, 246 trades (in-sample).
**2022:** return -17.6%, max DD -21.5%, 232 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 2 · Trade count 5 · Edge after costs 1 = **10/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -9.7%, max drawdown -28.9%.
- 2022: return -17.6%, max drawdown -21.5%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.11 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.07).

## volume_breakout — FAIL (9/25)

**Thesis:** New highs on 1.5x+ volume in an uptrend signal fresh demand.
**Who's on the other side:** Holders selling at 'resistance' and short-term faders.

**Rules:** ENTRY: close > prior 20-day high, volume >= 1.5x 50-day avg, close > 200SMA, 50SMA > 200SMA -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"lookback": 20, "vol_mult": 1.5, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -15.3% | -26.7% | -30.2% |
| Sharpe | -0.01 | -0.52 | -0.62 |
| Max drawdown | -50.4% | -32.7% | -38.1% |
| Trades | 948 | 512 | 520 |
| Win rate | 46% | 42% | 38% |
| Avg R (after costs) | +0.00 | -0.07 | -0.08 |
| Profit factor | 0.97 | 0.82 | 0.83 |

**Walk-forward:** 11 windows, Sharpe -0.47, return -54.9%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -35.0%, 95th-percentile -52.0%, worst -66.5%.
**Deflated Sharpe:** 0.07 probability the edge is real after 22 trials.
**2020:** return -20.6%, max DD -31.0%, 185 trades (in-sample).
**2022:** return -27.4%, max DD -29.5%, 176 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -20.6%, max drawdown -31.0%.
- 2022: return -27.4%, max drawdown -29.5%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.07 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.26).

## earnings_drift — FAIL (9/25)

**Thesis:** Strong post-earnings gaps that hold on heavy volume keep drifting as the market under-reacts.
**Who's on the other side:** Slow-to-update holders and analysts; sellers taking quick profits.

**Rules:** ENTRY: on the earnings reaction day, gap up >= 3%, close > open, volume >= 2.0x 50-day avg -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"gap_min": 0.03, "vol_mult": 2.0, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -22.5% | -25.9% | -26.2% |
| Sharpe | -0.37 | -0.87 | -0.82 |
| Max drawdown | -32.6% | -34.4% | -35.5% |
| Trades | 425 | 282 | 250 |
| Win rate | 46% | 42% | 42% |
| Avg R (after costs) | -0.05 | -0.11 | -0.12 |
| Profit factor | 0.84 | 0.76 | 0.72 |

**Walk-forward:** 11 windows, Sharpe -0.42, return -23.0%, 45% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -29.3%, 95th-percentile -43.4%, worst -55.4%.
**Deflated Sharpe:** 0.02 probability the edge is real after 22 trials.
**2020:** return -21.6%, max DD -23.1%, 78 trades (in-sample).
**2022:** return +6.7%, max DD -9.8%, 79 trades (in-sample).
**Market condition that breaks it:** uptrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -21.6%, max drawdown -23.1%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.02 < 0.95 after counting 22 variants tried, so it could be luck.
- Weakest regime: uptrend/high-vol (avg R -0.12).
