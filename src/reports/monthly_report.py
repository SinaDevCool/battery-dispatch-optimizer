from pathlib import Path

from src.features.forecast_quality_features import build_forecast_quality_features
from src.features.negative_price_features import build_negative_price_features


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