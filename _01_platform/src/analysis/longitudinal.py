"""EVAL-004 — Longitudinal Movement.

Tracks metric changes over time windows for operators. The core question:
how do an operator's canonical metrics move across repeated measurement
windows? Are they improving, declining, or stable?

Per spec 18:
    Input: repeated windows (time series of metrics).
    Output: metric change, stability, band movement.

Per Build B §6.4 (Longitudinal Movement Eval):
    This eval divides the observation period into N consecutive windows,
    scores each operator in each window, and then computes:

    - Metric deltas: change between consecutive windows (percent change).
    - Trend direction: improving / declining / stable per metric.
    - Band movement: whether the operator's percentile band (e.g. p25–p50)
      shifts across windows.
    - Stability score: how consistent the operator's metrics are across
      windows (inverse of coefficient of variation).

All metrics are content-free (token counts only). Outcome claims are
ASSOCIATION, never CAUSATION. Trend labels are developmental observations,
not personnel judgments.
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

from domain.measurement import Measurement
from domain.observation import Observation
from domain.operator import Operator
from metrics.engine import ScoringEngine


@dataclass(frozen=True, slots=True)
class MetricTrajectory:
    """One metric's movement across windows for one operator."""
    metric_id: str
    window_values: List[Optional[float]]  # value per window (None if ineligible)
    deltas: List[Optional[float]]  # percent change between consecutive windows
    trend: str  # "improving" | "declining" | "stable" | "insufficient"
    stability_score: float  # 0–1, higher = more stable
    band_movement: str  # description of percentile band shifts

    def to_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "window_values": [round(v, 4) if v is not None else None for v in self.window_values],
            "deltas": [round(d, 4) if d is not None else None for d in self.deltas],
            "trend": self.trend,
            "stability_score": round(self.stability_score, 4),
            "band_movement": self.band_movement,
        }


@dataclass(frozen=True, slots=True)
class OperatorLongitudinal:
    """One operator's longitudinal movement across windows."""
    operator_id: str
    pseudonym: str
    team: Optional[str]
    window_labels: List[str]  # e.g. ["W1: 2026-07-01..2026-07-10", ...]
    metric_trajectories: List[MetricTrajectory] = field(default_factory=list)
    overall_trend: str = ""  # aggregate across metrics
    overall_stability: float = 0.0

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "pseudonym": self.pseudonym,
            "team": self.team,
            "window_labels": list(self.window_labels),
            "metric_trajectories": [t.to_dict() for t in self.metric_trajectories],
            "overall_trend": self.overall_trend,
            "overall_stability": round(self.overall_stability, 4),
        }


@dataclass(frozen=True, slots=True)
class LongitudinalMovement:
    """The complete longitudinal-movement analysis result."""
    window_count: int
    window_labels: List[str] = field(default_factory=list)
    operator_trajectories: List[OperatorLongitudinal] = field(default_factory=list)
    cohort_trend_summary: Dict[str, int] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "window_count": self.window_count,
            "window_labels": list(self.window_labels),
            "operator_trajectories": [t.to_dict() for t in self.operator_trajectories],
            "cohort_trend_summary": dict(self.cohort_trend_summary),
            "summary": self.summary,
        }


def _percent_delta(old: float, new: float) -> Optional[float]:
    """Percent change from old to new. Returns None if old is 0 or None."""
    if old is None or new is None or old == 0:
        return None
    return ((new - old) / abs(old)) * 100.0


def _coefficient_of_variation(values: List[float]) -> float:
    """CV = stdev / mean. Returns 0.0 for empty or zero-mean."""
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5 / abs(mean)


def _stability_score(values: List[float]) -> float:
    """Convert CV to a 0–1 stability score (1 = perfectly stable).

    stability = 1 / (1 + CV). When CV=0, stability=1. When CV is large,
    stability approaches 0.
    """
    cv = _coefficient_of_variation(values)
    return 1.0 / (1.0 + cv)


def _trend_direction(deltas: List[Optional[float]], metric_id: str) -> str:
    """Determine trend from a list of percent deltas.

    For metrics where higher is better (leverage, yield, token_snr,
    log_leverage, construction), positive deltas = improving.
    """
    valid = [d for d in deltas if d is not None]
    if len(valid) < 2:
        return "insufficient"
    mean_delta = sum(valid) / len(valid)
    # Threshold: 5% average change per window to count as a trend.
    if mean_delta > 5.0:
        return "improving"
    if mean_delta < -5.0:
        return "declining"
    return "stable"


def _band_movement(values: List[Optional[float]]) -> str:
    """Describe band movement across windows.

    Uses simple quartile bands based on the operator's own value range.
    """
    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return "insufficient data"
    lo = min(valid)
    hi = max(valid)
    if hi == lo:
        return "flat — no band movement"
    span = hi - lo
    first = valid[0]
    last = valid[-1]
    first_band = "low" if first < lo + span / 3 else ("mid" if first < lo + 2 * span / 3 else "high")
    last_band = "low" if last < lo + span / 3 else ("mid" if last < lo + 2 * span / 3 else "high")
    if first_band == last_band:
        return f"stable in {first_band} band"
    return f"moved from {first_band} to {last_band} band"


