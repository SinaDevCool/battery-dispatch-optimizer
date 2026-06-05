import json
import sqlite3

from src.config.paths import DATABASE_FILE
from src.db.database import get_connection, initialize_database
from src.db.models import row_to_dict


def save_execution_proposal(proposal, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    summary = proposal.get("summary", {})

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO execution_proposals (
                asset_id,
                generated_at,
                status,
                approval_status,
                signal_id,
                workflow_run_id,
                target_date,
                market,
                order_count,
                total_buy_mwh,
                total_sell_mwh,
                expected_pnl_eur,
                max_daily_loss_eur,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal["asset_id"],
                proposal["generated_at"],
                proposal["status"],
                proposal.get("approval_status"),
                proposal.get("signal_id"),
                proposal.get("workflow_run_id"),
                proposal.get("target_date"),
                proposal.get("market"),
                summary.get("order_count"),
                summary.get("total_buy_mwh"),
                summary.get("total_sell_mwh"),
                summary.get("expected_pnl_eur"),
                summary.get("max_daily_loss_eur"),
                json.dumps(proposal, default=str),
            ),
        )

    return cursor.lastrowid


def get_latest_execution_proposal(asset_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM execution_proposals
            WHERE asset_id = ?
            ORDER BY execution_proposal_id DESC
            LIMIT 1
            """,
            (asset_id,),
        ).fetchone()

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result


def list_execution_proposals(asset_id, limit=25, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                execution_proposal_id,
                asset_id,
                generated_at,
                status,
                approval_status,
                signal_id,
                workflow_run_id,
                target_date,
                market,
                order_count,
                total_buy_mwh,
                total_sell_mwh,
                expected_pnl_eur,
                max_daily_loss_eur
            FROM execution_proposals
            WHERE asset_id = ?
            ORDER BY execution_proposal_id DESC
            LIMIT ?
            """,
            (asset_id, limit),
        ).fetchall()

    return [row_to_dict(row) for row in rows]


def save_execution_paper_trade(paper_trade, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    summary = paper_trade.get("summary", {})

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO execution_paper_trades (
                asset_id,
                execution_proposal_id,
                generated_at,
                status,
                mode,
                order_count,
                filled_order_count,
                buy_cost_eur,
                sell_revenue_eur,
                paper_pnl_eur,
                expected_pnl_eur,
                paper_vs_expected_delta_eur,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper_trade["asset_id"],
                paper_trade.get("execution_proposal_id"),
                paper_trade["generated_at"],
                paper_trade["status"],
                paper_trade.get("mode"),
                summary.get("order_count"),
                summary.get("filled_order_count"),
                summary.get("buy_cost_eur"),
                summary.get("sell_revenue_eur"),
                summary.get("paper_pnl_eur"),
                summary.get("expected_pnl_eur"),
                summary.get("paper_vs_expected_delta_eur"),
                json.dumps(paper_trade, default=str),
            ),
        )

    return cursor.lastrowid


def get_latest_execution_paper_trade(asset_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM execution_paper_trades
            WHERE asset_id = ?
            ORDER BY paper_trade_id DESC
            LIMIT 1
            """,
            (asset_id,),
        ).fetchone()

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result


def list_execution_paper_trades(asset_id, limit=25, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                paper_trade_id,
                asset_id,
                execution_proposal_id,
                generated_at,
                status,
                mode,
                order_count,
                filled_order_count,
                buy_cost_eur,
                sell_revenue_eur,
                paper_pnl_eur,
                expected_pnl_eur,
                paper_vs_expected_delta_eur
            FROM execution_paper_trades
            WHERE asset_id = ?
            ORDER BY paper_trade_id DESC
            LIMIT ?
            """,
            (asset_id, limit),
        ).fetchall()

    return [row_to_dict(row) for row in rows]


def save_execution_market_submission(submission, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    summary = submission.get("summary", {})

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO execution_market_submissions (
                asset_id,
                execution_proposal_id,
                submitted_at,
                adapter_id,
                status,
                submitted_bid_count,
                accepted_bid_count,
                rejected_bid_count,
                awarded_bid_count,
                notional_eur,
                live_submission,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                submission["asset_id"],
                submission.get("execution_proposal_id"),
                submission["submitted_at"],
                submission["adapter_id"],
                submission["status"],
                summary.get("submitted_bid_count"),
                summary.get("accepted_bid_count"),
                summary.get("rejected_bid_count"),
                summary.get("awarded_bid_count"),
                summary.get("notional_eur"),
                1 if submission.get("live_submission") else 0,
                json.dumps(submission, default=str),
            ),
        )

    return cursor.lastrowid


def get_latest_execution_market_submission(asset_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM execution_market_submissions
            WHERE asset_id = ?
            ORDER BY market_submission_id DESC
            LIMIT 1
            """,
            (asset_id,),
        ).fetchone()

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result


def list_execution_market_submissions(asset_id, limit=25, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                market_submission_id,
                asset_id,
                execution_proposal_id,
                submitted_at,
                adapter_id,
                status,
                submitted_bid_count,
                accepted_bid_count,
                rejected_bid_count,
                awarded_bid_count,
                notional_eur,
                live_submission
            FROM execution_market_submissions
            WHERE asset_id = ?
            ORDER BY market_submission_id DESC
            LIMIT ?
            """,
            (asset_id, limit),
        ).fetchall()

    return [row_to_dict(row) for row in rows]


