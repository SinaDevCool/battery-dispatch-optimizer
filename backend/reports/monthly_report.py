from datetime import datetime
from html import escape
from pathlib import Path

from backend.features.forecast_quality_features import build_forecast_quality_features
from backend.features.negative_price_features import build_negative_price_features


def build_feature_summary_html(forecast_df=None):
    if forecast_df is None or forecast_df.empty:
        return """
<h2>Forecast Feature Summary</h2>
<p>No forecast data available for feature summary.</p>
"""

    quality_features = build_forecast_quality_features(
        forecast_df,
        price_column="forecast_price",
    )

    negative_features = build_negative_price_features(
        forecast_df,
        price_column="forecast_price",
    )

    rows = []

    for key, value in quality_features.items():
        rows.append(f"<tr><td>{key}</td><td>{value}</td></tr>")

    for key, value in negative_features.items():
        rows.append(f"<tr><td>{key}</td><td>{value}</td></tr>")

    return f"""
<h2>Forecast Feature Summary</h2>

<table>
    <tr>
        <th>Feature</th>
        <th>Value</th>
    </tr>
    {''.join(rows)}
</table>
"""


def build_monthly_report_html(
    report_month,
    monthly_negative=None,
    battery_monthly=None,
    alert_summary=None,
    forecast_df=None,
):
    negative_hours = 0
    negative_share = 0
    avg_price = 0
    min_price = 0
    max_price = 0

    battery_profit = 0
    trade_days = 0
    avg_profit_per_mw_day = 0

    total_alerts = 0
    high_alerts = 0
    medium_alerts = 0

    if monthly_negative is not None and not monthly_negative.empty:
        row = monthly_negative.iloc[0]
        negative_hours = row.get("negative_price_hours", 0)
        negative_share = row.get("negative_price_share_percent", 0)
        avg_price = row.get("avg_price", 0)
        min_price = row.get("min_price", 0)
        max_price = row.get("max_price", 0)

    if battery_monthly is not None and not battery_monthly.empty:
        row = battery_monthly.iloc[0]
        battery_profit = row.get("total_net_profit_eur", 0)
        trade_days = row.get("trade_days", row.get("days", 0))
        avg_profit_per_mw_day = row.get("avg_profit_per_mw_day", 0)

    if alert_summary is not None and not alert_summary.empty:
        total_alerts = alert_summary["count"].sum()

        high_alerts = alert_summary.loc[
            alert_summary["severity"] == "high",
            "count",
        ].sum()

        medium_alerts = alert_summary.loc[
            alert_summary["severity"] == "medium",
            "count",
        ].sum()

    feature_summary_html = build_feature_summary_html(forecast_df)

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Battery Dispatch Market Report - {report_month}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}

        html, body {{
            margin: 0;
            padding: 0;
            background: #ffffff;
            color: #111827;
            font-family: Arial, sans-serif;
            line-height: 1.5;
        }}

        body {{
            padding: 40px;
        }}

        h1 {{
            color: #111827;
            font-size: 32px;
            margin: 0 0 8px 0;
        }}

        h2 {{
            color: #111827;
            font-size: 22px;
            margin: 32px 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 1px solid #e5e7eb;
        }}

        p {{
            color: #374151;
            font-size: 15px;
            margin: 10px 0;
        }}

        b {{
            color: #111827;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
            font-size: 14px;
            color: #111827;
        }}

        th {{
            background: #f3f4f6;
            color: #111827;
            text-align: left;
            padding: 10px;
            border: 1px solid #d1d5db;
        }}

        td {{
            padding: 10px;
            border: 1px solid #e5e7eb;
            color: #374151;
            vertical-align: top;
        }}

        .subtitle {{
            color: #6b7280;
            margin-bottom: 32px;
            font-size: 15px;
        }}

        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 16px;
            margin: 28px 0;
        }}

        .kpi {{
            border: 1px solid #d1d5db;
            border-radius: 8px;
            padding: 18px;
            background: #f9fafb;
        }}

        .kpi-label {{
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
            margin-bottom: 8px;
            font-weight: bold;
        }}

        .kpi-value {{
            font-size: 26px;
            font-weight: bold;
            color: #111827;
        }}

        .note {{
            background: #fffbeb;
            color: #92400e;
            padding: 14px;
            border-left: 4px solid #f59e0b;
            margin: 28px 0;
            border-radius: 4px;
        }}

        @media print {{
            body {{
                padding: 24px;
            }}
        }}
    </style>
