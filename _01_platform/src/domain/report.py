"""Report — a projection generated from underlying objects; never source of truth.

Per `14_PRODUCT_OBJECT_MODEL.md`: "Projection generated from the underlying
objects; never source of truth." Reports are derived views (cohort summary,
operator profile, divergence table) that can always be regenerated from
observations + measurements.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, Optional


@dataclass(frozen=True, slots=True)
class Report:
    report_id: str
    report_type: str  # cohort_summary | operator_profile | divergence | pilot_readout
    cohort_id: str
    window_start: date
    window_end: date
    content: Dict[str, Any] = field(default_factory=dict)
    metric_registry_version: Optional[str] = None
    reference_version: Optional[str] = None
    synthetic: bool = False

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "cohort_id": self.cohort_id,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "content": dict(self.content),
            "metric_registry_version": self.metric_registry_version,
            "reference_version": self.reference_version,
            "synthetic": self.synthetic,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Report":
        ws = d["window_start"]
        we = d["window_end"]
        if isinstance(ws, str):
            ws = date.fromisoformat(ws)
        if isinstance(we, str):
            we = date.fromisoformat(we)
        return cls(
            report_id=d["report_id"],
            report_type=d["report_type"],
            cohort_id=d["cohort_id"],
            window_start=ws,
            window_end=we,
            content=dict(d.get("content", {})),
            metric_registry_version=d.get("metric_registry_version"),
            reference_version=d.get("reference_version"),
            synthetic=d.get("synthetic", False),
        )
