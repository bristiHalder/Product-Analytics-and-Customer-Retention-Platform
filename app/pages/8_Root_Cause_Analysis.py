"""Page 8 — Root Cause Analysis.

Executive question: Why did the metric move?
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
from src.analytics import metrics as m  # noqa: E402
from src.analytics import root_cause as rc  # noqa: E402

theme.setup_page("Root Cause Analysis", "🔍")

data = ui.load_data()
f = ui.sidebar_filters(data["fact_events"])
frames = ui.filtered_frames(data, f)
events, users = frames["events"], frames["users"]

ui.page_title("🔍", "Root Cause Analysis", "Why did the metric move?")

if events.empty:
    theme.insight("No data matches the current filters. Widen the date range or clear filters.", "warning")
    st.stop()

rev = m.revenue_trend(events)
ret = m.retention_trend(events)

with st.expander("⚙️ Detection Settings"):
    threshold = st.slider("Drop sensitivity threshold (%)", -50, -5, -15,
                          help="Flag periods where a metric falls by at least this much vs the prior period")

rev_drops = rc.detect_drops(rev.set_index("date")["revenue"].rename("revenue"), threshold)
ret_drops = rc.detect_drops(ret.set_index("week")["retention_pct"].rename("retention"), threshold)

# ── Executive insight (answer in 5 seconds) ───────────────────────────────────
total_anomalies = len(rev_drops) + len(ret_drops)
if total_anomalies == 0:
    theme.hero_insight(
        eyebrow="STATUS",
        headline="No significant metric drops detected",
        body=f"Revenue and retention are within normal ranges at the {abs(threshold)}% sensitivity threshold.",
        bg=theme.SUCCESS_SOFT,
    )
else:
    worst_drop = min(
        [(a.change_pct, "Revenue", a.period) for a in rev_drops] +
        [(a.change_pct, "Retention", a.period) for a in ret_drops],
        key=lambda x: x[0],
        default=(0, "", ""),
    )
    theme.hero_insight(
        eyebrow=f"{total_anomalies} ANOMAL{'Y' if total_anomalies == 1 else 'IES'} DETECTED",
        headline=f"Largest drop: {worst_drop[1]} fell {abs(worst_drop[0]):.0f}% on {worst_drop[2]}",
        body=(
            f"<b>{len(rev_drops)}</b> revenue drop events and <b>{len(ret_drops)}</b> retention drop events "
            f"exceeded the {abs(threshold)}% threshold. See ranked causes below."
        ),
        bg=theme.DANGER_SOFT,
    )

# ── Anomaly KPIs ─────────────────────────────────────────────────────────────
k1, k2 = st.columns(2, gap="medium")
ui.kpi_card(k1, "Revenue Drop Events", f"{len(rev_drops)}",
            help_text="Periods exceeding the drop threshold",
            higher_is_better=False, context=f"Threshold: {threshold}%")
ui.kpi_card(k2, "Retention Drop Events", f"{len(ret_drops)}",
            help_text="Weeks exceeding the drop threshold",
            higher_is_better=False, context=f"Threshold: {threshold}%")

# ── Revenue trend with annotations ───────────────────────────────────────────
theme.chart_header("Revenue trend with detected drops", "Red markers indicate periods exceeding the drop threshold")
fig = px.line(rev, x="date", y="revenue", color_discrete_sequence=[theme.SUCCESS])
fig.update_traces(line=dict(width=2.5))
for a in rev_drops:
    fig.add_annotation(
        x=a.period, y=0, yref="paper", yshift=10,
        text=f"{a.change_pct:.0f}%", showarrow=True, arrowhead=2,
        arrowcolor=theme.DANGER, font=dict(color=theme.DANGER, size=11),
        ax=0, ay=-30,
    )
theme.plot(fig, 300, container=st)

# ── Ranked causes as executive finding cards ──────────────────────────────────
theme.section("Probable Causes", "Ranked by estimated impact")
drivers = rc.correlation_drivers(users, "is_churned")
seg = rc.segment_impact(events, "category")
causes = rc.rank_probable_causes(rev, drivers, seg, top_n=5)

if not causes:
    theme.insight("No significant causes detected for the current selection.", "info")
else:
    for c in causes:
        # Translate technical cause into executive format
        theme.finding_card(
            what=f"#{c['rank']} — {c['cause']}",
            why=c["evidence"],
            impact=f"Impact score: {c['impact']:.1f} — {'High' if c['impact'] > 50 else 'Medium' if c['impact'] > 20 else 'Low'} severity",
            action="Investigate this signal and implement targeted remediation",
        )

# ── Technical detail in expanders ─────────────────────────────────────────────
with st.expander("Churn correlation detail"):
    st.dataframe(drivers.head(10), use_container_width=True, hide_index=True)

if "change_pct" in seg.columns:
    with st.expander("Segment revenue change (MoM)"):
        st.dataframe(seg.sort_values("change_pct"), use_container_width=True, hide_index=True)
