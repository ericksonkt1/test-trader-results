# Strategist report — 2026-11-19

- Data: Yahoo Finance via yfinance (adjusted daily bars), 2018-01-02 → 2026-11-18, 985 tickers with usable history, earnings dates for 985
- Insider data (SEC Form 4 data sets): {"status": "SEC data unavailable, strategy skipped", "quarters_missing": 36}
- In-sample: 2018-12-31 → 2024-03-19 · Out-of-sample: 2024-03-20 → 2026-11-18
- Variants tested tonight (counted for deflated Sharpe): 16
- Costs: 15 bps slippage per side, $0 commission · Capital $10,000 · risk 1.0%/trade
- Pass bar: score ≥ 18/25, ≥ 30 OOS trades, positive OOS expectancy, positive under stress

## Ranking (by out-of-sample strength)

| # | Strategy | Score | OOS Sharpe | DSR | OOS trades | Avg R | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | volume_breakout | 9/25 | -0.15 | 0.21 | 506 | -0.02 | FAIL |
| 2 | pullback_reversion | 9/25 | -0.22 | 0.18 | 858 | -0.01 | FAIL |
| 3 | earnings_drift | 9/25 | -0.85 | 0.02 | 280 | -0.11 | FAIL |

## volume_breakout — FAIL (9/25)

**Thesis:** New highs on 1.5x+ volume in an uptrend signal fresh demand.
**Who's on the other side:** Holders selling at 'resistance' and short-term faders.

**Rules:** ENTRY: close > prior 50-day high, volume >= 1.5x 50-day avg, close > 200SMA, 50SMA > 200SMA -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"lookback": 50, "vol_mult": 1.5, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -20.4% | -11.3% | -25.3% |
| Sharpe | -0.07 | -0.15 | -0.49 |
| Max drawdown | -50.0% | -31.9% | -32.8% |
| Trades | 930 | 506 | 506 |
| Win rate | 46% | 45% | 40% |
| Avg R (after costs) | -0.00 | -0.02 | -0.07 |
| Profit factor | 0.95 | 0.92 | 0.86 |

**Walk-forward:** 11 windows, Sharpe -0.34, return -46.3%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -25.7%, 95th-percentile -43.0%, worst -59.1%.
**Deflated Sharpe:** 0.21 probability the edge is real after 16 trials.
**2020:** return -18.1%, max DD -29.9%, 179 trades (in-sample).
**2022:** return -29.9%, max DD -30.2%, 167 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -18.1%, max drawdown -29.9%.
- 2022: return -29.9%, max drawdown -30.2%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.21 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.29).

## pullback_reversion — FAIL (9/25)

**Thesis:** Sharp 2-day selloffs in healthy uptrends are forced/emotional selling that reverts within days.
**Who's on the other side:** Panic sellers and stop-loss cascades.

**Rules:** ENTRY: close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 10, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -30.8% | -9.7% | -52.9% |
| Sharpe | -0.46 | -0.22 | -1.87 |
| Max drawdown | -36.3% | -30.1% | -54.5% |
| Trades | 1377 | 858 | 888 |
| Win rate | 59% | 59% | 52% |
| Avg R (after costs) | -0.02 | -0.01 | -0.09 |
| Profit factor | 0.86 | 0.94 | 0.59 |

**Walk-forward:** 11 windows, Sharpe -0.35, return -26.3%, 45% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -18.7%, 95th-percentile -32.0%, worst -49.9%.
**Deflated Sharpe:** 0.18 probability the edge is real after 16 trials.
**2020:** return -9.6%, max DD -29.5%, 248 trades (in-sample).
**2022:** return -17.6%, max DD -21.2%, 228 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -9.6%, max drawdown -29.5%.
- 2022: return -17.6%, max drawdown -21.2%.
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
| Total return | -19.6% | -25.1% | -25.3% |
| Sharpe | -0.31 | -0.85 | -0.79 |
| Max drawdown | -29.9% | -33.8% | -35.9% |
| Trades | 423 | 280 | 251 |
| Win rate | 46% | 42% | 42% |
| Avg R (after costs) | -0.05 | -0.11 | -0.11 |
| Profit factor | 0.86 | 0.77 | 0.72 |

**Walk-forward:** 11 windows, Sharpe -0.40, return -22.3%, 45% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -28.5%, 95th-percentile -42.4%, worst -54.5%.
**Deflated Sharpe:** 0.02 probability the edge is real after 16 trials.
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
- Deflated Sharpe 0.02 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.13).
