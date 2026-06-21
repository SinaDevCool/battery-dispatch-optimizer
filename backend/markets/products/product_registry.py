from backend.markets.products.germany_products import load_germany_market_products
from backend.services.demo_evidence import get_demo_regulatory_value


def list_market_products(country=None):
    products = load_germany_market_products()

    if country:
        products = [
            product for product in products
            if product.country.lower() == country.lower()
        ]

    return products


def get_market_product(product_id):
    for product in list_market_products():
        if product.product_id == product_id:
            return product

    raise ValueError(f"Market product not found: {product_id}")


def build_asset_product_eligibility(asset, product):
    blocking_reasons = []
    review_warnings = []

    battery_config = asset.battery_config or {}
    grid_connection = asset.grid_connection or {}
    regulatory = asset.regulatory or {}

    max_discharge_power_mw = float(
        battery_config.get("max_discharge_power_mw", 0.0)
    )
    max_charge_power_mw = float(
        battery_config.get("max_charge_power_mw", 0.0)
    )
    capacity_mwh = float(battery_config.get("capacity_mwh", 0.0))
    power_mw = min(max_charge_power_mw, max_discharge_power_mw)

    duration_hours = None
    if power_mw > 0:
        duration_hours = capacity_mwh / power_mw

    if product.minimum_power_mw is not None and power_mw < product.minimum_power_mw:
        blocking_reasons.append(
            {
                "code": "minimum_power_not_met",
                "message": "Asset power is below the product minimum power requirement.",
                "context": {
                    "asset_power_mw": power_mw,
                    "minimum_power_mw": product.minimum_power_mw,
                },
            }
        )

    if (
        product.minimum_duration_hours is not None
        and duration_hours is not None
        and duration_hours < product.minimum_duration_hours
    ):
        blocking_reasons.append(
            {
                "code": "minimum_duration_not_met",
                "message": "Asset energy duration is below the product minimum duration requirement.",
                "context": {
                    "asset_duration_hours": duration_hours,
                    "minimum_duration_hours": product.minimum_duration_hours,
                },
            }
        )

    for field_name in product.required_asset_fields:
        if not get_nested_asset_field(asset, field_name):
            review_warnings.append(
                {
                    "code": "missing_asset_field",
                    "message": "A product-relevant asset field is missing or empty.",
                    "context": {"field": field_name},
                }
            )

    for field_name in product.required_regulatory_fields:
        if not regulatory.get(field_name) and not get_demo_regulatory_value(asset, field_name):
            review_warnings.append(
                {
                    "code": "missing_regulatory_field",
                    "message": "A product-relevant regulatory field is missing or false.",
                    "context": {"field": field_name},
                }
            )

    if product.requires_prequalification:
        prequalification_fields = [
            field for field in product.required_regulatory_fields
            if field.startswith("prequalified_")
        ]

        if prequalification_fields and not any(
            regulatory.get(field) or get_demo_regulatory_value(asset, field)
            for field in prequalification_fields
        ):
            blocking_reasons.append(
                {
                    "code": "prequalification_missing",
                    "message": "This product requires prequalification before it can be treated as commercially eligible.",
                    "context": {"required_fields": prequalification_fields},
                }
            )

    if not grid_connection:
        review_warnings.append(
            {
                "code": "grid_connection_missing",
                "message": "Grid connection assumptions are missing.",
            }
        )

    eligibility_status = classify_eligibility(blocking_reasons, review_warnings)

    return {
        "product": product.to_dict(),
        "eligibility_status": eligibility_status,
        "eligible": eligibility_status in ["eligible", "review_required"],
        "blocking_reasons": blocking_reasons,
        "review_warnings": review_warnings,
        "asset_capability": {
            "power_mw": power_mw,
            "capacity_mwh": capacity_mwh,
            "duration_hours": duration_hours,
        },
    }


def build_asset_product_eligibility_list(asset):
    return [
        build_asset_product_eligibility(asset, product)
        for product in list_market_products(country="Germany")
    ]


def get_nested_asset_field(asset, field_name):
    value = getattr(asset, field_name, None)

    if value:
        return value

    if field_name == "battery_config":
        return asset.battery_config

    if field_name == "commercial_config":
        return asset.commercial_config

    if field_name == "grid_connection":
        return asset.grid_connection

    return value


def classify_eligibility(blocking_reasons, review_warnings):
    if blocking_reasons:
        return "not_eligible"

    if review_warnings:
        return "review_required"

    return "eligible"
