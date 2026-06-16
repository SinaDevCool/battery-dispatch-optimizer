from __future__ import annotations

from typing import Any


READY_SCORE = {"ready": 20, "review": 10, "blocked": 0}


def build_investor_readiness(
    *,
    asset: dict[str, Any],
    evidence: dict[str, Any],
    execution: dict[str, Any],
    forecast: dict[str, Any],
    revenue: dict[str, Any],
    signal: dict[str, Any],
) -> dict[str, Any]:
    story = build_asset_investor_story(
        asset=asset,
        evidence=evidence,
        revenue=revenue,
        signal=signal,
    )
    finance = build_project_finance_case(asset=asset, revenue=revenue)
    checkpoints = [
        build_asset_identity_checkpoint(asset=asset, forecast=forecast),
        build_physical_checkpoint(signal=signal),
        build_revenue_checkpoint(revenue=revenue),
        build_execution_checkpoint(execution=execution),
        build_investor_proof_checkpoint(evidence=evidence),
    ]
    score = round(
        sum(READY_SCORE[checkpoint["decision"]] for checkpoint in checkpoints)
        / (len(checkpoints) * 20)
        * 100
    )
    overall = (
        "blocked"
        if any(checkpoint["decision"] == "blocked" for checkpoint in checkpoints)
        else "ready"
        if all(checkpoint["decision"] == "ready" for checkpoint in checkpoints)
        else "review"
    )
    open_gaps = list(evidence.get("open_gaps") or [])
    checkpoint_blockers = [
        checkpoint["next_action"]
        for checkpoint in checkpoints
        if checkpoint["decision"] == "blocked"
    ]
    blockers = [*checkpoint_blockers, *open_gaps]

    return {
        "status": "ok",
        "asset_id": asset.get("asset_id"),
        "summary": {
            "readiness_status": overall,
            "readiness_score": score,
            "checkpoint_count": len(checkpoints),
            "ready_count": count_decisions(checkpoints, "ready"),
            "review_count": count_decisions(checkpoints, "review"),
            "blocked_count": count_decisions(checkpoints, "blocked"),
            "open_gap_count": len(open_gaps),
            "data_mode": asset.get("data_mode") or (evidence.get("metadata") or {}).get("data_mode") or "mock",
            "investor_lens": story["investor_lens"],
            "recommended_next_action": (
                blockers[0] if blockers else "Use this asset in the investor demo flow."
            ),
        },
        "checkpoints": checkpoints,
        "demo_flow": build_demo_flow_rows(checkpoints),
        "diligence_rows": story["diligence_rows"],
        "finance_assumptions": finance["assumptions"],
        "finance_summary": finance["summary"],
        "project_economics": finance["economics"],
        "source_rows": build_source_rows(str(asset.get("asset_id") or "")),
        "story": story,
        "blockers": blockers,
        "portfolio_row": {
            "asset": asset.get("asset_name") or asset.get("site_name") or asset.get("asset_id"),
            "asset_type": format_asset_type(asset),
            "data_mode": asset.get("data_mode") or "mock",
            "asset_identity": checkpoints[0]["status"],
            "physical_operation": checkpoints[1]["status"],
            "revenue_case": checkpoints[2]["status"],
            "execution_safety": checkpoints[3]["status"],
            "investor_proof": checkpoints[4]["status"],
            "investor_story": story["investor_lens"],
            "next_gap": blockers[0] if blockers else "No investor demo gap shown.",
            "score": score,
            "project_cost": finance["summary"]["total_project_cost_eur"],
            "payback_years": finance["summary"]["simple_payback_years"],
            "simple_return": finance["summary"]["simple_return_percent"],
        },
    }


def build_asset_identity_checkpoint(
    *, asset: dict[str, Any], forecast: dict[str, Any]
) -> dict[str, Any]:
    has_identity = bool(asset.get("asset_id") and (asset.get("asset_name") or asset.get("site_name")))
    has_physics = bool(asset_capacity_mwh(asset) and asset_discharge_mw(asset))
    has_forecast = bool(asset.get("forecast_file") and forecast.get("status") == "ok")
    valid_rows = forecast.get("valid_row_count") or forecast.get("row_count") or 0
    decision = "ready" if has_identity and has_physics and has_forecast else "review" if has_identity else "blocked"

    return checkpoint(
        decision=decision,
        evidence=f"{format_asset_type(asset)} / {asset.get('data_mode') or 'mock'} / {valid_rows} forecast row(s)",
        identifier="asset-identity",
        investor_question="Is this a real investable asset type with a defined operating envelope?",
        label="What asset am I looking at?",
        next_action="Review asset registry",
        proof_to_show="Asset type, battery size, power limits, data mode, forecast file",
        route="/assets",
        status="ready" if decision == "ready" else decision,
    )