</head>
<body>

<h1>Battery Dispatch Market Report</h1>
<div class="subtitle">Monthly analysis for {report_month}</div>

<h2>Executive Summary</h2>

<p>
In {report_month}, the market recorded <b>{negative_hours:.0f}</b>
negative-price hours, with a negative-price share of
<b>{negative_share:.2f}%</b>.
The average spot price was <b>{avg_price:.2f} EUR/MWh</b>,
with a minimum of <b>{min_price:.2f}</b> and a maximum of
<b>{max_price:.2f}</b>.
</p>

<p>
The battery model estimated <b>{battery_profit:.2f} EUR</b>
of net arbitrage opportunity, across <b>{trade_days:.0f}</b>
trade days. Average opportunity was
<b>{avg_profit_per_mw_day:.2f} EUR/MW-day</b>.
</p>

<div class="kpi-grid">
    <div class="kpi">
        <div class="kpi-label">Negative Hours</div>
        <div class="kpi-value">{negative_hours:.0f}</div>
    </div>

    <div class="kpi">
        <div class="kpi-label">Negative Share</div>
        <div class="kpi-value">{negative_share:.1f}%</div>
    </div>

    <div class="kpi">
        <div class="kpi-label">Battery Net Profit</div>
        <div class="kpi-value">{battery_profit:.0f} EUR</div>
    </div>

    <div class="kpi">
        <div class="kpi-label">High Alerts</div>
        <div class="kpi-value">{high_alerts:.0f}</div>
    </div>
</div>

<h2>Alert Summary</h2>

<p>
Total alerts: <b>{total_alerts:.0f}</b>.
High alerts: <b>{high_alerts:.0f}</b>.
Medium alerts: <b>{medium_alerts:.0f}</b>.
</p>

{feature_summary_html}

<div class="note">
This report is based on a simplified battery dispatch model.
It is useful for analysis and product development, but it is not
a financial trading recommendation.
</div>

