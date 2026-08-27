"""Cohort — a group of operators evaluated together in a pilot window.

Per `14_PRODUCT_OBJECT_MODEL.md`: Tenant → Cohort → Operator.
A cohort defines the evaluation window and the operator set.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass(frozen=True, slots=True)
class Cohort:
    cohort_id: str
    tenant_id: str
    name: str
    window_start: date
    window_end: date
    operator_ids: List[str] = field(default_factory=list)
    synthetic: bool = False
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "cohort_id": self.cohort_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "operator_ids": list(self.operator_ids),
            "synthetic": self.synthetic,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Cohort":
        ws = d["window_start"]
        we = d["window_end"]
        if isinstance(ws, str):
            ws = date.fromisoformat(ws)
        if isinstance(we, str):
            we = date.fromisoformat(we)
        return cls(
            cohort_id=d["cohort_id"],
            tenant_id=d.get("tenant_id", ""),
            name=d["name"],
            window_start=ws,
            window_end=we,
            operator_ids=list(d.get("operator_ids", [])),
            synthetic=d.get("synthetic", False),
            description=d.get("description"),
        )
