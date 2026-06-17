"""Light SaaS design system for the analytics platform.

Single source of truth for colours, typography, the Plotly chart theme, global
CSS and reusable components (KPI cards, business health summary, hero insights,
decision banners, finding cards, structured AI answers). Inspired by Amplitude,
Mixpanel, Stripe Dashboard, Notion and Airtable Analytics.
"""
from __future__ import annotations

import math
from typing import Optional, Sequence

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Design tokens — clean light theme
# ─────────────────────────────────────────────────────────────────────────────
BG = "#F8FAFC"            # app background (slate-50)
BG_ELEVATED = "#FFFFFF"   # sidebar / elevated panels
CARD = "#FFFFFF"          # card surface
CARD_HOVER = "#FFFFFF"
BORDER = "#E2E8F0"        # slate-200 (subtle)
GRID = "rgba(148,163,184,0.18)"

TEXT = "#0F172A"          # slate-900
TEXT_MUTED = "#64748B"    # slate-500
TEXT_FAINT = "#94A3B8"    # slate-400

PRIMARY = "#2563EB"       # blue-600
SUCCESS = "#10B981"       # emerald-500
WARNING = "#F59E0B"       # amber-500
DANGER = "#EF4444"        # red-500
PURPLE = "#8B5CF6"        # violet-500
CYAN = "#06B6D4"          # cyan-500

# Soft tints for light surfaces
PRIMARY_SOFT = "rgba(37,99,235,0.08)"
SUCCESS_SOFT = "rgba(16,185,129,0.10)"
WARNING_SOFT = "rgba(245,158,11,0.12)"
DANGER_SOFT = "rgba(239,68,68,0.10)"
PURPLE_SOFT = "rgba(139,92,246,0.08)"

# Categorical palette for charts (modern, friendly)
CATEGORICAL = [PRIMARY, SUCCESS, WARNING, PURPLE, CYAN, DANGER, "#0EA5E9", "#F472B6"]
SEQUENTIAL_BLUE = [[0, "#EFF6FF"], [0.5, "#60A5FA"], [1, "#1D4ED8"]]

PLOT_TEMPLATE = "saas_light"
PLOTLY_CONFIG = {"displayModeBar": False, "displaylogo": False, "responsive": True}


# ─────────────────────────────────────────────────────────────────────────────
# Plotly theme — clean, minimal gridlines, readable fonts
# ─────────────────────────────────────────────────────────────────────────────
def _register_plotly_template() -> None:
    pio.templates["saas_light"] = go.layout.Template(
        layout=go.Layout(
            font=dict(family="Inter, -apple-system, Segoe UI, sans-serif",
                      color=TEXT, size=14),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            colorway=CATEGORICAL,
            margin=dict(l=10, r=14, t=36, b=10),
            hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=BORDER,
                            font=dict(color=TEXT, size=13)),
            xaxis=dict(gridcolor="rgba(0,0,0,0)", zerolinecolor=GRID,
                       linecolor=BORDER, tickcolor=BORDER,
                       tickfont=dict(size=13, color=TEXT_MUTED),
                       title=dict(font=dict(size=13, color=TEXT_MUTED)),
                       automargin=True),
            yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor="rgba(0,0,0,0)",
                       tickcolor="rgba(0,0,0,0)",
                       tickfont=dict(size=13, color=TEXT_MUTED),
                       title=dict(font=dict(size=13, color=TEXT_MUTED)),
                       automargin=True),
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)",
                        font=dict(color=TEXT_MUTED, size=13),
                        orientation="h", yanchor="bottom", y=1.02, x=0),
            title=dict(font=dict(size=15, color=TEXT)),
            colorscale=dict(sequential=SEQUENTIAL_BLUE),
        )
    )
    pio.templates.default = "saas_light"


def style_fig(fig: go.Figure, height: int = 300, title: str = "") -> go.Figure:
    """Apply consistent sizing/title/theme to a figure built elsewhere."""
    fig.update_layout(template=PLOT_TEMPLATE, height=height,
                      title=dict(text=title or ""),
                      showlegend=fig.layout.showlegend)
    return fig


def plot(fig: go.Figure, height: int = 300, title: str = "", container=None) -> None:
    """Style and render a chart with the clean toolbar-free config."""
    target = container if container is not None else st
    target.plotly_chart(style_fig(fig, height, title),
                        use_container_width=True, config=PLOTLY_CONFIG)


