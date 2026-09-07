"""PilotRun — the thin control-plane object that binds a pilot's identity,
state, evidence, and decisions.

Per the deep-dive review §11 and PILOT_OBJECT.md: PilotRun is the missing
connective tissue. It is a control plane over the measurement engine, not
another analytical database. It references a frozen PilotConfiguration
and coordinates existing systems rather than reproducing them.

Design principle (PILOT_OBJECT.md):
    > The Pilot object binds existing domain objects to a pilot_id and
    > adds the governance layer (charter, success criteria, gates,
    > decisions). It does not re-implement measurements, diagnoses, or
    > interventions — those are existing domain objects referenced by
    > the pilot.

Three pilot layers (review §9):
    CommercialPilotTemplate  →  PilotConfiguration  →  PilotRun
    (what kind of engagement)  (launch choices)        (active engagement)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .pilot_state import PilotState, PilotStateMachine, StageTransition
from .success_criteria import SuccessCriteria
from .gate_record import GateRecord
from .decision_record import DecisionRecord


# Pilot ID pattern: uppercase letters, hyphen, 3 digits (e.g. ACME-001)
_PILOT_ID_PATTERN = re.compile(r"^[A-Z]+-\d{3}$")


def validate_pilot_id(pilot_id: str) -> str:
    """Validate and return a pilot ID.

    Raises ValueError if the ID does not match the canonical pattern.
    """
    if not _PILOT_ID_PATTERN.match(pilot_id):
        raise ValueError(
            f"Invalid pilot_id '{pilot_id}'. "
            f"Must match pattern ^[A-Z]+-\\d{{3}}$ (e.g. ACME-001)."
        )
    return pilot_id


@dataclass(frozen=True, slots=True)
class Milestone:
    """A milestone record tied to a pilot stage."""
    milestone_id: str
    pilot_id: str
    stage: str
    description: str
    completed_at: str
    artifact_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "milestone_id": self.milestone_id,
            "pilot_id": self.pilot_id,
            "stage": self.stage,
            "description": self.description,
            "completed_at": self.completed_at,
            "artifact_refs": list(self.artifact_refs),
        }


@dataclass(frozen=True, slots=True)
class Blocker:
    """An outstanding blocker for a pilot."""
    blocker_id: str
    pilot_id: str
    description: str
    severity: str  # "blocking", "warning", "info"
    raised_at: str
    resolved: bool = False
    resolved_at: str = ""

    def to_dict(self) -> dict:
        return {
            "blocker_id": self.blocker_id,
            "pilot_id": self.pilot_id,
            "description": self.description,
            "severity": self.severity,
            "raised_at": self.raised_at,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
        }


@dataclass
class PilotRun:
    """The active engagement object — the control plane over the measurement engine.

    This is a mutable object: the pilot progresses through stages, accumulates
    milestones, gates, and eventually a decision record. The configuration_id
    references a frozen PilotConfiguration (the immutable measurement contract).

    Per review §11 minimal shape:
        pilot_id, configuration_id, customer, decision_owner, start_date,
        target_end_date, current_stage, objectives, success_criteria,
        milestones, baseline_reference, findings, interventions,
        verification_results, pilot_gate_reviews, blockers, evidence_refs,
        current_status, final_decision.
    """
    pilot_id: str
    configuration_id: str
    customer: str
    decision_owner: str
    start_date: str
    target_end_date: str
    state_machine: PilotStateMachine
    objectives: str = ""
    success_criteria: SuccessCriteria = field(default_factory=SuccessCriteria)
    milestones: List[Milestone] = field(default_factory=list)
    baseline_reference: str = ""  # reference to frozen baseline snapshot
    blockers: List[Blocker] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    gate_records: List[GateRecord] = field(default_factory=list)
    decision_record: Optional[DecisionRecord] = None
    extension_periods: List[dict] = field(default_factory=list)
    created_at: str = ""
    created_by: str = ""

    def __post_init__(self) -> None:
        validate_pilot_id(self.pilot_id)
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def current_stage(self) -> PilotState:
        return self.state_machine.current_state

    @property
    def current_status(self) -> str:
        """Human-readable current status."""
        if self.decision_record:
            return f"TERMINATED — {self.decision_record.closure_outcome.value}"
        return self.state_machine.current_state.value

    @property
    def is_terminated(self) -> bool:
        return self.current_stage == PilotState.TERMINATED

    @property
    def final_decision(self) -> Optional[str]:
        if self.decision_record:
            return self.decision_record.closure_outcome.value
        return None

    def add_milestone(self, stage: str, description: str, artifact_refs: Optional[List[str]] = None) -> Milestone:
        """Record a milestone for a completed stage."""
        ms_id = f"MS-{self.pilot_id}-{len(self.milestones)+1:03d}"
        ms = Milestone(
            milestone_id=ms_id,
            pilot_id=self.pilot_id,
            stage=stage,
            description=description,
            completed_at=datetime.now(timezone.utc).isoformat(),
            artifact_refs=list(artifact_refs or []),
        )
        self.milestones.append(ms)
        return ms

    def add_blocker(self, description: str, severity: str = "blocking") -> Blocker:
        """Raise a new blocker."""
        blk_id = f"BLK-{self.pilot_id}-{len(self.blockers)+1:03d}"
        blk = Blocker(
            blocker_id=blk_id,
            pilot_id=self.pilot_id,
            description=description,
            severity=severity,
            raised_at=datetime.now(timezone.utc).isoformat(),
        )
        self.blockers.append(blk)
        return blk

    def resolve_blocker(self, blocker_id: str) -> None:
        """Mark a blocker as resolved."""
        for i, b in enumerate(self.blockers):
            if b.blocker_id == blocker_id and not b.resolved:
                self.blockers[i] = Blocker(
                    blocker_id=b.blocker_id,
                    pilot_id=b.pilot_id,
                    description=b.description,
                    severity=b.severity,
                    raised_at=b.raised_at,
                    resolved=True,
                    resolved_at=datetime.now(timezone.utc).isoformat(),
                )
                return
        raise ValueError(f"Blocker {blocker_id} not found or already resolved.")

    def add_gate_record(self, record: GateRecord) -> None:
        """Record a pilot-level gate evaluation."""
        self.gate_records.append(record)

    def set_decision_record(self, record: DecisionRecord) -> None:
        """Set the final decision record. Only allowed in DECIDING state."""
        if self.current_stage != PilotState.DECIDING:
            raise ValueError(
                f"Cannot set decision record in {self.current_stage.value} state. "
                f"Must be in DECIDING state."
            )
        if self.decision_record is not None:
            raise ValueError("Decision record already set — it is immutable.")
        self.decision_record = record

    def add_extension_period(self, reason: str, days: int, new_closure_date: str) -> None:
        """Record an extension period (for EXTEND closure)."""
        self.extension_periods.append({
            "reason": reason,
            "days": days,
            "new_closure_date": new_closure_date,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        })

    def engagement_status(self) -> dict:
        """The engagement-centric status display (review §12).

        Unlike pilot_status() which is measurement-centric, this reports
        the pilot lifecycle state: day, stage, objectives, baseline,
        findings, interventions, next gate, and final decision.
        """
        from datetime import date

        day_num = 0
        total_days = 0
        if self.start_date and self.target_end_date:
            try:
                start = date.fromisoformat(self.start_date)
                end = date.fromisoformat(self.target_end_date)
                total_days = (end - start).days
                today = date.today()
                day_num = max(0, (today - start).days)
            except ValueError:
                pass

        next_gate = ""
        sm = self.state_machine
        if sm.current_state == PilotState.DEFINED:
            next_gate = "Gate 1 — Launch Readiness"
        elif sm.current_state in (PilotState.INTERVENING, PilotState.VERIFYING):
            next_gate = "Gate 2 — Pilot Health"
        elif sm.current_state == PilotState.READOUT:
            next_gate = "Gate 3 — Closure / Scale"
        elif sm.current_state == PilotState.DECIDING:
            next_gate = "Gate 3 — Closure / Scale (pending)"
        elif sm.current_state == PilotState.TERMINATED:
            next_gate = "(terminal)"

        return {
            "pilot_id": self.pilot_id,
            "customer": self.customer,
            "day": f"{day_num} / {total_days}" if total_days else "—",
            "current_stage": sm.current_state.value,
            "objectives": self.objectives or "—",
            "baseline": "FROZEN" if self.baseline_reference else "NOT_SET",
            "milestones_completed": len(self.milestones),
            "findings": "—",  # populated from service layer
            "interventions": "—",  # populated from service layer
            "next_gate": next_gate,
            "blockers_open": sum(1 for b in self.blockers if not b.resolved),
            "final_decision": self.final_decision or "PENDING",
            "lifecycle_display": sm.lifecycle_display(),
        }

    def to_dict(self) -> dict:
        return {
            "pilot_id": self.pilot_id,
            "configuration_id": self.configuration_id,
            "customer": self.customer,
            "decision_owner": self.decision_owner,
            "start_date": self.start_date,
            "target_end_date": self.target_end_date,
            "current_stage": self.current_stage.value,
            "current_status": self.current_status,
            "objectives": self.objectives,
            "success_criteria": self.success_criteria.to_dict(),
            "milestones": [m.to_dict() for m in self.milestones],
            "baseline_reference": self.baseline_reference,
            "blockers": [b.to_dict() for b in self.blockers],
            "evidence_refs": list(self.evidence_refs),
            "gate_records": [g.to_dict() for g in self.gate_records],
            "decision_record": self.decision_record.to_dict() if self.decision_record else None,
            "extension_periods": list(self.extension_periods),
            "created_at": self.created_at,
            "created_by": self.created_by,
            "state_machine": self.state_machine.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PilotRun":
        from .decision_record import ClosureOutcome
        pr = cls(
            pilot_id=d["pilot_id"],
            configuration_id=d["configuration_id"],
            customer=d.get("customer", ""),
            decision_owner=d.get("decision_owner", ""),
            start_date=d.get("start_date", ""),
            target_end_date=d.get("target_end_date", ""),
            state_machine=PilotStateMachine.from_dict(d.get("state_machine", {})),
            objectives=d.get("objectives", ""),
            success_criteria=SuccessCriteria.from_dict(d.get("success_criteria", {})),
            baseline_reference=d.get("baseline_reference", ""),
            evidence_refs=list(d.get("evidence_refs", [])),
            extension_periods=list(d.get("extension_periods", [])),
            created_at=d.get("created_at", ""),
            created_by=d.get("created_by", ""),
        )
        for m in d.get("milestones", []):
            pr.milestones.append(Milestone(**m))
        for b in d.get("blockers", []):
            pr.blockers.append(Blocker(**b))
        for g in d.get("gate_records", []):
            pr.gate_records.append(GateRecord.from_dict(g))
        if d.get("decision_record"):
            pr.decision_record = DecisionRecord.from_dict(d["decision_record"])
        return pr


def create_pilot_run(
    pilot_id: str,
    configuration_id: str,
    customer: str,
    decision_owner: str,
    start_date: str,
    target_end_date: str,
    objectives: str = "",
    created_by: str = "",
) -> PilotRun:
    """Create a new PilotRun in the DEFINED state."""
    sm = PilotStateMachine(pilot_id=pilot_id, current_state=PilotState.DEFINED)
    return PilotRun(
        pilot_id=pilot_id,
        configuration_id=configuration_id,
        customer=customer,
        decision_owner=decision_owner,
        start_date=start_date,
        target_end_date=target_end_date,
        state_machine=sm,
        objectives=objectives,
        created_by=created_by,
    )
