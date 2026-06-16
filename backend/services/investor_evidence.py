from typing import Any


def build_forecast_proof(asset: dict[str, Any], status: dict[str, Any]):
    row_count = int(status.get("row_count") or status.get("rows") or 0)
    valid_rows = int(status.get("valid_row_count") or 0)
    duplicate_count = int(status.get("duplicate_timestamps") or 0)
    missing_count = int(status.get("missing_prices") or 0)
    invalid_count = max(row_count - valid_rows, 0)
    quality_score = calculate_forecast_quality_score(
        row_count=row_count,
        valid_rows=valid_rows,
        duplicate_count=duplicate_count,
        invalid_count=invalid_count,
        missing_count=missing_count,
    )
    profile = asset.get("data_profile") or {}
    data_mode = asset.get("data_mode") or "mock"
    forecast_source = (
        status.get("forecast_file")
        or profile.get("forecast_source")
        or asset.get("forecast_file")
    )
    market_data_mode = (
        profile.get("market_data_mode")
        or asset.get("data_source")
        or "mock forecast"
    )

    return {
        "kpis": [
            {
                "accent": "emerald"
                if quality_score >= 80
                else "amber"
                if quality_score >= 60
                else "red",
                "helper": "Backend forecast file quality score for the selected asset.",
                "label": "Forecast quality",
                "value": f"{quality_score}/100",
            },
            {
                "accent": "emerald" if valid_rows else "amber",
                "helper": "Valid forecast rows available for preview, dispatch, and scenario runs.",
                "label": "Valid rows",
                "value": valid_rows,
            },
            {
                "accent": "blue" if data_mode == "mock" else "emerald",
                "helper": "Current data boundary for investor-demo versus production evidence.",
                "label": "Data mode",
                "value": format_enum(data_mode),
            },
        ],
        "rows": [
            {
                "forecast_driver": "Selected asset forecast source",
                "mock_evidence": f"{forecast_source} / {market_data_mode}",
                "investor_meaning": "Forecast trust is tied to the selected asset profile, not a generic UI assumption.",
                "production_upgrade": "Replace mock forecast files with live provider feeds, source timestamps, and quality monitoring.",
            },
            {
                "forecast_driver": "Data quality gate",
                "mock_evidence": f"{valid_rows}/{row_count} valid row(s), {duplicate_count} duplicate timestamp(s), {missing_count} missing price(s)",
                "investor_meaning": "The forecast can only support dispatch and investor evidence when the backend file passes quality checks.",
                "production_upgrade": "Add provider SLAs, schema validation alerts, and automated stale-data rejection.",
            },
            {
                "forecast_driver": "Mock-to-production boundary",
                "mock_evidence": f"{format_enum(data_mode)} data / asset type {format_enum(asset.get('asset_type'))}",
                "investor_meaning": "Investor-demo outputs stay clearly separated from future production forecast integrations.",
                "production_upgrade": "Connect official forecast APIs, actual-price backtests, and signed data provenance.",
            },
        ],
    }


def build_scenario_proof(
    results: list[dict[str, Any]] | Any,
    asset: dict[str, Any] | None = None,
    forecast_file: str | None = None,
):
    rows = results if isinstance(results, list) else []
    best = (
        sorted(rows, key=lambda row: float(row.get("total_pnl_eur") or 0), reverse=True)[0]
        if rows
        else {}
    )
    asset_type = (asset or {}).get("asset_type") or "portfolio battery"

    return {
        "kpis": [
            {
                "accent": "emerald" if rows else "amber",
                "helper": "Backend sizing cases available for the selected asset context.",
                "label": "Sizing cases",
                "value": len(rows),
            },
            {
                "accent": "emerald" if best else "slate",
                "helper": "Highest modelled PnL case from the backend scenario run.",
                "label": "Best case",
                "value": best.get("scenario_name") or "-",
            },
            {
                "accent": "blue",
                "helper": "Forecast file used as scenario input.",
                "label": "Forecast source",
                "value": forecast_file or "default forecast",
            },
        ],
        "rows": [
            {
                "scenario_driver": "Selected asset context",
                "mock_evidence": f"{format_enum(asset_type)} / {len(rows)} sizing case(s)",
                "investor_meaning": "Scenario evidence is attached to the selected asset context instead of being invented in the UI.",
                "production_upgrade": "Persist asset-specific scenario runs with forecast snapshot IDs and optimizer run IDs.",
            },
            {
                "scenario_driver": "Best sizing economics",
                "mock_evidence": f"{best.get('scenario_name') or '-'} / {format_money(best.get('total_pnl_eur'))} / {format_number(best.get('profit_per_mw_day'))} EUR/MW-day",
                "investor_meaning": "The backend identifies which sizing case currently supports the commercial story.",
                "production_upgrade": "Link scenario economics to capex, degradation, availability, and contracted market access.",
            },
            {
                "scenario_driver": "Forecast-to-scenario trace",
                "mock_evidence": forecast_file or "default forecast file",
                "investor_meaning": "Scenario outputs remain traceable to the forecast input used for mock investor evidence.",
                "production_upgrade": "Attach provider provenance, actual-vs-forecast validation, and scenario version history.",
            },
        ],
    }


