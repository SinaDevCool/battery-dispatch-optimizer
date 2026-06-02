# Battery Dispatch Optimizer

A Python-based backend and dashboard for grid-scale battery dispatch, forecast-driven arbitrage, asset-level signal generation, Germany market assumptions, and revenue-stack analysis.

## What This Project Does

This project takes electricity price forecasts and converts them into battery charge/discharge recommendations.

It tracks battery state of charge, applies grid and battery constraints, calculates expected PnL, validates dispatch outputs, compares forecast sources, runs scenarios and stress tests, and exposes the results through a FastAPI backend and Streamlit dashboard.

The backend is moving toward a commercial battery optimization product, with support for:

- asset-level battery configuration
- Germany DE-LU market profile assumptions
- ENTSO-E forecast ingestion with local fallback
- rule-based and linear dispatch optimizers
- audit-grade dispatch validation
- regulatory assumption checks
- market product eligibility
- revenue stack estimates

## Current Product Scope

The current implementation focuses on Germany first.

The main supported market profile is:

```text
de_lu_day_ahead
```

The German market profile uses:

```text
15-minute intervals
96 expected intervals per day
DE_LU bidding zone
```

The project currently estimates real day-ahead arbitrage revenue and provides assumption-required placeholders for intraday, reserve capacity, and imbalance products.

## Features

- Asset-level battery configuration
- Client and site configuration
- Grid connection limits
- Commercial cost assumptions
- Battery SOC tracking
- Charge/discharge efficiency
- Minimum SOC constraint
- Max charge/discharge power constraints
- Rule-based dispatch optimizer
- Linear dynamic-programming optimizer
- Daily battery signal generation
- Asset-specific signal storage
- Signal run history
- Dispatch validation
- Forecast upload and validation
- Forecast quality checks
- ENTSO-E next-day forecast retrieval
- Local forecast fallback
- Demo forecast generation
- In-house forecast placeholder
- Forecast profitability comparison
- Scenario analysis
- Price stress testing
- Germany regulatory assumption checks
- Germany market product catalog
- Asset product eligibility checks
- Revenue stack estimates
- Monthly HTML reports
- FastAPI backend
- Streamlit dashboard

## Project Structure

```text
battery-dispatch-optimizer/
+-- dashboard/
|   +-- app.py
|   +-- api_client.py
|   +-- styles.py
|   +-- components/
|   +-- tabs/
+-- data/
|   +-- config/
|   |   +-- assets.json
|   |   +-- client_config.json
|   |   +-- market_profiles.json
|   +-- processed/
|   |   +-- next_day_price_forecast.csv
|   +-- outputs/
|       +-- assets/
|       +-- runs/
|       +-- latest_battery_signal.json
|       +-- portfolio_results.json
|       +-- revenue_stack_results.json
|       +-- scenario_results.json
|       +-- price_stress_results.json
+-- scripts/
+-- src/
|   +-- api/
|   |   +-- main.py
|   |   +-- schemas.py
|   |   +-- routes/
|   +-- assets/
|   +-- backtesting/
|   +-- config/
|   +-- dispatch/
|   +-- features/
|   +-- forecasts/
|   +-- markets/
|   |   +-- products/
|   +-- optimization/
|   +-- optimizer/
|   +-- regulatory/
|   +-- reports/
|   +-- revenue/
|   |   +-- calculators/
|   +-- scenarios/
|   +-- services/
|   +-- signals/
|   +-- validation/
|   +-- workflows/
+-- tests/
+-- requirements.txt
+-- README.md
```

## Backend Architecture

The backend is organized into focused layers.

