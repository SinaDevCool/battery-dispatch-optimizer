# Battery Dispatch Optimizer

A simple Python project for battery dispatch backtesting, market signals, and future API/MCP integration.

The project started from Google Colab notebooks using Netztransparenz market data and is being converted into a reusable Python backend.

## What It Does

- Loads electricity price data
- Tracks battery state of charge
- Applies charge/discharge efficiency
- Applies max charge/discharge power limits
- Calculates simple PnL
- Generates battery dispatch signals
- Provides a FastAPI endpoint for battery signals

## Project Structure

```text
data/
  raw/
  processed/
  outputs/

src/
  api/
  backtesting/
  config/
  features/
  markets/
  optimizer/
  reports/
  signals/

scripts/
  run_backtest.py
  run_daily_signal.py
  update_data.py