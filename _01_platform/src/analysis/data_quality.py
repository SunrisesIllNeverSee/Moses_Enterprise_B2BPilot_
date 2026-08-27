"""Data quality checks — missingness, impossible values, duplicates, provenance.

P0-D analysis: produces the Data Quality + Eligibility Report (deliverable #1).
Returns QualityResult objects that can block misleading comparisons.
"""
from __future__ import annotations

import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.observation import Observation
from domain.quality_result import QualityResult, QualitySeverity


def check_missingness(
    operator_ids: List[str],
    observations: List[Observation],
    window_start: date,
    window_end: date,
) -> List[QualityResult]:
    """Check for operators with sparse or missing observations."""
    results: List[QualityResult] = []
    window_days = (window_end - window_start).days + 1

    for oid in operator_ids:
        obs = [o for o in observations if o.operator_id == oid
               and window_start <= o.timestamp.date() <= window_end]
        active_days = len(set(o.timestamp.date() for o in obs))
        missing_days = window_days - active_days
        missing_pct = round(100 * missing_days / window_days, 1) if window_days > 0 else 0

        synthetic = any(o.synthetic for o in obs)

        if missing_pct > 50:
            severity = QualitySeverity.BLOCKING
            passed = False
            reason = f"missing {missing_pct}% of window days ({missing_days}/{window_days})"
        elif missing_pct > 20:
            severity = QualitySeverity.WARNING
            passed = True
            reason = f"missing {missing_pct}% of window days ({missing_days}/{window_days})"
        else:
            severity = QualitySeverity.OK
            passed = True
            reason = f"missing {missing_pct}% of window days"

        results.append(QualityResult(
            check_id="missingness",
            operator_id=oid,
            window_start=window_start,
            window_end=window_end,
            passed=passed,
            severity=severity,
            reason=reason,
            detail=f"active_days={active_days}, window_days={window_days}",
            synthetic=synthetic,
        ))
    return results


def check_impossible_values(
    observations: List[Observation],
) -> List[QualityResult]:
    """Check for impossible token values (negative, all-zero, etc.)."""
    results: List[QualityResult] = []
    for o in observations:
        issues = []
        if o.I < 0:
            issues.append("negative input_tokens")
        if o.O < 0:
            issues.append("negative output_tokens")
        if o.R < 0:
            issues.append("negative cache_read_tokens")
        if o.W < 0:
            issues.append("negative cache_write_tokens")
        if o.I == 0 and o.O == 0 and o.R == 0 and o.W == 0:
            # Zero-activity days are sparse, not impossible — warn rather than block.
            results.append(QualityResult(
                check_id="impossible_values",
                operator_id=o.operator_id,
                window_start=o.timestamp.date(),
                window_end=o.timestamp.date(),
                passed=True,
                severity=QualitySeverity.WARNING,
                reason="all token counts are zero (zero-activity day)",
                detail=f"observation_id={o.observation_id}",
                synthetic=o.synthetic,
            ))
            continue

        if issues:
            results.append(QualityResult(
                check_id="impossible_values",
                operator_id=o.operator_id,
                window_start=o.timestamp.date(),
                window_end=o.timestamp.date(),
                passed=False,
                severity=QualitySeverity.BLOCKING,
                reason="; ".join(issues),
                detail=f"observation_id={o.observation_id}",
                synthetic=o.synthetic,
            ))
    return results


def check_duplicates(
    observations: List[Observation],
) -> List[QualityResult]:
    """Check for duplicate observation IDs."""
    id_counts = Counter(o.observation_id for o in observations)
    dupes = {oid: count for oid, count in id_counts.items() if count > 1}

    results: List[QualityResult] = []
    for obs_id, count in dupes.items():
        # Find the first observation with this ID for context
        first = next(o for o in observations if o.observation_id == obs_id)
        results.append(QualityResult(
            check_id="duplicate_ids",
            operator_id=first.operator_id,
            window_start=first.timestamp.date(),
            window_end=first.timestamp.date(),
            passed=False,
            severity=QualitySeverity.BLOCKING,
            reason=f"observation_id '{obs_id}' appears {count} times",
            synthetic=first.synthetic,
        ))
    return results


