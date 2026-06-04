from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_status_endpoint():
    response = client.get("/status")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "/battery/signal" in data["available_endpoints"]
    assert "/assets/{asset_id}/signal/latest" in data["available_endpoints"]
    assert "/assets/{asset_id}/regulatory/germany" in data["available_endpoints"]
    assert "/markets/products" in data["available_endpoints"]
    assert "/assets/{asset_id}/eligible-products" in data["available_endpoints"]
    assert "/assets/{asset_id}/revenue-stack/run" in data["available_endpoints"]
    assert "/assets/{asset_id}/revenue-stack/allocate" in data["available_endpoints"]
    assert "/assets/{asset_id}/revenue-stack/allocation/latest" in data["available_endpoints"]
    assert "/assets/{asset_id}/signals" in data["available_endpoints"]
    assert "/assets/{asset_id}/revenue-stack/runs" in data["available_endpoints"]
    assert "/backtesting/forecast-actual/run" in data["available_endpoints"]
    assert "/backtesting/forecast-actual/latest" in data["available_endpoints"]
    assert "/assets/{asset_id}/forecast-performance" in data["available_endpoints"]
    assert "/assets/{asset_id}/forecast-confidence" in data["available_endpoints"]
    assert "/data/update-actual-prices" in data["available_endpoints"]
    assert "/data/actual-prices/status" in data["available_endpoints"]
    assert "/assets/{asset_id}/storage-classification" in data["available_endpoints"]
    assert "/assets/{asset_id}/eeg-compliance/latest" in data["available_endpoints"]
    assert "/assets/{asset_id}/ancillary/germany/eligibility" in data["available_endpoints"]
    assert "/assets/{asset_id}/grid-fees/germany/sensitivity" in data["available_endpoints"]
    assert "/assets/{asset_id}/energy-origin/latest" in data["available_endpoints"]
    assert "/assets/{asset_id}/hedging/revenue" in data["available_endpoints"]
    assert "/assets/{asset_id}/telemetry/demo" in data["available_endpoints"]
    assert "/assets/{asset_id}/telemetry/latest" in data["available_endpoints"]
    assert "/assets/{asset_id}/telemetry/history" in data["available_endpoints"]
    assert "/execution/market-adapters" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/market-adapter/status" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/multi-market/allocation" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/epex/day-ahead/preview" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/epex/intraday-auction/preview" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/epex/intraday-continuous/preview" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/regelleistung/fcr/preview" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/regelleistung/afrr/preview" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/regelleistung/mfrr/preview" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/automation-guardrails" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/readiness" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/demo-submit" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/submissions/latest" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/submissions" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/approval/request" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/approval/approve" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/approval/reject" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/approval/latest" in data["available_endpoints"]
    assert "/assets/{asset_id}/execution/approvals" in data["available_endpoints"]
    assert "/assets/{asset_id}/settlement/reconcile" in data["available_endpoints"]
    assert "/assets/{asset_id}/settlement/latest" in data["available_endpoints"]
    assert "/assets/{asset_id}/settlement/runs" in data["available_endpoints"]


def test_battery_config_endpoint():
    response = client.get("/battery/config")

    assert response.status_code == 200

    data = response.json()

    assert "battery_config" in data
    assert "strategy_config" in data
    assert data["battery_config"]["capacity_mwh"] > 0


def test_battery_optimizers_endpoint():
    response = client.get("/battery/optimizers")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["default_optimizer"] == "rule_based_v1"
    assert "rule_based_v1" in data["available_optimizers"]
    assert "linear_v1" in data["available_optimizers"]


