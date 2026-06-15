# Battery Trader AI

Battery Trader AI is a battery trading intelligence platform for grid-scale storage assets. It combines forecasting, dispatch optimization, revenue assurance, market-route readiness, automation control, settlement evidence, audit evidence, and persona-specific workflows into one product.

The current product direction is not only "optimize a battery schedule." It is a two-layer operating system:

- **Client Evidence Portal**: business-facing evidence for asset owners, investors, project developers, executives, and client success teams.
- **Internal Trading OS**: operational tooling for trading desks, automation operators, risk/compliance, market operations, forecast/quants, and revenue analysts.

The strategic goal is to compete with enterprise battery trading platforms such as Entrix or Fluence by focusing on a sharper wedge: explainable automated trading, defensible business evidence, and auditable decision workflows from forecast to settlement.

## What The Product Does

Battery Trader AI turns asset configuration, price forecasts, market rules, regulatory assumptions, commercial assumptions, telemetry, execution evidence, settlement feedback, and audit records into a controlled battery trading workflow.

The platform can:

- load grid-scale battery assets and commercial assumptions
- ingest or generate electricity price forecasts
- run rule-based or linear dispatch optimization
- validate dispatch schedules against battery and market constraints
- estimate revenue stacks across German market products
- evaluate hedging, scenarios, and downside protection
- check German regulatory and market-rule assumptions
- rank market routes across EPEX and regelleistung readiness
- build pre-trade bid proposals
- run paper trading and simulated market submission
- manage automation policy, human gates, and remediation queues
- reconcile expected, paper, and realized settlement economics
- expose audit evidence for automated decisions
- generate client-facing monthly HTML reports
- adapt navigation and page framing by persona

The system is intentionally gated. Live automation is not treated as a single button. A trade must pass forecast trust, market eligibility, connector readiness, risk policy, paper validation, human approval, settlement evidence, and audit checks before it can be described as production-ready.

## Current Scope

The product is Germany-first.

Primary market profile:

```text
de_lu_day_ahead
```

Current German assumptions:

```text
DE-LU bidding zone
15-minute intervals
96 intervals per day
```

The strongest implemented economics are day-ahead arbitrage and dispatch-derived revenue. EPEX intraday, FCR, aFRR, mFRR, imbalance, and live market connector paths exist as explicit readiness, proposal, paper-trading, or placeholder layers where required data or real submission integrations are not yet available.

## Product Layers

### Client Evidence Portal

This layer answers: "Can a commercial stakeholder trust, fund, explain, or approve the asset strategy?"

Client-facing personas:

| Persona | Default page | Main decision |
|---|---:|---|
| Asset owner | Revenue Assurance | Is the asset creating defensible owner value? |
| Investor / lender | Hedging | Is the revenue bankable and downside protected? |
| Project developer | Scenario Lab | Is the project commercially and technically ready? |
| Executive | Control Room | What is the value, maturity, and top blocker? |
| Client success | Reports | What can we explain and deliver to the client? |

Client-facing pages emphasize business value, proof completeness, next actions, revenue certainty, settlement explanation, auditability, and report readiness.

### Internal Trading OS

This layer answers: "Can the team operate, route, automate, approve, and improve trading decisions?"

Internal personas:

| Persona | Default page | Main decision |
|---|---:|---|
| Trading desk | Mission Control | What should be traded, routed, validated, or held? |
| Automation operator | Automation Control | Can automation safely escalate? |
| Risk & compliance | Automation Gates | Can this decision be approved and defended? |
| Market operations | Market Access & Data | Which routes, credentials, and handshakes are production-ready? |
| Forecast / quant | Forecast Trust | Can the model output be trusted? |
| Revenue analyst | Revenue Assurance | What revenue assumptions should change? |

Internal pages keep backend details visible where useful: route status, adapter readiness, forecast confidence, remediation queue, approval state, paper fills, submission lifecycle, and event history.

## Frontend Architecture

The commercial UI is a Next.js application in `frontend/`.

Core frontend concepts:

- `frontend/src/lib/personas.ts` defines persona IDs, layers, default pages, visible navigation, and priorities.
- `frontend/src/lib/navigation.ts` defines the navigation groups and routes.
- `frontend/src/components/app-shell.tsx` applies persona-aware navigation and the current lens indicator.
- `frontend/src/components/persona-selector.tsx` is the single persona switcher.
- `frontend/src/app/*/page.tsx` contains route-level product pages.
- Shared components such as `DecisionBrief`, `SectionCard`, `KpiCard`, `DataTable`, and `StatusPill` keep each page decision-first.

