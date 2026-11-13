
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "comparison.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_db():
    conn = get_connection()

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        customer_name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS source_orders (
        order_id INTEGER,
        customer_id INTEGER,
        order_date TEXT,
        amount REAL,
        status TEXT,
        updated_at TEXT,
        source_file TEXT
    );

    CREATE TABLE IF NOT EXISTS target_full_refresh (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        order_date TEXT NOT NULL,
        amount REAL NOT NULL CHECK(amount >= 0),
        status TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        order_month TEXT NOT NULL,
        source_file TEXT,
        run_id TEXT
    );

    CREATE TABLE IF NOT EXISTS target_incremental_merge
    AS SELECT * FROM target_full_refresh WHERE 0;

    CREATE TABLE IF NOT EXISTS target_partition_replace
    AS SELECT * FROM target_full_refresh WHERE 0;

    CREATE TABLE IF NOT EXISTS rejected_records (
        reject_id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_record TEXT,
        reason TEXT,
        source_file TEXT,
        run_id TEXT,
        rejected_at TEXT
    );

    CREATE TABLE IF NOT EXISTS pipeline_runs (
        run_id TEXT PRIMARY KEY,
        strategy TEXT,
        status TEXT,
        started_at TEXT,
        ended_at TEXT,
        input_count INTEGER DEFAULT 0,
        output_count INTEGER DEFAULT 0,
        rejected_count INTEGER DEFAULT 0,
        duration_ms REAL,
        error_message TEXT
    );

    CREATE TABLE IF NOT EXISTS pipeline_watermarks (
        strategy TEXT PRIMARY KEY,
        last_watermark TEXT,
        updated_at TEXT
    );
    """)

    conn.commit()
    conn.close()
