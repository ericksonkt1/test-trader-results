# Strategist report — 2026-11-17

- Data: Yahoo Finance via yfinance (adjusted daily bars), 2018-01-02 → 2026-11-16, 985 tickers with usable history, earnings dates for 985
- Insider data (SEC Form 4 data sets): {"status": "SEC data unavailable, strategy skipped", "quarters_missing": 36}
- In-sample: 2018-12-31 → 2024-03-15 · Out-of-sample: 2024-03-18 → 2026-11-16
- Variants tested tonight (counted for deflated Sharpe): 16
- Costs: 15 bps slippage per side, $0 commission · Capital $10,000 · risk 1.0%/trade
- Pass bar: score ≥ 18/25, ≥ 30 OOS trades, positive OOS expectancy, positive under stress

## Ranking (by out-of-sample strength)

| # | Strategy | Score | OOS Sharpe | DSR | OOS trades | Avg R | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | volume_breakout | 11/25 | 0.04 | 0.29 | 503 | -0.01 | FAIL |
| 2 | pullback_reversion | 10/25 | -0.18 | 0.18 | 863 | -0.01 | FAIL |
| 3 | earnings_drift | 9/25 | -0.89 | 0.02 | 278 | -0.11 | FAIL |

## volume_breakout — FAIL (11/25)

**Thesis:** New highs on 1.5x+ volume in an uptrend signal fresh demand.
**Who's on the other side:** Holders selling at 'resistance' and short-term faders.

**Rules:** ENTRY: close > prior 50-day high, volume >= 1.5x 50-day avg, close > 200SMA, 50SMA > 200SMA -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"lookback": 50, "vol_mult": 1.5, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -20.6% | -2.7% | -20.9% |
| Sharpe | -0.07 | 0.04 | -0.38 |
| Max drawdown | -50.0% | -30.0% | -33.0% |
| Trades | 930 | 503 | 506 |
| Win rate | 46% | 45% | 41% |
| Avg R (after costs) | -0.00 | -0.01 | -0.05 |
| Profit factor | 0.95 | 0.96 | 0.89 |

**Walk-forward:** 11 windows, Sharpe -0.43, return -52.3%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -23.0%, 95th-percentile -41.2%, worst -51.4%.
**Deflated Sharpe:** 0.29 probability the edge is real after 16 trials.
**2020:** return -18.1%, max DD -29.9%, 179 trades (in-sample).
**2022:** return -29.9%, max DD -30.2%, 167 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 2 · Deflated Sharpe 1 · Max DD 2 · Trade count 5 · Edge after costs 1 = **11/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -18.1%, max drawdown -29.9%.
- 2022: return -29.9%, max drawdown -30.2%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.29 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.32).

## pullback_reversion — FAIL (10/25)

**Thesis:** Sharp 2-day selloffs in healthy uptrends are forced/emotional selling that reverts within days.
**Who's on the other side:** Panic sellers and stop-loss cascades.

**Rules:** ENTRY: close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 10, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -28.0% | -8.7% | -51.9% |
| Sharpe | -0.41 | -0.18 | -1.81 |
| Max drawdown | -34.3% | -29.3% | -54.3% |
| Trades | 1379 | 863 | 883 |
| Win rate | 59% | 59% | 52% |
| Avg R (after costs) | -0.02 | -0.01 | -0.09 |
| Profit factor | 0.87 | 0.94 | 0.60 |

**Walk-forward:** 11 windows, Sharpe -0.32, return -24.9%, 55% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -18.7%, 95th-percentile -32.2%, worst -49.7%.
**Deflated Sharpe:** 0.18 probability the edge is real after 16 trials.
**2020:** return -9.4%, max DD -29.0%, 248 trades (in-sample).
**2022:** return -16.9%, max DD -20.9%, 230 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 2 · Trade count 5 · Edge after costs 1 = **10/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -9.4%, max drawdown -29.0%.
- 2022: return -16.9%, max drawdown -20.9%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.18 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.08).

## earnings_drift — FAIL (9/25)

**Thesis:** Strong post-earnings gaps that hold on heavy volume keep drifting as the market under-reacts.
**Who's on the other side:** Slow-to-update holders and analysts; sellers taking quick profits.

**Rules:** ENTRY: on the earnings reaction day, gap up >= 3%, close > open, volume >= 2.0x 50-day avg -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"gap_min": 0.03, "vol_mult": 2.0, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -20.1% | -26.1% | -25.3% |
| Sharpe | -0.32 | -0.89 | -0.79 |
| Max drawdown | -31.2% | -33.8% | -34.6% |
| Trades | 423 | 278 | 252 |
| Win rate | 46% | 41% | 42% |
| Avg R (after costs) | -0.05 | -0.11 | -0.11 |
| Profit factor | 0.85 | 0.76 | 0.73 |

**Walk-forward:** 11 windows, Sharpe -0.51, return -27.4%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -29.9%, 95th-percentile -44.1%, worst -51.0%.
**Deflated Sharpe:** 0.02 probability the edge is real after 16 trials.
**2020:** return -21.4%, max DD -23.0%, 78 trades (in-sample).
**2022:** return +6.3%, max DD -9.7%, 79 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -21.4%, max drawdown -23.0%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.02 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.17).
