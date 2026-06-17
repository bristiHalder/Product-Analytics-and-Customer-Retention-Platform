"""Page 5 — Feature Adoption Analysis.

Executive question: Which behaviors create retention and revenue?
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
from src.analytics import feature_adoption as fa  # noqa: E402

theme.setup_page("Feature Adoption", "🧩")

data = ui.load_data()
f = ui.sidebar_filters(data["fact_events"])
frames = ui.filtered_frames(data, f)
users = frames["users"]

ui.page_title("🧩", "Feature Adoption", "Which behaviors create retention and revenue?")

if users.empty:
    theme.insight("No data matches the current filters. Widen the date range or clear filters.", "warning")
    st.stop()

table = fa.adoption_table(users)
ranking = fa.feature_value_ranking(table)

# ── Executive insight (answer in 5 seconds) ───────────────────────────────────
most_val = ranking["most_valuable"]
least_val = ranking["least_valuable"]
most_row = table[table["feature"] == most_val].iloc[0]
least_row = table[table["feature"] == least_val].iloc[0]

theme.hero_insight(
    eyebrow="KEY BEHAVIOR",
    headline=f"{most_val} is the highest-value action",
    body=(
        f"Retention correlation: <b>{most_row['retention_correlation']:.2f}</b> · "
        f"Revenue correlation: <b>{most_row['revenue_correlation']:.2f}</b> · "
        f"Adoption: <b>{most_row['adoption_rate_pct']:.0f}%</b>. "
        f"Moving users to this action earlier in their journey is the highest-leverage growth investment."
    ),
    bg=theme.SUCCESS_SOFT,
)

# ── Adoption KPI strip ────────────────────────────────────────────────────────
theme.kpi_group_label("ADOPTION RATES", theme.PRIMARY)
strip = st.columns(len(table), gap="medium")
for col, (_, r) in zip(strip, table.iterrows()):
    is_best = r["feature"] == most_val
    ctx = "⭐ Highest value action" if is_best else f"Ret corr: {r['retention_correlation']:.2f}"
    ui.kpi_card(col, r["feature"], f"{r['adoption_rate_pct']:.0f}%",
                help_text=f"Avg usage frequency: {r['avg_usage_frequency']:.1f}",
                context=ctx)

# ── Value correlation ─────────────────────────────────────────────────────────
theme.section("Behavior-Value Connection", "Higher correlation = stronger link to retention and revenue")
c1, c2 = st.columns(2, gap="medium")
with c1:
    theme.chart_header("Adoption funnel across actions", "What percentage of users reach each behavior?")
    fig = px.bar(table, x="feature", y="adoption_rate_pct",
                 color="feature", color_discrete_sequence=theme.CATEGORICAL)
    fig.update_layout(showlegend=False)
    theme.plot(fig, 300, container=st)
with c2:
    theme.chart_header("Retention vs revenue correlation", "Which behaviors predict business outcomes?")
    fig = px.bar(table, x="feature", y=["retention_correlation", "revenue_correlation"],
                 barmode="group",
                 color_discrete_map={"retention_correlation": theme.SUCCESS,
                                     "revenue_correlation": theme.PRIMARY})
    theme.plot(fig, 300, container=st)

with st.expander("View feature metrics"):
    st.dataframe(
        table.rename(columns={
            "feature": "Feature", "adoption_rate_pct": "Adoption (%)",
            "avg_usage_frequency": "Avg Usage Freq",
            "retention_correlation": "Retention Corr",
            "revenue_correlation": "Revenue Corr",
        }),
        use_container_width=True, hide_index=True,
    )

# ── Business Impact ───────────────────────────────────────────────────────────
theme.section("Business Impact")
theme.finding_card(
    what=f"⭐ {most_val} — highest-value action for retention and revenue",
    why=f"Retention correlation {most_row['retention_correlation']:.2f}, revenue correlation {most_row['revenue_correlation']:.2f}",
    impact=f"Users who reach {most_val} retain and monetise significantly better",
    action="Drive new users to this action within their first session via onboarding and activation experiments",
)
theme.finding_card(
    what=f"🔻 {least_val} — lowest-value action",
    why=f"Retention correlation {least_row['retention_correlation']:.2f}, revenue correlation {least_row['revenue_correlation']:.2f}",
    impact="Over-optimising this action in isolation yields diminishing returns",
    action="Deprioritise isolated optimisation — focus resources on higher-value actions instead",
)

theme.section("Recommendations")
for r in fa.feature_recommendations(ranking):
    ui.insight(r, "info")