def save_execution_approval(approval, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO execution_approvals (
                asset_id,
                execution_proposal_id,
                requested_at,
                decided_at,
                status,
                requested_by,
                decided_by,
                reason,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                approval["asset_id"],
                approval.get("execution_proposal_id"),
                approval["requested_at"],
                approval.get("decided_at"),
                approval["status"],
                approval.get("requested_by"),
                approval.get("decided_by"),
                approval.get("reason"),
                json.dumps(approval, default=str),
            ),
        )

    return cursor.lastrowid


def update_execution_approval(approval_id, approval, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        connection.execute(
            """
            UPDATE execution_approvals
            SET
                decided_at = ?,
                status = ?,
                decided_by = ?,
                reason = ?,
                payload_json = ?
            WHERE approval_id = ?
            """,
            (
                approval.get("decided_at"),
                approval["status"],
                approval.get("decided_by"),
                approval.get("reason"),
                json.dumps(approval, default=str),
                approval_id,
            ),
        )


def get_latest_execution_approval(asset_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM execution_approvals
            WHERE asset_id = ?
            ORDER BY approval_id DESC
            LIMIT 1
            """,
            (asset_id,),
        ).fetchone()

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result


def list_execution_approvals(asset_id, limit=25, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                approval_id,
                asset_id,
                execution_proposal_id,
                requested_at,
                decided_at,
                status,
                requested_by,
                decided_by,
                reason
            FROM execution_approvals
            WHERE asset_id = ?
            ORDER BY approval_id DESC
            LIMIT ?
            """,
            (asset_id, limit),
        ).fetchall()

    return [row_to_dict(row) for row in rows]


def save_automation_policy(policy, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    risk_limits = policy.get("risk_limits", {})
    confidence_policy = policy.get("confidence_policy", {})

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO automation_policies (
                asset_id,
                updated_at,
                policy_version,
                automation_mode,
                max_daily_loss_eur,
                max_order_power_mw,
                max_cycles_per_day,
                min_confidence_score,
                min_confidence_band,
                require_human_approval,
                require_paper_trade,
                allowed_markets_json,
                fallback_mode,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                policy["asset_id"],
                policy["updated_at"],
                policy["policy_version"],
                policy["automation_mode"],
                risk_limits.get("max_daily_loss_eur"),
                risk_limits.get("max_order_power_mw"),
                risk_limits.get("max_cycles_per_day"),
                confidence_policy.get("min_confidence_score"),
                confidence_policy.get("min_confidence_band"),
                1 if policy.get("approval_policy", {}).get("require_human_approval") else 0,
                1 if policy.get("simulation_policy", {}).get("require_paper_trade") else 0,
                json.dumps(policy.get("allowed_markets", []), default=str),
                policy.get("fallback_policy", {}).get("mode"),
                json.dumps(policy, default=str),
            ),
        )

    return cursor.lastrowid


def get_latest_automation_policy(asset_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM automation_policies
            WHERE asset_id = ?
            ORDER BY automation_policy_id DESC
            LIMIT 1
            """,
            (asset_id,),
        ).fetchone()

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result


def list_automation_policies(asset_id, limit=25, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                automation_policy_id,
                asset_id,
                updated_at,
                policy_version,
                automation_mode,
                max_daily_loss_eur,
                max_order_power_mw,
                max_cycles_per_day,
                min_confidence_score,
                min_confidence_band,
                require_human_approval,
                require_paper_trade,
                allowed_markets_json,
                fallback_mode
            FROM automation_policies
            WHERE asset_id = ?
            ORDER BY automation_policy_id DESC
            LIMIT ?
            """,
            (asset_id, limit),
        ).fetchall()

    policies = []
    for row in rows:
        policy = row_to_dict(row)
        policy["allowed_markets"] = json.loads(policy.pop("allowed_markets_json"))
        policies.append(policy)

    return policies


def save_automation_event(event, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    before = event.get("before", {})
    after = event.get("after", {})
    action_result = event.get("action_result", {})

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO automation_events (
                asset_id,
                created_at,
                event_type,
                action,
                status,
                automation_mode_before,
                automation_mode_after,
                strategy_mode_before,
                strategy_mode_after,
                error_type,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["asset_id"],
                event["created_at"],
                event["event_type"],
                event.get("action") or action_result.get("action"),
                event["status"],
                before.get("automation_mode"),
                after.get("automation_mode"),
                before.get("strategy_mode"),
                after.get("strategy_mode"),
                event.get("error_type") or action_result.get("error_type"),
                json.dumps(event, default=str),
            ),
        )

    return cursor.lastrowid


def get_latest_automation_event(asset_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        try:
            row = connection.execute(
                """
                SELECT *
                FROM automation_events
                WHERE asset_id = ?
                ORDER BY automation_event_id DESC
                LIMIT 1
                """,
                (asset_id,),
            ).fetchone()
        except sqlite3.OperationalError as error:
            if "no such table" in str(error).lower():
                return None

            raise

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result


def list_automation_events(asset_id, limit=25, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        try:
            rows = connection.execute(
                """
                SELECT
                    automation_event_id,
                    asset_id,
                    created_at,
                    event_type,
                    action,
                    status,
                    automation_mode_before,
                    automation_mode_after,
                    strategy_mode_before,
                    strategy_mode_after,
                    error_type
                FROM automation_events
                WHERE asset_id = ?
                ORDER BY automation_event_id DESC
                LIMIT ?
                """,
                (asset_id, limit),
            ).fetchall()
        except sqlite3.OperationalError as error:
            if "no such table" in str(error).lower():
                return []

            raise

    return [row_to_dict(row) for row in rows]