</body>
</html>
"""

    return html


def save_monthly_report(html, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html)

    return output_path


def build_asset_client_report_html(
    asset,
    completeness,
    signal,
    revenue,
    regulatory,
    execution_proposal,
    paper_trade,
    settlement,
    audit_events,
):
    generated_at = datetime.now().isoformat(timespec="seconds")
    asset_name = asset.get("asset_name") or asset.get("site_name") or asset.get("asset_id")
    signal_summary = nested(signal, "data", "summary", default={})
    dispatch_rows = nested(signal, "data", "dispatch", default=[])
    revenue_total = revenue.get("total_estimated_revenue_eur")
    settlement_summary = nested(settlement, "settlement", "summary", default={})
    evidence_score = completeness.get("score", 0)
    delivery_state = "Client ready" if completeness.get("missing_count") == 0 else "Draft"
    decision = (
        "Client-facing delivery is defensible."
        if delivery_state == "Client ready"
        else "Keep this report in draft until open evidence gaps are cleared."
    )
    next_actions = completeness.get("next_actions") or [
        "Keep evidence attached to the asset audit trail."
    ]
    asset_report = build_asset_specific_report_evidence(
        asset=asset,
        completeness=completeness,
        dispatch_rows=dispatch_rows,
        execution_proposal=execution_proposal,
        revenue=revenue,
        signal_summary=signal_summary,
    )

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Battery Trader AI Client Report - {safe(asset_name)}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 40px;
            background: #ffffff;
            color: #111827;
            font-family: Arial, sans-serif;
            line-height: 1.5;
        }}
        h1 {{ margin: 0 0 8px; font-size: 32px; }}
        h2 {{
            margin: 32px 0 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e5e7eb;
            font-size: 20px;
        }}
        p {{ color: #374151; font-size: 15px; }}
        table {{
            width: 100%;
            margin-top: 12px;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th {{
            padding: 10px;
            border: 1px solid #d1d5db;
            background: #f3f4f6;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border: 1px solid #e5e7eb;
            vertical-align: top;
        }}
        .subtitle {{ color: #6b7280; margin-bottom: 28px; }}
        .decision {{
            border: 1px solid #bfdbfe;
            border-left: 5px solid #2563eb;
            border-radius: 8px;
            padding: 16px;
            background: #eff6ff;
            margin: 24px 0;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin: 22px 0;
        }}
        .kpi {{
            border: 1px solid #d1d5db;
            border-radius: 8px;
            padding: 14px;
            background: #f9fafb;
        }}
        .label {{
            color: #6b7280;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}
        .value {{
            margin-top: 6px;
            color: #111827;
            font-size: 20px;
            font-weight: bold;
        }}
        .note {{
            margin-top: 28px;
            padding: 14px;
            border-left: 4px solid #f59e0b;
            background: #fffbeb;
            color: #92400e;
        }}
        .badge {{
            display: inline-block;
            margin-left: 8px;
            padding: 3px 8px;
            border-radius: 999px;
            background: #dbeafe;
            color: #1d4ed8;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}
        @media print {{
            body {{ padding: 24px; }}
        }}
    </style>
</head>
<body>
    <h1>Battery Trader AI Client Report</h1>
    <div class="subtitle">{safe(asset_name)} / {safe(asset.get("country"))} / generated {safe(generated_at)} <span class="badge">{safe(asset.get("data_mode") or "mock")} investor demo data</span></div>

    <div class="decision">
        <div class="label">Client delivery decision</div>
        <p><b>{safe(decision)}</b></p>
        <p>{safe(next_actions[0])}</p>
    </div>

    <div class="kpi-grid">
        {kpi("Delivery state", delivery_state)}
        {kpi("Evidence score", f"{evidence_score} / 100")}
        {kpi("Dispatch signal", signal_summary.get("signal", "-"))}
        {kpi("Revenue stack", money(revenue_total))}
    </div>

    <h2>Asset And Commercial Context</h2>
    {table([
        ("Asset ID", asset.get("asset_id")),
        ("Asset type", human_label(asset.get("asset_type"))),
        ("Market profile", asset.get("market_profile_id") or asset.get("market")),
        ("Capacity", f"{nested(asset, 'battery_config', 'capacity_mwh', default='-')} MWh"),
        ("Power limit", f"{nested(asset, 'battery_config', 'max_discharge_power_mw', default='-')} MW discharge"),
        ("Data boundary", asset_report["data_boundary"]),
    ])}

    <h2>{safe(asset_report["title"])}</h2>
    <p>{safe(asset_report["summary"])}</p>
    <div class="kpi-grid">
        {''.join(kpi(item["label"], item["value"]) for item in asset_report["kpis"])}
    </div>
    {evidence_table(asset_report["rows"])}

    <h2>Dispatch And Revenue Evidence</h2>
    {table([
        ("Latest signal", signal_summary.get("signal")),
        ("Expected dispatch PnL", money(signal_summary.get("total_pnl_eur"))),
        ("Profit per MW-day", money(signal_summary.get("profit_per_mw_day"))),
        ("Revenue stack total", money(revenue_total)),
        ("Revenue products", revenue.get("product_count") or len(revenue.get("products", []))),
    ])}

    <h2>Regulatory And Market Eligibility</h2>
    {table([
        ("Regulatory status", regulatory.get("status")),
        ("Market participation mode", nested(regulatory, "regulatory_assumptions", "market_participation_mode")),
        ("Storage classification", nested(regulatory, "regulatory_assumptions", "storage_classification")),
        ("Automation implication", "Regulatory assumptions are attached before live automation escalation."),
    ])}

    <h2>Execution, Settlement, And Audit Evidence</h2>
    {table([
        ("Execution proposal", record_status(execution_proposal, "execution_proposal_id")),
        ("Paper execution", record_status(paper_trade, "paper_trade_id")),
        ("Settlement status", nested(settlement, "settlement", "status", default=settlement.get("status"))),
        ("Expected / paper / realized PnL", settlement_pnl_label(settlement_summary)),
        ("Automation event count", len(audit_events)),
    ])}

    <h2>Evidence Readiness</h2>
    {checks_table(completeness.get("checks", []))}

    <h2>Next Actions Before Delivery</h2>
    {table([(f"Action {index + 1}", action) for index, action in enumerate(next_actions[:6])])}

    <div class="note">
        This report is generated from the Battery Trader AI evidence stack using selected-asset mock investor-demo data. Production delivery should replace local mock evidence with connected forecast, telemetry, market-adapter, exchange, settlement, and audit integrations.
    </div>
</body>
</html>
"""


