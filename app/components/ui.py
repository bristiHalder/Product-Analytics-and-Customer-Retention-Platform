"""Shared Streamlit helpers: data loading, sidebar, filters, snapshot builder,
business-impact estimators and executive health assessment.

Visual/design primitives live in `theme.py`; this module wires them to data.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

# Ensure project root on path when launched via `streamlit run app/streamlit_app.py`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components import theme  # noqa: E402
from src.analytics import data_access as da  # noqa: E402
from src.analytics import funnel as funnel_mod  # noqa: E402
from src.analytics import metrics as metrics_mod  # noqa: E402
from src.analytics import segmentation as seg_mod  # noqa: E402

# Backward-compatible colour aliases (now sourced from the design system)
PRIMARY = theme.PRIMARY
ACCENT = theme.SUCCESS
SUCCESS = theme.SUCCESS
WARNING = theme.WARNING
DANGER = theme.DANGER
PLOT_TEMPLATE = theme.PLOT_TEMPLATE

# Re-export design components for convenience: ui.kpi_card / ui.section / ...
kpi_card = theme.kpi_card
section = theme.section
insight = theme.insight
page_title = theme.page_title
setup_page = theme.setup_page
style_fig = theme.style_fig
chart_header = theme.chart_header
hero_insight = theme.hero_insight
business_health_summary = theme.business_health_summary
decision_banner = theme.decision_banner
finding_card = theme.finding_card
answer_card = theme.answer_card
kpi_group_label = theme.kpi_group_label


@st.cache_data(show_spinner="Loading analytics tables …")
def load_data() -> dict[str, pd.DataFrame]:
    return da.load_tables()


def _sidebar_brand() -> None:
    st.sidebar.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;padding:2px 2px 14px 2px;
                    border-bottom:1px solid {theme.BORDER};margin-bottom:14px">
          <div style="width:32px;height:32px;border-radius:9px;
                      background:linear-gradient(135deg,{theme.PRIMARY},{theme.PURPLE});
                      display:flex;align-items:center;justify-content:center;font-size:16px">📊</div>
          <div>
            <div style="font-weight:700;font-size:0.92rem;color:{theme.TEXT};line-height:1.1">Growth Analytics</div>
            <div style="font-size:0.68rem;color:{theme.TEXT_MUTED}">Product Intelligence</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_filters(events: pd.DataFrame) -> da.Filters:
    _sidebar_brand()
    opts = da.filter_options(events)

    st.sidebar.markdown(
        f'<div style="font-size:0.72rem;font-weight:600;letter-spacing:0.06em;'
        f'text-transform:uppercase;color:{theme.TEXT_MUTED};margin:4px 0 6px">Filters</div>',
        unsafe_allow_html=True,
    )

    rng = st.sidebar.date_input(
        "Date range",
        value=(opts["min_date"], opts["max_date"]),
        min_value=opts["min_date"],
        max_value=opts["max_date"],
    )
    start, end = rng if isinstance(rng, (tuple, list)) and len(rng) == 2 else (opts["min_date"], opts["max_date"])

    categories = st.sidebar.multiselect("Category", opts["categories"], default=[],
                                        placeholder="All categories")
    brands = st.sidebar.multiselect("Brand", opts["brands"], default=[],
                                    placeholder="All brands")
    min_rev = st.sidebar.slider("Min user revenue ($)", 0, 2000, 0, step=50,
                                help="Only include users with at least this lifetime revenue")

    st.sidebar.markdown(
        f'<div style="margin-top:14px;padding-top:12px;border-top:1px solid {theme.BORDER};'
        f'font-size:0.7rem;color:{theme.TEXT_FAINT}">Data: '
        f'{opts["min_date"]:%b %d, %Y} → {opts["max_date"]:%b %d, %Y}</div>',
        unsafe_allow_html=True,
    )

    return da.Filters(
        start=start, end=end,
        categories=categories or None,
        brands=brands or None,
        min_revenue=float(min_rev),
    )


def filtered_frames(data: dict[str, pd.DataFrame], f: da.Filters) -> dict[str, pd.DataFrame]:
    events = da.apply_event_filters(data["fact_events"], f)
    user_ids = set(events["user_id"].unique())
    users = data["user_metrics"][data["user_metrics"]["user_id"].isin(user_ids)].copy()
    if f.min_revenue:
        users = users[users["customer_lifetime_value"] >= f.min_revenue]
    sessions = data["session_metrics"][data["session_metrics"]["user_id"].isin(user_ids)]
    return {"events": events, "users": users, "sessions": sessions,
            "products": data["product_metrics"], "daily": data["daily_activity"]}


def build_snapshot(frames: dict[str, pd.DataFrame]) -> dict:
    """Compact snapshot consumed by the AI copilot."""
    events, users = frames["events"], frames["users"]
    kpis = metrics_mod.compute_kpis(events, users).as_dict()
    fres = funnel_mod.compute_funnel(users)
    seg = seg_mod.segment_summary(seg_mod.assign_segments(users))
    return {
        "kpis": kpis,
        "funnel": {
            "largest_dropoff_stage": fres.largest_dropoff_stage,
            "largest_dropoff_pct": fres.largest_dropoff_pct,
            "overall_conversion": fres.overall_conversion,
            "stages": fres.table.to_dict(orient="records"),
        },
        "segments": seg.to_dict(orient="records"),
        "churn": {"rate": kpis["churn_rate"], "top_drivers": []},
    }


def page_header(title: str, subtitle: str = "") -> None:
    """Backward-compatible header; splits a leading emoji into the icon slot."""
    parts = title.split(" ", 1)
    icon, rest = (parts[0], parts[1]) if len(parts) == 2 and not parts[0].isalnum() else ("📊", title)
    theme.page_title(icon, rest, subtitle)


# ─────────────────────────────────────────────────────────────────────────────
# Business Impact Helpers
# ─────────────────────────────────────────────────────────────────────────────
def assess_business_health(kpis, funnel_result=None) -> dict[str, str]:
    """Return explainable Strong/Stable/Weak labels from KPIs.

    Rules:
        Growth:    MoM >= 5% → Strong | -5..5% → Stable | <-5% → Weak
        Retention: rate >= 50% → Strong | 30..50% → Stable | <30% → Weak
        Revenue:   ARPU growing or > median → Strong | flat → Stable | declining → Weak
                   (simplified: use growth_rate as proxy)
        Risk:      churn <25% → Low | 25-40% → Medium | >40% → High
    """
    gr = kpis.growth_rate if hasattr(kpis, "growth_rate") else kpis.get("growth_rate", 0)
    ret = kpis.retention_rate if hasattr(kpis, "retention_rate") else kpis.get("retention_rate", 0)
    churn = kpis.churn_rate if hasattr(kpis, "churn_rate") else kpis.get("churn_rate", 0)

    growth = "Strong" if gr >= 5 else ("Stable" if gr >= -5 else "Weak")
    retention = "Strong" if ret >= 50 else ("Stable" if ret >= 30 else "Weak")
    revenue = "Strong" if gr >= 3 else ("Stable" if gr >= -3 else "Weak")
    risk = "Low" if churn < 25 else ("Medium" if churn < 40 else "High")

    return {"growth": growth, "retention": retention, "revenue": revenue, "risk": risk}


def estimate_funnel_revenue_impact(users: pd.DataFrame, funnel_result,
                                    arpu: float) -> dict:
    """Estimate the $ opportunity from fixing the largest funnel leak."""
    total_users = int(users["reached_view"].sum()) if "reached_view" in users else len(users)
    dropoff_pct = funnel_result.largest_dropoff_pct
    # Users lost at this stage
    lost_users = int(total_users * dropoff_pct / 100)
    # If we recovered 10% of lost users
    recoverable = int(lost_users * 0.10)
    revenue_opportunity = recoverable * arpu
    return {
        "lost_users": lost_users,
        "recoverable_users": recoverable,
        "revenue_opportunity": revenue_opportunity,
        "stage": funnel_result.largest_dropoff_stage,
        "dropoff_pct": dropoff_pct,
    }


def estimate_churn_revenue_at_risk(users: pd.DataFrame) -> dict:
    """Revenue at risk from churned and at-risk users."""
    churned = users[users["is_churned"] == 1] if "is_churned" in users else pd.DataFrame()
    churned_count = len(churned)
    revenue_at_risk = float(churned["customer_lifetime_value"].sum()) if not churned.empty else 0.0
    avg_clv = float(churned["customer_lifetime_value"].mean()) if not churned.empty else 0.0
    return {
        "churned_users": churned_count,
        "revenue_at_risk": revenue_at_risk,
        "avg_churned_clv": avg_clv,
    }


def estimate_experiment_annual_impact(lift_pct: float, baseline_rate: float,
                                       total_users: int, arpu: float) -> float:
    """Projected annual revenue impact from an experiment lift."""
    incremental_conversions = total_users * abs(lift_pct / 100) * baseline_rate
    return incremental_conversions * arpu * 12  # annualised
