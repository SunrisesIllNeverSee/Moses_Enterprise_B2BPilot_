"""Outcome correlation through lineage — connects operating patterns to
downstream consequences.

Per Jaimie's review §17: "Without an Outcome object, Micro Evals risks
eventually becoming extremely sophisticated behavior analytics. With an
Outcome object, it can become performance science."

This module correlates the micro_eval metrics from lineage chains with
the outcome metrics (quality score, cycle time) from the linked Outcome
nodes. The correlation reveals whether specific operating patterns
actually produce better outcomes.

IMPORTANT: All results are labeled ASSOCIATION, never CAUSATION.
Correlation does not imply causation. A controlled experiment
(EVAL-012) is required for causal claims. This analysis generates
hypotheses, not proofs.

Evidence grade: OBSERVATIONAL (grade 4) at best — these are
observational correlations from synthetic data, not controlled
experiments.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True, slots=True)
class MetricOutcomeCorrelation:
    """Correlation between one micro_eval metric and one outcome metric."""
    metric_id: str
    outcome_metric: str  # "external_quality_score", "cycle_time_minutes", "outcome_status"
    correlation: float  # Pearson r, -1 to +1
    p_value_approx: float  # approximate, from t-distribution
    sample_size: int
    interpretation: str
    direction: str  # "positive", "negative", "none"
    strength: str  # "strong", "moderate", "weak", "none"

    def to_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "outcome_metric": self.outcome_metric,
            "correlation": round(self.correlation, 4),
            "p_value_approx": round(self.p_value_approx, 4),
            "sample_size": self.sample_size,
            "interpretation": self.interpretation,
            "direction": self.direction,
            "strength": self.strength,
        }


@dataclass(frozen=True, slots=True)
class OutcomeCorrelationResult:
    """Full outcome correlation analysis across all metrics."""
    correlations: List[MetricOutcomeCorrelation]
    operators_analyzed: int
    lineages_with_outcomes: int
    evidence_grade: str  # always "OBSERVATIONAL"
    claim_status: str  # always "ASSOCIATION"
    summary: str

    def to_dict(self) -> dict:
        return {
            "correlations": [c.to_dict() for c in self.correlations],
            "operators_analyzed": self.operators_analyzed,
            "lineages_with_outcomes": self.lineages_with_outcomes,
            "evidence_grade": self.evidence_grade,
            "claim_status": self.claim_status,
            "summary": self.summary,
        }


def _pearson_r(x: List[float], y: List[float]) -> Tuple[float, float]:
    """Compute Pearson correlation coefficient and approximate p-value.

    Returns (r, p_value). If insufficient data or zero variance,
    returns (0.0, 1.0).
    """
    n = len(x)
    if n < 3:
        return 0.0, 1.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)

    if var_x == 0 or var_y == 0:
        return 0.0, 1.0

    r = cov / math.sqrt(var_x * var_y)
    # Clamp to [-1, 1] for floating point safety
    r = max(-1.0, min(1.0, r))

    # Approximate p-value from t-distribution
    # t = r * sqrt(n-2) / sqrt(1-r^2)
    if abs(r) >= 1.0:
        p = 0.0
    else:
        t_stat = r * math.sqrt(n - 2) / math.sqrt(1 - r * r)
        # Approximate two-tailed p-value using normal approximation
        # (good enough for n > 30; conservative for smaller n)
        p = 2.0 * (1.0 - _normal_cdf(abs(t_stat)))

    return r, p


def _normal_cdf(z: float) -> float:
    """Approximate standard normal CDF using error function."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _interpret_r(r: float, p: float, metric_id: str, outcome: str) -> Tuple[str, str, str]:
    """Interpret a correlation coefficient.

    Returns (interpretation, direction, strength).
    """
    if abs(r) < 0.1 or p > 0.1:
        return f"No meaningful correlation between {metric_id} and {outcome}.", "none", "none"

    direction = "positive" if r > 0 else "negative"
    abs_r = abs(r)

    if abs_r >= 0.7:
        strength = "strong"
    elif abs_r >= 0.4:
        strength = "moderate"
    else:
        strength = "weak"

    sign_word = "higher" if r > 0 else "lower"
    outcome_word = "higher" if outcome == "external_quality_score" else "lower"
    if outcome == "cycle_time_minutes":
        # Lower cycle time is better, so negative r is "good"
        good = r < 0
        quality_word = "better" if good else "worse"
        interp = f"{strength.capitalize()} {direction} correlation: higher {metric_id} → {quality_word} {outcome}."
    elif outcome == "external_quality_score":
        good = r > 0
        quality_word = "better" if good else "worse"
        interp = f"{strength.capitalize()} {direction} correlation: higher {metric_id} → {quality_word} {outcome}."
    else:
        interp = f"{strength.capitalize()} {direction} correlation between {metric_id} and {outcome}."

    return interp, direction, strength


