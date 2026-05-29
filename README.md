# Battery Dispatch Optimizer

A Python-based battery dispatch optimizer for grid-scale battery arbitrage.

## What This Project Does

This project takes hourly electricity price forecasts and converts them into battery charge/discharge signals.

It tracks battery state of charge, calculates simple PnL, runs scenario analysis, and exposes results through a FastAPI backend and Streamlit dashboard.

## Features

- Battery SOC tracking
- Charge and discharge efficiency
- Max charge/discharge power constraints
- Daily battery signal generation
- Historical backtesting
- Scenario analysis
- FastAPI backend
- Streamlit dashboard

## Project Structure

```text
battery-dispatch-optimizer/
├── dashboard/
│   └── app.py
├── data/
│   ├── processed/
│   └── outputs/
├── scripts/
├── src/
│   ├── api/
│   ├── backtesting/
│   ├── config/
│   ├── optimizer/
│   ├── scenarios/
│   └── signals/
├── tests/
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

To fetch ENTSO-E data, set your API token.

PowerShell:

```powershell
$env:ENTSOE_API_KEY="your_entsoe_token_here"
```

## Run the API

```bash
python -m uvicorn src.api.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Run the Dashboard

```bash
python -m streamlit run dashboard/app.py
```

## Forecast Input Format

The system expects a CSV file like this:

```csv
timestamp,forecast_price
2026-01-02 00:00:00,35
2026-01-02 01:00:00,10
2026-01-02 02:00:00,-8
2026-01-02 03:00:00,95
```

Expected path:

```text
data/processed/next_day_price_forecast.csv
```

## API Endpoints

| Method | Endpoint |
|---|---|
| GET | `/health` |
| GET | `/status` |
| POST | `/forecast/upload` |
| POST | `/battery/signal` |
| GET | `/battery/signal/latest` |
| POST | `/battery/backtest` |
| POST | `/scenarios/run` |

## Run Scripts

Daily signal:

```bash
python -m scripts.run_daily_signal
```

Scenario analysis:

```bash
python -m scripts.run_scenarios
```

Historical backtest:

```bash
python -m scripts.run_historical_backtest
```

## Run Tests

```bash
python -m pytest
```

## Notes

This project currently uses a rule-based dispatch engine.

It is intended for analysis, prototyping, and product development. It does not yet include full market execution risk, grid fees, taxes, imbalance costs, degradation modelling, or advanced mathematical optimization.