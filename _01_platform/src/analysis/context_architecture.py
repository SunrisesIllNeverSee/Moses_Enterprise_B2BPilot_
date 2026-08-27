"""EVAL-003 — Context Architecture.

Analyzes how operators structure context across repeated sessions/windows.
The core insight is the I/R/W decomposition: fresh input (I), cached/context
tokens read (R), and cached/context tokens written (W). These three
primitives reveal whether an operator reuses prior context, constructs new
context, or relies on fresh input.

Per spec 18:
    Input: I/R/W over repeated sessions/windows.
    Output: reuse/construction patterns with provider caveats.

Per Build B §6.2 (Context Architecture Eval):
    This eval examines the *architecture* of an operator's context strategy,
    not just the volume. Two ratios are central:

        reuse_ratio       = R / (R + I)
        construction_ratio = W / (W + I)

    A high reuse ratio means the operator leans on previously cached context
    (R) rather than re-supplying fresh input (I). A high construction ratio
    means the operator actively writes context (W) for future reuse rather
    than relying on fresh input alone.

Provider caveats:
    Different AI providers expose cache read/write differently. Claude
    reports cache_read_tokens and cache_write_tokens natively; other
    providers may report zero for R and W. When R and W are both zero
    across the cohort, the ratios degenerate and the module notes the
    provider limitation rather than drawing conclusions.

Pattern classification:
    - "context builder"     — high construction, moderate reuse
    - "context reuser"      — high reuse, low construction
    - "fresh input heavy"   — low reuse and low construction
    - "balanced"            — moderate on both axes

All metrics are content-free (token counts only). No content is inspected.
Outcome claims are ASSOCIATION, never CAUSATION.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.observation import Observation
from domain.operator import Operator


@dataclass(frozen=True, slots=True)
class OperatorContextProfile:
    """One operator's context architecture profile."""
    operator_id: str
    pseudonym: str
    team: Optional[str]
    total_input: int       # sum of I
    total_reuse: int       # sum of R
    total_construction: int  # sum of W
    reuse_ratio: float       # R / (R + I), 0–1
    construction_ratio: float  # W / (W + I), 0–1
    context_efficiency: float  # (R + W) / (I + R + W), 0–1
    pattern: str             # classification label
    session_count: int

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "pseudonym": self.pseudonym,
            "team": self.team,
            "total_input": self.total_input,
            "total_reuse": self.total_reuse,
            "total_construction": self.total_construction,
            "reuse_ratio": round(self.reuse_ratio, 4),
            "construction_ratio": round(self.construction_ratio, 4),
            "context_efficiency": round(self.context_efficiency, 4),
            "pattern": self.pattern,
            "session_count": self.session_count,
        }


@dataclass(frozen=True, slots=True)
class ContextArchitecture:
    """The complete context-architecture analysis result."""
    operator_profiles: List[OperatorContextProfile] = field(default_factory=list)
    cohort_avg_reuse_ratio: float = 0.0
    cohort_avg_construction_ratio: float = 0.0
    cohort_avg_context_efficiency: float = 0.0
    pattern_distribution: Dict[str, int] = field(default_factory=dict)
    provider_caveat: str = ""
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "operator_profiles": [p.to_dict() for p in self.operator_profiles],
            "cohort_avg_reuse_ratio": round(self.cohort_avg_reuse_ratio, 4),
            "cohort_avg_construction_ratio": round(self.cohort_avg_construction_ratio, 4),
            "cohort_avg_context_efficiency": round(self.cohort_avg_context_efficiency, 4),
            "pattern_distribution": dict(self.pattern_distribution),
            "provider_caveat": self.provider_caveat,
            "summary": self.summary,
        }