# ─────────────────────────────────────────────────────────────────────────────
# Global CSS — subtle shadows, whitespace, narrow sidebar, clear hierarchy
# ─────────────────────────────────────────────────────────────────────────────
def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
        .stApp {{ background: {BG}; }}
        .block-container {{ padding-top: 2.6rem; padding-bottom: 4rem; max-width: 1400px; }}

        /* Typographic hierarchy */
        h1, h2, h3, h4 {{ color: {TEXT}; letter-spacing: -0.015em; font-weight: 700; }}
        h1 {{ font-size: 1.65rem; }}
        h2 {{ font-size: 1.3rem; }}
        h3 {{ font-size: 1.05rem; }}
        p, span, label, li {{ color: {TEXT}; }}

        /* Narrow sidebar — content is the hero */
        section[data-testid="stSidebar"] {{
            background: {BG_ELEVATED};
            border-right: 1px solid {BORDER};
            width: 220px !important; min-width: 220px !important;
        }}
        section[data-testid="stSidebar"] > div {{ width: 220px !important; }}
        section[data-testid="stSidebar"] .block-container {{ padding-top: 1.4rem; }}
        section[data-testid="stSidebar"] * {{ font-size: 0.84rem; }}

        /* KPI card surface */
        .kpi-card {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 18px 20px;
            height: 100%;
            box-shadow: 0 1px 3px rgba(15,23,42,0.05), 0 1px 2px rgba(15,23,42,0.03);
            transition: box-shadow .18s ease, transform .18s ease;
        }}
        .kpi-card:hover {{
            box-shadow: 0 4px 12px rgba(15,23,42,0.08), 0 2px 4px rgba(15,23,42,0.04);
            transform: translateY(-1px);
        }}
        .kpi-label {{
            color: {TEXT_MUTED}; font-size: 0.72rem; font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.05em;
            display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
        }}
        .kpi-value {{ color: {TEXT}; font-size: 1.85rem; font-weight: 800; line-height: 1.05; }}
        .kpi-caption {{ color: {TEXT_FAINT}; font-size: 0.76rem; margin-top: 3px; }}
        .kpi-context {{ color: {TEXT_FAINT}; font-size: 0.72rem; margin-top: 4px; line-height: 1.35; }}
        .kpi-bottom {{ display: flex; align-items: center; justify-content: space-between; margin-top: 12px; }}
        .kpi-delta {{ font-size: 0.8rem; font-weight: 700; display: inline-flex; align-items: center; gap: 3px;
                      padding: 2px 8px; border-radius: 999px; }}
        .kpi-delta.up {{ color: {SUCCESS}; background: {SUCCESS_SOFT}; }}
        .kpi-delta.down {{ color: {DANGER}; background: {DANGER_SOFT}; }}
        .kpi-delta.flat {{ color: {TEXT_FAINT}; background: rgba(148,163,184,0.12); }}
        .kpi-help {{ color: {TEXT_FAINT}; font-size: 0.72rem; cursor: help; }}

        /* Section header */
        .section-head {{ margin: 2.2rem 0 0.7rem 0; }}
        .section-head .title {{ font-size: 1.1rem; font-weight: 700; color: {TEXT}; }}
        .section-head .sub {{ font-size: 0.84rem; color: {TEXT_MUTED}; margin-top: 3px; }}

        /* Chart caption (business meaning) */
        .chart-q {{ font-size: 0.95rem; font-weight: 600; color: {TEXT}; margin: 2px 0 0; }}
        .chart-sub {{ font-size: 0.8rem; color: {TEXT_MUTED}; margin: 1px 0 10px; }}

        /* Insight callout */
        .insight {{
            background: {CARD}; border: 1px solid {BORDER};
            border-left: 4px solid {PRIMARY};
            border-radius: 12px; padding: 14px 18px; margin: 8px 0;
            color: {TEXT}; font-size: 0.92rem; line-height: 1.55;
            box-shadow: 0 1px 2px rgba(15,23,42,0.04);
        }}
        .insight.success {{ border-left-color: {SUCCESS}; background: {SUCCESS_SOFT}; }}
        .insight.warning {{ border-left-color: {WARNING}; background: {WARNING_SOFT}; }}
        .insight.danger  {{ border-left-color: {DANGER}; background: {DANGER_SOFT}; }}
        .insight b {{ color: {TEXT}; }}

        /* Hero / big insight banner */
        .hero {{
            border-radius: 16px; padding: 22px 26px; margin: 4px 0 12px;
            box-shadow: 0 2px 8px rgba(15,23,42,0.06);
            border: 1px solid {BORDER};
        }}
        .hero .eyebrow {{ font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
                          letter-spacing: 0.07em; opacity: 0.9; }}
        .hero .headline {{ font-size: 1.25rem; font-weight: 800; line-height: 1.3; margin-top: 6px; }}
        .hero .body {{ font-size: 0.92rem; line-height: 1.55; margin-top: 6px; }}

        /* Business Health Summary */
        .health-summary {{
            background: {CARD}; border: 1px solid {BORDER}; border-radius: 16px;
            padding: 22px 26px; margin: 4px 0 12px;
            box-shadow: 0 2px 8px rgba(15,23,42,0.05);
        }}
        .health-row {{
            display: flex; align-items: center; justify-content: space-between;
            padding: 10px 0; border-bottom: 1px solid {BORDER};
        }}
        .health-row:last-child {{ border-bottom: none; }}
        .health-dim {{ font-size: 0.88rem; font-weight: 600; color: {TEXT}; }}
        .health-badge {{
            font-size: 0.76rem; font-weight: 700; padding: 3px 12px;
            border-radius: 999px; text-transform: uppercase; letter-spacing: 0.04em;
        }}
        .health-badge.strong {{ background: {SUCCESS_SOFT}; color: {SUCCESS}; }}
        .health-badge.stable {{ background: {PRIMARY_SOFT}; color: {PRIMARY}; }}
        .health-badge.weak {{ background: {DANGER_SOFT}; color: {DANGER}; }}
        .health-badge.low {{ background: {SUCCESS_SOFT}; color: {SUCCESS}; }}
        .health-badge.medium {{ background: {WARNING_SOFT}; color: #B45309; }}
        .health-badge.high {{ background: {DANGER_SOFT}; color: {DANGER}; }}

        /* Decision banner */
        .decision-banner {{
            border-radius: 16px; padding: 24px 28px; margin: 4px 0 16px;
            border: 1px solid {BORDER};
            box-shadow: 0 2px 10px rgba(15,23,42,0.06);
        }}
        .decision-banner.ship {{ background: {SUCCESS_SOFT}; border-left: 5px solid {SUCCESS}; }}
        .decision-banner.no-ship {{ background: {DANGER_SOFT}; border-left: 5px solid {DANGER}; }}
        .decision-banner.wait {{ background: {WARNING_SOFT}; border-left: 5px solid {WARNING}; }}
        .decision-label {{ font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
                           letter-spacing: 0.06em; margin-bottom: 6px; }}
        .decision-headline {{ font-size: 1.35rem; font-weight: 800; line-height: 1.2; }}
        .decision-detail {{ font-size: 0.9rem; color: {TEXT_MUTED}; margin-top: 8px; line-height: 1.5; }}

        /* Finding card (root cause / recommendations) */
        .finding-card {{
            background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px;
            padding: 18px 22px; margin: 8px 0;
            box-shadow: 0 1px 3px rgba(15,23,42,0.04);
        }}
        .finding-card .finding-what {{
            font-size: 0.96rem; font-weight: 700; color: {TEXT}; margin-bottom: 8px;
        }}
        .finding-row {{
            display: flex; gap: 6px; margin: 4px 0;
        }}
        .finding-label {{
            font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.05em; color: {TEXT_MUTED}; min-width: 90px; padding-top: 1px;
        }}
        .finding-value {{
            font-size: 0.88rem; color: {TEXT}; line-height: 1.45; flex: 1;
        }}

        /* KPI group header */
        .kpi-group-label {{
            font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.06em; color: {TEXT_MUTED}; margin: 0 0 8px 2px;
            display: flex; align-items: center; gap: 6px;
        }}
        .kpi-group-label .dot {{
            width: 8px; height: 8px; border-radius: 50%; display: inline-block;
        }}

        /* Pill / badge */
        .pill {{ display:inline-block; padding: 3px 11px; border-radius: 999px;
                 font-size: 0.74rem; font-weight: 600; }}
        .pill.blue {{ background: {PRIMARY_SOFT}; color: {PRIMARY}; }}
        .pill.green {{ background: {SUCCESS_SOFT}; color: {SUCCESS}; }}
        .pill.amber {{ background: {WARNING_SOFT}; color: #B45309; }}
        .pill.red {{ background: {DANGER_SOFT}; color: {DANGER}; }}
        .pill.gray {{ background: rgba(148,163,184,0.16); color: {TEXT_MUTED}; }}
        .pill.purple {{ background: {PURPLE_SOFT}; color: {PURPLE}; }}

        /* Structured answer card (AI copilot) */
        .answer-card {{
            background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px;
            padding: 20px 24px; margin: 10px 0;
            box-shadow: 0 1px 4px rgba(15,23,42,0.05);
        }}
        .answer-section {{ margin: 10px 0; }}
        .answer-section:first-child {{ margin-top: 0; }}
        .answer-section-label {{
            font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.06em; margin-bottom: 4px; padding: 2px 10px;
            border-radius: 6px; display: inline-block;
        }}
        .answer-section-label.obs {{ color: {PRIMARY}; background: {PRIMARY_SOFT}; }}
        .answer-section-label.evi {{ color: {PURPLE}; background: {PURPLE_SOFT}; }}
        .answer-section-label.rec {{ color: {SUCCESS}; background: {SUCCESS_SOFT}; }}
        .answer-section-label.imp {{ color: #B45309; background: {WARNING_SOFT}; }}
        .answer-section-text {{
            font-size: 0.9rem; color: {TEXT}; line-height: 1.55; margin-top: 4px;
            padding-left: 2px;
        }}

        /* Prompt pill buttons */
        .prompt-pills {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 16px; }}

        /* Segment card (premium) */
        .segment-card {{
            background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px;
            padding: 18px 20px; height: 100%;
            box-shadow: 0 1px 3px rgba(15,23,42,0.05);
            transition: box-shadow .18s ease;
        }}
        .segment-card:hover {{
            box-shadow: 0 4px 12px rgba(15,23,42,0.08);
        }}
        .segment-name {{ font-weight: 700; font-size: 0.95rem; color: {TEXT}; margin-bottom: 10px;
                          display: flex; align-items: center; gap: 6px; }}
        .segment-stat {{ display: flex; justify-content: space-between; padding: 4px 0;
                          font-size: 0.82rem; }}
        .segment-stat-label {{ color: {TEXT_MUTED}; }}
        .segment-stat-value {{ font-weight: 600; color: {TEXT}; }}

        /* Streamlit metric fallback */
        [data-testid="stMetric"] {{
            background: {CARD}; border: 1px solid {BORDER};
            border-radius: 14px; padding: 16px 18px;
            box-shadow: 0 1px 3px rgba(15,23,42,0.05);
        }}
        [data-testid="stMetricValue"] {{ font-size: 1.7rem; color: {TEXT}; }}

        /* Dataframe polish */
        [data-testid="stDataFrame"] {{ border: 1px solid {BORDER}; border-radius: 12px; }}

        /* Buttons */
        .stButton > button {{
            border-radius: 10px; border: 1px solid {BORDER}; background: {CARD};
            color: {TEXT}; font-weight: 500; font-size: 0.86rem;
            box-shadow: 0 1px 2px rgba(15,23,42,0.04); transition: all .15s ease;
        }}
        .stButton > button:hover {{
            border-color: {PRIMARY}; color: {PRIMARY};
            box-shadow: 0 2px 6px rgba(37,99,235,0.12);
        }}

        /* Chat-style bubbles for AI copilot */
        .chat-row {{ display: flex; gap: 12px; margin: 10px 0; align-items: flex-start; }}
        .chat-av {{ width: 32px; height: 32px; border-radius: 9px; flex: 0 0 32px;
                    display: flex; align-items: center; justify-content: center; font-size: 16px; }}
        .chat-av.user {{ background: {PRIMARY_SOFT}; }}
        .chat-av.ai {{ background: linear-gradient(135deg,{PRIMARY},{PURPLE}); color: #fff; }}
        .chat-msg {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;
                     padding: 12px 16px; font-size: 0.92rem; line-height: 1.55; flex: 1;
                     box-shadow: 0 1px 2px rgba(15,23,42,0.04); }}
        .chat-msg.user {{ background: {PRIMARY_SOFT}; border-color: rgba(37,99,235,0.18); }}

        /* Tabs */
        button[data-baseweb="tab"] {{ font-weight: 600; color: {TEXT_MUTED}; }}
        button[data-baseweb="tab"][aria-selected="true"] {{ color: {PRIMARY}; }}

        /* Hide default Streamlit chrome noise */
        #MainMenu, footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sparkline (inline SVG)
# ─────────────────────────────────────────────────────────────────────────────
def sparkline_svg(values: Sequence[float], color: str = PRIMARY,
                  width: int = 140, height: int = 40) -> str:
    vals = [float(v) for v in values if v is not None]
    if len(vals) < 2:
        return ""
    mn, mx = min(vals), max(vals)
    rng = (mx - mn) or 1.0
    n = len(vals)
    pts = [(i / (n - 1) * width, height - 4 - ((v - mn) / rng) * (height - 8))
           for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"0,{height} " + line + f" {width},{height}"
    cid = f"g{abs(hash((tuple(vals), color))) % 100000}"
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="none" style="display:block">'
        f'<defs><linearGradient id="{cid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.28"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
        f'<polygon points="{area}" fill="url(#{cid})"/>'
        f'<polyline points="{line}" fill="none" stroke="{color}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Components
# ─────────────────────────────────────────────────────────────────────────────
def kpi_card(
    container,
    label: str,
    value: str,
    delta: Optional[float] = None,
    spark: Optional[Sequence[float]] = None,
    help_text: str = "",
    higher_is_better: bool = True,
    delta_suffix: str = "%",
    context: str = "",
) -> None:
    """Render a professional KPI card (value, % change, sparkline, context)."""
    # Delta styling
    delta_html = ""
    spark_color = PRIMARY
    if delta is not None:
        good = (delta >= 0) if higher_is_better else (delta <= 0)
        if abs(delta) < 0.05:
            cls, arrow, spark_color = "flat", "→", TEXT_FAINT
        elif good:
            cls, arrow, spark_color = "up", ("▲" if delta >= 0 else "▼"), SUCCESS
        else:
            cls, arrow, spark_color = "down", ("▲" if delta >= 0 else "▼"), DANGER
        delta_html = f'<span class="kpi-delta {cls}">{arrow} {abs(delta):.1f}{delta_suffix}</span>'
    else:
        delta_html = '<span class="kpi-delta flat">&nbsp;</span>'

    spark_html = sparkline_svg(spark, spark_color) if spark is not None else ""
    help_icon = f'<span class="kpi-help" title="{help_text}">ⓘ</span>' if help_text else ""
    ctx_html = f'<div class="kpi-context">{context}</div>' if context else ""

    container.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}{help_icon}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-bottom">{delta_html}<span>{spark_html}</span></div>
            {ctx_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str = "") -> None:
    sub = f'<div class="sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="section-head"><div class="title">{title}</div>{sub}</div>',
        unsafe_allow_html=True,
    )


def kpi_group_label(title: str, color: str = PRIMARY) -> None:
    """Render a KPI group label (Growth / Retention / Revenue / Churn)."""
    st.markdown(
        f'<div class="kpi-group-label"><span class="dot" style="background:{color}"></span>{title}</div>',
        unsafe_allow_html=True,
    )


def insight(text: str, kind: str = "info") -> None:
    """kind: info | success | warning | danger"""
    cls = "" if kind == "info" else kind
    st.markdown(f'<div class="insight {cls}">{text}</div>', unsafe_allow_html=True)


def chart_header(question: str, subtitle: str = "") -> None:
    """Business question + subtitle above a chart."""
    sub = f'<div class="chart-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="chart-q">{question}</div>{sub}', unsafe_allow_html=True)


def hero_insight(eyebrow: str, headline: str, body: str,
                 bg: str = PRIMARY_SOFT, text_color: str = TEXT) -> None:
    """Large hero banner for the top insight on a page."""
    st.markdown(
        f"""
        <div class="hero" style="background:{bg}">
            <div class="eyebrow" style="color:{text_color}">{eyebrow}</div>
            <div class="headline" style="color:{text_color}">{headline}</div>
            <div class="body" style="color:{TEXT_MUTED}">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def business_health_summary(growth: str, retention: str, revenue: str,
                             risk: str, details: str = "") -> None:
    """Executive Business Health Summary — Strong/Stable/Weak labels, no arbitrary scores."""
    def _badge(label: str) -> str:
        cls = label.lower()
        return f'<span class="health-badge {cls}">{label}</span>'

    det = f'<div style="font-size:0.84rem;color:{TEXT_MUTED};margin-top:12px;line-height:1.5">{details}</div>' if details else ""
    st.markdown(
        f"""
        <div class="health-summary">
            <div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.06em;color:{TEXT_MUTED};margin-bottom:12px">
                Executive Business Health</div>
            <div class="health-row"><span class="health-dim">📈 Growth</span>{_badge(growth)}</div>
            <div class="health-row"><span class="health-dim">🔄 Retention</span>{_badge(retention)}</div>
            <div class="health-row"><span class="health-dim">💰 Revenue</span>{_badge(revenue)}</div>
            <div class="health-row"><span class="health-dim">⚠️ Risk Level</span>{_badge(risk)}</div>
            {det}
        </div>
        """,
        unsafe_allow_html=True,
    )


def decision_banner(recommendation: str, detail: str = "",
                     kind: str = "ship") -> None:
    """Ship / Do Not Ship / Need More Data hero banner."""
    cls = {"ship": "ship", "no-ship": "no-ship", "wait": "wait"}.get(kind, "wait")
    label_map = {"ship": "RECOMMENDATION: SHIP", "no-ship": "RECOMMENDATION: DO NOT SHIP",
                 "wait": "RECOMMENDATION: NEED MORE DATA"}
    st.markdown(
        f"""
        <div class="decision-banner {cls}">
            <div class="decision-label">{label_map.get(kind, "RECOMMENDATION")}</div>
            <div class="decision-headline">{recommendation}</div>
            <div class="decision-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def finding_card(what: str, why: str = "", impact: str = "",
                  action: str = "") -> None:
    """Structured executive finding: What → Why → Impact → Action."""
    rows = ""
    if why:
        rows += f'<div class="finding-row"><span class="finding-label">Why</span><span class="finding-value">{why}</span></div>'
    if impact:
        rows += f'<div class="finding-row"><span class="finding-label">Impact</span><span class="finding-value">{impact}</span></div>'
    if action:
        rows += f'<div class="finding-row"><span class="finding-label">Action</span><span class="finding-value">{action}</span></div>'
    st.markdown(
        f"""
        <div class="finding-card">
            <div class="finding-what">{what}</div>
            {rows}
        </div>
        """,
        unsafe_allow_html=True,
    )


def answer_card(observation: str, evidence: str, recommendation: str,
                expected_impact: str) -> None:
    """Structured AI answer with labeled sections."""
    st.markdown(
        f"""
        <div class="answer-card">
            <div class="answer-section">
                <div class="answer-section-label obs">Observation</div>
                <div class="answer-section-text">{observation}</div>
            </div>
            <div class="answer-section">
                <div class="answer-section-label evi">Evidence</div>
                <div class="answer-section-text">{evidence}</div>
            </div>
            <div class="answer-section">
                <div class="answer-section-label rec">Recommendation</div>
                <div class="answer-section-text">{recommendation}</div>
            </div>
            <div class="answer-section">
                <div class="answer-section-label imp">Expected Impact</div>
                <div class="answer-section-text">{expected_impact}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_title(icon: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div style="margin-bottom:0.4rem">
          <span style="font-size:1.5rem">{icon}</span>
          <span style="font-size:1.45rem;font-weight:700;color:{TEXT};margin-left:6px">{title}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f'<div style="color:{TEXT_MUTED};font-size:0.9rem;margin:-2px 0 0.6rem 0">{subtitle}</div>',
            unsafe_allow_html=True,
        )
    st.markdown(f'<hr style="border:none;border-top:1px solid {BORDER};margin:0.4rem 0 1.2rem 0">',
                unsafe_allow_html=True)


def setup_page(title: str, icon: str = "📊") -> None:
    """Per-page boilerplate: page config + theme registration + CSS."""
    st.set_page_config(page_title=title, page_icon=icon, layout="wide",
                       initial_sidebar_state="expanded")
    _register_plotly_template()
    inject_css()


# Register on import so charts built before setup_page still get the theme
_register_plotly_template()
