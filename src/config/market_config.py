MARKET_CONFIG = {
    "country": "Germany",
    "bidding_zone": "DE_LU",
    "currency": "EUR",
    "price_unit": "EUR/MWh",
    "timezone": "Europe/Berlin",
}


NETZTRANSPARENZ_ENDPOINTS = {
    "spot_prices": {
        "data": "Spotmarktpreise",
        "product": None,
        "format": "csv",
    },
    "solar_forecast": {
        "data": "prognose",
        "product": "Solar",
        "format": "csv",
    },
    "wind_forecast": {
        "data": "prognose",
        "product": "Wind",
        "format": "csv",
    },
    "online_solar": {
        "data": "OnlineHochrechnung",
        "product": "Solar",
        "format": "csv",
    },
    "online_wind_onshore": {
        "data": "OnlineHochrechnung",
        "product": "Windonshore",
        "format": "csv",
    },
    "online_wind_offshore": {
        "data": "OnlineHochrechnung",
        "product": "Windoffshore",
        "format": "csv",
    },
    "negative_prices_1h": {
        "data": "NegativePreise",
        "product": "1",
        "format": "csv",
    },
    "negative_prices_3h": {
        "data": "NegativePreise",
        "product": "3",
        "format": "csv",
    },
    "negative_prices_4h": {
        "data": "NegativePreise",
        "product": "4",
        "format": "csv",
    },
    "negative_prices_6h": {
        "data": "NegativePreise",
        "product": "6",
        "format": "csv",
    },
    "traffic_light": {
        "data": "Trafficlight",
        "product": None,
        "format": "json",
    },
}