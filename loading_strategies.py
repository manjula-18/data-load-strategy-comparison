
import sqlite3
import time
import uuid
import json
from datetime import datetime, timedelta

DB_NAME = "comparison.db"
LOOKBACK_HOURS = 24


# 1. Validate each order
def validate_order(order, customers):
    order_id, customer_id, order_date, amount, status, updated_at, source_file = order

    if not order_id or order_id <= 0:
        return "Invalid order ID"
    if not customer_id or customer_id <= 0:
        return "Invalid customer ID"
    if customer_id not in customers:
        return "Customer does not exist"
    if amount is None or amount < 0:
        return "Invalid amount"
    if not order_date:
        return "Missing order date"

    try:
        datetime.strptime(order_date, "%Y-%m-%d")
    except ValueError:
        return "Invalid order date format"

    if not updated_at:
        return "Missing update timestamp"

    return None


# 2. Read and save the watermark
def get_watermark(cursor):
    cursor.execute("""
        SELECT last_watermark FROM pipeline_watermarks
        WHERE strategy = 'Incremental Merge'
    """)
    result = cursor.fetchone()
    return result[0] if result else None


def save_watermark(cursor, watermark):
    cursor.execute("""
        INSERT INTO pipeline_watermarks
        VALUES (?, ?, ?)
        ON CONFLICT(strategy) DO UPDATE SET
        last_watermark = excluded.last_watermark,
        updated_at = excluded.updated_at
    """, (
        "Incremental Merge",
        watermark,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))


# 3. Read, validate and remove duplicate source records
def get_source_data(cursor, run_id, cutoff=None):
    query = "SELECT * FROM source_orders"
    params = ()

    if cutoff:
        query += """
            WHERE updated_at >= ?
            OR updated_at IS NULL OR updated_at = ''
        """
        params = (cutoff,)

    cursor.execute(query + " ORDER BY updated_at, rowid", params)
    source = cursor.fetchall()

    cursor.execute("SELECT customer_id FROM customers")
    customers = {row[0] for row in cursor.fetchall()}

    unique = {}
    rejected = 0

    for order in source:
        reason = validate_order(order, customers)

        if reason:
            cursor.execute("""
                INSERT INTO rejected_records
                (raw_record, reason, source_file, run_id, rejected_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                json.dumps(order), reason, order[6], run_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            rejected += 1
            continue

        order_id = order[0]

        if order_id not in unique or order[5] >= unique[order_id][5]:
            unique[order_id] = order

    rows = [
        (*order[:6], order[2][:7], order[6], run_id)
        for order in unique.values()
    ]

    duplicates = len(source) - rejected - len(rows)

    print("Source records:", len(source))
    print("Invalid records rejected:", rejected)
    print("Duplicate records removed:", duplicates)

    return rows, len(source), rejected


# 4. Insert records into a target table
def insert_rows(cursor, table, rows):
    cursor.executemany(f"""
        INSERT INTO {table}
        (order_id, customer_id, order_date, amount, status,
         updated_at, order_month, source_file, run_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)


# 5. Find new or updated records
def get_changed_rows(cursor, rows):
    cursor.execute("""
        SELECT order_id, updated_at FROM target_incremental_merge
    """)

    existing = dict(cursor.fetchall())

    return [
        row for row in rows
        if row[0] not in existing or row[5] > existing[row[0]]
    ]


# 6. Save pipeline execution details
def log_run(cursor, run_id, strategy, counts, duration,
            started, status="SUCCESS", error=None):

    cursor.execute("""
        INSERT INTO pipeline_runs
        (run_id, strategy, status, started_at, ended_at,
         input_count, output_count, rejected_count,
         duration_ms, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id, strategy, status, started,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        counts[0], counts[1], counts[2], duration, error
    ))


# 7. Run the selected loading strategy
def run_strategy(strategy):
    targets = {
        "Full Refresh": "target_full_refresh",
        "Incremental Merge": "target_incremental_merge",
        "Partition Replacement": "target_partition_replace"
    }

    if strategy not in targets:
        raise ValueError("Unknown loading strategy")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    run_id = str(uuid.uuid4())
    started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start = time.perf_counter()

    counts = [0, 0, 0]

    try:
        cutoff = None
        watermark = None

        if strategy == "Incremental Merge":
            watermark = get_watermark(cursor)
            print("Previous watermark:", watermark)

            if watermark:
                cutoff_time = datetime.strptime(
                    watermark, "%Y-%m-%d %H:%M:%S"
                ) - timedelta(hours=LOOKBACK_HOURS)

                cutoff = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")
                print("Lookback start:", cutoff)

        rows, counts[0], counts[2] = get_source_data(
            cursor, run_id, cutoff
        )

        table = targets[strategy]

        if strategy == "Full Refresh":
            cursor.execute(f"DELETE FROM {table}")
            insert_rows(cursor, table, rows)
            counts[1] = len(rows)

        elif strategy == "Incremental Merge":
            changed = get_changed_rows(cursor, rows)

            cursor.executemany(
                f"DELETE FROM {table} WHERE order_id = ?",
                [(row[0],) for row in changed]
            )

            insert_rows(cursor, table, changed)
            counts[1] = len(changed)

            print("Source records checked:", len(rows))
            print("New or updated records:", len(changed))
            print("Unchanged records skipped:", len(rows) - len(changed))

            if rows:
                new_watermark = max(row[5] for row in rows)

                if watermark is None or new_watermark > watermark:
                    save_watermark(cursor, new_watermark)
                    print("Updated watermark:", new_watermark)

        else:
            months = {row[6] for row in rows}

            cursor.executemany(
                f"DELETE FROM {table} WHERE order_month = ?",
                [(month,) for month in months]
            )

            insert_rows(cursor, table, rows)
            counts[1] = len(rows)
            print("Partitions replaced:", len(months))

        duration = (time.perf_counter() - start) * 1000

        log_run(cursor, run_id, strategy, counts, duration, started)
        conn.commit()

        print("\n", strategy, "completed successfully")
        print("Records processed:", counts[1])
        print("Records rejected:", counts[2])
        print("Execution time:", round(duration, 3), "ms")

    except Exception as error:
        conn.rollback()

        log_run(
            cursor, run_id, strategy, counts,
            (time.perf_counter() - start) * 1000,
            started, "FAILED", str(error)
        )
        conn.commit()

        print("Pipeline failed:", error)
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    for strategy in (
        "Full Refresh",
        "Incremental Merge",
        "Partition Replacement"
    ):
        run_strategy(strategy)
