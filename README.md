# Battery Dispatch Optimizer

A Python-based battery dispatch optimizer for grid-scale battery arbitrage, forecast comparison, scenario analysis, stress testing, and reporting.

## What This Project Does

This project takes hourly electricity price forecasts and converts them into battery charge/discharge signals.

It tracks battery state of charge, applies charge/discharge efficiency, includes battery and commercial constraints, calculates expected PnL, compares forecast sources, runs scenario analysis, runs price stress tests, and exposes results through a FastAPI backend and Streamlit dashboard.

The product can work in two modes:

- Live forecast mode using ENTSO-E data when an API token and connection are available.
- Local forecast mode using saved, uploaded, demo, or in-house placeholder forecast files.

If ENTSO-E is unavailable, the system can fall back to the saved local forecast so the workflow still runs.

## Features

- Battery SOC tracking
- Charge and discharge efficiency
- Minimum SOC constraint
- Max charge/discharge power constraints
- Commercial cost assumptions
- Degradation cost assumptions
- Daily battery signal generation
- Forecast upload and validation
- Forecast quality checks
- ENTSO-E next-day forecast retrieval
- Local fallback when ENTSO-E is unavailable
- Demo forecast generation
- High-spread demo forecast generation
- In-house forecast placeholder provider
- Forecast profitability comparison
- Scenario analysis across battery sizes
- Price stress testing
- Signal explanation engine
- Risk flag engine
- Signal run history
- Monthly HTML report generation
- FastAPI backend
- Streamlit dashboard
- Dashboard tabs for overview, forecast, signal, dispatch, scenarios, reports, and settings
- Centralized dashboard styling

## Project Structure

```text
battery-dispatch-optimizer/
├── dashboard/
│   ├── app.py
│   ├── api_client.py
│   ├── styles.py
│   ├── components/
│   │   ├── __init__.py
│   │   └── status_strip.py
│   └── tabs/
│       ├── __init__.py
│       ├── overview.py
│       ├── forecast.py
│       ├── signal.py
│       ├── dispatch.py
│       ├── scenarios.py
│       ├── reports.py
│       └── settings.py
├── data/
│   ├── config/
│   │   └── client_config.json
│   ├── processed/
│   │   ├── next_day_price_forecast.csv
│   │   ├── demo_high_spread_forecast.csv
│   │   └── inhouse_placeholder_forecast.csv
│   └── outputs/
│       ├── latest_battery_signal.json
│       ├── scenario_results.json
│       ├── price_stress_results.json
│       ├── forecast_profitability_comparison.json
│       ├── monthly_report_YYYY-MM.html
│       └── runs/
├── scripts/
│   ├── run_daily_signal.py
│   ├── run_scenarios.py
│   ├── run_historical_backtest.py
│   ├── run_monthly_report.py
│   └── update_data.py
├── src/
│   ├── api/
│   │   ├── main.py
│   │   └── schemas.py
│   ├── backtesting/
│   │   ├── backtester.py
│   │   ├── historical_backtest.py
│   │   └── metrics.py
│   ├── config/
│   │   ├── battery_config.py
│   │   ├── client_config.py
│   │   ├── client_presets.py
│   │   ├── commercial_config.py
│   │   ├── market_config.py
│   │   └── paths.py
│   ├── dispatch/
│   │   └── dispatch_agent.py
│   ├── features/
│   │   ├── battery_usage_features.py
│   │   ├── forecast_quality_features.py
│   │   ├── market_features.py
│   │   ├── negative_price_features.py
│   │   └── renewable_features.py
│   ├── forecasts/
│   │   ├── entsoe_forecast_provider.py
│   │   ├── forecast_comparison.py
│   │   ├── forecast_loader.py
│   │   ├── forecast_registry.py
│   │   ├── forecast_schema.py
│   │   └── inhouse_forecast_provider.py
│   ├── markets/
│   │   ├── data_cleaning.py
│   │   ├── data_loader.py
│   │   ├── entsoe_client.py
│   │   └── netztransparenz_client.py
│   ├── optimizer/
│   │   ├── battery_optimizer.py
│   │   └── dispatch_strategy.py
│   ├── reports/
│   │   └── monthly_report.py
│   ├── scenarios/
│   │   ├── scenario_runner.py
│   │   └── stress_runner.py
│   └── signals/
│       ├── explanation_engine.py
│       ├── risk_engine.py
│       └── signal_engine.py
├── tests/
├── requirements.txt
└── README.md
```

