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
- run rule-based or linear-program dispatch optimization
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

Recent investor-demo upgrades:

- selected-asset mock data now drives dispatch, scenarios, stress tests, revenue, execution, reports, and investor readiness
- grid, solar co-located, and industrial behind-the-meter assets each carry asset-specific physical proof and business value context
- `linear_program_v1` is available as the investor-facing optimizer engine while `rule_based_v1` remains available for comparison
- the `/dispatch` page exposes an optimizer selector, optimizer objective/constraint proof, and rule-based vs linear-program comparison

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
- Page-level summary endpoints are used first where possible so client-facing pages do not need to stitch many low-level API calls together before showing a decision.
- `/dispatch` now includes an optimizer selector, selected-engine signal generation, rule-based vs linear-program comparison, and backend objective/constraint proof.

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

There is no active `src/` application folder. Active backend code belongs in `backend/`; active frontend code belongs in `frontend/`. Older Streamlit and manual script work is kept under `archive/` so it is still inspectable without being confused with the production app path.

Major backend areas:

| Area | Purpose |
|---|---|
| `backend/api/routes/` | FastAPI HTTP API modules |
| `backend/api/routes/summaries.py` | Page-level summary API contracts for revenue, regulation, execution, and client evidence |
| `backend/assets/` | Asset loading, asset schema, portfolio dispatch |
| `backend/backtesting/` | Forecast-vs-actual and historical analysis support |
| `backend/config/` | Paths, app settings, client presets, market config |
| `backend/db/` | SQLite database setup and repository layer |
| `backend/dispatch/` | Dispatch and battery schedule utilities |
| `backend/energy_accounting/` | Energy-origin and accounting evidence |
| `backend/execution/` | Automation control, market routing, proposals, paper trading, connectors, gates, remediation, submission lifecycle |
| `backend/features/` | Feature engineering helpers |
| `backend/forecasts/` | Forecast loading, upload, ENTSO-E provider, comparison |
| `backend/grid_fees/` | Germany grid-fee sensitivity logic |
| `backend/hedging/` | Revenue contracts and downside protection views |
| `backend/markets/` | Market profiles, products, and market data helpers |
| `backend/optimization/` | Optimizer registry and optimization engines |
| `backend/regulatory/` | Germany regulatory and operating assumption checks |
| `backend/reports/` | Monthly client report generation |
| `backend/revenue/` | Revenue stack runner and revenue calculators |
| `backend/scenarios/` | Scenario and stress-test logic |
| `backend/services/` | Shared services and persistence helpers |
| `backend/settlement/` | Settlement variance and reconciliation logic |
| `backend/signals/` | Signal generation, explanations, and risk flags |
| `backend/storage/` | Local and cloud storage abstraction |
| `backend/telemetry/` | Asset telemetry snapshots |
| `backend/validation/` | Dispatch validation |
| `backend/workflows/` | Daily workflow orchestration |

Optimizer implementations now live under `backend/optimization/`. The old
`backend/optimizer/` package remains only as a compatibility shim for older callers;
new code should import from `backend.optimization`.

## Repository Layout

The active application surfaces are intentionally simple:

```text
backend/      FastAPI backend, domain services, execution control, persistence
frontend/     Next.js commercial frontend
tests/        backend test suite
```

Supporting folders and root files:

