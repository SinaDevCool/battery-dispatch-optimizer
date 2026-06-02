import sqlite3

from src.config.paths import DATABASE_FILE


def get_connection(db_file=DATABASE_FILE):
    db_file.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_file=DATABASE_FILE):
    with get_connection(db_file=db_file) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS signal_runs (
                signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                generated_at TEXT,
                target_date TEXT,
                optimizer_engine TEXT,
                forecast_provider TEXT,
                forecast_model TEXT,
                market_profile_id TEXT,
                signal TEXT,
                opportunity_level TEXT,
                total_pnl_eur REAL,
                profit_per_mw_day REAL,
                validation_status TEXT,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_signal_runs_asset_id
                ON signal_runs(asset_id);

            CREATE INDEX IF NOT EXISTS idx_signal_runs_generated_at
                ON signal_runs(generated_at);

            CREATE TABLE IF NOT EXISTS revenue_stack_runs (
                revenue_stack_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                generated_at TEXT,
                optimizer_engine TEXT,
                total_estimated_revenue_eur REAL,
                estimated_product_count INTEGER,
                product_count INTEGER,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_revenue_stack_runs_asset_id
                ON revenue_stack_runs(asset_id);

            CREATE INDEX IF NOT EXISTS idx_revenue_stack_runs_generated_at
                ON revenue_stack_runs(generated_at);

            CREATE TABLE IF NOT EXISTS revenue_product_results (
                revenue_product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                revenue_stack_id INTEGER NOT NULL,
                asset_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                status TEXT,
                eligibility_status TEXT,
                estimated_revenue_eur REAL,
                source TEXT,
                payload_json TEXT NOT NULL,
                FOREIGN KEY (revenue_stack_id)
                    REFERENCES revenue_stack_runs(revenue_stack_id)
            );

            CREATE INDEX IF NOT EXISTS idx_revenue_product_results_stack_id
                ON revenue_product_results(revenue_stack_id);

            CREATE INDEX IF NOT EXISTS idx_revenue_product_results_asset_id
                ON revenue_product_results(asset_id);

            CREATE TABLE IF NOT EXISTS forecast_actual_runs (
                forecast_actual_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                generated_at TEXT,
                target_date TEXT,
                forecast_provider TEXT,
                forecast_model TEXT,
                row_count INTEGER,
                mae_eur_per_mwh REAL,
                rmse_eur_per_mwh REAL,
                bias_eur_per_mwh REAL,
                predicted_pnl_eur REAL,
                realized_pnl_eur REAL,
                revenue_delta_eur REAL,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_forecast_actual_runs_asset_id
                ON forecast_actual_runs(asset_id);

            CREATE INDEX IF NOT EXISTS idx_forecast_actual_runs_generated_at
                ON forecast_actual_runs(generated_at);
            """
        )
