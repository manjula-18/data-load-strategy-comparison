
import sqlite3
import pandas as pd
import streamlit as st
from loading_strategies import run_strategy

DB_NAME = "comparison.db"

st.set_page_config(
    page_title="Data Loading Comparison",
    page_icon="📊",
    layout="wide"
)


def read_query(query):
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query(query, conn)


def get_count(table):
    with sqlite3.connect(DB_NAME) as conn:
        result = conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()
    return result[0]


# Dashboard heading
st.title("📊 Data Loading Strategy Comparison")
st.write(
    "Compare Full Refresh, Incremental Merge "
    "and Partition Replacement."
)

st.divider()

# Run loading strategies
st.subheader("Run Loading Strategy")

col1, col2, col3 = st.columns(3)

strategies = [
    ("Full Refresh", col1),
    ("Incremental Merge", col2),
    ("Partition Replacement", col3)
]

for strategy, column in strategies:
    with column:
        if st.button(strategy, use_container_width=True):
            try:
                with st.spinner(f"Running {strategy}..."):
                    run_strategy(strategy)

                st.success(f"{strategy} completed!")
                st.rerun()

            except Exception as error:
                st.error(f"Pipeline failed: {error}")


st.divider()

# Record counts
st.subheader("Database Record Counts")

source_count = get_count("source_orders")
full_count = get_count("target_full_refresh")
incremental_count = get_count("target_incremental_merge")
partition_count = get_count("target_partition_replace")
rejected_count = get_count("rejected_records")

c1, c2, c3 = st.columns(3)

c1.metric("Source Records", source_count)
c2.metric("Rejected Records", rejected_count)
c3.metric("Full Refresh Records", full_count)

c4, c5 = st.columns(2)

c4.metric("Incremental Merge Records", incremental_count)
c5.metric("Partition Replacement Records", partition_count)


st.divider()

# Latest successful execution for each strategy
st.subheader("Performance Comparison")

performance = read_query("""
    SELECT strategy, input_count, output_count, duration_ms
    FROM pipeline_runs p
    WHERE status = 'SUCCESS'
    AND rowid = (
        SELECT MAX(rowid)
        FROM pipeline_runs
        WHERE strategy = p.strategy
        AND status = 'SUCCESS'
    )
    ORDER BY strategy
""")

if not performance.empty:
    st.dataframe(performance, use_container_width=True)

    chart_data = performance.set_index("strategy")[
        ["duration_ms"]
    ]

    st.bar_chart(chart_data)

    fastest = performance.loc[
        performance["duration_ms"].idxmin()
    ]

    st.success(
        f"Fastest latest run: {fastest['strategy']} "
        f"({fastest['duration_ms']:.2f} ms)"
    )
else:
    st.info("Run a strategy to see performance results.")


st.divider()

# Pipeline execution history
st.subheader("Pipeline Execution History")

history = read_query("""
    SELECT
        strategy,
        status,
        input_count,
        output_count,
        rejected_count,
        ROUND(duration_ms, 2) AS duration_ms,
        started_at
    FROM pipeline_runs
    ORDER BY rowid DESC
    LIMIT 15
""")

if not history.empty:
    st.dataframe(history, use_container_width=True)
else:
    st.info("No pipeline executions found.")


st.divider()

# Rejected records
st.subheader("Rejected Records")

rejected = read_query("""
    SELECT
        reason,
        source_file,
        rejected_at
    FROM rejected_records
    ORDER BY reject_id DESC
    LIMIT 20
""")

if not rejected.empty:
    st.dataframe(rejected, use_container_width=True)
else:
    st.info("No rejected records found.")


st.caption("Data Loading Strategy Comparison Project")

