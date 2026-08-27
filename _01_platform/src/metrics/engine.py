"""ScoringEngine — the single canonical scoring path.

Reads `Observation` objects, aggregates token counts over a window, computes
canonical metrics via `metrics.py`, and emits `Measurement` objects conforming
to the `03` measurement object contract.

This is the ONE place metrics are computed. CLI/TUI/MCP all call this engine;
none implement formulas independently (per `21` P0 acceptance: "same fixture
produces same metric values in every interface").

Domain guards (P0 acceptance: "I=0 domain restrictions handled explicitly"):
    - Leverage: I > 0
    - Yield: I > 0
    - Token SNR: I + O > 0
    - Log Leverage: I > 0 and R > 0 (i.e. L > 0)
    - Construction: R > 0

When a guard fails, the Measurement is emitted with value=None and
eligibility recording the failed condition (e.g. "I=0").
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional

# Ensure src/ is on the path so `domain` is importable.
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from metrics.formulas import leverage, yield_metric, token_snr, log_leverage, construction as _construction
from domain.measurement import Measurement, MetricStatus
from domain.observation import Observation
from metrics.registry import MetricRegistry, load_registry


# Map metric_id → (aggregated scorer, unit, eligibility expression, status).
# Each scorer takes (I, O, R, W) aggregates and returns float|None.
_METRIC_SPECS = {
    "leverage":     (lambda I, O, R, W: leverage(I, R),       "ratio",      "I>0",      MetricStatus.CANONICAL),
    "yield":        (lambda I, O, R, W: yield_metric(I, O, R),"ratio",      "I>0",      MetricStatus.CANONICAL),
    "token_snr":    (lambda I, O, R, W: token_snr(I, O),      "share",      "I+O>0",    MetricStatus.CANONICAL_WITH_INTERPRETATION_LIMIT),
    "log_leverage": (lambda I, O, R, W: log_leverage(I, R),   "log10_ratio","I>0,R>0",  MetricStatus.CANONICAL),
    "construction": (lambda I, O, R, W: _construction(R, W),  "ratio",      "R>0",      MetricStatus.CANONICAL_WITH_INTERPRETATION_LIMIT),
}

METRIC_VERSION = "1.0"
SOURCE = "canonical_token_telemetry"


class ScoringEngine:
    """Computes canonical Measurements from Observations.

    Parameters:
        registry: a MetricRegistry (loaded from schemas/metric_registry.json).
                  If None, loads the default registry.
    """

    def __init__(self, registry: Optional[MetricRegistry] = None) -> None:
        self.registry = registry or load_registry()

    def score_operator(
        self,
        operator_id: str,
        observations: Iterable[Observation],
        window_start: date,
        window_end: date,
    ) -> List[Measurement]:
        """Compute all canonical metrics for one operator over a window.

        Returns a list of Measurement objects (one per canonical metric).
        Observations outside the window are ignored.
        """
        obs_in_window = [
            o for o in observations
            if o.operator_id == operator_id
            and _date_in_window(o.timestamp.date(), window_start, window_end)
        ]
        synthetic = any(o.synthetic for o in obs_in_window)

        # Aggregate token counts over the window.
        I = sum(o.I for o in obs_in_window)
        O = sum(o.O for o in obs_in_window)
        R = sum(o.R for o in obs_in_window)
        W = sum(o.W for o in obs_in_window)

        measurements: List[Measurement] = []
        for metric_id, (scorer, unit, eligibility, status) in _METRIC_SPECS.items():
            # Verify the metric is in the registry (raises KeyError if unknown).
            self.registry.get(metric_id)

            value = scorer(I, O, R, W)

            # Determine the actual eligibility outcome.
            if value is None:
                actual_eligibility = f"FAILED: {eligibility}"
            else:
                actual_eligibility = eligibility

            measurements.append(Measurement(
                metric_id=metric_id,
                metric_version=METRIC_VERSION,
                operator_id=operator_id,
                value=value,
                unit=unit,
                window_start=window_start,
                window_end=window_end,
                source=SOURCE,
                status=status,
                eligibility=actual_eligibility,
                synthetic=synthetic,
            ))
        return measurements

    def score_cohort(
        self,
        operator_ids: Iterable[str],
        observations: Iterable[Observation],
        window_start: date,
        window_end: date,
    ) -> Dict[str, List[Measurement]]:
        """Score all operators in a cohort. Returns operator_id → measurements."""
        obs_list = list(observations)
        return {
            oid: self.score_operator(oid, obs_list, window_start, window_end)
            for oid in operator_ids
        }


def _date_in_window(d: date, start: date, end: date) -> bool:
    return start <= d <= end
