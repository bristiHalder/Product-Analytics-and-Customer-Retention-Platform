"""Churn prediction — Logistic Regression, Random Forest, XGBoost.

Trains all three models, compares them on ROC-AUC, and returns the artefacts
the dashboard needs: ROC curves, confusion matrix and feature importance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    confusion_matrix,
    roc_auc_score,
    roc_curve,
    classification_report,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier
    _HAS_XGB = True
except Exception:  # pragma: no cover
    _HAS_XGB = False


FEATURE_COLUMNS = [
    "total_events", "n_views", "n_cart", "n_purchase", "n_sessions",
    "n_products", "n_brands", "n_categories", "customer_lifetime_value",
    "average_order_value", "lifespan_days", "purchase_frequency",
    "view_to_cart_rate", "cart_to_purchase_rate", "avg_session_events",
]
TARGET = "is_churned"


@dataclass
class ModelResult:
    name: str
    auc: float
    fpr: np.ndarray
    tpr: np.ndarray
    confusion: np.ndarray
    report: dict
    feature_importance: pd.DataFrame
    model: object = field(repr=False, default=None)


@dataclass
class ChurnTrainingOutput:
    results: dict[str, ModelResult]
    best_model: str
    X_test: pd.DataFrame
    y_test: pd.Series

    @property
    def best(self) -> ModelResult:
        return self.results[self.best_model]


def _prepare(users: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    cols = [c for c in FEATURE_COLUMNS if c in users.columns]
    X = users[cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    y = users[TARGET].astype(int)
    return X, y


def _importance(model, columns, kind: str) -> pd.DataFrame:
    if kind == "logreg":
        vals = np.abs(model.named_steps["clf"].coef_[0])
    else:
        vals = model.feature_importances_
    return (
        pd.DataFrame({"feature": columns, "importance": vals})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def train_churn_models(users: pd.DataFrame, test_size: float = 0.25, seed: int = 42) -> ChurnTrainingOutput:
    X, y = _prepare(users)
    if y.nunique() < 2:
        raise ValueError("Churn target has a single class — need both churned and active users.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )

    specs = {
        "Logistic Regression": (
            Pipeline([("scaler", StandardScaler()),
                      ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))]),
            "logreg",
        ),
        "Random Forest": (
            RandomForestClassifier(n_estimators=200, max_depth=8,
                                   class_weight="balanced", random_state=seed, n_jobs=-1),
            "tree",
        ),
    }
    if _HAS_XGB:
        pos = max((y_train == 0).sum(), 1)
        neg = max((y_train == 1).sum(), 1)
        specs["XGBoost"] = (
            XGBClassifier(
                n_estimators=300, max_depth=5, learning_rate=0.05,
                subsample=0.9, colsample_bytree=0.9, eval_metric="logloss",
                scale_pos_weight=pos / neg, random_state=seed, n_jobs=-1,
            ),
            "tree",
        )

    results: dict[str, ModelResult] = {}
    for name, (model, kind) in specs.items():
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[:, 1]
        preds = (proba >= 0.5).astype(int)
        auc = roc_auc_score(y_test, proba)
        fpr, tpr, _ = roc_curve(y_test, proba)
        cols = X.columns.tolist()
        importance = _importance(model, cols, kind)
        results[name] = ModelResult(
            name=name, auc=round(float(auc), 4), fpr=fpr, tpr=tpr,
            confusion=confusion_matrix(y_test, preds),
            report=classification_report(y_test, preds, output_dict=True, zero_division=0),
            feature_importance=importance, model=model,
        )

    best = max(results, key=lambda k: results[k].auc)
    return ChurnTrainingOutput(results=results, best_model=best, X_test=X_test, y_test=y_test)


def predict_churn_probability(model, users: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in FEATURE_COLUMNS if c in users.columns]
    X = users[cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    proba = model.predict_proba(X)[:, 1]
    out = users[["user_id"]].copy()
    out["churn_probability"] = proba.round(4)
    return out.sort_values("churn_probability", ascending=False)