def build_stress_proof(
    results: list[dict[str, Any]] | Any,
    asset: dict[str, Any] | None = None,
    forecast_file: str | None = None,
):
    rows = results if isinstance(results, list) else []
    worst = (
        sorted(rows, key=lambda row: float(row.get("total_pnl_eur") or 0))[0]
        if rows
        else {}
    )
    negative_count = len(
        [row for row in rows if float(row.get("total_pnl_eur") or 0) < 0]
    )
    investor_cases = [
        row.get("investor_case") or row.get("scenario_name")
        for row in rows
        if row.get("investor_case") or row.get("scenario_name")
    ]
    asset_type = (asset or {}).get("asset_type") or "portfolio battery"

    return {
        "kpis": [
            {
                "accent": "red" if negative_count else "emerald",
                "helper": "Stress cases with negative modelled PnL.",
                "label": "Downside breaches",
                "value": negative_count,
            },
            {
                "accent": "amber" if worst else "slate",
                "helper": "Lowest modelled PnL case from the backend stress run.",
                "label": "Worst case",
                "value": worst.get("scenario_name") or "-",
            },
            {
                "accent": "blue",
                "helper": "Selected asset type used for stress interpretation.",
                "label": "Asset type",
                "value": format_enum(asset_type),
            },
        ],
        "rows": [
            {
                "stress_driver": "Downside guardrail",
                "mock_evidence": f"{negative_count} negative case(s) / {len(rows)} stress case(s)",
                "investor_meaning": "Automation and investor claims should stay gated when downside cases breach the value story.",
                "production_upgrade": "Connect live risk limits, hedge contracts, and approved downside thresholds.",
            },
            {
                "stress_driver": "Worst stress economics",
                "mock_evidence": f"{worst.get('scenario_name') or '-'} / {format_money(worst.get('total_pnl_eur'))}",
                "investor_meaning": "The downside case is backend-calculated and visible before strategy escalation.",
                "production_upgrade": "Persist stress scenarios with market regime labels and risk committee approvals.",
            },
            {
                "stress_driver": "Investor downside cases",
                "mock_evidence": "; ".join(investor_cases[:6]) or "No investor stress cases loaded",
                "investor_meaning": "The stress run is labelled in investor language: base case, price downside, upside, dispatch underperformance, degradation, and asset-specific risk.",
                "production_upgrade": "Replace mock case labels with approved downside policies, traded hedge terms, and live availability telemetry.",
            },
            {
                "stress_driver": "Forecast-to-stress trace",
                "mock_evidence": forecast_file or "default forecast file",
                "investor_meaning": "Stress evidence is tied to the forecast input used for the selected asset demo.",
                "production_upgrade": "Attach production forecast provenance, scenario versioning, and settlement feedback loops.",
            },
        ],
    }


def calculate_forecast_quality_score(
    row_count: int,
    valid_rows: int,
    duplicate_count: int,
    invalid_count: int,
    missing_count: int,
):
    if row_count <= 0:
        return 0
    coverage_score = min((valid_rows / row_count) * 100, 100)
    score = coverage_score - duplicate_count * 8 - invalid_count * 6 - missing_count * 6
    return max(0, min(100, round(score)))


