"""OutcomeJoin — a customer-owned outcome record linked for validation.

Per `14_PRODUCT_OBJECT_MODEL.md`: "Customer-owned outcome record linked for
validation." Outcome data remains separately governed from operator metrics
(P2 acceptance: "outcome joins remain separately governed").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Optional


@dataclass(frozen=True, slots=True)
class OutcomeJoin:
    join_id: str
    operator_id: str
    intervention_id: Optional[str]
    window_start: date
    window_end: date
    # customer-owned outcome deltas (e.g. cycle_time_pct, quality_pct)
    external_deltas: Dict[str, float] = field(default_factory=dict)
    source: str = "customer_provided"
    synthetic: bool = False

    def to_dict(self) -> dict:
        return {
            "join_id": self.join_id,
            "operator_id": self.operator_id,
            "intervention_id": self.intervention_id,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "external_deltas": dict(self.external_deltas),
            "source": self.source,
            "synthetic": self.synthetic,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OutcomeJoin":
        ws = d["window_start"]
        we = d["window_end"]
        if isinstance(ws, str):
            ws = date.fromisoformat(ws)
        if isinstance(we, str):
            we = date.fromisoformat(we)
        return cls(
            join_id=d["join_id"],
            operator_id=d["operator_id"],
            intervention_id=d.get("intervention_id"),
            window_start=ws,
            window_end=we,
            external_deltas=dict(d.get("external_deltas", {})),
            source=d.get("source", "customer_provided"),
            synthetic=d.get("synthetic", False),
        )
