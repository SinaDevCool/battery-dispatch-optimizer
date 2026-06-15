STANDARD_FORECAST_COLUMNS = [
    "timestamp",
    "forecast_price",
    "load_forecast",
    "generation_forecast",
    "forecast_solar",
    "forecast_wind",
    "forecast_renewables_total",
    "forecast_provider",
    "forecast_model",
    "created_at",
]

REQUIRED_PROFIT_COLUMNS = [
    "timestamp",
    "forecast_price",
]

OPTIONAL_CONTEXT_COLUMNS = [
    "load_forecast",
    "generation_forecast",
    "forecast_solar",
    "forecast_wind",
    "forecast_renewables_total",
]


