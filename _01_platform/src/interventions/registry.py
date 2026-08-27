"""Intervention registry — catalog lookup and validation.

Per `09` intervention catalog v0: 12 interventions across workflow, tooling,
guide, human, and partner classes.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@dataclass(frozen=True, slots=True)
class InterventionCatalogEntry:
    """A single intervention catalog entry."""
    id: str
    name: str
    cls: str          # workflow | tooling | guide | human | partner
    target_pattern: str
    target_metric: Optional[str] = None
    typical_followup_days: int = 14

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "class": self.cls,
            "target_pattern": self.target_pattern,
            "target_metric": self.target_metric,
            "typical_followup_days": self.typical_followup_days,
        }


# Catalog v0 (per `09` §Intervention catalog v0)
_CATALOG: List[InterventionCatalogEntry] = [
    InterventionCatalogEntry("CTX-001", "Persistent Project Context", "workflow", "low leverage", "leverage", 14),
    InterventionCatalogEntry("CTX-002", "Context Handoff Template", "workflow", "resets/handoffs", "leverage", 14),
    InterventionCatalogEntry("CTX-003", "Memory Tool Trial", "tooling", "low reuse", "leverage", 21),
    InterventionCatalogEntry("FRM-001", "Task Decomposition Guide", "guide", "rich input/weak output", "yield", 14),
    InterventionCatalogEntry("FRM-002", "Acceptance-Criteria Template", "guide", "retry/rework", "yield", 14),
    InterventionCatalogEntry("MOD-001", "Model Routing Trial", "tooling", "model sensitivity", "yield", 21),
    InterventionCatalogEntry("AGT-001", "Agent/Tool Selection Review", "tooling", "tool mismatch", "yield", 14),
    InterventionCatalogEntry("REV-001", "Verification Loop", "workflow", "high generation/weak review", "token_snr", 14),
    InterventionCatalogEntry("STD-001", "Standard Project Scaffold", "workflow", "volatility", None, 21),
    InterventionCatalogEntry("COA-001", "Operator Coaching Session", "human", "unresolved pattern", "yield", 30),
    InterventionCatalogEntry("LRN-001", "External Training Assignment", "partner", "skill gap outside operator telemetry", None, 90),
    InterventionCatalogEntry("STG-001", "Stage Placement Trial", "workflow", "stage specialization", "yield", 21),
]


# Pattern → recommended intervention IDs (from `09`)
PATTERN_INTERVENTIONS: Dict[str, List[str]] = {
    "P-CTX-01": ["CTX-001", "CTX-002", "CTX-003"],
    "P-CTX-02": ["FRM-001", "MOD-001"],
    "P-BURN-01": ["COA-001", "CTX-001", "FRM-002"],
    "P-HIDDEN-01": [],  # no automatic intervention — "do not infer superior job performance"
    "P-MODEL-01": ["MOD-001", "AGT-001"],
    "P-STAGE-01": ["STG-001"],
}


class InterventionRegistry:
    """Lookup and validate interventions from the catalog."""

    def __init__(self) -> None:
        self._by_id: Dict[str, InterventionCatalogEntry] = {e.id: e for e in _CATALOG}

    def get(self, catalog_id: str) -> InterventionCatalogEntry:
        """Look up an intervention by catalog ID. Raises KeyError if not found."""
        entry = self._by_id.get(catalog_id)
        if entry is None:
            raise KeyError(f"Unknown intervention catalog_id: {catalog_id}")
        return entry

    def all(self) -> List[InterventionCatalogEntry]:
        """Return the full catalog."""
        return list(_CATALOG)

    def for_pattern(self, pattern_id: str) -> List[InterventionCatalogEntry]:
        """Return recommended interventions for a pattern."""
        ids = PATTERN_INTERVENTIONS.get(pattern_id, [])
        return [self._by_id[i] for i in ids if i in self._by_id]

    def validate_target_metric(self, catalog_id: str, target_metric: str) -> bool:
        """Check if a target metric is compatible with the intervention."""
        entry = self.get(catalog_id)
        if entry.target_metric is None:
            return True  # any metric is acceptable
        return entry.target_metric == target_metric
