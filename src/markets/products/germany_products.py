from src.markets.products.market_product_schema import MarketProduct


GERMANY_PRODUCT_DEFINITIONS = [
    {
        "product_id": "day_ahead_arbitrage",
        "name": "Day-ahead energy arbitrage",
        "country": "Germany",
        "market": "Day-ahead",
        "bidding_zone": "DE_LU",
        "settlement_interval_minutes": 15,
        "revenue_type": "energy_arbitrage",
        "requires_prequalification": False,
        "stackable_with": [
            "intraday_arbitrage",
            "imbalance_avoidance",
        ],
        "minimum_power_mw": 0.1,
        "minimum_duration_hours": 0.25,
        "risk_notes": [
            "Profitability depends on forecast quality, fees, imbalance exposure, and grid/tariff assumptions.",
        ],
        "required_asset_fields": [
            "market_profile_id",
            "battery_config",
            "commercial_config",
            "grid_connection",
        ],
    },
    {
        "product_id": "intraday_arbitrage",
        "name": "Intraday energy arbitrage",
        "country": "Germany",
        "market": "Intraday",
        "bidding_zone": "DE_LU",
        "settlement_interval_minutes": 15,
        "revenue_type": "energy_arbitrage",
        "requires_prequalification": False,
        "stackable_with": [
            "day_ahead_arbitrage",
            "imbalance_avoidance",
        ],
        "minimum_power_mw": 0.1,
        "minimum_duration_hours": 0.25,
        "risk_notes": [
            "Requires intraday price/liquidity data and execution assumptions before commercial use.",
        ],
        "required_asset_fields": [
            "market_profile_id",
            "battery_config",
            "commercial_config",
            "grid_connection",
        ],
    },
    {
        "product_id": "fcr_capacity",
        "name": "Frequency Containment Reserve capacity",
        "country": "Germany",
        "market": "Ancillary services",
        "bidding_zone": "DE_LU",
        "settlement_interval_minutes": 15,
        "revenue_type": "reserve_capacity",
        "requires_prequalification": True,
        "stackable_with": [
            "day_ahead_arbitrage",
            "intraday_arbitrage",
        ],
        "minimum_power_mw": 1.0,
        "minimum_duration_hours": 1.0,
        "risk_notes": [
            "Requires prequalification and reserve-specific availability, SOC, and activation assumptions.",
        ],
        "required_asset_fields": [
            "battery_config",
            "grid_connection",
        ],
        "required_regulatory_fields": [
            "prequalified_fcr",
            "balancing_responsible_party",
        ],
    },
    {
        "product_id": "afrr_capacity",
        "name": "Automatic Frequency Restoration Reserve capacity",
        "country": "Germany",
        "market": "Ancillary services",
        "bidding_zone": "DE_LU",
        "settlement_interval_minutes": 15,
        "revenue_type": "reserve_capacity",
        "requires_prequalification": True,
        "stackable_with": [
            "day_ahead_arbitrage",
            "intraday_arbitrage",
        ],
        "minimum_power_mw": 1.0,
        "minimum_duration_hours": 1.0,
        "risk_notes": [
            "Requires aFRR prequalification, activation assumptions, and capacity availability reservation.",
        ],
        "required_asset_fields": [
            "battery_config",
            "grid_connection",
        ],
        "required_regulatory_fields": [
            "prequalified_afrr",
            "balancing_responsible_party",
        ],
    },
    {
        "product_id": "mfrr_capacity",
        "name": "Manual Frequency Restoration Reserve capacity",
        "country": "Germany",
        "market": "Ancillary services",
        "bidding_zone": "DE_LU",
        "settlement_interval_minutes": 15,
        "revenue_type": "reserve_capacity",
        "requires_prequalification": True,
        "stackable_with": [
            "day_ahead_arbitrage",
            "intraday_arbitrage",
        ],
        "minimum_power_mw": 1.0,
        "minimum_duration_hours": 1.0,
        "risk_notes": [
            "Requires mFRR prequalification and activation/availability assumptions.",
        ],
        "required_asset_fields": [
            "battery_config",
            "grid_connection",
        ],
        "required_regulatory_fields": [
            "prequalified_mfrr",
            "balancing_responsible_party",
        ],
    },
    {
        "product_id": "imbalance_avoidance",
        "name": "Imbalance avoidance and schedule correction",
        "country": "Germany",
        "market": "Balancing responsibility",
        "bidding_zone": "DE_LU",
        "settlement_interval_minutes": 15,
        "revenue_type": "risk_reduction",
        "requires_prequalification": False,
        "stackable_with": [
            "day_ahead_arbitrage",
            "intraday_arbitrage",
        ],
        "minimum_power_mw": 0.1,
        "minimum_duration_hours": 0.25,
        "risk_notes": [
            "Requires imbalance price exposure, schedule data, and balancing responsible party assumptions.",
        ],
        "required_asset_fields": [
            "battery_config",
            "grid_connection",
        ],
        "required_regulatory_fields": [
            "balancing_responsible_party",
        ],
    },
]


def load_germany_market_products():
    return [
        MarketProduct.from_dict(product)
        for product in GERMANY_PRODUCT_DEFINITIONS
    ]
