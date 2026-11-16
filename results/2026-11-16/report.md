# Strategist report — 2026-11-16

- Data: Yahoo Finance via yfinance (adjusted daily bars), 2018-01-02 → 2026-11-13, 985 tickers with usable history, earnings dates for 985
- Insider data (SEC Form 4 data sets): {"status": "SEC data unavailable, strategy skipped", "quarters_missing": 36}
- In-sample: 2018-12-31 → 2024-03-15 · Out-of-sample: 2024-03-18 → 2026-11-13
- Variants tested tonight (counted for deflated Sharpe): 16
- Costs: 15 bps slippage per side, $0 commission · Capital $10,000 · risk 1.0%/trade
- Pass bar: score ≥ 18/25, ≥ 30 OOS trades, positive OOS expectancy, positive under stress

## Ranking (by out-of-sample strength)

| # | Strategy | Score | OOS Sharpe | DSR | OOS trades | Avg R | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | volume_breakout | 10/25 | -0.01 | 0.26 | 503 | -0.01 | FAIL |
| 2 | pullback_reversion | 10/25 | -0.23 | 0.16 | 862 | -0.01 | FAIL |
| 3 | earnings_drift | 9/25 | -0.91 | 0.02 | 278 | -0.11 | FAIL |

## volume_breakout — FAIL (10/25)

**Thesis:** New highs on 1.5x+ volume in an uptrend signal fresh demand.
**Who's on the other side:** Holders selling at 'resistance' and short-term faders.

**Rules:** ENTRY: close > prior 50-day high, volume >= 1.5x 50-day avg, close > 200SMA, 50SMA > 200SMA -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"lookback": 50, "vol_mult": 1.5, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -20.5% | -4.7% | -21.1% |
| Sharpe | -0.07 | -0.01 | -0.39 |
| Max drawdown | -50.0% | -28.4% | -32.2% |
| Trades | 930 | 503 | 505 |
| Win rate | 46% | 45% | 40% |
| Avg R (after costs) | -0.00 | -0.01 | -0.05 |
| Profit factor | 0.95 | 0.95 | 0.89 |

**Walk-forward:** 11 windows, Sharpe -0.43, return -52.0%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -23.2%, 95th-percentile -40.9%, worst -57.4%.
**Deflated Sharpe:** 0.26 probability the edge is real after 16 trials.
**2020:** return -18.1%, max DD -29.9%, 179 trades (in-sample).
**2022:** return -29.9%, max DD -30.2%, 167 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 2 · Trade count 5 · Edge after costs 1 = **10/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -18.1%, max drawdown -29.9%.
- 2022: return -29.9%, max drawdown -30.2%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.26 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.32).

## pullback_reversion — FAIL (10/25)

**Thesis:** Sharp 2-day selloffs in healthy uptrends are forced/emotional selling that reverts within days.
**Who's on the other side:** Panic sellers and stop-loss cascades.

**Rules:** ENTRY: close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 10, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -31.9% | -10.0% | -52.1% |
| Sharpe | -0.48 | -0.23 | -1.83 |
| Max drawdown | -37.4% | -29.3% | -54.5% |
| Trades | 1382 | 862 | 885 |
| Win rate | 59% | 58% | 53% |
| Avg R (after costs) | -0.02 | -0.01 | -0.09 |
| Profit factor | 0.86 | 0.93 | 0.60 |

**Walk-forward:** 11 windows, Sharpe -0.33, return -25.9%, 45% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -19.0%, 95th-percentile -34.1%, worst -49.6%.
**Deflated Sharpe:** 0.16 probability the edge is real after 16 trials.
**2020:** return -9.5%, max DD -28.5%, 247 trades (in-sample).
**2022:** return -17.2%, max DD -21.2%, 232 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 2 · Trade count 5 · Edge after costs 1 = **10/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -9.5%, max drawdown -28.5%.
- 2022: return -17.2%, max drawdown -21.2%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.16 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.09).

## earnings_drift — FAIL (9/25)

**Thesis:** Strong post-earnings gaps that hold on heavy volume keep drifting as the market under-reacts.
**Who's on the other side:** Slow-to-update holders and analysts; sellers taking quick profits.

**Rules:** ENTRY: on the earnings reaction day, gap up >= 3%, close > open, volume >= 2.0x 50-day avg -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"gap_min": 0.03, "vol_mult": 2.0, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -22.6% | -26.6% | -24.7% |
| Sharpe | -0.37 | -0.91 | -0.77 |
| Max drawdown | -33.0% | -34.2% | -34.5% |
| Trades | 421 | 278 | 252 |
| Win rate | 45% | 42% | 42% |
| Avg R (after costs) | -0.06 | -0.11 | -0.10 |
| Profit factor | 0.83 | 0.76 | 0.74 |

**Walk-forward:** 11 windows, Sharpe -0.58, return -29.2%, 45% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -30.3%, 95th-percentile -44.7%, worst -51.4%.
**Deflated Sharpe:** 0.02 probability the edge is real after 16 trials.
**2020:** return -21.2%, max DD -22.7%, 77 trades (in-sample).
**2022:** return +6.1%, max DD -9.8%, 79 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -21.2%, max drawdown -22.7%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.02 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.17).