Primary navigation groups:

| Group | Purpose |
|---|---|
| Portfolio | Control room, assets, decision evidence, revenue assurance, reports |
| Market Intelligence | Forecasts, market prices, signals, and rules |
| Optimization | Dispatch schedule, scenario lab, hedging |
| Automated Trading | Automation control, orchestrator, mission control |
| Risk & Compliance | Automation gates, regulation, settlement, audit, reports, settings |

Current frontend routes:

```text
/
/assets
/intelligence
/revenue
/reports
/forecasts
/market-prices
/market-signals
/market-rules
/dispatch
/scenarios
/hedging
/execution/automation-policies
/execution/orchestrator
/execution
/execution/market-allocation
/execution/proposals
/execution/simulation
/execution/market-connectors
/execution/risk-approval
/execution/settlement
/execution/audit
/regulation
/settings
```

## Backend Architecture

The backend is a FastAPI application in `backend/api/main.py`. Route modules are registered through `backend/api/routes/__init__.py`.

Major backend areas:

| Area | Purpose |
|---|---|
| `backend/api/routes/` | FastAPI HTTP API modules |
| `backend/assets/` | Asset loading, asset schema, portfolio dispatch |
| `backend/backtesting/` | Forecast-vs-actual and historical analysis support |
| `backend/config/` | Paths, app settings, client presets, market config |
| `backend/db/` | SQLite database setup and repository layer |
| `backend/dispatch/` | Dispatch and battery schedule utilities |
| `backend/execution/` | Automation control, market routing, proposals, paper trading, connectors, gates, remediation, submission lifecycle |
| `backend/forecasts/` | Forecast loading, upload, ENTSO-E provider, comparison |
| `backend/markets/` | Market profiles, products, and market data helpers |
| `backend/optimization/` | Optimizer registry and optimization engines |
| `backend/regulatory/` | Germany regulatory and operating assumption checks |
| `backend/reports/` | Monthly client report generation |
| `backend/revenue/` | Revenue stack runner and revenue calculators |
| `backend/scenarios/` | Scenario and stress-test logic |
| `backend/services/` | Shared services and persistence helpers |
| `backend/settlement/` | Settlement variance and reconciliation logic |
| `backend/signals/` | Signal generation, explanations, and risk flags |
| `backend/telemetry/` | Asset telemetry snapshots |
| `backend/validation/` | Dispatch validation |
| `backend/workflows/` | Daily workflow orchestration |

Optimizer implementations now live under `backend/optimization/`. The old
`backend/optimizer/` package remains only as a compatibility shim for older callers;
new code should import from `backend.optimization`.

## Repository Layout

The active application surfaces are:

```text
backend/     FastAPI backend, domain services, execution control, persistence
frontend/     Next.js commercial frontend
```

Supporting and transitional areas are:

```text
archive/streamlit_dashboard/
              archived Streamlit dashboard for internal prototyping
archive/manual_scripts/
              archived manual CLI utilities for local workflow checks
tests/        backend test suite
docs/         deployment and operating notes
data/config/  checked-in local seed configuration
```

Runtime/local artifacts are intentionally kept separate from seed
configuration:

```text
data/raw/
data/processed/
data/outputs/
data/db/
```

These runtime folders are ignored for source control and should map to managed
storage/database services in production.

### Execution Control Plane

The most important backend subsystem for the current product is `backend/execution/`.

It includes:

- automation policy and mode evaluation
- automation guardrails
- remediation queue and next-action orchestration
- market connector readiness
- official API compliance evidence
- live adapter handshake readiness
- multi-market allocation
- route automation certification
- bid package building
- pre-trade proposal generation
- paper trading and simulated award logic
- market submission lifecycle
- human approval workflow
- settlement and audit linkage

This is what makes the product more than an analytics dashboard: it models whether a trading decision can move from signal to proposal, paper validation, approval, submission evidence, settlement, and audit.

## Data And Persistence

Main data directories:

```text
data/config/      asset, client, and market configuration
data/processed/   forecast and actual-price CSV inputs
data/outputs/     generated signals, reports, scenario outputs, revenue outputs
data/db/          local SQLite database
```

Default SQLite database:

```text
data/db/battery_dispatch_optimizer.sqlite
```

Repository modules live under:

```text
backend/db/repositories/
```

