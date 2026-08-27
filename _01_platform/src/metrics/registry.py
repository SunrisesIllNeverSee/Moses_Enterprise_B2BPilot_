"""Metric registry loader — validates and serves metric metadata.

Loads `schemas/metric_registry.json` and provides lookups by metric_id.
The registry is authoritative (`21` non-negotiable: "`03_CANONICAL_METRIC_REGISTRY.md`
and `schemas/metric_registry.json` are authoritative.").

Unknown metric versions fail loudly (P0 acceptance test).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True, slots=True)
class MetricEntry:
    metric_id: str
    name: str
    status: str
    formula: Optional[str]
    requires: List[str] = field(default_factory=list)
    unit: Optional[str] = None


@dataclass(frozen=True, slots=True)
class MetricRegistry:
    registry_version: str
    date: str
    metrics: Dict[str, MetricEntry] = field(default_factory=dict)

    def get(self, metric_id: str) -> MetricEntry:
        """Look up a metric by ID. Raises KeyError if unknown."""
        try:
            return self.metrics[metric_id]
        except KeyError:
            raise KeyError(
                f"Unknown metric_id '{metric_id}' — not in registry version "
                f"{self.registry_version}. Known: {sorted(self.metrics)}"
            )

    @property
    def metric_ids(self) -> List[str]:
        return sorted(self.metrics.keys())

    def canonical_metric_ids(self) -> List[str]:
        """Metric IDs that are CANONICAL or CANONICAL_WITH_INTERPRETATION_LIMIT."""
        return sorted(
            mid for mid, m in self.metrics.items()
            if m.status in ("CANONICAL", "CANONICAL_WITH_INTERPRETATION_LIMIT")
        )


def load_registry(path: Optional[str] = None) -> MetricRegistry:
    """Load the metric registry from a JSON file.

    If no path is given, looks for schemas/metric_registry.json relative to
    the build package root.
    """
    if path is None:
        # src/metrics/registry.py → src/ → build_package_root/schemas/
        root = Path(__file__).resolve().parents[2]
        path = str(root / "schemas" / "metric_registry.json")
    with open(path) as f:
        data = json.load(f)
    metrics = {}
    for m in data.get("metrics", []):
        mid = m["metric_id"]
        metrics[mid] = MetricEntry(
            metric_id=mid,
            name=m["name"],
            status=m["status"],
            formula=m.get("formula"),
            requires=list(m.get("requires", [])),
            unit=m.get("unit"),
        )
    return MetricRegistry(
        registry_version=data["registry_version"],
        date=data["date"],
        metrics=metrics,
    )
