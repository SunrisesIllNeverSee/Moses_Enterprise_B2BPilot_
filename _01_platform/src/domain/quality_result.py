"""QualityResult — outcome of a data-quality check on an operator's observations.

Per `21` P0 acceptance tests: "quality failures block misleading comparisons."
A QualityResult with `passed=False` and `severity=BLOCKING` prevents the
operator's measurements from being used in cohort comparisons.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class QualitySeverity(str, Enum):
    """How a quality failure should be handled."""
    OK = "OK"
    WARNING = "WARNING"      # report but proceed
    BLOCKING = "BLOCKING"    # block comparisons / exports


@dataclass(frozen=True, slots=True)
class QualityResult:
    check_id: str
    operator_id: str
    window_start: date
    window_end: date
    passed: bool
    severity: QualitySeverity
    reason: str
    detail: Optional[str] = None
    synthetic: bool = False

    @property
    def blocks(self) -> bool:
        """True if this result blocks misleading comparisons."""
        return not self.passed and self.severity == QualitySeverity.BLOCKING

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "operator_id": self.operator_id,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "passed": self.passed,
            "severity": self.severity.value,
            "reason": self.reason,
            "detail": self.detail,
            "synthetic": self.synthetic,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "QualityResult":
        ws = d["window_start"]
        we = d["window_end"]
        if isinstance(ws, str):
            ws = date.fromisoformat(ws)
        if isinstance(we, str):
            we = date.fromisoformat(we)
        sev = d["severity"]
        if isinstance(sev, str):
            sev = QualitySeverity(sev)
        return cls(
            check_id=d["check_id"],
            operator_id=d["operator_id"],
            window_start=ws,
            window_end=we,
            passed=d["passed"],
            severity=sev,
            reason=d["reason"],
            detail=d.get("detail"),
            synthetic=d.get("synthetic", False),
        )