| Layer | Purpose |
|---|---|
| `src/api/routes/` | FastAPI route modules |
| `src/assets/` | Battery asset schema, asset loading, portfolio dispatch |
| `src/config/` | Central paths and default configs |
| `src/forecasts/` | Forecast loading, ENTSO-E provider, forecast comparison |
| `src/markets/` | Market profile loading and market data helpers |
| `src/markets/products/` | Germany market product catalog and eligibility checks |
| `src/optimization/` | Optimizer registry, rule-based optimizer, linear optimizer |
| `src/regulatory/` | Germany regulatory and commercial assumption checks |
| `src/revenue/` | Revenue stack runner and product revenue calculators |
| `src/services/` | Shared application services |
| `src/signals/` | Signal generation, explanations, risk flags |
| `src/validation/` | Dispatch validation |
| `src/workflows/` | Daily workflow orchestration |

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

If ENTSO-E support is missing, install:

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
python -m uvicorn src.api.main:app --reload --port 8000
```

Open the API documentation:

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

Dashboard tabs:

- Overview
- Forecast
- Signal
- Dispatch
- Scenarios & Stress
- Reports
- Settings

## Run the Product Frontend

The commercial UI is a Next.js frontend in:

```text
frontend/
```

Start it locally:

```bash
cd frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```

The frontend reads the API URL from:

```text
NEXT_PUBLIC_API_BASE_URL
```

For local development, the default API URL is:

```text
http://127.0.0.1:8000
```

For Azure, set:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-backend-app.azurewebsites.net
```

Streamlit is still useful as an internal prototype dashboard, but the Next.js
frontend is the recommended path for a customer-facing product.

## Azure App Service Deployment

The recommended commercial deployment is App Service-first:

```text
Next.js frontend App Service
FastAPI backend App Service
Azure PostgreSQL
Azure Blob Storage
Azure Key Vault
Microsoft Entra ID
Application Insights
```

Deployment notes are in:

```text
docs/azure-app-service.md
```

Backend startup command:

```bash
bash startup.sh
```

Frontend startup command:

```bash
bash startup.sh
```

For backend Azure app settings, copy from:

```text
.env.azure.example
```

For frontend Azure app settings, copy from:

```text
frontend/.env.azure.example
```

## Forecast Input Format

The system expects forecast files with at least:

```csv
timestamp,forecast_price
2026-01-02 00:00:00,35
2026-01-02 00:15:00,32
2026-01-02 00:30:00,28
2026-01-02 00:45:00,25
```

Main forecast path:

```text
data/processed/next_day_price_forecast.csv
```

Optional forecast feature columns:

```csv
timestamp,forecast_price,load_forecast,generation_forecast,forecast_solar,forecast_wind,forecast_renewables_total,forecast_provider,forecast_model
```

For Germany day-ahead mode, a full-day forecast should contain 96 rows at 15-minute resolution.

## Forecast Sources

| Forecast Source | Description |
|---|---|
| `local_saved_forecast` | Current saved CSV forecast |
| `entsoe` | Live ENTSO-E next-day forecast when available |
| `demo` | Generated demo forecast |
| `demo_high_spread` | Demo forecast with stronger price spread |
| `inhouse_placeholder` | Placeholder for a future internal forecast model |
| `uploaded` | User-uploaded forecast CSV |

## Forecast Fallback Logic

The daily workflow first tries ENTSO-E.

If ENTSO-E fails but a saved local forecast exists, the workflow continues with:

```text
local_saved_forecast
```

This allows the dashboard, signal generation, scenarios, and reports to continue working without live market data.

## Optimizers

Available optimizer engines:

| Optimizer | Description |
|---|---|
| `rule_based_v1` | Current rule-based spread dispatch engine |
| `linear_v1` | Discrete SOC dynamic-programming optimizer |

Example:

```bash
curl.exe -X POST "http://127.0.0.1:8000/battery/signal/run-latest?optimizer_engine=linear_v1"
```

## Dispatch Validation

Generated dispatch signals include validation output.

Validation checks:

- SOC stays within battery limits
- charge/discharge energy respects power and timestep limits
- dispatch actions are valid
- dispatch PnL is internally consistent
- summary PnL matches dispatch PnL
- dispatch interval matches market profile assumptions
- required metadata exists

Example validation output:

```json
{
  "status": "warning",
  "errors": [],
  "warnings": [],
  "error_count": 0,
  "warning_count": 1
}
```

