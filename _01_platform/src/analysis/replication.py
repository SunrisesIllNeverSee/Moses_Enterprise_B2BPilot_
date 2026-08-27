"""Replicated validation — checks whether findings hold across splits.

Per `16` P2 remaining: "replicated validation — not built."

A "finding" is a descriptive result from the pilot: a detected pattern, a
divergence class, or a workflow fit claim. Replication checks whether the
finding is stable across:

    1. Window split — two non-overlapping time windows (e.g. first 15 days
       vs last 15 days of the 30-day cohort window)
    2. Cohort split — two random halves of the operator population

Replication is about stability of the descriptive finding, NOT about causal
validation. A finding that replicates is more trustworthy as a description;
a finding that does not replicate should be treated with caution.

Result statuses:
    REPLICATED         — finding appears in both splits
    NOT_REPLICATED     — finding appears in only one split
    INSUFFICIENT_DATA  — one or both splits have too few observations
"""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.observation import Observation
from metrics.engine import ScoringEngine


class ReplicationStatus(str, Enum):
    REPLICATED = "REPLICATED"
    NOT_REPLICATED = "NOT_REPLICATED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class SplitMethod(str, Enum):
    WINDOW = "window"    # split by time: first half vs second half
    COHORT = "cohort"    # split by operator: random halves


@dataclass(frozen=True, slots=True)
class ReplicationResult:
    """Result of replicating a finding across a split."""
    finding_type: str          # "pattern" | "divergence" | "fit_claim"
    finding_id: str            # pattern_id, divergence_class, or stage_id
    split_method: str          # "window" | "cohort"
    status: str                # ReplicationStatus value
    split_a_count: int         # observations or operators in split A
    split_b_count: int         # observations or operators in split B
    split_a_found: bool        # finding present in split A
    split_b_found: bool        # finding present in split B
    synthetic: bool
    caveat: str                # always present — replication is descriptive, not causal

    def to_dict(self) -> dict:
        return {
            "finding_type": self.finding_type,
            "finding_id": self.finding_id,
            "split_method": self.split_method,
            "status": self.status,
            "split_a_count": self.split_a_count,
            "split_b_count": self.split_b_count,
            "split_a_found": self.split_a_found,
            "split_b_found": self.split_b_found,
            "synthetic": self.synthetic,
            "caveat": self.caveat,
        }


# Minimum observations per split for the finding to be evaluable
MIN_OBS_PER_SPLIT = 5
# Minimum operators per cohort split
MIN_OPERATORS_PER_SPLIT = 3


