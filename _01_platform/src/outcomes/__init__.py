"""Outcomes — external outcome joins with governance.

P2-B: Per `21` P2 acceptance:
- "outcome joins remain separately governed"
- "outcome analysis separates association from causal claim"

Architecture:
    outcomes/join_engine.py   — joins external outcomes to operator/intervention data
    outcomes/governance.py    — governance annotations for outcome data
    outcomes/cross_analysis.py — wires intervention verification to outcome joins
"""
from __future__ import annotations

from .join_engine import OutcomeJoinEngine, OutcomeJoinResult, OutcomeSource
from .governance import OutcomeGovernance, GovernanceLevel
from .cross_analysis import InterventionOutcomeAnalyzer, InterventionOutcomeResult

__all__ = [
    "OutcomeJoinEngine", "OutcomeJoinResult", "OutcomeSource",
    "OutcomeGovernance", "GovernanceLevel",
    "InterventionOutcomeAnalyzer", "InterventionOutcomeResult",
]
