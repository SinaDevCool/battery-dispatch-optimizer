import pytest

from backend.features.battery_usage_features import build_battery_usage_features


def test_battery_usage_features_empty_dispatch():
    result = build_battery_usage_features(
        dispatch_rows=[],
        capacity_mwh=20,
    )

    assert result["charged_mwh"] == 0.0
    assert result["discharged_mwh"] == 0.0
    assert result["throughput_mwh"] == 0.0
    assert result["equivalent_full_cycles"] == 0.0


def test_battery_usage_features_calculates_throughput_and_cycles():
    dispatch_rows = [
        {
            "action": "charge",
            "battery_energy_mwh": 5,
        },
        {
            "action": "discharge",
            "battery_energy_mwh": 4,
        },
        {
            "action": "idle",
            "battery_energy_mwh": 0,
        },
    ]

    result = build_battery_usage_features(
        dispatch_rows=dispatch_rows,
        capacity_mwh=20,
    )

    assert result["charged_mwh"] == 5.0
    assert result["discharged_mwh"] == 4.0
    assert result["throughput_mwh"] == 9.0
    assert result["equivalent_full_cycles"] == 0.225


def test_battery_usage_features_missing_columns():
    dispatch_rows = [
        {
            "action": "charge",
        }
    ]

    with pytest.raises(ValueError):
        build_battery_usage_features(
            dispatch_rows=dispatch_rows,
            capacity_mwh=20,
        )