```text
archive/      non-active historical tools kept for reference
docs/         deployment and operating notes, especially Azure App Service
data/config/  checked-in local seed configuration for assets, clients, markets
pytest.ini    pytest configuration
requirements.txt
              backend and archived Streamlit dependency list
startup.sh    backend App Service startup command
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

Archived code is organized as:

```text
archive/streamlit_dashboard/  older Streamlit prototype UI
archive/manual_scripts/       older manual CLI utilities and local checks
```

Do not add new production code to `archive/`. New backend code should go into the correct `backend/` domain package, and new UI code should go into `frontend/src/`.

### Mock Investor Demo Data

The selected UI assets are intentionally configured as mock investor-demo assets in `data/config/assets.json`.

Current mock assets:

| Asset ID | Type | Demo purpose |
|---|---|---|
| `default_site` | `grid_scale_battery` | Standalone merchant grid battery |
| `demo_solar_battery` | `solar_colocated_battery` | Solar shifting, renewable-origin evidence, and development diligence |
| `demo_industrial_btm` | `industrial_behind_the_meter_battery` | Behind-the-meter peak shaving, self-consumption, and optional market access |

Important asset metadata fields:

| Field | Current value | Meaning |
|---|---|---|
| `asset_type` | asset-specific | Product category shown in the asset selector and asset passport |
| `asset_subtype` | asset-specific | Operating archetype for the current asset |
| `data_mode` | `mock` | This asset uses local demo data, not production exchange or telemetry data |
| `data_source` | `local_seed_demo` | The source boundary for the current asset evidence |
| `data_profile.execution_adapter` | `demo_market` | Execution is simulated through the demo adapter |
| `data_profile.telemetry_mode` | `demo_local_telemetry` | Telemetry is seeded locally for demo validation |
| `data_profile.settlement_mode` | `simulated` | Settlement evidence is simulated for the investor-demo workflow |

This boundary is deliberate. Investor demos should work end-to-end with mock data, while future production integrations can add assets with `data_mode: "production"` and real forecast, telemetry, exchange, and settlement sources.

Selected-asset behavior is intentionally end-to-end:

- grid-scale assets show merchant spread, throughput, SOC, power, and grid connection evidence
- solar co-located assets show solar-shifting, renewable-origin charge, export-limit, and green-metering evidence
- industrial behind-the-meter assets show site-load, peak-shaving, import-headroom, and optional market-access evidence
- scenarios and stress tests now use the selected asset's physical profile rather than generic battery labels
- revenue stack, revenue allocation, execution proposal, and paper-trade evidence now carry selected-asset value context
- investor readiness packages source routes, diligence rows, finance assumptions, project economics, blockers, and production-upgrade boundaries

Mock forecast files are checked in under:

```text
data/mock/forecasts/
```

Each mock asset points to its own file so selected-asset workflows are not all driven by one generic forecast.

Before an investor walkthrough, reset the full mock evidence chain with:

```bash
python -m backend.demo.seed_investor_demo
```

Or through the running API:

```bash
curl.exe -X POST http://127.0.0.1:8000/demo/investor-seed
```

This seeds all mock investor assets with current forecast, dispatch, revenue, workflow, proposal, paper-trade, settlement, telemetry, report, and cockpit evidence. To seed one asset only:

```bash
python -m backend.demo.seed_investor_demo --asset-id demo_solar_battery
curl.exe -X POST "http://127.0.0.1:8000/demo/investor-seed?asset_id=demo_solar_battery"
```

The investor-demo seed also prepares selected-asset sizing scenarios and investor downside stress cases. The frontend `/investor-demo` page shows a route-backed checklist for:

- mock data seeded
- physical dispatch generated
- revenue generated
- sizing scenarios generated
- investor stress cases generated
- report generated
- investor readiness score available

Use this page before an investor walkthrough to confirm the selected mock asset is coherent across the product, not just present in the asset dropdown.

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
| Page summaries | `/assets/{asset_id}/revenue-summary`, `/regulatory-summary`, `/execution-summary`, `/client-evidence-summary` |
| Forecasts | `/forecast/upload`, `/forecast/status`, `/forecast/demo`, `/forecasts/compare-profitability` |
| Signals and dispatch | `/assets/{asset_id}/signal/run-latest`, `/assets/{asset_id}/signal/latest`, `/battery/optimizers` |
| Markets and products | `/markets`, `/markets/products`, `/assets/{asset_id}/eligible-products` |
| Revenue and hedging | `/assets/{asset_id}/revenue-stack/run`, `/assets/{asset_id}/revenue-stack/latest`, hedging-related asset routes |
| Scenarios and stress | `/assets/{asset_id}/scenarios/run-latest`, `/assets/{asset_id}/scenarios/latest`, `/assets/{asset_id}/stress/run-latest`, `/assets/{asset_id}/stress/latest` |
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
| Investor demo | `/demo/investor-seed`, `/assets/{asset_id}/investor-readiness` |
| Workflow | `/workflow/run-daily`, `/assets/{asset_id}/workflow-runs/run` |

OpenAPI docs are available when the backend is running:

```text
http://127.0.0.1:8000/docs
```

### Summary API Layer

The current frontend uses page-level summary endpoints before falling back to lower-level detail endpoints. These routes keep the UI decision-first and reduce frontend coupling to backend implementation details.

| Endpoint | Used by | Purpose |
|---|---|---|
| `/assets/{asset_id}/revenue-summary` | Revenue Assurance | Packages revenue stack, allocation, latest signal, EEG, ancillary eligibility, hedging, and business decision evidence |
| `/assets/{asset_id}/regulatory-summary` | Regulation | Packages storage classification, EEG compliance, ancillary eligibility, and approval blockers |
| `/assets/{asset_id}/execution-summary` | Execution / Mission Control | Packages proposal, readiness, automation control, guardrails, signal, paper trade, submission, approval, allocation, and telemetry status |
| `/assets/{asset_id}/client-evidence-summary` | Reports | Packages report readiness, evidence completeness, revenue, regulation, execution, and settlement state |
| `/assets/{asset_id}/investor-readiness` | Investor Demo, Scenarios, Reports | Packages the investor-facing readiness score, demo script, source map, diligence rows, and open gaps |

Detail endpoints still exist and are used for drill-down tabs, history tables, controls, and backend diagnostics.

## Installation

Backend dependencies:

```bash
pip install -r requirements.txt
```

`requirements.txt` is still needed because it is the backend dependency source for local development and deployment. It also includes `streamlit` because the archived Streamlit dashboard remains runnable for reference.

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
python -m uvicorn backend.api.main:app --reload --reload-dir backend --host 0.0.0.0 --port 8000
```

