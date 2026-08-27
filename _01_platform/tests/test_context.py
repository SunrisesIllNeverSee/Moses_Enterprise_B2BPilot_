"""Tests for the TaskContext domain module (Gap 4 — task difficulty context).

Verifies:
  - TaskContext dataclass creation and field validation
  - difficulty_weight blends complexity, task-type prior, and label
  - from_task_type convenience constructor derives complexity + difficulty
  - adjust_metric_for_context normalizes to a common difficulty scale
  - A high-complexity task yields a higher adjusted value than a
    low-complexity task for the same raw value (the core Gap 4 thesis)
  - Adjustment is bounded (never exceeds 2x or goes below 0.5x)
  - context_adjustment tags measurements with their task context
  - to_dict / from_dict round-trips
  - Governance: no punitive labels; adjustment is developmental
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestTaskContext(unittest.TestCase):
    """Tests for the TaskContext dataclass."""

    def test_creation_with_all_fields(self):
        from domain import TaskContext
        ctx = TaskContext(
            task_complexity=0.7,
            task_type="debugging",
            workflow_stage="implementation",
            estimated_difficulty="high",
            context_tokens_required=8000,
        )
        self.assertEqual(ctx.task_complexity, 0.7)
        self.assertEqual(ctx.task_type, "debugging")
        self.assertEqual(ctx.workflow_stage, "implementation")
        self.assertEqual(ctx.estimated_difficulty, "high")
        self.assertEqual(ctx.context_tokens_required, 8000)
        self.assertFalse(ctx.synthetic)

    def test_complexity_out_of_range_raises(self):
        from domain import TaskContext
        with self.assertRaises(ValueError):
            TaskContext(task_complexity=1.5, task_type="coding")
        with self.assertRaises(ValueError):
            TaskContext(task_complexity=-0.1, task_type="coding")

    def test_invalid_difficulty_label_raises(self):
        from domain import TaskContext
        with self.assertRaises(ValueError):
            TaskContext(task_complexity=0.5, task_type="coding", estimated_difficulty="extreme")

    def test_frozen_dataclass(self):
        from domain import TaskContext
        ctx = TaskContext(task_complexity=0.5, task_type="coding")
        params = getattr(TaskContext, "__dataclass_params__", None)
        self.assertIsNotNone(params)
        self.assertTrue(params.frozen, "TaskContext must be frozen")
        with self.assertRaises((AttributeError, Exception)):
            ctx.task_complexity = 0.9  # type: ignore[misc]

    def test_difficulty_weight_in_valid_range(self):
        from domain import TaskContext
        for complexity in (0.0, 0.2, 0.5, 0.8, 1.0):
            ctx = TaskContext(task_complexity=complexity, task_type="coding")
            w = ctx.difficulty_weight
            self.assertGreaterEqual(w, 0.0)
            self.assertLessEqual(w, 1.0)

    def test_higher_complexity_yields_higher_weight(self):
        from domain import TaskContext
        low = TaskContext(task_complexity=0.1, task_type="writing", estimated_difficulty="low")
        high = TaskContext(task_complexity=0.9, task_type="debugging", estimated_difficulty="high")
        self.assertGreater(high.difficulty_weight, low.difficulty_weight)

    def test_from_task_type_derives_complexity_and_difficulty(self):
        from domain import TaskContext
        ctx = TaskContext.from_task_type("debugging", workflow_stage="testing")
        self.assertEqual(ctx.task_type, "debugging")
        self.assertEqual(ctx.workflow_stage, "testing")
        # debugging has a high prior (0.75) → estimated_difficulty should be "high"
        self.assertEqual(ctx.estimated_difficulty, "high")
        self.assertGreater(ctx.task_complexity, 0.6)

    def test_from_task_type_writing_is_low(self):
        from domain import TaskContext
        ctx = TaskContext.from_task_type("writing")
        self.assertEqual(ctx.estimated_difficulty, "low")
        self.assertLess(ctx.task_complexity, 0.4)

    def test_to_dict_round_trip(self):
        from domain import TaskContext
        ctx = TaskContext(
            task_complexity=0.6,
            task_type="analysis",
            workflow_stage="discovery",
            estimated_difficulty="medium",
            context_tokens_required=4000,
            synthetic=True,
        )
        d = ctx.to_dict()
        restored = TaskContext.from_dict(d)
        self.assertEqual(restored.task_complexity, ctx.task_complexity)
        self.assertEqual(restored.task_type, ctx.task_type)
        self.assertEqual(restored.workflow_stage, ctx.workflow_stage)
        self.assertEqual(restored.estimated_difficulty, ctx.estimated_difficulty)
        self.assertEqual(restored.context_tokens_required, ctx.context_tokens_required)
        self.assertEqual(restored.synthetic, ctx.synthetic)

    def test_to_dict_includes_difficulty_weight(self):
        from domain import TaskContext
        ctx = TaskContext(task_complexity=0.5, task_type="coding")
        d = ctx.to_dict()
        self.assertIn("difficulty_weight", d)
        self.assertEqual(d["difficulty_weight"], ctx.difficulty_weight)


class TestAdjustMetricForContext(unittest.TestCase):
    """Tests for the context adjustment function — the core Gap 4 thesis."""

    def test_none_value_returns_none(self):
        from domain import TaskContext, adjust_metric_for_context
        ctx = TaskContext(task_complexity=0.8, task_type="debugging", estimated_difficulty="high")
        self.assertIsNone(adjust_metric_for_context(None, ctx))

    def test_high_complexity_raises_adjusted_value(self):
        """A Yield of 0.20 on a high-complexity task > 0.20 on a low-complexity task."""
        from domain import TaskContext, adjust_metric_for_context
        high_ctx = TaskContext(task_complexity=0.9, task_type="debugging", estimated_difficulty="high")
        low_ctx = TaskContext(task_complexity=0.1, task_type="writing", estimated_difficulty="low")
        raw = 0.20
        high_adj = adjust_metric_for_context(raw, high_ctx)
        low_adj = adjust_metric_for_context(raw, low_ctx)
        self.assertIsNotNone(high_adj)
        self.assertIsNotNone(low_adj)
        self.assertGreater(high_adj, low_adj,
                           "High-complexity task should yield higher adjusted value")

    def test_baseline_difficulty_neutral(self):
        """When task difficulty equals baseline, adjustment ratio is ~1.0."""
        from domain import TaskContext, adjust_metric_for_context
        # Build a context whose difficulty_weight equals the baseline.
        ctx = TaskContext(task_complexity=0.5, task_type="analysis", estimated_difficulty="medium")
        # Use the actual weight as the baseline so ratio == 1.0.
        baseline = ctx.difficulty_weight
        raw = 0.30
        adj = adjust_metric_for_context(raw, ctx, baseline_difficulty=baseline)
        self.assertAlmostEqual(adj, raw, places=5)

    def test_adjustment_bounded_above(self):
        """Adjustment never exceeds 2x the raw value."""
        from domain import TaskContext, adjust_metric_for_context
        ctx = TaskContext(task_complexity=1.0, task_type="debugging", estimated_difficulty="high")
        raw = 0.10
        adj = adjust_metric_for_context(raw, ctx, baseline_difficulty=0.2)
        self.assertLessEqual(adj, raw * 2.0)

    def test_adjustment_bounded_below(self):
        """Adjustment never goes below 0.5x the raw value."""
        from domain import TaskContext, adjust_metric_for_context
        ctx = TaskContext(task_complexity=0.0, task_type="writing", estimated_difficulty="low")
        raw = 0.50
        adj = adjust_metric_for_context(raw, ctx, baseline_difficulty=0.9)
        self.assertGreaterEqual(adj, raw * 0.5)

    def test_no_punitive_direction(self):
        """The adjustment is a normalization, not a penalty — it should not
        drive a high-complexity operator's value to zero."""
        from domain import TaskContext, adjust_metric_for_context
        ctx = TaskContext(task_complexity=1.0, task_type="debugging", estimated_difficulty="high")
        raw = 0.20
        adj = adjust_metric_for_context(raw, ctx)
        self.assertGreater(adj, 0,
                           "High-complexity adjustment should raise, not penalize")