def build_regulatory_proof(
    asset: dict[str, Any],
    classification: dict[str, Any],
    eeg: dict[str, Any],
    ancillary: dict[str, Any],
    blockers: list[str],
):
    asset_type = asset.get("asset_type")
    storage_mode = classification.get("storage_classification") or classification.get("storage_mode") or "not classified"
    ancillary_count = ancillary.get("eligible_product_count") or len(ancillary.get("eligible_products") or [])
    products = ancillary.get("products") or []
    blocked_products = [
        product
        for product in products
        if product.get("eligibility_status") == "not_eligible"
        or has_issue_list(product.get("blocking_reasons"))
    ]
    eeg_status = eeg.get("status") or ("eligible" if eeg.get("eeg_eligible") else "needs_review")
    approval_status = "needs_review" if blockers else "approval_ready"

    kpis = [
        {
            "accent": "amber" if blockers else "emerald",
            "helper": "Backend regulatory summary status for the selected asset.",
            "label": "Approval gate",
            "value": format_enum(approval_status),
        },
        {
            "accent": "emerald" if eeg.get("eeg_eligible") else "amber",
            "helper": "EEG and origin-risk evidence before market automation.",
            "label": "EEG status",
            "value": format_enum(eeg_status),
        },
        {
            "accent": "emerald" if ancillary_count else "amber",
            "helper": "Eligible ancillary products for German market participation.",
            "label": "Eligible products",
            "value": ancillary_count,
        },
    ]

    rows = [
        {
            "regulatory_driver": "Storage classification",
            "mock_evidence": f"{format_enum(storage_mode)} / asset type {format_enum(asset_type)}",
            "investor_meaning": "The asset is classified before revenue, route selection, or automation claims are trusted.",
            "production_upgrade": "Replace mock classification with signed asset registration, metering concept, and legal review evidence.",
        },
        {
            "regulatory_driver": "EEG and origin-risk gate",
            "mock_evidence": f"EEG eligible {eeg.get('eeg_eligible')} / mixed-origin risk {eeg.get('mixed_origin_risk') or 'not flagged'}",
            "investor_meaning": "Renewable-support and mixed-origin risks are separated from generic battery trading evidence.",
            "production_upgrade": "Connect official EEG assessment, renewable-origin metering, certificates, and settlement evidence.",
        },
        {
            "regulatory_driver": "Ancillary market eligibility",
            "mock_evidence": f"{ancillary_count} eligible product(s) / {len(blocked_products)} blocked product(s)",
            "investor_meaning": "Reserve-market upside is only shown where the backend eligibility model allows it.",
            "production_upgrade": "Connect prequalification status, market rule updates, and official product eligibility checks.",
        },
    ]

    if asset_type == "industrial_behind_the_meter_battery":
        rows[0]["investor_meaning"] = "Behind-the-meter value is checked against site, metering, and German market assumptions before external upside is claimed."
    elif asset_type == "solar_colocated_battery":
        rows[1]["investor_meaning"] = "Solar co-location and green-origin claims remain gated by EEG and metering evidence."

    return {
        "kpis": kpis,
        "rows": rows,
    }


