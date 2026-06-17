"""ETL orchestration: load → clean → transform → store.

Run as a module:
    python -m src.etl.pipeline --nrows 2000000

Outputs processed tables to PostgreSQL (when reachable) and always mirrors them
to parquet under data/processed so the dashboard runs offline.
"""
from __future__ import annotations

import argparse
import logging
from typing import Optional

import pandas as pd

from .. import db
from ..config import settings
from . import clean, load, transform

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("etl")

PROCESSED_TABLES = [
    "fact_events",
    "user_metrics",
    "session_metrics",
    "product_metrics",
    "daily_activity",
]


def _persist(df: pd.DataFrame, name: str, use_db: bool) -> None:
    settings.paths.ensure()
    out = settings.paths.processed_dir / f"{name}.parquet"
    df.to_parquet(out, index=False)
    log.info("Wrote %s rows → %s", f"{len(df):,}", out.name)
    if use_db:
        db.write_table(df, name)
        log.info("Loaded table '%s' into PostgreSQL", name)


def run(nrows: Optional[int] = None) -> dict[str, pd.DataFrame]:
    use_db = db.ping()
    if use_db:
        log.info("PostgreSQL reachable — loading schema")
        db.run_sql_file(settings.paths.processed_dir.parent.parent / "sql" / "01_schema.sql")
    else:
        log.warning("PostgreSQL not reachable — writing parquet only (offline mode)")

    log.info("Loading raw events ...")
    raw = load.load_raw(nrows=nrows)
    log.info("Cleaning %s raw rows ...", f"{len(raw):,}")
    events = clean.clean_events(raw)
    log.info(clean.data_quality_report(raw, events).to_string(index=False))

    log.info("Building analytical tables ...")
    sessions = transform.build_session_metrics(events)
    users = transform.build_user_metrics(events, sessions)
    products = transform.build_product_metrics(events)
    daily = transform.build_daily_activity(events)

    tables = {
        "fact_events": events,
        "user_metrics": users,
        "session_metrics": sessions,
        "product_metrics": products,
        "daily_activity": daily,
    }
    for name, df in tables.items():
        _persist(df, name, use_db)

    log.info("ETL complete ✅")
    return tables


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the growth analytics ETL")
    parser.add_argument("--nrows", type=int, default=None, help="Limit raw rows (for testing)")
    args = parser.parse_args()
    run(nrows=args.nrows)
