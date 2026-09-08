"""Tests for per-worker budgets (HRN-010 orchestration).

Verifies:
    - Step budget is enforced
    - Time budget is enforced
    - Cost budget is enforced
    - Exhausted workers are flagged
    - Remaining budget is computed correctly
    - Siblings are not affected by a worker exhaustion (bulkheading)
"""
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from workflow import (
    WorkerBudget,
    BudgetTracker,
    BudgetExceededError,
    BudgetDimension,
)


class TestWorkerBudget(unittest.TestCase):

    def test_step_budget_enforced(self):
        """Step budget raises when exceeded."""
        tracker = BudgetTracker()
        tracker.set_budget(WorkerBudget(
            worker_id="intervention_a",
            max_steps=3,
        ))
        tracker.start("intervention_a")
        tracker.record_step("intervention_a")
        tracker.record_step("intervention_a")
        tracker.record_step("intervention_a")
        with self.assertRaises(BudgetExceededError) as ctx:
            tracker.record_step("intervention_a")
        self.assertEqual(ctx.exception.dimension, BudgetDimension.STEPS)
        self.assertEqual(ctx.exception.used, 4)
        self.assertEqual(ctx.exception.cap, 3)

    def test_cost_budget_enforced(self):
        """Cost budget raises when exceeded."""
        tracker = BudgetTracker()
        tracker.set_budget(WorkerBudget(
            worker_id="intervention_b",
            max_cost=10.0,
        ))
        tracker.start("intervention_b")
        tracker.record_step("intervention_b", cost=3.0)
        tracker.record_step("intervention_b", cost=4.0)
        with self.assertRaises(BudgetExceededError) as ctx:
            tracker.record_step("intervention_b", cost=5.0)
        self.assertEqual(ctx.exception.dimension, BudgetDimension.COST)

    def test_time_budget_enforced(self):
        """Time budget raises when exceeded."""
        tracker = BudgetTracker()
        tracker.set_budget(WorkerBudget(
            worker_id="intervention_c",
            max_time_seconds=0.05,  # 50ms
        ))
        tracker.start("intervention_c")
        time.sleep(0.06)
        with self.assertRaises(BudgetExceededError) as ctx:
            tracker.record_step("intervention_c")
        self.assertEqual(ctx.exception.dimension, BudgetDimension.TIME)

    def test_no_budget_unlimited(self):
        """No budget set means unlimited (no error)."""
        tracker = BudgetTracker()
        tracker.start("worker_x")
        for _ in range(100):
            tracker.record_step("worker_x", cost=1.0)
        # Should not raise
        self.assertFalse(tracker.is_exhausted("worker_x"))

    def test_exhausted_flag(self):
        """is_exhausted returns True after a budget breach."""
        tracker = BudgetTracker()
        tracker.set_budget(WorkerBudget(
            worker_id="w",
            max_steps=1,
        ))
        tracker.start("w")
        tracker.record_step("w")
        self.assertFalse(tracker.is_exhausted("w"))
        with self.assertRaises(BudgetExceededError):
            tracker.record_step("w")
        self.assertTrue(tracker.is_exhausted("w"))

    def test_bulkheading_siblings_unaffected(self):
        """One worker's exhaustion does not affect siblings."""
        tracker = BudgetTracker()
        tracker.set_budget(WorkerBudget(worker_id="w1", max_steps=2))
        tracker.set_budget(WorkerBudget(worker_id="w2", max_steps=100))
        tracker.start("w1")
        tracker.start("w2")
        tracker.record_step("w1")
        tracker.record_step("w1")
        with self.assertRaises(BudgetExceededError):
            tracker.record_step("w1")
        # w2 should be unaffected
        tracker.record_step("w2")
        tracker.record_step("w2")
        self.assertFalse(tracker.is_exhausted("w2"))

    def test_remaining_budget(self):
        """remaining() returns correct remaining for each dimension."""
        tracker = BudgetTracker()
        tracker.set_budget(WorkerBudget(
            worker_id="w",
            max_steps=10,
            max_cost=100.0,
        ))
        tracker.start("w")
        tracker.record_step("w", cost=30.0)
        tracker.record_step("w", cost=20.0)
        remaining = tracker.remaining("w")
        self.assertEqual(remaining["steps"], 8)
        self.assertEqual(remaining["cost"], 50.0)
        self.assertIsNone(remaining["time"])

    def test_usage_tracking(self):
        """Usage is tracked correctly."""
        tracker = BudgetTracker()
        tracker.set_budget(WorkerBudget(worker_id="w", max_steps=5))
        tracker.start("w")
        tracker.record_step("w", cost=1.5)
        tracker.record_step("w", cost=2.5)
        usage = tracker.get_usage("w")
        self.assertEqual(usage.steps_used, 2)
        self.assertEqual(usage.cost_accumulated, 4.0)
        self.assertFalse(usage.exhausted)

    def test_all_usage(self):
        """all_usage returns usage for all workers."""
        tracker = BudgetTracker()
        tracker.set_budget(WorkerBudget(worker_id="w1", max_steps=5))
        tracker.set_budget(WorkerBudget(worker_id="w2", max_steps=5))
        tracker.start("w1")
        tracker.start("w2")
        tracker.record_step("w1")
        tracker.record_step("w2")
        all_usage = tracker.all_usage()
        self.assertEqual(len(all_usage), 2)
        self.assertEqual(all_usage["w1"].steps_used, 1)
        self.assertEqual(all_usage["w2"].steps_used, 1)


if __name__ == "__main__":
    unittest.main()
