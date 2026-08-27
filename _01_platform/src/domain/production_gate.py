"""Production gates — threshold-based routing for operator review.

Per MO§ES™ enterprise pilot readiness framework: "score < threshold → senior review" concept.
This module provides the gate evaluation logic that flags operators whose
metrics fall below (or above) a configured threshold for routing decisions.

Gates are NOT personnel decisions. They are workflow routing rules:
- Flag for senior review (not block, not penalize)
- Route to intervention queue
- Trigger a quality check

Every gate result carries a DEVELOPMENTAL decision-use label.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from .measurement import Measurement


class GateAction(str, Enum):
    """What happens when a gate fires."""
    FLAG_FOR_REVIEW = "FLAG_FOR_REVIEW"
    ROUTE_TO_INTERVENTION = "ROUTE_TO_INTERVENTION"
    BLOCK_PRODUCTION = "BLOCK_PRODUCTION"
    NOTIFY = "NOTIFY"


class GateDirection(str, Enum):
    """Which direction triggers the gate."""
    below = "below"
    above = "above"


@dataclass(frozen=True, slots=True)
class GateRule:
    """A single threshold rule for one metric.

    Example: leverage below 10th percentile → flag for review.
    """
    rule_id: str
    metric_id: str
    threshold: float
    direction: GateDirection
    action: GateAction
    description: str = ""
    is_percentile: bool = True


@dataclass(frozen=True, slots=True)
class GateResult:
    """The outcome of evaluating a gate rule against an operator."""
    rule_id: str
    operator_id: str
    metric_id: str
    metric_value: Optional[float]
    threshold: float
    direction: GateDirection
    action: GateAction
    fired: bool
    reason: str
    decision_use: str = "DEVELOPMENTAL"

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "operator_id": self.operator_id,
            "metric_id": self.metric_id,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "direction": self.direction.value,
            "action": self.action.value,
            "fired": self.fired,
            "reason": self.reason,
            "decision_use": self.decision_use,
        }


DEFAULT_GATE_RULES: List[GateRule] = [
    GateRule(
        rule_id="GATE-001",
        metric_id="leverage",
        threshold=10,
        direction=GateDirection.below,
        action=GateAction.FLAG_FOR_REVIEW,
        description="Low leverage — operator extracts little value per input token. Flag for coaching review.",
    ),
    GateRule(
        rule_id="GATE-002",
        metric_id="yield",
        threshold=10,
        direction=GateDirection.below,
        action=GateAction.ROUTE_TO_INTERVENTION,
        description="Low yield — operator discards most model output. Route to intervention queue.",
    ),
    GateRule(
        rule_id="GATE-003",
        metric_id="construction",
        threshold=25,
        direction=GateDirection.below,
        action=GateAction.NOTIFY,
        description="Low context construction — operator re-prompts from scratch. Notify team lead.",
    ),
]


def evaluate_gate(
    rule: GateRule,
    operator_id: str,
    measurements: List[Measurement],
    percentile_lookup: Optional[Dict[str, float]] = None,
) -> GateResult:
    """Evaluate a single gate rule against an operator's measurements.

    Args:
        rule: The gate rule to evaluate.
        operator_id: The operator being evaluated.
        measurements: The operator's canonical measurements.
        percentile_lookup: Optional dict mapping metric_id → absolute value
            at the threshold percentile. If provided, the threshold is
            interpreted as a percentile and the lookup provides the absolute
            value. If not provided, the threshold is treated as absolute.

    Returns:
        A GateResult indicating whether the gate fired.
    """
    # Find the metric value for this rule
    metric_value = None
    for m in measurements:
        if m.metric_id == rule.metric_id and m.value is not None:
            metric_value = m.value
            break

    if metric_value is None:
        return GateResult(
            rule_id=rule.rule_id,
            operator_id=operator_id,
            metric_id=rule.metric_id,
            metric_value=None,
            threshold=rule.threshold,
            direction=rule.direction,
            action=rule.action,
            fired=False,
            reason=f"metric {rule.metric_id} not available or null",
        )

    # Resolve percentile threshold to absolute value if lookup is provided
    effective_threshold = rule.threshold
    if rule.is_percentile and percentile_lookup:
        effective_threshold = percentile_lookup.get(rule.metric_id, rule.threshold)

    # Evaluate the gate
    if rule.direction == GateDirection.below:
        fired = metric_value < effective_threshold
        comparison = "<" if fired else ">="
    else:
        fired = metric_value > effective_threshold
        comparison = ">" if fired else "<="

    reason = (
        f"{rule.metric_id}={metric_value:.2f} {comparison} threshold {effective_threshold:.2f}"
        if fired else
        f"{rule.metric_id}={metric_value:.2f} {comparison} threshold {effective_threshold:.2f}"
    )

    return GateResult(
        rule_id=rule.rule_id,
        operator_id=operator_id,
        metric_id=rule.metric_id,
        metric_value=metric_value,
        threshold=effective_threshold,
        direction=rule.direction,
        action=rule.action,
        fired=fired,
        reason=reason,
    )


def evaluate_all_gates(
    operator_id: str,
    measurements: List[Measurement],
    rules: Optional[List[GateRule]] = None,
    percentile_lookup: Optional[Dict[str, float]] = None,
) -> List[GateResult]:
    """Evaluate all gate rules for an operator.

    Returns all results (fired and not fired). Callers can filter
    on `fired=True` to get only the gates that triggered.
    """
    active_rules = rules if rules is not None else DEFAULT_GATE_RULES
    return [
        evaluate_gate(rule, operator_id, measurements, percentile_lookup)
        for rule in active_rules
    ]


def evaluate_cohort_gates(
    operator_ids: List[str],
    measurements_by_operator: Dict[str, List[Measurement]],
    rules: Optional[List[GateRule]] = None,
    percentile_lookup: Optional[Dict[str, float]] = None,
) -> Dict[str, List[GateResult]]:
    """Evaluate gates for an entire cohort.

    Returns a dict mapping operator_id → list of GateResult.
    """
    return {
        oid: evaluate_all_gates(oid, measurements_by_operator.get(oid, []), rules, percentile_lookup)
        for oid in operator_ids
    }


def summarize_gates(results: Dict[str, List[GateResult]]) -> dict:
    """Summarize gate results across a cohort.

    Returns counts by action and a list of fired gates.
    """
    all_results = [r for results_list in results.values() for r in results_list]
    fired = [r for r in all_results if r.fired]
    by_action: Dict[str, int] = {}
    for r in fired:
        by_action[r.action.value] = by_action.get(r.action.value, 0) + 1
    return {
        "total_evaluations": len(all_results),
        "total_fired": len(fired),
        "operators_flagged": len({r.operator_id for r in fired}),
        "by_action": by_action,
        "fired_gates": [r.to_dict() for r in fired],
        "decision_use": "DEVELOPMENTAL",
        "label": "GATES — workflow routing, not personnel decisions",
    }
