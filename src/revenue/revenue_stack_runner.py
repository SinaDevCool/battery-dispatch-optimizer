import json
from datetime import datetime

from src.assets.asset_loader import get_asset
from src.config.paths import ASSET_OUTPUTS_DIR, REVENUE_STACK_RESULTS_FILE
from src.db.repositories.revenue_repository import (
    get_revenue_stack_run,
    list_revenue_stack_runs,
    save_revenue_stack_run,
)
from src.markets.products.product_registry import (
    build_asset_product_eligibility_list,
)
from src.revenue.calculators.day_ahead_calculator import (
    calculate_day_ahead_revenue,
)
from src.revenue.calculators.imbalance_placeholder import (
    calculate_imbalance_revenue,
)
from src.revenue.calculators.intraday_placeholder import (
    calculate_intraday_revenue,
)
from src.revenue.calculators.reserve_capacity_placeholder import (
    calculate_reserve_capacity_revenue,
)


def run_asset_revenue_stack(asset_id, optimizer_engine="rule_based_v1"):
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

        product_results.append(revenue_result)

    total_estimated_revenue_eur = sum(
        result["estimated_revenue_eur"]
        for result in product_results
        if isinstance(result["estimated_revenue_eur"], (int, float))
    )

    result = {
        "status": "ok",
        "asset_id": asset_id,
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


def save_revenue_stack_result(asset_id, result):
    REVENUE_STACK_RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(REVENUE_STACK_RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    asset_dir = ASSET_OUTPUTS_DIR / asset_id
    asset_dir.mkdir(parents=True, exist_ok=True)
    asset_file = asset_dir / "latest_revenue_stack.json"

    with open(asset_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    return {
        "revenue_stack_file": REVENUE_STACK_RESULTS_FILE,
        "asset_revenue_stack_file": asset_file,
    }


def load_latest_asset_revenue_stack(asset_id):
    asset_file = ASSET_OUTPUTS_DIR / asset_id / "latest_revenue_stack.json"

    if not asset_file.exists():
        database_result = load_latest_revenue_stack_from_database(asset_id)

        if database_result is not None:
            return database_result

        return {
            "status": "not_found",
            "message": f"No latest revenue stack found for asset: {asset_id}",
            "asset_id": asset_id,
            "products": [],
        }

    with open(asset_file, "r", encoding="utf-8") as file:
        return json.load(file)


def load_latest_revenue_stack_from_database(asset_id):
    revenue_stack_runs = list_revenue_stack_runs(asset_id=asset_id, limit=1)

    if not revenue_stack_runs:
        return None

    revenue_stack_id = revenue_stack_runs[0]["revenue_stack_id"]
    revenue_stack_run = get_revenue_stack_run(revenue_stack_id)

    if revenue_stack_run is None:
        return None

    payload = revenue_stack_run["payload"]
    payload["status"] = payload.get("status", "ok")
    payload["asset_id"] = asset_id
    payload["revenue_stack_id"] = revenue_stack_id
    payload["storage_source"] = "database"

    return payload
