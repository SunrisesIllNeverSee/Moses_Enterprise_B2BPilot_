"""DecisionRecord — the immutable closure decision for a pilot.

Per `pilot/governance/CLOSURE_OUTCOMES.md` and build plan T1.4: a pilot
must terminate in an explicit decision: STOP, EXTEND, EXPAND, or DEPLOY.

The decision record is immutable once created. It references the Gate 3
record that produced the closure outcome and carries outcome-specific
plans (extend plan, expand plan, deploy plan, stop lessons).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class ClosureOutcome(str, Enum):
    """The four valid closure outcomes for a pilot."""
    STOP = "STOP"
    EXTEND = "EXTEND"
    EXPAND = "EXPAND"
    DEPLOY = "DEPLOY"


@dataclass(frozen=True, slots=True)
class ExtendPlan:
    """Plan for an EXTEND closure outcome."""
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


@dataclass(frozen=True, slots=True)
class ExpandPlan:
    """Plan for an EXPAND closure outcome."""
    expansion_scope: str
    new_population: str
    new_duration_days: int
    additional_eval_families: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "expansion_scope": self.expansion_scope,
            "new_population": self.new_population,
            "new_duration_days": self.new_duration_days,
            "additional_eval_families": list(self.additional_eval_families),
        }


@dataclass(frozen=True, slots=True)
class DeployPlan:
    """Plan for a DEPLOY closure outcome."""
    production_transition: str
    owner: str
    timeline: str
    monitoring_plan: str

    def to_dict(self) -> dict:
        return {
            "production_transition": self.production_transition,
            "owner": self.owner,
            "timeline": self.timeline,
            "monitoring_plan": self.monitoring_plan,
        }


@dataclass(frozen=True, slots=True)
class StopLessons:
    """Lessons learned for a STOP closure outcome."""
    key_findings: str
    lessons_learned: str
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "key_findings": self.key_findings,
            "lessons_learned": self.lessons_learned,
            "recommendation": self.recommendation,
        }


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    """The immutable closure decision for a pilot.

    Created at the end of the DECIDE stage. References the Gate 3 record
    that authorized the closure. Once created, the decision is final.
    """
    decision_id: str
    pilot_id: str
    closure_outcome: ClosureOutcome
    rationale: str
    decided_at: str
    decided_by: str
    gate_3_record_id: str
    success_criteria_comparison: Optional[Dict] = None
    conditions: List[str] = field(default_factory=list)
    evidence_cited: List[str] = field(default_factory=list)
    extend_plan: Optional[ExtendPlan] = None
    expand_plan: Optional[ExpandPlan] = None
    deploy_plan: Optional[DeployPlan] = None
    stop_lessons: Optional[StopLessons] = None
    immutable: bool = True

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "pilot_id": self.pilot_id,
            "closure_outcome": self.closure_outcome.value,
            "rationale": self.rationale,
            "decided_at": self.decided_at,
            "decided_by": self.decided_by,
            "gate_3_record_id": self.gate_3_record_id,
            "success_criteria_comparison": self.success_criteria_comparison,
            "conditions": list(self.conditions),
            "evidence_cited": list(self.evidence_cited),
            "extend_plan": self.extend_plan.to_dict() if self.extend_plan else None,
            "expand_plan": self.expand_plan.to_dict() if self.expand_plan else None,
            "deploy_plan": self.deploy_plan.to_dict() if self.deploy_plan else None,
            "stop_lessons": self.stop_lessons.to_dict() if self.stop_lessons else None,
            "immutable": self.immutable,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DecisionRecord":
        return cls(
            decision_id=d["decision_id"],
            pilot_id=d["pilot_id"],
            closure_outcome=ClosureOutcome(d["closure_outcome"]),
            rationale=d.get("rationale", ""),
            decided_at=d.get("decided_at", ""),
            decided_by=d.get("decided_by", ""),
            gate_3_record_id=d.get("gate_3_record_id", ""),
            success_criteria_comparison=d.get("success_criteria_comparison"),
            conditions=list(d.get("conditions", [])),
            evidence_cited=list(d.get("evidence_cited", [])),
            extend_plan=ExtendPlan(**d["extend_plan"]) if d.get("extend_plan") else None,
            expand_plan=ExpandPlan(**d["expand_plan"]) if d.get("expand_plan") else None,
            deploy_plan=DeployPlan(**d["deploy_plan"]) if d.get("deploy_plan") else None,
            stop_lessons=StopLessons(**d["stop_lessons"]) if d.get("stop_lessons") else None,
        )


def create_decision_record(
    pilot_id: str,
    closure_outcome: ClosureOutcome,
    rationale: str,
    decided_by: str,
    gate_3_record_id: str,
    success_criteria_comparison: Optional[Dict] = None,
    conditions: Optional[List[str]] = None,
    evidence_cited: Optional[List[str]] = None,
    extend_plan: Optional[ExtendPlan] = None,
    expand_plan: Optional[ExpandPlan] = None,
    deploy_plan: Optional[DeployPlan] = None,
    stop_lessons: Optional[StopLessons] = None,
) -> DecisionRecord:
    """Create an immutable decision record.

    Validates outcome-specific requirements:
        EXTEND requires extend_plan
        EXPAND requires expand_plan
        DEPLOY requires deploy_plan
        STOP requires stop_lessons
    """
    if closure_outcome == ClosureOutcome.EXTEND and not extend_plan:
        raise ValueError("EXTEND closure requires an extend_plan.")
    if closure_outcome == ClosureOutcome.EXPAND and not expand_plan:
        raise ValueError("EXPAND closure requires an expand_plan.")
    if closure_outcome == ClosureOutcome.DEPLOY and not deploy_plan:
        raise ValueError("DEPLOY closure requires a deploy_plan.")
    if closure_outcome == ClosureOutcome.STOP and not stop_lessons:
        raise ValueError("STOP closure requires stop_lessons.")

    decision_id = f"DECISION-{pilot_id}"
    ts = datetime.now(timezone.utc).isoformat()

    return DecisionRecord(
        decision_id=decision_id,
        pilot_id=pilot_id,
        closure_outcome=closure_outcome,
        rationale=rationale,
        decided_at=ts,
        decided_by=decided_by,
        gate_3_record_id=gate_3_record_id,
        success_criteria_comparison=success_criteria_comparison,
        conditions=list(conditions or []),
        evidence_cited=list(evidence_cited or []),
        extend_plan=extend_plan,
        expand_plan=expand_plan,
        deploy_plan=deploy_plan,
        stop_lessons=stop_lessons,
        immutable=True,
    )
