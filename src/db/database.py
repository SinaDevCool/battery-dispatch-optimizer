import sqlite3

from src.config.paths import DATABASE_FILE


def get_connection(db_file=DATABASE_FILE):
    db_file.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_file=DATABASE_FILE):
    with get_connection(db_file=db_file) as connection:
        try:
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

            CREATE TABLE IF NOT EXISTS execution_paper_trades (
                paper_trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                execution_proposal_id INTEGER,
                generated_at TEXT NOT NULL,
                status TEXT NOT NULL,
                mode TEXT,
                order_count INTEGER,
                filled_order_count INTEGER,
                buy_cost_eur REAL,
                sell_revenue_eur REAL,
                paper_pnl_eur REAL,
                expected_pnl_eur REAL,
                paper_vs_expected_delta_eur REAL,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_execution_paper_trades_asset_id
                ON execution_paper_trades(asset_id);

            CREATE INDEX IF NOT EXISTS idx_execution_paper_trades_generated_at
                ON execution_paper_trades(generated_at);

            CREATE TABLE IF NOT EXISTS settlement_reconciliation_runs (
                settlement_reconciliation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                execution_proposal_id INTEGER,
                paper_trade_id INTEGER,
                forecast_actual_id INTEGER,
                expected_pnl_eur REAL,
                paper_pnl_eur REAL,
                realized_pnl_eur REAL,
                paper_delta_eur REAL,
                realized_delta_eur REAL,
                status TEXT NOT NULL,
                primary_variance_driver TEXT,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_settlement_reconciliation_asset_id
                ON settlement_reconciliation_runs(asset_id);

            CREATE INDEX IF NOT EXISTS idx_settlement_reconciliation_generated_at
                ON settlement_reconciliation_runs(generated_at);

            CREATE TABLE IF NOT EXISTS asset_telemetry_snapshots (
                telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                provider TEXT NOT NULL,
                status TEXT NOT NULL,
                availability_status TEXT,
                soc_mwh REAL,
                soc_percent REAL,
                available_charge_power_mw REAL,
                available_discharge_power_mw REAL,
                grid_import_limit_mw REAL,
                grid_export_limit_mw REAL,
                schedule_deviation_mwh REAL,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_asset_telemetry_asset_id
                ON asset_telemetry_snapshots(asset_id);

            CREATE INDEX IF NOT EXISTS idx_asset_telemetry_captured_at
                ON asset_telemetry_snapshots(captured_at);

            CREATE TABLE IF NOT EXISTS execution_market_submissions (
                market_submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                execution_proposal_id INTEGER,
                submitted_at TEXT NOT NULL,
                adapter_id TEXT NOT NULL,
                status TEXT NOT NULL,
                submitted_bid_count INTEGER,
                accepted_bid_count INTEGER,
                rejected_bid_count INTEGER,
                awarded_bid_count INTEGER,
                notional_eur REAL,
                live_submission INTEGER NOT NULL DEFAULT 0,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_execution_market_submissions_asset_id
                ON execution_market_submissions(asset_id);

            CREATE INDEX IF NOT EXISTS idx_execution_market_submissions_submitted_at
                ON execution_market_submissions(submitted_at);

            CREATE TABLE IF NOT EXISTS execution_approvals (
                approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                execution_proposal_id INTEGER,
                requested_at TEXT NOT NULL,
                decided_at TEXT,
                status TEXT NOT NULL,
                requested_by TEXT,
                decided_by TEXT,
                reason TEXT,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_execution_approvals_asset_id
                ON execution_approvals(asset_id);

            CREATE INDEX IF NOT EXISTS idx_execution_approvals_requested_at
                ON execution_approvals(requested_at);

            CREATE TABLE IF NOT EXISTS automation_policies (
                automation_policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                automation_mode TEXT NOT NULL,
                max_daily_loss_eur REAL,
                max_order_power_mw REAL,
                max_cycles_per_day REAL,
                min_confidence_score REAL,
                min_confidence_band TEXT,
                require_human_approval INTEGER NOT NULL DEFAULT 1,
                require_paper_trade INTEGER NOT NULL DEFAULT 1,
                allowed_markets_json TEXT NOT NULL,
                fallback_mode TEXT,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_automation_policies_asset_id
                ON automation_policies(asset_id);

            CREATE INDEX IF NOT EXISTS idx_automation_policies_updated_at
                ON automation_policies(updated_at);

            CREATE TABLE IF NOT EXISTS automation_events (
                automation_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                event_type TEXT NOT NULL,
                action TEXT,
                status TEXT NOT NULL,
                automation_mode_before TEXT,
                automation_mode_after TEXT,
                strategy_mode_before TEXT,
                strategy_mode_after TEXT,
                error_type TEXT,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_automation_events_asset_id
                ON automation_events(asset_id);

            CREATE INDEX IF NOT EXISTS idx_automation_events_created_at
                ON automation_events(created_at);

            CREATE TABLE IF NOT EXISTS official_api_evidence (
                evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                adapter_id TEXT NOT NULL,
                requirement_id TEXT NOT NULL,
                evidence_type TEXT,
                evidence_status TEXT NOT NULL,
                evidence_owner TEXT,
                evidence_reference TEXT,
                recorded_at TEXT NOT NULL,
                expires_at TEXT,
                review_at TEXT,
                unlocks_mode TEXT,
                payload_json TEXT NOT NULL,
                UNIQUE(adapter_id, requirement_id)
            );

            CREATE INDEX IF NOT EXISTS idx_official_api_evidence_adapter
                ON official_api_evidence(adapter_id);

            CREATE INDEX IF NOT EXISTS idx_official_api_evidence_requirement
                ON official_api_evidence(requirement_id);
            """
            )
        except sqlite3.OperationalError as error:
            if "readonly" in str(error).lower() and db_file.exists():
                return

            raise