## Asset Model

Assets are configured in:

```text
data/config/assets.json
```

Each asset can define:

- client name
- site name
- country
- market
- battery configuration
- strategy configuration
- commercial assumptions
- grid connection limits
- regulatory assumptions
- forecast file
- market profile id

Asset-specific signal results are saved under:

```text
data/outputs/assets/{asset_id}/
```

## Germany Regulatory Assumptions

The Germany regulatory layer checks whether key commercial assumptions are explicit.

It currently tracks:

- MaStR registration status
- MaStR unit id
- grid operator
- balancing responsible party
- metering concept
- technical connection rule
- grid connection limits
- grid fee assumptions
- network tariff model
- construction cost contribution / BKZ assumptions

Example:

```bash
curl.exe http://127.0.0.1:8000/assets/default_site/regulatory/germany
```

## Market Products

The Germany market product catalog currently includes:

| Product | Type |
|---|---|
| `day_ahead_arbitrage` | Energy arbitrage |
| `intraday_arbitrage` | Energy arbitrage |
| `fcr_capacity` | Reserve capacity |
| `afrr_capacity` | Reserve capacity |
| `mfrr_capacity` | Reserve capacity |
| `imbalance_avoidance` | Risk reduction |

Each product defines:

- country
- market
- bidding zone
- settlement interval
- revenue type
- prequalification requirement
- stackability
- minimum power
- minimum duration
- required assumptions
- risk notes

Check asset eligibility:

```bash
curl.exe http://127.0.0.1:8000/assets/default_site/eligible-products
```

## Revenue Stack

The revenue stack estimates product-level revenue for one asset.

Current behavior:

- `day_ahead_arbitrage` uses the dispatch optimizer and returns a real estimated PnL.
- `intraday_arbitrage`, `fcr_capacity`, `afrr_capacity`, `mfrr_capacity`, and `imbalance_avoidance` return explicit `assumption_required` results until the required market inputs are available.

Run revenue stack:

```bash
curl.exe -X POST "http://127.0.0.1:8000/assets/default_site/revenue-stack/run?optimizer_engine=linear_v1"
```

Load latest revenue stack:

