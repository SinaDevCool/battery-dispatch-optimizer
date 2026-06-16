# Local Data Layout

This directory is for local development data.

- `config/` contains checked-in seed configuration for assets, clients, and market profiles.
- `raw/`, `processed/`, `outputs/`, and `db/` are runtime/local artifact locations created as needed.
- `mock/forecasts/` contains checked-in investor-demo forecast profiles.

Production deployments should move generated outputs to object storage and
database state to a managed database instead of treating these runtime folders
as source-controlled application state.

## Mock vs Production Data

The checked-in `config/assets.json` file is the source of demo asset metadata.
Each asset can declare:

- `asset_type`: high-level product category, such as `grid_scale_battery`.
- `asset_subtype`: operating archetype, such as `standalone_grid_connected`.
- `data_mode`: `mock`, `paper`, or future `production`.
- `data_source`: where the asset's current evidence comes from.
- `data_profile`: human-readable explanation of the forecast, telemetry,
  execution, and settlement sources used for the selected asset.

The current investor-demo assets are intentionally marked as `mock`:

- `default_site`: standalone grid-scale battery.
- `demo_solar_battery`: solar co-located battery.
- `demo_industrial_btm`: industrial behind-the-meter battery.

Each mock asset has its own forecast profile:

- `mock/forecasts/grid_battery_price_forecast.csv`: merchant spread profile.
- `mock/forecasts/solar_battery_price_generation_forecast.csv`: price plus solar generation context.
- `mock/forecasts/industrial_btm_price_load_forecast.csv`: price plus industrial site load context.

They are safe for investor demos and local development, but they are not
production exchange, telemetry, forecast, or settlement data.
