# Strategist report — 2026-11-09

- Data: Yahoo Finance via yfinance (adjusted daily bars), 2018-01-02 → 2026-11-06, 985 tickers with usable history, earnings dates for 985
- Insider data (SEC Form 4 data sets): {"status": "SEC data unavailable, strategy skipped", "quarters_missing": 36}
- In-sample: 2018-12-31 → 2024-03-11 · Out-of-sample: 2024-03-12 → 2026-11-06
- Variants tested tonight (counted for deflated Sharpe): 16
- Costs: 15 bps slippage per side, $0 commission · Capital $10,000 · risk 1.0%/trade
- Pass bar: score ≥ 18/25, ≥ 30 OOS trades, positive OOS expectancy, positive under stress

## Ranking (by out-of-sample strength)

| # | Strategy | Score | OOS Sharpe | DSR | OOS trades | Avg R | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | pullback_reversion | 10/25 | -0.28 | 0.13 | 866 | -0.01 | FAIL |
| 2 | volume_breakout | 9/25 | -0.23 | 0.17 | 504 | -0.03 | FAIL |
| 3 | earnings_drift | 9/25 | -0.97 | 0.02 | 277 | -0.11 | FAIL |

## pullback_reversion — FAIL (10/25)

**Thesis:** Sharp 2-day selloffs in healthy uptrends are forced/emotional selling that reverts within days.
**Who's on the other side:** Panic sellers and stop-loss cascades.

**Rules:** ENTRY: close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 10, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -26.3% | -11.7% | -55.2% |
| Sharpe | -0.38 | -0.28 | -1.98 |
| Max drawdown | -35.1% | -28.9% | -55.4% |
| Trades | 1377 | 866 | 883 |
| Win rate | 59% | 59% | 52% |
| Avg R (after costs) | -0.02 | -0.01 | -0.10 |
| Profit factor | 0.87 | 0.93 | 0.58 |

**Walk-forward:** 11 windows, Sharpe -0.35, return -26.4%, 45% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -18.8%, 95th-percentile -32.6%, worst -49.2%.
**Deflated Sharpe:** 0.13 probability the edge is real after 16 trials.
**2020:** return -9.3%, max DD -28.5%, 245 trades (in-sample).
**2022:** return -17.4%, max DD -21.3%, 229 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 2 · Trade count 5 · Edge after costs 1 = **10/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -9.3%, max drawdown -28.5%.
- 2022: return -17.4%, max drawdown -21.3%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.13 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.09).

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
**Deflated Sharpe:** 0.17 probability the edge is real after 16 trials.
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
- Deflated Sharpe 0.17 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.34).

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
**Deflated Sharpe:** 0.02 probability the edge is real after 16 trials.
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
- Deflated Sharpe 0.02 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.17).
