"""Measurement — a versioned deterministic derived value.

Per `03_CANONICAL_METRIC_REGISTRY.md` measurement object contract, every
emitted metric MUST carry: metric_id, metric_version, value, unit,
window_start, window_end, source, status, eligibility.

This is the canonical output of the metric engine (P0-B). Measurements are
immutable once computed — they are deterministic projections of observations.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class MetricStatus(str, Enum):
    """Status vocabulary from `03_CANONICAL_METRIC_REGISTRY.md`."""
    CANONICAL = "CANONICAL"
    CANONICAL_WITH_INTERPRETATION_LIMIT = "CANONICAL_WITH_INTERPRETATION_LIMIT"
    NEEDS_CANONICAL_LOCK = "NEEDS_CANONICAL_LOCK"
    DERIVED_ENTERPRISE = "DERIVED_ENTERPRISE"
    RESEARCH = "RESEARCH"


@dataclass(frozen=True, slots=True)
class Measurement:
    """A single computed metric value for an operator over a window.

    The `eligibility` field records the domain guard that was satisfied
    (e.g. "I>0"). If the guard was not satisfied, `value` is None and
    `eligibility` records the failed condition (e.g. "I=0").
    """
    metric_id: str
    metric_version: str
    operator_id: str
    value: Optional[float]
    unit: str
    window_start: date
    window_end: date
    source: str
    status: MetricStatus
    eligibility: str
    synthetic: bool = False

    def to_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "metric_version": self.metric_version,
            "operator_id": self.operator_id,
            "value": self.value,
            "unit": self.unit,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "source": self.source,
            "status": self.status.value,
            "eligibility": self.eligibility,
            "synthetic": self.synthetic,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Measurement":
        ws = d["window_start"]
        we = d["window_end"]
        if isinstance(ws, str):
            ws = date.fromisoformat(ws)
        if isinstance(we, str):
            we = date.fromisoformat(we)
        status = d["status"]
        if isinstance(status, str):
            status = MetricStatus(status)
        return cls(
            metric_id=d["metric_id"],
            metric_version=d["metric_version"],
            operator_id=d["operator_id"],
            value=d["value"],
            unit=d["unit"],
            window_start=ws,
            window_end=we,
            source=d["source"],
            status=status,
            eligibility=d["eligibility"],
            synthetic=d.get("synthetic", False),
        )