def build_physical_checkpoint(*, signal: dict[str, Any]) -> dict[str, Any]:
    data = signal.get("data") or {}
    summary = data.get("summary") or {}
    dispatch_rows = len(data.get("dispatch") or [])
    validation_status = str((data.get("validation") or {}).get("status") or "missing").lower()
    has_schedule = signal.get("status") == "ok" and dispatch_rows > 0
    is_pass = "pass" in validation_status
    renewable_charge = to_number(summary.get("renewable_charge_mwh")) or 0
    peak_shaved = to_number(summary.get("peak_shaved_mwh")) or 0
    specialized_evidence = (
        f"; {format_number(renewable_charge)} MWh renewable charge"
        if renewable_charge > 0
        else f"; {format_number(peak_shaved)} MWh peak shaved"
        if peak_shaved > 0
        else ""
    )
    decision = "ready" if has_schedule and is_pass else "review" if has_schedule else "blocked"

    return checkpoint(
        decision=decision,
        evidence=(
            f"{dispatch_rows} dispatch intervals; {format_number(summary.get('charged_mwh'))} MWh charge / "
            f"{format_number(summary.get('discharged_mwh'))} MWh discharge{specialized_evidence}"
        ),
        identifier="physical-operation",
        investor_question="Does the schedule respect SOC, power, efficiency, and asset-specific constraints?",
        label="Can it physically operate?",
        next_action="Open dispatch proof",
        proof_to_show="SOC trajectory, charge/discharge energy, validation result",
        route="/dispatch",
        status="validation pass" if decision == "ready" else "review validation" if decision == "review" else "blocked",
    )


def build_revenue_checkpoint(*, revenue: dict[str, Any]) -> dict[str, Any]:
    summary = revenue.get("summary") or {}
    total_revenue = to_number(summary.get("total_estimated_revenue_eur")) or 0
    eligible = int(summary.get("eligible_product_count") or 0)
    review = int(summary.get("review_product_count") or 0)
    blocked = int(summary.get("blocked_product_count") or 0)
    has_revenue = revenue.get("status") in {"ok", "partial"} and total_revenue > 0
    decision = "ready" if has_revenue and eligible > 0 else "review" if has_revenue else "blocked"

    return checkpoint(
        decision=decision,
        evidence=f"{format_currency(total_revenue)} modelled; {eligible} eligible / {review} review / {blocked} blocked product(s)",
        identifier="revenue-case",
        investor_question="Is there a commercial reason to operate this asset?",
        label="Can it earn money?",
        next_action="Inspect revenue assurance",
        proof_to_show="Modelled revenue, eligible products, blocked value",
        route="/revenue",
        status="ready" if decision == "ready" else decision,
    )


def build_execution_checkpoint(*, execution: dict[str, Any]) -> dict[str, Any]:
    summary = execution.get("summary") or {}
    readiness_score = to_number(summary.get("readiness_score")) or 0
    blocker_count = int(summary.get("blocker_count") or 0)
    readiness_status = str(summary.get("readiness_status") or "missing").lower()
    proposal_available = bool(summary.get("proposal_available"))
    is_ready = (
        execution.get("status") in {"ok", "partial"}
        and blocker_count == 0
        and (readiness_score >= 70 or "ready" in readiness_status)
    )
    decision = "ready" if is_ready else "review" if proposal_available or readiness_score > 0 else "blocked"

    return checkpoint(
        decision=decision,
        evidence=f"{format_number(readiness_score, 1)}% execution readiness; {blocker_count} blocker(s); proposal {'available' if proposal_available else 'missing'}",
        identifier="execution-safety",
        investor_question="Can the strategy be executed without pretending live trading is connected?",
        label="Can it be executed safely?",
        next_action="Open mission control",
        proof_to_show="Readiness score, proposal availability, blocker count",
        route="/execution",
        status="ready" if decision == "ready" else decision,
    )


