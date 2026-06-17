"""Funnel analysis: view → cart → purchase → repeat purchase."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

STAGES = ["View Product", "Add To Cart", "Purchase", "Repeat Purchase"]


@dataclass
class FunnelResult:
    table: pd.DataFrame          # stage, users, conversion_from_prev, conversion_from_top, dropoff_pct
    largest_dropoff_stage: str
    largest_dropoff_pct: float
    overall_conversion: float


def compute_funnel(users: pd.DataFrame) -> FunnelResult:
    counts = [
        int(users["reached_view"].sum()),
        int(users["reached_cart"].sum()),
        int(users["reached_purchase"].sum()),
        int(users["reached_repeat"].sum()),
    ]
    rows = []
    top = counts[0] or 1
    for i, (stage, n) in enumerate(zip(STAGES, counts)):
        prev = counts[i - 1] if i > 0 else n
        conv_prev = 100 * n / prev if prev else 0.0
        dropoff = 100 - conv_prev if i > 0 else 0.0
        rows.append(
            {
                "stage": stage,
                "users": n,
                "conversion_from_prev_pct": round(conv_prev, 2),
                "conversion_from_top_pct": round(100 * n / top, 2),
                "dropoff_pct": round(dropoff, 2),
            }
        )
    table = pd.DataFrame(rows)

    # Largest drop-off across stage transitions (ignore stage 0)
    trans = table.iloc[1:]
    idx = trans["dropoff_pct"].idxmax()
    largest_stage = f"{STAGES[idx - 1]} → {STAGES[idx]}"
    largest_pct = float(trans.loc[idx, "dropoff_pct"])

    overall = round(100 * counts[2] / top, 2)
    return FunnelResult(table, largest_stage, largest_pct, overall)


def funnel_recommendations(res: FunnelResult) -> list[str]:
    recs = [
        f"Largest leak is **{res.largest_dropoff_stage}** with a "
        f"{res.largest_dropoff_pct:.1f}% drop-off — prioritise this transition.",
    ]
    stage = res.largest_dropoff_stage
    if "View Product → Add To Cart" in stage:
        recs += [
            "Improve product pages: clearer pricing, richer imagery, social proof.",
            "Add 'Add to cart' prominence and one-click add for logged-in users.",
        ]
    elif "Add To Cart → Purchase" in stage:
        recs += [
            "Reduce checkout friction: guest checkout, fewer form fields, more payment options.",
            "Trigger cart-abandonment emails/push within 1 hour of abandonment.",
        ]
    elif "Purchase → Repeat Purchase" in stage:
        recs += [
            "Launch post-purchase lifecycle: replenishment reminders, loyalty points, cross-sell.",
            "Personalise recommendations using first-purchase category affinity.",
        ]
    recs.append(
        f"Overall view→purchase conversion is {res.overall_conversion:.1f}%. "
        "Set an experiment to lift the weakest stage by 10%."
    )
    return recs
