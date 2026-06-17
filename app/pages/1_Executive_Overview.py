"""Page 1 — Executive Overview.

Executive question: What should leadership focus on?
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

theme.setup_page("Executive Overview", "📈")

data = ui.load_data()
f = ui.sidebar_filters(data["fact_events"])
frames = ui.filtered_frames(data, f)
events, users = frames["events"], frames["users"]

ui.page_title("📈", "Executive Overview",
              "What should leadership focus on?")

if events.empty:
    theme.insight("No data matches the current filters. Widen the date range or clear filters.", "warning")
    st.stop()

kpis = m.compute_kpis(events, users)
trends = m.kpi_trends(events, kpis)
fres = fn.compute_funnel(users)


def t(key, field, default=None):
    return trends.get(key, {}).get(field, default)


# ── Executive Business Health Summary ─────────────────────────────────────────
health = ui.assess_business_health(kpis, fres)
impact = ui.estimate_funnel_revenue_impact(users, fres, kpis.arpu)
churn_impact = ui.estimate_churn_revenue_at_risk(users)

h_col, opp_col = st.columns([2, 3], gap="large")

with h_col:
    detail_parts = []
    if kpis.growth_rate >= 0:
        detail_parts.append(f"User base growing at {kpis.growth_rate:+.1f}% MoM.")
    else:
        detail_parts.append(f"User base contracting at {kpis.growth_rate:.1f}% MoM — acquisition needs attention.")
    if kpis.churn_rate >= 40:
        detail_parts.append(f"Churn at {kpis.churn_rate:.0f}% is critically high.")
    elif kpis.churn_rate >= 25:
        detail_parts.append(f"Churn at {kpis.churn_rate:.0f}% is elevated — monitor closely.")
    ui.business_health_summary(
        health["growth"], health["retention"], health["revenue"], health["risk"],
        details=" ".join(detail_parts),
    )

with opp_col:
    # Biggest Opportunity — with estimated business impact
    opp_kind = "danger" if kpis.churn_rate >= 40 else ("warning" if kpis.churn_rate >= 25 else "info")
    opp_bg = theme.DANGER_SOFT if opp_kind == "danger" else (theme.WARNING_SOFT if opp_kind == "warning" else theme.PRIMARY_SOFT)
    theme.hero_insight(
        eyebrow="BIGGEST OPPORTUNITY",
        headline=f"Fix {fres.largest_dropoff_stage} — {fres.largest_dropoff_pct:.0f}% drop-off",
        body=(
            f"An estimated <b>{impact['lost_users']:,} users</b> are lost at this stage. "
            f"Recovering just 10% would add <b>~${impact['revenue_opportunity']:,.0f}</b> in revenue. "
            f"Meanwhile, <b>{churn_impact['churned_users']:,} churned users</b> represent "
            f"<b>${churn_impact['revenue_at_risk']:,.0f}</b> in revenue at risk."
        ),
        bg=opp_bg,
    )

# ── KPI Group: Growth ─────────────────────────────────────────────────────────
theme.kpi_group_label("GROWTH", theme.PRIMARY)
r1 = st.columns(4, gap="medium")
ui.kpi_card(r1[0], "DAU", f"{kpis.dau:,}", t("dau", "delta"), t("dau", "spark"),
            "Daily Active Users", context="Latest day vs prior day")
ui.kpi_card(r1[1], "WAU", f"{kpis.wau:,}", t("wau", "delta"), t("wau", "spark"),
            "Weekly Active Users", context="Trailing 7d vs prior 7d")
ui.kpi_card(r1[2], "MAU", f"{kpis.mau:,}", t("mau", "delta"), t("mau", "spark"),
            "Monthly Active Users", context="Trailing 30d vs prior 30d")
ui.kpi_card(r1[3], "MoM Growth", f"{kpis.growth_rate:+.1f}%", None, t("growth_rate", "spark"),
            "Month-over-month active-user growth")

# ── KPI Group: Retention & Revenue ────────────────────────────────────────────
ret_col, rev_col = st.columns(2, gap="large")

with ret_col:
    theme.kpi_group_label("RETENTION", theme.SUCCESS)
    rc = st.columns(2, gap="medium")
    ui.kpi_card(rc[0], "Retention", f"{kpis.retention_rate:.1f}%", t("retention_rate", "delta"),
                t("retention_rate", "spark"), "30-day rolling retention", higher_is_better=True,
                delta_suffix="pt", context="Users active in both current & prior 30d window")
    ui.kpi_card(rc[1], "Churn", f"{kpis.churn_rate:.1f}%", t("churn_rate", "delta"),
                t("churn_rate", "spark"), "Users inactive 30+ days", higher_is_better=False,
                delta_suffix="pt", context=f"{churn_impact['churned_users']:,} users · ${churn_impact['revenue_at_risk']:,.0f} at risk")

with rev_col:
    theme.kpi_group_label("REVENUE", theme.WARNING)
    vc = st.columns(2, gap="medium")
    ui.kpi_card(vc[0], "Revenue", f"${kpis.total_revenue:,.0f}", t("revenue", "delta"),
                t("revenue", "spark"), "Total revenue in filtered period",
                context="Trailing 7d vs prior 7d")
    ui.kpi_card(vc[1], "ARPU", f"${kpis.arpu:,.2f}", t("arpu", "delta"), t("arpu", "spark"),
                "Average revenue per user",
                context=f"Across {kpis.n_users:,} users")

# ── Trend Charts — each answers a business question ─────────────────────────
theme.section("Trends")
c1, c2 = st.columns(2, gap="medium")

with c1:
    theme.chart_header("Are we growing daily engagement?", "Daily active users over time")
    dau = m.daily_active_trend(events)
    fig = go.Figure(go.Scatter(x=dau["date"], y=dau["dau"], mode="lines",
                               line=dict(color=theme.PRIMARY, width=2.5),
                               fill="tozeroy", fillcolor="rgba(37,99,235,0.08)",
                               name="DAU"))
    theme.plot(fig, 260, container=st)

    theme.chart_header("Is revenue trending up?", "Daily purchase revenue")
    rev = m.revenue_trend(events)
    fig = go.Figure(go.Scatter(x=rev["date"], y=rev["revenue"], mode="lines",
                               line=dict(color=theme.SUCCESS, width=2.5),
                               fill="tozeroy", fillcolor="rgba(16,185,129,0.08)",
                               name="Revenue"))
    theme.plot(fig, 260, container=st)

with c2:
    theme.chart_header("How is monthly acquisition tracking?", "Unique active users per month")
    growth = m.monthly_growth_trend(events)
    fig = go.Figure(go.Bar(x=growth["event_month"], y=growth["active_users"],
                           marker_color=theme.PRIMARY, name="Active users"))
    theme.plot(fig, 260, container=st)

    theme.chart_header("Are we keeping users or losing them?", "Weekly retention vs churn rate")
    ret = m.retention_trend(events)
    churn = m.churn_trend(events)
    merged = ret.merge(churn, on="week")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=merged["week"], y=merged["retention_pct"], mode="lines",
                             line=dict(color=theme.SUCCESS, width=2.5), name="Retention %"))
    fig.add_trace(go.Scatter(x=merged["week"], y=merged["churn_pct"], mode="lines",
                             line=dict(color=theme.DANGER, width=2.5, dash="dot"), name="Churn %"))
    theme.plot(fig, 260, container=st)

# ── Executive Summary ─────────────────────────────────────────────────────────
theme.section("Executive Summary")
growth_kind = "success" if kpis.growth_rate >= 0 else "danger"
ui.insight(
    f"<b>Growth:</b> {kpis.mau:,} MAU at <b>{kpis.growth_rate:+.1f}%</b> MoM. "
    f"{'User base is expanding — sustain acquisition.' if kpis.growth_rate >= 0 else 'User base is contracting — prioritise acquisition channels.'}",
    growth_kind,
)
ui.insight(
    f"<b>Retention vs Churn:</b> {kpis.retention_rate:.0f}% retained / {kpis.churn_rate:.0f}% churned — "
    f"{'healthy balance.' if kpis.churn_rate < 30 else 'churn is elevated. '}"
    f"{'Revenue at risk from churned users: <b>${churn_impact[\"revenue_at_risk\"]:,.0f}</b>.' if kpis.churn_rate >= 25 else ''}",
    "success" if kpis.churn_rate < 30 else "warning",
)
ui.insight(
    f"<b>Revenue:</b> ${kpis.total_revenue:,.0f} total at ${kpis.arpu:,.2f} ARPU across {kpis.n_users:,} users. "
    f"Funnel opportunity: fixing <b>{fres.largest_dropoff_stage}</b> could unlock ~${impact['revenue_opportunity']:,.0f}.",
    "info",
)