def build_client_report_proof(
    asset: dict[str, Any],
    completeness: dict[str, Any],
    report: dict[str, Any],
    revenue: dict[str, Any],
    regulatory: dict[str, Any],
    execution: dict[str, Any],
):
    asset_type = asset.get("asset_type")
    report_available = report.get("status") == "ok"
    open_gap_count = int(completeness.get("missing_count") or 0)
    evidence_score = completeness.get("score")
    revenue_summary = revenue.get("summary") or {}
    regulatory_summary = regulatory.get("summary") or {}
    execution_summary = execution.get("summary") or {}
    latest_signal = (
        (execution.get("latest_signal") or {})
        if execution.get("latest_signal")
        else (revenue.get("latest_signal") or {})
    )
    signal_data = latest_signal.get("data") or {}
    signal_summary = signal_data.get("summary") or {}
    dispatch_rows = signal_data.get("dispatch") or []
    report_state = "HTML report available" if report_available else "Report artifact pending"
    evidence_state = (
        f"{completeness.get('complete_count') or 0}/"
        f"{completeness.get('check_count') or 0} evidence checks complete"
    )

    if asset_type == "solar_colocated_battery":
        return {
            "kpis": [
                {
                    "accent": "emerald" if report_available else "amber",
                    "helper": "Investor packet includes renewable-origin and co-location evidence.",
                    "label": "Green report state",
                    "value": "available" if report_available else "draft",
                },
                {
                    "accent": "amber" if open_gap_count > 0 else "emerald",
                    "helper": "Open items before the renewable evidence packet is defensible.",
                    "label": "Green evidence gaps",
                    "value": open_gap_count,
                },
                {
                    "accent": "blue",
                    "helper": "Mock report ties solar shifting to modelled commercial value.",
                    "label": "Reported value",
                    "value": format_money(revenue_summary.get("total_estimated_revenue_eur")),
                },
            ],
            "rows": [
                {
                    "report_section": "Renewable-origin dispatch evidence",
                    "mock_evidence": (
                        f"{format_energy(signal_summary.get('renewable_charge_mwh') or sum_rows(dispatch_rows, 'renewable_charge_mwh'))} "
                        f"renewable charge / {format_percent(signal_summary.get('renewable_charge_share'))} green charge share"
                    ),
                    "investor_meaning": "The report explains whether revenue is backed by renewable-origin charging, not generic battery operation.",
                    "production_upgrade": "Connect generation meter, battery meter, renewable-origin tags, and certificate/EEG settlement evidence.",
                },
                {
                    "report_section": "Co-located export and curtailment proof",
                    "mock_evidence": (
                        f"{format_energy(sum_rows(dispatch_rows, 'site_export_headroom_mwh'))} export headroom / "
                        f"{format_energy(sum_rows(dispatch_rows, 'solar_available_mwh'))} solar available"
                    ),
                    "investor_meaning": "Investors can see whether the solar battery respects the shared export envelope before revenue is trusted.",
                    "production_upgrade": "Replace mock headroom with inverter, export-limit telemetry, and DSO connection evidence.",
                },
                {
                    "report_section": "Investor green evidence packet",
                    "mock_evidence": (
                        f"{format_money(revenue_summary.get('total_estimated_revenue_eur'))} modelled / "
                        f"EEG {regulatory_summary.get('eeg_eligible', 'not evaluated')} / {report_state}"
                    ),
                    "investor_meaning": "The report joins green compliance, revenue value, and execution readiness into one diligence packet.",
                    "production_upgrade": "Connect official compliance evidence, exchange settlement, and generated PDF/export workflow.",
                },
            ],
        }

    if asset_type == "industrial_behind_the_meter_battery":
        return {
            "kpis": [
                {
                    "accent": "emerald" if report_available else "amber",
                    "helper": "Investor packet focuses on site savings plus optional market upside.",
                    "label": "Site report state",
                    "value": "available" if report_available else "draft",
                },
                {
                    "accent": "amber" if open_gap_count > 0 else "emerald",
                    "helper": "Open metering, tariff, or execution evidence gaps.",
                    "label": "Site evidence gaps",
                    "value": open_gap_count,
                },
                {
                    "accent": readiness_tone(execution_summary.get("readiness_status")),
                    "helper": "Execution readiness behind the report narrative.",
                    "label": "Execution proof",
                    "value": execution_summary.get("readiness_status") or "not evaluated",
                },
            ],
            "rows": [
                {
                    "report_section": "Peak shaving and site savings evidence",
                    "mock_evidence": (
                        f"{format_energy(signal_summary.get('peak_shaved_mwh') or sum_rows(dispatch_rows, 'peak_shaved_mwh'))} peak shaved / "
                        f"{format_energy(sum_rows(dispatch_rows, 'battery_site_load_offset_mwh'))} site load offset"
                    ),
                    "investor_meaning": "The report can prove the industrial asset creates value by reducing site load and peak exposure.",
                    "production_upgrade": "Connect site meter telemetry, tariff model, contracted capacity, and load forecast data.",
                },
                {
                    "report_section": "Optional market upside evidence",
                    "mock_evidence": (
                        f"{format_money(revenue_summary.get('total_estimated_revenue_eur'))} modelled / "
                        f"execution {execution_summary.get('readiness_status') or 'not evaluated'}"
                    ),
                    "investor_meaning": "Optional market revenue is separated from behind-the-meter savings so the investor story stays honest.",
                    "production_upgrade": "Connect market adapter status, settlement split, and site-bill reconciliation.",
                },
                {
                    "report_section": "Industrial delivery readiness",
                    "mock_evidence": f"{evidence_state} / {open_gap_count} open gap(s) / {report_state}",
                    "investor_meaning": "The report can show which industrial evidence remains mock before production delivery.",
                    "production_upgrade": "Replace local mock evidence with production meter, billing, EMS, and settlement feeds.",
                },
            ],
        }

    return {
        "kpis": [
            {
                "accent": "emerald" if report_available else "amber",
                "helper": "Latest selected-asset report artifact.",
                "label": "Report state",
                "value": "available" if report_available else "draft",
            },
            {
                "accent": "amber" if open_gap_count > 0 else "emerald",
                "helper": "Remaining evidence gaps before investor delivery.",
                "label": "Open gaps",
                "value": open_gap_count,
            },
            {
                "accent": "emerald" if float(evidence_score or 0) >= 80 else "amber" if evidence_score else "slate",
                "helper": "Data completeness score used to guard report delivery.",
                "label": "Evidence score",
                "value": "-" if evidence_score is None else f"{evidence_score} / 100",
            },
        ],
        "rows": [
            {
                "report_section": "Physical dispatch and SOC proof",
                "mock_evidence": (
                    f"{format_energy(signal_summary.get('throughput_mwh') or get_dispatch_throughput(dispatch_rows))} throughput / "
                    f"{format_energy(last_dispatch_value(dispatch_rows, 'soc_mwh'))} ending SOC"
                ),
                "investor_meaning": "The report packages physical dispatch evidence so the investor sees the battery could actually follow the value case.",
                "production_upgrade": "Connect EMS SOC, meter telemetry, degradation model, and validated dispatch records.",
            },
            {
                "report_section": "Revenue and execution readiness",
                "mock_evidence": (
                    f"{format_money(revenue_summary.get('total_estimated_revenue_eur'))} modelled / "
                    f"execution {execution_summary.get('readiness_status') or 'not evaluated'}"
                ),
                "investor_meaning": "The report connects merchant revenue, route readiness, and automation gates instead of presenting isolated numbers.",
                "production_upgrade": "Connect exchange prices, route certification, market submissions, and settlement evidence.",
            },
            {
                "report_section": "Mock-to-production evidence boundary",
                "mock_evidence": f"{evidence_state} / {open_gap_count} open gap(s) / {report_state}",
                "investor_meaning": "The report remains clearly marked as mock investor-demo evidence until production integrations are connected.",
                "production_upgrade": "Add production data connectors, PDF export, archive governance, and signed audit trail.",
            },
        ],
    }


