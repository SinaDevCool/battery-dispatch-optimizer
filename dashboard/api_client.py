import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


def get_json(endpoint):
    url = f"{API_BASE_URL}{endpoint}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.RequestException as error:
        st.error(f"Could not connect to API: {error}")
        return None


def post_json(endpoint, payload=None):
    url = f"{API_BASE_URL}{endpoint}"

    if payload is None:
        payload = {}

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    except requests.RequestException as error:
        st.error(f"Could not send data to API: {error}")
        return None