"""ReferencePopulation — a versioned field used for percentiles/comparisons.

Per `14_PRODUCT_OBJECT_MODEL.md`: versioned field used for percentiles/comparisons.
Per `02` §11: reference data should be loaded from a separate versioned file
(reference_field_vYYYYMMDD.json), not buried inside the generator.

Every percentile or comparison MUST identify the reference population version
(P0 acceptance test: "reference percentile always identifies reference version").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Optional


@dataclass(frozen=True, slots=True)
class ReferencePopulation:
    reference_id: str
    version: str  # e.g. "public_field_2026-08-17"
    date: date
    description: str
    # metric_id → distribution descriptor (percentiles, bands, or raw stats)
    # e.g. {"leverage": {"p10": 2.1, "p50": 12.0, "p90": 35.0}}
    distributions: Dict[str, dict] = field(default_factory=dict)
    synthetic: bool = False

    def percentile(self, metric_id: str, value: float) -> Optional[float]:
        """Approximate the percentile of `value` against the reference distribution.

        Uses linear interpolation between known percentile points if available.
        Returns None if the metric has no distribution in this reference population.
        """
        dist = self.distributions.get(metric_id)
        if not dist:
            return None
        # Expect keys like p0, p10, p25, p50, p75, p90, p100
        points = sorted(
            (int(k[1:]), v) for k, v in dist.items() if k.startswith("p") and k[1:].isdigit()
        )
        if not points:
            return None
        if value <= points[0][1]:
            return float(points[0][0])
        if value >= points[-1][1]:
            return float(points[-1][0])
        for i in range(1, len(points)):
            p_lo, v_lo = points[i - 1]
            p_hi, v_hi = points[i]
            if v_lo <= value <= v_hi:
                if v_hi == v_lo:
                    return float(p_lo)
                frac = (value - v_lo) / (v_hi - v_lo)
                return float(p_lo + frac * (p_hi - p_lo))
        return None

    def to_dict(self) -> dict:
        return {
            "reference_id": self.reference_id,
            "version": self.version,
            "date": self.date.isoformat(),
            "description": self.description,
            "distributions": dict(self.distributions),
            "synthetic": self.synthetic,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ReferencePopulation":
        dt = d["date"]
        if isinstance(dt, str):
            dt = date.fromisoformat(dt)
        return cls(
            reference_id=d["reference_id"],
            version=d["version"],
            date=dt,
            description=d["description"],
            distributions=dict(d.get("distributions", {})),
            synthetic=d.get("synthetic", False),
        )
