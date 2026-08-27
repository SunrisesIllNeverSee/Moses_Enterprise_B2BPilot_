"""Intervention — an action taken to test/improve a diagnosis.

Per `14_PRODUCT_OBJECT_MODEL.md`: "Action taken to test/improve a diagnosis."
Per `21` P1 acceptance: "intervention declares target metric/window before
follow-up."
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class InterventionOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    NO_EFFECT = "NO_EFFECT"
    NEGATIVE = "NEGATIVE"
    PENDING = "PENDING"


@dataclass(frozen=True, slots=True)
class Intervention:
    intervention_id: str
    operator_id: str
    catalog_id: str  # references the intervention catalog (e.g. INT-CTX-001)
    reason_pattern: str  # pattern_id that triggered this intervention
    target_metric: str  # the metric this intervention aims to improve
    start_date: date
    followup_days: int
    synthetic_outcome: InterventionOutcome = InterventionOutcome.PENDING
    synthetic: bool = False

    def to_dict(self) -> dict:
        return {
            "intervention_id": self.intervention_id,
            "operator_id": self.operator_id,
            "catalog_id": self.catalog_id,
            "reason_pattern": self.reason_pattern,
            "target_metric": self.target_metric,
            "start_date": self.start_date.isoformat(),
            "followup_days": self.followup_days,
            "synthetic_outcome": self.synthetic_outcome.value,
            "synthetic": self.synthetic,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Intervention":
        sd = d["start_date"]
        if isinstance(sd, str):
            sd = date.fromisoformat(sd)
        outcome = d.get("synthetic_outcome", "PENDING")
        if isinstance(outcome, str):
            outcome = InterventionOutcome(outcome)
        return cls(
            intervention_id=d["intervention_id"],
            operator_id=d["operator_id"],
            catalog_id=d["catalog_id"],
            reason_pattern=d["reason_pattern"],
            target_metric=d["target_metric"],
            start_date=sd,
            followup_days=int(d["followup_days"]),
            synthetic_outcome=outcome,
            synthetic=d.get("synthetic", False),
        )


# Intervention catalog v0 (per `09` §Intervention catalog v0)
INTERVENTION_CATALOG = [
    {"id": "CTX-001", "name": "Persistent Project Context", "class": "workflow", "target_pattern": "low leverage"},
    {"id": "CTX-002", "name": "Context Handoff Template", "class": "workflow", "target_pattern": "resets/handoffs"},
    {"id": "CTX-003", "name": "Memory Tool Trial", "class": "tooling", "target_pattern": "low reuse"},
    {"id": "FRM-001", "name": "Task Decomposition Guide", "class": "guide", "target_pattern": "rich input/weak output"},
    {"id": "FRM-002", "name": "Acceptance-Criteria Template", "class": "guide", "target_pattern": "retry/rework"},
    {"id": "MOD-001", "name": "Model Routing Trial", "class": "tooling", "target_pattern": "model sensitivity"},
    {"id": "AGT-001", "name": "Agent/Tool Selection Review", "class": "tooling", "target_pattern": "tool mismatch"},
    {"id": "REV-001", "name": "Verification Loop", "class": "workflow", "target_pattern": "high generation/weak review"},
    {"id": "STD-001", "name": "Standard Project Scaffold", "class": "workflow", "target_pattern": "volatility"},
    {"id": "COA-001", "name": "Operator Coaching Session", "class": "human", "target_pattern": "unresolved pattern"},
    {"id": "LRN-001", "name": "External Training Assignment", "class": "partner", "target_pattern": "skill gap outside operator telemetry"},
    {"id": "STG-001", "name": "Stage Placement Trial", "class": "workflow", "target_pattern": "stage specialization"},
]
