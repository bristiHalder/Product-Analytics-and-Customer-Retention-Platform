"""Page 3 — Cohort Analysis.

Executive question: Are users returning?
"""
from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components import theme, ui  # noqa: E402
from src.analytics import cohort as ch  # noqa: E402

theme.setup_page("Cohort Analysis", "🗓️")

data = ui.load_data()
f = ui.sidebar_filters(data["fact_events"])
frames = ui.filtered_frames(data, f)
events = frames["events"]

ui.page_title("🗓️", "Cohort Analysis", "Are users returning?")

if events.empty:
    theme.insight("No data matches the current filters. Widen the date range or clear filters.", "warning")
    st.stop()

dayn = ch.day_n_retention(events)
matrix = ch.monthly_cohort_matrix(events)

# ── Executive Retention Insight (answer in 5 seconds) ─────────────────────────
d1_val = float(dayn.loc[dayn["day"] == "D1", "retention_pct"].iloc[0]) if not dayn.empty else 0
d7_val = float(dayn.loc[dayn["day"] == "D7", "retention_pct"].iloc[0]) if not dayn.empty else 0
d30_val = float(dayn.loc[dayn["day"] == "D30", "retention_pct"].iloc[0]) if not dayn.empty else 0
d90_val = float(dayn.loc[dayn["day"] == "D90", "retention_pct"].iloc[0]) if not dayn.empty else 0

if d30_val >= 20:
    ret_status = "Strong"
    ret_summary = "Users are forming habits — focus on monetising retained users."
elif d30_val >= 10:
    ret_status = "Stable"
    ret_summary = "Retention is acceptable but has room to improve through onboarding optimisation."
else:
    ret_status = "Weak"
    ret_summary = "Retention is below industry benchmarks — invest heavily in onboarding and lifecycle messaging."

best_cohort = None
if not matrix.empty and matrix.shape[1] > 1:
    m1_col = matrix.iloc[:, 1]
    if m1_col.notna().any():
        best_cohort = m1_col.idxmax()
        best_cohort_val = float(m1_col.max())

theme.hero_insight(
    eyebrow="RETENTION STATUS",
    headline=f"Day-30 retention: {d30_val:.1f}% — {ret_status}",
    body=(
        f"D1: {d1_val:.1f}% → D7: {d7_val:.1f}% → D30: {d30_val:.1f}% → D90: {d90_val:.1f}%. "
        f"{ret_summary}"
        + (f" Strongest cohort: <b>{best_cohort}</b> ({best_cohort_val:.0f}% month-1 retention)." if best_cohort else "")
    ),
    bg=theme.SUCCESS_SOFT if ret_status == "Strong" else (theme.PRIMARY_SOFT if ret_status == "Stable" else theme.DANGER_SOFT),
)

# ── Day-N retention KPI cards ─────────────────────────────────────────────────
theme.kpi_group_label("DAY-N RETENTION", theme.SUCCESS)
cols = st.columns(4, gap="medium")
benchmarks = {"D1": 40, "D7": 20, "D30": 10, "D90": 5}
for col, (_, row) in zip(cols, dayn.iterrows()):
    bench = benchmarks.get(row["day"], 10)
    status = "above" if row["retention_pct"] >= bench else "below"
    ui.kpi_card(col, f"{row['day']} Retention", f"{row['retention_pct']:.1f}%",
                help_text=f"{int(row['retained_users']):,} users active on day {row['day'][1:]}",
                context=f"{'✓' if status == 'above' else '⚠'} Benchmark: ≥{bench}%")

# ── Retention heatmap (centerpiece) ───────────────────────────────────────────
theme.section("Retention Heatmap", "Rows = acquisition cohort · Columns = months since acquisition")
if matrix.empty:
    theme.insight("Not enough cohort history to render the heatmap.", "info")
else:
    fig = px.imshow(
        matrix,
        labels=dict(x="Months Since Acquisition", y="Cohort", color="Retention %"),
        color_continuous_scale="Blues",
        aspect="auto",
        text_auto=".0f",
    )
    fig.update_layout(height=480)
    theme.plot(fig, 480, container=st)

    with st.expander("View retention matrix"):
        st.dataframe(matrix, use_container_width=True)

# ── Business Impact Insights ──────────────────────────────────────────────────
theme.section("Retention Insights")
insights = ch.retention_insights(matrix, dayn)
for ins in insights:
    ui.insight(ins, "info")

if d30_val < 10:
    theme.finding_card(
        what=f"Day-30 retention at {d30_val:.1f}% is below the 10% benchmark",
        why="Users are not forming a habit loop — likely weak onboarding or low perceived value after first session",
        impact="Low retention compounds into high churn and rising acquisition costs",
        action="Invest in onboarding improvements, push notifications at D1/D3/D7, and first-session personalisation",
    )
