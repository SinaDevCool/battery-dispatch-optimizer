from fastapi.testclient import TestClient

from backend.api.main import app


client = TestClient(app)


def test_trading_supervisor_status_without_ai_brief():
    demo_response = client.post("/forecast/demo")
    assert demo_response.status_code == 200

    signal_response = client.post(
        "/assets/default_site/signal/run-latest?optimizer_engine=linear_program_v1"
    )
    assert signal_response.status_code == 200

    response = client.get(
        "/assets/default_site/agents/trading-supervisor/status"
    )
    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert data["agent"]["agent_id"] == "ai_trading_supervisor"
    assert data["agent"]["mode"] == "exception_supervision"
    assert data["supervisor_status"] in ["normal", "review", "exception"]
    assert data["decision"] in [
        "continue_live_automation",
        "continue_non_live_automation",
        "continue_with_human_review",
        "hold_live_execution",
    ]
    assert isinstance(data["exceptions"], list)
    assert data["ai_brief"]["status"] == "not_requested"
    assert "automation_control" in data["context"]
    assert "forecast_confidence" in data["context"]
    assert data["daily_brief"]["decision"] == data["decision"]
    assert data["suggested_questions"]
    assert data["safe_actions"]


def test_trading_supervisor_run_keeps_ai_optional():
    response = client.post(
        "/assets/default_site/agents/trading-supervisor/run",
        json={"include_ai_brief": False},
    )
    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["ai_brief"]["status"] == "not_requested"


def test_trading_supervisor_run_accepts_question_without_ai():
    response = client.post(
        "/assets/default_site/agents/trading-supervisor/run",
        json={
            "include_ai_brief": False,
            "question": "Why is live execution blocked?",
        },
    )
    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["operator_question"] == "Why is live execution blocked?"
    assert data["ai_brief"]["status"] == "not_requested"


def test_ai_agent_registry_and_supervisor_actions():
    registry_response = client.get("/agents")
    assert registry_response.status_code == 200

    registry = registry_response.json()
    assert registry["status"] == "ok"
    assert registry["agents"][0]["agent_id"] == "ai_trading_supervisor"

    actions_response = client.get(
        "/assets/default_site/agents/trading-supervisor/actions"
    )
    assert actions_response.status_code == 200

    actions = actions_response.json()
    assert actions["status"] == "ok"
    assert any(action["action_id"] == "run_paper_trade" for action in actions["actions"])


def test_persona_agent_registry_and_status():
    registry_response = client.get("/agents/personas")
    assert registry_response.status_code == 200

    registry = registry_response.json()
    assert registry["status"] == "ok"
    assert registry["persona_agent_map"]["investor_lender"] == "investor_evidence_agent"
    assert registry["persona_agent_map"]["revenue_analyst"] == "revenue_assurance_agent"

    status_response = client.get(
        "/assets/default_site/agents/persona/investor_lender/status"
    )
    assert status_response.status_code == 200

    status = status_response.json()
    assert status["status"] == "ok"
    assert status["persona_id"] == "investor_lender"
    assert status["agent"]["agent_id"] == "investor_evidence_agent"
    assert status["decision"]["decision"]
    assert status["decision"]["human_answer"]
    assert status["decision"]["business_value"]
    assert status["decision"]["placeholder_calculations"]["method"]
    assert isinstance(status["decision"]["score"], int)
    assert status["suggested_questions"]


def test_persona_agent_run_accepts_question():
    response = client.post(
        "/assets/default_site/agents/persona/revenue_analyst/run",
        json={
            "include_ai_brief": False,
            "question": "Where is revenue leaking?",
        },
    )
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["persona_id"] == "revenue_analyst"
    assert data["agent"]["agent_id"] == "revenue_assurance_agent"
    assert data["decision"]["operator_question"] == "Where is revenue leaking?"
    assert "revenue" in data["decision"]["human_answer"].lower()


def test_persona_agent_missing_evidence_answer_is_human_readable(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/assets/default_site/agents/persona/asset_owner/run",
        json={
            "evidence_mode": "live",
            "include_ai_brief": True,
            "question": "What evidence is missing?",
        },
    )
    assert response.status_code == 200

    data = response.json()
    brief = data["ai_brief"]["brief"]

    assert data["decision"]["missing_evidence"]
    assert "What is missing" in brief
    assert "Revenue Assurance (/revenue)" in brief
    assert "blocked_product_count" not in brief


def test_persona_agent_production_gap_answer_uses_persona_voice(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/assets/default_site/agents/persona/client_success/run",
        json={
            "evidence_mode": "live",
            "include_ai_brief": True,
            "question": "Which production gap should we solve first?",
        },
    )
    assert response.status_code == 200

    data = response.json()
    brief = data["ai_brief"]["brief"]

    assert data["decision"]["question_intent"] == "production_gap_prioritization"
    assert "For my client update" in brief
    assert "settlement proof first" in brief
    assert "Settlement Evidence (/execution/settlement)" in brief
    assert "Execution readiness is marked partial" not in brief
    assert "Is this battery bankable or profitable this month?" in data["suggested_questions"]


def test_persona_agent_mock_mode_returns_complete_simulated_client_pack(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/assets/default_site/agents/persona/client_success/run",
        json={
            "evidence_mode": "mock",
            "include_ai_brief": True,
            "question": "What proof is missing before client reporting?",
        },
    )
    assert response.status_code == 200

    data = response.json()
    brief = data["ai_brief"]["brief"]

    assert data["evidence_mode"] == "mock"
    assert data["decision"]["priority_intelligence"]["evidence_mode"] == "mock"
    assert "Mock Data evidence pack is ready" in brief
    assert "simulated proof for the value story" in brief
    assert "2 domain(s) still need" not in brief


