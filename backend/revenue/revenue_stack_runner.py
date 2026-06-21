import json
from datetime import datetime

from backend.assets.asset_loader import get_asset
from backend.data_environment import current_data_mode, is_live_mode, live_not_configured_response, mode_global_output_file
from backend.services.asset_output_paths import asset_output_dir, readable_asset_output_file
from backend.db.repositories.revenue_repository import (
    get_revenue_stack_run,
    list_revenue_stack_runs,
    save_revenue_stack_run,
)
from backend.markets.products.product_registry import (
    build_asset_product_eligibility_list,
)
from backend.revenue.calculators.day_ahead_calculator import (
    calculate_day_ahead_revenue,
)
from backend.revenue.calculators.imbalance_placeholder import (
    calculate_imbalance_revenue,
)
from backend.revenue.calculators.intraday_placeholder import (
    calculate_intraday_revenue,
)
from backend.revenue.calculators.reserve_capacity_placeholder import (
    calculate_reserve_capacity_revenue,
)


def run_asset_revenue_stack(asset_id, optimizer_engine="rule_based_v1"):
    data_mode = current_data_mode()
    asset = get_asset(asset_id)
    eligibility_results = build_asset_product_eligibility_list(asset)

    product_results = []

    for eligibility in eligibility_results:
        product = eligibility["product"]
        product_id = product["product_id"]

        revenue_result = calculate_product_revenue(
            asset=asset,
            product_id=product_id,
            optimizer_engine=optimizer_engine,
        ).to_dict()

        revenue_result["eligibility_status"] = eligibility["eligibility_status"]
        revenue_result["eligible"] = eligibility["eligible"]
        revenue_result["blocking_reasons"] = eligibility["blocking_reasons"]
        revenue_result["review_warnings"] = eligibility["review_warnings"]
        revenue_result["asset_value_context"] = build_asset_value_context(
            asset=asset,
            product_id=product_id,
            revenue_result=revenue_result,
        )

        product_results.append(revenue_result)

    total_estimated_revenue_eur = sum(
        result["estimated_revenue_eur"]
        for result in product_results
        if isinstance(result["estimated_revenue_eur"], (int, float))
    )

    result = {
        "status": "ok",
        "asset_id": asset_id,
        "data_mode": data_mode,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "optimizer_engine": optimizer_engine,
        "total_estimated_revenue_eur": round(total_estimated_revenue_eur, 2),
        "estimated_product_count": len(
            [
                product for product in product_results
                if isinstance(product["estimated_revenue_eur"], (int, float))
            ]
        ),
        "product_count": len(product_results),
        "asset_value_context": build_revenue_stack_context(
            asset=asset,
            product_results=product_results,
            total_estimated_revenue_eur=total_estimated_revenue_eur,
        ),
        "products": product_results,
    }

    revenue_stack_id = save_revenue_stack_run(result)
    result["revenue_stack_id"] = revenue_stack_id
    save_revenue_stack_result(asset_id, result)

    return result


def calculate_product_revenue(asset, product_id, optimizer_engine="rule_based_v1"):
    if product_id == "day_ahead_arbitrage":
        return calculate_day_ahead_revenue(
            asset=asset,
            optimizer_engine=optimizer_engine,
        )

    if product_id == "intraday_arbitrage":
        return calculate_intraday_revenue(asset)

    if product_id in ["fcr_capacity", "afrr_capacity", "mfrr_capacity"]:
        return calculate_reserve_capacity_revenue(
            asset=asset,
            product_id=product_id,
        )

    if product_id == "imbalance_avoidance":
        return calculate_imbalance_revenue(asset)

    raise ValueError(f"Unsupported revenue product: {product_id}")


def build_asset_value_context(asset, product_id, revenue_result):
    asset_type = str(asset.asset_type or "")
    details = revenue_result.get("details") or {}
    summary = details.get("summary") or {}

    if "solar" in asset_type:
        renewable_charge = summary.get("renewable_charge_mwh")
        renewable_share = summary.get("renewable_charge_share")
        return {
            "asset_story": "solar_colocated_revenue",
            "value_driver": "Shift forecast solar production into higher-value market intervals while preserving renewable-origin evidence.",
            "investor_meaning": "Revenue is credible only if the dispatch can show renewable-origin charge, export-limit compliance, and market value in the same evidence chain.",
            "mock_metric": {
                "label": "Renewable-origin charge",
                "value": renewable_charge,
                "unit": "MWh",
                "share": renewable_share,
            },
            "production_upgrade": "Replace mock solar forecast with generation meter data, export limits, renewable-origin accounting, and settled market revenue.",
        }

    if "industrial" in asset_type or "behind_the_meter" in asset_type:
        peak_shaved = summary.get("peak_shaved_mwh")
        return {
            "asset_story": "industrial_btm_revenue",
            "value_driver": "Prioritize site load reduction and peak shaving, then treat market access as optional upside.",
            "investor_meaning": "The revenue case should separate industrial bill value from external market trading value before production use.",
            "mock_metric": {
                "label": "Peak shaved",
                "value": peak_shaved,
                "unit": "MWh",
            },
            "production_upgrade": "Connect site-load meter data, tariff/demand-charge logic, baseline methodology, and market settlement records.",
        }

    return {
        "asset_story": "grid_scale_merchant_revenue",
        "value_driver": "Capture merchant spread value within SOC, power, efficiency, degradation, and grid connection limits.",
        "investor_meaning": "The standalone battery revenue case is credible when modelled spread capture matches physically validated dispatch.",
        "mock_metric": {
            "label": "Battery throughput",
            "value": summary.get("throughput_mwh"),
            "unit": "MWh",
        },
        "production_upgrade": "Replace mock price forecast with exchange prices, executed orders, degradation model, and settlement reconciliation.",
    }