def build_asset_specific_report_evidence(
    asset,
    completeness,
    dispatch_rows,
    execution_proposal,
    revenue,
    signal_summary,
):
    asset_type = asset.get("asset_type")
    revenue_total = money(revenue.get("total_estimated_revenue_eur"))
    report_state = (
        "Evidence complete"
        if completeness.get("missing_count") == 0
        else f"{completeness.get('missing_count', 0)} open evidence gap(s)"
    )
    proposal_status = (
        execution_proposal.get("status")
        if isinstance(execution_proposal, dict)
        else "proposal pending"
    )

    if asset_type == "solar_colocated_battery":
        renewable_charge = energy(
            signal_summary.get("renewable_charge_mwh")
            or sum_rows(dispatch_rows, "renewable_charge_mwh")
        )
        green_share = percent(signal_summary.get("renewable_charge_share"))
        solar_available = energy(sum_rows(dispatch_rows, "solar_available_mwh"))
        export_headroom = energy(sum_rows(dispatch_rows, "site_export_headroom_mwh"))
        return {
            "data_boundary": "Mock solar co-located dispatch, renewable-origin, revenue, and report evidence.",
            "kpis": [
                {"label": "Renewable charge", "value": renewable_charge},
                {"label": "Green charge share", "value": green_share},
                {"label": "Solar available", "value": solar_available},
                {"label": "Revenue case", "value": revenue_total},
            ],
            "rows": [
                {
                    "section": "Renewable-origin dispatch",
                    "mock_evidence": f"{renewable_charge} renewable-origin charge / {green_share} green charge share",
                    "investor_meaning": "The report separates green charging evidence from generic battery arbitrage.",
                    "production_upgrade": "Connect generation meter, battery meter, origin tags, and certificate or EEG settlement evidence.",
                },
                {
                    "section": "Co-located export envelope",
                    "mock_evidence": f"{export_headroom} export headroom / {solar_available} solar available",
                    "investor_meaning": "The battery and solar plant share physical export constraints before revenue is trusted.",
                    "production_upgrade": "Use inverter limits, export-limit telemetry, and DSO connection evidence.",
                },
                {
                    "section": "Green investor packet",
                    "mock_evidence": f"{revenue_total} modelled / execution {safe_text(proposal_status)} / {report_state}",
                    "investor_meaning": "Renewable evidence, revenue, and execution readiness are presented as one diligence story.",
                    "production_upgrade": "Attach official compliance, exchange settlement, signed report export, and audit trail.",
                },
            ],
            "summary": "This selected-asset report explains a solar co-located battery as a renewable-shifting asset with export and green-origin constraints.",
            "title": "Solar + Battery Investor Evidence",
        }

    if asset_type == "industrial_behind_the_meter_battery":
        peak_shaved = energy(
            signal_summary.get("peak_shaved_mwh")
            or sum_rows(dispatch_rows, "peak_shaved_mwh")
        )
        site_offset = energy(sum_rows(dispatch_rows, "battery_site_load_offset_mwh"))
        net_import = energy(sum_rows(dispatch_rows, "net_site_import_mwh"))
        residual_peak = energy(sum_rows(dispatch_rows, "peak_excess_after_mwh"))
        return {
            "data_boundary": "Mock industrial load, tariff, behind-the-meter dispatch, and optional market evidence.",
            "kpis": [
                {"label": "Peak shaved", "value": peak_shaved},
                {"label": "Site load offset", "value": site_offset},
                {"label": "Net site import", "value": net_import},
                {"label": "Optional market value", "value": revenue_total},
            ],
            "rows": [
                {
                    "section": "Peak shaving and site savings",
                    "mock_evidence": f"{peak_shaved} peak shaved / {site_offset} site load offset",
                    "investor_meaning": "The report shows site-bill value before claiming market trading upside.",
                    "production_upgrade": "Connect site meter telemetry, load forecast, tariff model, and contracted capacity.",
                },
                {
                    "section": "Connection-limit control",
                    "mock_evidence": f"{residual_peak} residual peak excess / {net_import} net site import",
                    "investor_meaning": "The asset protects the industrial connection limit before external execution.",
                    "production_upgrade": "Use DSO limits, operating constraints, plant telemetry, and billing reconciliation.",
                },
                {
                    "section": "Optional market upside",
                    "mock_evidence": f"{revenue_total} modelled / execution {safe_text(proposal_status)} / {report_state}",
                    "investor_meaning": "External market value is framed as upside layered onto behind-the-meter savings.",
                    "production_upgrade": "Attach market adapter readiness, prequalification, and settlement split evidence.",
                },
            ],
            "summary": "This selected-asset report explains an industrial behind-the-meter battery through site-load protection, peak control, and optional market upside.",
            "title": "Industrial BTM Investor Evidence",
        }

    throughput = energy(
        signal_summary.get("throughput_mwh") or get_dispatch_throughput(dispatch_rows)
    )
    ending_soc = energy(last_row_value(dispatch_rows, "soc_mwh"))
    charged = energy(signal_summary.get("charged_mwh") or sum_positive_rows(dispatch_rows, "grid_energy_mwh"))
    discharged = energy(signal_summary.get("discharged_mwh") or sum_negative_rows(dispatch_rows, "grid_energy_mwh"))
    return {
        "data_boundary": "Mock grid-scale battery dispatch, revenue, execution, settlement, and audit evidence.",
        "kpis": [
            {"label": "Throughput", "value": throughput},
            {"label": "Ending SOC", "value": ending_soc},
            {"label": "Charged / discharged", "value": f"{charged} / {discharged}"},
            {"label": "Revenue case", "value": revenue_total},
        ],
        "rows": [
            {
                "section": "Physical dispatch and SOC proof",
                "mock_evidence": f"{throughput} throughput / {ending_soc} ending SOC",
                "investor_meaning": "The report shows the grid battery can physically follow the revenue case.",
                "production_upgrade": "Connect EMS SOC, meter telemetry, degradation model, and validated dispatch records.",
            },
            {
                "section": "Arbitrage and revenue stack",
                "mock_evidence": f"{charged} charged / {discharged} discharged / {revenue_total} modelled",
                "investor_meaning": "Merchant revenue is tied to battery movement rather than isolated financial totals.",
                "production_upgrade": "Connect exchange prices, revenue allocation, and settlement reconciliation.",
            },
            {
                "section": "Execution readiness boundary",
                "mock_evidence": f"Execution {safe_text(proposal_status)} / {report_state}",
                "investor_meaning": "The report keeps live execution gated while the demo uses mock evidence.",
                "production_upgrade": "Attach route certification, live adapter handshake, approval, submission, and audit evidence.",
            },
        ],
        "summary": "This selected-asset report explains a grid-scale battery through physical SOC limits, merchant dispatch, revenue stack, and execution readiness.",
        "title": "Grid Battery Investor Evidence",
    }


