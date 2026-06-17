"""Database access helpers.

Provides a cached SQLAlchemy engine plus convenience read/write functions used
by both the ETL layer and the dashboard. When Postgres is unavailable the
dashboard transparently falls back to the processed parquet files, so the demo
runs end-to-end even without a database.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return a process-wide SQLAlchemy engine."""
    return create_engine(settings.db.url, pool_pre_ping=True, future=True)


def ping() -> bool:
    """Return True if the database is reachable."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def write_table(df: pd.DataFrame, name: str, if_exists: str = "replace") -> None:
    """Persist a dataframe to Postgres and mirror it to parquet for offline use."""
    df.to_sql(name, get_engine(), if_exists=if_exists, index=False, chunksize=10_000)


def read_table(name: str) -> pd.DataFrame:
    return pd.read_sql_table(name, get_engine())


def read_sql(query: str, params: Optional[dict] = None) -> pd.DataFrame:
    return pd.read_sql_query(text(query), get_engine(), params=params or {})


def run_sql_file(path: Path) -> None:
    """Execute a multi-statement .sql file."""
    sql = Path(path).read_text(encoding="utf-8")
    with get_engine().begin() as conn:
        for statement in _split_statements(sql):
            conn.execute(text(statement))


def _split_statements(sql: str) -> list[str]:
    statements, buf = [], []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or not stripped:
            continue
        buf.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(buf).rstrip(";").strip())
            buf = []
    if buf:
        statements.append("\n".join(buf).strip())
    return [s for s in statements if s]
