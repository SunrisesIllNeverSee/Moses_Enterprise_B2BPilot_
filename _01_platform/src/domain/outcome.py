"""Outcome — observable downstream consequence of an operating sequence.

Per Jaimie's review §17: "You have Artifact, which is useful. But
artifact != outcome." The Outcome node completes the chain:

    Operator -> Interaction -> System -> Transformation -> Artifact -> Outcome

Without an Outcome object, the platform risks becoming "extremely
sophisticated behavior analytics." With it, the platform can become
"performance science" — testing whether operating patterns actually
produce downstream consequences.

Outcome is distinct from OutcomeJoin:
- OutcomeJoin is a customer-provided external record linked after the
  fact for validation (e.g., cycle_time_change_pct from an HR system).
- Outcome is a first-class node in the lineage chain, representing the
  observable downstream consequence of a specific transformation sequence
  (e.g., pr_merged, bug_fixed, feature_shipped with quality score and
  cycle time).

Required fields: outcome_id, lineage_id, operator_id, outcome_type,
outcome_status, synthetic.
Optional fields: artifact_id, external_quality_score, cycle_time_minutes,
recorded_at.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class OutcomeType(str, Enum):
    """Categorized downstream consequence type."""
    PR_MERGED = "pr_merged"
    BUG_FIXED = "bug_fixed"
    FEATURE_SHIPPED = "feature_shipped"
    TEST_PASSED = "test_passed"
    TASK_COMPLETED = "task_completed"
    DOC_PUBLISHED = "doc_published"


class OutcomeStatus(str, Enum):
    """Result status of the outcome."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"


@dataclass(frozen=True, slots=True)
class Outcome:
    """An observable downstream consequence linked to a lineage chain.

    The `synthetic` flag must survive import/export.
    """
    outcome_id: str
    lineage_id: str
    operator_id: str
    outcome_type: OutcomeType
    outcome_status: OutcomeStatus
    synthetic: bool = False
    artifact_id: Optional[str] = None
    external_quality_score: Optional[float] = None
    cycle_time_minutes: Optional[float] = None
    recorded_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "outcome_id": self.outcome_id,
            "lineage_id": self.lineage_id,
            "operator_id": self.operator_id,
            "outcome_type": self.outcome_type.value
                if isinstance(self.outcome_type, OutcomeType)
                else self.outcome_type,
            "outcome_status": self.outcome_status.value
                if isinstance(self.outcome_status, OutcomeStatus)
                else self.outcome_status,
            "synthetic": self.synthetic,
            "artifact_id": self.artifact_id,
            "external_quality_score": self.external_quality_score,
            "cycle_time_minutes": self.cycle_time_minutes,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Outcome":
        ot = d.get("outcome_type", "")
        os = d.get("outcome_status", "")
        recorded = d.get("recorded_at")
        return cls(
            outcome_id=d["outcome_id"],
            lineage_id=d["lineage_id"],
            operator_id=d["operator_id"],
            outcome_type=OutcomeType(ot) if ot in OutcomeType._value2member_map_ else ot,
            outcome_status=OutcomeStatus(os) if os in OutcomeStatus._value2member_map_ else os,
            synthetic=d.get("synthetic", False),
            artifact_id=d.get("artifact_id"),
            external_quality_score=d.get("external_quality_score"),
            cycle_time_minutes=d.get("cycle_time_minutes"),
            recorded_at=datetime.fromisoformat(recorded) if recorded else None,
        )