def kpi(label, value):
    return f"""
        <div class="kpi">
            <div class="label">{safe(label)}</div>
            <div class="value">{safe(value)}</div>
        </div>
    """


def evidence_table(rows):
    rendered_rows = "".join(
        "<tr>"
        f"<td>{safe(row.get('section'))}</td>"
        f"<td>{safe(row.get('mock_evidence'))}</td>"
        f"<td>{safe(row.get('investor_meaning'))}</td>"
        f"<td>{safe(row.get('production_upgrade'))}</td>"
        "</tr>"
        for row in rows
    )
    return (
        "<table>"
        "<tr><th>Report section</th><th>Mock evidence</th>"
        "<th>Investor meaning</th><th>Production upgrade</th></tr>"
        f"{rendered_rows}"
        "</table>"
    )


def table(rows):
    rendered_rows = "".join(
        f"<tr><th>{safe(label)}</th><td>{safe(value)}</td></tr>"
        for label, value in rows
    )
    return f"<table>{rendered_rows}</table>"


def checks_table(checks):
    if not checks:
        return table([("Evidence checks", "No readiness checks are available.")])

    rendered_rows = "".join(
        "<tr>"
        f"<td>{safe(check.get('label'))}</td>"
        f"<td>{safe(check.get('status'))}</td>"
        f"<td>{safe(check.get('record_id'))}</td>"
        f"<td>{safe(check.get('message'))}</td>"
        "</tr>"
        for check in checks
    )
    return (
        "<table>"
        "<tr><th>Check</th><th>Status</th><th>Record ID</th><th>Message</th></tr>"
        f"{rendered_rows}"
        "</table>"
    )


