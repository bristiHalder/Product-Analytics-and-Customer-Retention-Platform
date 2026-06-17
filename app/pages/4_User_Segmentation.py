"""Page 4 — User Segmentation.

Executive question: Which customers drive business value?
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
from src.analytics import segmentation as sg  # noqa: E402

theme.setup_page("User Segmentation", "👥")

data = ui.load_data()
f = ui.sidebar_filters(data["fact_events"])
frames = ui.filtered_frames(data, f)
users = frames["users"]

ui.page_title("👥", "User Segmentation", "Which customers drive business value?")

if users.empty:
    theme.insight("No data matches the current filters. Widen the date range or clear filters.", "warning")
    st.stop()

seg_users = sg.assign_segments(users)
summary = sg.segment_summary(seg_users)

# ── Executive insight (answer in 5 seconds) ───────────────────────────────────
top = summary.iloc[0]
total_rev = float(summary["total_revenue"].sum())

at_risk = summary[summary["segment"] == "At-Risk Customer"]
at_risk_rev = float(at_risk["total_revenue"].iloc[0]) if not at_risk.empty else 0
at_risk_users = int(at_risk["users"].iloc[0]) if not at_risk.empty else 0
at_risk_churn = float(at_risk["churn_rate"].iloc[0]) if not at_risk.empty else 0

theme.hero_insight(
    eyebrow="REVENUE CONCENTRATION",
    headline=f"{top['segment']} drives {top['revenue_share_pct']:.0f}% of revenue (${float(top['total_revenue']):,.0f})",
    body=(
        f"From just <b>{int(top['users']):,} users</b> at <b>${top['avg_clv']:,.0f} avg CLV</b>. "
        + (f"Meanwhile, <b>{at_risk_users:,} at-risk customers</b> represent "
           f"<b>${at_risk_rev:,.0f}</b> in threatened revenue (churn rate: {at_risk_churn:.0f}%)."
           if at_risk_rev > 0 else "No significant at-risk segment detected.")
    ),
    bg=theme.SUCCESS_SOFT,
)

# ── Premium segment cards ─────────────────────────────────────────────────────
theme.section("Segments at a Glance")
SEGMENT_ICONS = {
    "High Value Customer": "👑",
    "Power Buyer": "⚡",
    "Casual Buyer": "🛍️",
    "At-Risk Customer": "🚨",
    "Window Shopper": "👀",
}
SEGMENT_ACCENTS = {
    "High Value Customer": theme.WARNING,   # gold
    "Power Buyer": theme.PRIMARY,           # blue
    "Casual Buyer": theme.CYAN,             # cyan
    "At-Risk Customer": theme.DANGER,       # red
    "Window Shopper": theme.TEXT_FAINT,      # gray
}

strip = st.columns(min(len(summary), 5), gap="medium")
for col, (_, r) in zip(strip, summary.head(5).iterrows()):
    seg_name = r["segment"]
    icon = SEGMENT_ICONS.get(seg_name, "👤")
    accent = SEGMENT_ACCENTS.get(seg_name, theme.PRIMARY)
    col.markdown(
        f"""
        <div class="segment-card" style="border-top: 3px solid {accent}">
            <div class="segment-name">{icon} {seg_name}</div>
            <div class="segment-stat">
                <span class="segment-stat-label">Users</span>
                <span class="segment-stat-value">{int(r['users']):,}</span>
            </div>
            <div class="segment-stat">
                <span class="segment-stat-label">Revenue</span>
                <span class="segment-stat-value">${float(r['total_revenue']):,.0f}</span>
            </div>
            <div class="segment-stat">
                <span class="segment-stat-label">Rev Share</span>
                <span class="segment-stat-value">{r['revenue_share_pct']:.0f}%</span>
            </div>
            <div class="segment-stat">
                <span class="segment-stat-label">Avg CLV</span>
                <span class="segment-stat-value">${r['avg_clv']:,.0f}</span>
            </div>
            <div class="segment-stat">
                <span class="segment-stat-label">Churn</span>
                <span class="segment-stat-value">{r['churn_rate']:.0f}%</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Distribution charts ───────────────────────────────────────────────────────