The app still uses a hybrid persistence model: file outputs for some artifacts and SQLite repositories for asset, forecast, signal, revenue, execution, telemetry, settlement, workflow, and official API evidence records.

## Key API Categories

The API surface is broad. The most important categories are:

| Category | Example endpoints |
|---|---|
| Health and system readiness | `/health`, `/system/health`, `/system/persistence-readiness` |
| Assets | `/assets`, `/assets/{asset_id}/cockpit`, `/assets/{asset_id}/data-completeness` |
| Forecasts | `/forecast/upload`, `/forecast/status`, `/forecast/demo`, `/forecasts/compare-profitability` |
| Signals and dispatch | `/assets/{asset_id}/signal/run-latest`, `/assets/{asset_id}/signal/latest`, `/battery/optimizers` |
| Markets and products | `/markets`, `/markets/products`, `/assets/{asset_id}/eligible-products` |
| Revenue and hedging | `/assets/{asset_id}/revenue-stack/run`, `/assets/{asset_id}/revenue-stack/latest`, hedging-related asset routes |
| Regulation | `/regulatory/germany/requirements`, `/assets/{asset_id}/regulatory/germany` |
| Execution control | `/assets/{asset_id}/execution/automation-control/status`, `/assets/{asset_id}/execution/orchestrator/run` |
| Market allocation | `/assets/{asset_id}/execution/multi-market/allocation` |
| Proposals | `/assets/{asset_id}/execution/proposal/build`, `/assets/{asset_id}/execution/proposal/latest` |
| Paper trading | `/assets/{asset_id}/execution/paper-trade/run`, `/assets/{asset_id}/execution/paper-trade/latest` |
| Submission simulation | `/assets/{asset_id}/execution/demo-submit`, `/assets/{asset_id}/execution/submissions/latest` |
| Approval gates | `/assets/{asset_id}/execution/approval/request`, `/approve`, `/reject`, `/latest` |
| Connector readiness | `/execution/market-connectors/readiness`, `/system/live-adapter-handshake` |
| Settlement | `/assets/{asset_id}/settlement/reconcile`, `/assets/{asset_id}/settlement/latest` |
| Reports | `/reports/monthly/latest`, `/reports/monthly/latest/view`, `/assets/{asset_id}/reports/monthly/generate` |
| Workflow | `/workflow/run-daily`, `/assets/{asset_id}/workflow-runs/run` |

OpenAPI docs are available when the backend is running:

```text
http://127.0.0.1:8000/docs
```

## Installation

Backend dependencies:

```bash
pip install -r requirements.txt
```

Frontend dependencies:

```bash
cd frontend
npm install
```

## Environment Variables

Common backend variables:

```env
APP_ENV=local
FRONTEND_ORIGIN=http://127.0.0.1:3000
API_PUBLIC_BASE_URL=http://127.0.0.1:8000
AUTH_MODE=dev
STORAGE_BACKEND=local
ENTSOE_API_KEY=your_entsoe_token_here
```

The app can run without `ENTSOE_API_KEY` by using local, uploaded, demo, or placeholder forecasts.

Frontend API URL:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Azure-related variables are documented in:

```text
.env.azure.example
frontend/.env.azure.example
docs/azure-app-service.md
```

## Run Locally

Start the backend:

```bash
python -m uvicorn backend.api.main:app --reload --port 8000
```

Start the frontend:

```bash
cd frontend
npm run dev
```

Open:

