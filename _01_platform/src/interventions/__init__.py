"""Interventions — registry, recommendation, assignment, and closure flows.

P1-C: Per `21` P1 acceptance: "intervention declares target metric/window
before follow-up."

Architecture:
    interventions/registry.py    — intervention catalog + lookup
    interventions/manager.py     — recommend, assign, close flows
"""
from __future__ import annotations

from .registry import InterventionRegistry, InterventionCatalogEntry
from .manager import InterventionManager

__all__ = ["InterventionRegistry", "InterventionCatalogEntry", "InterventionManager"]
