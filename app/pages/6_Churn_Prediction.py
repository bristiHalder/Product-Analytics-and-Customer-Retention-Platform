"""Page 6 — Churn Prediction.

Executive question: Who is likely to leave and what is at risk?
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.components import theme, ui  # noqa: E402
from src.analytics import root_cause as rc  # noqa: E402
from src.ml import churn_model as cm  # noqa: E402

theme.setup_page("Churn Prediction", "⚠️")

data = ui.load_data()
f = ui.sidebar_filters(data["fact_events"])
frames = ui.filtered_frames(data, f)
users = frames["users"]

ui.page_title("⚠️", "Churn Prediction",
              "Who is likely to leave and what is at risk?")

if users.empty or users["is_churned"].nunique() < 2:
    theme.insight("Need both churned and active users in the filtered set to train models. "
                  "Widen the date range or clear filters.", "warning")
    st.stop()

churn_impact = ui.estimate_churn_revenue_at_risk(users)
churn_rate = 100 * users["is_churned"].mean()
active_count = int((users["is_churned"] == 0).sum())

# ── Hero: Business impact first ───────────────────────────────────────────────
risk_level = "High" if churn_rate >= 40 else ("Medium" if churn_rate >= 25 else "Low")
hero_bg = theme.DANGER_SOFT if risk_level == "High" else (theme.WARNING_SOFT if risk_level == "Medium" else theme.SUCCESS_SOFT)

theme.hero_insight(
    eyebrow=f"CHURN RISK: {risk_level.upper()}",
    headline=f"${churn_impact['revenue_at_risk']:,.0f} revenue at risk from {churn_impact['churned_users']:,} churned users",
    body=(
        f"Churn rate: <b>{churn_rate:.1f}%</b> · "
        f"Avg CLV of churned users: <b>${churn_impact['avg_churned_clv']:,.0f}</b> · "
        f"Active users: <b>{active_count:,}</b>. "
        f"{'Immediate intervention required.' if risk_level == 'High' else 'Monitor and implement preventive measures.' if risk_level == 'Medium' else 'Healthy — maintain current retention strategies.'}"
    ),
    bg=hero_bg,
)

# ── Business Impact KPIs ─────────────────────────────────────────────────────
k1, k2, k3 = st.columns(3, gap="medium")
ui.kpi_card(k1, "Revenue at Risk", f"${churn_impact['revenue_at_risk']:,.0f}",
            help_text="Total CLV of churned users", higher_is_better=False,
            context=f"From {churn_impact['churned_users']:,} churned users")
ui.kpi_card(k2, "Churn Rate", f"{churn_rate:.1f}%",
            help_text="Users inactive 30+ days", higher_is_better=False,
            context=f"Risk level: {risk_level}")
ui.kpi_card(k3, "Active Users", f"{active_count:,}",
            help_text="Users still active",
            context=f"Avg CLV: ${float(users.loc[users['is_churned']==0, 'customer_lifetime_value'].mean()):,.0f}" if active_count > 0 else "")

# ── Top Churn Drivers with recommended actions ────────────────────────────────
theme.section("Top Churn Drivers", "Behavioral signals most correlated with churning")
drivers = rc.correlation_drivers(users, "is_churned").head(8)

theme.chart_header("Churn correlation by feature", "Positive = increases churn · Negative = protective")
fig = px.bar(drivers, x="correlation", y="feature", orientation="h",
             color="correlation", color_continuous_scale="RdBu_r")
fig.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
theme.plot(fig, 320, container=st)

# Actionable finding cards for top 3 drivers
theme.section("Recommended Actions")
DRIVER_ACTIONS = {
    "n_sessions": "Implement session-frequency nudges: push notifications, email cadence, and in-app prompts.",
    "n_purchase": "Drive repeat purchases with post-purchase lifecycle emails and loyalty incentives.",
    "purchase_frequency": "Create purchase-frequency triggers: replenishment reminders, subscription offers.",
    "n_views": "Increase engagement depth: personalised recommendations, curated content feeds.",
    "customer_lifetime_value": "Protect high-CLV users with concierge support and early churn intervention.",
    "lifespan_days": "Focus on early retention: improve Day-1 and Day-7 onboarding experiences.",
    "avg_session_events": "Deepen session engagement: guided workflows, progressive disclosure of features.",
    "view_to_cart_rate": "Improve product discovery: better search, recommendations, and social proof.",
    "cart_to_purchase_rate": "Reduce checkout friction: simplify forms, add payment options, cart recovery emails.",
    "n_cart": "Target cart abandoners with time-sensitive recovery campaigns.",
}

for _, row in drivers.head(3).iterrows():
    feat = row["feature"]
    direction = "increases" if row["correlation"] > 0 else "decreases"
    action = DRIVER_ACTIONS.get(feat, "Investigate this signal further and design targeted interventions.")
    theme.finding_card(
        what=f"'{feat}' strongly {direction} churn risk (r = {row['correlation']:+.2f})",
        why=f"{'Low' if row['correlation'] > 0 else 'High'} {feat.replace('_', ' ')} is a leading indicator of churn",
        impact=f"Addressing this driver could reduce churn impact on ${churn_impact['revenue_at_risk'] * abs(row['correlation']):,.0f} in revenue",
        action=action,
    )

# ── Model Evaluation (secondary section) ─────────────────────────────────────
theme.section("Model Evaluation")
with st.spinner("Training models …"):
    output = cm.train_churn_models(users)

cols = st.columns(len(output.results), gap="medium")
for col, (name, res) in zip(cols, output.results.items()):
    flag = "🏆 " if name == output.best_model else ""
    ui.kpi_card(col, f"{flag}{name}", f"{res.auc:.3f}",
                help_text="ROC-AUC (higher is better)",
                context="Best model" if name == output.best_model else "")

best = output.best

with st.expander("Model Details — ROC Curve & Confusion Matrix"):
    b1, b2 = st.columns(2, gap="medium")
    with b1:
        theme.chart_header("ROC curve", "How well do models rank churn risk?")
        roc = go.Figure()
        palette = [theme.PRIMARY, theme.SUCCESS, theme.WARNING]
        for (name, res), c in zip(output.results.items(), palette):
            roc.add_trace(go.Scatter(x=res.fpr, y=res.tpr, mode="lines",
                                     line=dict(color=c, width=2.5),
                                     name=f"{name} ({res.auc:.3f})"))
        roc.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines",
                                 line=dict(dash="dash", color=theme.TEXT_FAINT), name="Random"))
        roc.update_layout(xaxis_title="False Positive Rate", yaxis_title="True Positive Rate")
        theme.plot(roc, 320, container=st)

    with b2:
        theme.chart_header(f"Confusion matrix — {best.name}", "Predicted vs actual churn labels")
        fig = px.imshow(best.confusion, text_auto=True, color_continuous_scale="Blues",
                        labels=dict(x="Predicted", y="Actual"),
                        x=["Active", "Churn"], y=["Active", "Churn"])
        fig.update_layout(coloraxis_showscale=False)
        theme.plot(fig, 320, container=st)

with st.expander(f"Feature Importance — {best.name}"):
    fig = px.bar(best.feature_importance.head(12), x="importance", y="feature",
                 orientation="h", color_discrete_sequence=[theme.PRIMARY])
    fig.update_layout(yaxis=dict(autorange="reversed"))
    theme.plot(fig, 340, container=st)

# ── Highest-risk users ────────────────────────────────────────────────────────
theme.section("Highest-Risk Users", "Prioritise win-back outreach to these accounts")
risk = cm.predict_churn_probability(best.model, users)
# Add CLV for business context
if "customer_lifetime_value" in users.columns:
    risk = risk.merge(users[["user_id", "customer_lifetime_value"]], on="user_id", how="left")
    risk = risk.rename(columns={"customer_lifetime_value": "CLV ($)"})
st.dataframe(risk.head(15), use_container_width=True, hide_index=True)