def check_provenance(
    observations: List[Observation],
) -> List[QualityResult]:
    """Check that all observations have provenance set."""
    results: List[QualityResult] = []
    for o in observations:
        if not o.provenance:
            results.append(QualityResult(
                check_id="provenance",
                operator_id=o.operator_id,
                window_start=o.timestamp.date(),
                window_end=o.timestamp.date(),
                passed=False,
                severity=QualitySeverity.WARNING,
                reason="no provenance set",
                detail=f"observation_id={o.observation_id}",
                synthetic=o.synthetic,
            ))
    return results


def check_sparse_operators(
    operator_ids: List[str],
    observations: List[Observation],
    window_start: date,
    window_end: date,
    min_obs: int = 5,
) -> List[QualityResult]:
    """Check for operators with too few observations to support valid comparison."""
    results: List[QualityResult] = []
    for oid in operator_ids:
        obs = [o for o in observations if o.operator_id == oid
               and window_start <= o.timestamp.date() <= window_end]
        count = len(obs)
        synthetic = any(o.synthetic for o in obs)

        if count < min_obs:
            results.append(QualityResult(
                check_id="sparse_operator",
                operator_id=oid,
                window_start=window_start,
                window_end=window_end,
                passed=False,
                severity=QualitySeverity.BLOCKING,
                reason=f"only {count} observations (min {min_obs})",
                synthetic=synthetic,
            ))
    return results


def check_source_confidence(
    observations: List[Observation],
) -> List[QualityResult]:
    """Check for low or missing source_confidence that gates cross-provider comparison.

    Observations with source_confidence='low' or None should not be directly
    compared to high-confidence sources without an explicit caveat.
    """
    results: List[QualityResult] = []
    for o in observations:
        sc = o.source_confidence
        if sc is None:
            results.append(QualityResult(
                check_id="source_confidence",
                operator_id=o.operator_id,
                window_start=o.timestamp.date(),
                window_end=o.timestamp.date(),
                passed=True,
                severity=QualitySeverity.WARNING,
                reason="source_confidence not set — comparison caveats unavailable",
                detail=f"observation_id={o.observation_id}",
                synthetic=o.synthetic,
            ))
        elif sc == "low":
            results.append(QualityResult(
                check_id="source_confidence",
                operator_id=o.operator_id,
                window_start=o.timestamp.date(),
                window_end=o.timestamp.date(),
                passed=False,
                severity=QualitySeverity.WARNING,
                reason="low source_confidence — do not compare to high-confidence sources without caveat",
                detail=f"observation_id={o.observation_id}",
                synthetic=o.synthetic,
            ))
    return results


def run_all_quality_checks(
    operator_ids: List[str],
    observations: List[Observation],
    window_start: date,
    window_end: date,
) -> Dict[str, List[QualityResult]]:
    """Run all data quality checks and return results grouped by check type."""
    return {
        "missingness": check_missingness(operator_ids, observations, window_start, window_end),
        "impossible_values": check_impossible_values(observations),
        "duplicates": check_duplicates(observations),
        "provenance": check_provenance(observations),
        "source_confidence": check_source_confidence(observations),
        "sparse_operators": check_sparse_operators(operator_ids, observations, window_start, window_end),
    }


def summarize_quality(
    results: Dict[str, List[QualityResult]],
) -> Dict[str, int]:
    """Summarize quality check results into counts by severity."""
    counts = {"OK": 0, "WARNING": 0, "BLOCKING": 0}
    for check_results in results.values():
        for r in check_results:
            counts[r.severity.value] = counts.get(r.severity.value, 0) + 1
    return counts