def test_battery_signal_endpoint():
    payload = {
        "price_data": [
            {
                "timestamp": "2026-01-01 00:00:00",
                "price": 40,
            },
            {
                "timestamp": "2026-01-01 01:00:00",
                "price": 10,
            },
            {
                "timestamp": "2026-01-01 02:00:00",
                "price": 100,
            },
        ]
    }

    response = client.post("/battery/signal", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert "summary" in data
    assert "dispatch" in data
    assert len(data["dispatch"]) == 3
    assert data["summary"]["signal"] in ["ACTION", "NO_ACTION", "NO_DATA"]


def test_battery_backtest_endpoint():
    payload = {
        "price_data": [
            {
                "timestamp": "2026-01-01 00:00:00",
                "price": 40,
            },
            {
                "timestamp": "2026-01-01 01:00:00",
                "price": 10,
            },
            {
                "timestamp": "2026-01-01 02:00:00",
                "price": 100,
            },
        ]
    }

    response = client.post("/battery/backtest", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert "summary" in data
    assert "dispatch" in data
    assert len(data["dispatch"]) == 3


def test_forecast_features_endpoint():
    response = client.get("/features/forecast")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data


def test_battery_constraints_endpoint():
    response = client.get("/battery/constraints")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data

    if data["status"] == "ok":
        assert "usable_capacity_mwh" in data
        assert "charge_duration_hours" in data
        assert "discharge_duration_hours" in data


def test_system_health_endpoint():
    response = client.get("/system/health")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "checks" in data


def test_assets_endpoint():
    response = client.get("/assets")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_count"] >= 1
    assert "assets" in data
    assert "asset_id" in data["assets"][0]


def test_markets_endpoint():
    response = client.get("/markets")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["market_count"] >= 1
    assert data["markets"][0]["market_profile_id"] == "de_lu_day_ahead"


def test_germany_market_profile_endpoint():
    response = client.get("/markets/de_lu_day_ahead")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["market"]["bidding_zone"] == "DE_LU"
    assert data["market"]["market_time_unit_minutes"] == 15
    assert data["market"]["expected_intervals_per_day"] == 96


def test_market_products_endpoint():
    response = client.get("/markets/products")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["product_count"] >= 1
    assert "day_ahead_arbitrage" in [
        product["product_id"] for product in data["products"]
    ]


def test_market_product_detail_endpoint():
    response = client.get("/markets/products/day_ahead_arbitrage")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["product"]["product_id"] == "day_ahead_arbitrage"


def test_asset_eligible_products_endpoint():
    response = client.get("/assets/default_site/eligible-products")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert data["product_count"] >= 1
    assert "products" in data


def test_asset_revenue_stack_latest_endpoint():
    response = client.get("/assets/default_site/revenue-stack/latest")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert data["asset_id"] == "default_site"


def test_asset_revenue_stack_database_history_endpoint():
    response = client.get("/assets/default_site/revenue-stack/runs")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "runs" in data


def test_run_asset_revenue_stack_endpoint():
    response = client.post("/assets/default_site/revenue-stack/run")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data

    if data["status"] == "ok":
        assert data["asset_id"] == "default_site"
        assert "products" in data
        assert "total_estimated_revenue_eur" in data


def test_germany_regulatory_requirements_endpoint():
    response = client.get("/regulatory/germany/requirements")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["country"] == "Germany"
    assert len(data["requirements"]) >= 1


def test_asset_germany_regulatory_endpoint():
    response = client.get("/assets/default_site/regulatory/germany")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "regulatory_assumptions" in data


def test_portfolio_latest_endpoint():
    response = client.get("/portfolio/latest")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "assets" in data


def test_asset_signal_latest_endpoint():
    response = client.get("/assets/default_site/signal/latest")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert data["asset_id"] == "default_site"


def test_asset_signal_database_history_endpoint():
    response = client.get("/assets/default_site/signals")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "runs" in data


def test_run_latest_battery_signal_endpoint():
    response = client.post("/battery/signal/run-latest")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data

    if data["status"] == "ok":
        assert "data" in data
        assert "summary" in data["data"]
        assert "dispatch" in data["data"]
        assert "validation" in data
        assert data["validation"]["status"] in ["pass", "warning", "fail"]

def test_client_presets_endpoint():
    response = client.get("/client/presets")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "presets" in data
    assert "grid_scale_battery" in data["presets"]


def test_apply_missing_client_preset():
    response = client.post("/client/presets/not_a_real_preset/apply")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "not_found"

def test_latest_forecast_actual_endpoint():
    response = client.get("/backtesting/forecast-actual/latest")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert data.get("asset_id") == "default_site"


def test_asset_forecast_performance_endpoint():
    response = client.get("/assets/default_site/forecast-performance")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "runs" in data


def test_asset_forecast_confidence_endpoint():
    response = client.get("/assets/default_site/forecast-confidence")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert data["asset_id"] == "default_site"
    assert "confidence_score" in data
    assert "confidence_band" in data
    assert "automation_eligibility" in data
    assert "risk_policy" in data

def test_actual_price_status_endpoint():
    response = client.get("/data/actual-prices/status")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "actual_file" in data

def test_storage_classification_endpoint():
    response = client.get("/assets/default_site/storage-classification")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert data["asset_id"] == "default_site"
    assert "storage_mode" in data


def test_eeg_compliance_endpoint():
    response = client.get("/assets/default_site/eeg-compliance/latest")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert data["asset_id"] == "default_site"
    assert "recommended_actions" in data


def test_ancillary_germany_eligibility_endpoint():
    response = client.get("/assets/default_site/ancillary/germany/eligibility")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "products" in data


def test_grid_fee_sensitivity_endpoint():
    response = client.get("/assets/default_site/grid-fees/germany/sensitivity")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "scenarios" in data


def test_hedged_revenue_endpoint():
    response = client.get("/assets/default_site/hedging/revenue")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "contracts" in data

def test_revenue_stack_allocation_latest_endpoint():
    response = client.get("/assets/default_site/revenue-stack/allocation/latest")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert data["asset_id"] == "default_site"
    assert "allocation" in data


def test_revenue_stack_allocate_endpoint():
    response = client.post("/assets/default_site/revenue-stack/allocate")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data

    if data["status"] == "ok":
        assert data["asset_id"] == "default_site"
        assert "constraints" in data
        assert "allocation" in data
        assert "excluded_products" in data


def test_execution_proposal_and_paper_trade_endpoints():
    workflow_response = client.post("/assets/default_site/workflow-runs/run")

    assert workflow_response.status_code == 200
    assert workflow_response.json()["status"] == "ok"

    proposal_response = client.post(
        "/assets/default_site/execution/proposal/build"
    )

    assert proposal_response.status_code == 200

    proposal_data = proposal_response.json()

    assert proposal_data["status"] == "ok"
    assert proposal_data["asset_id"] == "default_site"
    assert "proposal" in proposal_data
    assert "orders" in proposal_data["proposal"]
    assert "bids" in proposal_data["proposal"]
    assert "bid_lifecycle" in proposal_data["proposal"]

    if proposal_data["proposal"]["bids"]:
        first_bid = proposal_data["proposal"]["bids"][0]

        assert "bid_id" in first_bid
        assert "market_product_id" in first_bid
        assert "approval_status" in first_bid
        assert "submission_status" in first_bid
        assert "forecast_confidence_score" in first_bid
        assert "risk_adjusted_volume_mw" in first_bid
        assert "risk_adjusted_limit_price_eur_mwh" in first_bid
        assert "automation_eligibility" in first_bid

    paper_trade_response = client.post(
        "/assets/default_site/execution/paper-trade/run"
    )

    assert paper_trade_response.status_code == 200

    paper_trade_data = paper_trade_response.json()

    assert paper_trade_data["status"] in ["ok", "invalid"]
    assert paper_trade_data["asset_id"] == "default_site"

    if paper_trade_data["status"] == "ok":
        paper_trade = paper_trade_data["paper_trade"]

        assert paper_trade["adapter_id"] == "paper"
        assert paper_trade["lifecycle_status"] == "paper_filled"
        assert "bid_lifecycle" in paper_trade
        assert "bids" in paper_trade

    latest_response = client.get(
        "/assets/default_site/execution/paper-trade/latest"
    )

    assert latest_response.status_code == 200

    latest_data = latest_response.json()

    assert latest_data["status"] in ["ok", "not_found"]
    assert latest_data["asset_id"] == "default_site"

    history_response = client.get(
        "/assets/default_site/execution/paper-trades?limit=5"
    )

    assert history_response.status_code == 200

    history_data = history_response.json()

    assert history_data["status"] == "ok"
    assert history_data["asset_id"] == "default_site"
    assert "paper_trades" in history_data


def test_settlement_reconciliation_endpoints():
    client.post("/assets/default_site/workflow-runs/run")
    client.post("/assets/default_site/execution/proposal/build")
    client.post("/assets/default_site/execution/paper-trade/run")

    reconcile_response = client.post(
        "/assets/default_site/settlement/reconcile"
    )

    assert reconcile_response.status_code == 200

    reconcile_data = reconcile_response.json()

    assert reconcile_data["status"] in ["settled", "paper_reconciled"]
    assert reconcile_data["asset_id"] == "default_site"
    assert "summary" in reconcile_data
    assert "variance_drivers" in reconcile_data
    assert "primary_variance_driver" in reconcile_data

    latest_response = client.get("/assets/default_site/settlement/latest")

    assert latest_response.status_code == 200

    latest_data = latest_response.json()

    assert latest_data["status"] == "ok"
    assert latest_data["asset_id"] == "default_site"
    assert "settlement" in latest_data

    history_response = client.get("/assets/default_site/settlement/runs?limit=5")

    assert history_response.status_code == 200

    history_data = history_response.json()

    assert history_data["status"] == "ok"
    assert history_data["asset_id"] == "default_site"
    assert "settlements" in history_data


def test_execution_automation_guardrails_endpoint():
    client.post("/assets/default_site/workflow-runs/run")
    client.post("/assets/default_site/execution/proposal/build")
    client.post("/assets/default_site/execution/approval/approve")
    client.post("/assets/default_site/execution/paper-trade/run")
    client.post("/assets/default_site/settlement/reconcile")
    client.post("/assets/default_site/telemetry/demo")

    response = client.get("/assets/default_site/execution/automation-guardrails")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert data["automation_status"] in [
        "blocked",
        "human_approval_required",
        "paper_only",
        "supervised_live_candidate",
    ]
    assert "guardrails" in data
    assert "summary" in data
    assert data["summary"]["total"] >= 1
    assert "approval_policy" in [
        guardrail["guardrail"] for guardrail in data["guardrails"]
    ]


def test_execution_readiness_endpoint():
    client.post("/assets/default_site/workflow-runs/run")
    client.post("/assets/default_site/execution/proposal/build")
    client.post("/assets/default_site/execution/approval/approve")
    client.post("/assets/default_site/execution/paper-trade/run")
    client.post("/assets/default_site/settlement/reconcile")
    client.post("/assets/default_site/telemetry/demo")

    response = client.get("/assets/default_site/execution/readiness")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "readiness_status" in data
    assert "readiness_score" in data
    assert "market_adapter_status" in data
    assert "automation_status" in data
    assert "checks" in data
    assert "summary" in data
    assert "evidence" in data
    assert "recommended_actions" in data
    assert data["summary"]["total"] >= 1
    assert "operator_approval" in [
        check["check"] for check in data["checks"]
    ]


def test_execution_multi_market_allocation_endpoint():
    client.post("/assets/default_site/workflow-runs/run")
    client.post("/assets/default_site/revenue-stack/allocate")
    client.post("/assets/default_site/execution/proposal/build")
    client.post("/assets/default_site/execution/approval/approve")
    client.post("/assets/default_site/execution/paper-trade/run")
    client.post("/assets/default_site/settlement/reconcile")
    client.post("/assets/default_site/telemetry/demo")

    response = client.get(
        "/assets/default_site/execution/multi-market/allocation"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "allocation_status" in data
    assert "primary_market" in data
    assert "secondary_market" in data
    assert "summary" in data
    assert "allocation" in data
    assert "excluded_markets" in data
    assert "recommended_actions" in data
    assert "evidence" in data
    assert data["summary"]["candidate_market_count"] >= 6
    assert "epex_day_ahead" in [
        candidate["adapter_id"] for candidate in data["allocation"]
    ]


def test_germany_market_adapter_registry_endpoints():
    registry_response = client.get("/execution/market-adapters?country=Germany")

    assert registry_response.status_code == 200

    registry_data = registry_response.json()

    assert registry_data["status"] == "ok"
    assert registry_data["country"] == "Germany"
    assert "adapters" in registry_data

    adapter_ids = [
        adapter["adapter_id"] for adapter in registry_data["adapters"]
    ]

    assert "epex_day_ahead" in adapter_ids
    assert "epex_intraday_auction" in adapter_ids
    assert "epex_intraday_continuous" in adapter_ids
    assert "regelleistung_fcr" in adapter_ids
    assert "regelleistung_afrr" in adapter_ids
    assert "regelleistung_mfrr" in adapter_ids

    status_response = client.get(
        "/assets/default_site/execution/market-adapter/status"
    )

    assert status_response.status_code == 200

    status_data = status_response.json()

    assert status_data["status"] == "ok"
    assert status_data["asset_id"] == "default_site"
    assert status_data["bidding_zone"] == "DE_LU"
    assert status_data["market_adapter_status"] == "epex_day_ahead_preview_ready"
    assert status_data["live_submission_enabled"] is False
    assert status_data["planned_adapter_count"] >= 6
    assert "adapters" in status_data


def test_epex_day_ahead_preview_endpoint():
    client.post("/assets/default_site/workflow-runs/run")
    client.post("/assets/default_site/execution/proposal/build")

    response = client.get(
        "/assets/default_site/execution/epex/day-ahead/preview"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "preview" in data

    preview = data["preview"]

    assert preview["adapter_id"] == "epex_day_ahead"
    assert preview["venue"] == "EPEX SPOT"
    assert preview["bidding_zone"] == "DE_LU"
    assert preview["live_submission"] is False
    assert "orders" in preview
    assert "validation" in preview
    assert "summary" in preview

    if preview["orders"]:
        first_order = preview["orders"][0]

        assert first_order["venue"] == "EPEX SPOT"
        assert first_order["bidding_zone"] == "DE_LU"
        assert first_order["side"] in ["BUY", "SELL"]
        assert first_order["order_type"] == "LIMIT"
        assert first_order["live_submission"] is False


def test_epex_intraday_auction_preview_endpoint():
    client.post("/assets/default_site/workflow-runs/run")
    client.post("/assets/default_site/execution/proposal/build")

    response = client.get(
        "/assets/default_site/execution/epex/intraday-auction/preview"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "preview" in data

    preview = data["preview"]

    assert preview["adapter_id"] == "epex_intraday_auction"
    assert preview["venue"] == "EPEX SPOT"
    assert preview["market_segment"] == "intraday_auction"
    assert preview["bidding_zone"] == "DE_LU"
    assert preview["live_submission"] is False
    assert "orders" in preview
    assert "validation" in preview
    assert "summary" in preview

    if preview["orders"]:
        first_order = preview["orders"][0]

        assert first_order["product"] == "INTRADAY_AUCTION_15_MIN"
        assert first_order["venue"] == "EPEX SPOT"
        assert first_order["bidding_zone"] == "DE_LU"
        assert first_order["side"] in ["BUY", "SELL"]
        assert first_order["order_type"] == "LIMIT"
        assert first_order["live_submission"] is False


def test_epex_intraday_continuous_preview_endpoint():
    client.post("/assets/default_site/workflow-runs/run")
    client.post("/assets/default_site/execution/proposal/build")

    response = client.get(
        "/assets/default_site/execution/epex/intraday-continuous/preview"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "preview" in data

    preview = data["preview"]

    assert preview["adapter_id"] == "epex_intraday_continuous"
    assert preview["venue"] == "EPEX SPOT"
    assert preview["market_segment"] == "intraday_continuous"
    assert preview["bidding_zone"] == "DE_LU"
    assert preview["live_submission"] is False
    assert "assumptions" in preview
    assert "orders" in preview
    assert "validation" in preview
    assert "summary" in preview

    if preview["orders"]:
        first_order = preview["orders"][0]

        assert first_order["product"] == "INTRADAY_CONTINUOUS_15_MIN"
        assert first_order["venue"] == "EPEX SPOT"
        assert first_order["bidding_zone"] == "DE_LU"
        assert first_order["side"] in ["BUY", "SELL"]
        assert first_order["execution_style"] in [
            "aggressive",
            "passive",
            "do_not_cross",
        ]
        assert first_order["partial_fill_policy"]
        assert first_order["cancel_replace_policy"]
        assert first_order["live_submission"] is False


def test_regelleistung_fcr_preview_endpoint():
    client.post("/assets/default_site/telemetry/demo")

    response = client.get(
        "/assets/default_site/execution/regelleistung/fcr/preview"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "preview" in data

    preview = data["preview"]

    assert preview["adapter_id"] == "regelleistung_fcr"
    assert preview["venue"] == "regelleistung.net"
    assert preview["product"] == "FCR_CAPACITY"
    assert preview["bidding_zone"] == "DE_LU"
    assert preview["live_submission"] is False
    assert "capability" in preview
    assert "validation" in preview
    assert "summary" in preview
    assert "bids" in preview

    check_names = [
        check["check"] for check in preview["validation"]["checks"]
    ]

    assert "minimum_power" in check_names
    assert "symmetric_capability" in check_names
    assert "energy_duration" in check_names
    assert "soc_reserve" in check_names
    assert "fcr_prequalification" in check_names
    assert "telemetry" in check_names


def test_regelleistung_afrr_preview_endpoint():
    client.post("/assets/default_site/telemetry/demo")

    response = client.get(
        "/assets/default_site/execution/regelleistung/afrr/preview"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "preview" in data

    preview = data["preview"]

    assert preview["adapter_id"] == "regelleistung_afrr"
    assert preview["venue"] == "regelleistung.net"
    assert preview["product"] == "AFRR_CAPACITY_ENERGY"
    assert preview["bidding_zone"] == "DE_LU"
    assert preview["live_submission"] is False
    assert "capability" in preview
    assert "validation" in preview
    assert "summary" in preview
    assert "bids" in preview

    product_ids = [bid["product"] for bid in preview["bids"]]

    assert "AFRR_CAPACITY_POSITIVE" in product_ids
    assert "AFRR_CAPACITY_NEGATIVE" in product_ids
    assert "AFRR_ENERGY_POSITIVE" in product_ids
    assert "AFRR_ENERGY_NEGATIVE" in product_ids

    check_names = [
        check["check"] for check in preview["validation"]["checks"]
    ]

    assert "minimum_power" in check_names
    assert "positive_reserve_capability" in check_names
    assert "negative_reserve_capability" in check_names
    assert "soc_headroom" in check_names
    assert "afrr_prequalification" in check_names
    assert "telemetry" in check_names
    assert "capacity_reservation" in check_names


def test_regelleistung_mfrr_preview_endpoint():
    client.post("/assets/default_site/telemetry/demo")

    response = client.get(
        "/assets/default_site/execution/regelleistung/mfrr/preview"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "preview" in data

    preview = data["preview"]

    assert preview["adapter_id"] == "regelleistung_mfrr"
    assert preview["venue"] == "regelleistung.net"
    assert preview["product"] == "MFRR_CAPACITY_ENERGY"
    assert preview["bidding_zone"] == "DE_LU"
    assert preview["live_submission"] is False
    assert "capability" in preview
    assert "validation" in preview
    assert "summary" in preview
    assert "bids" in preview

    product_ids = [bid["product"] for bid in preview["bids"]]

    assert "MFRR_CAPACITY_POSITIVE" in product_ids
    assert "MFRR_CAPACITY_NEGATIVE" in product_ids
    assert "MFRR_ENERGY_POSITIVE" in product_ids
    assert "MFRR_ENERGY_NEGATIVE" in product_ids

    check_names = [
        check["check"] for check in preview["validation"]["checks"]
    ]

    assert "minimum_power" in check_names
    assert "positive_reserve_capability" in check_names
    assert "negative_reserve_capability" in check_names
    assert "soc_headroom" in check_names
    assert "mfrr_prequalification" in check_names
    assert "telemetry" in check_names
    assert "manual_activation_readiness" in check_names
    assert "capacity_reservation" in check_names


def test_asset_telemetry_endpoints():
    demo_response = client.post("/assets/default_site/telemetry/demo")

    assert demo_response.status_code == 200

    demo_data = demo_response.json()

    assert demo_data["status"] == "ok"
    assert demo_data["asset_id"] == "default_site"
    assert demo_data["telemetry"]["provider"] == "demo_local_telemetry"
    assert demo_data["telemetry"]["availability_status"] == "available"

    latest_response = client.get("/assets/default_site/telemetry/latest")

    assert latest_response.status_code == 200

    latest_data = latest_response.json()

    assert latest_data["status"] == "ok"
    assert latest_data["asset_id"] == "default_site"
    assert "telemetry" in latest_data

    history_response = client.get("/assets/default_site/telemetry/history?limit=5")

    assert history_response.status_code == 200

    history_data = history_response.json()

    assert history_data["status"] == "ok"
    assert history_data["asset_id"] == "default_site"
    assert "telemetry" in history_data


def test_execution_demo_market_submission_endpoints():
    client.post("/assets/default_site/workflow-runs/run")
    client.post("/assets/default_site/execution/proposal/build")

    blocked_response = client.post("/assets/default_site/execution/demo-submit")

    assert blocked_response.status_code == 200

    blocked_data = blocked_response.json()

    assert blocked_data["status"] == "blocked"
    assert blocked_data["asset_id"] == "default_site"
    assert "approval" in blocked_data["message"].lower()

    request_response = client.post(
        "/assets/default_site/execution/approval/request"
    )

    assert request_response.status_code == 200

    request_data = request_response.json()

    assert request_data["status"] == "ok"
    assert request_data["asset_id"] == "default_site"
    assert request_data["approval"]["status"] == "requested"
    assert "execution_proposal_id" in request_data["approval"]

    approve_response = client.post(
        "/assets/default_site/execution/approval/approve"
    )

    assert approve_response.status_code == 200

    approve_data = approve_response.json()

    assert approve_data["status"] == "ok"
    assert approve_data["asset_id"] == "default_site"
    assert approve_data["approval"]["status"] == "approved"
    assert approve_data["approval"]["execution_proposal_id"] == request_data["approval"]["execution_proposal_id"]

    latest_approval_response = client.get(
        "/assets/default_site/execution/approval/latest"
    )

    assert latest_approval_response.status_code == 200

    latest_approval_data = latest_approval_response.json()

    assert latest_approval_data["status"] == "ok"
    assert latest_approval_data["approval"]["status"] == "approved"

    approval_history_response = client.get(
        "/assets/default_site/execution/approvals?limit=5"
    )

    assert approval_history_response.status_code == 200

    approval_history_data = approval_history_response.json()

    assert approval_history_data["status"] == "ok"
    assert approval_history_data["asset_id"] == "default_site"
    assert "approvals" in approval_history_data
    assert len(approval_history_data["approvals"]) >= 1

    submit_response = client.post("/assets/default_site/execution/demo-submit")

    assert submit_response.status_code == 200

    submit_data = submit_response.json()

    assert submit_data["status"] == "ok"
    assert submit_data["asset_id"] == "default_site"
    assert submit_data["submission"]["adapter_id"] == "demo_market"
    assert submit_data["submission"]["live_submission"] is False
    assert submit_data["submission"]["approval_id"] == approve_data["approval"]["approval_id"]
    assert "lifecycle" in submit_data["submission"]
    assert "summary" in submit_data["submission"]

    latest_response = client.get("/assets/default_site/execution/submissions/latest")

    assert latest_response.status_code == 200

    latest_data = latest_response.json()

    assert latest_data["status"] == "ok"
    assert latest_data["asset_id"] == "default_site"
    assert "submission" in latest_data

    history_response = client.get("/assets/default_site/execution/submissions?limit=5")

    assert history_response.status_code == 200

    history_data = history_response.json()

    assert history_data["status"] == "ok"
    assert history_data["asset_id"] == "default_site"
    assert "submissions" in history_data
