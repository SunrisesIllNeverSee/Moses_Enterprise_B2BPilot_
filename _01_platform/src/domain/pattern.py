"""Pattern — a descriptive relationship among measurements; no causal claim.

Per `14_PRODUCT_OBJECT_MODEL.md`: "Descriptive relationship among measurements;
no causal claim." Patterns are the layer above Measurement and below Diagnosis
in the interpretation ladder (`03`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass(frozen=True, slots=True)
class Pattern:
    pattern_id: str
    operator_id: str
    window_start: date
    window_end: date
    description: str
    supporting_metrics: List[str] = field(default_factory=list)
    status: str = "observed"  # observed | derived | inconclusive
    synthetic: bool = False

    def to_dict(self) -> dict:
        return {
            "pattern_id": self.pattern_id,
            "operator_id": self.operator_id,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "description": self.description,
            "supporting_metrics": list(self.supporting_metrics),
            "status": self.status,
            "synthetic": self.synthetic,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Pattern":
        ws = d["window_start"]
        we = d["window_end"]
        if isinstance(ws, str):
            ws = date.fromisoformat(ws)
        if isinstance(we, str):
            we = date.fromisoformat(we)
        return cls(
            pattern_id=d["pattern_id"],
            operator_id=d["operator_id"],
            window_start=ws,
            window_end=we,
            description=d["description"],
            supporting_metrics=list(d.get("supporting_metrics", [])),
            status=d.get("status", "observed"),
            synthetic=d.get("synthetic", False),
        )
