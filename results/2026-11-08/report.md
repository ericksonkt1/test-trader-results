# Strategist report — 2026-11-08

- Data: Yahoo Finance via yfinance (adjusted daily bars), 2018-01-02 → 2026-11-06, 985 tickers with usable history
- In-sample: 2018-12-31 → 2024-03-11 · Out-of-sample: 2024-03-12 → 2026-11-06
- Variants tested tonight (counted for deflated Sharpe): 16
- Costs: 15 bps slippage per side, $0 commission · Capital $10,000 · risk 1.0%/trade
- Pass bar: score ≥ 18/25, ≥ 30 OOS trades, positive OOS expectancy, positive under stress

## Ranking (by out-of-sample strength)

| # | Strategy | Score | OOS Sharpe | DSR | OOS trades | Avg R | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | volume_breakout | 9/25 | -0.18 | 0.23 | 516 | -0.01 | FAIL |
| 2 | pullback_reversion | 9/25 | -0.75 | 0.04 | 960 | -0.03 | FAIL |
| 3 | earnings_drift | 9/25 | -0.81 | 0.04 | 177 | -0.12 | FAIL |

## volume_breakout — FAIL (9/25)

**Thesis:** New highs on 1.5x+ volume in an uptrend signal fresh demand.
**Who's on the other side:** Holders selling at 'resistance' and short-term faders.

**Rules:** ENTRY: close > prior 50-day high, volume >= 1.5x 50-day avg, close > 200SMA, 50SMA > 200SMA -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"lookback": 50, "vol_mult": 1.5, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -32.3% | -13.1% | -25.9% |
| Sharpe | -0.21 | -0.18 | -0.52 |
| Max drawdown | -53.9% | -34.3% | -33.0% |
| Trades | 938 | 516 | 513 |
| Win rate | 43% | 43% | 39% |
| Avg R (after costs) | -0.03 | -0.01 | -0.08 |
| Profit factor | 0.90 | 0.94 | 0.86 |

**Walk-forward:** 11 windows, Sharpe -0.50, return -53.6%, 27% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -26.3%, 95th-percentile -43.3%, worst -60.1%.
**Deflated Sharpe:** 0.23 probability the edge is real after 16 trials.
**2020:** return -22.8%, max DD -30.4%, 183 trades (in-sample).
**2022:** return -31.6%, max DD -36.1%, 175 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -22.8%, max drawdown -30.4%.
- 2022: return -31.6%, max drawdown -36.1%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.23 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.27).

## pullback_reversion — FAIL (9/25)

**Thesis:** Sharp 2-day selloffs in healthy uptrends are forced/emotional selling that reverts within days.
**Who's on the other side:** Panic sellers and stop-loss cascades.

**Rules:** ENTRY: close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 5 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 5, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -31.7% | -25.7% | -52.8% |
| Sharpe | -0.48 | -0.75 | -1.87 |
| Max drawdown | -41.7% | -32.3% | -53.7% |
| Trades | 1528 | 960 | 1003 |
| Win rate | 57% | 55% | 51% |
| Avg R (after costs) | -0.03 | -0.03 | -0.08 |
| Profit factor | 0.86 | 0.86 | 0.63 |

**Walk-forward:** 11 windows, Sharpe -0.49, return -34.2%, 45% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -28.4%, 95th-percentile -42.8%, worst -54.2%.
**Deflated Sharpe:** 0.04 probability the edge is real after 16 trials.
**2020:** return -10.6%, max DD -29.3%, 267 trades (in-sample).
**2022:** return -19.6%, max DD -22.2%, 249 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -10.6%, max drawdown -29.3%.
- 2022: return -19.6%, max drawdown -22.2%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.04 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.08).

## earnings_drift — FAIL (9/25)

**Thesis:** Strong post-earnings gaps that hold on heavy volume keep drifting as the market under-reacts.
**Who's on the other side:** Slow-to-update holders and analysts; sellers taking quick profits.

**Rules:** ENTRY: on the earnings reaction day, gap up >= 5%, close > open, volume >= 2.0x 50-day avg -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"gap_min": 0.05, "vol_mult": 2.0, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -8.7% | -19.6% | -17.3% |
| Sharpe | -0.17 | -0.81 | -0.83 |
| Max drawdown | -29.4% | -23.0% | -21.8% |
| Trades | 241 | 177 | 153 |
| Win rate | 44% | 39% | 42% |
| Avg R (after costs) | -0.04 | -0.12 | -0.11 |
| Profit factor | 0.89 | 0.75 | 0.73 |

**Walk-forward:** 11 windows, Sharpe -0.20, return -10.7%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -22.1%, 95th-percentile -34.4%, worst -44.9%.
**Deflated Sharpe:** 0.04 probability the edge is real after 16 trials.
**2020:** return -11.1%, max DD -17.7%, 43 trades (in-sample).
**2022:** return +2.9%, max DD -7.9%, 48 trades (in-sample).
**Market condition that breaks it:** downtrend/low-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 2 · Trade count 4 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -11.1%, max drawdown -17.7%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.04 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/low-vol (avg R -0.62).
