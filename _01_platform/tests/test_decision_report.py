"""Tests for the decision-oriented reporting layer (Gap 8).

Verifies:
  - build_decision_report translates metrics to decision vocabulary
  - Per-operator report uses decision names ("output efficiency" not "yield")
  - Low-percentile Yield → "context structuring coaching" recommendation
  - Low Leverage → "context caching workshop" recommendation
  - HIGH_USAGE_LOW_OPERATION divergence → "workflow review" recommendation
  - All recommendations are developmental (coaching, workshops, reviews)
  - No punitive labels appear anywhere in the output
  - Outcome claims are ASSOCIATION, never CAUSATION
  - Cohort report aggregates without ranking individual operators
  - Markdown export uses decision vocabulary
  - Governance labels are present
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# Punitive / personnel-action terms that must NEVER appear in the
# actionable findings or recommendations of a decision report.
# (Governance disclaimers that *disavow* these terms are fine — we
# check the findings/recommendations content, not the disclaimer text.)
_FORBIDDEN_TERMS = [
    "pip", "performance improvement plan", "termination", "terminate",
    "demotion", "demote", "fire", "fired", "layoff",
    "disciplinary", "reprimand", "sanction", "penalty", "penalize",
    "underperformer", "underperforming", "worst", "bottom performer",
]


def _actionable_text(report: dict) -> str:
    """Extract only the actionable findings + recommendations from a report.

    Excludes governance notes and labels (which may legitimately
    *disavow* punitive terms, e.g. 'no punitive labels').
    """
    parts: list[str] = []
    for f in report.get("metric_findings", []):
        parts.append(f.get("finding", ""))
        parts.append(f.get("recommended_action", ""))
        parts.append(f.get("action_detail", ""))
    df = report.get("divergence_finding")
    if df:
        parts.append(df.get("finding", ""))
        parts.append(df.get("recommended_action", ""))
        parts.append(df.get("action_detail", ""))
    for d in report.get("divergence_findings", []):
        parts.append(d.get("finding", ""))
        parts.append(d.get("recommended_action", ""))
        parts.append(d.get("action_detail", ""))
    for ta in report.get("top_developmental_actions", []):
        parts.append(ta.get("recommended_action", ""))
    return " ".join(parts).lower()


class TestOperatorDecisionReport(unittest.TestCase):
    """Tests for the per-operator decision report."""

    def setUp(self):
        from service import PilotService
        self.svc = PilotService()
        self.oid = self.svc.operator_ids[0]

    def test_report_structure(self):
        from reporting import build_operator_decision_report
        report = build_operator_decision_report(self.svc, self.oid)
        self.assertEqual(report["report_type"], "decision_report")
        self.assertEqual(report["operator_id"], self.oid)
        self.assertIn("metric_findings", report)
        self.assertIn("label", report)
        self.assertIn("governance_note", report)
        self.assertGreater(len(report["metric_findings"]), 0)

    def test_uses_decision_names_not_metric_ids(self):
        """Yield → 'output efficiency', Leverage → 'context reuse'."""
        from reporting import build_operator_decision_report
        report = build_operator_decision_report(self.svc, self.oid)
        decision_names = {f["decision_name"] for f in report["metric_findings"]}
        self.assertIn("output efficiency", decision_names)
        self.assertIn("context reuse", decision_names)

    def test_each_finding_has_recommended_action(self):
        from reporting import build_operator_decision_report
        report = build_operator_decision_report(self.svc, self.oid)
        for f in report["metric_findings"]:
            self.assertIn("recommended_action", f)
            self.assertTrue(f["recommended_action"],
                            "recommended_action must not be empty")
            self.assertIn("action_detail", f)

    def test_low_yield_recommends_context_structuring_coaching(self):
        """Per Jaimie's review: low Yield → 'context structuring coaching'."""
        from reporting import build_operator_decision_report
        # Find an operator with a low yield percentile, or construct the
        # finding directly to verify the mapping.
        from reporting.decision_report import _metric_finding
        finding = _metric_finding("yield", 0.15, 10.0)
        self.assertIn("bottom 10%", finding["finding"])
        self.assertEqual(finding["recommended_action"], "context structuring coaching")

    def test_low_leverage_recommends_context_caching_workshop(self):
        """Per Jaimie's review: low Leverage → 'context caching workshop'."""
        from reporting.decision_report import _metric_finding
        finding = _metric_finding("leverage", 0.05, 15.0)
        self.assertIn("context reuse", finding["finding"].lower())
        self.assertEqual(finding["recommended_action"], "context caching workshop")

    def test_high_usage_low_operation_divergence_recommends_workflow_review(self):
        """Per Jaimie's review: high usage, low performance → 'workflow review'."""
        from reporting.decision_report import _divergence_finding
        finding = _divergence_finding("HIGH_USAGE_LOW_OPERATION")
        self.assertIn("workflow review", finding["recommended_action"])
        self.assertIn("loop", finding["finding"].lower())

    def test_no_punitive_labels(self):
        from reporting import build_operator_decision_report
        report = build_operator_decision_report(self.svc, self.oid)
        text = _actionable_text(report)
        for term in _FORBIDDEN_TERMS:
            self.assertNotIn(term, text,
                             f"Forbidden punitive term '{term}' found in decision report")

    def test_claim_type_is_association(self):
        from reporting import build_operator_decision_report
        report = build_operator_decision_report(self.svc, self.oid)
        for f in report["metric_findings"]:
            self.assertEqual(f["claim_type"], "ASSOCIATION")
        self.assertEqual(report["claim_type"], "ASSOCIATION")

    def test_label_is_developmental(self):
        from reporting import build_operator_decision_report
        report = build_operator_decision_report(self.svc, self.oid)
        self.assertIn("DEVELOPMENTAL", report["label"])

    def test_unknown_operator_returns_error(self):
        from reporting import build_operator_decision_report
        report = build_operator_decision_report(self.svc, "nonexistent_op")
        self.assertIn("error", report)

    def test_via_service_decision_report(self):
        report = self.svc.decision_report(self.oid)
        self.assertEqual(report["report_type"], "decision_report")
        self.assertGreater(len(report["metric_findings"]), 0)


