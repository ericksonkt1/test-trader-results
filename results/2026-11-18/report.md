# Strategist report — 2026-11-18

- Data: Yahoo Finance via yfinance (adjusted daily bars), 2018-01-02 → 2026-11-17, 984 tickers with usable history, earnings dates for 984
- Insider data (SEC Form 4 data sets): {"status": "SEC data unavailable, strategy skipped", "quarters_missing": 36}
- In-sample: 2018-12-31 → 2024-03-18 · Out-of-sample: 2024-03-19 → 2026-11-17
- Variants tested tonight (counted for deflated Sharpe): 16
- Costs: 15 bps slippage per side, $0 commission · Capital $10,000 · risk 1.0%/trade
- Pass bar: score ≥ 18/25, ≥ 30 OOS trades, positive OOS expectancy, positive under stress

## Ranking (by out-of-sample strength)

| # | Strategy | Score | OOS Sharpe | DSR | OOS trades | Avg R | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | volume_breakout | 9/25 | -0.52 | 0.08 | 511 | -0.07 | FAIL |
| 2 | pullback_reversion | 9/25 | -0.73 | 0.04 | 943 | -0.03 | FAIL |
| 3 | earnings_drift | 9/25 | -0.88 | 0.02 | 278 | -0.11 | FAIL |

## volume_breakout — FAIL (9/25)

**Thesis:** New highs on 1.5x+ volume in an uptrend signal fresh demand.
**Who's on the other side:** Holders selling at 'resistance' and short-term faders.

**Rules:** ENTRY: close > prior 20-day high, volume >= 1.5x 50-day avg, close > 200SMA, 50SMA > 200SMA -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"lookback": 20, "vol_mult": 1.5, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -20.9% | -26.5% | -26.6% |
| Sharpe | -0.06 | -0.52 | -0.52 |
| Max drawdown | -52.4% | -32.5% | -37.8% |
| Trades | 945 | 511 | 514 |
| Win rate | 46% | 42% | 40% |
| Avg R (after costs) | -0.00 | -0.07 | -0.07 |
| Profit factor | 0.95 | 0.83 | 0.84 |

**Walk-forward:** 11 windows, Sharpe -0.42, return -51.6%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -34.6%, 95th-percentile -51.2%, worst -66.9%.
**Deflated Sharpe:** 0.08 probability the edge is real after 16 trials.
**2020:** return -20.8%, max DD -31.2%, 186 trades (in-sample).
**2022:** return -26.0%, max DD -28.3%, 175 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -20.8%, max drawdown -31.2%.
- 2022: return -26.0%, max drawdown -28.3%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.08 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.30).

## pullback_reversion — FAIL (9/25)

**Thesis:** Sharp 2-day selloffs in healthy uptrends are forced/emotional selling that reverts within days.
**Who's on the other side:** Panic sellers and stop-loss cascades.

**Rules:** ENTRY: close > 200SMA and RSI(2) < 5 -> buy-limit next open at <= signal close. STOP: entry - 2.5 x ATR(14). EXIT: close > 5SMA (next open) or after 5 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.5 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"rsi_max": 5, "max_hold": 5, "stop_atr": 2.5}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -28.9% | -24.9% | -52.9% |
| Sharpe | -0.44 | -0.73 | -1.93 |
| Max drawdown | -34.9% | -36.9% | -54.9% |
| Trades | 1502 | 943 | 976 |
| Win rate | 58% | 56% | 51% |
| Avg R (after costs) | -0.02 | -0.03 | -0.09 |
| Profit factor | 0.88 | 0.85 | 0.61 |

**Walk-forward:** 11 windows, Sharpe -0.35, return -26.4%, 36% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -28.8%, 95th-percentile -43.1%, worst -54.2%.
**Deflated Sharpe:** 0.04 probability the edge is real after 16 trials.
**2020:** return -8.9%, max DD -28.1%, 264 trades (in-sample).
**2022:** return -18.3%, max DD -21.6%, 247 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -8.9%, max drawdown -28.1%.
- 2022: return -18.3%, max drawdown -21.6%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.04 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.09).

## earnings_drift — FAIL (9/25)

**Thesis:** Strong post-earnings gaps that hold on heavy volume keep drifting as the market under-reacts.
**Who's on the other side:** Slow-to-update holders and analysts; sellers taking quick profits.

**Rules:** ENTRY: on the earnings reaction day, gap up >= 3%, close > open, volume >= 2.0x 50-day avg -> buy-limit next open at <= signal close +1%. STOP: entry - 2.0 x ATR(14). EXIT: close below 10-day low (next open) or after 10 sessions.

**Sizing:** shares = (equity × 1%) ÷ stop distance (2.0 × ATR14), capped at 25% of equity and available cash. Max 6 open positions.

**Chosen variant (best in-sample):** `{"gap_min": 0.03, "vol_mult": 2.0, "max_hold": 10, "stop_atr": 2.0, "exit_low": 10}`

| | In-sample | Out-of-sample | OOS stress (2× slip, 1 bar late) |
|---|---|---|---|
| Total return | -18.7% | -26.0% | -25.7% |
| Sharpe | -0.29 | -0.88 | -0.81 |
| Max drawdown | -29.3% | -33.8% | -34.6% |
| Trades | 423 | 278 | 251 |
| Win rate | 46% | 41% | 41% |
| Avg R (after costs) | -0.05 | -0.11 | -0.11 |
| Profit factor | 0.87 | 0.76 | 0.72 |

**Walk-forward:** 11 windows, Sharpe -0.41, return -23.0%, 45% of windows profitable.
**Monte Carlo (1,000 resamples of OOS trades):** median drawdown -29.9%, 95th-percentile -44.2%, worst -51.3%.
**Deflated Sharpe:** 0.02 probability the edge is real after 16 trials.
**2020:** return -20.8%, max DD -22.3%, 77 trades (in-sample).
**2022:** return +5.3%, max DD -9.6%, 80 trades (in-sample).
**Market condition that breaks it:** downtrend/high-vol

Score: OOS Sharpe 1 · Deflated Sharpe 1 · Max DD 1 · Trade count 5 · Edge after costs 1 = **9/25**

**WHY THIS COULD FAIL**
- Survivorship bias: the universe is today's index members, so delisted losers are missing and results are flattered.
- Float and market-cap filters aren't applied point in time in the backtest. The live Scout applies them from Robinhood fundamentals.
- Edge disappears with double slippage + one bar late, so it's too fill-sensitive.
- 2020: return -20.8%, max drawdown -22.3%.
- Fewer than 60% of walk-forward windows were profitable.
- Deflated Sharpe 0.02 < 0.95 after counting 16 variants tried, so it could be luck.
- Weakest regime: downtrend/high-vol (avg R -0.16).
