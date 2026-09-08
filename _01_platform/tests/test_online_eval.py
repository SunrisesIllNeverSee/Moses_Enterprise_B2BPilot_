"""Tests for online evaluation — shadow judges on live traces (HRN-009).

Verifies:
    - Shadow judge runs alongside primary without blocking
    - Shadow judge failure is non-blocking
    - Drift is detected when scores diverge
    - Operational signals are captured
    - Report aggregates traces and signals correctly
    - Export for offline evaluation works
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from governance import (
    SignalType,
    OnlineEvaluator,
    OnlineEvalReport,
)


class TestOnlineEvaluator(unittest.TestCase):

    def test_shadow_judge_runs_alongside_primary(self):
        """Shadow judge score is recorded alongside primary."""
        evaluator = OnlineEvaluator(
            shadow_judge=lambda item: 0.8,
        )
        trace = evaluator.evaluate(
            item={"id": "item_1"},
            primary_score=0.7,
            item_id="item_1",
        )
        self.assertEqual(trace.primary_score, 0.7)
        self.assertEqual(trace.shadow_score, 0.8)

    def test_shadow_judge_failure_is_non_blocking(self):
        """Shadow judge failure does not block primary evaluation."""
        def failing_judge(item):
            raise RuntimeError("judge crashed")

        evaluator = OnlineEvaluator(shadow_judge=failing_judge)
        trace = evaluator.evaluate(
            item={"id": "item_1"},
            primary_score=0.7,
            item_id="item_1",
        )
        self.assertEqual(trace.primary_score, 0.7)
        self.assertIsNone(trace.shadow_score)  # shadow failed → None

    def test_no_shadow_judge(self):
        """Without a shadow judge, shadow_score is None."""
        evaluator = OnlineEvaluator(shadow_judge=None)
        trace = evaluator.evaluate(
            item={"id": "item_1"},
            primary_score=0.7,
            item_id="item_1",
        )
        self.assertEqual(trace.primary_score, 0.7)
        self.assertIsNone(trace.shadow_score)

    def test_drift_detection(self):
        """Drift is detected when |shadow - primary| > threshold."""
        evaluator = OnlineEvaluator(
            shadow_judge=lambda item: 0.9,
            drift_threshold=0.1,
        )
        evaluator.evaluate(item={"id": "1"}, primary_score=0.5, item_id="1")
        report = evaluator.report()
        self.assertEqual(len(report.drift_traces), 1)
        self.assertIn("drift_detected", report.signal_counts)

    def test_no_drift_when_scores_close(self):
        """No drift when scores are within threshold."""
        evaluator = OnlineEvaluator(
            shadow_judge=lambda item: 0.55,
            drift_threshold=0.1,
        )
        evaluator.evaluate(item={"id": "1"}, primary_score=0.5, item_id="1")
        report = evaluator.report()
        self.assertEqual(len(report.drift_traces), 0)

    def test_operational_signals_captured(self):
        """Operational signals are captured and counted."""
        evaluator = OnlineEvaluator()
        trace = evaluator.evaluate(item={"id": "1"}, primary_score=0.5, item_id="1")
        evaluator.record_signal(
            trace_id=trace.trace_id,
            signal_type=SignalType.USER_FEEDBACK,
            value=1.0,
            detail="user approved",
        )
        evaluator.record_signal(
            trace_id=trace.trace_id,
            signal_type=SignalType.ESCALATION,
            detail="escalated to human",
        )
        report = evaluator.report()
        self.assertEqual(report.signal_counts.get("user_feedback"), 1)
        self.assertEqual(report.signal_counts.get("escalation"), 1)

    def test_report_aggregates_traces(self):
        """Report aggregates trace count and coverage."""
        evaluator = OnlineEvaluator(shadow_judge=lambda item: 0.5)
        for i in range(10):
            evaluator.evaluate(item={"id": str(i)}, primary_score=0.5, item_id=str(i))
        report = evaluator.report()
        self.assertEqual(report.trace_count, 10)
        self.assertEqual(report.shadow_judge_coverage, 1.0)

    def test_mean_score_delta(self):
        """Mean score delta is computed correctly."""
        evaluator = OnlineEvaluator(shadow_judge=lambda item: 0.7)
        evaluator.evaluate(item={"id": "1"}, primary_score=0.5, item_id="1")
        evaluator.evaluate(item={"id": "2"}, primary_score=0.5, item_id="2")
        report = evaluator.report()
        self.assertAlmostEqual(report.mean_score_delta, 0.2, places=2)

    def test_export_for_offline(self):
        """Export produces traces, signals, and report for offline eval."""
        evaluator = OnlineEvaluator(shadow_judge=lambda item: 0.8)
        trace = evaluator.evaluate(item={"id": "1"}, primary_score=0.7, item_id="1")
        evaluator.record_signal(
            trace_id=trace.trace_id,
            signal_type=SignalType.FAILURE,
            detail="test failure",
        )
        exported = evaluator.export_for_offline()
        self.assertIn("traces", exported)
        self.assertIn("signals", exported)
        self.assertIn("report", exported)
        self.assertEqual(len(exported["traces"]), 1)
        self.assertEqual(len(exported["signals"]), 1)

    def test_empty_report(self):
        """Empty evaluator produces empty report."""
        evaluator = OnlineEvaluator()
        report = evaluator.report()
        self.assertEqual(report.trace_count, 0)
        self.assertEqual(report.shadow_judge_coverage, 0.0)

    def test_traces_and_signals_accessible(self):
        """Traces and signals are accessible as properties."""
        evaluator = OnlineEvaluator(shadow_judge=lambda item: 0.5)
        evaluator.evaluate(item={"id": "1"}, primary_score=0.5, item_id="1")
        evaluator.record_signal(
            trace_id="trace_000001",
            signal_type=SignalType.USER_FEEDBACK,
        )
        self.assertEqual(len(evaluator.traces), 1)
        self.assertEqual(len(evaluator.signals), 1)


if __name__ == "__main__":
    unittest.main()
