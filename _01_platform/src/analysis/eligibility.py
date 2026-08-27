"""Eligibility checks — determine which operators can be validly compared.

P0 acceptance: "quality failures block misleading comparisons."
An operator is eligible if they have sufficient observations, active days,
and token volume within the evaluation window.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.observation import Observation
from domain.quality_result import QualityResult, QualitySeverity


# Default eligibility thresholds.
MIN_OBSERVATIONS = 7       # at least 7 observations in the window
MIN_ACTIVE_DAYS = 5        # at least 5 distinct active days
MIN_TOTAL_TOKENS = 1000    # at least 1000 total tokens (I+O+R+W)


@dataclass(frozen=True, slots=True)
class EligibilityConfig:
    min_observations: int = MIN_OBSERVATIONS
    min_active_days: int = MIN_ACTIVE_DAYS
    min_total_tokens: int = MIN_TOTAL_TOKENS


def check_eligibility(
    operator_id: str,
    observations: List[Observation],
    window_start: date,
    window_end: date,
    config: Optional[EligibilityConfig] = None,
) -> QualityResult:
    """Check if an operator is eligible for valid comparison.

    Returns a QualityResult with passed=True if eligible, or
    passed=False with severity=BLOCKING if not.
    """
    cfg = config or EligibilityConfig()

    obs_in_window = [
        o for o in observations
        if o.operator_id == operator_id
        and window_start <= o.timestamp.date() <= window_end
    ]

    obs_count = len(obs_in_window)
    active_days = len(set(o.timestamp.date() for o in obs_in_window))
    total_tokens = sum(o.I + o.O + o.R + o.W for o in obs_in_window)

    synthetic = any(o.synthetic for o in obs_in_window)

    failures = []
    if obs_count < cfg.min_observations:
        failures.append(f"observations={obs_count} < {cfg.min_observations}")
    if active_days < cfg.min_active_days:
        failures.append(f"active_days={active_days} < {cfg.min_active_days}")
    if total_tokens < cfg.min_total_tokens:
        failures.append(f"total_tokens={total_tokens} < {cfg.min_total_tokens}")

    if failures:
        return QualityResult(
            check_id="eligibility",
            operator_id=operator_id,
            window_start=window_start,
            window_end=window_end,
            passed=False,
            severity=QualitySeverity.BLOCKING,
            reason="; ".join(failures),
            detail=f"obs_count={obs_count}, active_days={active_days}, total_tokens={total_tokens}",
            synthetic=synthetic,
        )
    return QualityResult(
        check_id="eligibility",
        operator_id=operator_id,
        window_start=window_start,
        window_end=window_end,
        passed=True,
        severity=QualitySeverity.OK,
        reason=f"eligible: {obs_count} obs, {active_days} active days, {total_tokens} tokens",
        synthetic=synthetic,
    )


def check_cohort_eligibility(
    operator_ids: List[str],
    observations: List[Observation],
    window_start: date,
    window_end: date,
    config: Optional[EligibilityConfig] = None,
) -> Dict[str, QualityResult]:
    """Check eligibility for all operators in a cohort."""
    return {
        oid: check_eligibility(oid, observations, window_start, window_end, config)
        for oid in operator_ids
    }
