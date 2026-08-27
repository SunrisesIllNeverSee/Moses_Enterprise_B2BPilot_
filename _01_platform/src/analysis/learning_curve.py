"""EVAL-015 — AI Learning Curve.

Models operator improvement trajectories over time. The core question:
how fast is an operator improving, what shape is their learning curve,
and have they plateaued?

Per spec 18:
    Input: longitudinal measurement + intervention history.
    Output: rate/shape of operator change with uncertainty.

Per Build B §6.5 (Learning Curve Eval):
    This eval divides the observation period into N consecutive windows,
    scores each operator in each window, and then models the trajectory
    of their composite metric (or individual metrics) over time:

    - Improvement rate: the slope of the metric over time windows
      (percent change per window). Positive = improving.
    - Curve shape: linear / diminishing / accelerating. Determined by
      comparing the slope in the first half vs the second half of windows.
    - Uncertainty bounds: confidence interval on the slope estimate,
      derived from the variability of per-window values.
    - Plateau detection: if the last 2+ windows show < 2% change, the
      operator may have plateaued.

    Intervention history (if available) provides context: an intervention
    between windows W2 and W3 may explain a slope change. This is
    ASSOCIATION, not CAUSATION — the module notes the temporal co-occurrence
    but does not claim the intervention caused the change.

All metrics are content-free (token counts only). No punitive labels or
leaderboards. Outcome claims are ASSOCIATION, never CAUSATION. Curve shape
labels are developmental observations, not personnel judgments.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.measurement import Measurement
from domain.observation import Observation
from domain.operator import Operator
from metrics.engine import ScoringEngine


@dataclass(frozen=True, slots=True)
class MetricLearningCurve:
    """One metric's learning curve for one operator."""
    metric_id: str
    window_values: List[Optional[float]]
    improvement_rate: float  # percent change per window (slope)
    curve_shape: str  # "linear" | "diminishing" | "accelerating" | "flat" | "insufficient"
    uncertainty_lower: float  # lower bound on improvement rate
    uncertainty_upper: float  # upper bound on improvement rate
    plateaued: bool
    plateau_description: str

    def to_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "window_values": [round(v, 4) if v is not None else None for v in self.window_values],
            "improvement_rate": round(self.improvement_rate, 4),
            "curve_shape": self.curve_shape,
            "uncertainty_lower": round(self.uncertainty_lower, 4),
            "uncertainty_upper": round(self.uncertainty_upper, 4),
            "plateaued": self.plateaued,
            "plateau_description": self.plateau_description,
        }


@dataclass(frozen=True, slots=True)
class OperatorLearningCurve:
    """One operator's complete learning curve analysis."""
    operator_id: str
    pseudonym: str
    team: Optional[str]
    window_labels: List[str]
    metric_curves: List[MetricLearningCurve] = field(default_factory=list)
    overall_improvement_rate: float = 0.0
    overall_curve_shape: str = ""
    overall_plateaued: bool = False
    intervention_context: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "pseudonym": self.pseudonym,
            "team": self.team,
            "window_labels": list(self.window_labels),
            "metric_curves": [c.to_dict() for c in self.metric_curves],
            "overall_improvement_rate": round(self.overall_improvement_rate, 4),
            "overall_curve_shape": self.overall_curve_shape,
            "overall_plateaued": self.overall_plateaued,
            "intervention_context": list(self.intervention_context),
            "note": self.note,
        }


@dataclass(frozen=True, slots=True)
class LearningCurveAnalysis:
    """The complete learning-curve analysis result."""
    window_count: int
    window_labels: List[str] = field(default_factory=list)
    operator_curves: List[OperatorLearningCurve] = field(default_factory=list)
    cohort_improvement_rate: float = 0.0
    cohort_plateau_count: int = 0
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "window_count": self.window_count,
            "window_labels": list(self.window_labels),
            "operator_curves": [c.to_dict() for c in self.operator_curves],
            "cohort_improvement_rate": round(self.cohort_improvement_rate, 4),
            "cohort_plateau_count": self.cohort_plateau_count,
            "summary": self.summary,
        }


def _linear_slope(values: List[float]) -> float:
    """Compute the slope of a simple linear regression: y = a + b*x.

    Returns b (slope). x values are 0, 1, 2, ... n-1.
    """
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _slope_to_percent_rate(slope: float, values: List[float]) -> float:
    """Convert absolute slope to percent change per window.

    Uses the mean of the values as the base.
    """
    if not values:
        return 0.0
    mean_val = sum(values) / len(values)
    if mean_val == 0:
        return 0.0
    return (slope / abs(mean_val)) * 100.0


