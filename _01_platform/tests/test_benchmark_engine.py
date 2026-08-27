"""Tests for the Benchmark Engine (Q8 gap closure).

Verifies:
  - All 13 benchmark classes are defined
  - Selection algorithm follows §7.14 priority order
  - Eligibility checks work per-class
  - Statistical method selection follows §7.15.5 decision table
  - Benchmark results include uncertainty (CI, sample size, limitations)
  - Evidence grades are assigned correctly
  - Cohort evaluation works for multiple operators
"""
from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestBenchmarkEngine(unittest.TestCase):
    """Tests for the Benchmark Engine."""

    # ── 13 benchmark classes ─────────────────────────────────────────────

    def test_thirteen_benchmark_classes(self):
        from benchmark import BenchmarkClass
        values = {c.value for c in BenchmarkClass}
        self.assertEqual(len(values), 13)
        expected = {
            "self_vs_prior", "repeated_task", "matched_task",
            "peer", "role", "cohort", "team", "organization",
            "system", "workflow", "model", "intervention", "external_field",
        }
        self.assertEqual(values, expected)

    # ── Selection algorithm (§7.14) ──────────────────────────────────────

    def test_selection_intervention_first(self):
        """Step 1: intervention evals select the intervention benchmark."""
        from benchmark import BenchmarkContext, BenchmarkClass, select_benchmark
        ctx = BenchmarkContext(
            operator_id="op_001",
            metric="leverage",
            operator_value=15.0,
            window_start=date(2026, 7, 1),
            window_end=date(2026, 7, 30),
            comparison_values=tuple([10.0] * 20),
            is_intervention=True,
            control_group_values=(10.0, 11.0, 12.0, 13.0, 14.0),
            treatment_group_values=(15.0, 16.0, 17.0, 18.0, 19.0),
            synthetic=True,
        )
        result = select_benchmark(ctx)
        self.assertEqual(result.selected_class, BenchmarkClass.INTERVENTION)

    def test_selection_self_vs_prior(self):
        """Step 4: prior window data selects self_vs_prior."""
        from benchmark import BenchmarkContext, BenchmarkClass, select_benchmark
        ctx = BenchmarkContext(
            operator_id="op_001",
            metric="leverage",
            operator_value=15.0,
            window_start=date(2026, 7, 1),
            window_end=date(2026, 7, 30),
            comparison_values=tuple([10.0] * 20),
            prior_window_values=(8.0, 9.0, 10.0, 11.0, 12.0),
            synthetic=True,
        )
        result = select_benchmark(ctx)
        self.assertEqual(result.selected_class, BenchmarkClass.SELF_VS_PRIOR)

    def test_selection_peer_when_no_prior(self):
        """Step 5: peer benchmark when ≥5 comparison values, no prior."""
        from benchmark import BenchmarkContext, BenchmarkClass, select_benchmark
        ctx = BenchmarkContext(
            operator_id="op_001",
            metric="leverage",
            operator_value=15.0,
            window_start=date(2026, 7, 1),
            window_end=date(2026, 7, 30),
            comparison_values=tuple([10.0, 11.0, 12.0, 13.0, 14.0]),
            synthetic=True,
        )
        result = select_benchmark(ctx)
        self.assertEqual(result.selected_class, BenchmarkClass.PEER)

    def test_selection_no_valid_benchmark(self):
        """Step 11: no valid benchmark when insufficient data."""
        from benchmark import BenchmarkContext, select_benchmark
        ctx = BenchmarkContext(
            operator_id="op_001",
            metric="leverage",
            operator_value=15.0,
            window_start=date(2026, 7, 1),
            window_end=date(2026, 7, 30),
            comparison_values=(),  # no comparison data
            synthetic=True,
        )
        result = select_benchmark(ctx)
        self.assertIsNone(result.selected_class)

    # ── Eligibility ──────────────────────────────────────────────────────

    def test_eligibility_cohort_min_10(self):
        """Cohort benchmark requires ≥10 operators."""
        from benchmark import BenchmarkContext, BenchmarkClass
        from benchmark.engine import _check_eligibility
        ctx = BenchmarkContext(
            operator_id="op_001",
            metric="leverage",
            operator_value=15.0,
            window_start=date(2026, 7, 1),
            window_end=date(2026, 7, 30),
            comparison_values=tuple([10.0] * 9),  # only 9, below min of 10
            synthetic=True,
        )
        elig = _check_eligibility(BenchmarkClass.COHORT, ctx)
        self.assertFalse(elig.eligible)

    def test_eligibility_cohort_passes_with_10(self):
        """Cohort benchmark passes with ≥10 operators."""
        from benchmark import BenchmarkContext, BenchmarkClass
        from benchmark.engine import _check_eligibility
        ctx = BenchmarkContext(
            operator_id="op_001",
            metric="leverage",
            operator_value=15.0,
            window_start=date(2026, 7, 1),
            window_end=date(2026, 7, 30),
            comparison_values=tuple([10.0] * 15),
            synthetic=True,
        )
        elig = _check_eligibility(BenchmarkClass.COHORT, ctx)
        self.assertTrue(elig.eligible)

    # ── Statistical method selection (§7.15.5) ───────────────────────────

    def test_method_selection_self_vs_prior_large(self):
        """Self vs prior with ≥10 obs uses paired bootstrap BCa."""
        from benchmark import BenchmarkClass, StatisticalMethod
        from benchmark.engine import _select_method
        method = _select_method(BenchmarkClass.SELF_VS_PRIOR, 15)
        self.assertEqual(method, StatisticalMethod.PAIRED_BOOTSTRAP_BCA)

    def test_method_selection_self_vs_prior_small(self):
        """Self vs prior with <10 obs uses Wilcoxon signed-rank."""
        from benchmark import BenchmarkClass, StatisticalMethod
        from benchmark.engine import _select_method
        method = _select_method(BenchmarkClass.SELF_VS_PRIOR, 5)
        self.assertEqual(method, StatisticalMethod.WILCOXON_SIGNED_RANK)

    def test_method_selection_peer_large(self):
        """Peer with ≥20 uses non-paired bootstrap BCa."""
        from benchmark import BenchmarkClass, StatisticalMethod
        from benchmark.engine import _select_method
        method = _select_method(BenchmarkClass.PEER, 25)
        self.assertEqual(method, StatisticalMethod.NON_PAIRED_BOOTSTRAP_BCA)

    def test_method_selection_peer_small(self):
        """Peer with <20 uses Bayesian Dirichlet."""
        from benchmark import BenchmarkClass, StatisticalMethod
        from benchmark.engine import _select_method
        method = _select_method(BenchmarkClass.PEER, 7)
        self.assertEqual(method, StatisticalMethod.BAYESIAN_DIRICHLET)

    def test_method_selection_intervention_large(self):
        """Intervention with ≥10 uses DiD."""
        from benchmark import BenchmarkClass, StatisticalMethod
        from benchmark.engine import _select_method
        method = _select_method(BenchmarkClass.INTERVENTION, 15)
        self.assertEqual(method, StatisticalMethod.DIFFERENCE_IN_DIFFERENCES)

    # ── Benchmark result includes uncertainty ────────────────────────────

    def test_result_includes_uncertainty(self):
        """Every benchmark result must include CI, sample size, and limitations."""
        from benchmark import BenchmarkEngine, BenchmarkContext, BenchmarkClass
        engine = BenchmarkEngine()
        ctx = BenchmarkContext(
            operator_id="op_001",
            metric="leverage",
            operator_value=17.75,
            window_start=date(2026, 7, 1),
            window_end=date(2026, 7, 30),
            comparison_values=tuple([12.0, 14.2, 10.5, 18.0, 15.3] * 4),
            comparison_description="cohort peers",
            synthetic=True,
        )
        result = engine.evaluate(ctx, BenchmarkClass.COHORT)
        self.assertTrue(result.eligibility.eligible)
        # Must have percentile rank
        self.assertIn("percentile_rank", result.result)
        # Must have CI
        self.assertIn("percentile_ci_95", result.result)
        # Must have delta CI
        self.assertIn("delta_ci_95", result.result)
        # Must have sample size
        self.assertIn("operator", result.sample_size)
        self.assertIn("benchmark_group", result.sample_size)
        # Must have limitations
        self.assertGreater(len(result.limitations), 0)
        # Must have evidence grade
        self.assertIsNotNone(result.evidence_grade)

    def test_result_to_dict_serializable(self):
        """BenchmarkResult.to_dict() produces a JSON-serializable dict."""
        import json
        from benchmark import BenchmarkEngine, BenchmarkContext, BenchmarkClass
        engine = BenchmarkEngine()
        ctx = BenchmarkContext(
            operator_id="op_001",
            metric="leverage",
            operator_value=15.0,
            window_start=date(2026, 7, 1),
            window_end=date(2026, 7, 30),
            comparison_values=tuple([10.0] * 15),
            synthetic=True,
        )
        result = engine.evaluate(ctx, BenchmarkClass.COHORT)
        d = result.to_dict()
        # Should be JSON-serializable
        json_str = json.dumps(d, default=str)
        self.assertIsInstance(json_str, str)

    # ── Evidence grades ──────────────────────────────────────────────────

    def test_evidence_grade_intervention(self):
        """Intervention benchmark gets controlled_experiment grade."""
        from benchmark import BenchmarkEngine, BenchmarkContext, BenchmarkClass, EvidenceGrade
        engine = BenchmarkEngine()
        ctx = BenchmarkContext(
            operator_id="op_001",
            metric="leverage",
            operator_value=15.0,
            window_start=date(2026, 7, 1),
            window_end=date(2026, 7, 30),
            comparison_values=tuple([10.0] * 10),
            is_intervention=True,
            control_group_values=tuple([10.0] * 5),
            treatment_group_values=tuple([15.0] * 5),
            synthetic=True,
        )
        result = engine.evaluate(ctx, BenchmarkClass.INTERVENTION)
        self.assertEqual(result.evidence_grade, EvidenceGrade.CONTROLLED_EXPERIMENT)

    # ── Cohort evaluation ────────────────────────────────────────────────

    def test_evaluate_cohort(self):
        """evaluate_cohort produces one result per operator."""
        from benchmark import BenchmarkEngine
        engine = BenchmarkEngine()
        operator_values = {
            f"op_{i:03d}": 10.0 + i * 0.5 for i in range(20)
        }
        results = engine.evaluate_cohort(
            operator_values,
            metric="leverage",
            window_start=date(2026, 7, 1),
            window_end=date(2026, 7, 30),
            synthetic=True,
        )
        self.assertEqual(len(results), 20)
        # Each result should be a cohort benchmark
        for r in results:
            self.assertEqual(r.benchmark_class.value, "cohort")

    # ── No false leaderboards ────────────────────────────────────────────

    def test_no_false_leaderboards(self):
        """Benchmarks never present a simple ranked list without uncertainty.

        Every result must include CI and sample size — never just a rank.
        """
        from benchmark import BenchmarkEngine, BenchmarkContext, BenchmarkClass
        engine = BenchmarkEngine()
        ctx = BenchmarkContext(
            operator_id="op_001",
            metric="leverage",
            operator_value=20.0,
            window_start=date(2026, 7, 1),
            window_end=date(2026, 7, 30),
            comparison_values=tuple([10.0 + i for i in range(20)]),
            synthetic=True,
        )
        result = engine.evaluate(ctx, BenchmarkClass.COHORT)
        # Must have percentile rank AND CI
        self.assertIn("percentile_rank", result.result)
        self.assertIn("percentile_ci_95", result.result)
        # CI must be a list of two values
        ci = result.result["percentile_ci_95"]
        self.assertEqual(len(ci), 2)
        self.assertLessEqual(ci[0], ci[1])


if __name__ == "__main__":
    unittest.main()
