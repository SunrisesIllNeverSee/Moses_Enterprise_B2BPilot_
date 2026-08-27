"""Tenant — the enterprise customer org that owns cohorts and data."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class Tenant:
    tenant_id: str
    name: str
    industry: Optional[str] = None
    synthetic: bool = False

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "industry": self.industry,
            "synthetic": self.synthetic,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Tenant":
        return cls(
            tenant_id=d["tenant_id"],
            name=d["name"],
            industry=d.get("industry"),
            synthetic=d.get("synthetic", False),
        )