def build_investor_proof_checkpoint(*, evidence: dict[str, Any]) -> dict[str, Any]:
    summary = evidence.get("summary") or {}
    delivery_status = str(summary.get("delivery_status") or "missing").lower()
    evidence_score = to_number(summary.get("evidence_score")) or 0
    open_gaps = int(summary.get("open_gap_count") or 0)
    report_available = bool(summary.get("report_available"))
    is_ready = evidence.get("status") in {"ok", "partial"} and report_available and open_gaps == 0
    decision = "ready" if is_ready else "review" if evidence.get("status") in {"ok", "partial"} else "blocked"

    return checkpoint(
        decision=decision,
        evidence=f"{format_number(evidence_score, 0)}% evidence score; {open_gaps} open gap(s); report {'available' if report_available else 'missing'}",
        identifier="investor-proof",
        investor_question="Can the platform package the asset case into diligence evidence?",
        label="Can we prove it to investors?",
        next_action="Open reports",
        proof_to_show="Report availability, evidence score, open gaps",
        route="/reports",
        status="client ready" if is_ready else delivery_status if delivery_status != "missing" else decision,
    )


def checkpoint(
    *,
    decision: str,
    evidence: str,
    identifier: str,
    investor_question: str,
    label: str,
    next_action: str,
    proof_to_show: str,
    route: str,
    status: str,
) -> dict[str, Any]:
    return {
        "decision": decision,
        "evidence": evidence,
        "id": identifier,
        "investor_question": investor_question,
        "label": label,
        "next_action": next_action,
        "proof_to_show": proof_to_show,
        "route": route,
        "status": status,
        "tone": {"ready": "emerald", "review": "amber", "blocked": "red"}[decision],
    }


def build_demo_flow_rows(checkpoints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "stop": index + 1,
            "page": checkpoint["label"],
            "investor_question": checkpoint["investor_question"],
            "proof_to_show": checkpoint["proof_to_show"],
            "status": checkpoint["status"],
            "demo_action": checkpoint["next_action"],
        }
        for index, checkpoint in enumerate(checkpoints)
    ]


