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
        @media print {{
            body {{ padding: 24px; }}
        }}
    </style>
</head>
<body>
    <h1>Battery Trader AI Client Report</h1>
    <div class="subtitle">{safe(asset_name)} / {safe(asset.get("country"))} / generated {safe(generated_at)}</div>

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
        ("Market profile", asset.get("market_profile_id") or asset.get("market")),
        ("Capacity", f"{nested(asset, 'battery_config', 'capacity_mwh', default='-')} MWh"),
        ("Power limit", f"{nested(asset, 'battery_config', 'max_discharge_power_mw', default='-')} MW discharge"),
    ])}

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
        This report is generated from the Battery Trader AI evidence stack. It should be treated as a client delivery packet only when evidence readiness, settlement, and audit gaps are clear.
    </div>
</body>
</html>
"""


def kpi(label, value):
    return f"""
        <div class="kpi">
            <div class="label">{safe(label)}</div>
            <div class="value">{safe(value)}</div>
        </div>
    """


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


def safe(value):
    if value is None:
        return "-"

    return escape(str(value))