def build_revenue_stack_context(asset, product_results, total_estimated_revenue_eur):
    numeric_products = [
        product for product in product_results
        if isinstance(product.get("estimated_revenue_eur"), (int, float))
    ]
    eligible_products = [
        product for product in product_results
        if product.get("eligibility_status") == "eligible"
    ]
    blocked_products = [
        product for product in product_results
        if product.get("eligibility_status") == "not_eligible"
    ]

    return {
        "asset_id": asset.asset_id,
        "asset_type": asset.asset_type,
        "data_mode": getattr(asset, "data_mode", None) or "mock",
        "mock_or_production": getattr(asset, "data_mode", None) or "mock",
        "primary_value_driver": build_asset_value_context(
            asset=asset,
            product_id="portfolio",
            revenue_result={"details": {}},
        )["value_driver"],
        "total_estimated_revenue_eur": round(total_estimated_revenue_eur, 2),
        "estimated_product_count": len(numeric_products),
        "eligible_product_count": len(eligible_products),
        "blocked_product_count": len(blocked_products),
        "production_boundary": "Mock revenue is generated from local forecast and dispatch evidence; production revenue must come from exchange, telemetry, and settlement connectors.",
    }


def save_revenue_stack_result(asset_id, result):
    result["data_mode"] = current_data_mode()
    global_file = mode_global_output_file("revenue_stack_results.json")
    global_file.parent.mkdir(parents=True, exist_ok=True)

    with open(global_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    asset_dir = asset_output_dir(asset_id)
    asset_dir.mkdir(parents=True, exist_ok=True)
    asset_file = asset_dir / "latest_revenue_stack.json"

    with open(asset_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    return {
        "revenue_stack_file": global_file,
        "asset_revenue_stack_file": asset_file,
    }


def load_latest_asset_revenue_stack(asset_id):
    data_mode = current_data_mode()
    asset_file = readable_asset_output_file(asset_id, "latest_revenue_stack.json", data_mode=data_mode)

    if not asset_file.exists():
        database_result = load_latest_revenue_stack_from_database(asset_id, data_mode=data_mode)

        if database_result is not None:
            return database_result

        if is_live_mode(data_mode):
            return live_not_configured_response(asset_id, "revenue_stack") | {"products": []}

        return {
            "status": "not_found",
            "data_mode": data_mode,
            "message": f"No latest revenue stack found for asset: {asset_id}",
            "asset_id": asset_id,
            "products": [],
        }

    with open(asset_file, "r", encoding="utf-8") as file:
        result = json.load(file)
        result.setdefault("data_mode", data_mode)
        if is_live_mode(data_mode) and result.get("data_mode") != "live":
            return live_not_configured_response(asset_id, "revenue_stack") | {"products": []}
        return result


def load_latest_revenue_stack_from_database(asset_id, data_mode: str | None = None):
    revenue_stack_runs = list_revenue_stack_runs(asset_id=asset_id, limit=1)

    if not revenue_stack_runs:
        return None

    revenue_stack_id = revenue_stack_runs[0]["revenue_stack_id"]
    revenue_stack_run = get_revenue_stack_run(revenue_stack_id)

    if revenue_stack_run is None:
        return None

    payload = revenue_stack_run["payload"]
    payload_data_mode = payload.get("data_mode") or ((payload.get("asset_value_context") or {}).get("data_mode"))
    if payload_data_mode and payload_data_mode != (data_mode or current_data_mode()):
        return None
    if not payload_data_mode and is_live_mode(data_mode or current_data_mode()):
        return None
    payload["status"] = payload.get("status", "ok")
    payload["asset_id"] = asset_id
    payload["data_mode"] = data_mode or current_data_mode()
    payload["revenue_stack_id"] = revenue_stack_id
    payload["storage_source"] = "database"

    return payload