def _split_windows(
    window_start: date,
    window_end: date,
    window_count: int,
) -> List[Tuple[date, date, str]]:
    """Split [window_start, window_end] into N consecutive sub-windows.

    Returns a list of (start, end, label) tuples.
    """
    total_days = (window_end - window_start).days + 1
    if total_days <= 0 or window_count <= 0:
        return [(window_start, window_end, f"W1: {window_start}..{window_end}")]
    # Distribute days as evenly as possible.
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


def compute_longitudinal_movement(
    operators: List[Operator],
    observations: List[Observation],
    engine: ScoringEngine,
    metric_ids: List[str],
    window_start: date,
    window_end: date,
    window_count: int = 3,
    operator_id: str = "",
) -> LongitudinalMovement:
    """Compute longitudinal movement across time windows.

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

    Returns:
        LongitudinalMovement with per-operator trajectories, trend
        directions, band movements, and stability scores.
    """
    if not operators:
        return LongitudinalMovement(window_count=window_count, summary="No operators.")

    windows = _split_windows(window_start, window_end, window_count)
    actual_window_count = len(windows)
    window_labels = [w[2] for w in windows]

    # Filter operators if a specific one is requested.
    target_ops = [o for o in operators if not operator_id or o.operator_id == operator_id]
    if operator_id and not target_ops:
        return LongitudinalMovement(
            window_count=actual_window_count,
            window_labels=window_labels,
            summary=f"Operator {operator_id} not found.",
        )

    op_map = {o.operator_id: o for o in operators}

    # Pre-group observations by operator for efficiency.
    obs_by_op: Dict[str, List[Observation]] = {}
    for obs in observations:
        obs_by_op.setdefault(obs.operator_id, []).append(obs)

    operator_trajectories: List[OperatorLongitudinal] = []
    trend_counts: Dict[str, int] = {}

    for op in target_ops:
        oid = op.operator_id
        op_obs = obs_by_op.get(oid, [])

        metric_trajectories: List[MetricTrajectory] = []
        all_stabilities: List[float] = []
        all_trends: List[str] = []

        for mid in metric_ids:
            # Score this operator in each sub-window.
            window_values: List[Optional[float]] = []
            for ws, we, _ in windows:
                ms = engine.score_operator(oid, op_obs, ws, we)
                m = next((x for x in ms if x.metric_id == mid), None)
                window_values.append(m.value if m else None)

            # Compute deltas between consecutive windows.
            deltas: List[Optional[float]] = []
            for i in range(1, len(window_values)):
                deltas.append(_percent_delta(window_values[i - 1], window_values[i]))

            # Trend direction.
            trend = _trend_direction(deltas, mid)
            all_trends.append(trend)
            trend_counts[trend] = trend_counts.get(trend, 0) + 1

            # Stability score (only from valid values).
            valid_vals = [v for v in window_values if v is not None]
            stability = _stability_score(valid_vals)
            all_stabilities.append(stability)

            # Band movement.
            band = _band_movement(window_values)

            metric_trajectories.append(MetricTrajectory(
                metric_id=mid,
                window_values=window_values,
                deltas=deltas,
                trend=trend,
                stability_score=stability,
                band_movement=band,
            ))

        # Overall trend: majority vote across metrics.
        if all_trends:
            improving = all_trends.count("improving")
            declining = all_trends.count("declining")
            if improving > declining and improving > all_trends.count("stable"):
                overall_trend = "improving"
            elif declining > improving and declining > all_trends.count("stable"):
                overall_trend = "declining"
            else:
                overall_trend = "stable"
        else:
            overall_trend = "insufficient"

        overall_stability = sum(all_stabilities) / len(all_stabilities) if all_stabilities else 0.0

        operator_trajectories.append(OperatorLongitudinal(
            operator_id=oid,
            pseudonym=op.pseudonym,
            team=op.team,
            window_labels=window_labels,
            metric_trajectories=metric_trajectories,
            overall_trend=overall_trend,
            overall_stability=overall_stability,
        ))

    # Sort by operator_id for deterministic output.
    operator_trajectories.sort(key=lambda t: t.operator_id)

    # Summary.
    summary_parts = [
        f"{len(operator_trajectories)} operator(s) analyzed across {actual_window_count} window(s).",
    ]
    for trend, count in sorted(trend_counts.items()):
        summary_parts.append(f"{count} metric trajectory(ies) {trend}.")

    return LongitudinalMovement(
        window_count=actual_window_count,
        window_labels=window_labels,
        operator_trajectories=operator_trajectories,
        cohort_trend_summary=trend_counts,
        summary=" ".join(summary_parts),
    )