## Installation

Install the project dependencies:

```bash
pip install -r requirements.txt
```

If ENTSO-E support is not already installed, install:

```bash
pip install entsoe-py beautifulsoup4 python-dotenv
```

## Environment Variables

To fetch ENTSO-E data, set an ENTSO-E API token.

Recommended local setup: create a `.env` file in the project root.

```env
ENTSOE_API_KEY=your_entsoe_token_here
```

Make sure `.env` is included in `.gitignore`:

```gitignore
.env
```

PowerShell alternative:

```powershell
$env:ENTSOE_API_KEY="your_entsoe_token_here"
```

The product can still run without an ENTSO-E token by using local, uploaded, demo, or placeholder forecasts.

## Run the API

Start the FastAPI backend:

```bash
python -m uvicorn src.api.main:app --reload
```

Then open the API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Run the Dashboard

Open a second terminal and run:

```bash
python -m streamlit run dashboard/app.py
```

Then open:

```text
http://localhost:8501
```

The dashboard is organized into these tabs:

- Overview
- Forecast
- Signal
- Dispatch
- Scenarios & Stress
- Reports
- Settings

## Forecast Input Format

The system expects forecast files with at least these columns:

```csv
timestamp,forecast_price
2026-01-02 00:00:00,35
2026-01-02 01:00:00,10
2026-01-02 02:00:00,-8
2026-01-02 03:00:00,95
```

Main forecast path:

```text
data/processed/next_day_price_forecast.csv
```

Optional forecast feature columns:

```csv
timestamp,forecast_price,load_forecast,generation_forecast,forecast_solar,forecast_wind,forecast_renewables_total,forecast_provider,forecast_model
```

## Forecast Sources

The product supports multiple forecast sources.

| Forecast Source | Description |
|---|---|
| `local_saved_forecast` | Current saved CSV forecast |
| `entsoe` | Live ENTSO-E next-day forecast when available |
| `demo` | Basic generated demo forecast |
| `demo_high_spread` | Demo forecast with stronger price spread |
| `inhouse_placeholder` | Placeholder for a future internal forecast model |
| `uploaded` | User-uploaded forecast CSV |

## Forecast Fallback Logic

The daily workflow first tries to use ENTSO-E.

If ENTSO-E fails but a saved local forecast exists, the workflow continues with:

```text
local_saved_forecast
```