def build_asset_investor_story(
    *,
    asset: dict[str, Any],
    evidence: dict[str, Any],
    revenue: dict[str, Any],
    signal: dict[str, Any],
) -> dict[str, Any]:
    asset_type = str(asset.get("asset_type") or "")
    revenue_value = format_currency((revenue.get("summary") or {}).get("total_estimated_revenue_eur") or 0)
    dispatch_rows = len(((signal.get("data") or {}).get("dispatch") or []))
    signal_summary = (signal.get("data") or {}).get("summary") or {}
    evidence_score = (evidence.get("summary") or {}).get("evidence_score") or "-"
    production_upgrade = (
        "Replace local mock files with live forecast feeds, telemetry, market adapters, "
        "settlement records, and production report storage while preserving the same evidence contract."
    )

    if "solar" in asset_type:
        return {
            "demo_thesis": (
                "This asset demonstrates a renewable co-located battery story: shift solar energy "
                f"into higher-value hours, preserve renewable-origin evidence, and show investors how {revenue_value} "
                f"of modelled value is supported by {dispatch_rows} validated dispatch intervals."
            ),
            "investor_lens": "Renewable developer / infrastructure investor",
            "production_upgrade": production_upgrade,
            "risk_frame": "Main diligence risk is proving renewable-origin metering and regulatory treatment before production claims.",
            "diligence_rows": [
                diligence_row(
                    "Physical configuration",
                    f"{asset_capacity_mwh(asset) or '-'} MWh battery, {asset_discharge_mw(asset) or '-'} MW discharge, solar co-location profile",
                    "The battery is not a generic merchant asset; it depends on solar availability and export limits.",
                    "Connect generation meter, storage meter, site controller, and export-limit telemetry.",
                ),
                diligence_row(
                    "Renewable origin",
                    f"{format_number(signal_summary.get('renewable_charge_mwh'))} MWh renewable charge in the mock schedule",
                    "Green charging claims need meter-backed proof before bankability review.",
                    "Use certified metering concept, GO/EEG treatment, and measured charge origin.",
                ),
                diligence_row(
                    "Commercial case",
                    f"{revenue_value} modelled revenue with report evidence score {evidence_score}",
                    "Value comes from time-shifting renewable production and optional market participation.",
                    "Replace mock prices and generation forecast with live forecast providers and settled revenue.",
                ),
            ],
        }

    if "industrial" in asset_type or "behind" in asset_type:
        return {
            "demo_thesis": (
                "This asset demonstrates a behind-the-meter industrial case: reduce site peak exposure, "
                f"respect site import/export limits, and show investors how operational savings and optional market access combine into {revenue_value} of modelled value."
            ),
            "investor_lens": "Industrial customer / project finance reviewer",
            "production_upgrade": production_upgrade,
            "risk_frame": "Main diligence risk is tariff and load-meter proof, not only market price upside.",
            "diligence_rows": [
                diligence_row(
                    "Physical configuration",
                    f"{asset_capacity_mwh(asset) or '-'} MWh battery, {asset_discharge_mw(asset) or '-'} MW discharge, peak-shaving dispatch profile",
                    "The asset must protect the industrial site first, then monetize flexibility.",
                    "Connect site load meter, EMS telemetry, tariff model, and export permission data.",
                ),
                diligence_row(
                    "Peak reduction",
                    f"{format_number(signal_summary.get('peak_shaved_mwh'))} MWh peak shaved in the mock schedule",
                    "Investor value depends on reducing high-cost demand peaks without violating site constraints.",
                    "Use measured load, tariff windows, demand charges, and verified baseline methodology.",
                ),
                diligence_row(
                    "Commercial case",
                    f"{revenue_value} modelled value with report evidence score {evidence_score}",
                    "The revenue story should separate bill savings from tradable market upside.",
                    "Split settlement evidence into site savings, market revenue, and operating costs.",
                ),
            ],
        }

    return {
        "demo_thesis": (
            "This asset demonstrates the standalone grid battery case: use the physical battery envelope "
            f"to capture merchant spreads, keep execution gated, and show investors how {revenue_value} of modelled value "
            f"is backed by {dispatch_rows} validated dispatch intervals."
        ),
        "investor_lens": "Grid-scale battery investor / asset owner",
        "production_upgrade": production_upgrade,
        "risk_frame": "Main diligence risk is live market access and settlement proof after the mock spread case is validated.",
        "diligence_rows": [
            diligence_row(
                "Physical configuration",
                f"{asset_capacity_mwh(asset) or '-'} MWh battery, {asset_discharge_mw(asset) or '-'} MW discharge, standalone grid connection",
                "Revenue claims must be bounded by capacity, power, SOC, and efficiency.",
                "Connect EMS telemetry, grid connection limits, outage state, and measured SOC.",
            ),
            diligence_row(
                "Merchant operation",
                f"{format_number(signal_summary.get('charged_mwh'))} MWh charge / {format_number(signal_summary.get('discharged_mwh'))} MWh discharge",
                "The asset earns only when spread capture survives losses, fees, and degradation.",
                "Use exchange prices, executed orders, fees, degradation model, and settlement records.",
            ),
            diligence_row(
                "Commercial case",
                f"{revenue_value} modelled revenue with report evidence score {evidence_score}",
                "The initial investor story is merchant value with optional ancillary expansion.",
                "Add live market eligibility, prequalification evidence, and realized settlement variance.",
            ),
        ],
    }


