"""Percentile computation against a reference population.

Every percentile identifies the reference population version (P0 acceptance:
"reference percentile always identifies reference version").
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.measurement import Measurement
from domain.reference_population import ReferencePopulation


def compute_percentiles(
    measurements: List[Measurement],
    reference: ReferencePopulation,
) -> Dict[str, Dict[str, Measurement]]:
    """Compute percentile Measurements for each operator × metric.

    Returns a nested dict: operator_id → metric_id → percentile Measurement.
    The percentile Measurement carries the reference version in its `source`
    field so downstream consumers always know which reference was used.
    """
    result: Dict[str, Dict[str, Measurement]] = {}
    for m in measurements:
        if m.value is None:
            continue
        pct = reference.percentile(m.metric_id, m.value)
        if pct is None:
            continue
        pct_measurement = Measurement(
            metric_id=f"{m.metric_id}_percentile",
            metric_version=m.metric_version,
            operator_id=m.operator_id,
            value=round(pct, 1),
            unit="percentile",
            window_start=m.window_start,
            window_end=m.window_end,
            source=f"reference:{reference.version}",
            status=m.status,
            eligibility=m.eligibility,
            synthetic=m.synthetic,
        )
        result.setdefault(m.operator_id, {})[pct_measurement.metric_id] = pct_measurement
    return result
