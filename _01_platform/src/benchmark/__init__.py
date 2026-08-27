"""Benchmark Engine — MO§ES™ Enterprise Pilot Readiness §7.

Provides the comparison framework for evaluation results. While the Evaluation
Engine (§6) measures operators, the Benchmark Engine answers: "compared to what?"

13 benchmark classes:
  7.1  Self vs prior self     — within-operator, longitudinal
  7.2  Repeated task          — within-operator, same task
  7.3  Matched task           — within-operator, similar task
  7.4  Peer                   — between-operator, similar operators
  7.5  Role                   — between-operator, same role
  7.6  Cohort                 — between-operator, same cohort
  7.7  Team                   — between-operator, same team
  7.8  Organization           — between-operator, whole org
  7.9  System                 — system context, same system
  7.10 Workflow               — stage context, same stage
  7.11 Model                  — model context, same model
  7.12 Intervention           — causal, treatment vs control
  7.13 External field         — external reference

Frozen invariants:
  - MO§ES™ rendering (never MO§E§, never MOSES without the §)
  - SigRank evaluates AI operators, not AI models
  - No false leaderboards: benchmarks never present a simple ranked list
    without uncertainty.
"""
from __future__ import annotations

from .engine import (
    BenchmarkEngine,
    BenchmarkResult,
    BenchmarkClass,
    BenchmarkContext,
    SelectionResult,
    StatisticalMethod,
    EvidenceGrade,
    select_benchmark,
)

__all__ = [
    "BenchmarkEngine",
    "BenchmarkResult",
    "BenchmarkClass",
    "BenchmarkContext",
    "SelectionResult",
    "StatisticalMethod",
    "EvidenceGrade",
    "select_benchmark",
]
