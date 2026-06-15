import json
from datetime import datetime

from backend.assets.asset_loader import get_asset
from backend.config.paths import ASSET_OUTPUTS_DIR, REVENUE_STACK_ALLOCATION_FILE
from backend.revenue.revenue_stack_runner import (
    load_latest_asset_revenue_stack,
    run_asset_revenue_stack,
)


PRODUCT_ALLOCATION_RULES = {
    "day_ahead_arbitrage": {
        "minimum_power_mw": 0.1,
        "energy_hours_per_mw": 2.0,
        "max_power_fraction": 1.0,
        "priority_adjustment": 1.0,
    },
    "intraday_arbitrage": {
        "minimum_power_mw": 0.1,
        "energy_hours_per_mw": 1.0,
        "max_power_fraction": 0.5,
        "priority_adjustment": 0.9,
    },
    "fcr_capacity": {
        "minimum_power_mw": 1.0,
        "energy_hours_per_mw": 1.0,
        "max_power_fraction": 0.5,
        "priority_adjustment": 1.05,
    },
    "afrr_capacity": {
        "minimum_power_mw": 1.0,
        "energy_hours_per_mw": 1.0,
        "max_power_fraction": 0.5,
        "priority_adjustment": 1.0,
    },
    "mfrr_capacity": {
        "minimum_power_mw": 1.0,
        "energy_hours_per_mw": 1.0,
        "max_power_fraction": 0.35,
        "priority_adjustment": 0.95,
    },
    "imbalance_avoidance": {
        "minimum_power_mw": 0.1,
        "energy_hours_per_mw": 0.5,
        "max_power_fraction": 0.25,
        "priority_adjustment": 0.75,
    },
}


def run_revenue_stack_allocation(
    asset_id,
    optimizer_engine="rule_based_v1",
    refresh_revenue_stack=False,
):
    asset = get_asset(asset_id)

    if refresh_revenue_stack:
        revenue_stack = run_asset_revenue_stack(
            asset_id=asset_id,
            optimizer_engine=optimizer_engine,
        )
    else:
        revenue_stack = load_latest_asset_revenue_stack(asset_id)

        if revenue_stack.get("status") != "ok":
            revenue_stack = run_asset_revenue_stack(
                asset_id=asset_id,
                optimizer_engine=optimizer_engine,
            )

    result = allocate_revenue_stack(asset=asset, revenue_stack=revenue_stack)
    save_revenue_stack_allocation(asset_id=asset_id, result=result)

    return result


def allocate_revenue_stack(asset, revenue_stack):
    max_power_mw = get_asset_power_mw(asset)
    max_energy_mwh = get_asset_energy_mwh(asset)

    candidates = []
    excluded_products = []

    for product in revenue_stack.get("products", []):
        candidate = build_product_candidate(
            product=product,
            max_power_mw=max_power_mw,
            max_energy_mwh=max_energy_mwh,
        )

        if candidate["eligible_for_allocation"]:
            candidates.append(candidate)
        else:
            excluded_products.append(candidate)

    candidates = sorted(
        candidates,
        key=lambda row: row["allocation_score_eur_per_mw"],
        reverse=True,
    )

    remaining_power_mw = max_power_mw
    remaining_energy_mwh = max_energy_mwh
    allocation = []

    for candidate in candidates:
        if remaining_power_mw <= 0 or remaining_energy_mwh <= 0:
            candidate["eligible_for_allocation"] = False
            candidate["exclusion_reason"] = "No remaining battery power or energy capacity."
            excluded_products.append(candidate)
            continue

        allocated_power_mw = min(
            candidate["max_allocatable_power_mw"],
            remaining_power_mw,
        )
        required_energy_mwh = allocated_power_mw * candidate["energy_hours_per_mw"]

        if required_energy_mwh > remaining_energy_mwh:
            allocated_power_mw = remaining_energy_mwh / candidate["energy_hours_per_mw"]
            required_energy_mwh = remaining_energy_mwh

        if allocated_power_mw < candidate["minimum_power_mw"]:
            candidate["eligible_for_allocation"] = False
            candidate["exclusion_reason"] = "Remaining capacity is below product minimum power."
            excluded_products.append(candidate)
            continue

        revenue_scale = allocated_power_mw / max_power_mw if max_power_mw > 0 else 0.0
        expected_revenue = candidate["estimated_revenue_eur"] * revenue_scale

        allocation.append(
            {
                "product_id": candidate["product_id"],
                "allocated_power_mw": round(allocated_power_mw, 4),
                "allocated_energy_mwh": round(required_energy_mwh, 4),
                "expected_revenue_eur": round(expected_revenue, 2),
                "revenue_per_allocated_mw_eur": round(
                    expected_revenue / allocated_power_mw,
                    2,
                ),
                "source_status": candidate["source_status"],
                "allocation_reason": candidate["allocation_reason"],
            }
        )

        remaining_power_mw -= allocated_power_mw
        remaining_energy_mwh -= required_energy_mwh

    total_expected_revenue = sum(row["expected_revenue_eur"] for row in allocation)

    return {
        "status": "ok",
        "asset_id": asset.asset_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "revenue_stack_status": revenue_stack.get("status"),
        "constraints": {
            "max_power_mw": round(max_power_mw, 4),
            "max_energy_mwh": round(max_energy_mwh, 4),
            "remaining_power_mw": round(max(remaining_power_mw, 0.0), 4),
            "remaining_energy_mwh": round(max(remaining_energy_mwh, 0.0), 4),
        },
        "allocation_count": len(allocation),
        "total_expected_revenue_eur": round(total_expected_revenue, 2),
        "allocation": allocation,
        "excluded_products": sanitize_excluded_products(excluded_products),
    }


