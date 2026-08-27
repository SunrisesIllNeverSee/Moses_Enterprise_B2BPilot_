"""Pre/post verifier — compares baseline vs follow-up metric deltas.

Per `21` P1 acceptance:
- "pre/post verifier shows target + non-target metric deltas"
- "intervention failure is representable and reportable"

The verifier computes deltas for ALL canonical metrics, not just the target,
so that unintended side effects are visible. It explicitly represents
NEGATIVE and NO_EFFECT outcomes.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.intervention import Intervention, InterventionOutcome
from domain.measurement import Measurement
from metrics.engine import ScoringEngine


@dataclass(frozen=True, slots=True)
class MetricDelta:
    """Delta for a single metric between baseline and follow-up."""
    metric_id: str
    baseline_value: Optional[float]
    followup_value: Optional[float]
    absolute_delta: Optional[float]
    percent_delta: Optional[float]
    is_target: bool  # True if this is the intervention's target metric

    def to_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "baseline": self.baseline_value,
            "followup": self.followup_value,
            "absolute_delta": self.absolute_delta,
            "percent_delta": self.percent_delta,
            "is_target": self.is_target,
        }


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Full pre/post verification result for an intervention."""
    intervention_id: str
    operator_id: str
    target_metric: str
    baseline_window: Tuple[date, date]
    followup_window: Tuple[date, date]
    deltas: List[MetricDelta]
    outcome: InterventionOutcome
    target_delta: Optional[MetricDelta]
    non_target_deltas: List[MetricDelta]
    summary: str
    synthetic: bool

    def to_dict(self) -> dict:
        return {
            "intervention_id": self.intervention_id,
            "operator_id": self.operator_id,
            "target_metric": self.target_metric,
            "baseline_window": [self.baseline_window[0].isoformat(), self.baseline_window[1].isoformat()],
            "followup_window": [self.followup_window[0].isoformat(), self.followup_window[1].isoformat()],
            "deltas": [d.to_dict() for d in self.deltas],
            "outcome": self.outcome.value,
            "target_delta": self.target_delta.to_dict() if self.target_delta else None,
            "non_target_deltas": [d.to_dict() for d in self.non_target_deltas],
            "summary": self.summary,
            "synthetic": self.synthetic,
        }


class PrePostVerifier:
    """Verifies pre/post intervention metric changes.

    Computes deltas for ALL canonical metrics (target + non-target) so
    unintended side effects are visible. Represents all outcomes including
    NEGATIVE and NO_EFFECT.
    """

    def __init__(self, engine: Optional[ScoringEngine] = None) -> None:
        self.engine = engine or ScoringEngine()

    def verify(
        self,
        intervention: Intervention,
        observations: list,
        baseline_start: date,
        baseline_end: date,
    ) -> VerificationResult:
        """Verify an intervention by comparing baseline vs follow-up metrics.

        Args:
            intervention: the intervention to verify
            observations: the operator's observations (must span both windows)
            baseline_start/end: the baseline evaluation window
        """
        # Follow-up window: intervention start + followup_days
        followup_start = intervention.start_date
        followup_end = intervention.start_date + timedelta(days=intervention.followup_days)

        # Score both windows
        baseline_ms = self.engine.score_operator(
            intervention.operator_id, observations, baseline_start, baseline_end
        )
        followup_ms = self.engine.score_operator(
            intervention.operator_id, observations, followup_start, followup_end
        )

        # Build metric maps
        baseline_map = {m.metric_id: m for m in baseline_ms}
        followup_map = {m.metric_id: m for m in followup_ms}

        # Compute deltas for ALL canonical metrics
        all_metric_ids = set(baseline_map.keys()) | set(followup_map.keys())
        deltas: List[MetricDelta] = []
        target_delta: Optional[MetricDelta] = None
        non_target_deltas: List[MetricDelta] = []

        for mid in sorted(all_metric_ids):
            b = baseline_map.get(mid)
            f = followup_map.get(mid)
            b_val = b.value if b and b.value is not None else None
            f_val = f.value if f and f.value is not None else None

            abs_delta = None
            pct_delta = None
            if b_val is not None and f_val is not None:
                abs_delta = round(f_val - b_val, 4)
                if b_val != 0:
                    pct_delta = round((f_val - b_val) / b_val * 100, 2)

            is_target = (mid == intervention.target_metric)
            delta = MetricDelta(
                metric_id=mid,
                baseline_value=b_val,
                followup_value=f_val,
                absolute_delta=abs_delta,
                percent_delta=pct_delta,
                is_target=is_target,
            )
            deltas.append(delta)
            if is_target:
                target_delta = delta
            else:
                non_target_deltas.append(delta)

        # Build summary
        if target_delta and target_delta.percent_delta is not None:
            summary = f"Target metric '{intervention.target_metric}': {target_delta.percent_delta:+.1f}%"
        else:
            summary = f"Target metric '{intervention.target_metric}': no data in follow-up window"

        if non_target_deltas:
            non_target_summary = "; ".join(
                f"{d.metric_id}: {d.percent_delta:+.1f}%" if d.percent_delta is not None
                else f"{d.metric_id}: N/A"
                for d in non_target_deltas
            )
            summary += f" | Non-target: {non_target_summary}"

        return VerificationResult(
            intervention_id=intervention.intervention_id,
            operator_id=intervention.operator_id,
            target_metric=intervention.target_metric,
            baseline_window=(baseline_start, baseline_end),
            followup_window=(followup_start, followup_end),
            deltas=deltas,
            outcome=intervention.synthetic_outcome,
            target_delta=target_delta,
            non_target_deltas=non_target_deltas,
            summary=summary,
            synthetic=intervention.synthetic,
        )

    def verify_with_outcome(
        self,
        intervention: Intervention,
        observations: list,
        baseline_start: date,
        baseline_end: date,
        outcome: InterventionOutcome,
    ) -> VerificationResult:
        """Verify with an explicit outcome (e.g. from external assessment).

        Per P1: "intervention failure is representable and reportable."
        This method allows representing NEGATIVE and NO_EFFECT outcomes.
        """
        # Close the intervention with the declared outcome first
        from interventions.manager import InterventionManager
        mgr = InterventionManager()
        closed = mgr.close(intervention, outcome)
        return self.verify(closed, observations, baseline_start, baseline_end)
