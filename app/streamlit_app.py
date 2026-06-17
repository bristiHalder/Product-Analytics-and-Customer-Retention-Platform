"""AI-Powered Product Growth Analytics Platform — entry point.

Run with:  streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components import theme  # noqa: E402

theme.setup_page("Product Growth Analytics", "📊")

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:4px">
      <div style="width:44px;height:44px;border-radius:11px;
                  background:linear-gradient(135deg,{theme.PRIMARY},{theme.PURPLE});
                  display:flex;align-items:center;justify-content:center;font-size:22px">📊</div>
      <div>
        <div style="font-size:1.55rem;font-weight:700;color:{theme.TEXT};line-height:1.1">
          Product Growth Analytics</div>
        <div style="color:{theme.TEXT_MUTED};font-size:0.88rem">
          Growth · Retention · Conversion · Churn · Experimentation</div>
      </div>
    </div>
    <hr style="border:none;border-top:1px solid {theme.BORDER};margin:1rem 0 1.4rem 0">
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f'<div style="color:{theme.TEXT_MUTED};font-size:0.93rem;max-width:720px;margin-bottom:1.6rem;line-height:1.6">'
    "An analytics platform for Product Data Scientists and Growth Teams — turn raw "
    "clickstream events into executive decisions on growth, retention and monetisation. "
    "Select a workspace from the sidebar to begin.</div>",
    unsafe_allow_html=True,
)

# ── Navigation cards ──────────────────────────────────────────────────────────
GROUPS = [
    ("Growth & Engagement", [
        ("📈", "Executive Overview", "What should leadership focus on?"),
        ("🔻", "Funnel Analysis", "Where are we losing revenue?"),
        ("🗓️", "Cohort Analysis", "Are users returning?"),
    ]),
    ("Customers & Behaviour", [
        ("👥", "User Segmentation", "Which customers drive business value?"),
        ("🧩", "Feature Adoption", "Which behaviors create retention & revenue?"),
        ("⚠️", "Churn Prediction", "Who is likely to leave and what is at risk?"),
    ]),
    ("Experimentation & Intelligence", [
        ("🧪", "A/B Testing Lab", "Should we ship this change?"),
        ("🔍", "Root Cause Analysis", "Why did the metric move?"),
        ("🤖", "AI Insights Copilot", "What should we do next?"),
    ]),
]

for group, items in GROUPS:
    theme.section(group)
    cols = st.columns(3, gap="medium")
    for col, (icon, name, desc) in zip(cols, items):
        col.markdown(
            f"""
            <div class="kpi-card" style="min-height:120px;cursor:default">
              <div style="font-size:1.3rem;margin-bottom:8px">{icon}</div>
              <div style="font-weight:600;color:{theme.TEXT};font-size:0.96rem">{name}</div>
              <div style="color:{theme.TEXT_MUTED};font-size:0.82rem;margin-top:5px;line-height:1.45">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
theme.insight(
    "First run? Generate data and run the ETL: "
    "<code>python -m scripts.generate_sample_data</code> then "
    "<code>python -m src.etl.pipeline</code>.",
    kind="info",
)
