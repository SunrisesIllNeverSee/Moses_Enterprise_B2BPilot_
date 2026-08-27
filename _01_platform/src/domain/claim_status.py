"""ClaimStatus — the 9-status claim registry per spec 17, unified with the
8-grade evidence ladder per Build B §12.

Two axes govern every statement MO§ES™ produces:

1. **EvidenceGrade** (evidence_grade.py) — how strong is the data? (8 levels)
2. **ClaimStatus** (this module) — what kind of claim is being made? (9 statuses)

These are complementary, not competing. The evidence grade determines which
claim statuses are *permitted*. A result with grade `controlled_experiment`
may carry claim status `CAUSALLY_SUPPORTED`. A result with grade
`insufficient_evidence` may only carry `HYPOTHESIS`.

The mapping function `permitted_claims(grade)` enforces this relationship.

Claim statuses (spec 17):
    PROVEN / CANONICAL  — mathematical identity or system behavior
    MEASURED            — observed in a declared dataset/window
    DERIVED             — computed deterministically from measurements
    REPLICATED          — repeated across declared samples/windows
    CORRELATED          — statistical association with external outcome
    PREDICTIVE          — validated out-of-sample predictive relationship
    CAUSALLY_SUPPORTED  — intervention/experimental evidence
    HYPOTHESIS          — plausible interpretation requiring testing
    MARKETING_PROHIBITED — language that should not be used without stronger evidence
"""
from __future__ import annotations

from enum import Enum
from typing import List, Set

from domain.evidence_grade import EvidenceGrade


class ClaimStatus(str, Enum):
    """The 9-status claim registry per spec 17."""
    PROVEN = "PROVEN"
    CANONICAL = "CANONICAL"
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    REPLICATED = "REPLICATED"
    CORRELATED = "CORRELATED"
    PREDICTIVE = "PREDICTIVE"
    CAUSALLY_SUPPORTED = "CAUSALLY_SUPPORTED"
    HYPOTHESIS = "HYPOTHESIS"
    MARKETING_PROHIBITED = "MARKETING_PROHIBITED"


# Evidence grade → permitted claim statuses
# This is the unified framework: the evidence ladder gates which claims
# are allowed. A result's evidence grade determines its maximum claim strength.
EVIDENCE_TO_CLAIMS: dict[EvidenceGrade, Set[ClaimStatus]] = {
    EvidenceGrade.CONTROLLED_EXPERIMENT: {
        ClaimStatus.PROVEN,
        ClaimStatus.CANONICAL,
        ClaimStatus.MEASURED,
        ClaimStatus.DERIVED,
        ClaimStatus.REPLICATED,
        ClaimStatus.CORRELATED,
        ClaimStatus.PREDICTIVE,
        ClaimStatus.CAUSALLY_SUPPORTED,
    },
    EvidenceGrade.COMPLETE_INTERACTION_TELEMETRY: {
        ClaimStatus.PROVEN,
        ClaimStatus.CANONICAL,
        ClaimStatus.MEASURED,
        ClaimStatus.DERIVED,
        ClaimStatus.REPLICATED,
        ClaimStatus.CORRELATED,
    },
    EvidenceGrade.STRONG_OBSERVATIONAL_TELEMETRY: {
        ClaimStatus.PROVEN,
        ClaimStatus.CANONICAL,
        ClaimStatus.MEASURED,
        ClaimStatus.DERIVED,
        ClaimStatus.REPLICATED,
        ClaimStatus.CORRELATED,
    },
    EvidenceGrade.PARTIAL_TELEMETRY: {
        ClaimStatus.MEASURED,
        ClaimStatus.DERIVED,
        ClaimStatus.HYPOTHESIS,
    },
    EvidenceGrade.ACTIVITY_METADATA: {
        ClaimStatus.MEASURED,
        ClaimStatus.HYPOTHESIS,
    },
    EvidenceGrade.CUSTOMER_SUPPLIED_OUTCOME: {
        ClaimStatus.CORRELATED,
        ClaimStatus.PREDICTIVE,
        ClaimStatus.HYPOTHESIS,
    },
    EvidenceGrade.INFERRED_SIGNAL: {
        ClaimStatus.HYPOTHESIS,
    },
    EvidenceGrade.INSUFFICIENT_EVIDENCE: {
        ClaimStatus.HYPOTHESIS,
    },
}

# Claim status → required minimum evidence grade
# The inverse mapping: to make this claim, you need at least this grade.
CLAIM_TO_MIN_GRADE: dict[ClaimStatus, EvidenceGrade] = {
    ClaimStatus.PROVEN: EvidenceGrade.CONTROLLED_EXPERIMENT,
    ClaimStatus.CANONICAL: EvidenceGrade.CONTROLLED_EXPERIMENT,
    ClaimStatus.CAUSALLY_SUPPORTED: EvidenceGrade.CONTROLLED_EXPERIMENT,
    ClaimStatus.PREDICTIVE: EvidenceGrade.CUSTOMER_SUPPLIED_OUTCOME,
    ClaimStatus.REPLICATED: EvidenceGrade.STRONG_OBSERVATIONAL_TELEMETRY,
    ClaimStatus.CORRELATED: EvidenceGrade.STRONG_OBSERVATIONAL_TELEMETRY,
    ClaimStatus.DERIVED: EvidenceGrade.COMPLETE_INTERACTION_TELEMETRY,
    ClaimStatus.MEASURED: EvidenceGrade.PARTIAL_TELEMETRY,
    ClaimStatus.HYPOTHESIS: EvidenceGrade.INSUFFICIENT_EVIDENCE,
    ClaimStatus.MARKETING_PROHIBITED: EvidenceGrade.INSUFFICIENT_EVIDENCE,
}


def permitted_claims(grade: EvidenceGrade) -> List[ClaimStatus]:
    """Return the claim statuses permitted at this evidence grade.

    The evidence grade determines the maximum claim strength. A result
    may carry any claim status in the returned list. Claims above this
    level are prohibited and must be downgraded.
    """
    return sorted(EVIDENCE_TO_CLAIMS.get(grade, {ClaimStatus.HYPOTHESIS}),
                  key=lambda c: list(ClaimStatus).index(c))


def can_claim(grade: EvidenceGrade, status: ClaimStatus) -> bool:
    """Check whether this evidence grade permits this claim status."""
    return status in EVIDENCE_TO_CLAIMS.get(grade, set())


def min_grade_for_claim(status: ClaimStatus) -> EvidenceGrade:
    """Return the minimum evidence grade required to make this claim."""
    return CLAIM_TO_MIN_GRADE.get(status, EvidenceGrade.INSUFFICIENT_EVIDENCE)


def enforce_claim(grade: EvidenceGrade, requested: ClaimStatus) -> ClaimStatus:
    """Enforce the evidence-grade → claim-status mapping.

    If the requested claim is permitted at this grade, return it.
    Otherwise, downgrade to the strongest permitted claim, or HYPOTHESIS
    if none are permitted.
    """
    if can_claim(grade, requested):
        return requested
    permitted = permitted_claims(grade)
    if permitted:
        return permitted[-1]  # strongest permitted
    return ClaimStatus.HYPOTHESIS
