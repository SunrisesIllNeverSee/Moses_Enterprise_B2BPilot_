"""Composite Employee Score — a developmental roll-up of canonical metrics.

Per `21` §8 "do not build yet" list: "one proprietary composite employee
score." This module implements it with governance guardrails.

The composite score combines the four canonical metrics into a single
0–100 developmental score using reference-population percentiles:

    leverage     (R/I)           — 30% weight
    yield        (R*O)/(I^2)     — 30% weight
    token_snr    O/(I+O)         — 20% weight
    construction W/R              — 20% weight

Each metric is normalized to 0–100 using the reference population's
percentile distribution (p0→0, p100→100, linear interpolation between
known percentile points). The weighted sum produces the composite.

Governance guardrails (per `12` §Development doctrine + §Avoid-list):
- Label: DEVELOPMENTAL — never PERSONNEL
- No punitive labels: the score is framed as "development index," not
  "performance rating"
- No bottom-employee leaderboard: scores can be sorted descending for
  development-group identification, but the product must never surface
  a worst-to-best ranking
- No automatic adverse actions: the score must never trigger personnel
  decisions without separate governance approval
- Interpretation limits: token_snr and construction are
  CANONICAL_WITH_INTERPRETATION_LIMIT — the composite carries this caveat
- Unresolved metrics (velocity, compression_operating_ratio, stability)
  are NOT included — they have status NEEDS_CANONICAL_LOCK and no formula
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from domain import Measurement, ReferencePopulation


# Weights for each canonical metric in the composite.
# Only CANONICAL and CANONICAL_WITH_INTERPRETATION_LIMIT metrics are included.
# NEEDS_CANONICAL_LOCK metrics (velocity, compression, stability) are excluded.
METRIC_WEIGHTS: Dict[str, float] = {
    "leverage": 0.30,
    "yield": 0.30,
    "token_snr": 0.20,
    "construction": 0.20,
}

# Metrics with interpretation limits (per metric registry status)
INTERPRETATION_LIMIT_METRICS = {"token_snr", "construction"}

# The composite score name and label
COMPOSITE_NAME = "AI Operator Development Index"
COMPOSITE_ID = "dev_index"
COMPOSITE_LABEL = "DEVELOPMENTAL — for development use; not a personnel performance rating"


@dataclass(frozen=True, slots=True)
class CompositeScore:
    """A single operator's composite developmental score.

    Attributes:
        operator_id: The operator this score belongs to.
        score: 0–100 composite score (weighted percentile-normalized sum).
        components: Per-metric breakdown (metric_id → {value, percentile, normalized, weight}).
        label: Governance label (always DEVELOPMENTAL).
        caveats: Interpretation caveats from CANONICAL_WITH_INTERPRETATION_LIMIT metrics.
        synthetic: Whether this score is based on synthetic data.
    """
    operator_id: str
    score: float
    components: Dict[str, dict] = field(default_factory=dict)
    label: str = COMPOSITE_LABEL
    caveats: List[str] = field(default_factory=list)
    synthetic: bool = False

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "score": round(self.score, 2),
            "score_id": COMPOSITE_ID,
            "name": COMPOSITE_NAME,
            "components": dict(self.components),
            "label": self.label,
            "caveats": list(self.caveats),
            "synthetic": self.synthetic,
        }


def _normalize_via_percentile(
    value: Optional[float],
    reference: "ReferencePopulation",
    metric_id: str,
) -> Optional[float]:
    """Normalize a metric value to 0–100 using the reference percentile.

    Uses the reference population's percentile distribution to map the
    raw metric value to a 0–100 scale. Linear interpolation between
    known percentile points (p0, p10, p25, p50, p75, p90, p100).
    """
    if value is None:
        return None
    percentile = reference.percentile(metric_id, value)
    if percentile is None:
        return None
    return percentile  # already 0–100


def compute_composite_score(
    operator_id: str,
    measurements: List["Measurement"],
    reference: "ReferencePopulation",
    synthetic: bool = False,
) -> CompositeScore:
    """Compute the composite developmental score for an operator.

    Args:
        operator_id: The operator ID.
        measurements: The operator's canonical measurements (from ScoringEngine).
        reference: The reference population for percentile normalization.
        synthetic: Whether the data is synthetic.

    Returns:
        CompositeScore with the 0–100 score and per-metric breakdown.
    """
    ms_by_id = {m.metric_id: m for m in measurements}
    components: Dict[str, dict] = {}
    caveats: List[str] = []
    weighted_sum = 0.0
    total_weight_used = 0.0

    for metric_id, weight in METRIC_WEIGHTS.items():
        m = ms_by_id.get(metric_id)
        if m is None or m.value is None:
            components[metric_id] = {
                "value": None,
                "percentile": None,
                "normalized": None,
                "weight": weight,
                "status": "missing",
            }
            continue

        normalized = _normalize_via_percentile(m.value, reference, metric_id)
        if normalized is None:
            components[metric_id] = {
                "value": m.value,
                "percentile": None,
                "normalized": None,
                "weight": weight,
                "status": m.status.value if hasattr(m.status, 'value') else str(m.status),
            }
            continue

        weighted_sum += normalized * weight
        total_weight_used += weight

        components[metric_id] = {
            "value": round(m.value, 6) if m.value is not None else None,
            "percentile": round(normalized, 2),
            "normalized": round(normalized, 2),
            "weight": weight,
            "status": m.status.value if hasattr(m.status, 'value') else str(m.status),
        }

        if metric_id in INTERPRETATION_LIMIT_METRICS:
            caveats.append(
                f"{metric_id} has CANONICAL_WITH_INTERPRETATION_LIMIT status — "
                f"interpret with caution; context-dependent metric."
            )

    # If some metrics are missing, renormalize the weights of available metrics
    if total_weight_used > 0 and total_weight_used < 1.0:
        score = (weighted_sum / total_weight_used) * 100
        caveats.append(
            f"Score based on {total_weight_used:.0%} of available metrics — "
            f"some canonical metrics were missing or uncomputable."
        )
    elif total_weight_used == 0:
        score = 0.0
        caveats.append("No canonical metrics available — score is 0 (insufficient data).")
    else:
        score = weighted_sum

    return CompositeScore(
        operator_id=operator_id,
        score=score,
        components=components,
        caveats=caveats,
        synthetic=synthetic,
    )


def compute_cohort_composite_scores(
    operator_ids: List[str],
    cohort_measurements: Dict[str, List["Measurement"]],
    reference: "ReferencePopulation",
    synthetic: bool = False,
) -> Dict[str, CompositeScore]:
    """Compute composite scores for all operators in a cohort.

    Returns a dict of operator_id → CompositeScore. Does NOT sort or
    rank — per governance avoid-list, the caller must not surface a
    worst-to-best leaderboard.
    """
    return {
        oid: compute_composite_score(
            oid, cohort_measurements.get(oid, []), reference, synthetic
        )
        for oid in operator_ids
    }


def composite_score_summary(
    scores: Dict[str, CompositeScore],
) -> dict:
    """Summarize composite scores across a cohort (aggregate, not individual ranking).

    Returns distribution statistics (min, max, median, mean, quartiles)
    without exposing individual operator rankings. Per governance: this
    is for cohort-level development planning, not individual evaluation.
    """
    values = sorted(s.score for s in scores.values() if s.score is not None)
    if not values:
        return {
            "count": 0,
            "min": None, "max": None, "median": None, "mean": None,
            "q1": None, "q3": None,
        }
    n = len(values)
    median = values[n // 2] if n % 2 == 1 else (values[n // 2 - 1] + values[n // 2]) / 2
    q1 = values[n // 4] if n >= 4 else values[0]
    q3 = values[3 * n // 4] if n >= 4 else values[-1]
    return {
        "count": n,
        "min": round(values[0], 2),
        "max": round(values[-1], 2),
        "median": round(median, 2),
        "mean": round(sum(values) / n, 2),
        "q1": round(q1, 2),
        "q3": round(q3, 2),
    }