Use `backend.api.main:app`, not the old `src.api.main:app` path. The
`--reload-dir backend` flag keeps Uvicorn from watching generated frontend
folders such as `frontend/.next`.

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

Quick health checks:

```bash
curl.exe http://127.0.0.1:8000/health
curl.exe http://127.0.0.1:8000/status
curl.exe http://127.0.0.1:8000/assets/default_site/client-evidence-summary
```

## Investor Demo Runbook

Use this sequence before showing the product to an investor or lender.

1. Start the backend:

```bash
python -m uvicorn backend.api.main:app --reload --reload-dir backend --host 0.0.0.0 --port 8000
```

2. Start the frontend:

```bash
cd frontend
npm run dev
```

3. Seed all mock investor-demo assets:

```bash
curl.exe -X POST http://127.0.0.1:8000/demo/investor-seed
```

4. Open the app:

```text
http://localhost:3000/investor-demo
```

5. Confirm the selected asset checklist shows evidence for:

```text
mock data -> physical dispatch -> revenue -> scenarios -> stress -> reports -> investor readiness
```

6. Walk through the product in this order:

```text
Investor Demo -> Asset Registry -> Forecast Trust -> Dispatch Schedule -> Revenue Assurance -> Scenario Lab -> Reports -> Mission Control
```

On the Dispatch Schedule page, use the optimizer selector to show the difference between:

```text
rule_based_v1       simple spread-threshold baseline
linear_program_v1   objective-driven dispatch with SOC, power, efficiency, cost, and no-simultaneous-charge/discharge proof
```

The page displays backend optimization metadata directly: engine, method, solver, objective function, objective value, constraint status, SOC envelope, and engine comparison rows.

Status language used in the demo:

| Label | Meaning |
|---|---|
| `Mock-ready` | The evidence is generated and usable for the investor demo |
| `Mock-ready / production gated` | Demo evidence exists, but live forecast, exchange, telemetry, settlement, or approval integrations are intentionally not treated as production-ready |
| `Needs production evidence` | The page is showing the next proof needed before this can support a production claim |
| `Production data` | The selected asset or source is marked as production rather than mock |

For a single-asset walkthrough, seed only the selected asset:

```bash
curl.exe -X POST "http://127.0.0.1:8000/demo/investor-seed?asset_id=demo_solar_battery"
```

## Run The Archived Streamlit Dashboard

The Streamlit dashboard is archived historical code. It remains useful for internal prototyping or comparison, but the Next.js frontend is the commercial product UI.

```bash
python -m streamlit run archive/streamlit_dashboard/app.py
```

Open:

```text
http://localhost:8501
```

## Common Workflows

Prepare investor demo:

```bash
curl.exe -X POST http://127.0.0.1:8000/demo/investor-seed
```

