import os
from io import StringIO

import pandas as pd
import requests


TOKEN_URL = "https://identity.netztransparenz.de/users/connect/token"
BASE_URL = "https://ds.netztransparenz.de/api/v1/data"


def get_access_token(client_id=None, client_secret=None):
    if client_id is None:
        client_id = os.environ.get("IPNT_CLIENT_ID")

    if client_secret is None:
        client_secret = os.environ.get("IPNT_CLIENT_SECRET")

    if not client_id:
        raise ValueError("Missing IPNT_CLIENT_ID")

    if not client_secret:
        raise ValueError("Missing IPNT_CLIENT_SECRET")

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()["access_token"]


def build_data_url(data, product, date_from, date_to):
    if product:
        return f"{BASE_URL}/{data}/{product}/{date_from}/{date_to}"

    return f"{BASE_URL}/{data}/{date_from}/{date_to}"


def fetch_data_response(token, data, product, date_from, date_to):
    url = build_data_url(
        data=data,
        product=product,
        date_from=date_from,
        date_to=date_to,
    )

    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=120,
    )

    response.raise_for_status()

    return response


def fetch_csv(token, data, product, date_from, date_to):
    response = fetch_data_response(
        token=token,
        data=data,
        product=product,
        date_from=date_from,
        date_to=date_to,
    )

    return response.text


def fetch_csv_dataframe(token, data, product, date_from, date_to):
    csv_text = fetch_csv(
        token=token,
        data=data,
        product=product,
        date_from=date_from,
        date_to=date_to,
    )

    if not csv_text.strip():
        return pd.DataFrame()

    return pd.read_csv(StringIO(csv_text), sep=";", decimal=",")


