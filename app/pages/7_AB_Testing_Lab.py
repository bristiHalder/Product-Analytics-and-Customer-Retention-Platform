"""Page 7 — A/B Testing Lab.

Executive question: Should we ship this change?
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
from src.analytics import ab_testing as ab  # noqa: E402

theme.setup_page("A/B Testing Lab", "🧪")

ui.page_title("🧪", "A/B Testing Lab", "Should we ship this change?")

with st.sidebar:
    st.markdown(
        f'<div style="font-size:0.72rem;font-weight:600;letter-spacing:0.06em;'
        f'text-transform:uppercase;color:{theme.TEXT_MUTED};margin:14px 0 6px">Experiment Design</div>',
        unsafe_allow_html=True,
    )
    n_per_arm = st.slider("Users per arm", 500, 50000, 8000, step=500)
    baseline = st.slider("Baseline conversion", 0.01, 0.50, 0.12, step=0.01)
    true_lift = st.slider("True absolute lift", -0.05, 0.10, 0.015, step=0.005)
    alpha = st.select_slider("Significance (α)", [0.01, 0.05, 0.10], value=0.05)
    seed = st.number_input("Random seed", value=7, step=1)

control, treatment = ab.simulate_experiment(int(n_per_arm), baseline, true_lift, int(seed))
res = ab.analyze(control, treatment, alpha=alpha)

# ── Decision banner (hero — answer in 5 seconds) ─────────────────────────────
confidence = (1 - res.p_value) * 100
# Estimated annual impact
annual_impact = ui.estimate_experiment_annual_impact(
    res.relative_lift_pct, baseline, n_per_arm * 2, 50.0  # assume $50 ARPU for projection
)

if res.recommendation.startswith("Ship"):
    kind = "ship"
    detail = (
        f"Confidence: <b>{confidence:.1f}%</b> · "
        f"Lift: <b>{res.relative_lift_pct:+.1f}%</b> relative · "
        f"Projected annual impact: <b>~${annual_impact:,.0f}</b> incremental revenue"
    )
elif res.recommendation.startswith("Do Not"):
    kind = "no-ship"
    detail = (
        f"Confidence: <b>{confidence:.1f}%</b> · "
        f"Treatment underperforms by <b>{abs(res.relative_lift_pct):.1f}%</b> · "
        f"Shipping would cost an estimated <b>~${abs(annual_impact):,.0f}/year</b>"
    )
else:
    kind = "wait"
    detail = (
        f"Confidence: <b>{confidence:.1f}%</b> (below {(1-alpha)*100:.0f}% threshold) · "
        f"Observed lift: <b>{res.relative_lift_pct:+.1f}%</b> · "
        f"Continue collecting data to reach statistical significance"
    )

theme.decision_banner(res.recommendation, detail, kind)

# ── Result KPIs ───────────────────────────────────────────────────────────────
theme.section("Experiment Results")
r1 = st.columns(4, gap="medium")
ui.kpi_card(r1[0], "Control CVR", f"{res.control_rate:.2%}",
            help_text="Baseline conversion rate",
            context=f"{res.control_n:,} users")
ui.kpi_card(r1[1], "Treatment CVR", f"{res.treatment_rate:.2%}",
            help_text="New variant conversion rate",
            context=f"{res.treatment_n:,} users")
ui.kpi_card(r1[2], "Relative Lift", f"{res.relative_lift_pct:+.1f}%",
            help_text="Treatment vs control", higher_is_better=True,
            context=f"Absolute: {res.absolute_lift:+.3f}")
ui.kpi_card(r1[3], "P-value", f"{res.p_value:.4f}",
            help_text=f"Significant if < {alpha}", higher_is_better=False, delta_suffix="",
            context=f"{'✓ Significant' if res.significant else '✗ Not significant'} at α={alpha}")

# ── Confidence interval ───────────────────────────────────────────────────────
theme.section("Confidence Interval")
theme.chart_header("Effect size with 95% CI", "Does the interval exclude zero?")
fig = go.Figure()
# CI bar
fig.add_trace(go.Scatter(
    x=[res.ci_low, res.ci_high], y=["Effect", "Effect"],
    mode="lines", line=dict(color=theme.PRIMARY, width=6),
    name="95% CI",
))
# Point estimate
fig.add_trace(go.Scatter(
    x=[res.absolute_lift], y=["Effect"],
    mode="markers", marker=dict(color=theme.PRIMARY, size=14),
    name=f"Lift: {res.absolute_lift:+.4f}",
))
# Zero line
fig.add_vline(x=0, line_dash="dash", line_color=theme.TEXT_FAINT)
fig.update_layout(
    height=120, showlegend=True,
    xaxis_title="Absolute difference in conversion rate",
    yaxis=dict(visible=False),
    margin=dict(l=10, r=10, t=10, b=40),
)
theme.plot(fig, 120, container=st)

# ── Conversion chart ──────────────────────────────────────────────────────────
theme.section("Conversion by Variant")
fig = go.Figure(go.Bar(
    x=["Control", "Treatment"],
    y=[res.control_rate, res.treatment_rate],
    marker_color=[theme.TEXT_FAINT, theme.SUCCESS if res.absolute_lift > 0 else theme.DANGER],
    text=[f"{res.control_rate:.2%}", f"{res.treatment_rate:.2%}"],
    textposition="outside",
))
fig.update_layout(yaxis_title="Conversion Rate")
theme.plot(fig, 300, container=st)

# ── Sample size planner ───────────────────────────────────────────────────────
theme.section("Sample Size Planner", "How many users do you need to trust the result?")
p1, p2 = st.columns(2, gap="medium")
mde = p1.slider("Minimum detectable effect (absolute)", 0.005, 0.05, 0.01, step=0.005)
power = p2.select_slider("Power", [0.7, 0.8, 0.9], value=0.8)
n_needed = ab.required_sample_size(baseline, mde, alpha=alpha, power=power)
ui.insight(
    f"To detect a <b>{mde:.1%}</b> absolute lift at α={alpha}, power={power}: "
    f"<b>{n_needed:,} users per arm</b> ({2 * n_needed:,} total).",
    "info",
)
