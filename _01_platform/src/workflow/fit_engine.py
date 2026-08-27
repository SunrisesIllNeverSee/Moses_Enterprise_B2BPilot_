"""Workflow fit engine — computes stage fit with sample-size gates.

Per `21` P2 acceptance:
- "workflow fit exposes observation count and uncertainty"
- "no stage-fit claim without minimum sample rule"

The engine computes a provisional fit score for each operator × stage,
but BLOCKS any fit claim that doesn't meet the minimum sample size.
Results always carry observation_count and uncertainty.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.workflow import Workflow, WorkflowObservation


# Minimum samples required to make a stage-fit claim (per P2 acceptance)
MIN_SAMPLES_FOR_FIT_CLAIM = 5
# Below this, the result is marked "insufficient_sample"
MIN_SAMPLES_FOR_PROVISIONAL = 1


@dataclass(frozen=True, slots=True)
class StageFitResult:
    """Fit result for a single operator × stage."""
    operator_id: str
    workflow_id: str
    stage_id: str
    provisional_fit: Optional[float]      # 0.0–1.0 or None if insufficient
    observation_count: int
    uncertainty: float                     # standard error of the fit estimate
    claim_status: str                      # "fit_claim" | "provisional" | "insufficient_sample"
    can_claim_fit: bool                    # False if below min sample
    synthetic: bool

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "workflow_id": self.workflow_id,
            "stage_id": self.stage_id,
            "provisional_fit": self.provisional_fit,
            "observation_count": self.observation_count,
            "uncertainty": round(self.uncertainty, 4),
            "claim_status": self.claim_status,
            "can_claim_fit": self.can_claim_fit,
            "synthetic": self.synthetic,
        }


@dataclass(frozen=True, slots=True)
class WorkflowFitReport:
    """Full workflow fit report for a cohort."""
    workflow_id: str
    stages: List[str]
    operator_results: Dict[str, List[StageFitResult]]
    min_sample_rule: int
    summary: Dict[str, int]  # count by claim_status

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "stages": list(self.stages),
            "min_sample_rule": self.min_sample_rule,
            "operators": {
                oid: [r.to_dict() for r in results]
                for oid, results in self.operator_results.items()
            },
            "summary": dict(self.summary),
        }


class WorkflowFitEngine:
    """Computes workflow stage fit with sample-size gates.

    Per P2: "no stage-fit claim without minimum sample rule."
    """

    def __init__(self, min_samples: int = MIN_SAMPLES_FOR_FIT_CLAIM) -> None:
        self.min_samples = min_samples

    def compute_fit(
        self,
        operator_id: str,
        workflow: Workflow,
        observations: List[WorkflowObservation],
    ) -> List[StageFitResult]:
        """Compute stage fit for a single operator across all stages.

        Returns one StageFitResult per stage in the workflow.
        """
        results: List[StageFitResult] = []
        for stage in workflow.stages:
            stage_obs = [o for o in observations
                         if o.operator_id == operator_id and o.stage_id == stage.stage_id]
            count = len(stage_obs)

            if count == 0:
                results.append(StageFitResult(
                    operator_id=operator_id,
                    workflow_id=workflow.workflow_id,
                    stage_id=stage.stage_id,
                    provisional_fit=None,
                    observation_count=0,
                    uncertainty=1.0,  # max uncertainty
                    claim_status="insufficient_sample",
                    can_claim_fit=False,
                    synthetic=True,
                ))
                continue

            # Compute mean provisional fit
            fit_values = [o.provisional_fit or 0 for o in stage_obs]
            mean_fit = sum(fit_values) / count

            # Uncertainty = std / sqrt(n)
            if count > 1:
                variance = sum((v - mean_fit) ** 2 for v in fit_values) / count
                std = math.sqrt(variance)
                uncertainty = std / math.sqrt(count)
            else:
                uncertainty = 1.0  # single observation → max uncertainty

            # Determine claim status based on sample size
            if count >= self.min_samples:
                claim_status = "fit_claim"
                can_claim = True
            elif count >= MIN_SAMPLES_FOR_PROVISIONAL:
                claim_status = "provisional"
                can_claim = False
            else:
                claim_status = "insufficient_sample"
                can_claim = False

            results.append(StageFitResult(
                operator_id=operator_id,
                workflow_id=workflow.workflow_id,
                stage_id=stage.stage_id,
                provisional_fit=round(mean_fit, 4),
                observation_count=count,
                uncertainty=round(uncertainty, 4),
                claim_status=claim_status,
                can_claim_fit=can_claim,
                synthetic=True,
            ))

        return results

    def compute_cohort_fit(
        self,
        operator_ids: List[str],
        workflow: Workflow,
        all_observations: List[WorkflowObservation],
    ) -> WorkflowFitReport:
        """Compute workflow fit for all operators in a cohort."""
        operator_results: Dict[str, List[StageFitResult]] = {}
        summary_counts = {"fit_claim": 0, "provisional": 0, "insufficient_sample": 0}

        for oid in operator_ids:
            results = self.compute_fit(oid, workflow, all_observations)
            operator_results[oid] = results
            for r in results:
                summary_counts[r.claim_status] = summary_counts.get(r.claim_status, 0) + 1

        return WorkflowFitReport(
            workflow_id=workflow.workflow_id,
            stages=[s.stage_id for s in workflow.stages],
            operator_results=operator_results,
            min_sample_rule=self.min_samples,
            summary=summary_counts,
        )
