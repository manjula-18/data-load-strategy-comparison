
import sqlite3
import pandas as pd
import streamlit as st
from loading_strategies import run_strategy

DB_NAME = "comparison.db"

st.set_page_config(
    page_title="Data Engineering Command Center",
    page_icon="⚡",
    layout="wide"
)

# ---------- DESIGN ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #081323, #101d32);
    color: #edf4ff;
}
[data-testid="stSidebar"] {
    background: #0b1728;
    border-right: 1px solid #203550;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}
h1, h2, h3 {
    color: #edf4ff !important;
}
p, label {
    color: #b7c8dc;
}
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #142944, #102238);
    border: 1px solid #254767;
    padding: 20px;
    border-radius: 14px;
}
[data-testid="stMetricValue"] {
    color: #48d8e8;
}
.stButton > button {
    background: linear-gradient(90deg, #087eaa, #1765bd);
    color: white;
    border: 0;
    border-radius: 10px;
    padding: 12px;
    font-weight: 600;
}
.stButton > button:hover {
    background: #159ac4;
    color: white;
    border: 1px solid #48d8e8;
}
hr {
    border-color: #25415f;
}
</style>
""", unsafe_allow_html=True)


# ---------- DATABASE ----------
def read_query(query):
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query(query, conn)


def get_count(table):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]


# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("## ⚡ DATA ENGINE")
    st.caption("DATA LOADING COMMAND CENTER")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        ["Overview", "Performance", "Execution History", "Data Quality"]
    )

    st.divider()
    st.markdown("### Project Information")
    st.caption("Data Loading Strategy Comparison")
    st.caption("Python • SQLite • Pandas • Streamlit")
    st.caption(
        "Full Refresh | Incremental Merge | Partition Replacement"
    )


# ---------- HEADER ----------
st.markdown("""
<div style="
    background: linear-gradient(110deg,#123b60,#075b82,#123b60);
    padding: 28px;
    border-radius: 18px;
    border: 1px solid #287ba1;
    margin-bottom: 22px;">
    <div style="color:#66e6f2;font-size:13px;font-weight:bold;">
        DATA ENGINEERING / PIPELINE MONITORING
    </div>
    <h1 style="margin:8px 0;color:white;">
        ⚡ Data Engineering Command Center
    </h1>
    <p style="margin:0;color:#d1e9f4;">
        Monitor, execute and compare three database loading strategies.
    </p>
</div>
""", unsafe_allow_html=True)


# ---------- DATABASE METRICS ----------
source_count = get_count("source_orders")
full_count = get_count("target_full_refresh")
incremental_count = get_count("target_incremental_merge")
partition_count = get_count("target_partition_replace")
rejected_count = get_count("rejected_records")

total_runs = read_query(
    "SELECT COUNT(*) AS total FROM pipeline_runs"
).iloc[0]["total"]

k1, k2, k3, k4 = st.columns(4)

k1.metric("📥 Source Records", f"{source_count:,}")
k2.metric("✅ Full Refresh", f"{full_count:,}")
k3.metric("🔄 Incremental Merge", f"{incremental_count:,}")
k4.metric("⚠️ Rejected Records", f"{rejected_count:,}")

st.markdown(
    f"<p style='color:#8fa9c2;font-size:13px;'>"
    f"Total pipeline executions: <b>{total_runs}</b></p>",
    unsafe_allow_html=True
)


# ---------- PIPELINE FLOW ----------
st.markdown("## 🔗 Data Pipeline Architecture")

st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;
flex-wrap:wrap;gap:8px;background:#10243b;padding:22px;
border:1px solid #254767;border-radius:15px;">
<div style="text-align:center;flex:1;min-width:110px;">
<div style="font-size:30px;">📂</div>
<b style="color:#55d9ee;">SOURCE DATA</b>
<p style="font-size:12px;">Incoming records</p>
</div>
<div style="color:#48d8e8;font-size:24px;">➜</div>
<div style="text-align:center;flex:1;min-width:110px;">
<div style="font-size:30px;">🛡️</div>
<b style="color:#55d9ee;">VALIDATION</b>
<p style="font-size:12px;">Quality checks</p>
</div>
<div style="color:#48d8e8;font-size:24px;">➜</div>
<div style="text-align:center;flex:1;min-width:110px;">
<div style="font-size:30px;">⚙️</div>
<b style="color:#55d9ee;">TRANSFORMATION</b>
<p style="font-size:12px;">Loading strategies</p>
</div>
<div style="color:#48d8e8;font-size:24px;">➜</div>
<div style="text-align:center;flex:1;min-width:110px;">
<div style="font-size:30px;">🗄️</div>
<b style="color:#55d9ee;">TARGET DATABASE</b>
<p style="font-size:12px;">SQLite tables</p>
</div>
</div>
""", unsafe_allow_html=True)


# ---------- OVERVIEW ----------
if page == "Overview":
    st.markdown("## 🚀 Execute Loading Strategies")
    st.caption("Choose a strategy to run its data-loading pipeline.")

    descriptions = [
        ("Full Refresh", "🔄", "Replace the complete target dataset."),
        ("Incremental Merge", "⚡", "Load only new or changed records."),
        ("Partition Replacement", "📦", "Replace affected data partitions.")
    ]

    cols = st.columns(3)

    for i, (strategy, icon, description) in enumerate(descriptions):
        with cols[i]:
            st.markdown(
                f"""
                <div style="background:#142b45;padding:18px;
                border:1px solid #2b5275;border-radius:14px;
                min-height:125px;">
                <div style="font-size:27px;">{icon}</div>
                <h3 style="margin:8px 0;">{strategy}</h3>
                <p style="font-size:13px;">{description}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                f"▶ Run {strategy}",
                key=f"run_{i}",
                width="stretch"
            ):
                try:
                    with st.spinner(f"Executing {strategy}..."):
                        run_strategy(strategy)

                    st.success(f"{strategy} completed successfully!")
                    st.rerun()

                except Exception as error:
                    st.error(f"Pipeline failed: {error}")

    st.markdown("## 📊 Target Database Overview")

    target_data = pd.DataFrame({
        "Loading Strategy": [
            "Full Refresh",
            "Incremental Merge",
            "Partition Replacement"
        ],
        "Target Records": [
            full_count,
            incremental_count,
            partition_count
        ]
    })

    st.bar_chart(
        target_data.set_index("Loading Strategy"),
        y="Target Records"
    )


# ---------- PERFORMANCE ----------
if page == "Performance":
    st.markdown("## 📈 Performance Analytics")

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
        st.dataframe(performance, width="stretch")

        st.markdown("### Execution Time Comparison")

        st.bar_chart(
            performance.set_index("strategy"),
            y="duration_ms"
        )

        fastest = performance.loc[
            performance["duration_ms"].idxmin()
        ]

        st.success(
            f"Fastest latest run: {fastest['strategy']} "
            f"({fastest['duration_ms']:.2f} ms)"
        )

        st.caption(
            "Execution times depend on the number of records processed. "
            "Compare workloads before drawing conclusions."
        )
    else:
        st.info("Run a strategy to generate performance results.")


# ---------- EXECUTION HISTORY ----------
if page == "Execution History":
    st.markdown("## 🕒 Pipeline Execution Monitor")

    history = read_query("""
        SELECT strategy, status, input_count, output_count,
        rejected_count, ROUND(duration_ms, 2) AS duration_ms,
        started_at
        FROM pipeline_runs
        ORDER BY rowid DESC
        LIMIT 30
    """)

    if not history.empty:
        st.dataframe(history, width="stretch")
    else:
        st.info("No execution history available yet.")


# ---------- DATA QUALITY ----------
if page == "Data Quality":
    st.markdown("## 🛡️ Data Quality Center")

    st.metric("Total Rejected Records", f"{rejected_count:,}")

    rejected = read_query("""
        SELECT reason, source_file, rejected_at
        FROM rejected_records
        ORDER BY reject_id DESC
        LIMIT 50
    """)

    if not rejected.empty:
        st.markdown("### Rejected Record Details")
        st.dataframe(rejected, width="stretch")

        st.markdown("### Rejection Reasons")

        reason_counts = (
            rejected["reason"]
            .fillna("Unknown")
            .value_counts()
            .reset_index()
        )

        reason_counts.columns = ["Reason", "Count"]

        st.bar_chart(
            reason_counts.set_index("Reason"),
            y="Count"
        )
    else:
        st.success("No rejected records found.")


# ---------- FOOTER ----------
st.divider()

st.markdown(
    "<p style='text-align:center;color:#7893ad;font-size:12px;'>"
    "DATA ENGINEERING COMMAND CENTER | Built with Python, "
    "SQLite, Pandas and Streamlit</p>",
    unsafe_allow_html=True
)