def _classify_pattern(reuse_ratio: float, construction_ratio: float) -> str:
    """Classify an operator's context architecture pattern.

    Thresholds are heuristic and developmental — not punitive labels.
    """
    reuse_high = reuse_ratio > 0.6
    construction_high = construction_ratio > 0.6
    reuse_low = reuse_ratio < 0.3
    construction_low = construction_ratio < 0.3

    if construction_high and not reuse_low:
        return "context builder"
    if reuse_high and construction_low:
        return "context reuser"
    if reuse_low and construction_low:
        return "fresh input heavy"
    return "balanced"


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Division that returns 0.0 when denominator is 0."""
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def compute_context_architecture(
    operators: List[Operator],
    observations: List[Observation],
) -> ContextArchitecture:
    """Compute context-architecture profiles for all operators.

    Args:
        operators: All operators in the cohort.
        observations: All observations (token telemetry) for the cohort.

    Returns:
        ContextArchitecture with per-operator profiles, cohort averages,
        pattern distribution, and provider caveats.
    """
    if not operators:
        return ContextArchitecture(summary="No operators.")

    op_map = {o.operator_id: o for o in operators}

    # Aggregate I/R/W per operator across all observations.
    agg: Dict[str, Dict[str, int]] = {}
    for obs in observations:
        oid = obs.operator_id
        if oid not in agg:
            agg[oid] = {"I": 0, "R": 0, "W": 0, "sessions": 0}
        agg[oid]["I"] += obs.I
        agg[oid]["R"] += obs.R
        agg[oid]["W"] += obs.W
        agg[oid]["sessions"] += 1

    # Detect provider caveat: if R and W are both zero across the entire
    # cohort, the provider does not report cache tokens.
    total_R = sum(a["R"] for a in agg.values())
    total_W = sum(a["W"] for a in agg.values())
    provider_caveat = ""
    if total_R == 0 and total_W == 0:
        provider_caveat = (
            "Provider caveat: cache read (R) and cache write (W) tokens are "
            "both zero across the cohort. This provider may not report cache "
            "tokens. Reuse and construction ratios are degenerate (0.0) and "
            "should not be interpreted."
        )

    profiles: List[OperatorContextProfile] = []
    for op in operators:
        oid = op.operator_id
        a = agg.get(oid, {"I": 0, "R": 0, "W": 0, "sessions": 0})
        I, R, W = a["I"], a["R"], a["W"]
        reuse_ratio = _safe_ratio(R, R + I)
        construction_ratio = _safe_ratio(W, W + I)
        context_efficiency = _safe_ratio(R + W, I + R + W)
        pattern = _classify_pattern(reuse_ratio, construction_ratio)

        profiles.append(OperatorContextProfile(
            operator_id=oid,
            pseudonym=op.pseudonym,
            team=op.team,
            total_input=I,
            total_reuse=R,
            total_construction=W,
            reuse_ratio=reuse_ratio,
            construction_ratio=construction_ratio,
            context_efficiency=context_efficiency,
            pattern=pattern,
            session_count=a["sessions"],
        ))

    # Sort by operator_id for deterministic output.
    profiles.sort(key=lambda p: p.operator_id)

    # Cohort averages.
    n = len(profiles)
    avg_reuse = sum(p.reuse_ratio for p in profiles) / n if n else 0.0
    avg_construction = sum(p.construction_ratio for p in profiles) / n if n else 0.0
    avg_efficiency = sum(p.context_efficiency for p in profiles) / n if n else 0.0

    # Pattern distribution.
    pattern_dist: Dict[str, int] = {}
    for p in profiles:
        pattern_dist[p.pattern] = pattern_dist.get(p.pattern, 0) + 1

    # Summary.
    summary_parts = [
        f"{n} operators analyzed.",
        f"Cohort average reuse ratio: {avg_reuse:.2f}.",
        f"Cohort average construction ratio: {avg_construction:.2f}.",
    ]
    dominant = max(pattern_dist, key=pattern_dist.get) if pattern_dist else "unknown"
    summary_parts.append(f"Dominant pattern: {dominant} ({pattern_dist.get(dominant, 0)} operators).")
    if provider_caveat:
        summary_parts.append("Provider caveat applies — ratios may be degenerate.")

    return ContextArchitecture(
        operator_profiles=profiles,
        cohort_avg_reuse_ratio=avg_reuse,
        cohort_avg_construction_ratio=avg_construction,
        cohort_avg_context_efficiency=avg_efficiency,
        pattern_distribution=pattern_dist,
        provider_caveat=provider_caveat,
        summary=" ".join(summary_parts),
    )