def build_project_finance_case(
    *,
    asset: dict[str, Any],
    revenue: dict[str, Any],
) -> dict[str, Any]:
    assumptions = asset.get("investment_assumptions") or {}
    commercial = asset.get("commercial_config") or {}
    capacity_mwh = to_number(asset_capacity_mwh(asset)) or 0.0
    power_mw = to_number(asset_discharge_mw(asset)) or 0.0
    battery_capex = to_number(assumptions.get("battery_capex_eur_per_mwh")) or 0.0
    power_capex = to_number(assumptions.get("power_capex_eur_per_mw")) or 0.0
    balance_of_plant = to_number(assumptions.get("balance_of_plant_eur")) or 0.0
    contingency_percent = to_number(assumptions.get("capex_contingency_percent")) or 0.0
    connection_cost = to_number(commercial.get("connection_cost_eur")) or 0.0
    contribution_per_mw = (
        to_number(commercial.get("construction_cost_contribution_eur_per_mw")) or 0.0
    )
    ordered_capacity = to_number(commercial.get("ordered_capacity_mw")) or power_mw
    opex_percent = to_number(assumptions.get("annual_fixed_opex_percent_of_capex")) or 0.0
    operating_days = to_number(assumptions.get("operating_days_per_year")) or 0.0
    downside_haircut = to_number(assumptions.get("downside_revenue_haircut_percent")) or 0.0
    daily_revenue = to_number((revenue.get("summary") or {}).get("total_estimated_revenue_eur")) or 0.0

    equipment_cost = capacity_mwh * battery_capex + power_mw * power_capex
    grid_cost = connection_cost + contribution_per_mw * ordered_capacity
    subtotal = equipment_cost + balance_of_plant + grid_cost
    contingency = subtotal * contingency_percent / 100
    total_project_cost = subtotal + contingency
    annual_revenue = daily_revenue * operating_days
    annual_fixed_opex = total_project_cost * opex_percent
    annual_net_cashflow = annual_revenue - annual_fixed_opex
    gross_margin = safe_ratio(annual_net_cashflow, annual_revenue) * 100
    simple_payback = safe_ratio(total_project_cost, annual_net_cashflow)
    simple_return = safe_ratio(annual_net_cashflow, total_project_cost) * 100
    downside_revenue = annual_revenue * (1 - downside_haircut / 100)
    downside_net_cashflow = downside_revenue - annual_fixed_opex

    summary = {
        "annual_fixed_opex_eur": round(annual_fixed_opex, 2),
        "annual_net_cashflow_eur": round(annual_net_cashflow, 2),
        "annual_revenue_run_rate_eur": round(annual_revenue, 2),
        "downside_net_cashflow_eur": round(downside_net_cashflow, 2),
        "gross_margin_percent": round(gross_margin, 1),
        "simple_payback_years": round(simple_payback, 1) if simple_payback else None,
        "simple_return_percent": round(simple_return, 1),
        "total_project_cost_eur": round(total_project_cost, 2),
    }

    return {
        "summary": summary,
        "assumptions": [
            finance_assumption_row(
                "Battery capex",
                f"{format_currency(battery_capex)} per MWh x {format_number(capacity_mwh)} MWh",
                "Benchmark cost for the battery energy block in the mock investment case.",
                "Replace with EPC and supplier quote.",
            ),
            finance_assumption_row(
                "Power conversion capex",
                f"{format_currency(power_capex)} per MW x {format_number(power_mw)} MW",
                "Benchmark cost for inverter/power capacity.",
                "Replace with PCS, transformer, and grid connection quote.",
            ),
            finance_assumption_row(
                "Balance of plant and grid cost",
                f"{format_currency(balance_of_plant + grid_cost)} before contingency",
                "Includes mock civil, installation, connection, and construction contribution assumptions.",
                "Replace with site design, DSO offer, construction budget, and owner scope split.",
            ),
            finance_assumption_row(
                "Operating days",
                f"{format_number(operating_days, 0)} day(s) per year",
                "Annualizes the demo-day revenue into a simple run-rate, not a forecast guarantee.",
                "Replace with production forecast distribution, outages, degradation, and availability plan.",
            ),
            finance_assumption_row(
                "Downside haircut",
                f"{format_number(downside_haircut, 0)}% revenue haircut",
                "Shows how sensitive simple payback is to lower realized revenue.",
                "Replace with approved downside case, hedge terms, and lender sensitivity model.",
            ),
        ],
        "economics": [
            finance_economics_row(
                "Total project cost",
                format_currency(total_project_cost),
                "Mock capex including equipment, balance of plant, grid cost, and contingency.",
                assumptions.get("production_upgrade"),
            ),
            finance_economics_row(
                "Annual revenue run-rate",
                format_currency(annual_revenue),
                "Demo-day modelled revenue annualized by the mock operating-days assumption.",
                "Replace with full-year forecast, availability, degradation, and settlement backtest.",
            ),
            finance_economics_row(
                "Annual net cashflow",
                format_currency(annual_net_cashflow),
                f"After mock fixed OPEX of {format_currency(annual_fixed_opex)}.",
                "Replace with O&M contract, insurance, land lease, augmentation reserve, and financing costs.",
            ),
            finance_economics_row(
                "Gross margin",
                f"{format_number(gross_margin, 1)}%",
                "Simple margin after fixed OPEX; excludes debt service and taxes.",
                "Replace with project finance model and accounting policy.",
            ),
            finance_economics_row(
                "Simple payback",
                f"{format_number(simple_payback, 1)} years" if simple_payback else "not meaningful",
                "Simple capex divided by annual net cashflow; not a bank-grade IRR.",
                "Replace with levered/unlevered IRR and lender downside cases.",
            ),
            finance_economics_row(
                "Downside net cashflow",
                format_currency(downside_net_cashflow),
                f"Applies a {format_number(downside_haircut, 0)}% revenue haircut to show downside effect.",
                "Replace with market downside, availability downside, degradation, and hedge sensitivity.",
            ),
        ],
    }


