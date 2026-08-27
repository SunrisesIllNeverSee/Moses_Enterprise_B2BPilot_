"""Decision-use classification labels per `12` §Decision-use restrictions.

The product should explicitly distinguish:
    - developmental use
    - research / measurement use
    - workflow experimentation
    - personnel decision use

Personnel actions should require higher evidence/governance thresholds. A
single measurement should never automatically trigger hiring, firing,
compensation, or promotion decisions.

This module provides the canonical enum and helper functions that map each
product surface to its decision-use class. The labels are surfaced in MCP
tool responses and markdown exporters via `decision_use_label()`.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.diagnosis import Diagnosis
    from domain.intervention import Intervention


class DecisionUse(str, Enum):
    """Decision-use classification per `12` §Decision-use restrictions."""
    DEVELOPMENTAL = "DEVELOPMENTAL"
    RESEARCH = "RESEARCH"
    WORKFLOW_EXPERIMENTATION = "WORKFLOW_EXPERIMENTATION"
    PERSONNEL = "PERSONNEL"

    def label(self) -> str:
        """Return the human-readable label with the governance caveat."""
        if self is DecisionUse.PERSONNEL:
            return (
                "PERSONNEL — requires higher evidence/governance thresholds; "
                "a single measurement must never automatically trigger a "
                "personnel decision"
            )
        return f"{self.value} — for {self.value.lower().replace('_', ' ')} use"


def decision_use_for_diagnosis(_diagnosis: "Diagnosis") -> DecisionUse:
    """Diagnostics are developmental — they surface hypotheses for growth, not
    personnel actions. Per `09`: a metric pattern is not a personality trait.
    """
    return DecisionUse.DEVELOPMENTAL


def decision_use_for_intervention(_intervention: "Intervention") -> DecisionUse:
    """Interventions/experiments are workflow experimentation — they test a
    change to the workflow/tooling, not a personnel action. Per `09`:
    interventions are EXPERIMENTS, not personnel actions.
    """
    return DecisionUse.WORKFLOW_EXPERIMENTATION


def decision_use_for_outcome_join() -> DecisionUse:
    """Outcome joins are research/measurement use — they correlate internal
    metrics with external outcomes under separate governance. Per P2: always
    ASSOCIATION, never CAUSATION.
    """
    return DecisionUse.RESEARCH


def decision_use_for_personnel() -> DecisionUse:
    """Personnel decisions require the highest governance threshold.

    Surfaces the elevated governance warning. Per `12`: "A single SigRank
    measurement should never automatically trigger hiring, firing,
    compensation, or promotion decisions."
    """
    return DecisionUse.PERSONNEL
