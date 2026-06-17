"""User segmentation: RFM-style value tiers + behavioural segments."""
from __future__ import annotations

import numpy as np
import pandas as pd


def assign_segments(users: pd.DataFrame) -> pd.DataFrame:
    """Add a `segment` column using value + activity + frequency signals.

    Segments:
        High Value Customer  — top CLV quartile, still active
        Power Buyer          — frequent repeat purchaser
        Casual Buyer         — at least one purchase, low frequency
        At-Risk Customer     — previously valuable but now inactive
        Window Shopper       — engaged but never purchased
    """
    df = users.copy()
    clv_q75 = df["customer_lifetime_value"].quantile(0.75)
    freq_q75 = df["purchase_frequency"].quantile(0.75)

    def classify(r) -> str:
        churned = r.get("is_churned", 0) == 1
        has_purchase = r["n_orders"] >= 1
        if not has_purchase:
            return "Window Shopper"
        if churned and r["customer_lifetime_value"] >= clv_q75:
            return "At-Risk Customer"
        if r["customer_lifetime_value"] >= clv_q75:
            return "High Value Customer"
        if r["is_repeat_purchaser"] == 1 and r["purchase_frequency"] >= freq_q75:
            return "Power Buyer"
        return "Casual Buyer"

    df["segment"] = df.apply(classify, axis=1)
    return df


def segment_summary(users_seg: pd.DataFrame) -> pd.DataFrame:
    g = users_seg.groupby("segment")
    summary = g.agg(
        users=("user_id", "nunique"),
        avg_clv=("customer_lifetime_value", "mean"),
        total_revenue=("customer_lifetime_value", "sum"),
        avg_orders=("n_orders", "mean"),
        avg_sessions=("n_sessions", "mean"),
        churn_rate=("is_churned", "mean"),
    ).reset_index()
    total_rev = summary["total_revenue"].sum() or 1
    summary["revenue_share_pct"] = (100 * summary["total_revenue"] / total_rev).round(2)
    summary["churn_rate"] = (100 * summary["churn_rate"]).round(2)
    return summary.sort_values("total_revenue", ascending=False)


def preference_breakdown(users_seg: pd.DataFrame, by: str = "preferred_category") -> pd.DataFrame:
    return (
        users_seg.groupby(by)
        .agg(users=("user_id", "nunique"),
             revenue=("customer_lifetime_value", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
