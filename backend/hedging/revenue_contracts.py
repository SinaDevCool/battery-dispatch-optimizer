DEFAULT_HEDGE_CONTRACTS = [
    {
        "contract_type": "fixed_tolling",
        "name": "Fixed tolling agreement",
        "floor_revenue_eur_per_mw_month": 8500.0,
        "upside_share_percent": 0.0,
        "availability_requirement_percent": 95.0,
        "penalty_eur_per_unavailable_mw_hour": 50.0,
    },
    {
        "contract_type": "floor_plus_upside",
        "name": "Revenue floor plus merchant upside",
        "floor_revenue_eur_per_mw_month": 6000.0,
        "upside_share_percent": 35.0,
        "availability_requirement_percent": 95.0,
        "penalty_eur_per_unavailable_mw_hour": 50.0,
    },
    {
        "contract_type": "availability_payment",
        "name": "Availability payment",
        "floor_revenue_eur_per_mw_month": 5000.0,
        "upside_share_percent": 0.0,
        "availability_requirement_percent": 98.0,
        "penalty_eur_per_unavailable_mw_hour": 80.0,
    },
    {
        "contract_type": "merchant_share",
        "name": "Merchant revenue share",
        "floor_revenue_eur_per_mw_month": 0.0,
        "upside_share_percent": 50.0,
        "availability_requirement_percent": 90.0,
        "penalty_eur_per_unavailable_mw_hour": 30.0,
    },
]


def build_hedged_revenue_view(asset, merchant_revenue_eur=0.0, contract=None):
    battery_config = asset.battery_config or {}
    grid_connection = asset.grid_connection or {}

    power_mw = float(
        grid_connection.get("connection_capacity_mw")
        or battery_config.get("max_discharge_power_mw")
        or battery_config.get("power_mw")
        or 0.0
    )
    merchant_revenue_eur = float(merchant_revenue_eur or 0.0)

    contracts = [contract] if contract else DEFAULT_HEDGE_CONTRACTS
    contract_source = "client_contract" if contract else "default_assumption_library"
    results = []

    for contract_config in contracts:
        results.append(
            evaluate_contract(
                contract=contract_config,
                power_mw=power_mw,
                merchant_revenue_eur=merchant_revenue_eur,
            )
        )

    best_contract = None
    if results:
        best_contract = sorted(
            results,
            key=lambda row: row["expected_owner_revenue_eur_per_month"],
            reverse=True,
        )[0]

    return {
        "status": "ok",
        "asset_id": asset.asset_id,
        "contract_source": contract_source,
        "merchant_revenue_eur_per_month": round(merchant_revenue_eur, 2),
        "power_mw": round(power_mw, 4),
        "best_contract": best_contract,
        "contracts": results,
        "summary": {
            "hedged_revenue_eur": (best_contract or {}).get(
                "expected_owner_revenue_eur_per_month",
                0.0,
            ),
            "merchant_upside_eur": (best_contract or {}).get(
                "owner_upside_eur_per_month",
                0.0,
            ),
            "residual_exposure_eur": (best_contract or {}).get(
                "merchant_revenue_given_away_eur_per_month",
                0.0,
            ),
            "downside_protection_eur": (best_contract or {}).get(
                "downside_protection_eur_per_month",
                0.0,
            ),
            "contract_count": len(results),
            "contract_source": contract_source,
        },
        "assumption_basis": [
            {
                "input": "merchant_revenue_eur_per_month",
                "source": "latest revenue stack, falling back to latest dispatch signal PnL",
                "value": round(merchant_revenue_eur, 2),
            },
            {
                "input": "power_mw",
                "source": "asset grid connection capacity, falling back to battery discharge power",
                "value": round(power_mw, 4),
            },
            {
                "input": "contract_terms",
                "source": contract_source,
                "value": len(results),
            },
        ],
    }


def evaluate_contract(contract, power_mw, merchant_revenue_eur):
    floor_revenue = float(contract.get("floor_revenue_eur_per_mw_month", 0.0)) * power_mw
    upside_share_percent = float(contract.get("upside_share_percent", 0.0))
    upside_revenue = max(merchant_revenue_eur - floor_revenue, 0.0)
    owner_upside = upside_revenue * (upside_share_percent / 100.0)
    expected_owner_revenue = floor_revenue + owner_upside

    downside_protection = max(floor_revenue - merchant_revenue_eur, 0.0)
    merchant_revenue_given_away = max(merchant_revenue_eur - expected_owner_revenue, 0.0)

    return {
        "contract_type": contract.get("contract_type"),
        "name": contract.get("name"),
        "floor_revenue_eur_per_mw_month": contract.get(
            "floor_revenue_eur_per_mw_month",
            0.0,
        ),
        "floor_revenue_eur_per_month": round(floor_revenue, 2),
        "upside_share_percent": upside_share_percent,
        "owner_upside_eur_per_month": round(owner_upside, 2),
        "expected_owner_revenue_eur_per_month": round(expected_owner_revenue, 2),
        "downside_protection_eur_per_month": round(downside_protection, 2),
        "merchant_revenue_given_away_eur_per_month": round(
            merchant_revenue_given_away,
            2,
        ),
        "availability_requirement_percent": contract.get(
            "availability_requirement_percent",
        ),
        "penalty_eur_per_unavailable_mw_hour": contract.get(
            "penalty_eur_per_unavailable_mw_hour",
        ),
    }



