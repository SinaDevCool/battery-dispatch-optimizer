import json

from backend.config.paths import DATABASE_FILE
from backend.db.database import get_connection, initialize_database
from backend.db.models import row_to_dict


def save_revenue_stack_run(revenue_stack_result, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    asset_id = revenue_stack_result["asset_id"]

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO revenue_stack_runs (
                asset_id,
                generated_at,
                optimizer_engine,
                total_estimated_revenue_eur,
                estimated_product_count,
                product_count,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asset_id,
                revenue_stack_result.get("generated_at"),
                revenue_stack_result.get("optimizer_engine"),
                revenue_stack_result.get("total_estimated_revenue_eur"),
                revenue_stack_result.get("estimated_product_count"),
                revenue_stack_result.get("product_count"),
                json.dumps(revenue_stack_result),
            ),
        )

        revenue_stack_id = cursor.lastrowid

        for product in revenue_stack_result.get("products", []):
            connection.execute(
                """
                INSERT INTO revenue_product_results (
                    revenue_stack_id,
                    asset_id,
                    product_id,
                    status,
                    eligibility_status,
                    estimated_revenue_eur,
                    source,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    revenue_stack_id,
                    asset_id,
                    product.get("product_id"),
                    product.get("status"),
                    product.get("eligibility_status"),
                    product.get("estimated_revenue_eur"),
                    product.get("source"),
                    json.dumps(product),
                ),
            )

    return revenue_stack_id


def list_revenue_stack_runs(asset_id, limit=50, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                revenue_stack_id,
                asset_id,
                generated_at,
                optimizer_engine,
                total_estimated_revenue_eur,
                estimated_product_count,
                product_count
            FROM revenue_stack_runs
            WHERE asset_id = ?
            ORDER BY revenue_stack_id DESC
            LIMIT ?
            """,
            (asset_id, limit),
        ).fetchall()

    return [row_to_dict(row) for row in rows]


def get_revenue_stack_run(revenue_stack_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM revenue_stack_runs
            WHERE revenue_stack_id = ?
            """,
            (revenue_stack_id,),
        ).fetchone()

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result


def list_revenue_product_results(revenue_stack_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM revenue_product_results
            WHERE revenue_stack_id = ?
            ORDER BY revenue_product_id ASC
            """,
            (revenue_stack_id,),
        ).fetchall()

    results = []

    for row in rows:
        item = row_to_dict(row)
        item["payload"] = json.loads(item.pop("payload_json"))
        results.append(item)

    return results



