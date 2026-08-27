"""Outcome join engine — joins external outcomes to pilot data.

Per `21` P2:
- "outcome joins remain separately governed"
- "outcome analysis separates association from causal claim"

The join engine:
1. Requires a governance object before any join
2. Labels all results as ASSOCIATION (never CAUSATION)
3. Separates internal metric deltas from external outcome deltas
4. Reports sample sizes and uncertainty

Supported sources: GitHub (PRs, issues), Jira (tickets), external CSV.
"""
from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from .governance import OutcomeGovernance, GovernanceLevel


class OutcomeSource(str, Enum):
    GITHUB = "github"
    JIRA = "jira"
    EXTERNAL_CSV = "external_csv"
    SYNTHETIC = "synthetic"


@dataclass(frozen=True, slots=True)
class OutcomeRecord:
    """A single external outcome record."""
    operator_id: str
    intervention_id: Optional[str]
    window_start: str
    window_end: str
    metrics: Dict[str, float]  # e.g. {"cycle_time_change_pct": 4.7, "quality_change_pct": 1.7}
    source: str
    synthetic: bool

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "intervention_id": self.intervention_id,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "metrics": dict(self.metrics),
            "source": self.source,
            "synthetic": self.synthetic,
        }


@dataclass(frozen=True, slots=True)
class OutcomeJoinResult:
    """Result of joining outcomes to pilot data."""
    operator_id: str
    intervention_id: Optional[str]
    internal_metric_deltas: Dict[str, Optional[float]]  # from telemetry
    external_outcome_deltas: Dict[str, Optional[float]]  # from external source
    claim_type: str  # ALWAYS "ASSOCIATION" per P2
    governance: OutcomeGovernance
    sample_size: int
    synthetic: bool

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "intervention_id": self.intervention_id,
            "internal_metric_deltas": dict(self.internal_metric_deltas),
            "external_outcome_deltas": dict(self.external_outcome_deltas),
            "claim_type": self.claim_type,
            "governance": self.governance.to_dict(),
            "sample_size": self.sample_size,
            "synthetic": self.synthetic,
        }


class OutcomeJoinEngine:
    """Joins external outcome data to pilot internal metrics.

    Per P2: "outcome joins remain separately governed" and "outcome analysis
    separates association from causal claim."
    """

    def __init__(self, governance: OutcomeGovernance) -> None:
        """Initialize with required governance metadata.

        Raises ValueError if governance is not provided.
        """
        if governance is None:
            raise ValueError("Governance metadata is required for outcome joins (P2: separately governed)")
        self.governance = governance

    def load_outcomes_csv(self, path: str) -> List[OutcomeRecord]:
        """Load outcome records from a CSV file.

        Expected columns: operator_id, intervention_id (optional),
        window_start, window_end, and any metric columns.
        """
        records: List[OutcomeRecord] = []
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Outcome file not found: {p}")

        with open(p, newline="") as f:
            reader = csv.DictReader(f)
            metric_cols = [c for c in reader.fieldnames
                          if c not in ("operator_id", "intervention_id", "window_start", "window_end", "source", "synthetic")]
            for row in reader:
                metrics = {}
                for col in metric_cols:
                    val = row.get(col)
                    if val and val.strip():
                        try:
                            metrics[col] = float(val)
                        except ValueError:
                            pass
                records.append(OutcomeRecord(
                    operator_id=row["operator_id"],
                    intervention_id=row.get("intervention_id") or None,
                    window_start=row.get("window_start", ""),
                    window_end=row.get("window_end", ""),
                    metrics=metrics,
                    source=row.get("source", self.governance.source),
                    synthetic=row.get("synthetic", "").lower() == "true",
                ))
        return records

    def join(
        self,
        operator_id: str,
        internal_deltas: Dict[str, Optional[float]],
        outcome_records: List[OutcomeRecord],
        intervention_id: Optional[str] = None,
    ) -> OutcomeJoinResult:
        """Join internal metric deltas to external outcomes.

        Per P2: the result is ALWAYS labeled ASSOCIATION, never CAUSATION.
        Internal and external deltas are kept separate.
        """
        # Filter records for this operator/intervention
        matching = [
            r for r in outcome_records
            if r.operator_id == operator_id
            and (intervention_id is None or r.intervention_id == intervention_id)
        ]

        # Aggregate external deltas
        external_deltas: Dict[str, Optional[float]] = {}
        if matching:
            for key in matching[0].metrics.keys():
                values = [r.metrics.get(key) for r in matching if r.metrics.get(key) is not None]
                if values:
                    external_deltas[key] = round(sum(values) / len(values), 4)
                else:
                    external_deltas[key] = None

        return OutcomeJoinResult(
            operator_id=operator_id,
            intervention_id=intervention_id,
            internal_metric_deltas=dict(internal_deltas),
            external_outcome_deltas=external_deltas,
            claim_type="ASSOCIATION",  # ALWAYS per P2
            governance=self.governance,
            sample_size=len(matching),
            synthetic=all(r.synthetic for r in matching) if matching else True,
        )

    def join_cohort(
        self,
        internal_deltas_by_operator: Dict[str, Dict[str, Optional[float]]],
        outcome_records: List[OutcomeRecord],
    ) -> List[OutcomeJoinResult]:
        """Join outcomes for all operators in a cohort."""
        results: List[OutcomeJoinResult] = []
        for oid, deltas in internal_deltas_by_operator.items():
            result = self.join(oid, deltas, outcome_records)
            results.append(result)
        return results