This is the recommended one-command setup before showing the app to an investor. It prepares all mock investor assets and generates forecast-backed dispatch, revenue, scenarios, stress tests, execution evidence, settlement evidence, reports, and readiness summaries.

Prepare one investor demo asset:

```bash
curl.exe -X POST "http://127.0.0.1:8000/demo/investor-seed?asset_id=default_site"
```

Verify the selected asset demo checklist:

```bash
curl.exe http://127.0.0.1:8000/assets/default_site/signal/latest
curl.exe http://127.0.0.1:8000/assets/default_site/revenue-summary
curl.exe http://127.0.0.1:8000/assets/default_site/scenarios/latest
curl.exe http://127.0.0.1:8000/assets/default_site/stress/latest
curl.exe http://127.0.0.1:8000/assets/default_site/client-evidence-summary
curl.exe http://127.0.0.1:8000/assets/default_site/investor-readiness
```

Investor walkthrough order:

```text
Investor Demo -> Asset Registry -> Forecast Trust -> Dispatch Schedule -> Revenue Assurance -> Scenario Lab -> Reports -> Mission Control
```

Create demo forecast:

```bash
curl.exe -X POST http://127.0.0.1:8000/forecast/demo
```

Generate asset signal:

```bash
curl.exe -X POST "http://127.0.0.1:8000/assets/default_site/signal/run-latest?optimizer_engine=linear_program_v1"
```

Run revenue stack:

```bash
curl.exe -X POST "http://127.0.0.1:8000/assets/default_site/revenue-stack/run?optimizer_engine=linear_program_v1"
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
curl.exe -X POST "http://127.0.0.1:8000/workflow/run-daily?optimizer_engine=linear_program_v1"
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
| `linear_v1` | Backward-compatible linear optimizer name |
| `linear_program_v1` | Investor-facing linear-program dispatch engine with explicit objective and constraint metadata |

Recommended demo engine:

```text
linear_program_v1
```

`linear_program_v1` optimizes net dispatch value with a transparent objective:

```text
maximize
  discharge_grid_mwh * price
  - charge_grid_mwh * price
  - trading fees
  - market access fees
  - grid fees
  - taxes and levies
  - degradation cost
```

It exposes constraint proof in the signal metadata:

```text
SOC balance
minimum and maximum SOC
initial and terminal SOC
charge and discharge power limits
charge and discharge efficiency
per-interval energy limits
no simultaneous charge/discharge, enforced by a single SOC transition per interval
```

Implementation note: the current engine is dependency-free and solves the linear dispatch formulation through discrete SOC dynamic programming. This preserves the backend API contract now while leaving room to swap in an external LP/MILP solver such as PuLP, OR-Tools, or HiGHS later.

Example:

```bash
curl.exe -X POST "http://127.0.0.1:8000/assets/default_site/signal/run-latest?optimizer_engine=linear_program_v1"
curl.exe http://127.0.0.1:8000/battery/optimizers
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
python -m pytest tests
```

Run frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

Recent verification baseline:

```text
backend syntax and API smoke checks passing for the latest optimizer/data-flow changes
frontend lint passing
frontend production build passing
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

`startup.sh` is intentionally kept because Azure App Service can call it directly. It starts `backend.api.main:app` on the provided `PORT`.

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
- `linear_program_v1` exposes objective and constraint proof, but it currently uses dependency-free discrete SOC dynamic programming rather than an external LP/MILP solver
- some artifacts still use local file outputs while others use SQLite repositories
- Azure deployment hardening is planned but not complete
- summary endpoints currently use flexible response envelopes; dedicated Pydantic response models should be added next for stricter backend contracts

## Recommended Next Product Improvements

1. Add dedicated Pydantic models for the summary endpoints.
2. Add backend PDF export for client reports.
3. Replace reserve activation placeholders with real activation-price logic.
4. Separate simulation, supervised live, and production live adapters more strictly in the UI and backend.
5. Add production authentication and role-based access.
6. Move remaining file-based outputs into database/object storage.
7. Add deeper forecast-vs-actual learning loops into route allocation and revenue assumptions.
8. Swap the dependency-free `linear_program_v1` solver backend for a production LP/MILP solver while preserving the current API contract.
9. Add stronger multi-market co-optimization across day-ahead, intraday, and ancillary products.


