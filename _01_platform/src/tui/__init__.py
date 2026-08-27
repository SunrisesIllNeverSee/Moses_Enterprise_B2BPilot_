"""Enterprise TUI — pilot analyst console per `06_TUI_PRODUCT_SPEC.md`.

10 top-level screens:
    [1] PILOT     [6] WORKFLOW
    [2] COHORT    [7] INTERVENTIONS
    [3] OPERATOR  [8] VERIFY
    [4] DIVERGENCE [9] DATA QUALITY
    [5] DIAGNOSE  [0] EXPORT

The TUI is a thin wrapper over PilotService. It does NOT implement business logic.
Uses `rich` for rendering (already a runtime dependency).
"""
from __future__ import annotations

from .app import TuiApp

__all__ = ["TuiApp"]
