"""Outcome governance — separates association from causal claim.

Per `21` P2: "outcome joins remain separately governed" and "outcome analysis
separates association from causal claim."

Outcome data is customer-controlled and must be registered with governance
authorization before joining. The join is always labeled as ASSOCIATION,
never CAUSATION.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class GovernanceLevel(str, Enum):
    """Governance level required for outcome data joins."""
    NONE = "none"                    # no governance required (synthetic)
    CUSTOMER_APPROVED = "customer_approved"  # customer has approved the join
    IRB_APPROVED = "irb_approved"    # IRB or equivalent ethics board approval
    RESTRICTED = "restricted"        # join not permitted


@dataclass(frozen=True, slots=True)
class OutcomeGovernance:
    """Governance metadata for an outcome data source.

    Per P2: "outcome joins remain separately governed."
    """
    source: str                      # e.g. "github", "jira", "external_csv"
    governance_level: GovernanceLevel
    authorized_by: Optional[str]     # who authorized this join
    authorization_date: Optional[str]  # ISO date string
    privacy_class: str               # "pseudonymous" | "anonymized" | "identified"
    retention_days: int              # how long the join data may be retained
    purpose: str                     # declared purpose for this join
    causal_claim_permitted: bool = False  # ALWAYS False per P2

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "governance_level": self.governance_level.value,
            "authorized_by": self.authorized_by,
            "authorization_date": self.authorization_date,
            "privacy_class": self.privacy_class,
            "retention_days": self.retention_days,
            "purpose": self.purpose,
            "causal_claim_permitted": self.causal_claim_permitted,
        }

    @classmethod
    def synthetic(cls, source: str = "synthetic") -> "OutcomeGovernance":
        """Create a governance object for synthetic demo data."""
        return cls(
            source=source,
            governance_level=GovernanceLevel.NONE,
            authorized_by=None,
            authorization_date=None,
            privacy_class="pseudonymous_synthetic",
            retention_days=0,
            purpose="synthetic_demo",
            causal_claim_permitted=False,
        )