class TestCohortDecisionReport(unittest.TestCase):
    """Tests for the cohort-level decision report."""

    def setUp(self):
        from service import PilotService
        self.svc = PilotService()

    def test_report_structure(self):
        from reporting import build_cohort_decision_report
        report = build_cohort_decision_report(self.svc)
        self.assertEqual(report["report_type"], "cohort_decision_report")
        self.assertIn("divergence_findings", report)
        self.assertIn("metric_band_counts", report)
        self.assertIn("top_developmental_actions", report)
        self.assertIn("label", report)

    def test_no_individual_ranking(self):
        """Cohort report must not rank individual operators."""
        from reporting import build_cohort_decision_report
        report = build_cohort_decision_report(self.svc)
        text = _actionable_text(report)
        # Should not contain per-operator rankings in the actionable content
        self.assertNotIn("leaderboard", text)
        self.assertNotIn("ranked", text)

    def test_top_actions_are_developmental(self):
        from reporting import build_cohort_decision_report
        report = build_cohort_decision_report(self.svc)
        for ta in report["top_developmental_actions"]:
            action = ta["recommended_action"].lower()
            # Must be a developmental action, not a personnel action
            self.assertNotIn("fire", action)
            self.assertNotIn("terminate", action)
            self.assertNotIn("demote", action)

    def test_no_punitive_labels(self):
        from reporting import build_cohort_decision_report
        report = build_cohort_decision_report(self.svc)
        text = _actionable_text(report)
        for term in _FORBIDDEN_TERMS:
            self.assertNotIn(term, text,
                             f"Forbidden punitive term '{term}' found in cohort report")

    def test_via_service_decision_report(self):
        report = self.svc.decision_report()
        self.assertEqual(report["report_type"], "cohort_decision_report")


class TestDecisionReportMarkdown(unittest.TestCase):
    """Tests for the Markdown export of the decision report."""

    def setUp(self):
        from service import PilotService
        self.svc = PilotService()
        self.oid = self.svc.operator_ids[0]

    def test_operator_markdown_uses_decision_vocabulary(self):
        from reporting import export_decision_report_markdown
        md = export_decision_report_markdown(self.svc, operator_id=self.oid)
        self.assertIn("Decision Report", md)
        self.assertIn("output efficiency", md.lower())
        self.assertIn("Recommended action", md)
        self.assertIn("DEVELOPMENTAL", md)

    def test_cohort_markdown(self):
        from reporting import export_decision_report_markdown
        md = export_decision_report_markdown(self.svc)
        self.assertIn("Decision Report", md)
        self.assertIn("Top Developmental Actions", md)

    def test_markdown_no_punitive_labels(self):
        from reporting import export_decision_report_markdown
        md = export_decision_report_markdown(self.svc, operator_id=self.oid)
        # Strip the governance disclaimer footer (which legitimately
        # *disavows* punitive terms) before checking.
        body = md.split("---")[0]
        for term in _FORBIDDEN_TERMS:
            self.assertNotIn(term, body.lower(),
                             f"Forbidden punitive term '{term}' in markdown body")

    def test_markdown_contains_association_disclaimer(self):
        from reporting import export_decision_report_markdown
        md = export_decision_report_markdown(self.svc, operator_id=self.oid)
        self.assertIn("ASSOCIATION", md)
        self.assertIn("never CAUSATION", md)


if __name__ == "__main__":
    unittest.main()
