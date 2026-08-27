"""Diagnosis — a hypothesis explaining a pattern, with alternatives and confidence.

Per `14_PRODUCT_OBJECT_MODEL.md`: "Hypothesis explaining a pattern, with
alternatives and confidence."
Per `21` P1 acceptance: "every diagnosis contains evidence + alternatives +
status=HYPOTHESIS."
Per `02` §15 status vocabulary: measured, observed, derived, hypothesis,
validated, rejected, inconclusive.
Per `09` diagnostic hierarchy: every diagnosis is labeled with its hierarchy
level (operator / tool_model / workflow / organization) and emitted in
hierarchy order. A higher-level hypothesis is flagged as structurally
stronger than a lower-level one when evidence supports both — this is the
spec's primary safeguard against operator-blame misattribution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional


class DiagnosisStatus(str, Enum):
    MEASURED = "measured"
    OBSERVED = "observed"
    DERIVED = "derived"
    HYPOTHESIS = "hypothesis"
    VALIDATED = "validated"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


class DiagnosticLevel(str, Enum):
    """Diagnostic hierarchy levels per `09` §Diagnostic hierarchy.

    Order matters: OPERATOR < TOOL_MODEL < WORKFLOW < ORGANIZATION.
    The diagnosis engine emits hypotheses in this order and flags a
    higher-level hypothesis as structurally stronger than a lower-level
    one when evidence supports both. Do not advance to a higher level
    until the current level has been examined and ruled out (or noted
    as a contributor).
    """
    OPERATOR = "operator"
    TOOL_MODEL = "tool_model"
    WORKFLOW = "workflow"
    ORGANIZATION = "organization"

    @classmethod
    def order(cls, level: "DiagnosticLevel") -> int:
        """Return the integer sort key for a level (lower = examined first)."""
        return _LEVEL_ORDER[level]


_LEVEL_ORDER = {
    DiagnosticLevel.OPERATOR: 0,
    DiagnosticLevel.TOOL_MODEL: 1,
    DiagnosticLevel.WORKFLOW: 2,
    DiagnosticLevel.ORGANIZATION: 3,
}


@dataclass(frozen=True, slots=True)
class Diagnosis:
    diagnosis_id: str
    operator_id: str
    pattern_id: str
    hypothesis: str
    confidence: float  # 0.0–1.0
    status: DiagnosisStatus
    evidence: str
    alternatives: List[str] = field(default_factory=list)
    recommended_interventions: List[str] = field(default_factory=list)
    window_start: Optional[date] = None
    window_end: Optional[date] = None
    synthetic: bool = False
    # Diagnostic hierarchy (per `09`). Defaults to OPERATOR for backward
    # compatibility with diagnoses that predate the hierarchy rule.
    level: DiagnosticLevel = DiagnosticLevel.OPERATOR
    # True when a higher-level (tool_model/workflow/organization) hypothesis
    # is emitted alongside an operator-level one for the same operator and
    # evidence supports both. The higher-level hypothesis is the one flagged;
    # it is the spec's safeguard against operator-blame misattribution.
    structurally_stronger: bool = False

    def to_dict(self) -> dict:
        return {
            "diagnosis_id": self.diagnosis_id,
            "operator_id": self.operator_id,
            "pattern_id": self.pattern_id,
            "hypothesis": self.hypothesis,
            "confidence": self.confidence,
            "status": self.status.value,
            "evidence": self.evidence,
            "alternatives": list(self.alternatives),
            "recommended_interventions": list(self.recommended_interventions),
            "window_start": self.window_start.isoformat() if self.window_start else None,
            "window_end": self.window_end.isoformat() if self.window_end else None,
            "synthetic": self.synthetic,
            "level": self.level.value,
            "structurally_stronger": self.structurally_stronger,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Diagnosis":
        ws = d.get("window_start")
        we = d.get("window_end")
        if isinstance(ws, str):
            ws = date.fromisoformat(ws)
        if isinstance(we, str):
            we = date.fromisoformat(we)
        status = d["status"]
        if isinstance(status, str):
            status = DiagnosisStatus(status)
        level = d.get("level", DiagnosticLevel.OPERATOR.value)
        if isinstance(level, str):
            level = DiagnosticLevel(level)
        return cls(
            diagnosis_id=d["diagnosis_id"],
            operator_id=d["operator_id"],
            pattern_id=d["pattern_id"],
            hypothesis=d["hypothesis"],
            confidence=float(d["confidence"]),
            status=status,
            evidence=d["evidence"],
            alternatives=list(d.get("alternatives", [])),
            recommended_interventions=list(d.get("recommended_interventions", [])),
            window_start=ws,
            window_end=we,
            synthetic=d.get("synthetic", False),
            level=level,
            structurally_stronger=bool(d.get("structurally_stronger", False)),
        )