def build_product_candidate(product, max_power_mw, max_energy_mwh):
    product_id = product.get("product_id")
    rule = PRODUCT_ALLOCATION_RULES.get(
        product_id,
        {
            "minimum_power_mw": 0.1,
            "energy_hours_per_mw": 1.0,
            "max_power_fraction": 0.25,
            "priority_adjustment": 0.5,
        },
    )

    estimated_revenue = product.get("estimated_revenue_eur")
    eligible = bool(product.get("eligible", True))
    source_status = product.get("status")
    missing_inputs = product.get("missing_inputs", []) or []
    blocking_reasons = product.get("blocking_reasons", []) or []

    candidate = {
        "product_id": product_id,
        "source_status": source_status,
        "estimated_revenue_eur": estimated_revenue,
        "minimum_power_mw": float(rule["minimum_power_mw"]),
        "energy_hours_per_mw": float(rule["energy_hours_per_mw"]),
        "max_allocatable_power_mw": round(
            max_power_mw * float(rule["max_power_fraction"]),
            4,
        ),
        "allocation_score_eur_per_mw": 0.0,
        "eligible_for_allocation": False,
        "exclusion_reason": None,
        "allocation_reason": "Ranked by expected revenue per MW under battery power and energy constraints.",
    }

    if not eligible:
        candidate["exclusion_reason"] = "Product eligibility check failed."
        candidate["blocking_reasons"] = blocking_reasons
        return candidate

    if not isinstance(estimated_revenue, (int, float)):
        candidate["exclusion_reason"] = "Product has no numeric revenue estimate."
        candidate["missing_inputs"] = missing_inputs
        return candidate

    if estimated_revenue <= 0:
        candidate["exclusion_reason"] = "Product revenue estimate is zero or negative."
        return candidate

    if max_power_mw <= 0 or max_energy_mwh <= 0:
        candidate["exclusion_reason"] = "Battery power or energy capacity is missing."
        return candidate

    if candidate["max_allocatable_power_mw"] < candidate["minimum_power_mw"]:
        candidate["exclusion_reason"] = "Product maximum allocation is below minimum power."
        return candidate

    required_energy_at_minimum = candidate["minimum_power_mw"] * candidate["energy_hours_per_mw"]

    if required_energy_at_minimum > max_energy_mwh:
        candidate["exclusion_reason"] = "Battery energy is below product minimum duration requirement."
        return candidate

    candidate["eligible_for_allocation"] = True
    candidate["allocation_score_eur_per_mw"] = round(
        (estimated_revenue / max_power_mw) * float(rule["priority_adjustment"]),
        4,
    )

    return candidate


def sanitize_excluded_products(excluded_products):
    sanitized = []

    for product in excluded_products:
        sanitized.append(
            {
                "product_id": product.get("product_id"),
                "source_status": product.get("source_status"),
                "estimated_revenue_eur": product.get("estimated_revenue_eur"),
                "exclusion_reason": product.get("exclusion_reason"),
                "missing_inputs": product.get("missing_inputs", []),
                "blocking_reasons": product.get("blocking_reasons", []),
            }
        )

    return sanitized


def get_asset_power_mw(asset):
    battery_config = asset.battery_config or {}
    grid_connection = asset.grid_connection or {}

    return float(
        grid_connection.get("connection_capacity_mw")
        or grid_connection.get("max_export_mw")
        or battery_config.get("max_discharge_power_mw")
        or battery_config.get("power_mw")
        or 0.0
    )


def get_asset_energy_mwh(asset):
    battery_config = asset.battery_config or {}

    return float(
        battery_config.get("capacity_mwh")
        or battery_config.get("energy_mwh")
        or 0.0
    )


def save_revenue_stack_allocation(asset_id, result):
    REVENUE_STACK_ALLOCATION_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(REVENUE_STACK_ALLOCATION_FILE, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    asset_dir = ASSET_OUTPUTS_DIR / asset_id
    asset_dir.mkdir(parents=True, exist_ok=True)
    asset_file = asset_dir / "latest_revenue_stack_allocation.json"

    with open(asset_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    return {
        "revenue_stack_allocation_file": REVENUE_STACK_ALLOCATION_FILE,
        "asset_revenue_stack_allocation_file": asset_file,
    }


def load_latest_revenue_stack_allocation(asset_id):
    asset_file = ASSET_OUTPUTS_DIR / asset_id / "latest_revenue_stack_allocation.json"

    if not asset_file.exists():
        return {
            "status": "not_found",
            "message": f"No latest revenue stack allocation found for asset: {asset_id}",
            "asset_id": asset_id,
            "allocation": [],
            "excluded_products": [],
        }

    with open(asset_file, "r", encoding="utf-8") as file:
        return json.load(file)



