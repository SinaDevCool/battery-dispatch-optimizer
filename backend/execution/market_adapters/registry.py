GERMAN_MARKET_ADAPTERS = [
    {
        "adapter_id": "paper",
        "adapter_name": "Paper market simulator",
        "country": "Germany",
        "bidding_zone": "DE_LU",
        "venue": "internal",
        "market_segment": "simulation",
        "product_family": "paper_trading",
        "environment": "paper",
        "connection_status": "available",
        "credential_status": "not_required",
        "live_submission": False,
        "supported_products": ["day_ahead_arbitrage"],
        "supported_granularity": ["hourly", "15_min"],
        "next_connection_action": "Use this adapter for risk-free execution validation.",
    },
    {
        "adapter_id": "demo_market",
        "adapter_name": "Demo market lifecycle simulator",
        "country": "Germany",
        "bidding_zone": "DE_LU",
        "venue": "internal",
        "market_segment": "simulation",
        "product_family": "demo_submission",
        "environment": "demo",
        "connection_status": "available",
        "credential_status": "not_required",
        "live_submission": False,
        "supported_products": ["day_ahead_arbitrage"],
        "supported_granularity": ["hourly", "15_min"],
        "next_connection_action": "Use this adapter to test approval, submission, award, and settlement evidence.",
    },
    {
        "adapter_id": "epex_day_ahead",
        "adapter_name": "EPEX SPOT Day-Ahead",
        "country": "Germany",
        "bidding_zone": "DE_LU",
        "venue": "EPEX SPOT",
        "market_segment": "day_ahead",
        "product_family": "energy_arbitrage",
        "environment": "preview",
        "connection_status": "preview_available",
        "credential_status": "missing",
        "live_submission": False,
        "supported_products": ["day_ahead_hourly", "day_ahead_15_min"],
        "supported_granularity": ["hourly", "15_min"],
        "next_connection_action": "Confirm EPEX market access, member or broker route, bidding zone permissions, and settlement process.",
    },
    {
        "adapter_id": "epex_intraday_auction",
        "adapter_name": "EPEX SPOT Intraday Auction",
        "country": "Germany",
        "bidding_zone": "DE_LU",
        "venue": "EPEX SPOT",
        "market_segment": "intraday_auction",
        "product_family": "short_term_energy_arbitrage",
        "environment": "preview",
        "connection_status": "preview_available",
        "credential_status": "missing",
        "live_submission": False,
        "supported_products": ["intraday_auction_15_min"],
        "supported_granularity": ["15_min"],
        "next_connection_action": "Add intraday auction product mapping, gate closure rules, and order validation.",
    },
    {
        "adapter_id": "epex_intraday_continuous",
        "adapter_name": "EPEX SPOT Intraday Continuous",
        "country": "Germany",
        "bidding_zone": "DE_LU",
        "venue": "EPEX SPOT",
        "market_segment": "intraday_continuous",
        "product_family": "continuous_rebalancing",
        "environment": "preview",
        "connection_status": "preview_available",
        "credential_status": "missing",
        "live_submission": False,
        "supported_products": ["intraday_continuous_15_min", "intraday_continuous_hourly"],
        "supported_granularity": ["15_min", "hourly"],
        "next_connection_action": "Implement order book, partial fill, spread, liquidity, and rebalancing controls before live connection.",
    },
    {
        "adapter_id": "regelleistung_fcr",
        "adapter_name": "Regelleistung FCR",
        "country": "Germany",
        "bidding_zone": "DE_LU",
        "venue": "regelleistung.net",
        "market_segment": "balancing_capacity",
        "product_family": "frequency_containment_reserve",
        "environment": "preview",
        "connection_status": "preview_available",
        "credential_status": "missing",
        "live_submission": False,
        "supported_products": ["fcr_capacity"],
        "supported_granularity": ["4_hour_blocks"],
        "next_connection_action": "Add prequalification, availability, symmetric capacity, and TSO settlement evidence.",
    },
    {
        "adapter_id": "regelleistung_afrr",
        "adapter_name": "Regelleistung aFRR",
        "country": "Germany",
        "bidding_zone": "DE_LU",
        "venue": "regelleistung.net",
        "market_segment": "balancing_capacity_energy",
        "product_family": "automatic_frequency_restoration_reserve",
        "environment": "preview",
        "connection_status": "preview_available",
        "credential_status": "missing",
        "live_submission": False,
        "supported_products": ["afrr_capacity_positive", "afrr_capacity_negative", "afrr_energy_positive", "afrr_energy_negative"],
        "supported_granularity": ["15_min", "4_hour_blocks"],
        "next_connection_action": "Add prequalification, activation telemetry, capacity reservation, and energy activation accounting.",
    },
    {
        "adapter_id": "regelleistung_mfrr",
        "adapter_name": "Regelleistung mFRR",
        "country": "Germany",
        "bidding_zone": "DE_LU",
        "venue": "regelleistung.net",
        "market_segment": "balancing_capacity_energy",
        "product_family": "manual_frequency_restoration_reserve",
        "environment": "preview",
        "connection_status": "preview_available",
        "credential_status": "missing",
        "live_submission": False,
        "supported_products": ["mfrr_capacity_positive", "mfrr_capacity_negative", "mfrr_energy_positive", "mfrr_energy_negative"],
        "supported_granularity": ["15_min", "4_hour_blocks"],
        "next_connection_action": "Add mFRR product qualification, activation workflow, and imbalance settlement rules.",
    },
]


def list_market_adapters(country=None):
    adapters = GERMAN_MARKET_ADAPTERS

    if country:
        adapters = [
            adapter
            for adapter in adapters
            if adapter["country"].lower() == country.lower()
        ]

    return adapters


def get_market_adapter(adapter_id):
    for adapter in GERMAN_MARKET_ADAPTERS:
        if adapter["adapter_id"] == adapter_id:
            return adapter

    return None


def get_asset_market_adapter_status(asset_id):
    adapters = list_market_adapters(country="Germany")
    connected = [
        adapter
        for adapter in adapters
        if adapter["connection_status"] in ["available", "preview_available"]
    ]
    planned = [
        adapter
        for adapter in adapters
        if adapter["connection_status"] in ["planned", "preview_available"]
    ]

    return {
        "status": "ok",
        "asset_id": asset_id,
        "country": "Germany",
        "bidding_zone": "DE_LU",
        "market_adapter_status": (
            "epex_day_ahead_preview_ready" if connected else "not_connected"
        ),
        "live_submission_enabled": any(
            adapter["live_submission"] for adapter in adapters
        ),
        "connected_adapter_count": len(connected),
        "planned_adapter_count": len(planned),
        "primary_adapter": connected[0] if connected else None,
        "adapters": adapters,
        "next_connection_action": "Prioritize EPEX SPOT Day-Ahead for Germany, then Intraday Auction, Intraday Continuous, FCR, aFRR, and mFRR.",
    }



