"""GateRecord — pilot-level decision gate records.

Per `pilot/governance/DECISION_GATES.md`: three formal decision gates
govern the pilot lifecycle. These are DISTINCT from operator-level
routing gates (`production_gate.py`).

    Gate 1 — LAUNCH READINESS: LAUNCH / LAUNCH_WITH_CONDITIONS / DEFER / DECLINE
    Gate 2 — PILOT HEALTH:     CONTINUE / ADJUST / ESCALATE / TERMINATE
    Gate 3 — CLOSURE / SCALE:   STOP / EXTEND / EXPAND / DEPLOY

Both layers coexist:
    - Pilot-level gates (this module): govern the pilot lifecycle.
    - Operator-level gates (production_gate.py): route individual operators.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from .success_criteria import CriteriaEvaluation


class GateType(str, Enum):
    """Which pilot-level decision gate."""
    GATE_1_LAUNCH_READINESS = "GATE_1_LAUNCH_READINESS"
    GATE_2_PILOT_HEALTH = "GATE_2_PILOT_HEALTH"
    GATE_3_CLOSURE_SCALE = "GATE_3_CLOSURE_SCALE"


class Gate1Outcome(str, Enum):
    """Outcomes for Gate 1 — Launch Readiness."""
    LAUNCH = "LAUNCH"
    LAUNCH_WITH_CONDITIONS = "LAUNCH_WITH_CONDITIONS"
    DEFER = "DEFER"
    DECLINE = "DECLINE"


class Gate2Outcome(str, Enum):
    """Outcomes for Gate 2 — Pilot Health."""
    CONTINUE = "CONTINUE"
    ADJUST = "ADJUST"
    ESCALATE = "ESCALATE"
    TERMINATE = "TERMINATE"


class Gate3Outcome(str, Enum):
    """Outcomes for Gate 3 — Closure / Scale."""
    STOP = "STOP"
    EXTEND = "EXTEND"
    EXPAND = "EXPAND"
    DEPLOY = "DEPLOY"


@dataclass(frozen=True, slots=True)
class ExtendRequirements:
    """Required fields for an EXTEND outcome (Gate 3).

    Per DECISION_GATES.md: no indefinite pilot state. Every EXTEND must
    have a bounded extension and a new closure date.
    """
    reason: str
    missing_evidence: str
    new_evidence_requirement: str
    extension_period_days: int
    new_closure_date: str

    def to_dict(self) -> dict:
        return {
            "reason": self.reason,
            "missing_evidence": self.missing_evidence,
            "new_evidence_requirement": self.new_evidence_requirement,
            "extension_period_days": self.extension_period_days,
            "new_closure_date": self.new_closure_date,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ExtendRequirements":
        return cls(
            reason=d["reason"],
            missing_evidence=d["missing_evidence"],
            new_evidence_requirement=d["new_evidence_requirement"],
            extension_period_days=d["extension_period_days"],
            new_closure_date=d["new_closure_date"],
        )


@dataclass(frozen=True, slots=True)
class GateRecord:
    """A formal pilot-level decision gate record.

    Immutable once created. Preserves owner, evidence, rationale,
    disposition, timestamp, and required follow-up.
    """
    gate_id: str
    pilot_id: str
    gate_type: GateType
    outcome: str  # Gate1Outcome / Gate2Outcome / Gate3Outcome value
    rationale: str
    evaluated_at: str
    evaluated_by: str
    conditions: List[str] = field(default_factory=list)
    criteria_evaluation: Optional[Dict] = None  # Gate 3 only
    extend_requirements: Optional[ExtendRequirements] = None  # Gate 3 EXTEND only
    evidence_cited: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "gate_id": self.gate_id,
            "pilot_id": self.pilot_id,
            "gate_type": self.gate_type.value,
            "outcome": self.outcome,
            "rationale": self.rationale,
            "evaluated_at": self.evaluated_at,
            "evaluated_by": self.evaluated_by,
            "conditions": list(self.conditions),
            "criteria_evaluation": self.criteria_evaluation,
            "extend_requirements": self.extend_requirements.to_dict() if self.extend_requirements else None,
            "evidence_cited": list(self.evidence_cited),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GateRecord":
        return cls(
            gate_id=d["gate_id"],
            pilot_id=d["pilot_id"],
            gate_type=GateType(d["gate_type"]),
            outcome=d["outcome"],
            rationale=d.get("rationale", ""),
            evaluated_at=d.get("evaluated_at", ""),
            evaluated_by=d.get("evaluated_by", ""),
            conditions=list(d.get("conditions", [])),
            criteria_evaluation=d.get("criteria_evaluation"),
            extend_requirements=ExtendRequirements.from_dict(d["extend_requirements"]) if d.get("extend_requirements") else None,
            evidence_cited=list(d.get("evidence_cited", [])),
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def evaluate_gate_1(
    pilot_id: str,
    evaluated_by: str,
    charter_valid: bool,
    success_criteria_locked: bool,
    population_bounded: bool,
    duration_bounded: bool,
    governance_cleared: bool,
    authorized: bool,
    instrumentable: bool = True,
    conditions: Optional[List[str]] = None,
    rationale: str = "",
) -> GateRecord:
    """Evaluate Gate 1 — Launch Readiness.

    Returns LAUNCH if all criteria met, LAUNCH_WITH_CONDITIONS if minor
    gaps with conditions, DEFER if gaps must be addressed, DECLINE if
    fundamental issues.
    """
    gate_id = f"GATE1-{pilot_id}"
    all_met = all([
        charter_valid, success_criteria_locked, population_bounded,
        duration_bounded, governance_cleared, authorized, instrumentable,
    ])
    if all_met:
        outcome = Gate1Outcome.LAUNCH.value
    elif charter_valid and population_bounded and duration_bounded and conditions:
        outcome = Gate1Outcome.LAUNCH_WITH_CONDITIONS.value
    elif charter_valid:
        outcome = Gate1Outcome.DEFER.value
    else:
        outcome = Gate1Outcome.DECLINE.value

    if not rationale:
        failed = []
        if not charter_valid: failed.append("charter not valid")
        if not success_criteria_locked: failed.append("success criteria not locked")
        if not population_bounded: failed.append("population not bounded")
        if not duration_bounded: failed.append("duration not bounded")
        if not governance_cleared: failed.append("governance not cleared")
        if not authorized: failed.append("not authorized")
        if not instrumentable: failed.append("not instrumentable")
        rationale = f"Gate 1 evaluation: {outcome}. Issues: {', '.join(failed) or 'none'}."

    return GateRecord(
        gate_id=gate_id,
        pilot_id=pilot_id,
        gate_type=GateType.GATE_1_LAUNCH_READINESS,
        outcome=outcome,
        rationale=rationale,
        evaluated_at=_now(),
        evaluated_by=evaluated_by,
        conditions=list(conditions or []),
    )


def evaluate_gate_2(
    pilot_id: str,
    evaluated_by: str,
    data_sufficient: bool,
    no_blocking_quality: bool,
    participation_ok: bool,
    governance_ok: bool,
    protocol_ok: bool,
    rationale: str = "",
) -> GateRecord:
    """Evaluate Gate 2 — Pilot Health.

    Returns CONTINUE if healthy, ADJUST if minor issues, ESCALATE if
    significant issues requiring authority, TERMINATE if no longer valid.
    """
    gate_id = f"GATE2-{pilot_id}"
    all_ok = all([data_sufficient, no_blocking_quality, participation_ok, governance_ok, protocol_ok])
    if all_ok:
        outcome = Gate2Outcome.CONTINUE.value
    elif governance_ok and data_sufficient:
        outcome = Gate2Outcome.ADJUST.value
    elif governance_ok:
        outcome = Gate2Outcome.ESCALATE.value
    else:
        outcome = Gate2Outcome.TERMINATE.value

    if not rationale:
        issues = []
        if not data_sufficient: issues.append("data insufficient")
        if not no_blocking_quality: issues.append("blocking quality issues")
        if not participation_ok: issues.append("participation below threshold")
        if not governance_ok: issues.append("governance concern")
        if not protocol_ok: issues.append("protocol deviation")
        rationale = f"Gate 2 evaluation: {outcome}. Issues: {', '.join(issues) or 'none'}."

    return GateRecord(
        gate_id=gate_id,
        pilot_id=pilot_id,
        gate_type=GateType.GATE_2_PILOT_HEALTH,
        outcome=outcome,
        rationale=rationale,
        evaluated_at=_now(),
        evaluated_by=evaluated_by,
    )


def evaluate_gate_3(
    pilot_id: str,
    evaluated_by: str,
    criteria_eval: CriteriaEvaluation,
    rationale: str = "",
    extend_requirements: Optional[ExtendRequirements] = None,
) -> GateRecord:
    """Evaluate Gate 3 — Closure / Scale.

    Uses the success criteria evaluation to determine STOP / EXTEND /
    EXPAND / DEPLOY.

    Per DECISION_GATES.md aggregation:
        All MET → DEPLOY or EXPAND
        Majority MET, minority PARTIAL → EXPAND or EXTEND
        Majority PARTIAL or mixed → EXTEND
        Majority MISSED → STOP or EXTEND
        Critical criterion MISSED → STOP
    """
    gate_id = f"GATE3-{pilot_id}"

    if criteria_eval.all_met:
        outcome = Gate3Outcome.DEPLOY.value
    elif criteria_eval.majority_met:
        outcome = Gate3Outcome.EXPAND.value
    elif criteria_eval.majority_missed:
        outcome = Gate3Outcome.STOP.value
    else:
        outcome = Gate3Outcome.EXTEND.value

    # EXTEND requires extend_requirements
    if outcome == Gate3Outcome.EXTEND.value and not extend_requirements:
        raise ValueError(
            "EXTEND outcome requires extend_requirements "
            "(reason, missing_evidence, new_evidence_requirement, "
            "extension_period_days, new_closure_date)."
        )

    if not rationale:
        rationale = (
            f"Gate 3 evaluation: {outcome}. "
            f"Criteria: {criteria_eval.summary}. "
            f"All met={criteria_eval.all_met}, majority_met={criteria_eval.majority_met}, "
            f"majority_missed={criteria_eval.majority_missed}."
        )

    return GateRecord(
        gate_id=gate_id,
        pilot_id=pilot_id,
        gate_type=GateType.GATE_3_CLOSURE_SCALE,
        outcome=outcome,
        rationale=rationale,
        evaluated_at=_now(),
        evaluated_by=evaluated_by,
        criteria_evaluation=criteria_eval.to_dict(),
        extend_requirements=extend_requirements,
    )
