"""Stage 3 — Build user / session / product level analytical tables.

Maps raw events into a product funnel (view → cart → purchase → repeat purchase)
and derives the business metrics requested by the platform spec.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import settings


# ─────────────────────────────────────────────────────────────────────────────
# Session level
# ─────────────────────────────────────────────────────────────────────────────
def build_session_metrics(events: pd.DataFrame) -> pd.DataFrame:
    """One row per user_session with engagement + monetisation proxies."""
    g = events.groupby("user_session", observed=True)
    sessions = g.agg(
        user_id=("user_id", "first"),
        session_start=("event_time", "min"),
        session_end=("event_time", "max"),
        n_events=("event_type", "size"),
        n_views=("event_type", lambda s: (s == "view").sum()),
        n_cart=("event_type", lambda s: (s == "cart").sum()),
        n_purchase=("event_type", lambda s: (s == "purchase").sum()),
        n_products=("product_id", "nunique"),
        revenue=("price", lambda s: s[events.loc[s.index, "event_type"] == "purchase"].sum()),
    ).reset_index()

    # session_duration_proxy = span between first and last event (seconds)
    sessions["session_duration_proxy"] = (
        (sessions["session_end"] - sessions["session_start"]).dt.total_seconds()
    )
    # cart_abandonment = added to cart but did not purchase in the session
    sessions["cart_abandonment"] = (
        (sessions["n_cart"] > 0) & (sessions["n_purchase"] == 0)
    ).astype(int)
    sessions["converted"] = (sessions["n_purchase"] > 0).astype(int)
    sessions["session_date"] = sessions["session_start"].dt.normalize()
    return sessions


# ─────────────────────────────────────────────────────────────────────────────
# User level
# ─────────────────────────────────────────────────────────────────────────────
def build_user_metrics(events: pd.DataFrame, sessions: pd.DataFrame) -> pd.DataFrame:
    """One row per user with funnel, retention and CLV style metrics."""
    purchases = events[events["event_type"] == "purchase"]
    analysis_date = events["event_time"].max()

    g = events.groupby("user_id", observed=True)
    users = g.agg(
        first_seen=("event_time", "min"),
        last_seen=("event_time", "max"),
        total_events=("event_type", "size"),
        n_views=("event_type", lambda s: (s == "view").sum()),
        n_cart=("event_type", lambda s: (s == "cart").sum()),
        n_purchase=("event_type", lambda s: (s == "purchase").sum()),
        n_sessions=("user_session", "nunique"),
        n_products=("product_id", "nunique"),
        n_brands=("brand", "nunique"),
        n_categories=("category", "nunique"),
    ).reset_index()

    # Revenue / monetisation
    rev = purchases.groupby("user_id", observed=True)["price"].agg(
        ["sum", "mean", "count"]
    )
    rev.columns = ["customer_lifetime_value", "average_order_value", "n_orders"]
    users = users.merge(rev, on="user_id", how="left").fillna(
        {"customer_lifetime_value": 0.0, "average_order_value": 0.0, "n_orders": 0}
    )

    # Cohort = first activity month
    users["cohort_month"] = users["first_seen"].dt.to_period("M").astype(str)
    users["signup_date"] = users["first_seen"].dt.normalize()

    # Lifespan & recency
    users["lifespan_days"] = (
        (users["last_seen"] - users["first_seen"]).dt.total_seconds() / 86400
    ).round(2)
    last_purchase = purchases.groupby("user_id", observed=True)["event_time"].max()
    users = users.merge(
        last_purchase.rename("last_purchase_time"), on="user_id", how="left"
    )
    users["days_since_last_purchase"] = (
        (analysis_date - users["last_purchase_time"]).dt.total_seconds() / 86400
    )
    users["days_since_last_seen"] = (
        (analysis_date - users["last_seen"]).dt.total_seconds() / 86400
    )

    # Frequency & funnel flags
    users["purchase_frequency"] = users["n_orders"] / users["n_sessions"].clip(lower=1)
    users["is_repeat_purchaser"] = (users["n_orders"] >= 2).astype(int)
    users["reached_view"] = (users["n_views"] > 0).astype(int)
    users["reached_cart"] = (users["n_cart"] > 0).astype(int)
    users["reached_purchase"] = (users["n_orders"] >= 1).astype(int)
    users["reached_repeat"] = users["is_repeat_purchaser"]

    # Churn label: no activity within the configured inactivity window
    users["is_churned"] = (
        users["days_since_last_seen"] > settings.churn_inactivity_days
    ).astype(int)

    # Engagement ratios used by feature-adoption & churn models
    users["view_to_cart_rate"] = users["n_cart"] / users["n_views"].clip(lower=1)
    users["cart_to_purchase_rate"] = users["n_orders"] / users["n_cart"].clip(lower=1)
    users["avg_session_events"] = users["total_events"] / users["n_sessions"].clip(lower=1)

    # Preferred brand / category (mode)
    users = users.merge(_preferred(events, "brand", "preferred_brand"), on="user_id", how="left")
    users = users.merge(
        _preferred(events, "category", "preferred_category"), on="user_id", how="left"
    )
    return users


def _preferred(events: pd.DataFrame, col: str, out: str) -> pd.DataFrame:
    mode = (
        events.groupby("user_id", observed=True)[col]
        .agg(lambda s: s.value_counts().index[0] if len(s) else "unknown")
        .rename(out)
        .reset_index()
    )
    return mode


# ─────────────────────────────────────────────────────────────────────────────
# Product level
# ─────────────────────────────────────────────────────────────────────────────
def build_product_metrics(events: pd.DataFrame) -> pd.DataFrame:
    """One row per product with funnel + revenue stats."""
    g = events.groupby("product_id", observed=True)
    products = g.agg(
        category=("category", "first"),
        brand=("brand", "first"),
        avg_price=("price", "mean"),
        n_views=("event_type", lambda s: (s == "view").sum()),
        n_cart=("event_type", lambda s: (s == "cart").sum()),
        n_purchase=("event_type", lambda s: (s == "purchase").sum()),
        n_unique_users=("user_id", "nunique"),
    ).reset_index()
    purchases = events[events["event_type"] == "purchase"]
    rev = purchases.groupby("product_id", observed=True)["price"].sum().rename("revenue")
    products = products.merge(rev, on="product_id", how="left").fillna({"revenue": 0.0})
    products["view_to_purchase_rate"] = (
        products["n_purchase"] / products["n_views"].clip(lower=1)
    )
    return products


# ─────────────────────────────────────────────────────────────────────────────
# Daily activity (for DAU/WAU/MAU and trend charts)
# ─────────────────────────────────────────────────────────────────────────────
def build_daily_activity(events: pd.DataFrame) -> pd.DataFrame:
    daily = (
        events.groupby("event_date", observed=True)
        .agg(
            active_users=("user_id", "nunique"),
            sessions=("user_session", "nunique"),
            events=("event_type", "size"),
            purchases=("event_type", lambda s: (s == "purchase").sum()),
        )
        .reset_index()
        .rename(columns={"event_date": "activity_date"})
    )
    rev = (
        events[events["event_type"] == "purchase"]
        .groupby("event_date", observed=True)["price"]
        .sum()
        .rename("revenue")
        .reset_index()
        .rename(columns={"event_date": "activity_date"})
    )
    daily = daily.merge(rev, on="activity_date", how="left").fillna({"revenue": 0.0})
    return daily.sort_values("activity_date").reset_index(drop=True)
