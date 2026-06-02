from src.regulatory.regulatory_result import RegulatoryResult


GERMANY_MARKET_PROFILE_ID = "de_lu_day_ahead"


def build_germany_regulatory_assumptions(asset):
    regulatory = asset.regulatory or {}
    commercial_config = asset.commercial_config or {}
    grid_connection = asset.grid_connection or {}

    warnings = []
    requirements = build_germany_requirements()

    assumptions = {
        "country": asset.country,
        "market": asset.market,
        "market_profile_id": asset.market_profile_id,
        "bidding_zone": "DE_LU",
        "mastr_unit_id": regulatory.get("mastr_unit_id"),
        "mastr_registered": bool(regulatory.get("mastr_registered", False)),
        "grid_operator": regulatory.get("grid_operator"),
        "balancing_responsible_party": regulatory.get("balancing_responsible_party"),
        "metering_concept": regulatory.get("metering_concept"),
        "technical_connection_rule": regulatory.get("technical_connection_rule"),
        "grid_connection": grid_connection,
        "grid_fee_import_eur_per_mwh": commercial_config.get(
            "grid_fee_import_eur_per_mwh",
        ),
        "grid_fee_export_eur_per_mwh": commercial_config.get(
            "grid_fee_export_eur_per_mwh",
        ),
        "network_tariff_model": commercial_config.get("network_tariff_model"),
        "construction_cost_contribution_eur_per_mw": commercial_config.get(
            "construction_cost_contribution_eur_per_mw",
        ),
        "netting_storage_losses_only": commercial_config.get(
            "netting_storage_losses_only",
        ),
    }

    if asset.market_profile_id != GERMANY_MARKET_PROFILE_ID:
        warnings.append(
            build_warning(
                code="market_profile_not_germany_day_ahead",
                severity="medium",
                message="Asset is not assigned to the German DE-LU day-ahead market profile.",
            )
        )

    if not assumptions["mastr_registered"]:
        warnings.append(
            build_warning(
                code="mastr_registration_missing",
                severity="high",
                message="MaStR registration is missing or marked false for this German storage asset.",
            )
        )

    if not assumptions["mastr_unit_id"]:
        warnings.append(
            build_warning(
                code="mastr_unit_id_missing",
                severity="medium",
                message="MaStR unit id is missing, so asset registration traceability is incomplete.",
            )
        )

    if not assumptions["grid_operator"]:
        warnings.append(
            build_warning(
                code="grid_operator_missing",
                severity="medium",
                message="Grid operator is missing; German grid connection and tariff assumptions cannot be tied to a network area.",
            )
        )

    if not assumptions["balancing_responsible_party"]:
        warnings.append(
            build_warning(
                code="balancing_responsible_party_missing",
                severity="medium",
                message="Balancing responsible party is missing; settlement responsibility is not explicit.",
            )
        )

    if not assumptions["metering_concept"]:
        warnings.append(
            build_warning(
                code="metering_concept_missing",
                severity="high",
                message="Metering concept is missing; German storage settlement can depend on metering and use case separation.",
            )
        )

    if not assumptions["technical_connection_rule"]:
        warnings.append(
            build_warning(
                code="technical_connection_rule_missing",
                severity="medium",
                message="Technical connection rule is missing, for example VDE-AR-N 4110 or VDE-AR-N 4120 depending on voltage level.",
            )
        )

    if not grid_connection:
        warnings.append(
            build_warning(
                code="grid_connection_missing",
                severity="high",
                message="Grid connection limits are missing; dispatch power may not reflect the permitted connection.",
            )
        )
    else:
        check_grid_connection_fields(grid_connection, warnings)

    check_grid_fee_assumptions(commercial_config, warnings)

    status = classify_regulatory_status(warnings)

    return RegulatoryResult(
        status=status,
        warnings=warnings,
        requirements=requirements,
        assumptions=assumptions,
    )


def check_grid_connection_fields(grid_connection, warnings):
    required_fields = [
        "connection_capacity_mw",
        "max_import_mw",
        "max_export_mw",
    ]

    missing_fields = [
        field for field in required_fields
        if grid_connection.get(field) is None
    ]

    if missing_fields:
        warnings.append(
            build_warning(
                code="grid_connection_limits_incomplete",
                severity="high",
                message="Grid connection capacity, import limit, or export limit is missing.",
                context={"missing_fields": missing_fields},
            )
        )


def check_grid_fee_assumptions(commercial_config, warnings):
    import_fee = commercial_config.get("grid_fee_import_eur_per_mwh", 0.0)
    export_fee = commercial_config.get("grid_fee_export_eur_per_mwh", 0.0)
    tariff_model = commercial_config.get("network_tariff_model")
    construction_cost = commercial_config.get(
        "construction_cost_contribution_eur_per_mw",
        0.0,
    )

    if import_fee == 0.0 and export_fee == 0.0:
        warnings.append(
            build_warning(
                code="grid_fee_assumption_zero",
                severity="medium",
                message="Grid import and export fees are set to zero; this must be explicitly justified for German commercial use.",
            )
        )

    if not tariff_model:
        warnings.append(
            build_warning(
                code="network_tariff_model_missing",
                severity="medium",
                message="Network tariff model is missing; grid fee treatment is not auditable.",
            )
        )

    if construction_cost == 0.0:
        warnings.append(
            build_warning(
                code="construction_cost_contribution_missing",
                severity="medium",
                message="Construction cost contribution/BKZ assumption is zero or missing.",
            )
        )


def build_germany_requirements():
    return [
        {
            "code": "mastr_registration",
            "name": "MaStR registration",
            "authority": "Bundesnetzagentur",
            "description": "German generation and storage assets need traceable Marktstammdatenregister registration data.",
        },
        {
            "code": "grid_connection_limits",
            "name": "Grid connection limits",
            "authority": "Grid operator",
            "description": "Import/export limits and connection capacity should be known before dispatch profitability is treated as commercial.",
        },
        {
            "code": "technical_connection_rule",
            "name": "Technical connection rule",
            "authority": "VDE/FNN and grid operator",
            "description": "Connection rule should be captured, for example VDE-AR-N 4110 for medium voltage or VDE-AR-N 4120 for high voltage.",
        },
        {
            "code": "metering_concept",
            "name": "Metering concept",
            "authority": "Grid operator / metering operator",
            "description": "Metering concept should be explicit, especially when storage charging, losses, generation, or mixed use cases need separation.",
        },
        {
            "code": "network_tariff_assumption",
            "name": "Network tariff and fee assumption",
            "authority": "Bundesnetzagentur / grid operator",
            "description": "Grid fee and tariff assumptions should be configurable and visible because German storage treatment can depend on use case and current regulation.",
        },
    ]


def classify_regulatory_status(warnings):
    severities = [warning["severity"] for warning in warnings]

    if "high" in severities:
        return "high_risk"

    if "medium" in severities:
        return "needs_review"

    return "ready"


def build_warning(code, severity, message, context=None):
    warning = {
        "code": code,
        "severity": severity,
        "message": message,
    }

    if context:
        warning["context"] = context

    return warning
