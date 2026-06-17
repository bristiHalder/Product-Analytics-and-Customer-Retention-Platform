"""Page 9 — AI Insights Copilot.

Executive question: What should we do next?
Positioned as an Executive Insights Assistant — analytics-first, not chatbot-first.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components import theme, ui  # noqa: E402
from src.ai import copilot  # noqa: E402
from src.analytics import root_cause as rc  # noqa: E402
from src.config import settings  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Helpers (defined before use)
# ─────────────────────────────────────────────────────────────────────────────
def _parse_structured_answer(text: str) -> dict | None:
    """Parse a structured answer with **Observation**, **Evidence**, etc."""
    patterns = {
        "observation": r"\*\*Observation\*\*\s*\n?(.*?)(?=\*\*Evidence|$)",
        "evidence": r"\*\*Evidence\*\*\s*\n?(.*?)(?=\*\*Recommendation|$)",
        "recommendation": r"\*\*Recommendation\*\*\s*\n?(.*?)(?=\*\*Expected Impact|$)",
        "expected_impact": r"\*\*Expected Impact\*\*\s*\n?(.*?)$",
    }
    result = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            result[key] = match.group(1).strip()
    return result if len(result) >= 2 else None


# ─────────────────────────────────────────────────────────────────────────────
# Page
# ─────────────────────────────────────────────────────────────────────────────
theme.setup_page("AI Insights Copilot", "🤖")

data = ui.load_data()
f = ui.sidebar_filters(data["fact_events"])
frames = ui.filtered_frames(data, f)

ui.page_title("🤖", "Executive Insights Assistant",
              "What should we do next? — Ask questions grounded in live dashboard metrics.")

if frames["events"].empty:
    theme.insight("No data matches the current filters. Widen the date range or clear filters.", "warning")
    st.stop()

# Build snapshot and enrich churn drivers
snapshot = ui.build_snapshot(frames)
drivers = rc.correlation_drivers(frames["users"], "is_churned").head(3)
snapshot["churn"]["top_drivers"] = drivers["feature"].tolist()

# ── Engine status ─────────────────────────────────────────────────────────────
provider = settings.ai.provider if settings.ai.enabled else "offline rule-based engine"
pill = "green" if settings.ai.enabled else "amber"

# ── Suggested prompts ─────────────────────────────────────────────────────────
theme.section("Ask a Question")
cols = st.columns(len(copilot.SUGGESTED_QUESTIONS), gap="small")
clicked = None
for col, q in zip(cols, copilot.SUGGESTED_QUESTIONS):
    if col.button(q, use_container_width=True):
        clicked = q

question = st.text_input("Ask anything about growth, retention, churn, or revenue:",
                         value=clicked or "",
                         placeholder="e.g. Why is churn increasing? What should management prioritize?")

# ── Answer ────────────────────────────────────────────────────────────────────
if question:
    with st.spinner("Analysing dashboard metrics …"):
        answer = copilot.ask(question, snapshot)

    theme.section("Analysis")

    # Try to parse structured answer (Observation / Evidence / Recommendation / Expected Impact)
    sections = _parse_structured_answer(answer)

    if sections:
        ui.answer_card(
            observation=sections.get("observation", ""),
            evidence=sections.get("evidence", ""),
            recommendation=sections.get("recommendation", ""),
            expected_impact=sections.get("expected_impact", ""),
        )
    else:
        # Fallback: render as a clean insight card
        st.markdown(f'<div class="answer-card"><div style="font-size:0.9rem;line-height:1.6">{answer}</div></div>',
                    unsafe_allow_html=True)
else:
    theme.insight(
        "Pick a suggested question or type your own. Every answer follows the structure: "
        "<b>Observation → Evidence → Recommendation → Expected Impact</b>.",
        "info",
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f'<div style="margin-top:16px"><span class="pill {pill}">Engine: {provider}</span></div>',
            unsafe_allow_html=True)

with st.expander("📦 Dashboard snapshot the AI reads"):
    st.json(snapshot)
