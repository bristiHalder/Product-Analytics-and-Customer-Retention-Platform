"""Feature-adoption analysis — treat user actions as product features.

Features: view, cart, purchase, repeat purchase. We measure adoption rate,
usage frequency, and correlation with retention & revenue.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FEATURES = {
    "View": ("reached_view", "n_views"),
    "Cart": ("reached_cart", "n_cart"),
    "Purchase": ("reached_purchase", "n_purchase"),
    "Repeat Purchase": ("reached_repeat", "n_orders"),
}


def adoption_table(users: pd.DataFrame) -> pd.DataFrame:
    n = len(users) or 1
    retained = (users["is_churned"] == 0).astype(int)
    rows = []
    for feat, (flag_col, freq_col) in FEATURES.items():
        adopters = users[flag_col].sum()
        adoption_rate = 100 * adopters / n
        usage_freq = users.loc[users[flag_col] == 1, freq_col].mean()
        # correlation of adoption flag with retention & revenue
        ret_corr = _safe_corr(users[flag_col], retained)
        rev_corr = _safe_corr(users[flag_col], users["customer_lifetime_value"])
        rows.append(
            {
                "feature": feat,
                "adoption_rate_pct": round(adoption_rate, 2),
                "avg_usage_frequency": round(float(usage_freq or 0), 2),
                "retention_correlation": round(ret_corr, 3),
                "revenue_correlation": round(rev_corr, 3),
            }
        )
    return pd.DataFrame(rows)


def _safe_corr(a: pd.Series, b: pd.Series) -> float:
    if a.nunique() < 2 or b.nunique() < 2:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def feature_value_ranking(table: pd.DataFrame) -> dict:
    """Composite value score = mean of retention & revenue correlation."""
    t = table.copy()
    t["value_score"] = (t["retention_correlation"] + t["revenue_correlation"]) / 2
    t = t.sort_values("value_score", ascending=False)
    return {
        "ranked": t,
        "most_valuable": t.iloc[0]["feature"],
        "least_valuable": t.iloc[-1]["feature"],
    }


def feature_recommendations(ranking: dict) -> list[str]:
    most = ranking["most_valuable"]
    least = ranking["least_valuable"]
    return [
        f"**{most}** is the most value-correlated action — drive users toward it earlier in the journey.",
        f"**{least}** is the least correlated with value — avoid over-optimising it in isolation.",
        "Build activation experiments that move new users to the most valuable action within their first session.",
    ]
