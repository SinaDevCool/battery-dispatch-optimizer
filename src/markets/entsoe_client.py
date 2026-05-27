import os


def get_entsoe_api_key(api_key=None):
    if api_key is None:
        api_key = os.environ.get("ENTSOE_API_KEY")

    if not api_key:
        raise ValueError("Missing ENTSOE_API_KEY")

    return api_key


def fetch_day_ahead_prices_placeholder(country_code, start_date, end_date):
    raise NotImplementedError(
        "ENTSO-E client is not implemented yet. "
        "Later we will use entsoe-py or the ENTSO-E REST API here."
    )


def fetch_load_forecast_placeholder(country_code, start_date, end_date):
    raise NotImplementedError(
        "ENTSO-E load forecast retrieval is not implemented yet."
    )


def fetch_generation_forecast_placeholder(country_code, start_date, end_date):
    raise NotImplementedError(
        "ENTSO-E generation forecast retrieval is not implemented yet."
    )