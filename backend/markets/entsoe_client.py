import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv


load_dotenv()


ENTSOE_API_URL = "https://web-api.tp.entsoe.eu/api"

# Germany / Luxembourg bidding zone
GERMANY_LUXEMBOURG_BIDDING_ZONE = "10Y1001A1001A82H"


def get_entsoe_api_key(api_key=None):
    if api_key is None:
        api_key = os.environ.get("ENTSOE_API_KEY")

    if not api_key:
        raise ValueError(
            "Missing ENTSOE_API_KEY. "
            "Set it in PowerShell with: $env:ENTSOE_API_KEY='your_token_here' "
            "or add it to a local .env file."
        )

    return api_key


def format_entsoe_datetime(dt):
    return dt.strftime("%Y%m%d%H%M")


def fetch_day_ahead_prices(
    start_datetime,
    end_datetime,
    bidding_zone=GERMANY_LUXEMBOURG_BIDDING_ZONE,
    api_key=None,
):
    api_key = get_entsoe_api_key(api_key)

    params = {
        "securityToken": api_key,
        "documentType": "A44",
        "in_Domain": bidding_zone,
        "out_Domain": bidding_zone,
        "periodStart": format_entsoe_datetime(start_datetime),
        "periodEnd": format_entsoe_datetime(end_datetime),
    }

    response = requests.get(
        ENTSOE_API_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.text


def parse_day_ahead_prices(xml_text):
    root = ET.fromstring(xml_text)

    namespace = {
        "ns": root.tag.split("}")[0].replace("{", "")
    }

    rows = []

    for time_series in root.findall(".//ns:TimeSeries", namespace):
        for period in time_series.findall(".//ns:Period", namespace):
            start_text = period.findtext(
                "ns:timeInterval/ns:start",
                namespaces=namespace,
            )

            resolution = period.findtext(
                "ns:resolution",
                namespaces=namespace,
            )

            if start_text is None:
                continue

            period_start = datetime.fromisoformat(
                start_text.replace("Z", "+00:00")
            )

            if resolution == "PT15M":
                step = timedelta(minutes=15)
            else:
                step = timedelta(hours=1)

            for point in period.findall("ns:Point", namespace):
                position_text = point.findtext(
                    "ns:position",
                    namespaces=namespace,
                )

                price_text = point.findtext(
                    "ns:price.amount",
                    namespaces=namespace,
                )

                if position_text is None or price_text is None:
                    continue

                position = int(position_text)
                price = float(price_text)

                timestamp = period_start + ((position - 1) * step)

                rows.append(
                    {
                        "timestamp": timestamp.replace(tzinfo=None),
                        "forecast_price": price,
                    }
                )

    return rows


def get_next_day_price_forecast(
    bidding_zone=GERMANY_LUXEMBOURG_BIDDING_ZONE,
    api_key=None,
):
    now_utc = datetime.now(timezone.utc)
    tomorrow = now_utc.date() + timedelta(days=1)

    return get_price_forecast_for_date(
        target_date=tomorrow,
        bidding_zone=bidding_zone,
        api_key=api_key,
    )


def get_price_forecast_for_date(
    target_date,
    bidding_zone=GERMANY_LUXEMBOURG_BIDDING_ZONE,
    api_key=None,
):
    start_datetime = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        0,
        0,
        tzinfo=timezone.utc,
    )

    end_datetime = start_datetime + timedelta(days=1)

    xml_text = fetch_day_ahead_prices(
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        bidding_zone=bidding_zone,
        api_key=api_key,
    )

    return parse_day_ahead_prices(xml_text)


def get_latest_available_price_forecast(
    bidding_zone=GERMANY_LUXEMBOURG_BIDDING_ZONE,
    api_key=None,
):
    now_utc = datetime.now(timezone.utc)

    candidate_dates = [
        now_utc.date() + timedelta(days=1),
        now_utc.date(),
        now_utc.date() - timedelta(days=1),
    ]

    for target_date in candidate_dates:
        try:
            rows = get_price_forecast_for_date(
                target_date=target_date,
                bidding_zone=bidding_zone,
                api_key=api_key,
            )

            if rows:
                return {
                    "target_date": str(target_date),
                    "rows": rows,
                }

        except Exception as error:
            print(f"Could not fetch ENTSO-E prices for {target_date}: {error}")

    return {
        "target_date": None,
        "rows": [],
    }


