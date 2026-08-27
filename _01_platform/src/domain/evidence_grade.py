"""EvidenceGrade — the evidence ladder and assessment for canonical objects.

Per `03_CONNECTION_INGESTION.md` §5.6 Object 19 and §12: The evidence grade
enum defines the eight-level evidence ladder. EvidenceGradeAssessment records
the grade assigned to a canonical object, the conclusions permitted and
prohibited at that grade, and the confounds that limit interpretation.

Evidence grades (highest to lowest):
    controlled_experiment          — randomized controlled trial
    complete_interaction_telemetry — full state-transition chain captured
    strong_observational_telemetry — token-level I/O/R/W telemetry
    partial_telemetry              — incomplete token telemetry
    activity_metadata              — usage logs without token detail
    customer_supplied_outcome      — external outcome data
    inferred_signal                — inferred from indirect signals
    insufficient_evidence          — not enough to support conclusions
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class EvidenceGrade(str, Enum):
    """The eight-level evidence ladder per `03` §12."""
    CONTROLLED_EXPERIMENT = "controlled_experiment"
    COMPLETE_INTERACTION_TELEMETRY = "complete_interaction_telemetry"
    STRONG_OBSERVATIONAL_TELEMETRY = "strong_observational_telemetry"
    PARTIAL_TELEMETRY = "partial_telemetry"
    ACTIVITY_METADATA = "activity_metadata"
    CUSTOMER_SUPPLIED_OUTCOME = "customer_supplied_outcome"
    INFERRED_SIGNAL = "inferred_signal"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True, slots=True)
class EvidenceGradeAssessment:
    """An evidence grade assessment for a canonical object.

    Records the grade, the conclusions permitted and prohibited at that grade,
    and the confounds that limit interpretation.

    The `synthetic` flag must survive import/export.
    """
    assessment_id: str
    target_type: str
    target_id: str
    grade: EvidenceGrade
    assessed_at: datetime
    synthetic: bool = False
    permitted_conclusions: List[str] = field(default_factory=list)
    prohibited_conclusions: List[str] = field(default_factory=list)
    confounds: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Normalize naive datetimes to UTC for consistent serialization.
        if self.assessed_at.tzinfo is None:
            object.__setattr__(
                self, "assessed_at",
                self.assessed_at.replace(tzinfo=timezone.utc),
            )

    def to_dict(self) -> dict:
        return {
            "assessment_id": self.assessment_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "grade": self.grade.value,
            "assessed_at": self.assessed_at.isoformat(),
            "synthetic": self.synthetic,
            "permitted_conclusions": list(self.permitted_conclusions),
            "prohibited_conclusions": list(self.prohibited_conclusions),
            "confounds": list(self.confounds),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EvidenceGradeAssessment":
        assessed = d["assessed_at"]
        if isinstance(assessed, str):
            assessed = datetime.fromisoformat(assessed.replace("Z", "+00:00"))
        grade = d["grade"]
        if isinstance(grade, str):
            grade = EvidenceGrade(grade)
        return cls(
            assessment_id=d["assessment_id"],
            target_type=d["target_type"],
            target_id=d["target_id"],
            grade=grade,
            assessed_at=assessed,
            synthetic=bool(d.get("synthetic", False)),
            permitted_conclusions=list(d.get("permitted_conclusions", [])),
            prohibited_conclusions=list(d.get("prohibited_conclusions", [])),
            confounds=list(d.get("confounds", [])),
        )
