

import os
import shutil
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from unittest.mock import patch

import loading_strategies


@contextmanager
def database_connection(db_path):
    conn = sqlite3.connect(db_path)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


class TestLoadingStrategies(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(
            self.temp_dir.name, "test_comparison.db"
        )

        original_db = os.path.join(
            os.path.dirname(__file__), "comparison.db"
        )
        shutil.copy2(original_db, self.test_db)

        # Register cleanup so the database path is restored first.
        self.addCleanup(self.temp_dir.cleanup)

        self.db_patch = patch.object(
            loading_strategies, "DB_NAME", self.test_db
        )
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)

        with database_connection(self.test_db) as conn:
            for table in [
                "pipeline_watermarks",
                "pipeline_runs",
                "rejected_records",
                "target_full_refresh",
                "target_incremental_merge",
                "target_partition_replace",
                "source_orders",
                "customers"
            ]:
                conn.execute(f"DELETE FROM {table}")

            conn.execute(
                "INSERT INTO customers VALUES (?, ?)",
                (1, "Test Customer")
            )

    def add_order(
        self, order_id=1, amount=500,
        updated_at="2099-01-04 10:00:00",
        order_date="2099-01-04", customer_id=1
    ):
        with database_connection(self.test_db) as conn:
            conn.execute("""
                INSERT INTO source_orders
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id, customer_id, order_date,
                amount, "Completed", updated_at, "test_file"
            ))

    def get_count(self, table):
        with database_connection(self.test_db) as conn:
            return conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

    def test_happy_path_full_refresh(self):
        self.add_order()
        loading_strategies.run_strategy("Full Refresh")
        self.assertEqual(self.get_count("target_full_refresh"), 1)

    def test_empty_source(self):
        loading_strategies.run_strategy("Full Refresh")
        self.assertEqual(self.get_count("target_full_refresh"), 0)

    def test_invalid_and_null_records(self):
        self.add_order(order_id=1, amount=None)
        self.add_order(order_id=2, order_date="wrong-date")

        loading_strategies.run_strategy("Full Refresh")

        self.assertEqual(self.get_count("target_full_refresh"), 0)
        self.assertEqual(self.get_count("rejected_records"), 2)

    def test_duplicate_records(self):
        self.add_order(
            order_id=10, amount=500,
            updated_at="2099-01-04 10:00:00"
        )
        self.add_order(
            order_id=10, amount=900,
            updated_at="2099-01-04 12:00:00"
        )

        loading_strategies.run_strategy("Full Refresh")

        self.assertEqual(self.get_count("target_full_refresh"), 1)

        with database_connection(self.test_db) as conn:
            amount = conn.execute("""
                SELECT amount FROM target_full_refresh
                WHERE order_id = 10
            """).fetchone()[0]

        self.assertEqual(amount, 900)

    def test_incremental_rerun_does_not_duplicate(self):
        self.add_order()

        loading_strategies.run_strategy("Incremental Merge")
        loading_strategies.run_strategy("Incremental Merge")

        self.assertEqual(
            self.get_count("target_incremental_merge"), 1
        )

    def test_late_arriving_record(self):
        with database_connection(self.test_db) as conn:
            conn.execute("""
                INSERT INTO pipeline_watermarks
                VALUES (?, ?, ?)
            """, (
                "Incremental Merge",
                "2099-01-04 10:00:00",
                "2099-01-04 10:00:00"
            ))

        self.add_order(
            order_id=20,
            amount=1800,
            updated_at="2099-01-03 18:00:00",
            order_date="2099-01-03"
        )

        loading_strategies.run_strategy("Incremental Merge")

        with database_connection(self.test_db) as conn:
            result = conn.execute("""
                SELECT amount FROM target_incremental_merge
                WHERE order_id = 20
            """).fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(result[0], 1800)


if __name__ == "__main__":
    unittest.main(verbosity=2)