def build_revenue_proof(
    allocation: dict[str, Any],
    asset: dict[str, Any],
    revenue_rows: list[dict[str, Any]],
    signal: dict[str, Any],
    hedging: dict[str, Any],
    total_revenue: Any,
):
    asset_type = asset.get("asset_type")
    signal_data = signal.get("data") or {}
    signal_summary = signal_data.get("summary") or {}
    dispatch_rows = signal_data.get("dispatch") or []
    physics_model = (signal_data.get("asset_physics") or {}).get(
        "physics_model",
        "mock dispatch physics",
    )
    allocation_rows = allocation.get("results") or allocation.get("allocation") or []
    hedge_summary = hedging.get("summary") or {}
    total_revenue_value = numeric(total_revenue)
    throughput = get_dispatch_throughput_from_summary(signal_summary, dispatch_rows)
    revenue_per_mwh = safe_divide(total_revenue_value, throughput)
    allocated_power = sum_rows(allocation_rows, "allocated_capacity_mw")
    power_mw = asset.get("max_discharge_power_mw") or asset.get("max_charge_power_mw")
    eligible_route_count = len(
        [row for row in revenue_rows if row.get("eligibility_status") == "eligible"]
    )
    top_revenue_route = sorted(
        revenue_rows,
        key=lambda row: numeric(row.get("estimated_revenue_eur")),
        reverse=True,
    )[0] if revenue_rows else {}
    allocation_text = (
        f"{len(allocation_rows)} allocation route(s) loaded"
        if allocation_rows
        else "Allocation evidence pending"
    )

    if asset_type == "solar_colocated_battery":
        return {
            "kpis": [
                {
                    "accent": "emerald",
                    "helper": "Mock solar-origin energy shifted through the battery.",
                    "label": "Renewable charge",
                    "value": format_energy(signal_summary.get("renewable_charge_mwh") or sum_rows(dispatch_rows, "renewable_charge_mwh")),
                },
                {
                    "accent": "blue",
                    "helper": "Share of charged energy backed by renewable-origin fields.",
                    "label": "Green charge share",
                    "value": format_percent(signal_summary.get("renewable_charge_share")),
                },
                {
                    "accent": "emerald",
                    "helper": "Revenue linked to the selected solar plus battery profile.",
                    "label": "Modelled revenue",
                    "value": format_money(total_revenue_value),
                },
            ],
            "rows": [
                {
                    "revenue_driver": "Renewable shifting value",
                    "mock_evidence": f"{format_energy(signal_summary.get('renewable_charge_mwh') or sum_rows(dispatch_rows, 'renewable_charge_mwh'))} renewable-origin charge / {format_percent(signal_summary.get('renewable_charge_share'))} green charge share",
                    "investor_meaning": "The revenue case is not generic arbitrage; it is tied to renewable-origin charging and solar shifting.",
                    "production_upgrade": "Replace mock solar generation with inverter, meter, and production forecast feeds.",
                },
                {
                    "revenue_driver": "Export and curtailment proof",
                    "mock_evidence": f"{format_energy(sum_rows(dispatch_rows, 'solar_available_mwh'))} solar available / {format_energy(sum_rows(dispatch_rows, 'site_export_headroom_mwh'))} export headroom",
                    "investor_meaning": "The battery can monetize solar energy without claiming unavailable grid-charged green value.",
                    "production_upgrade": "Connect generation meter, export-limit telemetry, and renewable-origin settlement evidence.",
                },
                {
                    "revenue_driver": "Market revenue stack",
                    "mock_evidence": f"{eligible_route_count}/{len(revenue_rows) or 0} eligible route(s); top route {top_revenue_route.get('product_id') or 'pending'}; {format_money(total_revenue_value)} modelled",
                    "investor_meaning": "Revenue is supported by market products only where the selected solar battery remains eligible.",
                    "production_upgrade": "Link exchange prices, market access status, and certificate/EEG eligibility checks.",
                },
            ],
        }

    if asset_type == "industrial_behind_the_meter_battery":
        return {
            "kpis": [
                {
                    "accent": "emerald",
                    "helper": "Mock site demand reduced by battery dispatch.",
                    "label": "Peak shaved",
                    "value": format_energy(signal_summary.get("peak_shaved_mwh") or sum_rows(dispatch_rows, "peak_shaved_mwh")),
                },
                {
                    "accent": "amber",
                    "helper": "Residual site import after battery offset.",
                    "label": "Net site import",
                    "value": format_energy(sum_rows(dispatch_rows, "net_site_import_mwh")),
                },
                {
                    "accent": "blue",
                    "helper": "Eligible market routes on top of behind-the-meter value.",
                    "label": "Optional market routes",
                    "value": f"{eligible_route_count}/{len(revenue_rows) or 0}",
                },
            ],
            "rows": [
                {
                    "revenue_driver": "Peak shaving and avoided import",
                    "mock_evidence": f"{format_energy(signal_summary.get('peak_shaved_mwh') or sum_rows(dispatch_rows, 'peak_shaved_mwh'))} peak shaved / {format_energy(sum_rows(dispatch_rows, 'battery_site_load_offset_mwh'))} site load offset",
                    "investor_meaning": "The revenue case includes site-bill value, not only exchange trading revenue.",
                    "production_upgrade": "Replace mock load with site meter telemetry, tariff model, and contracted capacity data.",
                },
                {
                    "revenue_driver": "Connection-limit proof",
                    "mock_evidence": f"{format_energy(sum_rows(dispatch_rows, 'peak_excess_before_mwh'))} peak excess before / {format_energy(sum_rows(dispatch_rows, 'peak_excess_after_mwh'))} after battery",
                    "investor_meaning": "The battery respects the industrial connection limit before claiming external market revenue.",
                    "production_upgrade": "Connect live grid connection limits, load forecasts, and DSO capacity constraints.",
                },
                {
                    "revenue_driver": "Optional market upside",
                    "mock_evidence": f"{eligible_route_count}/{len(revenue_rows) or 0} eligible route(s); {allocation_text}; {format_money(total_revenue_value)} modelled",
                    "investor_meaning": "Optional market participation is upside layered on top of behind-the-meter savings.",
                    "production_upgrade": "Connect market adapter readiness, prequalification, and metered settlement feeds.",
                },
            ],
        }

    return {
        "kpis": [
            {
                "accent": "emerald",
                "helper": "Charge plus discharge volume behind the merchant case.",
                "label": "Physical throughput",
                "value": format_energy(throughput),
            },
            {
                "accent": "blue",
                "helper": "Revenue normalized by physical battery movement.",
                "label": "Revenue per MWh",
                "value": "-" if revenue_per_mwh is None else f"{format_money(revenue_per_mwh)}/MWh",
            },
            {
                "accent": "emerald" if allocated_power > 0 else "amber",
                "helper": "Capacity assigned to monetization routes.",
                "label": "Allocated power",
                "value": f"{format_number(allocated_power, 1)} MW" if allocated_power > 0 else f"{format_number(power_mw, 1)} MW available" if power_mw else "-",
            },
        ],
        "rows": [
            {
                "revenue_driver": "Arbitrage spread capture",
                "mock_evidence": f"{format_energy(signal_summary.get('charged_mwh') or sum_rows(dispatch_rows, 'grid_energy_mwh'))} charged / {format_energy(signal_summary.get('discharged_mwh'))} discharged / {format_energy(throughput)} throughput",
                "investor_meaning": "Merchant revenue is backed by actual charge/discharge movement, not static UI assumptions.",
                "production_upgrade": "Replace mock forecast with exchange prices and live battery telemetry.",
            },
            {
                "revenue_driver": "Battery constraint proof",
                "mock_evidence": f"{physics_model}; SOC and power constraints applied in dispatch",
                "investor_meaning": "The model accounts for physical battery limits before revenue is treated as tradable.",
                "production_upgrade": "Connect EMS SOC, availability, degradation model, and meter validation.",
            },
            {
                "revenue_driver": "Bankable commercial bridge",
                "mock_evidence": f"{format_money(total_revenue_value)} modelled / {format_money(hedge_summary.get('hedged_revenue_eur'))} hedged / {allocation_text}",
                "investor_meaning": "The investor case separates executable merchant value from hedge protection and blocked upside.",
                "production_upgrade": "Connect portfolio hedges, exchange settlements, and allocation decisions.",
            },
        ],
    }


