import json
from datetime import datetime

from backend.assets.asset_loader import get_asset, load_assets
from backend.config.paths import DATABASE_FILE
from backend.db.database import get_connection, initialize_database
from backend.db.models import row_to_dict


def sync_assets_to_database(db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)
    assets = load_assets()

    with get_connection(db_file=db_file) as connection:
        for asset in assets:
            payload = asset.to_dict()
            battery_config = payload.get("battery_config", {})

            connection.execute(
                """
                INSERT INTO assets (
                    asset_id,
                    client_name,
                    site_name,
                    asset_name,
                    country,
                    market,
                    market_profile_id,
                    capacity_mwh,
                    max_charge_power_mw,
                    max_discharge_power_mw,
                    forecast_file,
                    payload_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    client_name = excluded.client_name,
                    site_name = excluded.site_name,
                    asset_name = excluded.asset_name,
                    country = excluded.country,
                    market = excluded.market,
                    market_profile_id = excluded.market_profile_id,
                    capacity_mwh = excluded.capacity_mwh,
                    max_charge_power_mw = excluded.max_charge_power_mw,
                    max_discharge_power_mw = excluded.max_discharge_power_mw,
                    forecast_file = excluded.forecast_file,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (
                    payload.get("asset_id"),
                    payload.get("client_name"),
                    payload.get("site_name"),
                    payload.get("asset_name"),
                    payload.get("country"),
                    payload.get("market"),
                    payload.get("market_profile_id"),
                    battery_config.get("capacity_mwh"),
                    battery_config.get("max_charge_power_mw"),
                    battery_config.get("max_discharge_power_mw"),
                    payload.get("forecast_file"),
                    json.dumps(payload),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )

    return len(assets)


def list_asset_records(db_file=DATABASE_FILE):
    sync_assets_to_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM assets
            ORDER BY asset_id ASC
            """
        ).fetchall()

    records = []

    for row in rows:
        record = row_to_dict(row)
        record.update(json.loads(record.pop("payload_json")))
        records.append(record)

    return records


def get_asset_record(asset_id, db_file=DATABASE_FILE):
    sync_assets_to_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM assets
            WHERE asset_id = ?
            """,
            (asset_id,),
        ).fetchone()

    if row is None:
        return get_asset(asset_id).to_dict()

    record = row_to_dict(row)
    record.update(json.loads(record.pop("payload_json")))

    return record