class TestContextAdjustmentPipeline(unittest.TestCase):
    """Tests for the context_adjustment pipeline tagging function."""

    def test_tags_measurements_with_context(self):
        from domain import TaskContext, context_adjustment
        from domain.measurement import Measurement, MetricStatus
        from datetime import date
        ctx = TaskContext(task_complexity=0.7, task_type="coding", estimated_difficulty="high")
        ms = [
            Measurement(
                metric_id="yield", metric_version="1.0", operator_id="op_001",
                value=0.20, unit="ratio", window_start=date(2026, 1, 1),
                window_end=date(2026, 1, 31), source="test", status=MetricStatus.CANONICAL,
                eligibility="I>0",
            ),
            Measurement(
                metric_id="leverage", metric_version="1.0", operator_id="op_001",
                value=5.0, unit="ratio", window_start=date(2026, 1, 1),
                window_end=date(2026, 1, 31), source="test", status=MetricStatus.CANONICAL,
                eligibility="I>0",
            ),
        ]
        adjusted = context_adjustment(ms, ctx)
        self.assertEqual(len(adjusted), 2)
        for a in adjusted:
            self.assertIn("context_adjusted_value", a)
            self.assertIn("task_context", a)
            self.assertEqual(a["task_context"]["task_type"], "coding")
            self.assertIn("baseline_difficulty", a)

    def test_none_value_propagates(self):
        from domain import TaskContext, context_adjustment
        from domain.measurement import Measurement, MetricStatus
        from datetime import date
        ctx = TaskContext(task_complexity=0.5, task_type="coding")
        ms = [
            Measurement(
                metric_id="yield", metric_version="1.0", operator_id="op_001",
                value=None, unit="ratio", window_start=date(2026, 1, 1),
                window_end=date(2026, 1, 31), source="test",
                status=MetricStatus.CANONICAL, eligibility="FAILED: I>0",
            ),
        ]
        adjusted = context_adjustment(ms, ctx)
        self.assertIsNone(adjusted[0]["context_adjusted_value"])
        self.assertIsNotNone(adjusted[0]["task_context"])