def compute_outcome_correlation(
    # List of (micro_eval_dict, outcome_dict) pairs from lineages
    lineage_outcomes: List[Tuple[dict, dict]],
    metric_ids: Optional[List[str]] = None,
) -> OutcomeCorrelationResult:
    """Correlate micro_eval metrics with outcome metrics through lineage.

    Args:
        lineage_outcomes: List of (micro_eval, outcome) pairs where
            micro_eval is the dict from Lineage.micro_eval and outcome
            is the dict from Outcome.to_dict().
        metric_ids: If provided, only correlate these metrics.
            Otherwise, use all metrics found in micro_eval dicts.

    Returns:
        OutcomeCorrelationResult with all correlations.

    All results are labeled ASSOCIATION with evidence grade OBSERVATIONAL.
    """
    # Filter to lineages that have both micro_eval and outcome data
    valid: List[Tuple[dict, dict]] = []
    for me, out in lineage_outcomes:
        if me and out:
            qs = out.get("external_quality_score")
            ct = out.get("cycle_time_minutes")
            if qs is not None or ct is not None:
                valid.append((me, out))

    if len(valid) < 3:
        return OutcomeCorrelationResult(
            correlations=[],
            operators_analyzed=len(valid),
            lineages_with_outcomes=len(valid),
            evidence_grade="OBSERVATIONAL",
            claim_status="ASSOCIATION",
            summary="Insufficient data for correlation analysis — need at least 3 lineages with outcomes.",
        )

    # Determine metric set
    if metric_ids is None:
        all_metrics: set = set()
        for me, _ in valid:
            all_metrics.update(k for k, v in me.items() if isinstance(v, (int, float)))
        metric_ids = sorted(all_metrics)

    # Extract outcome series
    quality_scores = [out.get("external_quality_score") for _, out in valid]
    cycle_times = [out.get("cycle_time_minutes") for _, out in valid]

    correlations: List[MetricOutcomeCorrelation] = []

    for mid in metric_ids:
        # Quality score correlation
        q_vals = [me.get(mid) for me, _ in valid]
        q_pairs = [(m, q) for m, q in zip(q_vals, quality_scores) if m is not None and q is not None]
        if len(q_pairs) >= 3:
            xs = [p[0] for p in q_pairs]
            ys = [p[1] for p in q_pairs]
            r, p = _pearson_r(xs, ys)
            interp, direction, strength = _interpret_r(r, p, mid, "external_quality_score")
            correlations.append(MetricOutcomeCorrelation(
                metric_id=mid,
                outcome_metric="external_quality_score",
                correlation=r,
                p_value_approx=p,
                sample_size=len(q_pairs),
                interpretation=interp,
                direction=direction,
                strength=strength,
            ))

        # Cycle time correlation
        c_vals = [me.get(mid) for me, _ in valid]
        c_pairs = [(m, c) for m, c in zip(c_vals, cycle_times) if m is not None and c is not None]
        if len(c_pairs) >= 3:
            xs = [p[0] for p in c_pairs]
            ys = [p[1] for p in c_pairs]
            r, p = _pearson_r(xs, ys)
            interp, direction, strength = _interpret_r(r, p, mid, "cycle_time_minutes")
            correlations.append(MetricOutcomeCorrelation(
                metric_id=mid,
                outcome_metric="cycle_time_minutes",
                correlation=r,
                p_value_approx=p,
                sample_size=len(c_pairs),
                interpretation=interp,
                direction=direction,
                strength=strength,
            ))

    # Summary
    if not correlations:
        summary = "No correlations computed — insufficient paired data."
    else:
        strong = [c for c in correlations if c.strength == "strong"]
        moderate = [c for c in correlations if c.strength == "moderate"]
        summary = (
            f"Computed {len(correlations)} correlations across {len(metric_ids)} metrics "
            f"and 2 outcome measures. "
            f"{len(strong)} strong, {len(moderate)} moderate. "
            f"All results are ASSOCIATION (observational), not causation."
        )

    return OutcomeCorrelationResult(
        correlations=correlations,
        operators_analyzed=len(valid),
        lineages_with_outcomes=len(valid),
        evidence_grade="OBSERVATIONAL",
        claim_status="ASSOCIATION",
        summary=summary,
    )
