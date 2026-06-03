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
            CREATE TABLE IF NOT EXISTS assets (
                asset_id TEXT PRIMARY KEY,
                client_name TEXT,
                site_name TEXT,
                asset_name TEXT,
                country TEXT,
                market TEXT,
                market_profile_id TEXT,
                capacity_mwh REAL,
                max_charge_power_mw REAL,
                max_discharge_power_mw REAL,
                forecast_file TEXT,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_assets_market_profile_id
                ON assets(market_profile_id);

            CREATE TABLE IF NOT EXISTS forecast_snapshots (
                forecast_snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_file TEXT NOT NULL,
                forecast_provider TEXT,
                forecast_model TEXT,
                target_date TEXT,
                row_count INTEGER,
                min_price REAL,
                max_price REAL,
                average_price REAL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_forecast_snapshots_target_date
                ON forecast_snapshots(target_date);

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

            CREATE TABLE IF NOT EXISTS business_decisions (
                decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                recommendation_title TEXT NOT NULL,
                recommendation_status TEXT,
                readiness TEXT,
                expected_pnl_eur REAL,
                hedged_revenue_eur REAL,
                residual_exposure_eur REAL,
                forecast_provider TEXT,
                forecast_model TEXT,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_business_decisions_asset_id
                ON business_decisions(asset_id);

            CREATE INDEX IF NOT EXISTS idx_business_decisions_generated_at
                ON business_decisions(generated_at);

            CREATE TABLE IF NOT EXISTS workflow_runs (
                workflow_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                optimizer_engine TEXT,
                forecast_snapshot_id INTEGER,
                signal_id INTEGER,
                revenue_stack_id INTEGER,
                decision_id INTEGER,
                target_date TEXT,
                forecast_provider TEXT,
                forecast_model TEXT,
                recommendation_status TEXT,
                expected_pnl_eur REAL,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_workflow_runs_asset_id
                ON workflow_runs(asset_id);

            CREATE INDEX IF NOT EXISTS idx_workflow_runs_started_at
                ON workflow_runs(started_at);

            CREATE TABLE IF NOT EXISTS execution_proposals (
                execution_proposal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                status TEXT NOT NULL,
                approval_status TEXT,
                signal_id INTEGER,
                workflow_run_id INTEGER,
                target_date TEXT,
                market TEXT,
                order_count INTEGER,
                total_buy_mwh REAL,
                total_sell_mwh REAL,
                expected_pnl_eur REAL,
                max_daily_loss_eur REAL,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_execution_proposals_asset_id
                ON execution_proposals(asset_id);

            CREATE INDEX IF NOT EXISTS idx_execution_proposals_generated_at
                ON execution_proposals(generated_at);
            """
        )
