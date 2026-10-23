# Pipeline Guardian

**Track 04: The Work Behind the Work** — a lightweight data operations dashboard that helps teams spot pipeline failures, delayed jobs, stale datasets, and data-quality risks before business reports are affected.

## Problem

Teams rely on scheduled data pipelines for reporting and operational decisions. Failures, unexpected zero-row outputs, stale datasets, missing values, and duplicate records can go unnoticed. Investigating these issues manually delays decisions and erodes trust in dashboards.

## Solution

Pipeline Guardian provides a Streamlit dashboard with:
- Pipeline run status and a simple operational health indicator
- Rule-based incident detection with severity levels
- Actionable diagnostic recommendations
- Demo data-quality checks for missing values, duplicate rows, stale datasets, and unexpectedly low row counts
- CSV upload for basic pipeline-run monitoring
- Downloadable incident report

## Important scope note

This hackathon prototype uses simulated demo records and transparent rules. It does **not** connect to production orchestration tools, send real alerts, or prove actual business savings. Uploaded CSV monitoring supports the documented fields; quality details for uploaded data are inferred only from available run metadata.

## Tech stack

- Python
- Streamlit
- Pandas
- Plotly

## Run locally

1. Install Python 3.10 or newer.
2. Clone this repository or download the project folder.
3. Open a terminal in the project directory.
4. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # macOS/Linux:
   source .venv/bin/activate
   ```

5. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Start the app:

   ```bash
   streamlit run app.py
   ```

7. Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Upload format

Use a CSV containing these required columns:

| Column | Meaning | Example |
|---|---|---|
| `pipeline_id` | Unique pipeline name | `sales_daily` |
| `status` | Run status | `Success`, `Failed`, `Delayed`, `Warning` |
| `duration_min` | Runtime in minutes | `12` |
| `last_run` | Timestamp of last run | `2026-10-24 02:00:00` |
| `records_processed` | Number of records processed | `1200` |

Optional columns: `business_use`, `failed_checks`.

A sample file is included at `data/sample_pipeline_runs.csv`.

## Deployment

### Streamlit Community Cloud
1. Push the repository to a public GitHub repository.
2. Sign in to Streamlit Community Cloud and choose **Create app**.
3. Select the repository, branch, and `app.py` as the main file.
4. Deploy. No secrets are required for the demo.

### Local deployment
Follow the Run locally instructions above. For a live demo, test the app and CSV upload before recording.

## Demo flow (under 3 minutes)

1. **0:00–0:25 — Problem:** Explain that silent pipeline failures and stale data undermine business reporting.
2. **0:25–0:55 — Overview:** Show the pipeline status metrics and operational health indicator.
3. **0:55–1:35 — Incident centre:** Highlight a failed customer sync, zero records, and recommended investigation steps.
4. **1:35–2:10 — Data quality:** Show missing values, duplicates, and record-volume thresholds.
5. **2:10–2:35 — Practical use:** Upload a CSV and download the incident report.
6. **2:35–2:55 — Impact and roadmap:** Explain how connectors, notifications, and historical baselines could be added next.

## Roadmap

- Connect to orchestration systems such as Airflow or Prefect
- Store incident history and track recovery time
- Add email/Slack notifications
- Learn expected data-volume patterns from historical runs
- Add configurable dataset contracts and team ownership

## License

Released under the MIT License. See `LICENSE`.
