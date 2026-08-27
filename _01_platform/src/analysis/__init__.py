"""Analysis — cohort distributions, divergence, percentiles, eligibility, quality,
org topology (EVAL-013), operator similarity (EVAL-014),
operator×system decomposition, outcome correlation.

P0-D analysis functions that operate on Measurements produced by the
ScoringEngine. These are pure functions — no I/O, no side effects.
"""
from __future__ import annotations

from .divergence import compute_divergence, DivergenceResult
from .percentiles import compute_percentiles
from .distributions import compute_cohort_distributions, MetricDistribution
from .eligibility import check_eligibility, check_cohort_eligibility, EligibilityConfig
from .data_quality import (
    run_all_quality_checks, summarize_quality,
    check_missingness, check_impossible_values, check_duplicates,
    check_provenance, check_sparse_operators,
)
from .verifier import PrePostVerifier, VerificationResult, MetricDelta
from .replication import ReplicationEngine, ReplicationResult, ReplicationStatus, SplitMethod
from .org_topology import (
    compute_org_topology, OrgTopology, TeamTopology,
    CapabilityConcentration, PlatformAdoption, SinglePointOfFailure,
)
from .similarity import (
    compute_operator_similarity, SimilarityResult, SimilarityMatch,
)
from .operator_system import (
    compute_operator_system_decomposition, OperatorSystemDecomposition,
    MetricDecomposition, OperatorEffect, SystemEffect, InteractionCell,
)
from .outcome_correlation import (
    compute_outcome_correlation, OutcomeCorrelationResult,
    MetricOutcomeCorrelation,
)

__all__ = [
    "compute_divergence", "DivergenceResult",
    "compute_percentiles",
    "compute_cohort_distributions", "MetricDistribution",
    "check_eligibility", "check_cohort_eligibility", "EligibilityConfig",
    "run_all_quality_checks", "summarize_quality",
    "check_missingness", "check_impossible_values", "check_duplicates",
    "check_provenance", "check_sparse_operators",
    "PrePostVerifier", "VerificationResult", "MetricDelta",
    "ReplicationEngine", "ReplicationResult", "ReplicationStatus", "SplitMethod",
    # EVAL-013: Org AI Topology
    "compute_org_topology", "OrgTopology", "TeamTopology",
    "CapabilityConcentration", "PlatformAdoption", "SinglePointOfFailure",
    # EVAL-014: Operator Similarity Search
    "compute_operator_similarity", "SimilarityResult", "SimilarityMatch",
    # Operator×System decomposition
    "compute_operator_system_decomposition", "OperatorSystemDecomposition",
    "MetricDecomposition", "OperatorEffect", "SystemEffect", "InteractionCell",
    # Outcome correlation through lineage
    "compute_outcome_correlation", "OutcomeCorrelationResult",
    "MetricOutcomeCorrelation",
]
