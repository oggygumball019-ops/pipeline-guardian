import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Pipeline Guardian", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: #f5f7fb; padding: 14px 16px; border-radius: 12px; border: 1px solid #e7eaf0;}
.small-note {color: #64748b; font-size: 0.9rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
[data-testid="stMetric"] {
    background-color: #1e293b !important;
    border: 1px solid #475569 !important;
    padding: 16px !important;
    border-radius: 10px !important;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p {
    color: #cbd5e1 !important;
}

[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div {
    color: #ffffff !important;
}

[data-testid="stMetricDelta"] {
    color: #93c5fd !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Pipeline Guardian")
st.caption("Data operations observability · Detect issues before they undermine business decisions")
st.info("Demo environment: sample records are simulated for this prototype. No live production systems are connected.")

def demo_runs():
    now = datetime.now().replace(second=0, microsecond=0)
    rows = [
        ("sales_daily", "Sales reporting", "Success", 3, now - timedelta(hours=1), 120, 0),
        ("customer_sync", "Customer platform", "Failed", 0, now - timedelta(hours=2), 0, 1),
        ("inventory_refresh", "Inventory dashboard", "Delayed", 28, now - timedelta(hours=4), 80, 0),
        ("payments_etl", "Finance reporting", "Success", 5, now - timedelta(hours=1, minutes=30), 540, 0),
        ("marketing_events", "Marketing analytics", "Warning", 12, now - timedelta(hours=7), 300, 0),
        ("product_catalog", "Product analytics", "Success", 4, now - timedelta(hours=2, minutes=30), 210, 0),
        ("returns_pipeline", "Operations dashboard", "Failed", 0, now - timedelta(hours=6), 0, 1),
        ("web_sessions", "Growth dashboard", "Success", 7, now - timedelta(hours=1), 1800, 0),
    ]
    return pd.DataFrame(rows, columns=["pipeline_id","business_use","status","duration_min","last_run","records_processed","failed_checks"])

def demo_quality():
    return pd.DataFrame([
        {"dataset":"sales_daily","rows":1200,"missing_values":0,"duplicate_rows":0,"last_updated_hours":1,"expected_min_rows":900},
        {"dataset":"customer_sync","rows":0,"missing_values":0,"duplicate_rows":0,"last_updated_hours":26,"expected_min_rows":500},
        {"dataset":"inventory_refresh","rows":80,"missing_values":12,"duplicate_rows":3,"last_updated_hours":4,"expected_min_rows":200},
        {"dataset":"payments_etl","rows":540,"missing_values":2,"duplicate_rows":0,"last_updated_hours":2,"expected_min_rows":400},
        {"dataset":"marketing_events","rows":300,"missing_values":18,"duplicate_rows":4,"last_updated_hours":7,"expected_min_rows":250},
        {"dataset":"product_catalog","rows":210,"missing_values":0,"duplicate_rows":0,"last_updated_hours":3,"expected_min_rows":150},
        {"dataset":"returns_pipeline","rows":0,"missing_values":0,"duplicate_rows":0,"last_updated_hours":12,"expected_min_rows":100},
        {"dataset":"web_sessions","rows":1800,"missing_values":7,"duplicate_rows":2,"last_updated_hours":1,"expected_min_rows":1000},
    ])

def classify(row, stale_hours=6):
    issues = []
    if str(row["status"]).lower() == "failed":
        issues.append(("Critical", "Pipeline run failed", "Inspect the latest job logs, credentials, and upstream dependencies."))
    if int(row["records_processed"]) == 0:
        issues.append(("High", "No records processed", "Check source availability and confirm whether an empty result is expected."))
    if str(row["status"]).lower() == "delayed":
        issues.append(("High", "Pipeline is delayed", "Review runtime history and upstream dependencies; rerun only after validating the cause."))
    if str(row["status"]).lower() == "warning":
        issues.append(("Medium", "Pipeline warning", "Review warning logs and validate the output before refreshing business reports."))
    if pd.notna(row.get("last_updated_hours")) and float(row["last_updated_hours"]) > stale_hours:
        issues.append(("High", "Dataset may be stale", "Confirm the expected refresh schedule and check the most recent successful run."))
    if int(row.get("missing_values", 0)) > 0:
        issues.append(("Medium", "Missing values detected", "Check source fields and transformation rules; quantify affected rows before publishing."))
    if int(row.get("duplicate_rows", 0)) > 0:
        issues.append(("Medium", "Duplicate rows detected", "Check primary-key uniqueness and deduplication logic before downstream aggregation."))
    if int(row.get("rows", 0)) < int(row.get("expected_min_rows", 0)):
        issues.append(("High", "Record volume below threshold", "Compare with historical volumes and verify source ingestion completeness."))
    return issues

with st.sidebar:
    st.header("Controls")
    mode = st.radio("Data source", ["Demo data", "Upload pipeline CSV"], index=0)
    stale_hours = st.slider("Stale dataset threshold (hours)", 1, 48, 6)
    st.caption("Upload CSV columns: pipeline_id, status, duration_min, last_run, records_processed. Optional: business_use, failed_checks.")
    uploaded = st.file_uploader("Upload pipeline runs CSV", type=["csv"]) if mode == "Upload pipeline CSV" else None

runs = demo_runs()
if mode == "Upload pipeline CSV":
    if uploaded is None:
        st.warning("Upload a CSV to inspect your pipeline runs. The demo view is shown until a file is uploaded.")
    else:
        try:
            user_df = pd.read_csv(uploaded)
            required = {"pipeline_id","status","duration_min","last_run","records_processed"}
            missing = required - set(user_df.columns)
            if missing:
                st.error("Missing required columns: " + ", ".join(sorted(missing)))
            else:
                if "business_use" not in user_df: user_df["business_use"] = "Not specified"
                if "failed_checks" not in user_df: user_df["failed_checks"] = 0
                user_df["last_run"] = pd.to_datetime(user_df["last_run"], errors="coerce")
                runs = user_df
        except Exception as exc:
            st.error(f"Could not read the CSV: {exc}")

quality = demo_quality()
if mode == "Upload pipeline CSV" and uploaded is not None and "runs" in locals() and not runs.equals(demo_runs()):
    # For user uploads, pipeline-level checks are still useful without a separate quality file.
    quality = pd.DataFrame({
        "dataset": runs["pipeline_id"],
        "rows": pd.to_numeric(runs["records_processed"], errors="coerce").fillna(0).astype(int),
        "missing_values": 0,
        "duplicate_rows": 0,
        "last_updated_hours": (
            pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None)
            - pd.to_datetime(runs["last_run"], errors="coerce")
        ).dt.total_seconds().div(3600).clip(lower=0).fillna(0).round(1),
    })

runs["status"] = runs["status"].astype(str).str.title()
status_filter = st.multiselect("Filter pipeline status", sorted(runs["status"].dropna().unique()), default=sorted(runs["status"].dropna().unique()))
filtered = runs[runs["status"].isin(status_filter)].copy()

issues = []
for _, row in filtered.iterrows():
    q = quality[quality["dataset"] == row["pipeline_id"]]
    merged = row.to_dict()
    if not q.empty:
        merged.update(q.iloc[0].to_dict())
    else:
        merged.update({"rows": int(row.get("records_processed", 0)), "missing_values": 0, "duplicate_rows": 0, "last_updated_hours": 0, "expected_min_rows": 1})
    for severity, title, recommendation in classify(merged, stale_hours):
        issues.append({
            "Pipeline": row["pipeline_id"],
            "Business use": row.get("business_use", "Not specified"),
            "Severity": severity,
            "Issue": title,
            "Recommended next step": recommendation
        })
incidents = pd.DataFrame(issues, columns=["Pipeline","Business use","Severity","Issue","Recommended next step"])

total = len(filtered)
failed = int((filtered["status"] == "Failed").sum())
success = int((filtered["status"] == "Success").sum())
incident_count = len(incidents)
health = max(0, round(100 * (1 - min(1, (failed + int((filtered["status"] == "Delayed").sum()) + int((filtered["status"] == "Warning").sum())) / max(total,1)))))

c1,c2,c3,c4 = st.columns(4)
c1.metric("Pipelines monitored", total)
c2.metric("Successful runs", success)
c3.metric("Failed runs", failed, delta=f"{failed} need attention" if failed else "No failed runs", delta_color="inverse")
c4.metric("Detected issues", incident_count)

left, right = st.columns([1.3,1])
with left:
    st.subheader("Pipeline run status")
    if not filtered.empty:
        status_counts = filtered["status"].value_counts().rename_axis("Status").reset_index(name="Pipelines")
        st.plotly_chart(px.bar(status_counts, x="Status", y="Pipelines", color="Status", title="Runs by status"), use_container_width=True)
    else:
        st.write("No pipelines match this filter.")
with right:
    st.subheader("Operational health")
    st.metric("Health indicator", f"{health}/100")
    st.progress(health / 100)
    st.caption("Prototype indicator based on the share of runs marked failed, delayed, or warning. It is not a certified SLA metric.")

st.subheader("Incident centre")
if incidents.empty:
    st.success("No issues detected under the current settings.")
else:
    sev_filter = st.multiselect("Severity", ["Critical","High","Medium"], default=["Critical","High","Medium"])
    view = incidents[incidents["Severity"].isin(sev_filter)].copy()
    order = {"Critical":0,"High":1,"Medium":2}
    if not view.empty:
        view["_order"] = view["Severity"].map(order)
        view = view.sort_values(["_order","Pipeline"]).drop(columns="_order")
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.download_button("Download incident report CSV", view.to_csv(index=False).encode("utf-8"), "pipeline_guardian_incidents.csv", "text/csv")

st.subheader("Dataset quality checks")
st.caption("Demo quality checks use simulated values. Uploaded pipeline CSVs support status, zero-record, and stale-run checks.")
qview = quality.copy()
qview["Quality status"] = qview.apply(
    lambda r: "Critical" if r["rows"] == 0 or r["rows"] < r["expected_min_rows"] else
              ("Warning" if r["missing_values"] > 0 or r["duplicate_rows"] > 0 or r["last_updated_hours"] > stale_hours else "Healthy"), axis=1)
st.dataframe(qview.rename(columns={
    "dataset":"Dataset","rows":"Rows processed","missing_values":"Missing values",
    "duplicate_rows":"Duplicate rows","last_updated_hours":"Hours since update",
    "expected_min_rows":"Expected minimum rows"
}), use_container_width=True, hide_index=True)

st.divider()
st.caption("Pipeline Guardian prototype · Rules-based detection with explainable recommendations · Demo data is simulated.")
