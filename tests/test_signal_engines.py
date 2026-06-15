import pandas as pd

from backend.signals.explanation_engine import explain_battery_signal
from backend.signals.risk_engine import build_risk_flags


def sample_signal():
    return {
        "summary": {
            "signal": "ACTION",
            "total_pnl_eur": 1000.0,
            "profit_per_mw_day": 100.0,
            "opportunity_level": "medium",
            "charge_hours": 1,
            "discharge_hours": 1,
            "first_charge_timestamp": "2026-01-01 01:00:00",
            "first_discharge_timestamp": "2026-01-01 03:00:00",
            "throughput_mwh": 20.0,
            "equivalent_full_cycles": 0.5,
        },
        "dispatch": [
            {
                "timestamp": "2026-01-01 01:00:00",
                "price": -5.0,
                "action": "charge",
                "soc_mwh": 19.5,
                "battery_energy_mwh": 9.5,
                "market_value_eur": 50.0,
                "cost_eur": 10.0,
                "pnl_eur": 40.0,
                "total_pnl_eur": 40.0,
            },
            {
                "timestamp": "2026-01-01 03:00:00",
                "price": 120.0,
                "action": "discharge",
                "soc_mwh": 10.0,
                "battery_energy_mwh": 9.5,
                "market_value_eur": 1200.0,
                "cost_eur": 20.0,
                "pnl_eur": 1180.0,
                "total_pnl_eur": 1220.0,
            },
        ],
        "metadata": {
            "source": "test",
            "target_date": "2026-01-01",
        },
    }


def test_explanation_engine_returns_text():
    forecast_df = pd.DataFrame(
        {
            "timestamp": [
                "2026-01-01 00:00:00",
                "2026-01-01 01:00:00",
            ],
            "forecast_price": [10, -5],
        }
    )

    result = explain_battery_signal(
        sample_signal(),
        forecast_df=forecast_df,
    )

    assert result["status"] == "ok"
    assert "expected total PnL" in result["explanation"]
    assert "equivalent full cycle" in result["explanation"]


def test_risk_engine_detects_cycle_usage_and_negative_prices():
    forecast_df = pd.DataFrame(
        {
            "timestamp": [
                "2026-01-01 00:00:00",
                "2026-01-01 01:00:00",
            ],
            "forecast_price": [10, -5],
        }
    )

    risks = build_risk_flags(
        sample_signal(),
        forecast_df=forecast_df,
    )

    risk_types = [risk["type"] for risk in risks]

    assert "negative_price_charging" in risk_types
    assert "medium_cycle_usage" in risk_types
    assert "forecast_negative_prices" in risk_types