```bash
curl.exe http://127.0.0.1:8000/assets/default_site/revenue-stack/latest
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | API health check |
| GET | `/system/health` | System readiness checks |
| GET | `/status` | Project and endpoint status |
| GET | `/data/status` | File availability status |
| POST | `/data/update-entsoe` | Try live ENTSO-E forecast update |
| GET | `/dashboard/summary` | Dashboard summary |
| GET | `/assets` | List configured assets |
| POST | `/assets/{asset_id}/signal/run-latest` | Generate asset-specific signal |
| GET | `/assets/{asset_id}/signal/latest` | Load latest asset signal |
| GET | `/assets/{asset_id}/signal/history` | List asset signal history |
| GET | `/portfolio/latest` | Load latest portfolio results |
| POST | `/portfolio/run-daily` | Run dispatch across configured assets |
| GET | `/markets` | List market profiles |
| GET | `/markets/{market_profile_id}` | Load one market profile |
| GET | `/markets/products` | List market products |
| GET | `/markets/products/{product_id}` | Load one market product |
| GET | `/assets/{asset_id}/eligible-products` | Check product eligibility |
| GET | `/regulatory/germany/requirements` | Germany regulatory checklist |
| GET | `/assets/{asset_id}/regulatory/germany` | Asset regulatory assumptions |
| POST | `/assets/{asset_id}/revenue-stack/run` | Run asset revenue stack |
| GET | `/assets/{asset_id}/revenue-stack/latest` | Load latest asset revenue stack |
| GET | `/client/config` | Load client config |
| POST | `/client/config` | Save client config |
| GET | `/client/presets` | List client presets |
| POST | `/client/presets/{preset_name}/apply` | Apply client preset |
| POST | `/forecast/upload` | Upload forecast data |
| GET | `/forecast/status` | Forecast quality checks |
| GET | `/forecast/preview` | Forecast preview rows |
| GET | `/features/forecast` | Forecast feature summary |
| POST | `/forecast/demo` | Create demo forecast |
| POST | `/forecast/demo-high-spread` | Create high-spread demo forecast |
| POST | `/forecast/inhouse-placeholder` | Create in-house placeholder forecast |
| POST | `/forecasts/compare-profitability` | Compare forecast profitability |
| GET | `/forecasts/compare-profitability/latest` | Load latest forecast comparison |
| GET | `/battery/optimizers` | List optimizer engines |
| GET | `/battery/config` | Default battery and strategy config |
| GET | `/battery/constraints` | Battery constraint summary |
| POST | `/battery/signal` | Generate signal from API payload |
| POST | `/battery/signal/run-latest` | Generate signal from saved forecast |
| GET | `/battery/signal/latest` | Load latest global battery signal |
| GET | `/battery/signal/latest/explanation` | Explain latest signal |
| GET | `/battery/signal/latest/risks` | Risk flags for latest signal |
| GET | `/battery/signal/history` | List global signal run history |
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

Update ENTSO-E forecast:

```bash
curl.exe -X POST http://127.0.0.1:8000/data/update-entsoe
```

Generate latest battery signal:

```bash
curl.exe -X POST "http://127.0.0.1:8000/battery/signal/run-latest?optimizer_engine=linear_v1"
```

Generate asset-specific signal:

```bash
curl.exe -X POST "http://127.0.0.1:8000/assets/default_site/signal/run-latest?optimizer_engine=linear_v1"
```

Run the full daily workflow:

```bash
curl.exe -X POST "http://127.0.0.1:8000/workflow/run-daily?optimizer_engine=linear_v1"
```

Run portfolio dispatch:

```bash
curl.exe -X POST "http://127.0.0.1:8000/portfolio/run-daily?optimizer_engine=linear_v1"
```

Run revenue stack:

```bash
curl.exe -X POST "http://127.0.0.1:8000/assets/default_site/revenue-stack/run?optimizer_engine=linear_v1"
```

## Daily Workflow

The daily workflow:

1. Tries to fetch ENTSO-E forecast data.
2. Falls back to the saved local forecast if ENTSO-E is unavailable.
3. Dispatches the default asset.
4. Adds asset metadata.
5. Adds dispatch validation.
6. Saves global signal output.
7. Saves asset-specific signal output.
8. Runs scenarios.
9. Saves scenario results.

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

Run selected backend tests:

```bash
python -m pytest tests/test_api.py tests/test_optimization.py tests/test_market_products.py tests/test_revenue_stack.py
```

## Dashboard Structure

Dashboard entry point:

```text
dashboard/app.py
```

Dashboard API helper:

```text
dashboard/api_client.py
```

Dashboard styling:

```text
dashboard/styles.py
```

Dashboard tabs:

```text
dashboard/tabs/
```

## Monthly Reports

Monthly reports are generated as standalone HTML files.

Output location:

```text
data/outputs/monthly_report_YYYY-MM.html
```

Report builder:

```text
src/reports/monthly_report.py
```

Reports are intentionally styled separately from the Streamlit dashboard because they are standalone HTML documents.

## Notes

This project is intended for analysis, prototyping, and product development.

It is not a financial trading recommendation.

The backend is becoming a stronger commercial battery optimization platform, but several areas are still placeholders or simplified:

- intraday market execution
- FCR/aFRR/mFRR auction and activation modeling
- imbalance settlement
- forecast-vs-actual backtesting
- advanced degradation modeling
- multi-market co-optimization
- database persistence
- authentication and deployment hardening

## Planned Extensions

- Real intraday price integration
- Reserve capacity price inputs
- Forecast accuracy tracking
- Forecast-vs-actual backtesting
- Multi-market optimization
- More detailed German grid fee treatment
- Portfolio-level revenue stack
- Database-backed history
- Production frontend replacing Streamlit
- User authentication
- Deployment configuration