class TestServiceContextAdjustment(unittest.TestCase):
    """Tests for the PilotService.context_adjustment method."""

    def test_service_context_adjustment(self):
        from service import PilotService
        from domain import TaskContext
        svc = PilotService()
        oid = svc.operator_ids[0]
        ctx = TaskContext.from_task_type("debugging", workflow_stage="implementation")
        result = svc.context_adjustment(oid, ctx)
        self.assertEqual(result["operator_id"], oid)
        self.assertIn("task_context", result)
        self.assertIn("adjusted_metrics", result)
        self.assertIn("label", result)
        self.assertGreater(len(result["adjusted_metrics"]), 0)
        # Governance label is developmental
        self.assertIn("DEVELOPMENTAL", result["label"])

    def test_service_score_operator_with_context(self):
        from service import PilotService
        from domain import TaskContext
        svc = PilotService()
        oid = svc.operator_ids[0]
        ctx = TaskContext.from_task_type("coding")
        tagged = svc.score_operator_with_context(oid, ctx)
        self.assertGreater(len(tagged), 0)
        for t in tagged:
            self.assertIn("context_adjusted_value", t)
            self.assertIn("task_context", t)

    def test_high_vs_low_complexity_adjustment_via_service(self):
        """End-to-end: same operator, high vs low complexity → different adjusted values."""
        from service import PilotService
        from domain import TaskContext
        svc = PilotService()
        oid = svc.operator_ids[0]
        high_ctx = TaskContext(task_complexity=0.95, task_type="debugging", estimated_difficulty="high")
        low_ctx = TaskContext(task_complexity=0.05, task_type="writing", estimated_difficulty="low")
        high_result = svc.context_adjustment(oid, high_ctx)
        low_result = svc.context_adjustment(oid, low_ctx)
        # Find the yield metric in both
        high_yield = next(m for m in high_result["adjusted_metrics"] if m["metric_id"] == "yield")
        low_yield = next(m for m in low_result["adjusted_metrics"] if m["metric_id"] == "yield")
        if high_yield["value"] is not None and low_yield["value"] is not None:
            self.assertGreaterEqual(
                high_yield["context_adjusted_value"],
                low_yield["context_adjusted_value"],
                "High-complexity adjusted yield should be >= low-complexity adjusted yield",
            )


if __name__ == "__main__":
    unittest.main()
