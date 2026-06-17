"""Root-cause analysis — detect metric drops and rank probable causes."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Anomaly:
    metric: str
    period: str
    change_pct: float
    direction: str


def detect_drops(series: pd.Series, threshold_pct: float = -10.0) -> list[Anomaly]:
    """Flag periods where a metric drops more than threshold_pct vs prior period."""
    s = series.dropna()
    pct = s.pct_change() * 100
    anomalies = []
    for idx, change in pct.items():
        if change <= threshold_pct:
            anomalies.append(
                Anomaly(metric=series.name or "metric", period=str(idx),
                        change_pct=round(float(change), 2), direction="drop")
            )
    return anomalies


def correlation_drivers(users: pd.DataFrame, target: str = "is_churned") -> pd.DataFrame:
    """Correlate behavioural features with a target (e.g. churn)."""
    num = users.select_dtypes(include=[np.number]).copy()
    if target not in num:
        return pd.DataFrame(columns=["feature", "correlation"])
    corr = num.corr(numeric_only=True)[target].drop(labels=[target], errors="ignore")
    out = corr.rename("correlation").reset_index().rename(columns={"index": "feature"})
    out["abs_corr"] = out["correlation"].abs()
    return out.sort_values("abs_corr", ascending=False).drop(columns="abs_corr")


def segment_impact(events: pd.DataFrame, dimension: str = "category") -> pd.DataFrame:
    """Revenue contribution & MoM change per segment dimension."""
    p = events[events["event_type"] == "purchase"].copy()
    if p.empty:
        return pd.DataFrame()
    monthly = p.groupby([dimension, "event_month"])["price"].sum().reset_index()
    pivot = monthly.pivot(index=dimension, columns="event_month", values="price").fillna(0)
    if pivot.shape[1] >= 2:
        last, prev = pivot.columns[-1], pivot.columns[-2]
        pivot["change_pct"] = 100 * (pivot[last] - pivot[prev]) / pivot[prev].replace(0, np.nan)
    return pivot.reset_index()


def rank_probable_causes(
    revenue_trend: pd.DataFrame,
    churn_drivers: pd.DataFrame,
    seg_impact: pd.DataFrame,
    top_n: int = 5,
) -> list[dict]:
    """Combine signals into a ranked, human-readable list of probable causes."""
    causes: list[dict] = []

    # 1. Revenue drop periods
    if "revenue" in revenue_trend:
        for a in detect_drops(revenue_trend.set_index("date")["revenue"]):
            causes.append({
                "cause": f"Revenue fell {abs(a.change_pct):.0f}% on {a.period}",
                "impact": abs(a.change_pct),
                "evidence": "Day-over-day revenue trend anomaly.",
            })

    # 2. Top churn drivers
    for _, r in churn_drivers.head(3).iterrows():
        causes.append({
            "cause": f"'{r['feature']}' strongly correlates with churn ({r['correlation']:+.2f})",
            "impact": abs(r["correlation"]) * 100,
            "evidence": "Pearson correlation with churn label.",
        })

    # 3. Segment revenue declines
    if "change_pct" in seg_impact.columns:
        worst = seg_impact.sort_values("change_pct").head(2)
        for _, r in worst.iterrows():
            dim = r[seg_impact.columns[0]]
            causes.append({
                "cause": f"Segment '{dim}' revenue changed {r['change_pct']:+.0f}% MoM",
                "impact": abs(r["change_pct"]) if pd.notna(r["change_pct"]) else 0,
                "evidence": "Month-over-month revenue by segment.",
            })

    ranked = sorted(causes, key=lambda c: c["impact"], reverse=True)[:top_n]
    for i, c in enumerate(ranked, 1):
        c["rank"] = i
    return ranked
