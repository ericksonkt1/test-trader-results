# test-trader-results

Strategist backtests for the Test Trader paper-trading desk. Research only: nothing here places orders.

- `latest.md`: newest report (read by the weekday morning brief)
- `results/YYYY-MM-DD/`: report.md, report.json, out-of-sample trades per strategy
- `strategist/`: the backtester; `config.json`: universe, risk, grids, pass bar
- `.github/workflows/strategist.yml`: runs Sun–Thu ~21:07 PT on GitHub Actions; Actions tab → "Run workflow" for a manual run

Data (prices, earnings dates, universe) lives in the Actions cache, not in git. The universe is today's S&P 400 + 600 members from Wikipedia, so backtests carry survivorship bias (every report says so).

Code test without network: `python -m strategist.run --config config.json --synthetic` (with `DATA_DIR=./data`).
