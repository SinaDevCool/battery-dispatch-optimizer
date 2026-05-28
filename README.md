
# Battery Dispatch Optimizer

A simple battery dispatch optimizer for grid-scale battery arbitrage.

The project takes hourly electricity price forecasts, creates a charge/discharge schedule, tracks battery state of charge, calculates simple PnL, runs scenario analysis, and exposes the results through a FastAPI backend and Streamlit dashboard.

## Features

- Battery SOC tracking
- Charge and discharge efficiency
- Max charge/discharge power constraints
- Simple PnL calculation
- Daily battery signal generation
- Historical backtesting
- Scenario analysis for different battery sizes
- Forecast CSV upload
- Streamlit dashboard
- FastAPI backend
- Monthly HTML report support

## Project Structure

```text
battery dispatch optimizer/
  dashboard/
    app.py
  data/
    config/
      client_config.json
    processed/
      next_day_price_forecast.csv
    outputs/
      latest_battery_signal.json
      scenario_results.json
  scripts/
    run_daily_signal.py
    run_scenarios.py
    run_historical_backtest.py
    run_monthly_report.py
  src/
    api/
      main.py
      schemas.py
    backtesting/
      backtester.py
      historical_backtest.py
      metrics.py
    config/
      battery_config.py
      client_config.py
      market_config.py
    optimizer/
      battery_optimizer.py
      dispatch_strategy.py
    scenarios/
      scenario_runner.py
    signals/
      signal_engine.py
  tests/
    test_api.py
    test_battery_optimizer.py
Installation
pip install -r requirements.txt
Run the API
python -m uvicorn src.api.main:app --reload
Open:

http://127.0.0.1:8000/docs
Run the Dashboard
In a second terminal:

python -m streamlit run dashboard/app.py
Forecast Input Format
The dashboard and backend expect a CSV like:

timestamp,forecast_price
2026-01-02 00:00:00,35
2026-01-02 01:00:00,10
2026-01-02 02:00:00,-8
2026-01-02 03:00:00,95
2026-01-02 04:00:00,130
Expected path:

data/processed/next_day_price_forecast.csv
Main API Endpoints
GET  /health
GET  /status
GET  /data/status
GET  /client/config
POST /client/config
POST /forecast/upload
GET  /battery/config
POST /battery/signal
POST /battery/signal/run-latest
GET  /battery/signal/latest
POST /battery/backtest
POST /scenarios/run
POST /scenarios/run-latest
GET  /scenarios/latest
GET  /reports/monthly/latest
GET  /reports/monthly/latest/view
Run Daily Signal from Terminal
python -m scripts.run_daily_signal
Run Scenario Analysis from Terminal
python -m scripts.run_scenarios
Run Historical Backtest
python -m scripts.run_historical_backtest
Run Tests
python -m pytest
Notes
This project currently uses a simple rule-based dispatch engine. It is intended for analysis, prototyping, and product development.

It is not financial trading advice and does not yet include full market execution risk, grid fees, taxes, imbalance costs, degradation modeling, or advanced mathematical optimization.
```