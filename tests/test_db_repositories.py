from src.db.repositories.revenue_repository import (
    get_revenue_stack_run,
    list_revenue_product_results,
    list_revenue_stack_runs,
    save_revenue_stack_run,
)
from src.db.repositories.signal_repository import (
    get_signal_run,
    list_signal_runs,
    save_signal_run,
)


def test_signal_repository_saves_and_loads_signal_run(tmp_path):
    db_file = tmp_path / "test.sqlite"
    signal_result = {
        "summary": {
            "signal": "ACTION",
            "opportunity_level": "medium",
            "total_pnl_eur": 123.45,
            "profit_per_mw_day": 12.34,
        },
        "dispatch": [],
        "metadata": {
            "asset_id": "asset_1",
            "generated_at": "2026-01-01T00:00:00",
            "target_date": "2026-01-02",
            "forecast_provider": "local_saved_forecast",
            "forecast_model": "local_saved_forecast",
            "market_profile_id": "de_lu_day_ahead",
        },
        "optimization": {
            "optimizer_engine": "linear_v1",
        },
        "validation": {
            "status": "pass",
        },
    }

    signal_id = save_signal_run(
        signal_result=signal_result,
        asset_id="asset_1",
        db_file=db_file,
    )

    runs = list_signal_runs(
        asset_id="asset_1",
        db_file=db_file,
    )
    loaded = get_signal_run(
        signal_id=signal_id,
        db_file=db_file,
    )

    assert signal_id == 1
    assert len(runs) == 1
    assert runs[0]["signal"] == "ACTION"
    assert loaded["payload"]["summary"]["total_pnl_eur"] == 123.45


def test_revenue_repository_saves_stack_and_product_results(tmp_path):
    db_file = tmp_path / "test.sqlite"
    revenue_stack_result = {
        "asset_id": "asset_1",
        "generated_at": "2026-01-01T00:00:00",
        "optimizer_engine": "linear_v1",
        "total_estimated_revenue_eur": 100.0,
        "estimated_product_count": 1,
        "product_count": 2,
        "products": [
            {
                "product_id": "day_ahead_arbitrage",
                "status": "ok",
                "eligibility_status": "eligible",
                "estimated_revenue_eur": 100.0,
                "source": "dispatch_optimizer",
            },
            {
                "product_id": "fcr_capacity",
                "status": "assumption_required",
                "eligibility_status": "not_eligible",
                "estimated_revenue_eur": None,
                "source": "placeholder",
            },
        ],
    }

    revenue_stack_id = save_revenue_stack_run(
        revenue_stack_result=revenue_stack_result,
        db_file=db_file,
    )

    runs = list_revenue_stack_runs(
        asset_id="asset_1",
        db_file=db_file,
    )
    loaded = get_revenue_stack_run(
        revenue_stack_id=revenue_stack_id,
        db_file=db_file,
    )
    products = list_revenue_product_results(
        revenue_stack_id=revenue_stack_id,
        db_file=db_file,
    )

    assert revenue_stack_id == 1
    assert len(runs) == 1
    assert loaded["payload"]["total_estimated_revenue_eur"] == 100.0
    assert len(products) == 2
    assert products[0]["product_id"] == "day_ahead_arbitrage"
