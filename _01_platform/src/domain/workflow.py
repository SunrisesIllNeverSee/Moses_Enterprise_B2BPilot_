"""Workflow, Stage, WorkflowObservation — empirical operator×stage fit.

Per `14_PRODUCT_OBJECT_MODEL.md`: Tenant → Workflow → Stage → WorkflowObservation.
Per `10_WORKFLOW_FIT_ENGINE_SPEC.md`: the canonical 7-stage software-dev workflow
is discovery, requirements, architecture, implementation, testing, review, release.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


# Canonical 7-stage software development workflow (per `10`).
CANONICAL_SOFTWARE_DEV_STAGES = [
    ("discovery", 1),
    ("requirements", 2),
    ("architecture", 3),
    ("implementation", 4),
    ("testing", 5),
    ("review", 6),
    ("release", 7),
]


@dataclass(frozen=True, slots=True)
class Stage:
    stage_id: str
    order: int
    name: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "stage_id": self.stage_id,
            "order": self.order,
            "name": self.name or self.stage_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Stage":
        return cls(
            stage_id=d["stage_id"],
            order=int(d["order"]),
            name=d.get("name"),
        )


@dataclass(frozen=True, slots=True)
class Workflow:
    workflow_id: str
    name: str
    stages: List[Stage] = field(default_factory=list)

    @classmethod
    def software_dev_v1(cls) -> "Workflow":
        """The canonical 7-stage software development workflow."""
        return cls(
            workflow_id="software_dev_v1",
            name="Software Development",
            stages=[Stage(sid, order) for sid, order in CANONICAL_SOFTWARE_DEV_STAGES],
        )

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "stages": [s.to_dict() for s in self.stages],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Workflow":
        return cls(
            workflow_id=d["workflow_id"],
            name=d["name"],
            stages=[Stage.from_dict(s) for s in d.get("stages", [])],
        )


@dataclass(frozen=True, slots=True)
class WorkflowObservation:
    """Operator + stage + environment + outcome (per `14` object model)."""
    operator_id: str
    workflow_id: str
    stage_id: str
    date: date
    time_spent_minutes: float = 0.0
    tasks_completed: int = 0
    external_quality_score: Optional[float] = None
    provisional_fit: Optional[float] = None  # demo only
    evidence_count: int = 0
    status: str = "synthetic_provisional"
    synthetic: bool = False

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "workflow_id": self.workflow_id,
            "stage_id": self.stage_id,
            "date": self.date.isoformat(),
            "time_spent_minutes": self.time_spent_minutes,
            "tasks_completed": self.tasks_completed,
            "external_quality_score": self.external_quality_score,
            "provisional_fit": self.provisional_fit,
            "evidence_count": self.evidence_count,
            "status": self.status,
            "synthetic": self.synthetic,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WorkflowObservation":
        dt = d["date"]
        if isinstance(dt, str):
            dt = date.fromisoformat(dt)
        return cls(
            operator_id=d["operator_id"],
            workflow_id=d["workflow_id"],
            stage_id=d["stage_id"],
            date=dt,
            time_spent_minutes=float(d.get("time_spent_minutes", 0)),
            tasks_completed=int(d.get("tasks_completed", 0)),
            external_quality_score=d.get("external_quality_score"),
            provisional_fit=d.get("provisional_fit"),
            evidence_count=int(d.get("evidence_count", 0)),
            status=d.get("status", "synthetic_provisional"),
            synthetic=d.get("synthetic", False),
        )
