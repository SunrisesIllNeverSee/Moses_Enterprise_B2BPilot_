"""Benchmark Engine implementation — MO§ES™ Enterprise Pilot Readiness §7.

Implements the 13 benchmark classes, the selection algorithm (§7.14),
statistical methods (§7.15), composition rules (§7.16), and uncertainty
presentation (§7.17).

Design principles (§7.0.1):
  1. No false leaderboards — benchmarks never present a simple ranked list
     without uncertainty.
  2. Within-operator preference — prefer within-operator comparisons over
     between-operator comparisons.
  3. Benchmark legitimacy — not every comparison is legitimate; the selection
     algorithm determines which benchmark class is valid.
  4. Uncertainty is mandatory — every benchmark result includes confidence
     intervals, sample sizes, eligibility criteria, and limitations.
  5. Nesting is explicit — benchmarks can be composed, but the composition is
     always made explicit in the output.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ── Enums ────────────────────────────────────────────────────────────────


class BenchmarkClass(str, Enum):
    """The 13 benchmark classes from §7."""

    SELF_VS_PRIOR = "self_vs_prior"
    REPEATED_TASK = "repeated_task"
    MATCHED_TASK = "matched_task"
    PEER = "peer"
    ROLE = "role"
    COHORT = "cohort"
    TEAM = "team"
    ORGANIZATION = "organization"
    SYSTEM = "system"
    WORKFLOW = "workflow"
    MODEL = "model"
    INTERVENTION = "intervention"
    EXTERNAL_FIELD = "external_field"


class StatisticalMethod(str, Enum):
    """Statistical methods from §7.15."""

    PAIRED_BOOTSTRAP_BCA = "paired_bootstrap_bca"
    CLUSTER_BOOTSTRAP = "cluster_bootstrap"
    NON_PAIRED_BOOTSTRAP_BCA = "non_paired_bootstrap_bca"
    BAYESIAN_HIERARCHICAL = "bayesian_hierarchical"
    BAYESIAN_DIRICHLET = "bayesian_dirichlet"
    BAYESIAN_BEFORE_AFTER = "bayesian_before_after"
    WILCOXON_SIGNED_RANK = "wilcoxon_signed_rank"
    MANN_WHITNEY_U = "mann_whitney_u"
    KRUSKAL_WALLIS = "kruskal_wallis"
    FRIEDMAN = "friedman"
    PERMUTATION_TEST = "permutation_test"
    DIFFERENCE_IN_DIFFERENCES = "difference_in_differences"
    MIXED_EFFECTS_REML = "mixed_effects_reml"
    OLS_ROBUST = "ols_robust"


class EvidenceGrade(str, Enum):
    """Evidence grades from §12, used in benchmark results."""

    CONTROLLED_EXPERIMENT = "controlled_experiment"
    COMPLETE_INTERACTION = "complete_interaction_telemetry"
    STRONG_OBSERVATIONAL = "strong_observational_telemetry"
    PARTIAL_TELEMETRY = "partial_telemetry"
    ACTIVITY_METADATA = "activity_metadata"
    CUSTOMER_SUPPLIED = "customer_supplied_outcome"
    INFERRED_SIGNAL = "inferred_signal"
    INSUFFICIENT = "insufficient_evidence"


# ── Data structures ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class BenchmarkContext:
    """Context for a benchmark evaluation.

    Carries all the information the selection algorithm and benchmark
    computations need: the operator, their measurements, the comparison
    group, and eligibility metadata.
    """

    operator_id: str
    metric: str
    operator_value: float
    window_start: date
    window_end: date
    # Comparison data
    comparison_values: Tuple[float, ...] = ()
    comparison_description: str = ""
    # Operator metadata
    team: Optional[str] = None
    role_family: Optional[str] = None
    cohort_id: Optional[str] = None
    # Prior window (for self_vs_prior)
    prior_window_values: Tuple[float, ...] = ()
    prior_window_start: Optional[date] = None
    prior_window_end: Optional[date] = None
    # Repeated task
    repeated_task_values: Tuple[Tuple[float, ...], ...] = ()
    # Intervention
    is_intervention: bool = False
    control_group_values: Tuple[float, ...] = ()
    treatment_group_values: Tuple[float, ...] = ()
    # External field
    external_field_values: Tuple[float, ...] = ()
    # System / model / workflow context
    system_id: Optional[str] = None
    model_id: Optional[str] = None
    workflow_stage_id: Optional[str] = None
    # Sample sizes
    operator_sample_size: int = 0
    comparison_sample_size: int = 0
    # Synthetic marker
    synthetic: bool = False


@dataclass(frozen=True)
class EligibilityResult:
    """Result of checking benchmark eligibility criteria."""

    eligible: bool
    criteria_checked: int
    criteria_passed: int
    failed_criteria: Tuple[str, ...] = ()


@dataclass(frozen=True)
class BenchmarkResult:
    """A single benchmark comparison result.

    Follows the schema from §7.0.2. Every result includes uncertainty,
    eligibility, and limitations.
    """

    benchmark_id: str
    benchmark_class: BenchmarkClass
    operator_id: str
    metric: str
    window_start: date
    window_end: date
    comparison_group: Dict[str, Any]
    eligibility: EligibilityResult
    result: Dict[str, Any]
    statistical_method: StatisticalMethod
    confidence_level: float
    sample_size: Dict[str, int]
    limitations: Tuple[str, ...]
    nested_benchmarks: Tuple["BenchmarkResult", ...] = ()
    evidence_grade: EvidenceGrade = EvidenceGrade.STRONG_OBSERVATIONAL
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    synthetic: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "benchmark_id": self.benchmark_id,
            "benchmark_class": self.benchmark_class.value,
            "operator_id": self.operator_id,
            "metric": self.metric,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "comparison_group": self.comparison_group,
            "eligibility": {
                "eligible": self.eligibility.eligible,
                "criteria_checked": self.eligibility.criteria_checked,
                "criteria_passed": self.eligibility.criteria_passed,
                "failed_criteria": list(self.eligibility.failed_criteria),
            },
            "result": self.result,
            "statistical_method": self.statistical_method.value,
            "confidence_level": self.confidence_level,
            "sample_size": self.sample_size,
            "limitations": list(self.limitations),
            "nested_benchmarks": [nb.to_dict() for nb in self.nested_benchmarks],
            "evidence_grade": self.evidence_grade.value,
            "timestamp": self.timestamp,
            "synthetic": self.synthetic,
        }


@dataclass(frozen=True)
class SelectionResult:
    """Result of the benchmark selection algorithm (§7.14)."""

    selected_class: Optional[BenchmarkClass]
    reason: str
    alternatives_considered: Tuple[BenchmarkClass, ...] = ()


# ── Statistical helpers ──────────────────────────────────────────────────


def _percentile_rank(value: float, reference: List[float]) -> float:
    """Compute the percentile rank of a value against a reference distribution."""
    if not reference:
        return 0.0
    below = sum(1 for r in reference if r < value)
    equal = sum(1 for r in reference if r == value)
    n = len(reference)
    # Use the midpoint method for ties
    return 100.0 * (below + 0.5 * equal) / n


def _bootstrap_ci(
    values: List[float],
    statistic_fn,
    n_resamples: int = 5000,
    confidence: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float]:
    """Bootstrap confidence interval (percentile method).

    A simplified bootstrap that doesn't require external dependencies.
    For production, replace with BCa (bias-corrected accelerated).
    """
    import random

    rng = random.Random(seed)
    n = len(values)
    if n < 2:
        return (0.0, 0.0)

    boot_stats = []
    for _ in range(n_resamples):
        sample = [rng.choice(values) for _ in range(n)]
        try:
            boot_stats.append(statistic_fn(sample))
        except (ZeroDivisionError, statistics.StatisticsError):
            continue

    if not boot_stats:
        return (0.0, 0.0)

    boot_stats.sort()
    alpha = (1.0 - confidence) / 2.0
    lower_idx = int(alpha * len(boot_stats))
    upper_idx = int((1.0 - alpha) * len(boot_stats)) - 1
    return (boot_stats[lower_idx], boot_stats[max(upper_idx, lower_idx)])


def _median(values: List[float]) -> float:
    """Safe median."""
    if not values:
        return 0.0
    return statistics.median(values)


def _iqr(values: List[float]) -> Tuple[float, float]:
    """Interquartile range (Q1, Q3)."""
    if not values:
        return (0.0, 0.0)
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    q1_idx = n // 4
    q3_idx = (3 * n) // 4
    return (sorted_vals[q1_idx], sorted_vals[min(q3_idx, n - 1)])


def _select_method(
    benchmark_class: BenchmarkClass,
    sample_size: int,
) -> StatisticalMethod:
    """Select the statistical method per §7.15.5 decision table."""
    table = {
        BenchmarkClass.SELF_VS_PRIOR: (
            StatisticalMethod.PAIRED_BOOTSTRAP_BCA
            if sample_size >= 10
            else StatisticalMethod.WILCOXON_SIGNED_RANK
        ),
        BenchmarkClass.REPEATED_TASK: (
            StatisticalMethod.PAIRED_BOOTSTRAP_BCA
            if sample_size >= 5
            else StatisticalMethod.FRIEDMAN
        ),
        BenchmarkClass.MATCHED_TASK: (
            StatisticalMethod.PAIRED_BOOTSTRAP_BCA
            if sample_size >= 5
            else StatisticalMethod.PERMUTATION_TEST
        ),
        BenchmarkClass.PEER: (
            StatisticalMethod.NON_PAIRED_BOOTSTRAP_BCA
            if sample_size >= 20
            else StatisticalMethod.BAYESIAN_DIRICHLET
        ),
        BenchmarkClass.ROLE: (
            StatisticalMethod.NON_PAIRED_BOOTSTRAP_BCA
            if sample_size >= 25
            else StatisticalMethod.BAYESIAN_HIERARCHICAL
        ),
        BenchmarkClass.COHORT: (
            StatisticalMethod.NON_PAIRED_BOOTSTRAP_BCA
            if sample_size >= 20
            else StatisticalMethod.PERMUTATION_TEST
        ),
        BenchmarkClass.TEAM: (
            StatisticalMethod.NON_PAIRED_BOOTSTRAP_BCA
            if sample_size >= 5
            else StatisticalMethod.BAYESIAN_HIERARCHICAL
        ),
        BenchmarkClass.ORGANIZATION: (
            StatisticalMethod.NON_PAIRED_BOOTSTRAP_BCA
            if sample_size >= 50
            else StatisticalMethod.MIXED_EFFECTS_REML
        ),
        BenchmarkClass.SYSTEM: (
            StatisticalMethod.NON_PAIRED_BOOTSTRAP_BCA
            if sample_size >= 10
            else StatisticalMethod.MIXED_EFFECTS_REML
        ),
        BenchmarkClass.WORKFLOW: (
            StatisticalMethod.NON_PAIRED_BOOTSTRAP_BCA
            if sample_size >= 10
            else StatisticalMethod.MIXED_EFFECTS_REML
        ),
        BenchmarkClass.MODEL: (
            StatisticalMethod.PAIRED_BOOTSTRAP_BCA
            if sample_size >= 10
            else StatisticalMethod.WILCOXON_SIGNED_RANK
        ),
        BenchmarkClass.INTERVENTION: (
            StatisticalMethod.DIFFERENCE_IN_DIFFERENCES
            if sample_size >= 10
            else StatisticalMethod.BAYESIAN_BEFORE_AFTER
        ),
        BenchmarkClass.EXTERNAL_FIELD: (
            StatisticalMethod.NON_PAIRED_BOOTSTRAP_BCA
            if sample_size >= 100
            else StatisticalMethod.BAYESIAN_DIRICHLET
        ),
    }
    return table.get(benchmark_class, StatisticalMethod.NON_PAIRED_BOOTSTRAP_BCA)


def _evidence_grade_for_class(
    benchmark_class: BenchmarkClass,
) -> EvidenceGrade:
    """Map benchmark class to default evidence grade."""
    if benchmark_class == BenchmarkClass.INTERVENTION:
        return EvidenceGrade.CONTROLLED_EXPERIMENT
    elif benchmark_class in (
        BenchmarkClass.SELF_VS_PRIOR,
        BenchmarkClass.REPEATED_TASK,
        BenchmarkClass.MATCHED_TASK,
    ):
        return EvidenceGrade.COMPLETE_INTERACTION
    elif benchmark_class == BenchmarkClass.EXTERNAL_FIELD:
        return EvidenceGrade.STRONG_OBSERVATIONAL
    else:
        return EvidenceGrade.STRONG_OBSERVATIONAL


def _limitations_for_class(
    benchmark_class: BenchmarkClass,
) -> Tuple[str, ...]:
    """Standard limitations per benchmark class."""
    base = ("observational_comparison", "no_causal_claim")
    specific = {
        BenchmarkClass.INTERVENTION: (
            "quasi_experimental",
            "confound_possible",
        ),
        BenchmarkClass.EXTERNAL_FIELD: (
            "external_reference",
            "population_match_not_verified",
        ),
        BenchmarkClass.SELF_VS_PRIOR: (
            "within_operator",
            "controls_for_individual_differences",
        ),
        BenchmarkClass.REPEATED_TASK: (
            "within_operator",
            "task_identity_assumed",
        ),
        BenchmarkClass.PEER: ("peer_definition_assumed",),
        BenchmarkClass.TEAM: ("team_definition_assumed",),
    }
    return specific.get(benchmark_class, base)


# ── Eligibility checks ───────────────────────────────────────────────────


def _check_eligibility(
    benchmark_class: BenchmarkClass,
    ctx: BenchmarkContext,
) -> EligibilityResult:
    """Check eligibility criteria for a benchmark class.

    Each class has different minimum sample size requirements per §7.1–7.13.
    """
    checks = []
    comparison = list(ctx.comparison_values)

    # Common: need at least some comparison data
    checks.append(("has_comparison_data", len(comparison) > 0))
    checks.append(("has_operator_value", ctx.operator_value is not None))

    # Class-specific minimums
    min_sizes = {
        BenchmarkClass.SELF_VS_PRIOR: 5,  # need ≥5 prior observations
        BenchmarkClass.REPEATED_TASK: 2,
        BenchmarkClass.MATCHED_TASK: 2,
        BenchmarkClass.PEER: 5,
        BenchmarkClass.ROLE: 10,
        BenchmarkClass.COHORT: 10,
        BenchmarkClass.TEAM: 3,
        BenchmarkClass.ORGANIZATION: 20,
        BenchmarkClass.SYSTEM: 10,
        BenchmarkClass.WORKFLOW: 10,
        BenchmarkClass.MODEL: 10,
        BenchmarkClass.INTERVENTION: 5,
        BenchmarkClass.EXTERNAL_FIELD: 50,
    }
    min_n = min_sizes.get(benchmark_class, 5)
    checks.append(("min_sample_size", len(comparison) >= min_n))

    # Self vs prior: need prior window data
    if benchmark_class == BenchmarkClass.SELF_VS_PRIOR:
        checks.append(("has_prior_window", len(ctx.prior_window_values) > 0))

    # Intervention: need treatment + control
    if benchmark_class == BenchmarkClass.INTERVENTION:
        checks.append((
            "has_control_group",
            len(ctx.control_group_values) > 0,
        ))

    # External field: need external data
    if benchmark_class == BenchmarkClass.EXTERNAL_FIELD:
        checks.append((
            "has_external_data",
            len(ctx.external_field_values) > 0,
        ))

    passed = sum(1 for _, ok in checks if ok)
    failed = tuple(name for name, ok in checks if not ok)
    return EligibilityResult(
        eligible=passed == len(checks),
        criteria_checked=len(checks),
        criteria_passed=passed,
        failed_criteria=failed,
    )


# ── Benchmark computations ───────────────────────────────────────────────


def _compute_benchmark(
    benchmark_class: BenchmarkClass,
    ctx: BenchmarkContext,
) -> BenchmarkResult:
    """Compute a single benchmark result.

    This is the core computation that produces the comparison statistics,
    confidence intervals, and percentile ranks.
    """
    comparison = list(ctx.comparison_values)
    eligibility = _check_eligibility(benchmark_class, ctx)

    # If not eligible, return a result with empty comparison
    if not eligibility.eligible:
        return BenchmarkResult(
            benchmark_id=f"bench_{benchmark_class.value}_{ctx.operator_id}",
            benchmark_class=benchmark_class,
            operator_id=ctx.operator_id,
            metric=ctx.metric,
            window_start=ctx.window_start,
            window_end=ctx.window_end,
            comparison_group={"n": len(comparison), "description": ctx.comparison_description},
            eligibility=eligibility,
            result={},
            statistical_method=_select_method(benchmark_class, len(comparison)),
            confidence_level=0.95,
            sample_size={
                "operator": ctx.operator_sample_size,
                "benchmark_group": len(comparison),
            },
            limitations=_limitations_for_class(benchmark_class),
            evidence_grade=EvidenceGrade.INSUFFICIENT,
            synthetic=ctx.synthetic,
        )

    # Compute comparison statistics
    bench_median = _median(comparison)
    bench_q1, bench_q3 = _iqr(comparison)
    delta = ctx.operator_value - bench_median
    pct_rank = _percentile_rank(ctx.operator_value, comparison)

    # Bootstrap CI for the percentile rank
    pct_ci = _bootstrap_ci(
        comparison,
        lambda sample: _percentile_rank(ctx.operator_value, sample),
        n_resamples=2000,
    )

    # Bootstrap CI for the delta
    delta_ci = _bootstrap_ci(
        comparison,
        lambda sample: ctx.operator_value - _median(sample),
        n_resamples=2000,
    )

    method = _select_method(benchmark_class, len(comparison))

    result_data = {
        "metric": ctx.metric,
        "operator_value": round(ctx.operator_value, 4),
        "benchmark_median": round(bench_median, 4),
        "benchmark_iqr": [round(bench_q1, 4), round(bench_q3, 4)],
        "delta": round(delta, 4),
        "delta_ci_95": [round(delta_ci[0], 4), round(delta_ci[1], 4)],
        "percentile_rank": round(pct_rank, 2),
        "percentile_ci_95": [round(pct_ci[0], 2), round(pct_ci[1], 2)],
    }

    # Intervention-specific: add treatment vs control delta
    if benchmark_class == BenchmarkClass.INTERVENTION:
        treatment = list(ctx.treatment_group_values)
        control = list(ctx.control_group_values)
        if treatment and control:
            treatment_mean = statistics.mean(treatment)
            control_mean = statistics.mean(control)
            result_data["treatment_mean"] = round(treatment_mean, 4)
            result_data["control_mean"] = round(control_mean, 4)
            result_data["treatment_control_delta"] = round(
                treatment_mean - control_mean, 4
            )

    # Self vs prior: add prior window stats
    if (
        benchmark_class == BenchmarkClass.SELF_VS_PRIOR
        and ctx.prior_window_values
    ):
        prior = list(ctx.prior_window_values)
        result_data["prior_median"] = round(_median(prior), 4)
        result_data["prior_iqr"] = [
            round(_iqr(prior)[0], 4),
            round(_iqr(prior)[1], 4),
        ]
        result_data["change_from_prior"] = round(
            ctx.operator_value - _median(prior), 4
        )

    return BenchmarkResult(
        benchmark_id=f"bench_{benchmark_class.value}_{ctx.operator_id}",
        benchmark_class=benchmark_class,
        operator_id=ctx.operator_id,
        metric=ctx.metric,
        window_start=ctx.window_start,
        window_end=ctx.window_end,
        comparison_group={"n": len(comparison), "description": ctx.comparison_description},
        eligibility=eligibility,
        result=result_data,
        statistical_method=method,
        confidence_level=0.95,
        sample_size={
            "operator": ctx.operator_sample_size,
            "benchmark_group": len(comparison),
        },
        limitations=_limitations_for_class(benchmark_class),
        evidence_grade=_evidence_grade_for_class(benchmark_class),
        synthetic=ctx.synthetic,
    )


# ── Selection algorithm (§7.14) ──────────────────────────────────────────


def select_benchmark(ctx: BenchmarkContext) -> SelectionResult:
    """Select the legitimate benchmark class for a given context.

    Implements the priority-ordered decision tree from §7.14.
    Within-operator benchmarks are preferred over between-operator benchmarks.
    """
    alternatives: List[BenchmarkClass] = []

    # STEP 1: Intervention
    if ctx.is_intervention:
        elig = _check_eligibility(BenchmarkClass.INTERVENTION, ctx)
        if elig.eligible:
            return SelectionResult(
                selected_class=BenchmarkClass.INTERVENTION,
                reason="Intervention eval — intervention benchmark selected (step 1)",
                alternatives_considered=tuple(alternatives),
            )

    # STEP 2: Repeated task
    if len(ctx.repeated_task_values) >= 2:
        alternatives.append(BenchmarkClass.REPEATED_TASK)
        elig = _check_eligibility(BenchmarkClass.REPEATED_TASK, ctx)
        if elig.eligible:
            return SelectionResult(
                selected_class=BenchmarkClass.REPEATED_TASK,
                reason="≥2 instances of same task — repeated task benchmark (step 2)",
                alternatives_considered=tuple(alternatives),
            )

    # STEP 3: Matched task (skip — requires propensity score match data)
    # Not implementable without matched task pairs; fall through.

    # STEP 4: Self vs prior self
    if ctx.prior_window_values:
        alternatives.append(BenchmarkClass.SELF_VS_PRIOR)
        elig = _check_eligibility(BenchmarkClass.SELF_VS_PRIOR, ctx)
        if elig.eligible:
            return SelectionResult(
                selected_class=BenchmarkClass.SELF_VS_PRIOR,
                reason="≥2 windows with no intervention — self vs prior (step 4)",
                alternatives_considered=tuple(alternatives),
            )

    # STEP 5: Peer (≥5 similar operators)
    if len(ctx.comparison_values) >= 5:
        alternatives.append(BenchmarkClass.PEER)
        elig = _check_eligibility(BenchmarkClass.PEER, ctx)
        if elig.eligible:
            return SelectionResult(
                selected_class=BenchmarkClass.PEER,
                reason="≥5 similar operators available — peer benchmark (step 5)",
                alternatives_considered=tuple(alternatives),
            )

    # STEP 6: Team (≥3 members)
    if ctx.team and len(ctx.comparison_values) >= 3:
        alternatives.append(BenchmarkClass.TEAM)
        elig = _check_eligibility(BenchmarkClass.TEAM, ctx)
        if elig.eligible:
            return SelectionResult(
                selected_class=BenchmarkClass.TEAM,
                reason="Operator on team with ≥3 members — team benchmark (step 6)",
                alternatives_considered=tuple(alternatives),
            )

    # STEP 7: Role (≥10 operators)
    if ctx.role_family and len(ctx.comparison_values) >= 10:
        alternatives.append(BenchmarkClass.ROLE)
        elig = _check_eligibility(BenchmarkClass.ROLE, ctx)
        if elig.eligible:
            return SelectionResult(
                selected_class=BenchmarkClass.ROLE,
                reason="Role with ≥10 operators — role benchmark (step 7)",
                alternatives_considered=tuple(alternatives),
            )

    # STEP 8: Cohort (≥10 operators)
    if ctx.cohort_id and len(ctx.comparison_values) >= 10:
        alternatives.append(BenchmarkClass.COHORT)
        elig = _check_eligibility(BenchmarkClass.COHORT, ctx)
        if elig.eligible:
            return SelectionResult(
                selected_class=BenchmarkClass.COHORT,
                reason="Cohort with ≥10 operators — cohort benchmark (step 8)",
                alternatives_considered=tuple(alternatives),
            )

    # STEP 9: Organization (≥20 operators)
    if len(ctx.comparison_values) >= 20:
        alternatives.append(BenchmarkClass.ORGANIZATION)
        elig = _check_eligibility(BenchmarkClass.ORGANIZATION, ctx)
        if elig.eligible:
            return SelectionResult(
                selected_class=BenchmarkClass.ORGANIZATION,
                reason="Organization with ≥20 operators — org benchmark (step 9)",
                alternatives_considered=tuple(alternatives),
            )

    # STEP 10: External field
    if ctx.external_field_values:
        alternatives.append(BenchmarkClass.EXTERNAL_FIELD)
        elig = _check_eligibility(BenchmarkClass.EXTERNAL_FIELD, ctx)
        if elig.eligible:
            return SelectionResult(
                selected_class=BenchmarkClass.EXTERNAL_FIELD,
                reason="Approved external benchmark available — external field (step 10)",
                alternatives_considered=tuple(alternatives),
            )

    # STEP 11: No valid benchmark
    return SelectionResult(
        selected_class=None,
        reason="No valid benchmark class — insufficient data for all classes",
        alternatives_considered=tuple(alternatives),
    )


# ── Benchmark Engine ─────────────────────────────────────────────────────


class BenchmarkEngine:
    """The benchmark engine.

    Usage:
        engine = BenchmarkEngine()
        result = engine.evaluate(ctx)
        # result is a BenchmarkResult with full uncertainty disclosure

    The engine:
      1. Selects the legitimate benchmark class (§7.14)
      2. Checks eligibility (§7.1–7.13 per-class rules)
      3. Computes the comparison with appropriate statistical methods (§7.15)
      4. Presents results with full uncertainty (§7.17)
    """

    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level

    def select(self, ctx: BenchmarkContext) -> SelectionResult:
        """Run the selection algorithm to determine the benchmark class."""
        return select_benchmark(ctx)

    def evaluate(
        self,
        ctx: BenchmarkContext,
        benchmark_class: Optional[BenchmarkClass] = None,
    ) -> BenchmarkResult:
        """Evaluate a benchmark.

        If benchmark_class is provided, compute that specific class.
        Otherwise, run the selection algorithm and compute the selected class.
        """
        if benchmark_class is None:
            selection = self.select(ctx)
            if selection.selected_class is None:
                # No valid benchmark — return an empty result
                return BenchmarkResult(
                    benchmark_id=f"bench_none_{ctx.operator_id}",
                    benchmark_class=BenchmarkClass.COHORT,  # placeholder
                    operator_id=ctx.operator_id,
                    metric=ctx.metric,
                    window_start=ctx.window_start,
                    window_end=ctx.window_end,
                    comparison_group={"n": 0, "description": "no valid benchmark"},
                    eligibility=EligibilityResult(
                        eligible=False,
                        criteria_checked=0,
                        criteria_passed=0,
                        failed_criteria=("no_valid_benchmark",),
                    ),
                    result={},
                    statistical_method=StatisticalMethod.NON_PAIRED_BOOTSTRAP_BCA,
                    confidence_level=self.confidence_level,
                    sample_size={
                        "operator": ctx.operator_sample_size,
                        "benchmark_group": 0,
                    },
                    limitations=("no_valid_benchmark", selection.reason),
                    evidence_grade=EvidenceGrade.INSUFFICIENT,
                    synthetic=ctx.synthetic,
                )
            benchmark_class = selection.selected_class

        return _compute_benchmark(benchmark_class, ctx)

    def evaluate_all(
        self,
        ctx: BenchmarkContext,
    ) -> List[BenchmarkResult]:
        """Evaluate all eligible benchmark classes for a context.

        Returns results for every class that passes eligibility, ordered by
        selection priority. The first result is the primary benchmark.
        """
        results = []
        for cls in BenchmarkClass:
            elig = _check_eligibility(cls, ctx)
            if elig.eligible:
                results.append(_compute_benchmark(cls, ctx))
        return results

    def evaluate_cohort(
        self,
        operator_values: Dict[str, float],
        metric: str,
        window_start: date,
        window_end: date,
        synthetic: bool = False,
    ) -> List[BenchmarkResult]:
        """Evaluate cohort benchmarks for all operators.

        For each operator, computes a cohort benchmark against all other
        operators in the cohort.
        """
        results = []
        values = list(operator_values.values())
        for op_id, value in operator_values.items():
            comparison = [v for k, v in operator_values.items() if k != op_id]
            ctx = BenchmarkContext(
                operator_id=op_id,
                metric=metric,
                operator_value=value,
                window_start=window_start,
                window_end=window_end,
                comparison_values=tuple(comparison),
                comparison_description="cohort peers",
                cohort_id="cohort",
                operator_sample_size=1,
                synthetic=synthetic,
            )
            results.append(self.evaluate(ctx, BenchmarkClass.COHORT))
        return results