class ReplicationEngine:
    """Checks whether findings hold across window or cohort splits.

    Replication is descriptive stability, not causal validation.
    """

    def __init__(self, engine: Optional[ScoringEngine] = None) -> None:
        self.engine = engine or ScoringEngine()

    def replicate_pattern(
        self,
        pattern_id: str,
        operator_id: str,
        observations: List[Observation],
        window_start: date,
        window_end: date,
        split_method: SplitMethod = SplitMethod.WINDOW,
        reference_population=None,
    ) -> ReplicationResult:
        """Check if a pattern replicates across a split.

        For window split: score the operator in first-half and second-half
        windows, then re-detect the pattern in each.

        For cohort split: split the operator's observations into two random
        halves (by observation, not by time) and re-detect the pattern in
        each half. This tests whether the pattern is stable across
        different samples of the operator's own activity.
        """
        if split_method == SplitMethod.WINDOW:
            return self._replicate_pattern_window(
                pattern_id, operator_id, observations,
                window_start, window_end,
                reference_population,
            )
        else:
            return self._replicate_pattern_cohort(
                pattern_id, operator_id, observations,
                window_start, window_end,
                reference_population,
            )

    def _replicate_pattern_window(
        self,
        pattern_id: str,
        operator_id: str,
        observations: List[Observation],
        window_start: date,
        window_end: date,
        reference_population=None,
    ) -> ReplicationResult:
        """Split the window in half and check pattern in each half."""
        from diagnostics import PatternEngine

        total_days = (window_end - window_start).days
        if total_days < 2:
            return ReplicationResult(
                finding_type="pattern",
                finding_id=pattern_id,
                split_method="window",
                status=ReplicationStatus.INSUFFICIENT_DATA.value,
                split_a_count=0, split_b_count=0,
                split_a_found=False, split_b_found=False,
                synthetic=True,
                caveat="Window too short to split.",
            )

        mid = window_start + timedelta(days=total_days // 2)

        # Split observations by timestamp
        obs_a = [o for o in observations if o.timestamp.date() <= mid]
        obs_b = [o for o in observations if o.timestamp.date() > mid]

        if len(obs_a) < MIN_OBS_PER_SPLIT or len(obs_b) < MIN_OBS_PER_SPLIT:
            return ReplicationResult(
                finding_type="pattern",
                finding_id=pattern_id,
                split_method="window",
                status=ReplicationStatus.INSUFFICIENT_DATA.value,
                split_a_count=len(obs_a),
                split_b_count=len(obs_b),
                split_a_found=False,
                split_b_found=False,
                synthetic=True,
                caveat=f"Insufficient observations in one or both splits (min {MIN_OBS_PER_SPLIT} per split).",
            )

        # Detect patterns in each half
        engine = PatternEngine()

        ms_a = self.engine.score_operator(operator_id, obs_a, window_start, mid)
        ms_b = self.engine.score_operator(operator_id, obs_b, mid + timedelta(days=1), window_end)

        patterns_a = engine.detect_patterns(operator_id, ms_a, reference_population, None, window_start, mid)
        patterns_b = engine.detect_patterns(operator_id, ms_b, reference_population, None, mid + timedelta(days=1), window_end)

        found_a = any(p.pattern_id == pattern_id for p in patterns_a)
        found_b = any(p.pattern_id == pattern_id for p in patterns_b)

        if found_a and found_b:
            status = ReplicationStatus.REPLICATED
        elif found_a or found_b:
            status = ReplicationStatus.NOT_REPLICATED
        else:
            status = ReplicationStatus.NOT_REPLICATED

        return ReplicationResult(
            finding_type="pattern",
            finding_id=pattern_id,
            split_method="window",
            status=status.value,
            split_a_count=len(obs_a),
            split_b_count=len(obs_b),
            split_a_found=found_a,
            split_b_found=found_b,
            synthetic=True,
            caveat="Replication is descriptive stability, not causal validation.",
        )

    def _replicate_pattern_cohort(
        self,
        pattern_id: str,
        operator_id: str,
        observations: List[Observation],
        window_start: date,
        window_end: date,
        reference_population=None,
        seed: int = 42,
    ) -> ReplicationResult:
        """Split the operator's observations into two random halves and check
        pattern in each half.

        This tests whether the pattern is stable across different samples of
        the operator's own activity, rather than across time windows.
        Uses a fixed seed for reproducibility.
        """
        from diagnostics import PatternEngine

        if len(observations) < 2 * MIN_OBS_PER_SPLIT:
            return ReplicationResult(
                finding_type="pattern",
                finding_id=pattern_id,
                split_method="cohort",
                status=ReplicationStatus.INSUFFICIENT_DATA.value,
                split_a_count=0, split_b_count=0,
                split_a_found=False, split_b_found=False,
                synthetic=True,
                caveat=f"Insufficient observations for cohort split (need {2 * MIN_OBS_PER_SPLIT}, got {len(observations)}).",
            )

        rng = random.Random(seed)
        shuffled = list(observations)
        rng.shuffle(shuffled)
        mid = len(shuffled) // 2
        obs_a = shuffled[:mid]
        obs_b = shuffled[mid:]

        if len(obs_a) < MIN_OBS_PER_SPLIT or len(obs_b) < MIN_OBS_PER_SPLIT:
            return ReplicationResult(
                finding_type="pattern",
                finding_id=pattern_id,
                split_method="cohort",
                status=ReplicationStatus.INSUFFICIENT_DATA.value,
                split_a_count=len(obs_a), split_b_count=len(obs_b),
                split_a_found=False, split_b_found=False,
                synthetic=True,
                caveat=f"Insufficient observations in one or both splits (min {MIN_OBS_PER_SPLIT} per split).",
            )

        engine = PatternEngine()

        ms_a = self.engine.score_operator(operator_id, obs_a, window_start, window_end)
        ms_b = self.engine.score_operator(operator_id, obs_b, window_start, window_end)

        patterns_a = engine.detect_patterns(operator_id, ms_a, reference_population, None, window_start, window_end)
        patterns_b = engine.detect_patterns(operator_id, ms_b, reference_population, None, window_start, window_end)

        found_a = any(p.pattern_id == pattern_id for p in patterns_a)
        found_b = any(p.pattern_id == pattern_id for p in patterns_b)

        if found_a and found_b:
            status = ReplicationStatus.REPLICATED
        else:
            status = ReplicationStatus.NOT_REPLICATED

        return ReplicationResult(
            finding_type="pattern",
            finding_id=pattern_id,
            split_method="cohort",
            status=status.value,
            split_a_count=len(obs_a),
            split_b_count=len(obs_b),
            split_a_found=found_a,
            split_b_found=found_b,
            synthetic=True,
            caveat="Replication is descriptive stability, not causal validation.",
        )

    def replicate_divergence(
        self,
        operator_id: str,
        observations: List[Observation],
        all_operator_ids: List[str],
        all_observations: List[Observation],
        window_start: date,
        window_end: date,
        split_method: SplitMethod = SplitMethod.WINDOW,
        seed: int = 42,
    ) -> ReplicationResult:
        """Check if an operator's divergence class replicates across a split.

        For window split: split observations by time (first half vs second
        half) and check if the operator's divergence class is the same in
        both halves.

        For cohort split: split the operator population into two random
        halves and check if the target operator's divergence class is the
        same when computed against each half's reference population.
        """
        if split_method == SplitMethod.WINDOW:
            total_days = (window_end - window_start).days
            if total_days < 2:
                return ReplicationResult(
                    finding_type="divergence",
                    finding_id=operator_id,
                    split_method="window",
                    status=ReplicationStatus.INSUFFICIENT_DATA.value,
                    split_a_count=0, split_b_count=0,
                    split_a_found=False, split_b_found=False,
                    synthetic=True,
                    caveat="Window too short to split.",
                )

            mid = window_start + timedelta(days=total_days // 2)
            obs_a = [o for o in all_observations if o.timestamp.date() <= mid]
            obs_b = [o for o in all_observations if o.timestamp.date() > mid]

            if len(obs_a) < MIN_OBS_PER_SPLIT or len(obs_b) < MIN_OBS_PER_SPLIT:
                return ReplicationResult(
                    finding_type="divergence",
                    finding_id=operator_id,
                    split_method="window",
                    status=ReplicationStatus.INSUFFICIENT_DATA.value,
                    split_a_count=len(obs_a), split_b_count=len(obs_b),
                    split_a_found=False, split_b_found=False,
                    synthetic=True,
                    caveat=f"Insufficient observations in one or both splits.",
                )

            # Compute divergence for each half
            div_a = self._compute_divergence_for_obs(all_operator_ids, obs_a, window_start, mid)
            div_b = self._compute_divergence_for_obs(all_operator_ids, obs_b, mid + timedelta(days=1), window_end)

            # Check if the operator's divergence class is the same in both.
            # Compare the full class string — not a truncated prefix — so
            # that LOW_USAGE_HIGH_OPERATION and LOW_LOW are not conflated.
            class_a = div_a.get(operator_id, "")
            class_b = div_b.get(operator_id, "")

            found_a = bool(class_a)
            found_b = bool(class_b)

            if found_a and found_b and class_a == class_b:
                status = ReplicationStatus.REPLICATED
            else:
                status = ReplicationStatus.NOT_REPLICATED

            return ReplicationResult(
                finding_type="divergence",
                finding_id=operator_id,
                split_method="window",
                status=status.value,
                split_a_count=len(obs_a),
                split_b_count=len(obs_b),
                split_a_found=found_a,
                split_b_found=found_b,
                synthetic=True,
                caveat="Replication is descriptive stability, not causal validation.",
            )

        # Cohort split: split operators into two random halves
        return self._replicate_divergence_cohort(
            operator_id, all_operator_ids, all_observations,
            window_start, window_end, seed,
        )

    def _replicate_divergence_cohort(
        self,
        operator_id: str,
        all_operator_ids: List[str],
        all_observations: List[Observation],
        window_start: date,
        window_end: date,
        seed: int = 42,
    ) -> ReplicationResult:
        """Split the operator population into two random halves and check if
        the target operator's divergence class holds in both.

        The target operator must be in both halves for the finding to be
        evaluable. Each half builds its own reference population from its
        own members.
        """
        if operator_id not in all_operator_ids:
            return ReplicationResult(
                finding_type="divergence",
                finding_id=operator_id,
                split_method="cohort",
                status=ReplicationStatus.INSUFFICIENT_DATA.value,
                split_a_count=0, split_b_count=0,
                split_a_found=False, split_b_found=False,
                synthetic=True,
                caveat=f"Operator {operator_id} not in cohort.",
            )

        if len(all_operator_ids) < 2 * MIN_OPERATORS_PER_SPLIT:
            return ReplicationResult(
                finding_type="divergence",
                finding_id=operator_id,
                split_method="cohort",
                status=ReplicationStatus.INSUFFICIENT_DATA.value,
                split_a_count=0, split_b_count=0,
                split_a_found=False, split_b_found=False,
                synthetic=True,
                caveat=f"Insufficient operators for cohort split (need {2 * MIN_OPERATORS_PER_SPLIT}, got {len(all_operator_ids)}).",
            )

        rng = random.Random(seed)
        shuffled_ids = [oid for oid in all_operator_ids if oid != operator_id]
        rng.shuffle(shuffled_ids)
        # Distribute the non-target operators evenly, then add the target
        # to both halves so its divergence can be computed in each.
        mid = len(shuffled_ids) // 2
        half_a = shuffled_ids[:mid] + [operator_id]
        half_b = shuffled_ids[mid:] + [operator_id]

        if len(half_a) < MIN_OPERATORS_PER_SPLIT or len(half_b) < MIN_OPERATORS_PER_SPLIT:
            return ReplicationResult(
                finding_type="divergence",
                finding_id=operator_id,
                split_method="cohort",
                status=ReplicationStatus.INSUFFICIENT_DATA.value,
                split_a_count=len(half_a), split_b_count=len(half_b),
                split_a_found=False, split_b_found=False,
                synthetic=True,
                caveat=f"Insufficient operators in one or both splits (min {MIN_OPERATORS_PER_SPLIT} per split).",
            )

        obs_a = [o for o in all_observations if o.operator_id in half_a]
        obs_b = [o for o in all_observations if o.operator_id in half_b]

        if len(obs_a) < MIN_OBS_PER_SPLIT or len(obs_b) < MIN_OBS_PER_SPLIT:
            return ReplicationResult(
                finding_type="divergence",
                finding_id=operator_id,
                split_method="cohort",
                status=ReplicationStatus.INSUFFICIENT_DATA.value,
                split_a_count=len(obs_a), split_b_count=len(obs_b),
                split_a_found=False, split_b_found=False,
                synthetic=True,
                caveat=f"Insufficient observations in one or both splits (min {MIN_OBS_PER_SPLIT} per split).",
            )

        div_a = self._compute_divergence_for_obs(half_a, obs_a, window_start, window_end)
        div_b = self._compute_divergence_for_obs(half_b, obs_b, window_start, window_end)

        # Compare the full class string — not a truncated prefix.
        class_a = div_a.get(operator_id, "")
        class_b = div_b.get(operator_id, "")

        found_a = bool(class_a)
        found_b = bool(class_b)

        if found_a and found_b and class_a == class_b:
            status = ReplicationStatus.REPLICATED
        else:
            status = ReplicationStatus.NOT_REPLICATED

        return ReplicationResult(
            finding_type="divergence",
            finding_id=operator_id,
            split_method="cohort",
            status=status.value,
            split_a_count=len(half_a),
            split_b_count=len(half_b),
            split_a_found=found_a,
            split_b_found=found_b,
            synthetic=True,
            caveat="Replication is descriptive stability, not causal validation.",
        )

    def _compute_divergence_for_obs(
        self,
        operator_ids: List[str],
        observations: List[Observation],
        window_start: date,
        window_end: date,
    ) -> Dict[str, str]:
        """Compute divergence classes for a set of observations.

        Uses the split's own cohort as its reference for replication purposes.
        In production, the full reference population would be used.
        """
        from analysis import compute_divergence, compute_percentiles
        from domain.reference_population import ReferencePopulation

        all_ms = self.engine.score_cohort(operator_ids, observations, window_start, window_end)
        flat_ms = [m for ms in all_ms.values() for m in ms]

        usage_tokens: Dict[str, int] = {}
        for obs in observations:
            usage_tokens[obs.operator_id] = usage_tokens.get(obs.operator_id, 0) + obs.I + obs.O + obs.R + obs.W

        # Build a reference population from the split's own measurements
        distributions: Dict[str, dict] = {}
        for mid in ("leverage", "yield", "token_snr", "construction"):
            vals = sorted(m.value for m in flat_ms if m.metric_id == mid and m.value is not None)
            if vals:
                n = len(vals)
                distributions[mid] = {
                    "p10": vals[n // 10] if n >= 10 else vals[0],
                    "p50": vals[n // 2],
                    "p90": vals[n * 9 // 10] if n >= 10 else vals[-1],
                }

        ref = ReferencePopulation(
            reference_id="replication-internal",
            version="replication-internal",
            date=window_start,
            description="Internal reference built from split cohort for replication",
            distributions=distributions,
            synthetic=True,
        )

        pcts = compute_percentiles(flat_ms, ref)
        divs = compute_divergence(pcts, usage_tokens)

        return {d.operator_id: d.divergence_class for d in divs}