This allows the dashboard, signal generation, scenarios, and reports to continue working without live market data.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | API health check |
| GET | `/system/health` | System readiness checks |
| GET | `/status` | Project and endpoint status |
| GET | `/data/status` | File availability status |
| POST | `/data/update-entsoe` | Try live ENTSO-E forecast update |
| GET | `/dashboard/summary` | Dashboard summary |
| GET | `/client/config` | Load client config |
| POST | `/client/config` | Save client config |
| GET | `/client/presets` | List client presets |
| POST | `/client/presets/{preset_name}/apply` | Apply client preset |
| POST | `/forecast/upload` | Upload forecast data |
| GET | `/forecast/status` | Forecast quality checks |
| GET | `/forecast/preview` | Forecast preview rows |
| GET | `/features/forecast` | Forecast feature summary |
| POST | `/forecast/demo` | Create base demo forecast |
| POST | `/forecast/demo-high-spread` | Create high-spread demo forecast |
| POST | `/forecast/inhouse-placeholder` | Create in-house placeholder forecast |
| POST | `/forecasts/compare-profitability` | Compare forecast profitability |
| GET | `/forecasts/compare-profitability/latest` | Load latest forecast comparison |
| GET | `/battery/config` | Default battery and strategy config |
| GET | `/battery/constraints` | Battery constraint summary |
| POST | `/battery/signal` | Generate signal from API payload |
| POST | `/battery/signal/run-latest` | Generate signal from saved forecast |
| GET | `/battery/signal/latest` | Load latest battery signal |
| GET | `/battery/signal/latest/explanation` | Explain latest signal |
| GET | `/battery/signal/latest/risks` | Risk flags for latest signal |
| GET | `/battery/signal/history` | List signal run history |
| GET | `/battery/signal/history/{file_name}` | Load historical signal run |
| POST | `/battery/backtest` | Backtest battery signal |
| POST | `/scenarios/run` | Run scenarios from request data |
| POST | `/scenarios/run-latest` | Run scenarios from saved forecast |
| GET | `/scenarios/latest` | Load latest scenario results |
| POST | `/stress/run-latest` | Run price stress tests |
| GET | `/stress/latest` | Load latest stress results |
| GET | `/reports/monthly/latest` | Latest monthly report status |
| GET | `/reports/monthly/latest/view` | View latest monthly report |
| POST | `/workflow/run-daily` | Full daily workflow |

## Common Workflows

Create a demo forecast:

```bash
curl.exe -X POST http://127.0.0.1:8000/forecast/demo
```

Create a high-spread demo forecast:

```bash
curl.exe -X POST http://127.0.0.1:8000/forecast/demo-high-spread
```

Create an in-house placeholder forecast:

```bash
curl.exe -X POST http://127.0.0.1:8000/forecast/inhouse-placeholder
```

Run forecast profitability comparison:

```bash
curl.exe -X POST http://127.0.0.1:8000/forecasts/compare-profitability
```

View latest forecast profitability comparison:

```bash
curl.exe http://127.0.0.1:8000/forecasts/compare-profitability/latest
```

Run the full daily workflow:

```bash
curl.exe -X POST http://127.0.0.1:8000/workflow/run-daily
```

The daily workflow will:

1. Try ENTSO-E forecast update.
2. Fall back to saved local forecast if ENTSO-E fails.
3. Generate a battery signal.
4. Save the latest signal.
5. Save run history.
6. Run scenarios.
7. Save scenario results.

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

Monthly report:

```bash
python -m scripts.run_monthly_report
```

Data update:

```bash
python -m scripts.update_data
```

## Run Tests

Run all tests:

```bash
python -m pytest
```

Run a specific test file:

```bash
python -m pytest tests/test_api.py
```

## Dashboard Structure

The dashboard entry point is:

```text
dashboard/app.py
```

Dashboard API helper functions are defined in:

```text
dashboard/api_client.py
```

Dashboard styling is centralized in:

```text
dashboard/styles.py
```

Reusable dashboard components are stored in:

```text
dashboard/components/
```

Dashboard tabs are stored in:

```text
dashboard/tabs/
```

## Monthly Reports

Monthly reports are generated as standalone HTML files.

Output location:

```text
data/outputs/monthly_report_YYYY-MM.html
```

The report builder is located at:

```text
src/reports/monthly_report.py
```

Reports are intentionally styled separately from the Streamlit dashboard because they are standalone HTML documents.

## Notes

This project currently uses a rule-based dispatch engine.

It is intended for analysis, prototyping, and product development. It is not a financial trading recommendation.

The current optimizer does not yet include full market execution risk, imbalance settlement, auction bidding logic, advanced degradation modelling, or mathematical optimization across multiple markets.

Planned extensions include:

- Real in-house forecast model integration
- Forecast model accuracy tracking
- Forecast-vs-actual backtesting
- Multi-market optimization
- More detailed degradation modelling
- Automated report archive
- User authentication
- Deployment configuration