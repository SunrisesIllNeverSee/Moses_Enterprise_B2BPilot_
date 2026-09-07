"""SuccessCriteria — locked success criteria for a pilot.

Per `pilot/governance/SUCCESS_CRITERIA.md` and the build plan T1.2:
success criteria must be locked before measurement (before BASELINE).
Gate 3 evaluates each criterion as MET / MISSED / PARTIAL against the
locked set.

Criteria are tiered:
    - global: apply to all pilots
    - template: apply to a commercial pilot template
    - customer: defined by the customer for this specific pilot
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class CriterionDirection(str, Enum):
    """Which direction satisfies the criterion."""
    at_least = "at_least"   # value >= threshold
    at_most = "at_most"     # value <= threshold
    equals = "equals"       # value == threshold


class CriterionAggregation(str, Enum):
    """How to aggregate the metric across the cohort."""
    median = "median"
    mean = "mean"
    percentile_25 = "percentile_25"
    percentile_75 = "percentile_75"
    count = "count"
    fraction = "fraction"   # fraction of operators meeting a sub-threshold


class CriterionTier(str, Enum):
    """Which tier a success criterion belongs to."""
    global_ = "global"
    template = "template"
    customer = "customer"


class CriterionStatus(str, Enum):
    """The evaluation result for a single criterion."""
    MET = "MET"
    MISSED = "MISSED"
    PARTIAL = "PARTIAL"
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass(frozen=True, slots=True)
class SuccessCriterion:
    """A single success criterion for a pilot.

    Example: "At least 90% usable cohort telemetry" →
        metric="eligible_fraction", threshold=0.90, direction=at_least,
        aggregation=fraction.
    """
    criterion_id: str
    metric: str
    threshold: float
    direction: CriterionDirection
    aggregation: CriterionAggregation
    rationale: str = ""
    tier: CriterionTier = CriterionTier.customer
    closure_mapping: str = ""  # which closure outcome this criterion informs
    tolerance_band: float = 0.0  # for PARTIAL evaluation (within this band of threshold)

    def to_dict(self) -> dict:
        return {
            "criterion_id": self.criterion_id,
            "metric": self.metric,
            "threshold": self.threshold,
            "direction": self.direction.value,
            "aggregation": self.aggregation.value,
            "rationale": self.rationale,
            "tier": self.tier.value,
            "closure_mapping": self.closure_mapping,
            "tolerance_band": self.tolerance_band,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SuccessCriterion":
        return cls(
            criterion_id=d["criterion_id"],
            metric=d["metric"],
            threshold=d["threshold"],
            direction=CriterionDirection(d.get("direction", "at_least")),
            aggregation=CriterionAggregation(d.get("aggregation", "median")),
            rationale=d.get("rationale", ""),
            tier=CriterionTier(d.get("tier", "customer")),
            closure_mapping=d.get("closure_mapping", ""),
            tolerance_band=d.get("tolerance_band", 0.0),
        )


@dataclass(frozen=True, slots=True)
class SuccessCriteria:
    """The locked set of success criteria for a pilot.

    Once locked (locked_at is set), the criteria list is immutable.
    Gate 3 evaluates against this locked set.
    """
    criteria: List[SuccessCriterion] = field(default_factory=list)
    locked_at: str = ""
    locked_by: str = ""

    @property
    def is_locked(self) -> bool:
        return bool(self.locked_at)

    def to_dict(self) -> dict:
        return {
            "criteria": [c.to_dict() for c in self.criteria],
            "locked_at": self.locked_at,
            "locked_by": self.locked_by,
            "is_locked": self.is_locked,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SuccessCriteria":
        return cls(
            criteria=[SuccessCriterion.from_dict(c) for c in d.get("criteria", [])],
            locked_at=d.get("locked_at", ""),
            locked_by=d.get("locked_by", ""),
        )

    @classmethod
    def unlocked(cls, criteria: List[SuccessCriterion]) -> "SuccessCriteria":
        """Create an unlocked set of criteria."""
        return cls(criteria=criteria)

    def lock(self, locked_by: str) -> "SuccessCriteria":
        """Return a new locked SuccessCriteria.

        Raises if already locked.
        """
        if self.is_locked:
            raise ValueError("Success criteria are already locked — cannot re-lock.")
        ts = datetime.now(timezone.utc).isoformat()
        return SuccessCriteria(
            criteria=list(self.criteria),
            locked_at=ts,
            locked_by=locked_by,
        )


@dataclass(frozen=True, slots=True)
class CriterionResult:
    """The evaluation result for a single criterion against measured data."""
    criterion_id: str
    status: CriterionStatus
    measured_value: Optional[float]
    threshold: float
    direction: CriterionDirection
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "criterion_id": self.criterion_id,
            "status": self.status.value,
            "measured_value": self.measured_value,
            "threshold": self.threshold,
            "direction": self.direction.value,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class CriteriaEvaluation:
    """The full evaluation of all success criteria for Gate 3."""
    results: List[CriterionResult]
    met_count: int
    missed_count: int
    partial_count: int
    not_evaluated_count: int
    summary: str

    def to_dict(self) -> dict:
        return {
            "results": [r.to_dict() for r in self.results],
            "met_count": self.met_count,
            "missed_count": self.missed_count,
            "partial_count": self.partial_count,
            "not_evaluated_count": self.not_evaluated_count,
            "summary": self.summary,
        }

    @property
    def all_met(self) -> bool:
        return self.missed_count == 0 and self.partial_count == 0 and self.met_count > 0

    @property
    def majority_met(self) -> bool:
        total = self.met_count + self.missed_count + self.partial_count
        return total > 0 and self.met_count > total / 2

    @property
    def majority_missed(self) -> bool:
        total = self.met_count + self.missed_count + self.partial_count
        return total > 0 and self.missed_count > total / 2


def evaluate_criterion(
    criterion: SuccessCriterion,
    measured_value: Optional[float],
) -> CriterionResult:
    """Evaluate a single criterion against a measured value.

    Returns MET, MISSED, or PARTIAL based on the threshold, direction,
    and tolerance band.
    """
    if measured_value is None:
        return CriterionResult(
            criterion_id=criterion.criterion_id,
            status=CriterionStatus.NOT_EVALUATED,
            measured_value=None,
            threshold=criterion.threshold,
            direction=criterion.direction,
            rationale="No measured value available.",
        )

    if criterion.direction == CriterionDirection.at_least:
        if measured_value >= criterion.threshold:
            status = CriterionStatus.MET
        elif measured_value >= criterion.threshold - criterion.tolerance_band:
            status = CriterionStatus.PARTIAL
        else:
            status = CriterionStatus.MISSED
    elif criterion.direction == CriterionDirection.at_most:
        if measured_value <= criterion.threshold:
            status = CriterionStatus.MET
        elif measured_value <= criterion.threshold + criterion.tolerance_band:
            status = CriterionStatus.PARTIAL
        else:
            status = CriterionStatus.MISSED
    else:  # equals
        if abs(measured_value - criterion.threshold) <= criterion.tolerance_band:
            status = CriterionStatus.MET
        elif abs(measured_value - criterion.threshold) <= criterion.tolerance_band * 2:
            status = CriterionStatus.PARTIAL
        else:
            status = CriterionStatus.MISSED

    return CriterionResult(
        criterion_id=criterion.criterion_id,
        status=status,
        measured_value=measured_value,
        threshold=criterion.threshold,
        direction=criterion.direction,
        rationale=f"{criterion.metric}={measured_value:.4f} vs threshold {criterion.threshold} ({criterion.direction.value})",
    )


def evaluate_criteria(
    criteria: SuccessCriteria,
    measured_values: dict,
) -> CriteriaEvaluation:
    """Evaluate all locked success criteria against measured values.

    Args:
        criteria: The locked SuccessCriteria set.
        measured_values: dict mapping criterion_id → measured value (float or None).

    Returns:
        CriteriaEvaluation with per-criterion results and aggregate counts.
    """
    if not criteria.is_locked:
        raise ValueError("Cannot evaluate unlocked success criteria — lock first.")

    results: List[CriterionResult] = []
    for c in criteria.criteria:
        val = measured_values.get(c.criterion_id)
        results.append(evaluate_criterion(c, val))

    met = sum(1 for r in results if r.status == CriterionStatus.MET)
    missed = sum(1 for r in results if r.status == CriterionStatus.MISSED)
    partial = sum(1 for r in results if r.status == CriterionStatus.PARTIAL)
    not_eval = sum(1 for r in results if r.status == CriterionStatus.NOT_EVALUATED)

    summary = f"{met} MET, {partial} PARTIAL, {missed} MISSED, {not_eval} NOT_EVALUATED"

    return CriteriaEvaluation(
        results=results,
        met_count=met,
        missed_count=missed,
        partial_count=partial,
        not_evaluated_count=not_eval,
        summary=summary,
    )
