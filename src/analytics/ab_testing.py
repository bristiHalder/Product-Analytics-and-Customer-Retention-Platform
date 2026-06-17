"""A/B testing lab — simulate experiments and run proper statistical tests."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
from statsmodels.stats.power import NormalIndPower


@dataclass
class ABResult:
    control_n: int
    treatment_n: int
    control_rate: float
    treatment_rate: float
    absolute_lift: float
    relative_lift_pct: float
    p_value: float
    ci_low: float
    ci_high: float
    significant: bool
    recommendation: str


def simulate_experiment(
    n_per_arm: int = 5000,
    baseline_rate: float = 0.12,
    true_lift: float = 0.015,
    seed: int = 7,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (control, treatment) binary conversion arrays."""
    rng = np.random.default_rng(seed)
    control = rng.binomial(1, baseline_rate, n_per_arm)
    treatment = rng.binomial(1, min(0.99, baseline_rate + true_lift), n_per_arm)
    return control, treatment


def analyze(control: np.ndarray, treatment: np.ndarray, alpha: float = 0.05) -> ABResult:
    c_n, t_n = len(control), len(treatment)
    c_conv, t_conv = int(control.sum()), int(treatment.sum())
    c_rate, t_rate = c_conv / c_n, t_conv / t_n

    # Two-proportion z-test
    stat, p_value = proportions_ztest([t_conv, c_conv], [t_n, c_n])

    # CI on the difference (Newcombe via independent CIs is approximate; use normal approx)
    se = np.sqrt(c_rate * (1 - c_rate) / c_n + t_rate * (1 - t_rate) / t_n)
    diff = t_rate - c_rate
    z = stats.norm.ppf(1 - alpha / 2)
    ci_low, ci_high = diff - z * se, diff + z * se

    rel_lift = 100 * diff / c_rate if c_rate else 0.0
    significant = p_value < alpha

    if significant and diff > 0:
        rec = "Ship 🚀 — statistically significant positive lift."
    elif significant and diff < 0:
        rec = "Do Not Ship ⛔ — treatment significantly underperforms control."
    else:
        rec = "Need More Data ⏳ — result is not statistically significant."

    return ABResult(
        control_n=c_n, treatment_n=t_n,
        control_rate=round(c_rate, 4), treatment_rate=round(t_rate, 4),
        absolute_lift=round(diff, 4), relative_lift_pct=round(rel_lift, 2),
        p_value=round(float(p_value), 5),
        ci_low=round(ci_low, 4), ci_high=round(ci_high, 4),
        significant=significant, recommendation=rec,
    )


def required_sample_size(baseline_rate: float, mde: float, alpha=0.05, power=0.8) -> int:
    """Sample size per arm to detect a minimum detectable effect `mde` (absolute)."""
    p1, p2 = baseline_rate, baseline_rate + mde
    pooled = (p1 + p2) / 2
    effect = (p2 - p1) / np.sqrt(pooled * (1 - pooled))
    analysis = NormalIndPower()
    n = analysis.solve_power(effect_size=effect, alpha=alpha, power=power, ratio=1.0)
    return int(np.ceil(n))