def build_execution_proof(
    asset: dict[str, Any],
    allocation: dict[str, Any],
    automation_control: dict[str, Any],
    proposal: dict[str, Any],
    readiness: dict[str, Any],
    signal: dict[str, Any],
    telemetry: dict[str, Any],
):
    asset_type = asset.get("asset_type")
    signal_data = signal.get("data") or {}
    signal_summary = signal_data.get("summary") or {}
    dispatch_rows = signal_data.get("dispatch") or []
    physics_model = (signal_data.get("asset_physics") or {}).get(
        "physics_model",
        "mock dispatch physics",
    )
    proposal_payload = proposal.get("proposal") or {}
    bids = get_proposal_bids(proposal_payload)
    bid_count = len(bids) or int((proposal_payload.get("summary") or {}).get("order_count") or 0)
    bid_energy = sum_rows(bids, "volume_mwh") or sum_rows(bids, "energy_mwh")
    primary_market = allocation.get("primary_market") or {}
    route_name = primary_market.get("market_name") or proposal_payload.get("market") or "No primary route selected"
    gate_status = (
        primary_market.get("market_gate_status")
        or (allocation.get("summary") or {}).get("market_gate_status")
        or readiness.get("readiness_status")
        or "not evaluated"
    )
    automation_mode = (
        automation_control.get("automation_mode")
        or automation_control.get("automation_status")
        or proposal_payload.get("execution_mode")
        or "mock gated automation"
    )
    selected_route = primary_market.get("market_name") or proposal_payload.get("market")
    readiness_score = numeric(readiness.get("readiness_score"))
    telemetry_payload = telemetry.get("telemetry") or {}

    if asset_type == "solar_colocated_battery":
        return {
            "kpis": [
                {
                    "accent": "emerald",
                    "helper": "Stored energy origin is tracked before bid evidence is trusted.",
                    "label": "Renewable execution",
                    "value": format_energy(signal_summary.get("renewable_charge_mwh") or sum_rows(dispatch_rows, "renewable_charge_mwh")),
                },
                {
                    "accent": "blue",
                    "helper": "Submission must respect the shared solar plus storage export envelope.",
                    "label": "Export headroom",
                    "value": format_energy(sum_rows(dispatch_rows, "site_export_headroom_mwh")),
                },
                {
                    "accent": "emerald" if selected_route else "amber",
                    "helper": "Selected market route for renewable-shifting execution.",
                    "label": "Execution route",
                    "value": selected_route or "route pending",
                },
            ],
            "rows": [
                {
                    "execution_driver": "Renewable-origin order gating",
                    "mock_evidence": f"{format_energy(signal_summary.get('renewable_charge_mwh') or sum_rows(dispatch_rows, 'renewable_charge_mwh'))} renewable charge / {physics_model}",
                    "investor_meaning": "The system does not treat every stored MWh as green unless the mock dispatch marks renewable-origin charging.",
                    "production_upgrade": "Connect generation meter, battery meter, origin tags, and certificate/EEG settlement evidence.",
                },
                {
                    "execution_driver": "Co-located export constraint",
                    "mock_evidence": f"{format_energy(sum_rows(dispatch_rows, 'site_export_headroom_mwh'))} export headroom / {format_energy(sum_rows(dispatch_rows, 'solar_available_mwh'))} solar available",
                    "investor_meaning": "Solar and battery execution share a site export limit, so bid volume must fit physical headroom.",
                    "production_upgrade": "Use live inverter limits, export-limit telemetry, and DSO connection constraints.",
                },
                {
                    "execution_driver": "Market route with green constraints",
                    "mock_evidence": f"{route_name} / gate {format_enum(gate_status)} / {bid_count} bid(s)",
                    "investor_meaning": "Market execution is only credible when the route, gate, and renewable metering story align.",
                    "production_upgrade": "Replace mock adapter with exchange submission, route certification, and metered settlement.",
                },
            ],
        }

    if asset_type == "industrial_behind_the_meter_battery":
        return {
            "kpis": [
                {
                    "accent": "emerald",
                    "helper": "Execution protects the industrial bill before market upside.",
                    "label": "Peak protected",
                    "value": format_energy(signal_summary.get("peak_shaved_mwh") or sum_rows(dispatch_rows, "peak_shaved_mwh")),
                },
                {
                    "accent": "blue",
                    "helper": "Battery discharge used to offset site load in the mock schedule.",
                    "label": "Load offset",
                    "value": format_energy(sum_rows(dispatch_rows, "battery_site_load_offset_mwh")),
                },
                {
                    "accent": "emerald" if selected_route else "amber",
                    "helper": "External market trading remains optional behind-the-meter upside.",
                    "label": "Optional route",
                    "value": selected_route or "gated",
                },
            ],
            "rows": [
                {
                    "execution_driver": "Site-load protection",
                    "mock_evidence": f"{format_energy(sum_rows(dispatch_rows, 'battery_site_load_offset_mwh'))} load offset / {format_energy(sum_rows(dispatch_rows, 'net_site_import_mwh'))} net site import",
                    "investor_meaning": "The execution plan protects the industrial site value before treating market trades as upside.",
                    "production_upgrade": "Connect site meter telemetry, load forecast, tariff model, and contracted capacity limits.",
                },
                {
                    "execution_driver": "Peak-limit control",
                    "mock_evidence": f"{format_energy(signal_summary.get('peak_shaved_mwh') or sum_rows(dispatch_rows, 'peak_shaved_mwh'))} peak shaved / {format_energy(sum_rows(dispatch_rows, 'peak_excess_after_mwh'))} residual excess",
                    "investor_meaning": "Behind-the-meter dispatch should reduce peak exposure rather than accidentally increasing site import risk.",
                    "production_upgrade": "Use live site demand, DSO capacity terms, and plant operating constraints.",
                },
                {
                    "execution_driver": "Optional market execution",
                    "mock_evidence": f"{route_name} / {bid_count} bid(s) / automation {format_enum(automation_mode)}",
                    "investor_meaning": "External bids are an additional route, not the core reason this industrial asset creates value.",
                    "production_upgrade": "Connect market adapter readiness, prequalification, and settlement split between site savings and market PnL.",
                },
            ],
        }

    return {
        "kpis": [
            {
                "accent": "emerald",
                "helper": "Order package volume compared with physical dispatch movement.",
                "label": "Bid energy",
                "value": format_energy(bid_energy if bid_energy > 0 else get_dispatch_throughput_from_summary(signal_summary, dispatch_rows)),
            },
            {
                "accent": "blue",
                "helper": "SOC evidence used to validate physical delivery capability.",
                "label": "Telemetry SOC",
                "value": f"{format_number(telemetry_payload.get('soc_percent'), 1)}%" if telemetry_payload.get("soc_percent") is not None else format_energy(last_dispatch_value(dispatch_rows, "soc_mwh")),
            },
            {
                "accent": "emerald" if readiness_score >= 70 else "amber" if readiness_score > 0 else "slate",
                "helper": "Readiness gate before supervised or live execution.",
                "label": "Execution readiness",
                "value": f"{format_number(readiness_score, 1)}/100" if readiness_score else readiness.get("readiness_status") or "not evaluated",
            },
        ],
        "rows": [
            {
                "execution_driver": "SOC and power bounded bids",
                "mock_evidence": f"{bid_count} bid(s) / {format_energy(bid_energy if bid_energy > 0 else get_dispatch_throughput_from_summary(signal_summary, dispatch_rows))} scheduled / SOC {format_energy(telemetry_payload.get('soc_mwh') or last_dispatch_value(dispatch_rows, 'soc_mwh'))}",
                "investor_meaning": "Bid volume is credible only when the battery can physically charge, discharge, and hold SOC reserves.",
                "production_upgrade": "Connect EMS SOC, availability, meter telemetry, and degradation-aware dispatch limits.",
            },
            {
                "execution_driver": "Market gate readiness",
                "mock_evidence": f"{route_name} / gate {format_enum(gate_status)} / readiness {format_number(readiness.get('readiness_score'), 1)}",
                "investor_meaning": "The route must clear market gate timing, connector readiness, and policy checks before submission.",
                "production_upgrade": "Use live exchange clocks, route certification, credentials, and official API handshake evidence.",
            },
            {
                "execution_driver": "Supervised automation envelope",
                "mock_evidence": f"{format_enum(automation_mode)} / {'live allowed' if automation_control.get('live_trading_allowed') else 'live gated'} / proposal {proposal_payload.get('status') or 'pending'}",
                "investor_meaning": "Automation is intentionally gated while the platform runs on investor-demo mock data.",
                "production_upgrade": "Enable supervised/live modes only after telemetry, adapter, approval, and settlement evidence are connected.",
            },
        ],
    }


