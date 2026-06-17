"""Stage 1 — Load raw eCommerce event data.

The Kaggle dataset "eCommerce Behavior Data from Multi Category Store" ships as
large monthly CSVs (~5 GB each). We load with explicit dtypes and optional row
limiting so the pipeline works on a laptop as well as a server.

Expected columns:
    event_time, event_type, product_id, category_id,
    category_code, brand, price, user_id, user_session
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from ..config import settings

RAW_DTYPES = {
    "event_type": "category",
    "product_id": "int64",
    "category_id": "int64",
    "category_code": "object",
    "brand": "object",
    "price": "float64",
    "user_id": "int64",
    "user_session": "object",
}

EXPECTED_COLUMNS = [
    "event_time",
    "event_type",
    "product_id",
    "category_id",
    "category_code",
    "brand",
    "price",
    "user_id",
    "user_session",
]


def load_raw(path: Optional[Path] = None, nrows: Optional[int] = None) -> pd.DataFrame:
    """Load the raw CSV into a dataframe with parsed timestamps."""
    path = Path(path or settings.paths.raw_data)
    if not path.exists():
        raise FileNotFoundError(
            f"Raw data not found at {path}. Download the Kaggle dataset or run "
            "`python -m scripts.generate_sample_data` to create a synthetic sample."
        )

    df = pd.read_csv(
        path,
        dtype=RAW_DTYPES,
        parse_dates=["event_time"],
        nrows=nrows,
    )
    missing = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Raw data missing required columns: {sorted(missing)}")
    return df[EXPECTED_COLUMNS]
