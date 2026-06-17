"""Unified data access for the analytics layer and dashboard.

Reads processed tables from PostgreSQL when available, otherwise from the
parquet mirror in data/processed. Supports lightweight filtering used by the
dashboard sidebar (date range, category, brand, min revenue).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

import pandas as pd

from .. import db
from ..config import settings

_TABLES = ["fact_events", "user_metrics", "session_metrics", "product_metrics", "daily_activity"]


def _load_one(name: str) -> pd.DataFrame:
    """Prefer Postgres; fall back to parquet."""
    parquet = settings.paths.processed_dir / f"{name}.parquet"
    try:
        if db.ping():
            return db.read_table(name)
    except Exception:
        pass
    if parquet.exists():
        return pd.read_parquet(parquet)
    raise FileNotFoundError(
        f"No data found for '{name}'. Run the ETL: `python -m src.etl.pipeline`."
    )


def load_tables() -> dict[str, pd.DataFrame]:
    return {name: _load_one(name) for name in _TABLES}


@dataclass
class Filters:
    start: Optional[date] = None
    end: Optional[date] = None
    categories: Optional[list[str]] = None
    brands: Optional[list[str]] = None
    min_revenue: float = 0.0


def apply_event_filters(events: pd.DataFrame, f: Filters) -> pd.DataFrame:
    df = events
    if f.start is not None:
        df = df[df["event_date"] >= pd.Timestamp(f.start)]
    if f.end is not None:
        df = df[df["event_date"] <= pd.Timestamp(f.end)]
    if f.categories:
        df = df[df["category"].isin(f.categories)]
    if f.brands:
        df = df[df["brand"].isin(f.brands)]
    return df


def filter_options(events: pd.DataFrame) -> dict:
    return {
        "categories": sorted(events["category"].dropna().unique().tolist()),
        "brands": sorted(events["brand"].dropna().unique().tolist()),
        "min_date": events["event_date"].min().date(),
        "max_date": events["event_date"].max().date(),
    }
