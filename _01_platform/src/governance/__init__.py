"""Governance — privacy governance surfaces per `12_PRIVACY_GOVERNANCE_SPEC.md`.

Surfaces:
    - Preferred manager objects (the development doctrine's "build these" list)
    - Decision-use classification labels (developmental / research /
      workflow experimentation / personnel)
    - Governance enforcement (6 items from MO§ES™ framework §13):
      purpose limitation, employee disclosure, consent, bias review,
      right to challenge, correction process

These are developmental objects, NOT performance rankings. The avoid-list
(no bottom-employee leaderboard, no automatic adverse-action ranking, no
punitive failure labels, no unsupported productivity claims) is enforced
across the codebase — this module surfaces the positive half of the
doctrine: the named manager-facing objects the product should build.
"""
from __future__ import annotations

from .decision_use import DecisionUse, decision_use_for_diagnosis, decision_use_for_intervention, decision_use_for_outcome_join
from .manager_objects import PreferredManagerObjects, compute_preferred_manager_objects
from .enforcement import (
    GovernanceEnforcement,
    ProcessingPurpose,
    PurposeLimitationGate,
    DisclosureAcknowledgment,
    DisclosureGate,
    DISCLOSURE_TEMPLATE,
    ConsentModel,
    ConsentState,
    ConsentRecord,
    ConsentManager,
    BiasSeverity,
    BiasReviewReport,
    BiasReviewManager,
    Challenge,
    ChallengeStatus,
    ChallengeResolution,
    ChallengeManager,
    CorrectionType,
    CorrectionStatus,
    CorrectionRecord,
    CorrectionManager,
    GovernanceAuditLog,
    GovernanceAuditEntry,
)

__all__ = [
    "DecisionUse",
    "decision_use_for_diagnosis",
    "decision_use_for_intervention",
    "decision_use_for_outcome_join",
    "PreferredManagerObjects",
    "compute_preferred_manager_objects",
    # Governance enforcement (spec 12 additions)
    "GovernanceEnforcement",
    "ProcessingPurpose",
    "PurposeLimitationGate",
    "DisclosureAcknowledgment",
    "DisclosureGate",
    "DISCLOSURE_TEMPLATE",
    "ConsentModel",
    "ConsentState",
    "ConsentRecord",
    "ConsentManager",
    "BiasSeverity",
    "BiasReviewReport",
    "BiasReviewManager",
    "Challenge",
    "ChallengeStatus",
    "ChallengeResolution",
    "ChallengeManager",
    "CorrectionType",
    "CorrectionStatus",
    "CorrectionRecord",
    "CorrectionManager",
    "GovernanceAuditLog",
    "GovernanceAuditEntry",
]
