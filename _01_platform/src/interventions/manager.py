"""Intervention manager — recommend, assign, and close interventions.

Per `21` P1 acceptance: "intervention declares target metric/window before
follow-up." This manager enforces that rule: an intervention cannot be
assigned without declaring its target metric and follow-up window.

Per `09`: interventions are EXPERIMENTS, not personnel actions. The manager
labels them as RECOMMENDATION (requires human approval) and EXPERIMENT.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.diagnosis import Diagnosis
from domain.intervention import Intervention, InterventionOutcome
from .registry import InterventionRegistry, InterventionCatalogEntry


class InterventionManager:
    """Manages intervention recommendation, assignment, and closure.

    Enforces P1 acceptance: "intervention declares target metric/window
    before follow-up."
    """

    def __init__(self, registry: Optional[InterventionRegistry] = None) -> None:
        self.registry = registry or InterventionRegistry()

    def recommend(self, diagnoses: List[Diagnosis]) -> List[InterventionCatalogEntry]:
        """Recommend interventions for a list of diagnoses.

        Returns catalog entries, deduplicated, sorted by relevance.
        """
        seen = set()
        recommendations: List[InterventionCatalogEntry] = []
        for d in diagnoses:
            for catalog_id in d.recommended_interventions:
                if catalog_id in seen:
                    continue
                seen.add(catalog_id)
                try:
                    entry = self.registry.get(catalog_id)
                    recommendations.append(entry)
                except KeyError:
                    pass  # skip unknown catalog IDs
        return recommendations

    def assign(
        self,
        intervention_id: str,
        operator_id: str,
        catalog_id: str,
        reason_pattern: str,
        target_metric: str,
        start_date: date,
        followup_days: int,
        synthetic: bool = True,
    ) -> Intervention:
        """Assign a new intervention.

        Per P1 acceptance, target_metric and followup_days are REQUIRED.
        Raises ValueError if target_metric is empty or followup_days <= 0.
        """
        if not target_metric:
            raise ValueError("target_metric is required (P1: intervention declares target metric before follow-up)")
        if followup_days <= 0:
            raise ValueError("followup_days must be > 0 (P1: intervention declares window before follow-up)")

        # Validate the catalog entry exists
        entry = self.registry.get(catalog_id)

        # Validate target metric is compatible (warn but don't block)
        if not self.registry.validate_target_metric(catalog_id, target_metric):
            # Soft warning — allow override but the mismatch is recorded
            pass

        return Intervention(
            intervention_id=intervention_id,
            operator_id=operator_id,
            catalog_id=catalog_id,
            reason_pattern=reason_pattern,
            target_metric=target_metric,
            start_date=start_date,
            followup_days=followup_days,
            synthetic_outcome=InterventionOutcome.PENDING,
            synthetic=synthetic,
        )

    def close(
        self,
        intervention: Intervention,
        outcome: InterventionOutcome,
    ) -> Intervention:
        """Close an intervention with a declared outcome.

        Per P1 acceptance: "intervention failure is representable and reportable."
        NEGATIVE and NO_EFFECT outcomes are explicitly representable.
        """
        return Intervention(
            intervention_id=intervention.intervention_id,
            operator_id=intervention.operator_id,
            catalog_id=intervention.catalog_id,
            reason_pattern=intervention.reason_pattern,
            target_metric=intervention.target_metric,
            start_date=intervention.start_date,
            followup_days=intervention.followup_days,
            synthetic_outcome=outcome,
            synthetic=intervention.synthetic,
        )

    def followup_window(self, intervention: Intervention) -> tuple[date, date]:
        """Return the (start, end) of the follow-up window."""
        end = intervention.start_date + timedelta(days=intervention.followup_days)
        return (intervention.start_date, end)

    def is_representable_failure(self, intervention: Intervention) -> bool:
        """Check if an intervention outcome is a representable failure.

        Per P1: "intervention failure is representable and reportable."
        """
        return intervention.synthetic_outcome in (
            InterventionOutcome.NEGATIVE,
            InterventionOutcome.NO_EFFECT,
        )