def sum_rows(rows: list[dict[str, Any]], key: str):
    total = 0.0
    for row in rows:
        try:
            total += float(row.get(key) or 0)
        except (TypeError, ValueError):
            continue
    return total


def get_dispatch_throughput_from_summary(
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
):
    throughput = numeric(summary.get("throughput_mwh"))
    if throughput > 0:
        return throughput
    charged = numeric(summary.get("charged_mwh"))
    discharged = numeric(summary.get("discharged_mwh"))
    if charged > 0 or discharged > 0:
        return charged + discharged
    return get_dispatch_throughput(rows)


def get_dispatch_throughput(rows: list[dict[str, Any]]):
    total = 0.0
    for row in rows:
        try:
            total += abs(float(row.get("grid_energy_mwh") or 0))
        except (TypeError, ValueError):
            continue
    return total


def last_dispatch_value(rows: list[dict[str, Any]], key: str):
    if not rows:
        return None
    try:
        return float(rows[-1].get(key))
    except (TypeError, ValueError):
        return None


def format_energy(value: Any):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{numeric_value:,.1f} MWh"


def format_money(value: Any):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"EUR {numeric_value:,.0f}"


def format_number(value: Any, digits: int = 2):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{numeric_value:,.{digits}f}"


def format_percent(value: Any):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "-"
    percent = numeric_value * 100 if numeric_value <= 1 else numeric_value
    return f"{percent:,.0f}%"


def readiness_tone(value: Any):
    if value in {"ready", "client_ready", "go_live_ready"}:
        return "emerald"
    if value == "blocked":
        return "red"
    if value:
        return "amber"
    return "slate"


def numeric(value: Any):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_divide(numerator: float, denominator: float):
    return numerator / denominator if denominator else None


def format_enum(value: Any):
    return str(value or "-").replace("_", " ")


def has_issue_list(value: Any):
    if not value:
        return False
    if isinstance(value, str):
        return value not in {"-", "none", "None"}
    if isinstance(value, list):
        return len(value) > 0
    return True


def get_proposal_bids(proposal: dict[str, Any]):
    if not proposal:
        return []
    if isinstance(proposal.get("bids"), list):
        return proposal["bids"]
    if isinstance(proposal.get("orders"), list):
        return proposal["orders"]
    bid_package = proposal.get("bid_package") or {}
    if isinstance(bid_package.get("orders"), list):
        return bid_package["orders"]
    return []

