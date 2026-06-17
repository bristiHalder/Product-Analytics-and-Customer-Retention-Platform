"""Generate a realistic synthetic sample of the Kaggle eCommerce dataset.

Produces the exact schema of "eCommerce Behavior Data from Multi Category Store"
so the entire platform (ETL, SQL, dashboard, ML, A/B tests) runs without the
multi-gigabyte download.

Usage:
    python -m scripts.generate_sample_data --users 5000 --days 120
"""
from __future__ import annotations

import argparse
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from src.config import settings

CATALOG = {
    "electronics.smartphone": [("apple", 900), ("samsung", 750), ("xiaomi", 300)],
    "electronics.audio.headphone": [("sony", 200), ("bose", 280), ("jbl", 90)],
    "computers.notebook": [("apple", 1500), ("dell", 1100), ("lenovo", 850)],
    "apparel.shoes": [("nike", 120), ("adidas", 110), ("puma", 80)],
    "appliances.kitchen.refrigerators": [("lg", 1200), ("samsung", 1300), ("bosch", 1400)],
    "furniture.living_room.sofa": [("ikea", 600), ("ashley", 900), ("unknown", 500)],
    "auto.accessories.player": [("pioneer", 150), ("sony", 130), ("unknown", 100)],
}


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def generate(n_users: int = 5000, n_days: int = 120, seed: int = 42) -> pd.DataFrame:
    rng = _rng(seed)
    start = datetime(2025, 1, 1)
    categories = list(CATALOG.keys())

    # Build a product catalog
    products = []
    pid = 1000000
    for cat in categories:
        cat_id = rng.integers(2_000_000_000_000_000_000, 2_100_000_000_000_000_000)
        for brand, base_price in CATALOG[cat]:
            for _ in range(rng.integers(3, 8)):
                pid += 1
                price = round(base_price * rng.uniform(0.7, 1.3), 2)
                products.append((pid, cat_id, cat, brand, price))
    products = pd.DataFrame(products, columns=["product_id", "category_id", "category_code", "brand", "price"])

    # Assign each user an engagement archetype influencing behaviour
    archetypes = rng.choice(
        ["power", "regular", "casual", "one_time"],
        size=n_users,
        p=[0.1, 0.35, 0.4, 0.15],
    )
    sessions_by_arch = {"power": (15, 40), "regular": (5, 15), "casual": (2, 6), "one_time": (1, 2)}

    rows = []
    for uid in range(1, n_users + 1):
        arch = archetypes[uid - 1]
        lo, hi = sessions_by_arch[arch]
        n_sessions = int(rng.integers(lo, hi + 1))
        # one_time / casual users front-load activity (drives churn signal)
        first_day = rng.integers(0, n_days) if arch in ("power", "regular") else rng.integers(0, n_days // 2)

        for _ in range(n_sessions):
            day_offset = int(min(n_days - 1, first_day + rng.exponential(20)))
            ts = start + timedelta(
                days=day_offset,
                hours=int(rng.integers(0, 24)),
                minutes=int(rng.integers(0, 60)),
            )
            session = str(uuid.UUID(bytes=rng.bytes(16)))
            n_view = int(rng.integers(1, 8))
            sample = products.sample(n=min(n_view, len(products)), random_state=int(rng.integers(0, 1e9)))

            for _, prod in sample.iterrows():
                rows.append((ts, "view", *prod[["product_id", "category_id", "category_code", "brand", "price"]], uid, session))
                ts += timedelta(seconds=int(rng.integers(20, 300)))

                # cart probability depends on archetype
                p_cart = {"power": 0.5, "regular": 0.3, "casual": 0.15, "one_time": 0.1}[arch]
                if rng.random() < p_cart:
                    rows.append((ts, "cart", *prod[["product_id", "category_id", "category_code", "brand", "price"]], uid, session))
                    ts += timedelta(seconds=int(rng.integers(10, 120)))

                    p_purchase = {"power": 0.7, "regular": 0.45, "casual": 0.25, "one_time": 0.2}[arch]
                    if rng.random() < p_purchase:
                        rows.append((ts, "purchase", *prod[["product_id", "category_id", "category_code", "brand", "price"]], uid, session))

    df = pd.DataFrame(
        rows,
        columns=["event_time", "event_type", "product_id", "category_id", "category_code", "brand", "price", "user_id", "user_session"],
    )
    df = df.sort_values("event_time").reset_index(drop=True)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic eCommerce events")
    parser.add_argument("--users", type=int, default=5000)
    parser.add_argument("--days", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = generate(args.users, args.days, args.seed)
    out = settings.paths.raw_data
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Generated {len(df):,} events for {args.users:,} users → {out}")


if __name__ == "__main__":
    main()