def finance_assumption_row(
    assumption: str,
    mock_value: str,
    investor_meaning: str,
    production_upgrade: str,
) -> dict[str, str]:
    return {
        "assumption": assumption,
        "mock_value": mock_value,
        "investor_meaning": investor_meaning,
        "production_upgrade": production_upgrade,
    }


def finance_economics_row(
    metric: str,
    value: str,
    investor_meaning: str,
    production_upgrade: Any,
) -> dict[str, str]:
    return {
        "metric": metric,
        "value": value,
        "investor_meaning": investor_meaning,
        "production_upgrade": str(production_upgrade or "Replace mock assumption with diligence-grade source."),
    }


def diligence_row(
    area: str,
    mock_evidence: str,
    investor_meaning: str,
    production_upgrade: str,
) -> dict[str, str]:
    return {
        "diligence_area": area,
        "mock_evidence": mock_evidence,
        "investor_meaning": investor_meaning,
        "production_upgrade": production_upgrade,
    }


def build_source_rows(asset_id: str) -> list[dict[str, str]]:
    return [
        {
            "backend_route": "/assets",
            "evidence_layer": "Asset identity",
            "page": "Asset Registry",
            "what_investor_sees": "Asset type, data mode, battery limits, forecast source",
        },
        {
            "backend_route": f"/assets/{asset_id}/signal/latest",
            "evidence_layer": "Physical operation",
            "page": "Dispatch Schedule",
            "what_investor_sees": "SOC-safe schedule, charge/discharge plan, validation proof",
        },
        {
            "backend_route": f"/assets/{asset_id}/revenue-summary",
            "evidence_layer": "Revenue case",
            "page": "Revenue Assurance",
            "what_investor_sees": "Modelled revenue, product eligibility, blocked product value",
        },
        {
            "backend_route": f"/assets/{asset_id}/execution-summary",
            "evidence_layer": "Execution safety",
            "page": "Mission Control",
            "what_investor_sees": "Execution readiness, proposal state, blocker count",
        },
        {
            "backend_route": f"/assets/{asset_id}/client-evidence-summary",
            "evidence_layer": "Investor proof",
            "page": "Reports",
            "what_investor_sees": "Report status, evidence score, open diligence gaps",
        },
    ]


def count_decisions(checkpoints: list[dict[str, Any]], decision: str) -> int:
    return len([checkpoint for checkpoint in checkpoints if checkpoint["decision"] == decision])


def format_asset_type(asset: dict[str, Any]) -> str:
    return " / ".join(
        value
        for value in [asset.get("asset_type"), asset.get("asset_subtype")]
        if value
    ) or "asset"


def asset_capacity_mwh(asset: dict[str, Any]) -> Any:
    return asset.get("capacity_mwh") or (asset.get("battery_config") or {}).get("capacity_mwh")


def asset_discharge_mw(asset: dict[str, Any]) -> Any:
    return asset.get("max_discharge_power_mw") or (asset.get("battery_config") or {}).get("max_discharge_power_mw")


def format_currency(value: Any) -> str:
    number = to_number(value)
    if number is None:
        return "-"
    return f"EUR {number:,.0f}"


def format_number(value: Any, digits: int = 2) -> str:
    number = to_number(value)
    if number is None:
        return "-"
    return f"{number:,.{digits}f}"


def to_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator
