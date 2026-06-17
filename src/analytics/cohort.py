"""Cohort & retention analysis (monthly acquisition cohorts + Day-N retention)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def monthly_cohort_matrix(events: pd.DataFrame) -> pd.DataFrame:
    """Retention matrix: rows = cohort month, cols = months since acquisition."""
    first = events.groupby("user_id")["event_time"].min().dt.to_period("M")
    first = first.rename("cohort").reset_index()

    activity = events[["user_id", "event_time"]].copy()
    activity["active"] = activity["event_time"].dt.to_period("M")
    activity = activity.merge(first, on="user_id")
    activity["month_number"] = (
        (activity["active"] - activity["cohort"]).apply(lambda x: x.n)
    )

    sizes = first.groupby("cohort")["user_id"].nunique()
    grp = (
        activity.groupby(["cohort", "month_number"])["user_id"].nunique().reset_index()
    )
    matrix = grp.pivot(index="cohort", columns="month_number", values="user_id")
    retention = matrix.divide(sizes, axis=0) * 100
    retention.index = retention.index.astype(str)
    return retention.round(1)


def cohort_sizes(events: pd.DataFrame) -> pd.Series:
    first = events.groupby("user_id")["event_time"].min().dt.to_period("M").astype(str)
    return first.value_counts().sort_index().rename("cohort_size")


def day_n_retention(events: pd.DataFrame, days=(1, 7, 30, 90)) -> pd.DataFrame:
    """Classic Day-N retention across the whole base."""
    signup = events.groupby("user_id")["event_date"].min().rename("signup")
    active = events[["user_id", "event_date"]].drop_duplicates().merge(signup, on="user_id")
    active["day_n"] = (active["event_date"] - active["signup"]).dt.days
    cohort_size = signup.shape[0]

    rows = []
    for d in days:
        retained = active.loc[active["day_n"] == d, "user_id"].nunique()
        rows.append({"day": f"D{d}", "retained_users": retained,
                     "retention_pct": round(100 * retained / cohort_size, 2) if cohort_size else 0})
    return pd.DataFrame(rows)


def retention_insights(retention: pd.DataFrame, dayn: pd.DataFrame) -> list[str]:
    insights = []
    if not dayn.empty:
        d1 = dayn.loc[dayn["day"] == "D1", "retention_pct"].squeeze()
        d30 = dayn.loc[dayn["day"] == "D30", "retention_pct"].squeeze()
        insights.append(f"Day-1 retention is {d1:.1f}% and Day-30 is {d30:.1f}%.")
        if d30 < 10:
            insights.append("Day-30 retention below 10% signals a weak habit loop — invest in onboarding & lifecycle messaging.")
    if retention.shape[1] > 1:
        # average month-1 retention across cohorts
        m1 = retention.iloc[:, 1].mean(skipna=True)
        insights.append(f"Average month-1 cohort retention is {m1:.1f}%.")
        best = retention.iloc[:, 1].idxmax() if retention.iloc[:, 1].notna().any() else None
        if best is not None:
            insights.append(f"Strongest cohort is {best} — study its acquisition channel & first-session behaviour.")
    return insights
