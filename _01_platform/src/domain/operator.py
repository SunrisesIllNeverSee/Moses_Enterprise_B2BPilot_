"""Operator — a pseudonymous enterprise AI user under evaluation.

Per `14_PRODUCT_OBJECT_MODEL.md`:
    operator_id, tenant_id, pseudonym, org metadata subset, consent/governance state.

No real names. The `synthetic` flag must survive import/export.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True, slots=True)
class Operator:
    operator_id: str
    tenant_id: str
    pseudonym: str
    cohort_id: str
    team: Optional[str] = None
    role_family: Optional[str] = None
    level: Optional[str] = None
    active: bool = True
    consent_state: str = "granted"  # granted | pending | withdrawn
    synthetic: bool = False
    primary_platform: Optional[str] = None
    pattern_demo: Optional[str] = None  # archetype label (demo only)

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "tenant_id": self.tenant_id,
            "pseudonym": self.pseudonym,
            "cohort_id": self.cohort_id,
            "team": self.team,
            "role_family": self.role_family,
            "level": self.level,
            "active": self.active,
            "consent_state": self.consent_state,
            "synthetic": self.synthetic,
            "primary_platform": self.primary_platform,
            "pattern_demo": self.pattern_demo,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Operator":
        return cls(
            operator_id=d["operator_id"],
            tenant_id=d.get("tenant_id", ""),
            pseudonym=d["pseudonym"],
            cohort_id=d.get("cohort_id", ""),
            team=d.get("team"),
            role_family=d.get("role_family"),
            level=d.get("level"),
            active=d.get("active", True),
            consent_state=d.get("consent_state", "granted"),
            synthetic=d.get("synthetic", False),
            primary_platform=d.get("primary_platform"),
            pattern_demo=d.get("pattern_demo"),
        )