def _uncertainty_bounds(values: List[float], slope: float) -> Tuple[float, float]:
    """Compute uncertainty bounds on the slope estimate.

    Uses the standard error of the regression slope. The 95% CI is
    approximately slope ± 2 * SE.
    """
    n = len(values)
    if n < 3:
        # With < 3 points, uncertainty is very high.
        return slope - abs(slope), slope + abs(slope)
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    # Residuals
    predicted = [slope * (i - x_mean) + y_mean for i in range(n)]
    residuals = [v - p for v, p in zip(values, predicted)]
    # Residual sum of squares
    rss = sum(r ** 2 for r in residuals)
    # Standard error of slope: SE = sqrt(RSS / (n-2)) / sqrt(sum((x - x_mean)^2))
    sxx = sum((i - x_mean) ** 2 for i in range(n))
    if sxx == 0:
        return slope, slope
    se = math.sqrt(rss / (n - 2)) / math.sqrt(sxx)
    return slope - 2 * se, slope + 2 * se


def _curve_shape(values: List[float]) -> str:
    """Determine the shape of the learning curve.

    Compares the slope in the first half vs the second half of the data:
    - If second-half slope is much smaller than first → "diminishing"
    - If second-half slope is much larger than first → "accelerating"
    - If both slopes are similar → "linear"
    - If both slopes are near zero → "flat"
    """
    n = len(values)
    if n < 3:
        return "insufficient"
    mid = n // 2
    first_half = values[:mid + 1]
    second_half = values[mid:]
    slope1 = _linear_slope(first_half)
    slope2 = _linear_slope(second_half)

    # Threshold for "near zero"
    mean_val = sum(values) / n if n > 0 else 0
    threshold = abs(mean_val) * 0.02 if mean_val != 0 else 0.01

    if abs(slope1) < threshold and abs(slope2) < threshold:
        return "flat"

    if slope1 > 0 and slope2 < slope1 * 0.5:
        return "diminishing"
    if slope1 < 0 and slope2 > slope1 * 0.5:
        return "diminishing"  # decline is slowing
    if slope2 > slope1 * 1.5 and slope1 > 0:
        return "accelerating"
    if slope2 < slope1 * 1.5 and slope1 < 0:
        return "accelerating"  # decline is accelerating
    return "linear"


def _detect_plateau(values: List[Optional[float]]) -> Tuple[bool, str]:
    """Detect if the operator has plateaued.

    A plateau is declared if the last 2+ windows show < 2% change
    relative to their mean.
    """
    valid = [v for v in values if v is not None]
    if len(valid) < 3:
        return False, "insufficient data for plateau detection"
    # Check the last 2+ windows.
    tail = valid[-2:] if len(valid) >= 2 else [valid[-1]]
    if len(tail) < 2:
        return False, "insufficient data for plateau detection"
    mean_tail = sum(tail) / len(tail)
    if mean_tail == 0:
        # If all zeros, that's a plateau of sorts.
        return True, "Last windows are flat at zero."
    max_change = max(abs(t - mean_tail) for t in tail) / abs(mean_tail)
    if max_change < 0.02:
        return True, f"Last {len(tail)} windows show < 2% variation — possible plateau."
    return False, "No plateau detected in recent windows."


def _split_windows(
    window_start: date,
    window_end: date,
    window_count: int,
) -> List[Tuple[date, date, str]]:
    """Split [window_start, window_end] into N consecutive sub-windows."""
    total_days = (window_end - window_start).days + 1
    if total_days <= 0 or window_count <= 0:
        return [(window_start, window_end, f"W1: {window_start}..{window_end}")]
    base = total_days // window_count
    remainder = total_days % window_count
    windows: List[Tuple[date, date, str]] = []
    current = window_start
    for i in range(window_count):
        days = base + (1 if i < remainder else 0)
        end = current + timedelta(days=days - 1)
        if end > window_end:
            end = window_end
        label = f"W{i + 1}: {current.isoformat()}..{end.isoformat()}"
        windows.append((current, end, label))
        current = end + timedelta(days=1)
    return windows


