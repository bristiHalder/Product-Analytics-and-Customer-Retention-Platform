"""Executive growth metrics: DAU/WAU/MAU, growth, retention, churn, revenue."""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

from ..config import settings


@dataclass
class ExecutiveKPIs:
    dau: int
    wau: int
    mau: int
    growth_rate: float          # MoM active-user growth %
    retention_rate: float       # % of users active in last 30d who were also active prior 30d
    churn_rate: float           # % of users inactive 30+ days
    total_revenue: float
    arpu: float
    n_users: int

    def as_dict(self) -> dict:
        return asdict(self)


def compute_kpis(events: pd.DataFrame, users: pd.DataFrame) -> ExecutiveKPIs:
    if events.empty:
        return ExecutiveKPIs(0, 0, 0, 0, 0, 0, 0, 0, 0)

    max_date = events["event_date"].max()
    dau = events.loc[events["event_date"] == max_date, "user_id"].nunique()
    wau = events.loc[events["event_date"] > max_date - pd.Timedelta(days=7), "user_id"].nunique()
    mau = events.loc[events["event_date"] > max_date - pd.Timedelta(days=30), "user_id"].nunique()

    # Month-over-month active-user growth
    monthly = events.groupby("event_month")["user_id"].nunique().sort_index()
    growth_rate = 0.0
    if len(monthly) >= 2 and monthly.iloc[-2] > 0:
        growth_rate = 100 * (monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2]

    # 30-day rolling retention: active in current 30d AND active in prior 30d
    cur = set(events.loc[events["event_date"] > max_date - pd.Timedelta(days=30), "user_id"])
    prev_mask = (events["event_date"] <= max_date - pd.Timedelta(days=30)) & (
        events["event_date"] > max_date - pd.Timedelta(days=60)
    )
    prev = set(events.loc[prev_mask, "user_id"])
    retention_rate = 100 * len(cur & prev) / len(prev) if prev else 0.0

    churn_rate = 100 * users["is_churned"].mean() if "is_churned" in users else 0.0
    total_revenue = float(users["customer_lifetime_value"].sum())
    n_users = int(users["user_id"].nunique())
    arpu = total_revenue / n_users if n_users else 0.0

    return ExecutiveKPIs(
        dau=int(dau), wau=int(wau), mau=int(mau),
        growth_rate=round(growth_rate, 2),
        retention_rate=round(retention_rate, 2),
        churn_rate=round(churn_rate, 2),
        total_revenue=round(total_revenue, 2),
        arpu=round(arpu, 2),
        n_users=n_users,
    )


def daily_active_trend(events: pd.DataFrame) -> pd.DataFrame:
    return (
        events.groupby("event_date")["user_id"].nunique()
        .rename("dau").reset_index().rename(columns={"event_date": "date"})
    )


def monthly_growth_trend(events: pd.DataFrame) -> pd.DataFrame:
    monthly = events.groupby("event_month")["user_id"].nunique().rename("active_users").reset_index()
    monthly["growth_pct"] = monthly["active_users"].pct_change() * 100
    return monthly


def revenue_trend(events: pd.DataFrame) -> pd.DataFrame:
    p = events[events["event_type"] == "purchase"]
    return (
        p.groupby("event_date")["price"].sum().rename("revenue")
        .reset_index().rename(columns={"event_date": "date"})
    )


def retention_trend(events: pd.DataFrame) -> pd.DataFrame:
    """Weekly retention: share of last week's users active again this week."""
    ev = events.copy()
    ev["week"] = ev["event_time"].dt.to_period("W").astype(str)
    weeks = sorted(ev["week"].unique())
    rows = []
    prev_users: set = set()
    for w in weeks:
        users_w = set(ev.loc[ev["week"] == w, "user_id"])
        ret = 100 * len(users_w & prev_users) / len(prev_users) if prev_users else np.nan
        rows.append({"week": w, "retention_pct": ret})
        prev_users = users_w
    return pd.DataFrame(rows)


def churn_trend(events: pd.DataFrame, window_days: int = 30) -> pd.DataFrame:
    """Approximate weekly churn = 100 - weekly retention."""
    ret = retention_trend(events)
    ret["churn_pct"] = 100 - ret["retention_pct"]
    return ret[["week", "churn_pct"]]


def _pct_change(cur: float, prev: float) -> float:
    if not prev:
        return 0.0
    return round(100 * (cur - prev) / prev, 2)


def _window_active(events: pd.DataFrame, end, days: int) -> int:
    start = end - pd.Timedelta(days=days - 1)
    mask = (events["event_date"] >= start) & (events["event_date"] <= end)
    return events.loc[mask, "user_id"].nunique()


def kpi_trends(events: pd.DataFrame, kpis: "ExecutiveKPIs") -> dict:
    """Per-KPI period-over-period deltas + small spark series for KPI cards."""
    if events.empty:
        return {}

    md = events["event_date"].max()
    daily = daily_active_trend(events)
    rev = revenue_trend(events).set_index("date")["revenue"]
    ret = retention_trend(events)["retention_pct"].dropna()
    churn = churn_trend(events)["churn_pct"].dropna()
    growth = monthly_growth_trend(events)["active_users"]

    # Active-user deltas: trailing window vs immediately preceding equal window
    prev_end = md - pd.Timedelta(days=1)
    wau_prev = _window_active(events, md - pd.Timedelta(days=7), 7)
    mau_prev = _window_active(events, md - pd.Timedelta(days=30), 30)
    dau_series = daily["dau"].tolist()
    dau_prev = dau_series[-2] if len(dau_series) >= 2 else kpis.dau

    # Revenue deltas: trailing 7d vs prior 7d
    rev_now = rev[rev.index > md - pd.Timedelta(days=7)].sum()
    rev_prev = rev[(rev.index <= md - pd.Timedelta(days=7)) &
                   (rev.index > md - pd.Timedelta(days=14))].sum()

    def spark(series, n=20):
        s = list(series)
        return s[-n:] if len(s) > 1 else s

    return {
        "dau": {"delta": _pct_change(kpis.dau, dau_prev), "spark": spark(dau_series)},
        "wau": {"delta": _pct_change(kpis.wau, wau_prev), "spark": spark(dau_series)},
        "mau": {"delta": _pct_change(kpis.mau, mau_prev), "spark": spark(dau_series)},
        "growth_rate": {"delta": None, "spark": spark(growth.tolist())},
        "retention_rate": {
            "delta": round(float(ret.iloc[-1] - ret.iloc[-2]), 2) if len(ret) >= 2 else None,
            "spark": spark(ret.tolist()),
        },
        "churn_rate": {
            "delta": round(float(churn.iloc[-1] - churn.iloc[-2]), 2) if len(churn) >= 2 else None,
            "spark": spark(churn.tolist()),
        },
        "revenue": {"delta": _pct_change(rev_now, rev_prev), "spark": spark(rev.tolist())},
        "arpu": {"delta": _pct_change(rev_now, rev_prev), "spark": spark(rev.tolist())},
    }
