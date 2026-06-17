"""AI Insights Copilot.

Wraps OpenAI / Gemini with a grounded prompt built from live dashboard metrics
(KPIs, funnel, cohort, churn). If no API key is configured, a deterministic
rule-based engine produces structured insights so the platform always works.

Every answer follows the structure:
    Observation → Evidence → Recommendation → Expected Impact
"""
from __future__ import annotations

import json
import textwrap
from typing import Any, Optional

from ..config import settings

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are a Senior Product Data Scientist at a top tech company (Meta/Google
    caliber). You analyse a product growth analytics dashboard and answer
    executive questions. Always ground answers in the provided metrics JSON.
    Structure every answer with these four bold sections:
    **Observation**, **Evidence**, **Recommendation**, **Expected Impact**.
    Be concise, quantitative, and decisive.
    """
).strip()


def build_context(snapshot: dict[str, Any]) -> str:
    """Serialise the dashboard snapshot into a compact JSON context block."""
    return json.dumps(snapshot, default=str, indent=2)


def ask(question: str, snapshot: dict[str, Any]) -> str:
    """Answer a question grounded in the dashboard snapshot."""
    context = build_context(snapshot)
    if settings.ai.enabled:
        try:
            if settings.ai.provider == "openai":
                return _ask_openai(question, context)
            if settings.ai.provider == "gemini":
                return _ask_gemini(question, context)
        except Exception as exc:  # graceful fallback
            return _rule_based(question, snapshot) + f"\n\n_(AI provider error: {exc}. Used offline engine.)_"
    return _rule_based(question, snapshot)


# ── Providers ────────────────────────────────────────────────────────────────
def _ask_openai(question: str, context: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.ai.openai_api_key)
    resp = client.chat.completions.create(
        model=settings.ai.openai_model,
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Dashboard metrics:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return resp.choices[0].message.content.strip()


def _ask_gemini(question: str, context: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.ai.gemini_api_key)
    model = genai.GenerativeModel(settings.ai.gemini_model, system_instruction=SYSTEM_PROMPT)
    resp = model.generate_content(f"Dashboard metrics:\n{context}\n\nQuestion: {question}")
    return resp.text.strip()


# ── Offline rule-based fallback ──────────────────────────────────────────────
def _fmt(section_obs, evidence, rec, impact) -> str:
    return (
        f"**Observation**\n{section_obs}\n\n"
        f"**Evidence**\n{evidence}\n\n"
        f"**Recommendation**\n{rec}\n\n"
        f"**Expected Impact**\n{impact}"
    )


def _rule_based(question: str, s: dict[str, Any]) -> str:
    q = question.lower()
    kpis = s.get("kpis", {})
    funnel = s.get("funnel", {})
    churn = s.get("churn", {})
    segments = s.get("segments", [])

    if "retention" in q:
        return _fmt(
            f"Retention rate is {kpis.get('retention_rate', 'n/a')}% with churn at {kpis.get('churn_rate', 'n/a')}%.",
            f"Largest funnel leak: {funnel.get('largest_dropoff_stage', 'n/a')} "
            f"({funnel.get('largest_dropoff_pct', 'n/a')}% drop-off).",
            "Strengthen onboarding and lifecycle messaging at the weakest funnel stage; "
            "trigger re-engagement for users inactive 14–29 days before they churn.",
            "A 5pt retention lift typically compounds into 15–25% higher 90-day LTV.",
        )
    if "churn" in q:
        drivers = ", ".join(churn.get("top_drivers", [])[:3]) or "low session frequency, no repeat purchase"
        return _fmt(
            f"Churn rate is {kpis.get('churn_rate', 'n/a')}% (no activity 30+ days).",
            f"Top churn-correlated signals: {drivers}.",
            "Target at-risk users (high CLV, rising inactivity) with win-back offers and "
            "remove friction at the cart→purchase step.",
            "Reducing churn by 10% on high-value users protects a disproportionate share of revenue.",
        )
    if "valuable" in q or "segment" in q:
        top = segments[0] if segments else {}
        return _fmt(
            f"The most valuable segment is '{top.get('segment', 'High Value Customer')}'.",
            f"It contributes ~{top.get('revenue_share_pct', 'n/a')}% of revenue "
            f"from {top.get('users', 'n/a')} users.",
            "Protect and expand this segment with loyalty, concierge support and lookalike acquisition.",
            "Defending the top revenue segment is the highest-ROI retention investment.",
        )
    if "prioriti" in q or "management" in q or "action" in q:
        return _fmt(
            "Growth is gated by the weakest funnel transition and high-value churn.",
            f"Funnel leak at {funnel.get('largest_dropoff_stage', 'n/a')}; "
            f"churn at {kpis.get('churn_rate', 'n/a')}%; ARPU ${kpis.get('arpu', 'n/a')}.",
            "1) Fix the largest funnel drop-off via experimentation. "
            "2) Launch win-back for at-risk high-value users. "
            "3) Drive repeat purchase with lifecycle automation.",
            "Sequenced correctly, expect mid-single-digit lifts in conversion and retention within a quarter.",
        )
    if "summar" in q:
        return _fmt(
            f"{kpis.get('mau', 'n/a')} MAU, {kpis.get('growth_rate', 'n/a')}% MoM growth, "
            f"${kpis.get('total_revenue', 'n/a')} revenue.",
            f"Retention {kpis.get('retention_rate', 'n/a')}%, churn {kpis.get('churn_rate', 'n/a')}%, "
            f"ARPU ${kpis.get('arpu', 'n/a')}. Biggest leak: {funnel.get('largest_dropoff_stage', 'n/a')}.",
            "Focus the roadmap on the weakest funnel stage and high-value retention.",
            "Compounding retention + conversion gains drive durable revenue growth.",
        )
    return _fmt(
        "I analysed the current dashboard snapshot.",
        f"KPIs: {json.dumps(kpis)}",
        "Ask about retention, churn, valuable segments, or priorities for a targeted recommendation.",
        "Grounded, metric-driven decisions reduce guesswork and accelerate growth.",
    )


SUGGESTED_QUESTIONS = [
    "Why did retention decrease?",
    "Why is churn increasing?",
    "Which segment is most valuable?",
    "What should management prioritize?",
    "Summarize this dashboard.",
]