def nested(value, *keys, default="-"):
    current = value or {}

    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current.get(key)

    return default if current is None else current


def money(value):
    try:
        return f"{float(value):,.0f} EUR"
    except (TypeError, ValueError):
        return "-"


def record_status(record, id_key):
    if not record:
        return "missing"

    if isinstance(record, dict) and record.get(id_key):
        return f"available, ID {record.get(id_key)}"

    return "available"


def settlement_pnl_label(summary):
    return (
        f"{money(summary.get('expected_pnl_eur'))} / "
        f"{money(summary.get('paper_pnl_eur'))} / "
        f"{money(summary.get('realized_pnl_eur'))}"
    )


def human_label(value):
    if not value:
        return "-"
    return str(value).replace("_", " ")


def safe_text(value):
    if value is None:
        return "-"
    return str(value).replace("_", " ")


def sum_rows(rows, key):
    total = 0.0
    for row in rows or []:
        try:
            total += float(row.get(key) or 0)
        except (AttributeError, TypeError, ValueError):
            continue
    return total


def sum_positive_rows(rows, key):
    total = 0.0
    for row in rows or []:
        try:
            value = float(row.get(key) or 0)
        except (AttributeError, TypeError, ValueError):
            continue
        if value > 0:
            total += value
    return total


def sum_negative_rows(rows, key):
    total = 0.0
    for row in rows or []:
        try:
            value = float(row.get(key) or 0)
        except (AttributeError, TypeError, ValueError):
            continue
        if value < 0:
            total += abs(value)
    return total


def get_dispatch_throughput(rows):
    return sum(abs(float(row.get("grid_energy_mwh") or 0)) for row in rows or [])


def last_row_value(rows, key):
    if not rows:
        return None
    try:
        return rows[-1].get(key)
    except (AttributeError, IndexError):
        return None


def energy(value):
    try:
        return f"{float(value):,.1f} MWh"
    except (TypeError, ValueError):
        return "-"


def percent(value):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "-"
    if numeric_value <= 1:
        numeric_value *= 100
    return f"{numeric_value:,.0f}%"


def safe(value):
    if value is None:
        return "-"

    return escape(str(value))



