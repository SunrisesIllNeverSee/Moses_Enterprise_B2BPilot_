"""Cross-analysis — wires intervention verification to external outcome joins.

Per `16` P2 remaining: "intervention × outcome analysis — not built (join engine
exists, cross-analysis not wired)."

This module connects:
    src/analysis/verifier.py  — per-intervention internal metric deltas
    src/outcomes/join_engine.py — external outcome deltas

Produces InterventionOutcomeResult objects that show both deltas side-by-side,
labeled ASSOCIATION (never CAUSATION). Governance metadata is required and
carried through every result.
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from analysis.verifier import PrePostVerifier, VerificationResult, MetricDelta
from domain.intervention import Intervention
from outcomes.governance import OutcomeGovernance
from outcomes.join_engine import OutcomeJoinEngine, OutcomeRecord, OutcomeJoinResult

_logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class InterventionOutcomeResult:
    """Combined result: internal metric deltas + external outcome deltas
    for a single intervention.

    Per P2: claim_type is ALWAYS "ASSOCIATION". Internal and external deltas
    are kept in separate fields. Governance metadata is carried through.
    """
    intervention_id: str
    operator_id: str
    target_metric: str
    internal_metric_deltas: Dict[str, Optional[float]]  # metric_id → percent_delta
    external_outcome_deltas: Dict[str, Optional[float]]  # outcome_metric → value
    claim_type: str  # ALWAYS "ASSOCIATION"
    governance: OutcomeGovernance
    sample_size: int
    synthetic: bool

    def to_dict(self) -> dict:
        return {
            "intervention_id": self.intervention_id,
            "operator_id": self.operator_id,
            "target_metric": self.target_metric,
            "internal_metric_deltas": dict(self.internal_metric_deltas),
            "external_outcome_deltas": dict(self.external_outcome_deltas),
            "claim_type": self.claim_type,
            "governance": self.governance.to_dict(),
            "sample_size": self.sample_size,
            "synthetic": self.synthetic,
        }


class InterventionOutcomeAnalyzer:
    """Cross-analyzes intervention results against external outcomes.

    Wires the pre/post verifier (internal metric deltas) to the outcome join
    engine (external outcome deltas). Every result is labeled ASSOCIATION.
    """

    def __init__(
        self,
        verifier: PrePostVerifier,
        join_engine: OutcomeJoinEngine,
    ) -> None:
        self.verifier = verifier
        self.join_engine = join_engine

    def analyze(
        self,
        interventions: List[Intervention],
        observations_by_operator: Dict[str, list],
        outcome_records: List[OutcomeRecord],
        baseline_start,
        baseline_end,
    ) -> List[InterventionOutcomeResult]:
        """Cross-analyze all interventions against external outcomes.

        Args:
            interventions: list of interventions to analyze
            observations_by_operator: operator_id → observations list
            outcome_records: external outcome records from the join engine
            baseline_start/end: baseline evaluation window

        Returns:
            List of InterventionOutcomeResult, one per intervention that has
            both internal verification data and matching outcome records.
        """
        results: List[InterventionOutcomeResult] = []

        for iv in interventions:
            obs = observations_by_operator.get(iv.operator_id, [])
            if not obs:
                continue

            # Compute internal metric deltas via the verifier
            try:
                vr: VerificationResult = self.verifier.verify(
                    iv, obs, baseline_start, baseline_end
                )
            except Exception as e:
                _logger.warning(
                    "cross_analysis: skipped verification for %s (operator %s): %s",
                    iv.intervention_id, iv.operator_id, e,
                )
                continue

            internal_deltas: Dict[str, Optional[float]] = {
                d.metric_id: d.percent_delta for d in vr.deltas
            }

            # Join to external outcomes via the join engine
            join_result: OutcomeJoinResult = self.join_engine.join(
                operator_id=iv.operator_id,
                internal_deltas=internal_deltas,
                outcome_records=outcome_records,
                intervention_id=iv.intervention_id,
            )

            results.append(InterventionOutcomeResult(
                intervention_id=iv.intervention_id,
                operator_id=iv.operator_id,
                target_metric=iv.target_metric,
                internal_metric_deltas=internal_deltas,
                external_outcome_deltas=join_result.external_outcome_deltas,
                claim_type="ASSOCIATION",
                governance=self.join_engine.governance,
                sample_size=join_result.sample_size,
                synthetic=iv.synthetic,
            ))

        return results