```text
http://localhost:3000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Run The Archived Streamlit Dashboard

The Streamlit dashboard remains useful for internal prototyping, but the Next.js frontend is the commercial product UI.

```bash
python -m streamlit run archive/streamlit_dashboard/app.py
```

Open:

```text
http://localhost:8501
```

## Common Workflows

Create demo forecast:

```bash
curl.exe -X POST http://127.0.0.1:8000/forecast/demo
```

Generate asset signal:

```bash
curl.exe -X POST "http://127.0.0.1:8000/assets/default_site/signal/run-latest?optimizer_engine=linear_v1"
```

Run revenue stack:

```bash
curl.exe -X POST "http://127.0.0.1:8000/assets/default_site/revenue-stack/run?optimizer_engine=linear_v1"
```

Build bid proposal:

```bash
curl.exe -X POST http://127.0.0.1:8000/assets/default_site/execution/proposal/build
```

Run paper trading:

```bash
curl.exe -X POST http://127.0.0.1:8000/assets/default_site/execution/paper-trade/run
```

Request and approve human gate:

```bash
curl.exe -X POST http://127.0.0.1:8000/assets/default_site/execution/approval/request
curl.exe -X POST http://127.0.0.1:8000/assets/default_site/execution/approval/approve
```

Run orchestrator next action:

```bash
curl.exe -X POST http://127.0.0.1:8000/assets/default_site/execution/orchestrator/run
```

Reconcile settlement:

```bash
curl.exe -X POST http://127.0.0.1:8000/assets/default_site/settlement/reconcile
```

Generate monthly report:

```bash
curl.exe -X POST http://127.0.0.1:8000/assets/default_site/reports/monthly/generate
```

Run daily workflow:

```bash
curl.exe -X POST "http://127.0.0.1:8000/workflow/run-daily?optimizer_engine=linear_v1"
```

## Forecast Input Format

Minimum CSV:

```csv
timestamp,forecast_price
2026-01-02 00:00:00,35
2026-01-02 00:15:00,32
2026-01-02 00:30:00,28
2026-01-02 00:45:00,25
```

Optional feature columns:

```csv
timestamp,forecast_price,load_forecast,generation_forecast,forecast_solar,forecast_wind,forecast_renewables_total,forecast_provider,forecast_model
```

For Germany day-ahead mode, a full day should contain 96 rows at 15-minute resolution.

Main local forecast path:

```text
data/processed/next_day_price_forecast.csv
```

## Optimizers

Available optimizer engines:

| Optimizer | Description |
|---|---|
| `rule_based_v1` | Spread-threshold dispatch logic |
| `linear_v1` | Discrete SOC dynamic-programming optimizer |

Example:

```bash
curl.exe -X POST "http://127.0.0.1:8000/battery/signal/run-latest?optimizer_engine=linear_v1"
```

## Market Products

The Germany product catalog currently includes:

| Product | Type | Current maturity |
|---|---|---|
| `day_ahead_arbitrage` | Energy arbitrage | strongest implemented economics |
| `intraday_arbitrage` | Energy arbitrage | assumption/data dependent |
| `fcr_capacity` | Reserve capacity | readiness and placeholder economics |
| `afrr_capacity` | Reserve capacity | readiness and placeholder economics |
| `mfrr_capacity` | Reserve capacity | readiness and placeholder economics |
| `imbalance_avoidance` | Risk reduction | assumption/data dependent |

Eligibility check:

```bash
curl.exe http://127.0.0.1:8000/assets/default_site/eligible-products
```

## Reports

Monthly reports are generated as standalone HTML files.

Report builder:

```text
backend/reports/monthly_report.py
```

Output pattern:

```text
data/outputs/monthly_report_YYYY-MM.html
data/outputs/monthly_report_{asset_id}_YYYY-MM.html
```

Current limitation: HTML report delivery is implemented. PDF export is intentionally shown as not connected in the UI until a backend PDF export route is added.

## Testing

Run backend tests:

```bash
python -m pytest
```

Run frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

## Deployment Direction

The intended commercial deployment is:

```text
Next.js frontend App Service
FastAPI backend App Service
Azure PostgreSQL or managed database
Azure Blob Storage
Azure Key Vault
Microsoft Entra ID
Application Insights
```

Deployment notes:

```text
docs/azure-app-service.md
```

Backend startup command:

```bash
bash startup.sh
```

Frontend startup command:

```bash
npm run start
```

## Known Limitations

This repository is a product-development and prototyping system. It is not a financial trading recommendation and not yet a production market submission system.

Important current limitations:

- no production authentication/authorization layer is enforced in local mode
- HTML monthly reports exist, but PDF export is not implemented yet
- real EPEX and TSO submission adapters are not connected to production credentials
- `demo-submit` simulates submission and should not be interpreted as live exchange trading
- reserve activation-energy logic still contains explicit placeholders
- intraday, reserve, imbalance, and degradation economics need stronger market data and model depth
- some artifacts still use local file outputs while others use SQLite repositories
- Azure deployment hardening is planned but not complete

## Recommended Next Product Improvements

1. Add backend PDF export for client reports.
2. Replace reserve activation placeholders with real activation-price logic.
3. Separate simulation, supervised live, and production live adapters more strictly in the UI and backend.
4. Add production authentication and role-based access.
5. Move remaining file-based outputs into database/object storage.
6. Add deeper forecast-vs-actual learning loops into route allocation and revenue assumptions.
7. Add stronger multi-market co-optimization across day-ahead, intraday, and ancillary products.


