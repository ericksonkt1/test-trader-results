# Strategist report — 2026-11-12

- Data: Yahoo Finance via yfinance (adjusted daily bars), 2018-01-02 → 2026-11-11, 985 tickers with usable history, earnings dates for 985
- Insider data (SEC Form 4 data sets): {"status": "SEC data unavailable, strategy skipped", "quarters_missing": 36}
- In-sample: 2018-12-31 → 2024-03-13 · Out-of-sample: 2024-03-14 → 2026-11-11
- Variants tested tonight (counted for deflated Sharpe): 16
- Costs: 15 bps slippage per side, $0 commission · Capital $10,000 · risk 1.0%/trade
- Pass bar: score ≥ 18/25, ≥ 30 OOS trades, positive OOS expectancy, positive under stress

## Ranking (by out-of-sample strength)

| # | Strategy | Score | OOS Sharpe | DSR | OOS trades | Avg R | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | volume_breakout | 9/25 | -0.10 | 0.22 | 506 | -0.02 | FAIL |
| 2 | pullback_reversion | 9/25 | -0.22 | 0.15 | 868 | -0.01 | FAIL |
| 3 | earnings_drift | 9/25 | -0.90 | 0.02 | 279 | -0.11 | FAIL |

## volume_breakout — FAIL (9/25)

**Thesis:** New highs on 1.5x+ volume in an uptrend signal fresh demand.
**Who's on the other side:** Holders selling at 'resistance' and short-term faders.

**Rules:** ENTRY: close > prior 50-day high, volume >= 1.5x 50-day avg, close > 200SMA, 50SMA > 200SMA -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"lookback": 50, "vol_mult": 1.5, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -18.3% | -8.8% | -21.3% |
| Sharpe | -0.05 | -0.10 | -0.40 |
| Max drawdown | -50.5% | -31.7% | -32.2% |
| Trades | 926 | 506 | 505 |
| Win rate | 46% | 45% | 41% |
| Avg R (after costs) | -0.01 | -0.02 | -0.05 |
| Profit factor | 0.95 | 0.95 | 0.89 |

**Walk-forward:** 11 windows, Sharpe -0.40, return -49.0%, 27% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -23.7%, 95th-percentile -39.6%, worst -54.3%.
**Deflated Sharpe:** 0.22 probability the edge is real after 16 trials.
**2020:** return -16.9%, max DD -28.7%, 178 trades (in-sample).
**2022:** return -30.3%, max DD -30.5%, 167 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -16.9%, max drawdown -28.7%.
- 2022: return -30.3%, max drawdown -30.5%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.22 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.32).

## pullback_reversion — FAIL (9/25)

**Thesis:** Sharp 2-day selloffs in healthy uptrends are forced/emotional selling that reverts within days.
**Who's on the other side:** Panic sellers and stop-loss cascades.

**Rules:** ENTRY: close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 10, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -27.6% | -9.8% | -52.2% |
| Sharpe | -0.40 | -0.22 | -1.82 |
| Max drawdown | -34.5% | -30.1% | -54.5% |
| Trades | 1373 | 868 | 889 |
| Win rate | 59% | 59% | 52% |
| Avg R (after costs) | -0.02 | -0.01 | -0.09 |
| Profit factor | 0.87 | 0.93 | 0.59 |

**Walk-forward:** 11 windows, Sharpe -0.32, return -25.0%, 45% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -19.4%, 95th-percentile -32.7%, worst -44.6%.
**Deflated Sharpe:** 0.15 probability the edge is real after 16 trials.
**2020:** return -9.5%, max DD -28.6%, 245 trades (in-sample).
**2022:** return -17.5%, max DD -21.0%, 231 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -9.5%, max drawdown -28.6%.
- 2022: return -17.5%, max drawdown -21.0%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.15 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.09).

## earnings_drift — FAIL (9/25)

**Thesis:** Strong post-earnings gaps that hold on heavy volume keep drifting as the market under-reacts.
**Who's on the other side:** Slow-to-update holders and analysts; sellers taking quick profits.

**Rules:** ENTRY: on the earnings reaction day, gap up >= 3%, close > open, volume >= 2.0x 50-day avg -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"gap_min": 0.03, "vol_mult": 2.0, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -21.9% | -26.3% | -24.2% |
| Sharpe | -0.36 | -0.90 | -0.75 |
| Max drawdown | -33.0% | -34.2% | -34.6% |
| Trades | 420 | 279 | 249 |
| Win rate | 45% | 42% | 42% |
| Avg R (after costs) | -0.06 | -0.11 | -0.10 |
| Profit factor | 0.83 | 0.77 | 0.74 |

**Walk-forward:** 11 windows, Sharpe -0.58, return -29.2%, 45% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -29.9%, 95th-percentile -44.1%, worst -53.7%.
**Deflated Sharpe:** 0.02 probability the edge is real after 16 trials.
**2020:** return -21.2%, max DD -22.6%, 77 trades (in-sample).
**2022:** return +6.2%, max DD -9.8%, 79 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -21.2%, max drawdown -22.6%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.02 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.15).