def test_persona_agent_mock_mode_has_no_production_gap_to_solve(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/assets/default_site/agents/persona/client_success/run",
        json={
            "evidence_mode": "mock",
            "include_ai_brief": True,
            "question": "Which production gap should we solve first?",
        },
    )
    assert response.status_code == 200

    data = response.json()
    brief = data["ai_brief"]["brief"]

    assert data["evidence_mode"] == "mock"
    assert data["decision"]["status"] == "ready"
    assert data["decision"]["score"] >= 80
    assert data["decision"]["blockers"] == []
    assert data["decision"]["missing_evidence"] == []
    assert "I do not see a missing proof item in Mock Data mode" in brief
    assert "settlement proof first" not in brief
    assert "production domain" not in brief


def test_persona_agent_profitability_question_returns_numbers(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/assets/default_site/agents/persona/client_success/run",
        json={
            "evidence_mode": "mock",
            "include_ai_brief": True,
            "question": "is the battrey bankable or proftable this month",
        },
    )
    assert response.status_code == 200

    data = response.json()
    brief = data["ai_brief"]["brief"]
    structured = data["decision"]["structured_answer"]

    assert data["decision"]["question_intent"] == "revenue_opportunity"
    assert structured["answer_type"] == "revenue_opportunity"
    assert structured["bankability_call"] in {
        "bankable_for_first_review",
        "not_bankable_yet",
    }
    assert structured["kpis"]["total_visible_revenue_eur"] > 0
    assert structured["top_product"]
    assert structured["evidence_completeness"]["status"] == "ready"
    assert data["decision"]["mock_evidence_completeness"]["status"] == "ready"
    assert data["decision"]["mock_evidence_completeness"]["missing_count"] == 0
    assert "total visible monthly opportunity" in brief
    assert "allocated into the current value stack" in brief
    assert "Top product:" in brief
    assert "Products I used:" in brief
    assert "Evidence completeness:" in brief
    assert "None EUR" not in brief


def test_forecast_trust_mock_answer_is_data_driven(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    seed_response = client.post("/demo/investor-seed?asset_id=default_site")
    assert seed_response.status_code == 200

    response = client.post(
        "/assets/default_site/agents/persona/forecast_quant/run",
        json={
            "evidence_mode": "mock",
            "include_ai_brief": True,
            "question": "Can we trust the forecast and optimizer output?",
        },
    )
    assert response.status_code == 200

    data = response.json()
    brief = data["ai_brief"]["brief"]
    forecast_evidence = data["decision"]["forecast_optimizer_evidence"]
    structured = data["decision"]["structured_answer"]

    assert data["decision"]["question_intent"] == "forecast_optimizer_trust"
    assert forecast_evidence["confidence_score"] is not None
    assert forecast_evidence["expected_pnl_eur"] is not None
    assert structured["answer_type"] == "forecast_optimizer_trust"
    assert structured["trust_decision"] in {
        "trust_for_supervised_sizing",
        "trust_with_reduced_sizing",
        "paper_only",
    }
    assert structured["kpis"]["confidence_score"] is not None
    assert structured["kpis"]["expected_pnl_eur"] is not None
    assert structured["bid_sizing"]["recommendation"]
    assert structured["evidence_completeness"]["status"] == "ready"
    assert data["decision"]["mock_evidence_completeness"]["status"] == "ready"
    assert data["decision"]["mock_evidence_completeness"]["missing_count"] == 0
    assert "Forecast evidence:" in brief
    assert "Optimizer evidence:" in brief
    assert "Validation and sizing:" in brief
    assert "Evidence completeness:" in brief
    assert "Missing: none" in brief
    assert "latest MAE" in brief
    assert "expected PnL" in brief
    assert "active interval" in brief
    assert "execution readiness status is partial" not in brief
    assert "If you need more detail" not in brief


def test_trading_supervisor_mock_mode_has_no_exceptions(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/assets/default_site/agents/trading-supervisor/run",
        json={
            "evidence_mode": "mock",
            "include_ai_brief": True,
            "question": "Is live allowed?",
        },
    )
    assert response.status_code == 200

    data = response.json()
    brief = data["ai_brief"]["brief"]

    assert data["evidence_mode"] == "mock"
    assert data["supervisor_status"] == "normal"
    assert data["decision"] == "continue_live_automation"
    assert data["exception_count"] == 0
    assert data["context"]["automation_control"]["live_trading_allowed"] is True
    assert data["context"]["automation_control"]["blockers"] == []
    assert "no material blocker" in data["recommendation"]["summary"]
    assert "Main exception: none currently detected." in brief


def test_trading_supervisor_history_records_runs():
    run_response = client.post(
        "/assets/default_site/agents/trading-supervisor/run",
        json={
            "include_ai_brief": False,
            "question": "What should I fix first?",
            "record_history": True,
        },
    )
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "ok"
    assert "history_record" in run_response.json()

    history_response = client.get(
        "/assets/default_site/agents/trading-supervisor/history?limit=5"
    )
    assert history_response.status_code == 200

    history = history_response.json()
    assert history["status"] == "ok"
    assert history["history_count"] >= 1
    assert history["history"][0]["question"] == "What should I fix first?"
