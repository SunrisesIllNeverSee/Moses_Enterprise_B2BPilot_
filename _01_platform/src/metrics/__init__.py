"""Metric engine — computes canonical measurements from observations.

P0-B: wires the canonical formula functions into a scoring module that reads
`Observation` objects and emits `Measurement` objects conforming to the
`03_CANONICAL_METRIC_REGISTRY.md` measurement object contract.

Architecture:
    metrics/formulas.py — pure formula functions (L, Y, S, D, C) with domain guards
    metrics/engine.py   — ScoringEngine: observations → Measurement objects
    metrics/registry.py — loads/validates the metric registry JSON

The engine is the single scoring path. CLI/TUI/MCP all call it; none compute
metrics independently (per `21` P0 acceptance: "same fixture produces same
metric values in every interface").

Formula functions are re-exported here so legacy `from metrics import leverage`
imports (e.g. tests/test_metrics.py) continue to work.
"""
from __future__ import annotations

from .formulas import leverage, yield_metric, token_snr, log_leverage, construction
from .engine import ScoringEngine
from .registry import MetricRegistry, load_registry
from .composite_score import (
    CompositeScore, compute_composite_score, compute_cohort_composite_scores,
    composite_score_summary, METRIC_WEIGHTS, COMPOSITE_NAME, COMPOSITE_ID,
)

__all__ = [
    "ScoringEngine", "MetricRegistry", "load_registry",
    "leverage", "yield_metric", "token_snr", "log_leverage", "construction",
    "CompositeScore", "compute_composite_score", "compute_cohort_composite_scores",
    "composite_score_summary", "METRIC_WEIGHTS", "COMPOSITE_NAME", "COMPOSITE_ID",
]

