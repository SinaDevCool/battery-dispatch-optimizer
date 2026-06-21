# AI Intelligence Layer

Battery Trader AI now keeps AI agent work under:

```text
backend/ai_intelligence/
```

This folder is the home for reusable agent logic, registries, safe actions,
history stores, and future bots. The first implemented agent is:

```text
ai_trading_supervisor
```

The second implemented capability is persona-aware agent routing:

```text
persona_intelligence_agent
```

## AI Trading Supervisor

The AI Trading Supervisor does not narrate every 15-minute dispatch interval.
It supervises continuous automated trading by looking for material exceptions,
evidence gaps, blocked gates, market-route issues, and operator questions.

Core endpoints:

```text
GET  /agents
GET  /assets/{asset_id}/agents/trading-supervisor/status
POST /assets/{asset_id}/agents/trading-supervisor/run
GET  /assets/{asset_id}/agents/trading-supervisor/history
GET  /assets/{asset_id}/agents/trading-supervisor/actions
POST /assets/{asset_id}/agents/trading-supervisor/actions/{action_id}
GET  /agents/personas
GET  /assets/{asset_id}/agents/persona/{persona_id}/status
POST /assets/{asset_id}/agents/persona/{persona_id}/run
```

Frontend:

```text
/execution/ai-supervisor
```

## What Makes It Agentic

The agent gathers context from deterministic backend systems:

- latest trading signal
- forecast confidence
- automation control mode
- automation blockers
- trading orchestrator status
- execution evidence IDs
- market-route and connector blockers

It then produces:

- supervisor decision
- material exceptions
- daily supervisor brief
- suggested operator questions
- answer to an operator question
- recent run history
- safe action recommendations

## Safety Boundary

The agent can explain, recommend, and trigger only safe actions:

- refresh demo forecast / workflow evidence
- run latest signal
- run orchestrator
- run paper trade
- refresh demo telemetry

It does not directly submit live trades or bypass approval gates.

## Persona Agent Map

The platform already has persona-specific navigation and product framing. The
AI intelligence layer maps those same personas to the highest-value agent lens:

| Persona | Agent | Main question |
|---|---|---|
| `trading_desk` | Trading Desk Agent | What should we do in the market now? |
| `automation_operator` | Automation Operator Agent | Can automation safely continue or escalate? |
| `risk_compliance` | Compliance & Audit Agent | Can this decision be approved and defended? |
| `market_operations` | Market Readiness Agent | Which routes and connectors are production-ready? |
| `forecast_quant` | Forecast Trust Agent | Can we trust the forecast and optimizer output? |
| `revenue_analyst` | Revenue Assurance Agent | Where is revenue created, blocked, or leaking? |
| `asset_owner` | Asset Owner Value Agent | Is this asset creating defensible owner value? |
| `investor_lender` | Investor Evidence Agent | Is this asset bankable and downside-protected? |
| `project_developer` | Project Development Agent | Is this project commercially ready to build or finance? |
| `executive` | Executive Decision Agent | What is the portfolio-level decision and top blocker? |
| `client_success` | Client Success Agent | What should we tell the client, and what must be fixed? |

The frontend page `/execution/ai-supervisor` shows:

- a persona-specific agent panel based on the selected persona
- persona-specific suggested questions
- persona-specific answer generation
- human-readable persona verdicts instead of raw machine status
- heuristic scores and calculation notes where the deeper backend model is not built yet
- the operational AI Trading Supervisor below it

Persona agents intentionally return business-readable fields:

```text
human_answer
score / score_label
what_it_means
business_value
recommended_actions
explainability
placeholder_calculations
```

The `placeholder_calculations` object is deliberate. It lets the hackathon demo
show the product direction now while clearly marking which deeper backend model
should be built later, such as bankability scoring, expected-vs-realized revenue
attribution, market-route readiness scoring, or interval-level forecast trust.

## Demo Script

1. Start backend and frontend.
2. Open `/execution/ai-supervisor`.
3. Confirm the daily supervisor brief shows `hold_live_execution`.
4. Ask: `Why is live execution blocked or allowed right now?`
5. Show the answer and recent agent run history.
6. Run `Run Paper Trade` or `Refresh Telemetry Demo`.
7. Refresh supervisor status and show updated evidence.

## Hackathon Extraction Notes

For a public demo repo, extract only:

- `backend/ai_intelligence/`
- `backend/api/routes/agents.py`
- a minimal FastAPI app
- `frontend/src/app/execution/ai-supervisor/`
- mock JSON evidence
- `.env.example`
- this document as the README basis

Do not publish real credentials, private client data, production strategy,
or the full internal platform unless the hackathon explicitly requires it.
