"""Stage 2 — Clean and standardise raw events."""
from __future__ import annotations

import numpy as np
import pandas as pd


def clean_events(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned copy of the raw event dataframe.

    Steps:
      * normalise timestamps to UTC-naive
      * drop rows without a user, product or event_type
      * fill categorical nulls with explicit "unknown" sentinels
      * coerce price to non-negative floats
      * split category_code into category / sub-category
      * remove exact duplicate events
    """
    df = df.copy()

    # Timestamps
    df["event_time"] = pd.to_datetime(df["event_time"], utc=True, errors="coerce")
    df["event_time"] = df["event_time"].dt.tz_localize(None)
    df = df.dropna(subset=["event_time", "user_id", "product_id", "event_type"])

    # Categorical nulls
    df["brand"] = df["brand"].fillna("unknown").astype(str).str.lower().str.strip()
    df["category_code"] = df["category_code"].fillna("unknown").astype(str).str.lower()
    df["user_session"] = df["user_session"].fillna("no_session").astype(str)

    # Price
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    df["price"] = df["price"].clip(lower=0.0)

    # Category hierarchy from "electronics.smartphone" → category / subcategory
    parts = df["category_code"].str.split(".", n=1, expand=True)
    df["category"] = parts[0].fillna("unknown")
    df["subcategory"] = parts[1].fillna("unknown") if parts.shape[1] > 1 else "unknown"

    # Calendar helpers reused downstream
    df["event_date"] = df["event_time"].dt.normalize()
    df["event_month"] = df["event_time"].dt.to_period("M").astype(str)

    df = df.drop_duplicates(
        subset=["event_time", "event_type", "product_id", "user_id", "user_session"]
    )

    # Normalise event types to the canonical funnel vocabulary
    valid = {"view", "cart", "remove_from_cart", "purchase"}
    df = df[df["event_type"].astype(str).isin(valid)]

    return df.reset_index(drop=True)


def data_quality_report(raw: pd.DataFrame, clean: pd.DataFrame) -> pd.DataFrame:
    """Small summary table used in the README / ETL logs."""
    return pd.DataFrame(
        {
            "metric": [
                "raw_rows",
                "clean_rows",
                "rows_dropped",
                "pct_dropped",
                "null_brand_filled",
                "null_category_filled",
            ],
            "value": [
                len(raw),
                len(clean),
                len(raw) - len(clean),
                round(100 * (len(raw) - len(clean)) / max(len(raw), 1), 2),
                int((raw["brand"].isna()).sum()) if "brand" in raw else 0,
                int((raw["category_code"].isna()).sum()) if "category_code" in raw else 0,
            ],
        }
    )