theme.section("Revenue Distribution")
c1, c2 = st.columns(2, gap="medium")
with c1:
    theme.chart_header("How are users distributed across segments?", "User count by segment")
    fig = px.pie(summary, names="segment", values="users", hole=0.55,
                 color_discrete_sequence=theme.CATEGORICAL)
    fig.update_traces(textposition="outside", textinfo="label+percent")
    theme.plot(fig, 300, container=st)
with c2:
    theme.chart_header("Which segments contribute the most revenue?", "Revenue share by segment")
    s = summary.sort_values("revenue_share_pct")
    fig = px.bar(s, x="revenue_share_pct", y="segment", orientation="h",
                 color="revenue_share_pct", color_continuous_scale="Blues")
    fig.update_layout(coloraxis_showscale=False)
    theme.plot(fig, 300, container=st)

# ── Preferences ───────────────────────────────────────────────────────────────
theme.section("Revenue by Preference")
c3, c4 = st.columns(2, gap="medium")
with c3:
    theme.chart_header("Top categories by revenue", "Product category revenue contribution")
    cat = sg.preference_breakdown(seg_users, "preferred_category").head(8)
    fig = px.bar(cat, x="revenue", y="preferred_category", orientation="h",
                 color_discrete_sequence=[theme.PRIMARY])
    fig.update_layout(yaxis=dict(autorange="reversed"))
    theme.plot(fig, 280, container=st)
with c4:
    theme.chart_header("Top brands by revenue", "Brand revenue contribution")
    brand = sg.preference_breakdown(seg_users, "preferred_brand").head(8)
    fig = px.bar(brand, x="revenue", y="preferred_brand", orientation="h",
                 color_discrete_sequence=[theme.SUCCESS])
    fig.update_layout(yaxis=dict(autorange="reversed"))
    theme.plot(fig, 280, container=st)

# ── Detail table ──────────────────────────────────────────────────────────────
with st.expander("View full segment metrics"):
    st.dataframe(
        summary.rename(columns={
            "segment": "Segment", "users": "Users", "avg_clv": "Avg CLV ($)",
            "total_revenue": "Revenue ($)", "avg_orders": "Avg Orders",
            "avg_sessions": "Avg Sessions", "churn_rate": "Churn (%)",
            "revenue_share_pct": "Revenue Share (%)",
        }).style.format({
            "Avg CLV ($)": "{:,.0f}", "Revenue ($)": "{:,.0f}",
            "Avg Orders": "{:.1f}", "Avg Sessions": "{:.1f}",
            "Churn (%)": "{:.1f}", "Revenue Share (%)": "{:.1f}",
        }),
        use_container_width=True, hide_index=True,
    )

# ── Business Impact Insights ─────────────────────────────────────────────────
theme.section("Business Impact")
theme.finding_card(
    what=f"{top['segment']} is the most valuable segment — protect and expand",
    why=f"Drives {top['revenue_share_pct']:.0f}% of revenue from {int(top['users']):,} users at ${top['avg_clv']:,.0f} CLV",
    impact=f"Losing 10% of this segment = ~${float(top['total_revenue']) * 0.1:,.0f} revenue at risk",
    action="Defend with loyalty programs, concierge support, and lookalike acquisition",
)
if not at_risk.empty:
    theme.finding_card(
        what=f"{at_risk_users:,} at-risk customers need immediate attention",
        why=f"High-value users with {at_risk_churn:.0f}% churn rate — previously valuable but now inactive",
        impact=f"${at_risk_rev:,.0f} in revenue at risk from this segment",
        action="Launch win-back campaigns: personalised offers, re-engagement emails, exit surveys",
    )
