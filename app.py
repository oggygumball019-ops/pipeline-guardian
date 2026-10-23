
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Pipeline Guardian",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {
        background-color: #1e293b !important;
        border: 1px solid #475569 !important;
        padding: 16px !important;
        border-radius: 10px !important;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {
        color: #cbd5e1 !important;
    }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] div {
        color: #ffffff !important;
    }
    [data-testid="stMetricDelta"] {color: #93c5fd !important;}
    .small-note {color: #94a3b8; font-size: 0.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛡️ Pipeline Guardian")
st.caption(
    "Data operations observability · Detect issues before they undermine business decisions"
)
st.info(
    "Demo environment: sample records are simulated for this prototype. "
    "No live production systems are connected."
)

QUALITY_COLUMNS = [
    "dataset",
    "rows",
    "missing_values",
    "duplicate_rows",
    "last_updated_hours",
    "expected_min_rows",
]
INCIDENT_COLUMNS = [
    "Pipeline",
    "Business use",
    "Severity",
    "Issue",
    "Recommended next step",
]


def safe_int(value, default=0):
    """Convert a value to int safely."""
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except (TypeError, ValueError, OverflowError):
        return default


def normalize_quality(df):
    """Ensure all quality columns exist and numeric fields are usable."""
    result = df.copy()
    defaults = {
        "dataset": "Unknown dataset",
        "rows": 0,
        "missing_values": 0,
        "duplicate_rows": 0,
        "last_updated_hours": 0.0,
        "expected_min_rows": 1,
    }

    for column, default in defaults.items():
        if column not in result.columns:
            result[column] = default

    for column in [
        "rows",
        "missing_values",
        "duplicate_rows",
        "last_updated_hours",
        "expected_min_rows",
    ]:
        result[column] = pd.to_numeric(
            result[column], errors="coerce"
        ).fillna(defaults[column])

    result["dataset"] = (
        result["dataset"].fillna("Unknown dataset").astype(str)
    )
    return result[QUALITY_COLUMNS].copy()


def demo_runs():
    now = datetime.now().replace(second=0, microsecond=0)
    data = [
        ("sales_daily", "Sales reporting", "Success", 3, now - timedelta(hours=1), 1200, 0),
        ("customer_sync", "Customer platform", "Failed", 0, now - timedelta(hours=2), 0, 1),
        ("inventory_refresh", "Inventory dashboard", "Delayed", 28, now - timedelta(hours=4), 80, 0),
        ("payments_etl", "Finance reporting", "Success", 5, now - timedelta(hours=1, minutes=30), 540, 0),
        ("marketing_events", "Marketing analytics", "Warning", 12, now - timedelta(hours=7), 300, 0),
        ("product_catalog", "Product analytics", "Success", 4, now - timedelta(hours=2, minutes=30), 210, 0),
        ("returns_pipeline", "Operations dashboard", "Failed", 0, now - timedelta(hours=6), 0, 1),
        ("web_sessions", "Growth dashboard", "Success", 7, now - timedelta(hours=1), 1800, 0),
    ]
    return pd.DataFrame(
        data,
        columns=[
            "pipeline_id",
            "business_use",
            "status",
            "duration_min",
            "last_run",
            "records_processed",
            "failed_checks",
        ],
    )


def demo_quality():
    data = [
        {"dataset": "sales_daily", "rows": 1200, "missing_values": 0, "duplicate_rows": 0, "last_updated_hours": 1, "expected_min_rows": 900},
        {"dataset": "customer_sync", "rows": 0, "missing_values": 0, "duplicate_rows": 0, "last_updated_hours": 26, "expected_min_rows": 500},
        {"dataset": "inventory_refresh", "rows": 80, "missing_values": 12, "duplicate_rows": 3, "last_updated_hours": 4, "expected_min_rows": 200},
        {"dataset": "payments_etl", "rows": 540, "missing_values": 2, "duplicate_rows": 0, "last_updated_hours": 2, "expected_min_rows": 400},
        {"dataset": "marketing_events", "rows": 300, "missing_values": 18, "duplicate_rows": 4, "last_updated_hours": 7, "expected_min_rows": 250},
        {"dataset": "product_catalog", "rows": 210, "missing_values": 0, "duplicate_rows": 0, "last_updated_hours": 3, "expected_min_rows": 150},
        {"dataset": "returns_pipeline", "rows": 0, "missing_values": 0, "duplicate_rows": 0, "last_updated_hours": 12, "expected_min_rows": 100},
        {"dataset": "web_sessions", "rows": 1800, "missing_values": 7, "duplicate_rows": 2, "last_updated_hours": 1, "expected_min_rows": 1000},
    ]
    return pd.DataFrame(data, columns=QUALITY_COLUMNS)


def classify(row, stale_hours=6):
    """Return explainable incidents for one pipeline/quality record."""
    issues = []
    status = str(row.get("status", "Unknown")).strip().lower()
    records = safe_int(row.get("records_processed", row.get("rows", 0)))
    rows = safe_int(row.get("rows", records))
    expected = safe_int(row.get("expected_min_rows", 0))

    if status == "failed":
        issues.append((
            "Critical",
            "Pipeline run failed",
            "Inspect the latest job logs, credentials, and upstream dependencies.",
        ))

    if records == 0:
        issues.append((
            "High",
            "No records processed",
            "Check source availability and confirm whether an empty result is expected.",
        ))

    if status == "delayed":
        issues.append((
            "High",
            "Pipeline is delayed",
            "Review runtime history and upstream dependencies; rerun only after validating the cause.",
        ))

    if status == "warning":
        issues.append((
            "Medium",
            "Pipeline warning",
            "Review warning logs and validate the output before refreshing business reports.",
        ))

    age = pd.to_numeric(
        pd.Series([row.get("last_updated_hours", 0)]),
        errors="coerce",
    ).fillna(0).iloc[0]

    if age > stale_hours:
        issues.append((
            "High",
            "Dataset may be stale",
            "Confirm the expected refresh schedule and check the most recent successful run.",
        ))

    if safe_int(row.get("missing_values", 0)) > 0:
        issues.append((
            "Medium",
            "Missing values detected",
            "Check source fields and transformation rules; quantify affected rows before publishing.",
        ))

    if safe_int(row.get("duplicate_rows", 0)) > 0:
        issues.append((
            "Medium",
            "Duplicate rows detected",
            "Check primary-key uniqueness and deduplication logic before downstream aggregation.",
        ))

    if expected > 0 and rows < expected:
        issues.append((
            "High",
            "Record volume below threshold",
            "Compare with historical volumes and verify source ingestion completeness.",
        ))

    return issues


# Sidebar controls
with st.sidebar:
    st.header("Controls")
    mode = st.radio(
        "Data source",
        ["Demo data", "Upload pipeline CSV"],
        index=0,
    )
    stale_hours = st.slider(
        "Stale dataset threshold (hours)",
        min_value=1,
        max_value=48,
        value=6,
    )
    st.caption(
        "Required CSV columns: pipeline_id, status, duration_min, "
        "last_run, records_processed. Optional: business_use, failed_checks, "
        "rows, missing_values, duplicate_rows, last_updated_hours, expected_min_rows."
    )
    uploaded = (
        st.file_uploader("Upload pipeline runs CSV", type=["csv"])
        if mode == "Upload pipeline CSV"
        else None
    )


# Load demo data first; a valid upload replaces it.
runs = demo_runs()
quality = demo_quality()
valid_upload = False

if mode == "Upload pipeline CSV":
    if uploaded is None:
        st.warning(
            "Upload a CSV to inspect your pipeline runs. "
            "Demo data is shown until a file is uploaded."
        )
    else:
        try:
            user_df = pd.read_csv(uploaded)
            required = {
                "pipeline_id",
                "status",
                "duration_min",
                "last_run",
                "records_processed",
            }
            missing = required - set(user_df.columns)

            if missing:
                st.error(
                    "Missing required columns: "
                    + ", ".join(sorted(missing))
                )
            elif user_df.empty:
                st.error(
                    "The uploaded CSV has headers but no data rows. "
                    "Please upload a CSV with at least one pipeline run."
                )
            else:
                if "business_use" not in user_df.columns:
                    user_df["business_use"] = "Not specified"
                if "failed_checks" not in user_df.columns:
                    user_df["failed_checks"] = 0

                user_df["pipeline_id"] = (
                    user_df["pipeline_id"]
                    .fillna("unknown_pipeline")
                    .astype(str)
                )
                user_df["status"] = (
                    user_df["status"]
                    .fillna("Unknown")
                    .astype(str)
                    .str.strip()
                    .str.title()
                )
                user_df["records_processed"] = pd.to_numeric(
                    user_df["records_processed"], errors="coerce"
                ).fillna(0).astype(int)
                user_df["duration_min"] = pd.to_numeric(
                    user_df["duration_min"], errors="coerce"
                ).fillna(0)

                # Interpret timezone-naive timestamps as India Standard Time.
                parsed = pd.to_datetime(
                    user_df["last_run"], errors="coerce"
                )
                if parsed.dt.tz is None:
                    parsed = parsed.dt.tz_localize(
                        "Asia/Kolkata",
                        ambiguous="NaT",
                        nonexistent="shift_forward",
                    )
                parsed_utc = parsed.dt.tz_convert("UTC")
                now_utc = pd.Timestamp.now(tz="UTC")
                calculated_age = (
                    (now_utc - parsed_utc).dt.total_seconds() / 3600
                ).clip(lower=0)

                runs = user_df.copy()

                # Optional quality fields are honored if supplied.
                quality = pd.DataFrame({
                    "dataset": runs["pipeline_id"],
                    "rows": (
                        pd.to_numeric(user_df["rows"], errors="coerce")
                        if "rows" in user_df.columns
                        else runs["records_processed"]
                    ),
                    "missing_values": (
                        pd.to_numeric(user_df["missing_values"], errors="coerce")
                        if "missing_values" in user_df.columns
                        else 0
                    ),
                    "duplicate_rows": (
                        pd.to_numeric(user_df["duplicate_rows"], errors="coerce")
                        if "duplicate_rows" in user_df.columns
                        else 0
                    ),
                    "last_updated_hours": (
                        pd.to_numeric(user_df["last_updated_hours"], errors="coerce")
                        if "last_updated_hours" in user_df.columns
                        else calculated_age
                    ),
                    "expected_min_rows": (
                        pd.to_numeric(user_df["expected_min_rows"], errors="coerce")
                        if "expected_min_rows" in user_df.columns
                        else 1
                    ),
                })
                quality = normalize_quality(quality)
                valid_upload = True

        except Exception as exc:
            st.error(f"Could not read the CSV: {exc}")


quality = normalize_quality(quality)
runs["status"] = (
    runs["status"].fillna("Unknown").astype(str).str.strip().str.title()
)
runs["records_processed"] = pd.to_numeric(
    runs["records_processed"], errors="coerce"
).fillna(0).astype(int)

status_options = sorted(runs["status"].dropna().unique().tolist())
status_filter = st.multiselect(
    "Filter pipeline status",
    status_options,
    default=status_options,
)
filtered = runs[runs["status"].isin(status_filter)].copy()


# Generate incidents. The quality metadata is matched by pipeline ID.
issues = []
for _, row in filtered.iterrows():
    pipeline_id = str(row["pipeline_id"])
    matching_quality = quality[quality["dataset"] == pipeline_id]

    merged = row.to_dict()
    if not matching_quality.empty:
        quality_row = matching_quality.iloc[0].to_dict()
        merged.update({
            "rows": safe_int(
                quality_row.get("rows", row.get("records_processed", 0))
            ),
            "last_updated_hours": safe_int(
                quality_row.get("last_updated_hours", 0)
            ),
            "expected_min_rows": safe_int(
                quality_row.get("expected_min_rows", 1)
            ),
            "missing_values": safe_int(
                quality_row.get("missing_values", 0)
            ),
            "duplicate_rows": safe_int(
                quality_row.get("duplicate_rows", 0)
            ),
        })
    else:
        merged.update({
            "rows": safe_int(row.get("records_processed", 0)),
            "last_updated_hours": 0,
            "expected_min_rows": 1,
            "missing_values": 0,
            "duplicate_rows": 0,
        })

    for severity, title, recommendation in classify(merged, stale_hours):
        issues.append({
            "Pipeline": pipeline_id,
            "Business use": row.get("business_use", "Not specified"),
            "Severity": severity,
            "Issue": title,
            "Recommended next step": recommendation,
        })

incidents = pd.DataFrame(issues, columns=INCIDENT_COLUMNS)


# Summary metrics
total = len(filtered)
failed = int((filtered["status"] == "Failed").sum())
success = int((filtered["status"] == "Success").sum())
incident_count = len(incidents)
attention_count = int(
    filtered["status"].isin(["Failed", "Delayed", "Warning"]).sum()
)
health = max(0, round(100 * (1 - attention_count / max(total, 1))))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Pipelines monitored", total)
c2.metric("Successful runs", success)
c3.metric(
    "Failed runs",
    failed,
    delta=f"{failed} need attention" if failed else "No failed runs",
    delta_color="inverse",
)
c4.metric("Detected issues", incident_count)

left, right = st.columns([1.3, 1])
with left:
    st.subheader("Pipeline run status")
    if not filtered.empty:
        status_counts = (
            filtered["status"]
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Pipelines")
        )
        st.plotly_chart(
            px.bar(
                status_counts,
                x="Status",
                y="Pipelines",
                color="Status",
                title="Runs by status",
            ),
            use_container_width=True,
        )
    else:
        st.write("No pipelines match this filter.")

with right:
    st.subheader("Operational health")
    st.metric("Health indicator", f"{health}/100")
    st.progress(health / 100)
    st.caption(
        "Prototype indicator based on the share of runs marked failed, "
        "delayed, or warning. It is not a certified SLA metric."
    )


# Incident centre
st.subheader("Incident centre")
if incidents.empty:
    st.success("No issues detected under the current settings.")
else:
    sev_filter = st.multiselect(
        "Severity",
        ["Critical", "High", "Medium"],
        default=["Critical", "High", "Medium"],
    )
    view = incidents[incidents["Severity"].isin(sev_filter)].copy()
    order = {"Critical": 0, "High": 1, "Medium": 2}
    if not view.empty:
        view["_order"] = view["Severity"].map(order).fillna(3)
        view = (
            view.sort_values(["_order", "Pipeline"])
            .drop(columns="_order")
        )
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.download_button(
        "Download incident report CSV",
        view.to_csv(index=False).encode("utf-8"),
        "pipeline_guardian_incidents.csv",
        "text/csv",
    )


# Dataset quality checks
st.subheader("Dataset quality checks")
if valid_upload:
    st.caption(
        "Uploaded CSV checks include run status, zero-record, stale-run, "
        "and record-volume checks. Missing-value and duplicate checks use "
        "the optional columns if they are supplied; otherwise those counts are zero."
    )
else:
    st.caption(
        "Demo quality checks use simulated values. "
        "No live production systems are connected."
    )

qview = normalize_quality(quality)
qview["Quality status"] = qview.apply(
    lambda r: (
        "Critical"
        if r["rows"] == 0 or (
            r["expected_min_rows"] > 0
            and r["rows"] < r["expected_min_rows"]
        )
        else (
            "Warning"
            if r["missing_values"] > 0
            or r["duplicate_rows"] > 0
            or r["last_updated_hours"] > stale_hours
            else "Healthy"
        )
    ),
    axis=1,
)

st.dataframe(
    qview.rename(columns={
        "dataset": "Dataset",
        "rows": "Rows processed",
        "missing_values": "Missing values",
        "duplicate_rows": "Duplicate rows",
        "last_updated_hours": "Hours since update",
        "expected_min_rows": "Expected minimum rows",
    }),
    use_container_width=True,
    hide_index=True,
)

st.divider()
st.caption(
    "Pipeline Guardian prototype · Rules-based detection with explainable "
    "recommendations · Demo data is simulated."
)
