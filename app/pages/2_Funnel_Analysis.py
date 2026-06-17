"""Page 2 — Funnel Analysis.

Executive question: Where are we losing revenue?
"""
from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components import theme, ui  # noqa: E402
from src.analytics import funnel as fn  # noqa: E402
from src.analytics import metrics as m  # noqa: E402

theme.setup_page("Funnel Analysis", "🔻")

data = ui.load_data()
f = ui.sidebar_filters(data["fact_events"])
frames = ui.filtered_frames(data, f)
users, events = frames["users"], frames["events"]

ui.page_title("🔻", "Funnel Analysis", "Where are we losing revenue?")

if users.empty:
    theme.insight("No data matches the current filters. Widen the date range or clear filters.", "warning")
    st.stop()

res = fn.compute_funnel(users)
kpis = m.compute_kpis(events, users) if not events.empty else None
arpu = kpis.arpu if kpis else 0
impact = ui.estimate_funnel_revenue_impact(users, res, arpu)

# ── Hero: Biggest leak with business impact ───────────────────────────────────
theme.hero_insight(
    eyebrow="LARGEST REVENUE LEAK",
    headline=f"{res.largest_dropoff_stage} — {res.largest_dropoff_pct:.0f}% drop-off",
    body=(
        f"<b>{impact['lost_users']:,} users</b> are lost at this stage. "
        f"Recovering 10% would add an estimated <b>~${impact['revenue_opportunity']:,.0f}</b> in revenue. "
        f"Overall view→purchase conversion: <b>{res.overall_conversion:.1f}%</b>."
    ),
    bg=theme.DANGER_SOFT,
)

# ── Headline metrics ──────────────────────────────────────────────────────────
m1, m2, m3 = st.columns(3, gap="medium")
ui.kpi_card(m1, "Overall Conversion", f"{res.overall_conversion:.1f}%",
            help_text="Share of viewers who reach Purchase",
            context="View → Purchase path")
ui.kpi_card(m2, "Largest Drop-off", f"{res.largest_dropoff_pct:.1f}%",
            help_text="Biggest single-stage leak", higher_is_better=False,
            context=res.largest_dropoff_stage)
ui.kpi_card(m3, "Revenue Opportunity", f"~${impact['revenue_opportunity']:,.0f}",
            help_text="Estimated revenue from recovering 10% of lost users",
            context=f"{impact['recoverable_users']:,} recoverable users")

# ── Funnel + breakdown side by side ───────────────────────────────────────────
theme.section("Conversion Funnel", "View → Add to Cart → Purchase → Repeat Purchase")
left, right = st.columns([3, 2], gap="medium")

with left:
    fig = go.Figure(go.Funnel(
        y=res.table["stage"],
        x=res.table["users"],
        textinfo="value+percent initial",
        marker={"color": [theme.PRIMARY, theme.PURPLE, theme.SUCCESS, theme.CYAN]},
        connector={"line": {"color": theme.BORDER}},
    ))
    theme.plot(fig, 400, container=st)

with right:
    theme.chart_header("Stage breakdown", "Users, conversion, and drop-off at each step")
    st.dataframe(
        res.table.rename(columns={
            "stage": "Stage", "users": "Users",
            "conversion_from_prev_pct": "From prev (%)",
            "conversion_from_top_pct": "From top (%)",
            "dropoff_pct": "Drop-off (%)",
        }),
        use_container_width=True, hide_index=True, height=340,
    )

# ── Impact Analysis ───────────────────────────────────────────────────────────
theme.section("Business Impact Analysis")

# Per-stage impact estimation
for _, row in res.table.iloc[1:].iterrows():
    if row["dropoff_pct"] > 5:
        stage_lost = int(res.table.iloc[0]["users"] * row["dropoff_pct"] / 100)
        stage_rev = int(stage_lost * 0.10 * arpu)
        severity = "danger" if row["dropoff_pct"] > 40 else ("warning" if row["dropoff_pct"] > 20 else "info")
        prev_idx = res.table[res.table["stage"] == row["stage"]].index[0]
        prev_stage = res.table.iloc[prev_idx - 1]["stage"] if prev_idx > 0 else "Entry"
        theme.finding_card(
            what=f"{prev_stage} → {row['stage']}: {row['dropoff_pct']:.1f}% drop-off",
            why=f"{stage_lost:,} users lost at this transition",
            impact=f"~${stage_rev:,.0f} recoverable revenue (10% recovery rate)",
            action="Prioritise UX improvements and targeted re-engagement at this stage",
        )

# ── Recommendations ───────────────────────────────────────────────────────────
theme.section("Recommended Actions")
for r in fn.funnel_recommendations(res):
    ui.insight(r, "info")
