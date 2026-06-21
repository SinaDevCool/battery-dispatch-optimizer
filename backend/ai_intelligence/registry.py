AI_AGENT_REGISTRY = [
    {
        "agent_id": "ai_trading_supervisor",
        "name": "AI Trading Supervisor Agent",
        "status": "active",
        "route": "/assets/{asset_id}/agents/trading-supervisor/status",
        "run_route": "/assets/{asset_id}/agents/trading-supervisor/run",
        "purpose": (
            "Supervise continuous automated battery trading through exceptions, "
            "evidence, safe actions, and operator questions."
        ),
        "safe_actions": [
            "refresh_forecast_demo",
            "run_signal",
            "run_orchestrator",
            "run_paper_trade",
            "refresh_telemetry_demo",
        ],
    },
    {
        "agent_id": "persona_intelligence_agent",
        "name": "Persona Intelligence Agent Router",
        "status": "active",
        "route": "/assets/{asset_id}/agents/persona/{persona_id}/status",
        "run_route": "/assets/{asset_id}/agents/persona/{persona_id}/run",
        "purpose": (
            "Map each platform persona to the highest-value AI decision lens, "
            "including investor evidence, revenue assurance, market readiness, "
            "compliance audit, forecast trust, and client success."
        ),
        "safe_actions": [],
    },
]


def list_ai_agents():
    return {
        "status": "ok",
        "agent_count": len(AI_AGENT_REGISTRY),
        "agents": AI_AGENT_REGISTRY,
    }
