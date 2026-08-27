"""Workflow — workflow fit analysis with observation count + uncertainty.

P2-A: Per `21` P2 acceptance:
- "workflow fit exposes observation count and uncertainty"
- "no stage-fit claim without minimum sample rule"

Architecture:
    workflow/fit_engine.py — computes stage fit with sample-size gates
"""
from __future__ import annotations

from .fit_engine import WorkflowFitEngine, StageFitResult, WorkflowFitReport

__all__ = ["WorkflowFitEngine", "StageFitResult", "WorkflowFitReport"]
