from pathlib import Path

import pandas as pd

from backend.reports.monthly_report import build_monthly_report_html, save_monthly_report


def main():
    report_month = "2026-04"

    monthly_negative_file = Path("data/processed/negative_price_monthly_summary.csv")
    battery_monthly_file = Path("data/outputs/historical_battery_monthly_summary.csv")
    alert_summary_file = Path("data/processed/alert_summary.csv")
    forecast_file = Path("data/processed/next_day_price_forecast.csv")

    monthly_negative = pd.DataFrame()
    battery_monthly = pd.DataFrame()
    alert_summary = pd.DataFrame()
    forecast_df = pd.DataFrame()

    if monthly_negative_file.exists():
        monthly_negative_all = pd.read_csv(monthly_negative_file)
        monthly_negative = monthly_negative_all[
            monthly_negative_all["month"] == report_month
        ]

    if battery_monthly_file.exists():
        battery_monthly_all = pd.read_csv(battery_monthly_file)
        battery_monthly = battery_monthly_all[
            battery_monthly_all["month"] == report_month
        ]

    if alert_summary_file.exists():
        alert_summary = pd.read_csv(alert_summary_file)

    if forecast_file.exists():
        forecast_df = pd.read_csv(forecast_file)

    html = build_monthly_report_html(
        report_month=report_month,
        monthly_negative=monthly_negative,
        battery_monthly=battery_monthly,
        alert_summary=alert_summary,
        forecast_df=forecast_df,
    )

    output_file = Path(f"data/outputs/monthly_report_{report_month}.html")

    save_monthly_report(
        html=html,
        output_path=output_file,
    )

    print(f"Saved monthly report to: {output_file}")


if __name__ == "__main__":
    main()


