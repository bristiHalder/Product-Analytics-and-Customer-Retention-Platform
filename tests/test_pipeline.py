"""End-to-end smoke tests for the analytics platform.

These run against a small synthetic dataset (no database required) and validate
the ETL transforms, funnel, cohort, segmentation, A/B testing and churn models.
"""
from __future__ import annotations

import pandas as pd
import pytest

from scripts.generate_sample_data import generate
from src.analytics import ab_testing as ab
from src.analytics import cohort as ch
from src.analytics import feature_adoption as fa
from src.analytics import funnel as fn
from src.analytics import metrics as m
from src.analytics import segmentation as sg
from src.etl import clean, transform
from src.ml import churn_model as cm


@pytest.fixture(scope="module")
def events() -> pd.DataFrame:
    raw = generate(n_users=600, n_days=90, seed=1)
    return clean.clean_events(raw)


@pytest.fixture(scope="module")
def users(events) -> pd.DataFrame:
    sessions = transform.build_session_metrics(events)
    return transform.build_user_metrics(events, sessions)


def test_clean_produces_canonical_events(events):
    assert not events.empty
    assert set(events["event_type"].unique()).issubset(
        {"view", "cart", "remove_from_cart", "purchase"}
    )
    assert events["price"].min() >= 0
    assert "category" in events.columns


def test_user_metrics_funnel_flags(users):
    assert (users["reached_view"] >= users["reached_cart"]).all()
    assert (users["reached_cart"] >= users["reached_purchase"]).all()
    assert (users["reached_purchase"] >= users["reached_repeat"]).all()
    assert users["customer_lifetime_value"].min() >= 0


def test_kpis(events, users):
    kpis = m.compute_kpis(events, users)
    assert kpis.mau >= kpis.dau
    assert 0 <= kpis.churn_rate <= 100


def test_funnel(users):
    res = fn.compute_funnel(users)
    counts = res.table["users"].tolist()
    assert counts == sorted(counts, reverse=True)
    assert res.largest_dropoff_stage
    assert fn.funnel_recommendations(res)


def test_cohort(events):
    matrix = ch.monthly_cohort_matrix(events)
    assert not matrix.empty
    dayn = ch.day_n_retention(events)
    assert set(dayn["day"]) == {"D1", "D7", "D30", "D90"}


def test_segmentation(users):
    seg = sg.assign_segments(users)
    summary = sg.segment_summary(seg)
    assert summary["revenue_share_pct"].sum() == pytest.approx(100, abs=1.0)


def test_feature_adoption(users):
    table = fa.adoption_table(users)
    ranking = fa.feature_value_ranking(table)
    assert ranking["most_valuable"] in table["feature"].tolist()


def test_ab_testing_significant_positive_lift():
    control, treatment = ab.simulate_experiment(20000, 0.12, 0.04, seed=3)
    res = ab.analyze(control, treatment)
    assert res.treatment_rate > res.control_rate
    assert res.recommendation.startswith("Ship")


def test_required_sample_size_positive():
    n = ab.required_sample_size(0.12, 0.01)
    assert n > 0


def test_churn_models_train(users):
    if users["is_churned"].nunique() < 2:
        pytest.skip("single churn class in sample")
    out = cm.train_churn_models(users)
    assert out.best_model in out.results
    assert 0.0 <= out.best.auc <= 1.0
    assert not out.best.feature_importance.empty