def compute_learning_curve(
    operators: List[Operator],
    observations: List[Observation],
    engine: ScoringEngine,
    metric_ids: List[str],
    window_start: date,
    window_end: date,
    window_count: int = 4,
    operator_id: str = "",
    interventions: Optional[List[dict]] = None,
) -> LearningCurveAnalysis:
    """Compute learning-curve trajectories for operators.

    Args:
        operators: All operators in the cohort.
        observations: All observations for the cohort.
        engine: ScoringEngine to compute per-window metrics.
        metric_ids: Canonical metric IDs to track.
        window_start: Start of the overall measurement window.
        window_end: End of the overall measurement window.
        window_count: Number of sub-windows to divide the period into.
        operator_id: If provided, only analyze this operator. If empty,
            analyze all operators.
        interventions: Optional list of intervention dicts with
            operator_id, start_date, and target_metric for context.

    Returns:
        LearningCurveAnalysis with per-operator improvement rates, curve
        shapes, uncertainty bounds, and plateau detection.
    """
    if not operators:
        return LearningCurveAnalysis(window_count=window_count, summary="No operators.")

    windows = _split_windows(window_start, window_end, window_count)
    actual_window_count = len(windows)
    window_labels = [w[2] for w in windows]

    # Filter operators if a specific one is requested.
    target_ops = [o for o in operators if not operator_id or o.operator_id == operator_id]
    if operator_id and not target_ops:
        return LearningCurveAnalysis(
            window_count=actual_window_count,
            window_labels=window_labels,
            summary=f"Operator {operator_id} not found.",
        )

    # Build intervention context lookup.
    iv_by_op: Dict[str, List[dict]] = {}
    if interventions:
        for iv in interventions:
            oid = iv.get("operator_id", "")
            if oid:
                iv_by_op.setdefault(oid, []).append(iv)

    # Pre-group observations by operator.
    obs_by_op: Dict[str, List[Observation]] = {}
    for obs in observations:
        obs_by_op.setdefault(obs.operator_id, []).append(obs)

    operator_curves: List[OperatorLearningCurve] = []
    all_improvement_rates: List[float] = []
    plateau_count = 0

    for op in target_ops:
        oid = op.operator_id
        op_obs = obs_by_op.get(oid, [])

        metric_curves: List[MetricLearningCurve] = []
        all_rates: List[float] = []
        all_shapes: List[str] = []
        any_plateau = False

        for mid in metric_ids:
            # Score this operator in each sub-window.
            window_values: List[Optional[float]] = []
            for ws, we, _ in windows:
                ms = engine.score_operator(oid, op_obs, ws, we)
                m = next((x for x in ms if x.metric_id == mid), None)
                window_values.append(m.value if m else None)

            valid_vals = [v for v in window_values if v is not None]

            if len(valid_vals) < 2:
                metric_curves.append(MetricLearningCurve(
                    metric_id=mid,
                    window_values=window_values,
                    improvement_rate=0.0,
                    curve_shape="insufficient",
                    uncertainty_lower=0.0,
                    uncertainty_upper=0.0,
                    plateaued=False,
                    plateau_description="insufficient data",
                ))
                all_shapes.append("insufficient")
                continue

            slope = _linear_slope(valid_vals)
            rate = _slope_to_percent_rate(slope, valid_vals)
            lo, hi = _uncertainty_bounds(valid_vals, slope)
            rate_lo = _slope_to_percent_rate(lo, valid_vals)
            rate_hi = _slope_to_percent_rate(hi, valid_vals)
            shape = _curve_shape(valid_vals)
            plateaued, plateau_desc = _detect_plateau(window_values)

            all_rates.append(rate)
            all_shapes.append(shape)
            if plateaued:
                any_plateau = True

            metric_curves.append(MetricLearningCurve(
                metric_id=mid,
                window_values=window_values,
                improvement_rate=rate,
                curve_shape=shape,
                uncertainty_lower=rate_lo,
                uncertainty_upper=rate_hi,
                plateaued=plateaued,
                plateau_description=plateau_desc,
            ))

        # Overall improvement rate: average across metrics.
        overall_rate = sum(all_rates) / len(all_rates) if all_rates else 0.0
        all_improvement_rates.append(overall_rate)

        # Overall curve shape: majority vote.
        if all_shapes:
            shape_counts: Dict[str, int] = {}
            for s in all_shapes:
                shape_counts[s] = shape_counts.get(s, 0) + 1
            overall_shape = max(shape_counts, key=shape_counts.get)
        else:
            overall_shape = "insufficient"

        if any_plateau:
            plateau_count += 1

        # Intervention context.
        iv_context: List[str] = []
        for iv in iv_by_op.get(oid, []):
            start = iv.get("start_date", "")
            target = iv.get("target_metric", "")
            reason = iv.get("reason_pattern", "")
            iv_context.append(
                f"Intervention started {start} targeting {target} "
                f"(pattern: {reason}). Temporal co-occurrence noted — "
                f"ASSOCIATION, not causation."
            )

        operator_curves.append(OperatorLearningCurve(
            operator_id=oid,
            pseudonym=op.pseudonym,
            team=op.team,
            window_labels=window_labels,
            metric_curves=metric_curves,
            overall_improvement_rate=overall_rate,
            overall_curve_shape=overall_shape,
            overall_plateaued=any_plateau,
            intervention_context=iv_context,
            note=(
                "Learning curve is a developmental observation. Improvement "
                "rate and curve shape describe metric trajectory, not operator "
                "worth. Intervention co-occurrence is ASSOCIATION, not causation."
            ),
        ))

    # Sort by operator_id for deterministic output.
    operator_curves.sort(key=lambda c: c.operator_id)

    # Cohort-level improvement rate.
    cohort_rate = sum(all_improvement_rates) / len(all_improvement_rates) if all_improvement_rates else 0.0

    # Summary.
    improving = sum(1 for r in all_improvement_rates if r > 2.0)
    declining = sum(1 for r in all_improvement_rates if r < -2.0)
    summary_parts = [
        f"{len(operator_curves)} operator(s) analyzed across {actual_window_count} window(s).",
        f"Cohort average improvement rate: {cohort_rate:.2f}% per window.",
        f"{improving} operator(s) improving, {declining} declining.",
        f"{plateau_count} operator(s) show plateau signals.",
    ]

    return LearningCurveAnalysis(
        window_count=actual_window_count,
        window_labels=window_labels,
        operator_curves=operator_curves,
        cohort_improvement_rate=cohort_rate,
        cohort_plateau_count=plateau_count,
        summary=" ".join(summary_parts),
    )
