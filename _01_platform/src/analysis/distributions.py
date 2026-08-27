"""Cohort distributions — medians, quartiles, outliers per metric.

P0-D analysis: computes distribution statistics for each canonical metric
across the cohort. Used by the Workforce Operating Map (deliverable #2).
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
class MetricDistribution:
    """Distribution statistics for a single metric across a cohort."""
    metric_id: str
    count: int
    min_val: Optional[float]
    p10: Optional[float]
    p25: Optional[float]
    median: Optional[float]
    p75: Optional[float]
    p90: Optional[float]
    max_val: Optional[float]
    mean: Optional[float]
    std: Optional[float]
    outliers: List[str]  # operator_ids with values outside [p10, p90] by >2σ

    def to_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "count": self.count,
            "min": self.min_val,
            "p10": self.p10,
            "p25": self.p25,
            "median": self.median,
            "p75": self.p75,
            "p90": self.p90,
            "max": self.max_val,
            "mean": round(self.mean, 4) if self.mean is not None else None,
            "std": round(self.std, 4) if self.std is not None else None,
            "outliers": self.outliers,
        }


def compute_cohort_distributions(
    measurements: List[Measurement],
) -> Dict[str, MetricDistribution]:
    """Compute distribution statistics for each metric across the cohort.

    Expects a flat list of Measurement objects (one per operator × metric).
    Returns a dict: metric_id → MetricDistribution.
    """
    import math

    # Group by metric_id
    by_metric: Dict[str, List[tuple]] = {}  # metric_id → [(operator_id, value)]
    for m in measurements:
        if m.value is None:
            continue
        by_metric.setdefault(m.metric_id, []).append((m.operator_id, m.value))

    distributions: Dict[str, MetricDistribution] = {}
    for metric_id, pairs in by_metric.items():
        values = sorted(v for _, v in pairs)
        n = len(values)
        if n == 0:
            distributions[metric_id] = MetricDistribution(
                metric_id=metric_id, count=0,
                min_val=None, p10=None, p25=None, median=None,
                p75=None, p90=None, max_val=None, mean=None, std=None,
                outliers=[],
            )
            continue

        def percentile(p: float) -> float:
            idx = min(int(n * p / 100), n - 1)
            return round(values[idx], 4)

        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n
        std = math.sqrt(variance)

        # Outliers: values more than 2σ from the mean
        outliers = [oid for oid, v in pairs if abs(v - mean) > 2 * std]

        distributions[metric_id] = MetricDistribution(
            metric_id=metric_id,
            count=n,
            min_val=round(values[0], 4),
            p10=percentile(10),
            p25=percentile(25),
            median=round(values[n // 2] if n % 2 == 1 else (values[n // 2 - 1] + values[n // 2]) / 2, 4),
            p75=percentile(75),
            p90=percentile(90),
            max_val=round(values[-1], 4),
            mean=round(mean, 4),
            std=round(std, 4),
            outliers=outliers,
        )

    return distributions
