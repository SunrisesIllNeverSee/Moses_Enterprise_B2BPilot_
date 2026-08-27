"""Usage-vs-operation divergence — the signature demo analysis.

Detects cases where an operator's usage percentile differs materially from
their operation (Yield/Leverage) percentile. This is the core thesis from
`02` §2: "HIGH USAGE ≠ STRONG OPERATION" and "LOW USAGE ≠ WEAK OPERATION".

Divergence classes:
    HIGH_USAGE_LOW_OPERATION   — high usage, low yield/leverage
    LOW_USAGE_HIGH_OPERATION   — low usage, high yield/leverage
    MIXED                      — moderate divergence
    LOW_LOW                    — low on both
    HIGH_HIGH                  — high on both (not a divergence case)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.measurement import Measurement


@dataclass(frozen=True, slots=True)
class DivergenceResult:
    operator_id: str
    usage_percentile: Optional[float]
    yield_percentile: Optional[float]
    leverage_percentile: Optional[float]
    divergence_pp: float  # usage_pct - yield_pct in percentage points
    divergence_class: str


def _classify(usage_pct: float, yield_pct: float, divergence_pp: float) -> str:
    if usage_pct >= 60 and yield_pct <= 40:
        return "HIGH_USAGE_LOW_OPERATION"
    if usage_pct <= 40 and yield_pct >= 60:
        return "LOW_USAGE_HIGH_OPERATION"
    if usage_pct <= 40 and yield_pct <= 40:
        return "LOW_LOW"
    return "MIXED"


def compute_divergence(
    percentile_measurements: Dict[str, Dict[str, Measurement]],
    usage_tokens: Dict[str, int],  # operator_id → total usage tokens
) -> List[DivergenceResult]:
    """Compute usage-vs-operation divergence for each operator.

    Usage percentile is computed from the usage_tokens distribution (total
    tokens as a proxy for adoption volume). Operation percentile comes from
    the Yield percentile measurements.
    """
    # Compute usage percentile from the raw token distribution.
    sorted_usage = sorted(usage_tokens.items(), key=lambda x: x[1])
    n = len(sorted_usage)
    usage_pct_map: Dict[str, float] = {}
    for i, (oid, _tokens) in enumerate(sorted_usage):
        usage_pct_map[oid] = round(100.0 * i / max(n - 1, 1), 1)

    results: List[DivergenceResult] = []
    for oid, pcts in percentile_measurements.items():
        usage_pct = usage_pct_map.get(oid)
        yield_pct_m = pcts.get("yield_percentile")
        lev_pct_m = pcts.get("leverage_percentile")
        yield_pct = yield_pct_m.value if yield_pct_m else None
        lev_pct = lev_pct_m.value if lev_pct_m else None

        if usage_pct is None or yield_pct is None:
            continue

        div_pp = round(usage_pct - yield_pct, 1)
        results.append(DivergenceResult(
            operator_id=oid,
            usage_percentile=usage_pct,
            yield_percentile=yield_pct,
            leverage_percentile=lev_pct,
            divergence_pp=div_pp,
            divergence_class=_classify(usage_pct, yield_pct, div_pp),
        ))

    results.sort(key=lambda r: abs(r.divergence_pp), reverse=True)
    return results
