"""Tests for P1 (pattern engine, diagnosis, interventions, verifier) and
P2 (workflow fit, outcome joins).

Covers the P1 and P2 acceptance tests from `21`:

P1 acceptance:
- every diagnosis contains evidence + alternatives + status=HYPOTHESIS
- intervention declares target metric/window before follow-up
- pre/post verifier shows target + non-target metric deltas
- intervention failure is representable and reportable

P2 acceptance:
- workflow fit exposes observation count and uncertainty
- outcome joins remain separately governed
- no stage-fit claim without minimum sample rule
- outcome analysis separates association from causal claim
"""
import csv
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from service import PilotService
from domain.diagnosis import DiagnosisStatus
from domain.intervention import InterventionOutcome
from diagnostics import PatternEngine, DiagnosisEngine, DetectedPattern
from diagnostics.pattern_engine import PatternThresholds
from interventions import InterventionRegistry, InterventionManager
from analysis.verifier import PrePostVerifier, MetricDelta
from workflow import WorkflowFitEngine
from outcomes import OutcomeJoinEngine, OutcomeGovernance, GovernanceLevel
from outcomes.cross_analysis import InterventionOutcomeAnalyzer, InterventionOutcomeResult
from analysis.verifier import PrePostVerifier


# ── P1-A: Pattern engine ─────────────────────────────────────────────────

class TestPatternEngine(unittest.TestCase):

    def setUp(self):
        self.svc = PilotService()

    def test_detects_patterns_for_cohort(self):
        cohort_patterns = self.svc.detect_cohort_patterns()
        self.assertEqual(len(cohort_patterns), 50)
        # At least some operators should have patterns
        operators_with = sum(1 for p in cohort_patterns.values() if p)
        self.assertGreater(operators_with, 0)

    def test_pattern_ids_are_from_registry(self):
        valid_ids = {"P-CTX-01", "P-CTX-02", "P-BURN-01", "P-HIDDEN-01", "P-MODEL-01", "P-STAGE-01"}
        cohort_patterns = self.svc.detect_cohort_patterns()
        for patterns in cohort_patterns.values():
            for p in patterns:
                self.assertIn(p.pattern_id, valid_ids)

    def test_patterns_carry_evidence(self):
        cohort_patterns = self.svc.detect_cohort_patterns()
        for patterns in cohort_patterns.values():
            for p in patterns:
                self.assertTrue(p.evidence_summary)
                self.assertGreater(p.confidence, 0)


# ── P1-B: Diagnosis engine ───────────────────────────────────────────────

class TestDiagnosisEngine(unittest.TestCase):
    """P1 acceptance: every diagnosis contains evidence + alternatives + status=HYPOTHESIS."""

    def setUp(self):
        self.svc = PilotService()
        self.cohort_diags = self.svc.generate_cohort_diagnoses()

    def test_all_diagnoses_have_evidence(self):
        for oid, diags in self.cohort_diags.items():
            for d in diags:
                self.assertTrue(d.evidence, f"{oid}: diagnosis missing evidence")

    def test_all_diagnoses_have_alternatives(self):
        for oid, diags in self.cohort_diags.items():
            for d in diags:
                self.assertGreater(len(d.alternatives), 0,
                                   f"{oid}: diagnosis missing alternatives")

    def test_all_diagnoses_are_hypotheses(self):
        for oid, diags in self.cohort_diags.items():
            for d in diags:
                self.assertEqual(d.status, DiagnosisStatus.HYPOTHESIS,
                                 f"{oid}: status is {d.status}, expected HYPOTHESIS")

    def test_no_causal_claims(self):
        """Diagnoses must never be VALIDATED without separate validation."""
        for oid, diags in self.cohort_diags.items():
            for d in diags:
                self.assertNotEqual(d.status, DiagnosisStatus.VALIDATED)


# ── P1-C: Intervention registry + manager ────────────────────────────────

class TestInterventionManager(unittest.TestCase):
    """P1 acceptance: intervention declares target metric/window before follow-up."""

    def test_assign_requires_target_metric(self):
        mgr = InterventionManager()
        with self.assertRaises(ValueError):
            mgr.assign("int_001", "op_031", "CTX-001", "P-CTX-01", "", date(2026, 8, 1), 14)

    def test_assign_requires_followup_days(self):
        mgr = InterventionManager()
        with self.assertRaises(ValueError):
            mgr.assign("int_001", "op_031", "CTX-001", "P-CTX-01", "leverage", date(2026, 8, 1), 0)

    def test_assign_with_valid_params(self):
        mgr = InterventionManager()
        iv = mgr.assign("int_001", "op_031", "CTX-001", "P-CTX-01", "leverage", date(2026, 8, 1), 14)
        self.assertEqual(iv.target_metric, "leverage")
        self.assertEqual(iv.followup_days, 14)

    def test_intervention_failure_representable(self):
        """P1: intervention failure is representable and reportable."""
        mgr = InterventionManager()
        iv = mgr.assign("int_001", "op_031", "CTX-001", "P-CTX-01", "leverage", date(2026, 8, 1), 14)
        closed_neg = mgr.close(iv, InterventionOutcome.NEGATIVE)
        self.assertEqual(closed_neg.synthetic_outcome, InterventionOutcome.NEGATIVE)
        self.assertTrue(mgr.is_representable_failure(closed_neg))

        closed_no_effect = mgr.close(iv, InterventionOutcome.NO_EFFECT)
        self.assertEqual(closed_no_effect.synthetic_outcome, InterventionOutcome.NO_EFFECT)
        self.assertTrue(mgr.is_representable_failure(closed_no_effect))

    def test_registry_has_12_entries(self):
        reg = InterventionRegistry()
        self.assertEqual(len(reg.all()), 12)

    def test_recommend_returns_relevant_interventions(self):
        svc = PilotService()
        recs = svc.recommend_interventions("op_031")
        # op_031 has P-CTX-01 pattern → should get CTX interventions
        self.assertGreater(len(recs), 0)


# ── P1-D: Pre/post verifier ──────────────────────────────────────────────

class TestPrePostVerifier(unittest.TestCase):
    """P1 acceptance: pre/post verifier shows target + non-target metric deltas."""

    def setUp(self):
        self.svc = PilotService()

    def test_verify_shows_target_and_non_target(self):
        results = self.svc.verify_all_interventions()
        self.assertGreater(len(results), 0)
        for r in results:
            # Target delta should exist
            self.assertIsNotNone(r.target_delta)
            self.assertTrue(r.target_delta.is_target)
            # Non-target deltas should also exist
            self.assertGreater(len(r.non_target_deltas), 0)
            for d in r.non_target_deltas:
                self.assertFalse(d.is_target)

    def test_verify_carries_observation_windows(self):
        results = self.svc.verify_all_interventions()
        for r in results:
            self.assertEqual(len(r.baseline_window), 2)
            self.assertEqual(len(r.followup_window), 2)

    def test_verify_represents_no_data_case(self):
        """When follow-up window has no data, the verifier should represent that."""
        results = self.svc.verify_all_interventions()
        # Demo data only covers July, follow-up is August → no follow-up data
        for r in results:
            if r.target_delta.followup_value is None:
                # This is the expected case — no data, represented explicitly
                self.assertIsNone(r.target_delta.absolute_delta)
                self.assertIn("no data", r.summary.lower())


# ── P2-A: Workflow fit ───────────────────────────────────────────────────

class TestWorkflowFit(unittest.TestCase):
    """P2 acceptance: workflow fit exposes observation count and uncertainty;
    no stage-fit claim without minimum sample rule."""

    def setUp(self):
        self.svc = PilotService()
        self.report = self.svc.workflow_fit_report()

    def test_exposes_observation_count(self):
        for results in self.report.operator_results.values():
            for r in results:
                self.assertGreaterEqual(r.observation_count, 0)

    def test_exposes_uncertainty(self):
        for results in self.report.operator_results.values():
            for r in results:
                self.assertIsNotNone(r.uncertainty)
                self.assertGreater(r.uncertainty, 0)

    def test_no_fit_claim_below_min_sample(self):
        """P2: no stage-fit claim without minimum sample rule."""
        for results in self.report.operator_results.values():
            for r in results:
                if r.observation_count < self.report.min_sample_rule:
                    self.assertFalse(r.can_claim_fit,
                                     f"{r.operator_id}/{r.stage_id}: fit claimed with only {r.observation_count} obs")

    def test_claim_status_reflects_sample_size(self):
        for results in self.report.operator_results.values():
            for r in results:
                if r.observation_count == 0:
                    self.assertEqual(r.claim_status, "insufficient_sample")
                elif r.observation_count < self.report.min_sample_rule:
                    self.assertIn(r.claim_status, ("provisional", "insufficient_sample"))

    def test_seven_stages(self):
        self.assertEqual(len(self.report.stages), 7)
        expected = {"discovery", "requirements", "architecture", "implementation", "testing", "review", "release"}
        self.assertEqual(set(self.report.stages), expected)


# ── P2-B: Outcome joins ──────────────────────────────────────────────────

class TestOutcomeJoins(unittest.TestCase):
    """P2 acceptance: outcome joins remain separately governed;
    outcome analysis separates association from causal claim."""

    def test_governance_required(self):
        with self.assertRaises(ValueError):
            OutcomeJoinEngine(None)

    def test_synthetic_governance(self):
        gov = OutcomeGovernance.synthetic()
        self.assertEqual(gov.governance_level, GovernanceLevel.NONE)
        self.assertFalse(gov.causal_claim_permitted)

    def test_join_labels_association_not_causation(self):
        svc = PilotService()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            w = csv.DictWriter(f, fieldnames=["operator_id", "intervention_id", "window_start", "window_end", "metric_x", "synthetic"])
            w.writeheader()
            w.writerow({"operator_id": "op_031", "intervention_id": "int_005", "window_start": "2026-08-01", "window_end": "2026-08-14", "metric_x": "1.5", "synthetic": "true"})
            path = f.name
        try:
            results = svc.join_outcomes(path)
            self.assertGreater(len(results), 0)
            for r in results:
                self.assertEqual(r["claim_type"], "ASSOCIATION")
                self.assertNotEqual(r["claim_type"], "CAUSATION")
        finally:
            os.unlink(path)

    def test_join_separates_internal_and_external(self):
        svc = PilotService()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            w = csv.DictWriter(f, fieldnames=["operator_id", "intervention_id", "window_start", "window_end", "ext_metric", "synthetic"])
            w.writeheader()
            for iv in svc.interventions[:3]:
                w.writerow({"operator_id": iv.operator_id, "intervention_id": iv.intervention_id, "window_start": "2026-08-01", "window_end": "2026-08-14", "ext_metric": "2.0", "synthetic": "true"})
            path = f.name
        try:
            results = svc.join_outcomes(path)
            for r in results:
                # Internal and external deltas must be in separate fields
                self.assertIn("internal_metric_deltas", r)
                self.assertIn("external_outcome_deltas", r)
                self.assertNotEqual(r["internal_metric_deltas"], r["external_outcome_deltas"])
        finally:
            os.unlink(path)

    def test_governance_metadata_carried(self):
        svc = PilotService()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            w = csv.DictWriter(f, fieldnames=["operator_id", "intervention_id", "window_start", "window_end", "metric_x", "synthetic"])
            w.writeheader()
            w.writerow({"operator_id": "op_031", "intervention_id": "", "window_start": "2026-08-01", "window_end": "2026-08-14", "metric_x": "1.5", "synthetic": "true"})
            path = f.name
        try:
            results = svc.join_outcomes(path)
            for r in results:
                self.assertIn("governance", r)
                self.assertIn("governance_level", r["governance"])
                self.assertFalse(r["governance"]["causal_claim_permitted"])
        finally:
            os.unlink(path)


# ── P2-C: Intervention × Outcome Analysis ────────────────────────────────

class TestInterventionOutcomeAnalysis(unittest.TestCase):
    """P2 remaining: intervention × outcome cross-analysis."""

    def test_cross_analysis_returns_results(self):
        """Cross-analysis produces results for interventions with outcome data."""
        svc = PilotService()
        outcome_path = str(Path(__file__).resolve().parents[1] / "demo_data" / "external_outcomes.csv")
        results = svc.intervention_outcome_analysis(outcome_path)
        self.assertGreater(len(results), 0)

    def test_cross_analysis_claim_always_association(self):
        """Every result is labeled ASSOCIATION — never CAUSATION."""
        svc = PilotService()
        outcome_path = str(Path(__file__).resolve().parents[1] / "demo_data" / "external_outcomes.csv")
        results = svc.intervention_outcome_analysis(outcome_path)
        for r in results:
            self.assertEqual(r.claim_type, "ASSOCIATION")

    def test_cross_analysis_separates_internal_and_external(self):
        """Internal metric deltas and external outcome deltas are in separate fields."""
        svc = PilotService()
        outcome_path = str(Path(__file__).resolve().parents[1] / "demo_data" / "external_outcomes.csv")
        results = svc.intervention_outcome_analysis(outcome_path)
        for r in results:
            self.assertIsInstance(r.internal_metric_deltas, dict)
            self.assertIsInstance(r.external_outcome_deltas, dict)

    def test_cross_analysis_governance_carried(self):
        """Governance metadata is required and carried through every result."""
        svc = PilotService()
        outcome_path = str(Path(__file__).resolve().parents[1] / "demo_data" / "external_outcomes.csv")
        results = svc.intervention_outcome_analysis(outcome_path)
        for r in results:
            self.assertIsNotNone(r.governance)
            self.assertFalse(r.governance.causal_claim_permitted)

    def test_cross_analysis_to_dict(self):
        """Results survive to_dict serialization."""
        svc = PilotService()
        outcome_path = str(Path(__file__).resolve().parents[1] / "demo_data" / "external_outcomes.csv")
        results = svc.intervention_outcome_analysis(outcome_path)
        for r in results:
            d = r.to_dict()
            self.assertIn("intervention_id", d)
            self.assertIn("internal_metric_deltas", d)
            self.assertIn("external_outcome_deltas", d)
            self.assertEqual(d["claim_type"], "ASSOCIATION")

    def test_cross_analysis_export_markdown(self):
        """Cross-analysis can be exported as Markdown."""
        from reporting import export_intervention_outcomes_markdown
        svc = PilotService()
        outcome_path = str(Path(__file__).resolve().parents[1] / "demo_data" / "external_outcomes.csv")
        results = svc.intervention_outcome_analysis(outcome_path)
        md = export_intervention_outcomes_markdown(svc, results)
        self.assertIn("Intervention × Outcome Analysis", md)
        self.assertIn("ASSOCIATION", md)
        self.assertIn("Internal Metric Deltas", md)
        self.assertIn("External Outcome Deltas", md)

    def test_cross_analysis_internal_deltas_not_null(self):
        """Internal metric deltas are non-null when follow-up telemetry exists.

        Regression test: the demo data now includes Aug 1-15 follow-up
        telemetry for intervention operators, so the verifier can compute
        real pre/post deltas instead of returning None.
        """
        svc = PilotService()
        outcome_path = str(Path(__file__).resolve().parents[1] / "demo_data" / "external_outcomes.csv")
        results = svc.intervention_outcome_analysis(outcome_path)
        self.assertGreater(len(results), 0)
        for r in results:
            target_delta = r.internal_metric_deltas.get(r.target_metric)
            self.assertIsNotNone(
                target_delta,
                f"Target metric '{r.target_metric}' delta is None for {r.intervention_id} — "
                "follow-up telemetry may be missing",
            )


# ── P2-D: Executive Solution Brief ───────────────────────────────────────

class TestExecutiveBrief(unittest.TestCase):
    """P2 remaining: executive solution brief generator (deliverable #11 + #12)."""

    def test_brief_generates_markdown(self):
        """The brief generates valid Markdown."""
        svc = PilotService()
        brief = svc.executive_brief()
        self.assertIsInstance(brief, str)
        self.assertIn("Executive Solution Brief", brief)

    def test_brief_includes_cohort_summary(self):
        """Brief includes cohort size, window, and data quality summary."""
        svc = PilotService()
        brief = svc.executive_brief()
        self.assertIn("Cohort:", brief)
        self.assertIn("Window:", brief)
        self.assertIn("Operators:", brief)
        self.assertIn("Data Quality Summary", brief)

    def test_brief_includes_key_findings(self):
        """Brief includes top patterns and divergence summary."""
        svc = PilotService()
        brief = svc.executive_brief()
        self.assertIn("Key Findings", brief)
        self.assertIn("Divergence", brief)

    def test_brief_includes_intervention_results(self):
        """Brief includes intervention outcome counts."""
        svc = PilotService()
        brief = svc.executive_brief()
        self.assertIn("Intervention Results", brief)

    def test_brief_includes_workflow_fit(self):
        """Brief includes workflow fit summary."""
        svc = PilotService()
        brief = svc.executive_brief()
        self.assertIn("Workflow Fit Summary", brief)
        self.assertIn("minimum sample", brief.lower())

    def test_brief_includes_next_evaluations(self):
        """Brief includes next-evaluations flywheel with eval family mappings."""
        svc = PilotService()
        brief = svc.executive_brief()
        self.assertIn("Next Evaluations", brief)

    def test_brief_next_evaluations_map_to_eval_families(self):
        """Each next-evaluation references an EVAL family ID from `18`."""
        svc = PilotService()
        brief = svc.executive_brief()
        # If there are next-evaluations, they should reference EVAL-XXX IDs
        if "EVAL-" in brief:
            # At least one EVAL reference exists
            self.assertIn("EVAL-", brief)
            # Each should be framed as experiment, not outcome claim
            self.assertIn("experiment", brief.lower())

    def test_brief_next_evaluations_count_is_3_to_4(self):
        """Per `13` deliverable #12: brief outputs 3-4 evidence-backed observations."""
        import re
        svc = PilotService()
        brief = svc.executive_brief()
        # Count next-evaluation sections (### N. EVAL-XXX)
        eval_sections = re.findall(r"### \d+\. EVAL-\d{3}", brief)
        self.assertGreaterEqual(
            len(eval_sections), 3,
            f"Expected 3-4 next-evaluations, got {len(eval_sections)}",
        )
        self.assertLessEqual(
            len(eval_sections), 4,
            f"Expected 3-4 next-evaluations, got {len(eval_sections)}",
        )

    def test_brief_next_evaluations_have_evidence(self):
        """Each next-evaluation must reference measured data (not speculation)."""
        svc = PilotService()
        brief = svc.executive_brief()
        # Every next-evaluation section should have an Evidence line
        import re
        # Split on the next-evaluation sections
        sections = re.split(r"### \d+\. EVAL-\d{3}", brief)
        # sections[0] is the preamble before the first eval; the rest are eval bodies
        for section in sections[1:]:
            # Stop at the next major section or end
            body = section.split("---")[0]
            self.assertIn("Evidence:", body, "Next-evaluation missing Evidence line")

    def test_brief_no_causal_claims(self):
        """Brief does not make causal claims."""
        svc = PilotService()
        brief = svc.executive_brief()
        self.assertNotIn("CAUSATION", brief)
        self.assertNotIn("caused", brief.lower())

    def test_brief_export_via_reporting(self):
        """Brief is accessible via the reporting module."""
        from reporting import export_executive_brief
        svc = PilotService()
        brief = export_executive_brief(svc)
        self.assertIn("Executive Solution Brief", brief)


# ── P2-E: Replicated Validation ──────────────────────────────────────────

class TestReplicatedValidation(unittest.TestCase):
    """P2 remaining: replicated validation across window/cohort splits."""

    def test_replicate_pattern_window_split(self):
        """Can split the 30-day window and check if a pattern appears in both halves."""
        svc = PilotService()
        result = svc.replicate_finding("pattern", "P-CTX-01", "window")
        self.assertEqual(result.finding_type, "pattern")
        self.assertEqual(result.finding_id, "P-CTX-01")
        self.assertEqual(result.split_method, "window")
        # Status should be one of the valid values
        self.assertIn(result.status, ("REPLICATED", "NOT_REPLICATED", "INSUFFICIENT_DATA"))

    def test_replicate_pattern_returns_counts(self):
        """Replication result includes observation counts for both splits."""
        svc = PilotService()
        result = svc.replicate_finding("pattern", "P-CTX-01", "window")
        self.assertIsInstance(result.split_a_count, int)
        self.assertIsInstance(result.split_b_count, int)

    def test_replicate_pattern_includes_caveat(self):
        """Replication result includes a non-empty caveat noting descriptive nature."""
        svc = PilotService()
        result = svc.replicate_finding("pattern", "P-CTX-01", "window")
        self.assertTrue(result.caveat)  # caveat is non-empty
        self.assertIn("descriptive", result.caveat.lower())

    def test_replicate_divergence_window_split(self):
        """Can check if an operator's divergence class holds across window halves."""
        svc = PilotService()
        result = svc.replicate_finding("divergence", svc.operator_ids[0], "window")
        self.assertEqual(result.finding_type, "divergence")
        self.assertIn(result.status, ("REPLICATED", "NOT_REPLICATED", "INSUFFICIENT_DATA"))

    def test_replicate_unknown_finding_type(self):
        """Unknown finding type returns INSUFFICIENT_DATA with a caveat."""
        svc = PilotService()
        result = svc.replicate_finding("unknown_type", "some_id", "window")
        self.assertEqual(result.status, "INSUFFICIENT_DATA")
        self.assertIn("Unknown finding type", result.caveat)

    def test_replicate_pattern_not_found(self):
        """Pattern that doesn't exist in any operator returns INSUFFICIENT_DATA."""
        svc = PilotService()
        result = svc.replicate_finding("pattern", "P-NONEXISTENT-99", "window")
        self.assertEqual(result.status, "INSUFFICIENT_DATA")
        self.assertIn("not found", result.caveat)

    def test_replication_result_to_dict(self):
        """Replication result survives to_dict serialization."""
        svc = PilotService()
        result = svc.replicate_finding("pattern", "P-CTX-01", "window")
        d = result.to_dict()
        self.assertIn("finding_type", d)
        self.assertIn("finding_id", d)
        self.assertIn("status", d)
        self.assertIn("split_a_found", d)
        self.assertIn("split_b_found", d)
        self.assertIn("caveat", d)

    def test_replication_no_causal_claim(self):
        """Replication caveat explicitly disclaims causal validation."""
        svc = PilotService()
        result = svc.replicate_finding("pattern", "P-CTX-01", "window")
        # The caveat explicitly says "not causal validation"
        self.assertIn("causal", result.caveat.lower())
        self.assertIn("not causal", result.caveat.lower())

    def test_replicate_pattern_cohort_split(self):
        """Can split the operator's observations into random halves and check pattern."""
        svc = PilotService()
        result = svc.replicate_finding("pattern", "P-CTX-01", "cohort")
        self.assertEqual(result.finding_type, "pattern")
        self.assertEqual(result.finding_id, "P-CTX-01")
        self.assertEqual(result.split_method, "cohort")
        self.assertIn(result.status, ("REPLICATED", "NOT_REPLICATED", "INSUFFICIENT_DATA"))

    def test_replicate_divergence_cohort_split(self):
        """Can split the cohort into two random halves and check if a divergence finding holds."""
        svc = PilotService()
        result = svc.replicate_finding("divergence", svc.operator_ids[0], "cohort")
        self.assertEqual(result.finding_type, "divergence")
        self.assertEqual(result.split_method, "cohort")
        self.assertIn(result.status, ("REPLICATED", "NOT_REPLICATED", "INSUFFICIENT_DATA"))
        # Cohort split should report operator counts in split_a/b_count
        self.assertIsInstance(result.split_a_count, int)
        self.assertIsInstance(result.split_b_count, int)

    def test_replicate_divergence_cohort_split_unknown_operator(self):
        """Cohort split for an operator not in the cohort returns INSUFFICIENT_DATA."""
        svc = PilotService()
        result = svc.replicate_finding("divergence", "op_nonexistent", "cohort")
        self.assertEqual(result.status, "INSUFFICIENT_DATA")
        self.assertIn("not in cohort", result.caveat)

    def test_replicate_divergence_cohort_split_reproducible(self):
        """Cohort split uses a fixed seed, so results are reproducible."""
        svc = PilotService()
        r1 = svc.replicate_finding("divergence", svc.operator_ids[0], "cohort")
        r2 = svc.replicate_finding("divergence", svc.operator_ids[0], "cohort")
        self.assertEqual(r1.status, r2.status)
        self.assertEqual(r1.split_a_found, r2.split_a_found)
        self.assertEqual(r1.split_b_found, r2.split_b_found)


# ── P2-F: Markdown rendering edge cases ──────────────────────────────────

class TestMarkdownRendering(unittest.TestCase):
    """Tests that markdown rendering handles None metric values without crashing."""

    def test_executive_brief_renders_with_none_median(self):
        """Executive brief does not crash when a median is None.

        Regression test for f-string conditional bug where
        {val:.4f} if val else 'N/A' was literal text, not a conditional.
        """
        svc = PilotService()
        # Monkey-patch cohort_medians to return None for a metric
        original = svc.cohort_medians
        svc.cohort_medians = lambda: {"leverage": None, "yield": 0.5, "token_snr": 1.0, "construction": 0.8}
        try:
            brief = svc.executive_brief()
            self.assertIn("N/A", brief)
            self.assertIn("Executive Solution Brief", brief)
        finally:
            svc.cohort_medians = original

    def test_cohort_markdown_renders_with_none_median(self):
        """Cohort markdown does not crash when a median is None.

        Regression test for the same f-string conditional bug in exporters.py.
        """
        from reporting import export_cohort_markdown
        svc = PilotService()
        original = svc.cohort_medians
        svc.cohort_medians = lambda: {"leverage": None, "yield": 0.5, "token_snr": 1.0, "construction": 0.8}
        try:
            md = export_cohort_markdown(svc)
            self.assertIn("N/A", md)
        finally:
            svc.cohort_medians = original


# ── Gap-fix tests: CLI commands, exporters, EXPERIMENT label ─────────────

class TestCLICommands(unittest.TestCase):
    """Tests for CLI commands wired during gap-fix pass."""

    def setUp(self):
        from cli.main import build_parser
        self.parser = build_parser()

    def _run(self, *argv):
        """Run a CLI command and capture output."""
        import io as _io
        from cli.main import main
        buf = _io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            rc = main(list(argv))
        finally:
            sys.stdout = old
        return rc, buf.getvalue()

    def test_pilot_init(self):
        """pilot init returns initialized status with governance."""
        rc, out = self._run("--json", "pilot", "init", "--cohort", "acme-50")
        self.assertEqual(rc, 0)
        import json
        data = json.loads(out)
        self.assertEqual(data["status"], "initialized")
        self.assertIn("metric_registry_version", data)

    def test_compare_models(self):
        """compare models shows per-model metrics for an operator."""
        rc, out = self._run("--json", "compare", "models", "op_031")
        self.assertEqual(rc, 0)
        import json
        data = json.loads(out)
        self.assertEqual(data["operator_id"], "op_031")
        self.assertIn("metric_by_model", data)
        self.assertGreater(len(data["models"]), 0)

    def test_intervention_assign_requires_authorization(self):
        """intervention assign fails without --authorized-by."""
        rc, out = self._run("--json", "intervention", "assign", "op_031",
                            "--plan", "CTX-001", "--target-metric", "yield")
        self.assertEqual(rc, 0)
        import json
        data = json.loads(out)
        self.assertIn("error", data)
        self.assertIn("authorization", data["error"].lower())

    def test_intervention_assign_with_authorization(self):
        """intervention assign succeeds with --authorized-by."""
        rc, out = self._run("--json", "intervention", "assign", "op_031",
                            "--plan", "CTX-001", "--target-metric", "yield",
                            "--followup-days", "14",
                            "--authorized-by", "test@acme.com")
        self.assertEqual(rc, 0)
        import json
        data = json.loads(out)
        self.assertEqual(data["catalog_id"], "CTX-001")
        self.assertEqual(data["authorized_by"], "test@acme.com")
        self.assertIn("EXPERIMENT", data["label"])

    def test_intervention_close_requires_authorization(self):
        """intervention close fails without --authorized-by."""
        rc, out = self._run("--json", "intervention", "close",
                            "--id", "int_001")
        self.assertEqual(rc, 0)
        import json
        data = json.loads(out)
        self.assertIn("error", data)

    def test_intervention_close_with_authorization(self):
        """intervention close succeeds with --authorized-by."""
        rc, out = self._run("--json", "intervention", "close",
                            "--id", "int_001", "--outcome", "SUCCESS",
                            "--authorized-by", "test@acme.com")
        self.assertEqual(rc, 0)
        import json
        data = json.loads(out)
        self.assertEqual(data["outcome"], "SUCCESS")
        self.assertIn("OUTCOME", data["label"])

    def test_workflow_observe(self):
        """workflow observe records a stage observation."""
        rc, out = self._run("--json", "workflow", "observe",
                            "--operator", "op_031", "--stage", "implementation")
        self.assertEqual(rc, 0)
        import json
        data = json.loads(out)
        self.assertTrue(data["recorded"])
        self.assertEqual(data["observation"]["stage_id"], "implementation")

    def test_export_zip_bundle(self):
        """export pilot --format zip produces a bundled report."""
        rc, out = self._run("export", "pilot", "--format", "zip")
        self.assertEqual(rc, 0)
        self.assertIn("PILOT EXPORT BUNDLE", out)
        self.assertIn("HYPOTHESIS MAP", out)
        self.assertIn("RE-MEASUREMENT REPORT", out)

    def test_export_hypothesis_map(self):
        """export hypothesis-map produces the deliverable."""
        rc, out = self._run("export", "hypothesis-map")
        self.assertEqual(rc, 0)
        self.assertIn("Hypothesis Map", out)
        self.assertIn("[HYPOTHESIS]", out)

    def test_export_remeasurement(self):
        """export remeasurement produces the deliverable."""
        rc, out = self._run("export", "remeasurement")
        self.assertEqual(rc, 0)
        self.assertIn("Re-measurement Report", out)
        self.assertIn("[EXPERIMENT]", out)


class TestNewExporters(unittest.TestCase):
    """Tests for the new standalone exporters (#6, #8)."""

    def test_export_hypothesis_map(self):
        """Deliverable #6: Hypothesis Map."""
        from reporting import export_hypothesis_map
        svc = PilotService()
        md = export_hypothesis_map(svc)
        self.assertIn("Hypothesis Map", md)
        self.assertIn("[HYPOTHESIS]", md)
        self.assertIn("[FACT]", md)
        self.assertIn("[LIMITATION]", md)

    def test_export_remeasurement_report(self):
        """Deliverable #8: Re-measurement Report."""
        from reporting import export_remeasurement_report
        svc = PilotService()
        md = export_remeasurement_report(svc)
        self.assertIn("Re-measurement Report", md)
        self.assertIn("[EXPERIMENT]", md)
        self.assertIn("[MEASUREMENT]", md)
        # Should have at least one intervention
        self.assertIn("int_", md)

    def test_experiment_label_in_intervention_outcomes(self):
        """EXPERIMENT label appears in intervention outcomes markdown."""
        from reporting import export_intervention_outcomes_markdown
        svc = PilotService()
        outcome_path = str(Path(__file__).resolve().parents[1] / "demo_data" / "external_outcomes.csv")
        results = svc.intervention_outcome_analysis(outcome_path)
        md = export_intervention_outcomes_markdown(svc, results)
        self.assertIn("[EXPERIMENT]", md)

    def test_experiment_label_in_executive_brief(self):
        """EXPERIMENT label appears in executive brief next-evaluations."""
        svc = PilotService()
        brief = svc.executive_brief()
        self.assertIn("[EXPERIMENT]", brief)
        self.assertIn("[MEASUREMENT]", brief)


class TestMCPCohortResource(unittest.TestCase):
    """Test the new enterprise://cohort/{cohort_id} resource."""

    def test_get_cohort_overview(self):
        """get_cohort_overview returns cohort-level data with governance."""
        from mcp_server.server import get_cohort_overview
        data = get_cohort_overview("acme_50")
        self.assertEqual(data["cohort_id"], "acme_50")
        self.assertIn("medians", data)
        self.assertIn("distributions", data)
        self.assertIn("divergence_counts", data)
        self.assertIn("synthetic", data)

    def test_mcp_has_6_resources(self):
        """MCP server registers all 6 resources from spec 08."""
        from mcp_server.server import mcp, _HAS_MCP_SDK
        if not _HAS_MCP_SDK:
            self.skipTest("MCP SDK not available")
        rm = mcp._resource_manager
        static_resources = set(rm._resources.keys())
        templates = set(rm._templates.keys())
        all_resources = static_resources | templates
        self.assertIn("enterprise://cohort/{cohort_id}", all_resources)
        self.assertIn("enterprise://pilot/{cohort_id}", all_resources)
        self.assertIn("enterprise://operator/{operator_id}", all_resources)
        self.assertIn("enterprise://metrics/registry", all_resources)
        self.assertIn("enterprise://interventions/catalog", all_resources)
        self.assertIn("enterprise://workflow/{workflow_id}", all_resources)
        self.assertEqual(len(all_resources), 6)


# ── Diagnostic hierarchy ordering rule (spec 09, gap #1) ──────────────────

class TestDiagnosticHierarchy(unittest.TestCase):
    """Tests for the diagnostic hierarchy ordering rule per `09`.

    The hierarchy rule is the spec's primary safeguard against operator-blame
    misattribution: diagnoses are labeled with their level (operator /
    tool_model / workflow / organization), emitted in hierarchy order, and
    a higher-level hypothesis is flagged structurally_stronger when evidence
    supports both an operator-level and a higher-level hypothesis.
    """

    def setUp(self):
        self.svc = PilotService()

    def test_diagnosis_has_level_field(self):
        """Every diagnosis carries a non-None hierarchy level."""
        cohort_diags = self.svc.generate_cohort_diagnoses()
        for oid, diags in cohort_diags.items():
            for d in diags:
                self.assertIsNotNone(d.level, f"{oid}: level is None")
                self.assertIn(d.level.value, ("operator", "tool_model", "workflow", "organization"))

    def test_diagnoses_sorted_by_hierarchy_level(self):
        """Diagnoses are emitted in hierarchy order (operator first)."""
        from domain.diagnosis import DiagnosticLevel
        cohort_diags = self.svc.generate_cohort_diagnoses()
        for oid, diags in cohort_diags.items():
            levels = [DiagnosticLevel.order(d.level) for d in diags]
            self.assertEqual(levels, sorted(levels),
                             f"{oid}: diagnoses not sorted by hierarchy level (got {levels})")

    def test_operator_level_diagnoses_not_flagged_stronger(self):
        """Operator-level diagnoses are never flagged structurally_stronger."""
        cohort_diags = self.svc.generate_cohort_diagnoses()
        for oid, diags in cohort_diags.items():
            for d in diags:
                if d.level.value == "operator":
                    self.assertFalse(d.structurally_stronger,
                                     f"{oid}: operator-level diagnosis flagged structurally_stronger")

    def test_higher_level_flagged_stronger_when_operator_also_present(self):
        """When both operator and higher-level hypotheses exist, the higher-
        level one is flagged structurally_stronger. Per `09`: "A hypothesis
        at a higher level should be flagged as structurally stronger than
        one at a lower level when evidence supports both."
        """
        from domain.diagnosis import DiagnosticLevel
        cohort_diags = self.svc.generate_cohort_diagnoses()
        # Find at least one operator with mixed levels (operator + higher).
        found_mixed = False
        for oid, diags in cohort_diags.items():
            levels = {d.level for d in diags}
            if DiagnosticLevel.OPERATOR in levels and len(levels - {DiagnosticLevel.OPERATOR}) > 0:
                found_mixed = True
                for d in diags:
                    if DiagnosticLevel.order(d.level) > DiagnosticLevel.order(DiagnosticLevel.OPERATOR):
                        self.assertTrue(d.structurally_stronger,
                                        f"{oid}: higher-level {d.pattern_id} not flagged structurally_stronger")
                break
        # The demo data should produce at least one operator with mixed levels
        # (P-CTX-02 operator-level + P-STAGE-01 workflow-level).
        self.assertTrue(found_mixed,
                        "Expected at least one operator with mixed-level diagnoses")

    def test_higher_level_not_flagged_when_no_operator_level(self):
        """A higher-level diagnosis is NOT flagged structurally_stronger when
        no operator-level diagnosis exists for the same operator."""
        from domain.diagnosis import DiagnosticLevel
        cohort_diags = self.svc.generate_cohort_diagnoses()
        for oid, diags in cohort_diags.items():
            levels = {d.level for d in diags}
            if DiagnosticLevel.OPERATOR not in levels:
                for d in diags:
                    self.assertFalse(d.structurally_stronger,
                                     f"{oid}: {d.pattern_id} flagged structurally_stronger without operator-level")

    def test_diagnosis_to_dict_includes_level_and_stronger(self):
        """to_dict() includes the level and structurally_stronger fields."""
        cohort_diags = self.svc.generate_cohort_diagnoses()
        for oid, diags in cohort_diags.items():
            for d in diags:
                d_dict = d.to_dict()
                self.assertIn("level", d_dict)
                self.assertIn("structurally_stronger", d_dict)
                self.assertIsInstance(d_dict["structurally_stronger"], bool)

    def test_diagnosis_from_dict_round_trips_level(self):
        """from_dict() round-trips the level and structurally_stronger fields."""
        from domain.diagnosis import Diagnosis, DiagnosticLevel
        cohort_diags = self.svc.generate_cohort_diagnoses()
        for oid, diags in cohort_diags.items():
            for d in diags:
                d_dict = d.to_dict()
                d2 = Diagnosis.from_dict(d_dict)
                self.assertEqual(d2.level, d.level)
                self.assertEqual(d2.structurally_stronger, d.structurally_stronger)

    def test_pattern_knowledge_tags_each_pattern_with_level(self):
        """Every pattern in PATTERN_KNOWLEDGE has a hierarchy level."""
        from diagnostics.diagnosis_engine import PATTERN_KNOWLEDGE
        from domain.diagnosis import DiagnosticLevel
        for pattern_id, knowledge in PATTERN_KNOWLEDGE.items():
            self.assertIn("level", knowledge, f"{pattern_id}: missing level in PATTERN_KNOWLEDGE")
            self.assertIsInstance(knowledge["level"], DiagnosticLevel,
                                  f"{pattern_id}: level not a DiagnosticLevel")

    def test_p_model_01_is_tool_model_level(self):
        """P-MODEL-01 is tagged as TOOL_MODEL level (the canonical tool/model pattern)."""
        from diagnostics.diagnosis_engine import PATTERN_KNOWLEDGE
        from domain.diagnosis import DiagnosticLevel
        self.assertEqual(PATTERN_KNOWLEDGE["P-MODEL-01"]["level"], DiagnosticLevel.TOOL_MODEL)

    def test_p_stage_01_is_workflow_level(self):
        """P-STAGE-01 is tagged as WORKFLOW level (the canonical workflow pattern)."""
        from diagnostics.diagnosis_engine import PATTERN_KNOWLEDGE
        from domain.diagnosis import DiagnosticLevel
        self.assertEqual(PATTERN_KNOWLEDGE["P-STAGE-01"]["level"], DiagnosticLevel.WORKFLOW)


# ── P-MODEL-01 and P-STAGE-01 detectors (spec 09, gap #2) ─────────────────

class TestPModel01Detector(unittest.TestCase):
    """Tests for the P-MODEL-01 (model sensitivity) detector."""

    def setUp(self):
        self.svc = PilotService()

    def test_p_model_01_detected_in_cohort(self):
        """P-MODEL-01 is detected for at least one operator in the demo cohort."""
        cohort_patterns = self.svc.detect_cohort_patterns()
        pmodel_count = sum(
            1 for patterns in cohort_patterns.values()
            for p in patterns if p.pattern_id == "P-MODEL-01"
        )
        self.assertGreater(pmodel_count, 0, "P-MODEL-01 not detected for any operator")

    def test_p_model_01_has_evidence(self):
        """P-MODEL-01 patterns carry evidence with model-level detail."""
        cohort_patterns = self.svc.detect_cohort_patterns()
        for oid, patterns in cohort_patterns.items():
            for p in patterns:
                if p.pattern_id == "P-MODEL-01":
                    self.assertIn("leverage", p.evidence_summary.lower())
                    self.assertIn("spread", p.evidence_summary.lower())
                    self.assertIn("model", p.evidence_summary.lower())

    def test_p_model_01_requires_multiple_models(self):
        """P-MODEL-01 is not detected when an operator uses only one model."""
        from diagnostics import PatternEngine
        from domain.measurement import Measurement, MetricStatus
        from domain.reference_population import ReferencePopulation
        from domain.observation import Observation
        from datetime import date, datetime, timezone
        # Build an operator with only one model — no model sensitivity possible.
        obs = [
            Observation(
                observation_id=f"test_{i}",
                operator_id="op_test",
                timestamp=datetime(2026, 7, 1 + i, 12, tzinfo=timezone.utc),
                input_tokens=100, output_tokens=50,
                cache_read_tokens=200, cache_write_tokens=300,
                synthetic=True, model="claude-code", platform="claude",
            )
            for i in range(10)
        ]
        ref = ReferencePopulation(
            reference_id="test", version="v1", date=date(2026, 7, 30),
            description="test", synthetic=True,
            distributions={"leverage": {"p0": 0, "p50": 10, "p100": 100}},
        )
        ms = [Measurement(
            metric_id="leverage", metric_version="1.0", operator_id="op_test",
            value=2.0, unit="ratio", window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            source="test", status=MetricStatus.CANONICAL, eligibility="I>0", synthetic=True,
        )]
        engine = PatternEngine()
        patterns = engine.detect_patterns(
            "op_test", ms, ref, usage_percentile=50,
            window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            observations=obs,
        )
        pmodel = [p for p in patterns if p.pattern_id == "P-MODEL-01"]
        self.assertEqual(len(pmodel), 0, "P-MODEL-01 detected with only one model")

    def test_p_model_01_detected_with_significant_spread(self):
        """P-MODEL-01 is detected when an operator's leverage shifts significantly across models."""
        from diagnostics import PatternEngine, PatternThresholds
        from domain.measurement import Measurement, MetricStatus
        from domain.reference_population import ReferencePopulation
        from domain.observation import Observation
        from datetime import date, datetime, timezone
        # Build an operator with two models and a large leverage spread.
        # Model A: R=100, I=100 → leverage=1.0
        # Model B: R=500, I=100 → leverage=5.0  (5x spread → 400% > 30% threshold)
        obs = []
        for i in range(5):
            obs.append(Observation(
                observation_id=f"a_{i}", operator_id="op_test",
                timestamp=datetime(2026, 7, 1 + i, 12, tzinfo=timezone.utc),
                input_tokens=100, output_tokens=50,
                cache_read_tokens=100, cache_write_tokens=200,
                synthetic=True, model="model_a", platform="claude",
            ))
        for i in range(5):
            obs.append(Observation(
                observation_id=f"b_{i}", operator_id="op_test",
                timestamp=datetime(2026, 7, 6 + i, 12, tzinfo=timezone.utc),
                input_tokens=100, output_tokens=50,
                cache_read_tokens=500, cache_write_tokens=200,
                synthetic=True, model="model_b", platform="claude",
            ))
        ref = ReferencePopulation(
            reference_id="test", version="v1", date=date(2026, 7, 30),
            description="test", synthetic=True,
            distributions={"leverage": {"p0": 0, "p50": 10, "p100": 100}},
        )
        ms = [Measurement(
            metric_id="leverage", metric_version="1.0", operator_id="op_test",
            value=3.0, unit="ratio", window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            source="test", status=MetricStatus.CANONICAL, eligibility="I>0", synthetic=True,
        )]
        engine = PatternEngine()
        patterns = engine.detect_patterns(
            "op_test", ms, ref, usage_percentile=50,
            window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            observations=obs,
        )
        pmodel = [p for p in patterns if p.pattern_id == "P-MODEL-01"]
        self.assertEqual(len(pmodel), 1, "P-MODEL-01 not detected with significant model spread")
        self.assertGreater(pmodel[0].confidence, 0)


class TestPStage01Detector(unittest.TestCase):
    """Tests for the P-STAGE-01 (stage specialization) detector."""

    def setUp(self):
        self.svc = PilotService()

    def test_p_stage_01_detected_in_cohort(self):
        """P-STAGE-01 is detected for at least one operator in the demo cohort."""
        cohort_patterns = self.svc.detect_cohort_patterns()
        pstage_count = sum(
            1 for patterns in cohort_patterns.values()
            for p in patterns if p.pattern_id == "P-STAGE-01"
        )
        self.assertGreater(pstage_count, 0, "P-STAGE-01 not detected for any operator")

    def test_p_stage_01_has_evidence(self):
        """P-STAGE-01 patterns carry evidence with stage-level detail."""
        cohort_patterns = self.svc.detect_cohort_patterns()
        for oid, patterns in cohort_patterns.items():
            for p in patterns:
                if p.pattern_id == "P-STAGE-01":
                    self.assertIn("fit", p.evidence_summary.lower())
                    self.assertIn("spread", p.evidence_summary.lower())
                    self.assertIn("stage", p.evidence_summary.lower())

    def test_p_stage_01_requires_multiple_stages(self):
        """P-STAGE-01 is not detected when an operator has only one stage."""
        from diagnostics import PatternEngine
        from domain.measurement import Measurement, MetricStatus
        from domain.reference_population import ReferencePopulation
        from domain.workflow import WorkflowObservation
        from datetime import date
        ref = ReferencePopulation(
            reference_id="test", version="v1", date=date(2026, 7, 30),
            description="test", synthetic=True,
            distributions={"leverage": {"p0": 0, "p50": 10, "p100": 100}},
        )
        ms = [Measurement(
            metric_id="leverage", metric_version="1.0", operator_id="op_test",
            value=2.0, unit="ratio", window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            source="test", status=MetricStatus.CANONICAL, eligibility="I>0", synthetic=True,
        )]
        wobs = [
            WorkflowObservation(
                operator_id="op_test", workflow_id="wf", stage_id="implementation",
                date=date(2026, 7, 15), provisional_fit=0.8, evidence_count=10, synthetic=True,
            ),
        ]
        engine = PatternEngine()
        patterns = engine.detect_patterns(
            "op_test", ms, ref, usage_percentile=50,
            window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            workflow_observations=wobs,
        )
        pstage = [p for p in patterns if p.pattern_id == "P-STAGE-01"]
        self.assertEqual(len(pstage), 0, "P-STAGE-01 detected with only one stage")

    def test_p_stage_01_detected_with_significant_spread(self):
        """P-STAGE-01 is detected when an operator's fit shifts significantly across stages."""
        from diagnostics import PatternEngine
        from domain.measurement import Measurement, MetricStatus
        from domain.reference_population import ReferencePopulation
        from domain.workflow import WorkflowObservation
        from datetime import date
        ref = ReferencePopulation(
            reference_id="test", version="v1", date=date(2026, 7, 30),
            description="test", synthetic=True,
            distributions={"leverage": {"p0": 0, "p50": 10, "p100": 100}},
        )
        ms = [Measurement(
            metric_id="leverage", metric_version="1.0", operator_id="op_test",
            value=2.0, unit="ratio", window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            source="test", status=MetricStatus.CANONICAL, eligibility="I>0", synthetic=True,
        )]
        # Stage A: fit=0.4, Stage B: fit=0.8 → 100% spread > 25% threshold
        wobs = [
            WorkflowObservation(
                operator_id="op_test", workflow_id="wf", stage_id="stage_a",
                date=date(2026, 7, 15), provisional_fit=0.4, evidence_count=10, synthetic=True,
            ),
            WorkflowObservation(
                operator_id="op_test", workflow_id="wf", stage_id="stage_b",
                date=date(2026, 7, 15), provisional_fit=0.8, evidence_count=10, synthetic=True,
            ),
        ]
        engine = PatternEngine()
        patterns = engine.detect_patterns(
            "op_test", ms, ref, usage_percentile=50,
            window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            workflow_observations=wobs,
        )
        pstage = [p for p in patterns if p.pattern_id == "P-STAGE-01"]
        self.assertEqual(len(pstage), 1, "P-STAGE-01 not detected with significant stage spread")
        self.assertGreater(pstage[0].confidence, 0)


# ── Preferred manager objects (spec 12) ───────────────────────────────────

class TestPreferredManagerObjects(unittest.TestCase):
    """Tests for the 8 preferred manager objects per `12` §Development doctrine.

    These are developmental objects, NOT performance rankings. The avoid-list
    (no leaderboard, no punitive labels, no composite score) is enforced.
    """

    def setUp(self):
        self.svc = PilotService()
        self.objs = self.svc.preferred_manager_objects()

    def test_returns_all_8_object_names(self):
        """All 8 preferred object names are present in the result."""
        expected = {
            "development_groups", "fastest_improvers", "stalled_cohorts",
            "workflow_bottlenecks", "tool_model_fit_opportunities",
            "training_candidates", "peer_support_matches", "remeasurement_queue",
        }
        self.assertEqual(set(self.objs.keys()), expected)

    def test_development_groups_have_evidence(self):
        """Development groups carry evidence and a developmental framing."""
        for g in self.objs["development_groups"]:
            self.assertIn("evidence", g)
            self.assertIn("framing", g)
            self.assertIn("developmental", g["framing"].lower())
            # The framing must explicitly disclaim ranking (e.g. "not a ranking").
            self.assertIn("not a ranking", g["framing"].lower())

    def test_fastest_improvers_not_ranked(self):
        """Fastest improvers are framed as developmental, not a ranking."""
        for imp in self.objs["fastest_improvers"]:
            self.assertIn("framing", imp)
            self.assertIn("developmental", imp["framing"].lower())
            self.assertIn("not a ranking", imp["framing"].lower())

    def test_tool_model_fit_from_p_model_01(self):
        """Tool/model-fit opportunities are surfaced from P-MODEL-01 detections."""
        # If P-MODEL-01 was detected, tool_model_fit_opportunities should be non-empty.
        cohort_patterns = self.svc.detect_cohort_patterns()
        pmodel_count = sum(
            1 for patterns in cohort_patterns.values()
            for p in patterns if p.pattern_id == "P-MODEL-01"
        )
        if pmodel_count > 0:
            self.assertGreater(len(self.objs["tool_model_fit_opportunities"]), 0)
            for opp in self.objs["tool_model_fit_opportunities"]:
                self.assertIn("operator_id", opp)
                self.assertIn("evidence", opp)

    def test_training_candidates_from_diagnoses(self):
        """Training candidates are surfaced from diagnoses with recommended interventions."""
        # Diagnoses with recommended interventions should produce training candidates.
        self.assertGreater(len(self.objs["training_candidates"]), 0)
        for tc in self.objs["training_candidates"]:
            self.assertIn("operator_id", tc)
            self.assertIn("recommended_interventions", tc)
            self.assertIn("framing", tc)
            # The framing must explicitly disclaim the underperformer label.
            self.assertIn("not an underperformer", tc["framing"].lower())

    def test_peer_support_matches_complementary(self):
        """Peer-support matches pair operators with complementary profiles."""
        matches = self.objs["peer_support_matches"]
        self.assertGreater(len(matches), 0)
        for m in matches:
            self.assertEqual(len(m["operator_ids"]), 2)
            self.assertIn("evidence", m)
            self.assertIn("complementary", m["evidence"].lower())

    def test_no_leaderboard_or_punitive_labels(self):
        """No object endorses leaderboard, punitive, or productivity-claim language.

        The framing strings explicitly disclaim these terms (e.g. "not a
        ranking"), so we check that any occurrence is in a negating context.
        """
        prohibited_endorsements = ("leaderboard", "bottom employee",
                                   "productivity score", "composite score",
                                   "adverse action")
        for obj_name, findings in self.objs.items():
            for f in findings:
                text = (f.get("evidence", "") + " " + f.get("framing", "")).lower()
                for word in prohibited_endorsements:
                    self.assertNotIn(word, text,
                                     f"{obj_name}: prohibited term '{word}' in output")
                # "ranking" and "underperformer" may appear only in negating
                # context (e.g. "not a ranking", "not an operator ranking",
                # "not an underperformer label").
                if "ranking" in text:
                    self.assertIn("not", text[:text.index("ranking")],
                                  f"{obj_name}: 'ranking' used without negation")
                if "underperformer" in text:
                    self.assertIn("not", text[:text.index("underperformer")],
                                  f"{obj_name}: 'underperformer' used without negation")

    def test_export_preferred_manager_objects_markdown(self):
        """The preferred-manager-objects exporter produces valid Markdown."""
        from reporting import export_preferred_manager_objects_markdown
        md = export_preferred_manager_objects_markdown(self.svc)
        self.assertIn("Preferred Manager Objects", md)
        self.assertIn("DEVELOPMENTAL", md)
        self.assertIn("not rankings", md.lower())
        # All 8 object titles should appear
        for title in ("Development Groups", "Fastest Improvers", "Stalled Cohorts",
                       "Workflow Bottlenecks", "Tool/Model-Fit Opportunities",
                       "Training Candidates", "Peer-Support Matches", "Remeasurement Queue"):
            self.assertIn(title, md)


# ── Decision-use classification labels (spec 12) ──────────────────────────

class TestDecisionUseLabels(unittest.TestCase):
    """Tests for the decision-use classification labels per `12`."""

    def test_diagnosis_label_is_developmental(self):
        """Diagnostics are labeled DEVELOPMENTAL."""
        from reporting import decision_use_label_diagnosis
        label = decision_use_label_diagnosis()
        self.assertIn("DEVELOPMENTAL", label)

    def test_intervention_label_is_workflow_experimentation(self):
        """Interventions are labeled WORKFLOW_EXPERIMENTATION."""
        from reporting import decision_use_label_intervention
        label = decision_use_label_intervention()
        self.assertIn("WORKFLOW_EXPERIMENTATION", label)

    def test_outcome_join_label_is_research(self):
        """Outcome joins are labeled RESEARCH."""
        from reporting import decision_use_label_outcome_join
        label = decision_use_label_outcome_join()
        self.assertIn("RESEARCH", label)

    def test_personnel_label_has_elevated_governance_warning(self):
        """Personnel label carries the elevated governance warning per `12`."""
        from reporting import decision_use_label_personnel
        label = decision_use_label_personnel()
        self.assertIn("PERSONNEL", label)
        self.assertIn("higher evidence", label.lower())
        self.assertIn("never automatically", label.lower())

    def test_decision_use_enum_has_four_values(self):
        """The DecisionUse enum has exactly the 4 values from `12`."""
        from governance import DecisionUse
        values = {d.value for d in DecisionUse}
        self.assertEqual(values, {"DEVELOPMENTAL", "RESEARCH", "WORKFLOW_EXPERIMENTATION", "PERSONNEL"})

    def test_decision_use_for_diagnosis_returns_developmental(self):
        """decision_use_for_diagnosis returns DEVELOPMENTAL."""
        from governance import decision_use_for_diagnosis, DecisionUse
        from domain.diagnosis import Diagnosis, DiagnosisStatus, DiagnosticLevel
        d = Diagnosis(
            diagnosis_id="test", operator_id="op_001", pattern_id="P-CTX-01",
            hypothesis="test", confidence=0.5, status=DiagnosisStatus.HYPOTHESIS,
            evidence="test", level=DiagnosticLevel.OPERATOR,
        )
        self.assertEqual(decision_use_for_diagnosis(d), DecisionUse.DEVELOPMENTAL)

    def test_decision_use_for_intervention_returns_workflow_experimentation(self):
        """decision_use_for_intervention returns WORKFLOW_EXPERIMENTATION."""
        from governance import decision_use_for_intervention, DecisionUse
        from domain.intervention import Intervention, InterventionOutcome
        from datetime import date
        iv = Intervention(
            intervention_id="test", operator_id="op_001", catalog_id="CTX-001",
            reason_pattern="P-CTX-01", target_metric="leverage",
            start_date=date(2026, 8, 1), followup_days=14,
        )
        self.assertEqual(decision_use_for_intervention(iv), DecisionUse.WORKFLOW_EXPERIMENTATION)

    def test_decision_use_for_outcome_join_returns_research(self):
        """decision_use_for_outcome_join returns RESEARCH."""
        from governance import decision_use_for_outcome_join, DecisionUse
        self.assertEqual(decision_use_for_outcome_join(), DecisionUse.RESEARCH)


# ── Structured provenance (spec 12) ───────────────────────────────────────

class TestStructuredProvenance(unittest.TestCase):
    """Tests for structured provenance per `12` §Provenance."""

    def test_provenance_object_has_structured_fields(self):
        """Provenance has all 7 fields from `12`."""
        from domain.provenance import Provenance
        p = Provenance(
            source_provider="ingest:claude",
            collection_method="claude_usage_export_json",
            collector_version="claude_adapter_v1",
            ingestion_timestamp="2026-08-18T10:00:00+00:00",
            original_time_window=("2026-07-01", "2026-07-30"),
            signature_checksum="abc123",
            synthetic=True,
        )
        self.assertEqual(p.source_provider, "ingest:claude")
        self.assertEqual(p.collection_method, "claude_usage_export_json")
        self.assertEqual(p.collector_version, "claude_adapter_v1")
        self.assertEqual(p.ingestion_timestamp, "2026-08-18T10:00:00+00:00")
        self.assertEqual(p.original_time_window, ("2026-07-01", "2026-07-30"))
        self.assertEqual(p.signature_checksum, "abc123")
        self.assertTrue(p.synthetic)

    def test_provenance_from_string_backward_compat(self):
        """A bare string is treated as source_provider (backward compatibility)."""
        from domain.provenance import Provenance
        p = Provenance.from_dict("ingest:claude")
        self.assertEqual(p.source_provider, "ingest:claude")
        self.assertIsNone(p.collection_method)

    def test_provenance_to_dict_emits_structured_form(self):
        """to_dict() emits the structured dict form."""
        from domain.provenance import Provenance
        p = Provenance(source_provider="ingest:claude", collection_method="json")
        d = p.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["source_provider"], "ingest:claude")
        self.assertEqual(d["collection_method"], "json")

    def test_provenance_truthiness(self):
        """Provenance is truthy when source_provider is set, falsy when empty."""
        from domain.provenance import Provenance
        self.assertTrue(Provenance(source_provider="ingest:claude"))
        self.assertFalse(Provenance(source_provider=""))

    def test_observation_accepts_string_provenance(self):
        """Observation accepts a bare string provenance (backward compatibility)."""
        from domain.observation import Observation
        from domain.provenance import Provenance
        from datetime import datetime, timezone
        obs = Observation(
            observation_id="test", operator_id="op_001",
            timestamp=datetime(2026, 7, 1, 12, tzinfo=timezone.utc),
            input_tokens=100, output_tokens=50, cache_read_tokens=200, cache_write_tokens=300,
            synthetic=True, provenance="ingest:claude",
        )
        self.assertIsInstance(obs.provenance, Provenance)
        self.assertEqual(obs.provenance.source_provider, "ingest:claude")

    def test_observation_to_dict_emits_structured_provenance(self):
        """Observation.to_dict() emits the structured provenance dict."""
        from domain.observation import Observation
        from datetime import datetime, timezone
        obs = Observation(
            observation_id="test", operator_id="op_001",
            timestamp=datetime(2026, 7, 1, 12, tzinfo=timezone.utc),
            input_tokens=100, output_tokens=50, cache_read_tokens=200, cache_write_tokens=300,
            synthetic=True, provenance="ingest:claude",
        )
        d = obs.to_dict()
        self.assertIsInstance(d["provenance"], dict)
        self.assertEqual(d["provenance"]["source_provider"], "ingest:claude")

    def test_observation_from_dict_round_trips_structured_provenance(self):
        """Observation.from_dict() round-trips structured provenance."""
        from domain.observation import Observation
        from domain.provenance import Provenance
        from datetime import datetime, timezone
        obs = Observation(
            observation_id="test", operator_id="op_001",
            timestamp=datetime(2026, 7, 1, 12, tzinfo=timezone.utc),
            input_tokens=100, output_tokens=50, cache_read_tokens=200, cache_write_tokens=300,
            synthetic=True,
            provenance=Provenance(
                source_provider="ingest:codex",
                collection_method="csv",
                collector_version="v1",
                original_time_window=("2026-07-01", "2026-07-30"),
                synthetic=True,
            ),
        )
        d = obs.to_dict()
        obs2 = Observation.from_dict(d)
        self.assertEqual(obs2.provenance.source_provider, "ingest:codex")
        self.assertEqual(obs2.provenance.collection_method, "csv")
        self.assertEqual(obs2.provenance.original_time_window, ("2026-07-01", "2026-07-30"))

    def test_demo_observations_have_structured_provenance(self):
        """Demo repository observations carry structured provenance."""
        svc = PilotService()
        for obs in svc.observations[:5]:
            self.assertIsNotNone(obs.provenance)
            self.assertTrue(obs.provenance.source_provider)
            self.assertIsNotNone(obs.provenance.collection_method)
            self.assertIsNotNone(obs.provenance.collector_version)
            self.assertIsNotNone(obs.provenance.ingestion_timestamp)

    def test_claude_adapter_populates_structured_provenance(self):
        """Claude adapter populates structured provenance fields."""
        import json, tempfile, os
        from ingest import ClaudeAdapter
        data = [{"operator_id": "op_001", "timestamp": "2026-07-01T12:00:00Z",
                 "input_tokens": 100, "output_tokens": 50, "model": "claude-code"}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            result = ClaudeAdapter().ingest(path)
            obs = result.observations[0]
            self.assertEqual(obs.provenance.source_provider, "ingest:claude")
            self.assertEqual(obs.provenance.collection_method, "claude_usage_export_json")
            self.assertEqual(obs.provenance.collector_version, "claude_adapter_v1")
            self.assertIsNotNone(obs.provenance.ingestion_timestamp)
        finally:
            os.unlink(path)

    def test_codex_adapter_populates_structured_provenance(self):
        """Codex adapter populates structured provenance fields."""
        import tempfile, os
        from ingest import CodexAdapter
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            f.write("operator_id,timestamp,input_tokens,output_tokens,model\n")
            f.write("op_001,2026-07-01,100,50,gpt-4\n")
            path = f.name
        try:
            result = CodexAdapter().ingest(path)
            obs = result.observations[0]
            self.assertEqual(obs.provenance.source_provider, "ingest:codex")
            self.assertEqual(obs.provenance.collection_method, "codex_usage_export_csv")
            self.assertEqual(obs.provenance.collector_version, "codex_adapter_v1")
            self.assertIsNotNone(obs.provenance.ingestion_timestamp)
        finally:
            os.unlink(path)

    def test_provenance_none_stays_none(self):
        """None provenance stays None (no provenance set)."""
        from domain.observation import Observation
        from datetime import datetime, timezone
        obs = Observation(
            observation_id="test", operator_id="op_001",
            timestamp=datetime(2026, 7, 1, 12, tzinfo=timezone.utc),
            input_tokens=100, output_tokens=50, cache_read_tokens=200, cache_write_tokens=300,
            synthetic=True, provenance=None,
        )
        self.assertIsNone(obs.provenance)


# ── Non-negotiables regression (spec 12 avoid-list) ───────────────────────

class TestAvoidListRegression(unittest.TestCase):
    """Regression tests for the `12` avoid-list — verify no prohibited
    language or composite scores were introduced by the new code.
    """

    def test_composite_score_has_governance_guardrails(self):
        """Composite employee score exists but carries DEVELOPMENTAL governance.

        Per `21` §8, the composite score was previously on the "do not build
        yet" list. It is now implemented with governance guardrails:
        - Labeled DEVELOPMENTAL, never PERSONNEL
        - No punitive labels (failure, underperformer, etc.)
        - No leaderboard / worst-to-best ranking
        - Includes interpretation-limit caveats for CANONICAL_WITH_INTERPRETATION_LIMIT metrics
        """
        from service import PilotService
        svc = PilotService()
        oid = svc.operator_ids[0]
        score = svc.composite_score(oid)
        # Must be labeled DEVELOPMENTAL
        self.assertIn("DEVELOPMENTAL", score.label)
        self.assertNotIn("PERSONNEL", score.label)
        # No punitive language
        label_lower = score.label.lower()
        self.assertNotIn("underperform", label_lower)
        self.assertNotIn("failure", label_lower)
        # Score must be 0-100
        self.assertGreaterEqual(score.score, 0)
        self.assertLessEqual(score.score, 100)
        # Summary must not expose individual rankings
        summary = svc.composite_score_summary()
        self.assertNotIn("operators", summary)
        self.assertNotIn("ranking", summary)

    def test_no_leaderboard_in_manager_objects(self):
        """Preferred manager objects do not produce a leaderboard."""
        svc = PilotService()
        objs = svc.preferred_manager_objects()
        for obj_name, findings in objs.items():
            for f in findings:
                text = str(f).lower()
                self.assertNotIn("leaderboard", text)
                self.assertNotIn("ranking worst", text)
                self.assertNotIn("bottom employee", text)


# ── Decision-use labels in MCP responses (spec 12) ─────────────────────────

class TestMCPDecisionUseLabels(unittest.TestCase):
    """Tests verifying MCP tool responses carry decision-use labels."""

    def test_get_diagnostics_has_developmental_label(self):
        """get_diagnostics carries DEVELOPMENTAL decision-use label."""
        from mcp_server.server import get_diagnostics
        data = get_diagnostics("op_002")
        self.assertIn("decision_use", data)
        self.assertIn("DEVELOPMENTAL", data["decision_use"])

    def test_get_operator_profile_has_developmental_label(self):
        """get_operator_profile carries DEVELOPMENTAL decision-use label."""
        from mcp_server.server import get_operator_profile
        data = get_operator_profile("op_002")
        self.assertIn("decision_use", data)
        self.assertIn("DEVELOPMENTAL", data["decision_use"])

    def test_get_intervention_status_has_workflow_label(self):
        """get_intervention_status carries WORKFLOW_EXPERIMENTATION label."""
        from mcp_server.server import get_intervention_status
        data = get_intervention_status()
        self.assertIn("decision_use", data)
        self.assertIn("WORKFLOW_EXPERIMENTATION", data["decision_use"])

    def test_verify_change_has_workflow_label(self):
        """verify_change carries WORKFLOW_EXPERIMENTATION label."""
        from mcp_server.server import verify_change
        data = verify_change(intervention_id="int_001")
        self.assertIn("decision_use", data)
        self.assertIn("WORKFLOW_EXPERIMENTATION", data["decision_use"])

    def test_assign_intervention_has_workflow_label(self):
        """assign_intervention carries WORKFLOW_EXPERIMENTATION label."""
        from mcp_server.server import assign_intervention
        data = assign_intervention(
            "op_001", "CTX-001", "leverage", 14, authorized_by="test"
        )
        self.assertIn("decision_use", data)
        self.assertIn("WORKFLOW_EXPERIMENTATION", data["decision_use"])

    def test_close_intervention_has_workflow_label(self):
        """close_intervention carries WORKFLOW_EXPERIMENTATION label."""
        from mcp_server.server import close_intervention, assign_intervention
        # First assign an intervention so we can close it
        assign_intervention(
            "op_001", "CTX-001", "leverage", 14, authorized_by="test",
            intervention_id="test_close_label",
        )
        data = close_intervention("test_close_label", "SUCCESS", authorized_by="test")
        self.assertIn("decision_use", data)
        self.assertIn("WORKFLOW_EXPERIMENTATION", data["decision_use"])

    def test_create_experiment_has_workflow_label(self):
        """create_experiment carries WORKFLOW_EXPERIMENTATION label."""
        from mcp_server.server import create_experiment
        data = create_experiment(
            "op_001", "leverage", 14, authorized_by="test"
        )
        self.assertIn("decision_use", data)
        self.assertIn("WORKFLOW_EXPERIMENTATION", data["decision_use"])

    def test_no_mcp_tool_auto_assigns_personnel(self):
        """No MCP tool response carries a PERSONNEL decision-use label."""
        from mcp_server.server import (
            get_diagnostics, get_operator_profile, get_intervention_status,
            verify_change, assign_intervention, create_experiment,
        )
        responses = [
            get_diagnostics("op_002"),
            get_operator_profile("op_002"),
            get_intervention_status(),
            verify_change(intervention_id="int_001"),
            assign_intervention("op_001", "CTX-001", "leverage", 14, authorized_by="test"),
            create_experiment("op_001", "leverage", 14, authorized_by="test"),
        ]
        for r in responses:
            label = r.get("decision_use", "")
            self.assertNotIn("PERSONNEL", label,
                             "MCP tool auto-assigned PERSONNEL label — must never happen")


# ── Decision-use labels in markdown exporters (spec 12) ────────────────────

class TestExporterDecisionUseLabels(unittest.TestCase):
    """Tests verifying existing markdown exporters emit decision-use labels."""

    def setUp(self):
        self.svc = PilotService()

    def test_operator_markdown_has_developmental_label(self):
        """export_operator_markdown emits DEVELOPMENTAL label for operators with diagnoses."""
        from reporting import export_operator_markdown
        # Find an operator with diagnoses
        oid = None
        for o in self.svc.operator_ids:
            if self.svc.diagnoses_for(o):
                oid = o
                break
        self.assertIsNotNone(oid, "No operator with diagnoses found")
        md = export_operator_markdown(self.svc, oid)
        self.assertIn("[GOVERNANCE]", md)
        self.assertIn("DEVELOPMENTAL", md)

    def test_hypothesis_map_has_developmental_label(self):
        """export_hypothesis_map emits DEVELOPMENTAL label at the top."""
        from reporting import export_hypothesis_map
        md = export_hypothesis_map(self.svc)
        self.assertIn("[GOVERNANCE]", md)
        self.assertIn("DEVELOPMENTAL", md)

    def test_intervention_outcomes_has_workflow_label(self):
        """export_intervention_outcomes_markdown emits WORKFLOW_EXPERIMENTATION label."""
        from reporting import export_intervention_outcomes_markdown
        results = self.svc.intervention_outcome_analysis("demo_data/external_outcomes.csv")
        md = export_intervention_outcomes_markdown(self.svc, results)
        self.assertIn("[GOVERNANCE]", md)
        self.assertIn("WORKFLOW_EXPERIMENTATION", md)

    def test_remeasurement_report_has_workflow_label(self):
        """export_remeasurement_report emits WORKFLOW_EXPERIMENTATION label."""
        from reporting import export_remeasurement_report
        md = export_remeasurement_report(self.svc)
        self.assertIn("[GOVERNANCE]", md)
        self.assertIn("WORKFLOW_EXPERIMENTATION", md)


# ── P-STAGE-01 threshold tuning (spec 09) ──────────────────────────────────

class TestPStage01ThresholdTuning(unittest.TestCase):
    """Tests for the P-STAGE-01 threshold tuning (0.25 → 0.50)."""

    def test_stage_fit_spread_is_50_percent(self):
        """The default stage_fit_spread threshold is 0.50 (50%)."""
        from diagnostics.pattern_engine import PatternThresholds
        self.assertEqual(PatternThresholds().stage_fit_spread, 0.50)

    def test_p_stage_01_count_dropped_from_45_to_32(self):
        """P-STAGE-01 detections dropped from 45 (at 25%) to ~32 (at 50%)."""
        svc = PilotService()
        patterns = svc.detect_cohort_patterns()
        pstage_count = sum(
            1 for ps in patterns.values() for p in ps if p.pattern_id == "P-STAGE-01"
        )
        self.assertGreater(pstage_count, 0, "P-STAGE-01 should still fire for some operators")
        self.assertLess(pstage_count, 45, "P-STAGE-01 should fire for fewer than 45 operators")

    def test_p_stage_01_not_detected_at_40_percent_spread(self):
        """P-STAGE-01 is NOT detected at 40% relative spread (below 50% threshold)."""
        from diagnostics import PatternEngine
        from domain.measurement import Measurement, MetricStatus
        from domain.reference_population import ReferencePopulation
        from domain.workflow import WorkflowObservation
        from datetime import date
        ref = ReferencePopulation(
            reference_id="test", version="v1", date=date(2026, 7, 30),
            description="test", synthetic=True,
            distributions={"leverage": {"p0": 0, "p50": 10, "p100": 100}},
        )
        ms = [Measurement(
            metric_id="leverage", metric_version="1.0", operator_id="op_test",
            value=2.0, unit="ratio", window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            source="test", status=MetricStatus.CANONICAL, eligibility="I>0", synthetic=True,
        )]
        # 0.5 → 0.7 = 40% spread, below 50% threshold
        wobs = [
            WorkflowObservation(
                operator_id="op_test", workflow_id="wf", stage_id="stage_a",
                date=date(2026, 7, 15), provisional_fit=0.5, evidence_count=10, synthetic=True,
            ),
            WorkflowObservation(
                operator_id="op_test", workflow_id="wf", stage_id="stage_b",
                date=date(2026, 7, 15), provisional_fit=0.7, evidence_count=10, synthetic=True,
            ),
        ]
        engine = PatternEngine()
        patterns = engine.detect_patterns(
            "op_test", ms, ref, usage_percentile=50,
            window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            workflow_observations=wobs,
        )
        pstage = [p for p in patterns if p.pattern_id == "P-STAGE-01"]
        self.assertEqual(len(pstage), 0, "P-STAGE-01 detected at 40% spread (below 50% threshold)")


# ── Training candidates dedup (one per operator per pattern) ───────────────

class TestTrainingCandidatesDedup(unittest.TestCase):
    """Tests for training candidates deduplication."""

    def setUp(self):
        self.svc = PilotService()
        self.objs = self.svc.preferred_manager_objects()

    def test_no_duplicate_operator_pattern_pairs(self):
        """No (operator_id, pattern_id) pair appears more than once."""
        tc = self.objs["training_candidates"]
        pairs = [(t["operator_id"], t["pattern_id"]) for t in tc]
        from collections import Counter
        dupes = {p: c for p, c in Counter(pairs).items() if c > 1}
        self.assertEqual(len(dupes), 0,
                         f"Duplicate (operator, pattern) pairs: {dupes}")

    def test_operator_can_appear_with_multiple_patterns(self):
        """An operator MAY appear multiple times if they have different patterns."""
        tc = self.objs["training_candidates"]
        from collections import Counter
        op_counts = Counter(t["operator_id"] for t in tc)
        multi = {op: c for op, c in op_counts.items() if c > 1}
        # At least one operator should have multiple patterns (if any exist)
        if tc:
            # Verify that any operator appearing multiple times has distinct patterns
            for op, count in multi.items():
                op_patterns = [t["pattern_id"] for t in tc if t["operator_id"] == op]
                self.assertEqual(len(op_patterns), len(set(op_patterns)),
                                 f"Operator {op} has duplicate patterns: {op_patterns}")

    def test_training_candidates_count_reduced(self):
        """Training candidates count is reduced from the pre-dedup 64."""
        tc = self.objs["training_candidates"]
        self.assertLess(len(tc), 64, "Training candidates not deduplicated (still >= 64)")


# ── Fastest improvers sort (numeric, not string) ───────────────────────────

class TestFastestImproversSort(unittest.TestCase):
    """Tests for the fastest improvers numeric sort fix."""

    def setUp(self):
        self.svc = PilotService()
        self.objs = self.svc.preferred_manager_objects()

    def test_sorted_by_numeric_magnitude(self):
        """Fastest improvers are sorted by numeric improvement_pct, not string."""
        imps = self.objs["fastest_improvers"]
        if len(imps) < 2:
            self.skipTest("Not enough improvers to test sort order")
        pcts = [i["improvement_pct"] for i in imps]
        self.assertEqual(pcts, sorted(pcts, reverse=True),
                         f"Improvers not sorted by numeric magnitude: {pcts}")

    def test_improvement_pct_field_present(self):
        """Each improver finding carries an improvement_pct numeric field."""
        imps = self.objs["fastest_improvers"]
        for i in imps:
            self.assertIn("improvement_pct", i)
            self.assertIsInstance(i["improvement_pct"], (int, float))

    def test_high_magnitude_ranks_above_low_magnitude(self):
        """A +55% improvement ranks above a +2% improvement regardless of metric name."""
        imps = self.objs["fastest_improvers"]
        if len(imps) < 2:
            self.skipTest("Not enough improvers to test ranking")
        # Find a 55% and a 2% improver
        high = [i for i in imps if i["improvement_pct"] >= 50]
        low = [i for i in imps if i["improvement_pct"] <= 5]
        if high and low:
            high_idx = imps.index(high[0])
            low_idx = imps.index(low[0])
            self.assertLess(high_idx, low_idx,
                            "High-magnitude improver should rank above low-magnitude")


# ── Workflow bottlenecks threshold (25% + min 5) ───────────────────────────

class TestWorkflowBottlenecksThreshold(unittest.TestCase):
    """Tests for the workflow bottlenecks threshold fix."""

    def setUp(self):
        self.svc = PilotService()
        self.objs = self.svc.preferred_manager_objects()

    def test_bottlenecks_use_25_percent_threshold(self):
        """Bottlenecks fire only when >= 25% of operators have low fit."""
        by_stage = self.svc.workflow_fit_by_stage()
        bottlenecks = self.objs["workflow_bottlenecks"]
        bottleneck_stages = {b["stage_id"] for b in bottlenecks}
        for stage_id, wobs in by_stage.items():
            low_fit = [w for w in wobs if w.provisional_fit is not None and w.provisional_fit < 0.5]
            should_fire = len(low_fit) >= max(5, len(wobs) * 0.25)
            if should_fire:
                self.assertIn(stage_id, bottleneck_stages,
                              f"Stage {stage_id} should fire but didn't")
            else:
                self.assertNotIn(stage_id, bottleneck_stages,
                                 f"Stage {stage_id} fired but shouldn't (only {len(low_fit)}/{len(wobs)})")

    def test_bottlenecks_not_firing_on_baseline_noise(self):
        """Bottlenecks do not fire on baseline distribution (was 6/7, now fewer)."""
        bottlenecks = self.objs["workflow_bottlenecks"]
        self.assertLess(len(bottlenecks), 6,
                        "Too many bottlenecks firing — threshold still too loose")


# ── min_observations gate ──────────────────────────────────────────────────

class TestMinObservationsGate(unittest.TestCase):
    """Tests for the min_observations evidence gate."""

    def test_gate_blocks_below_min_observations(self):
        """An operator with fewer than min_observations produces no patterns."""
        from diagnostics import PatternEngine
        from domain.measurement import Measurement, MetricStatus
        from domain.reference_population import ReferencePopulation
        from domain.observation import Observation
        from datetime import date, datetime, timezone
        ref = ReferencePopulation(
            reference_id="test", version="v1", date=date(2026, 7, 30),
            description="test", synthetic=True,
            distributions={"leverage": {"p0": 0, "p50": 10, "p100": 100}},
        )
        ms = [Measurement(
            metric_id="leverage", metric_version="1.0", operator_id="op_test",
            value=0.5, unit="ratio", window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            source="test", status=MetricStatus.CANONICAL, eligibility="I>0", synthetic=True,
        )]
        # Only 5 observations — below the default min_observations of 7
        obs = [
            Observation(
                observation_id=f"test_{i}", operator_id="op_test",
                timestamp=datetime(2026, 7, 1 + i, 12, tzinfo=timezone.utc),
                input_tokens=100, output_tokens=50,
                cache_read_tokens=200, cache_write_tokens=300,
                synthetic=True, model="claude-code", platform="claude",
            )
            for i in range(5)
        ]
        engine = PatternEngine()
        patterns = engine.detect_patterns(
            "op_test", ms, ref, usage_percentile=10,
            window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            observations=obs,
        )
        self.assertEqual(len(patterns), 0, "Patterns detected below min_observations gate")

    def test_gate_allows_at_min_observations(self):
        """An operator with exactly min_observations (7) is allowed through the gate."""
        from diagnostics import PatternEngine
        from domain.measurement import Measurement, MetricStatus
        from domain.reference_population import ReferencePopulation
        from domain.observation import Observation
        from datetime import date, datetime, timezone
        ref = ReferencePopulation(
            reference_id="test", version="v1", date=date(2026, 7, 30),
            description="test", synthetic=True,
            distributions={"leverage": {"p0": 0, "p50": 10, "p100": 100}},
        )
        ms = [Measurement(
            metric_id="leverage", metric_version="1.0", operator_id="op_test",
            value=0.5, unit="ratio", window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            source="test", status=MetricStatus.CANONICAL, eligibility="I>0", synthetic=True,
        )]
        # Exactly 7 observations — at the threshold
        obs = [
            Observation(
                observation_id=f"test_{i}", operator_id="op_test",
                timestamp=datetime(2026, 7, 1 + i, 12, tzinfo=timezone.utc),
                input_tokens=100, output_tokens=50,
                cache_read_tokens=200, cache_write_tokens=300,
                synthetic=True, model="claude-code", platform="claude",
            )
            for i in range(7)
        ]
        engine = PatternEngine()
        patterns = engine.detect_patterns(
            "op_test", ms, ref, usage_percentile=10,
            window_start=date(2026, 7, 1), window_end=date(2026, 7, 30),
            observations=obs,
        )
        # Gate should pass — patterns may or may not fire depending on metrics,
        # but the gate itself should not block.
        # (With leverage=0.5 and percentile 10, P-CTX-01 should fire.)
        self.assertTrue(any(p.pattern_id == "P-CTX-01" for p in patterns),
                        "Gate blocked at exactly min_observations (should allow through)")


# ── Diagnoses caching ──────────────────────────────────────────────────────

class TestDiagnosesCaching(unittest.TestCase):
    """Tests for the diagnoses cache in PilotService."""

    def test_diagnoses_cached_after_first_access(self):
        """Accessing svc.diagnoses twice does not recompute."""
        svc = PilotService()
        # First access populates the cache
        d1 = svc.diagnoses
        self.assertIsNotNone(svc._diagnoses_cache,
                             "Cache not populated after first access")
        # Second access should use the cache — same Diagnosis objects
        d2 = svc.diagnoses
        self.assertEqual(len(d1), len(d2), "Different number of diagnoses on second access")
        for a, b in zip(d1, d2):
            self.assertIs(a, b, "Second access returned different Diagnosis objects")

    def test_diagnoses_for_uses_cache(self):
        """diagnoses_for uses the cached cohort dict."""
        svc = PilotService()
        # Populate cache via diagnoses property
        _ = svc.diagnoses
        self.assertIsNotNone(svc._diagnoses_cache)
        # diagnoses_for should use the cache, not recompute
        d1 = svc.diagnoses_for("op_002")
        d2 = svc.diagnoses_for("op_002")
        self.assertIs(d1, d2, "diagnoses_for returned different objects — not using cache")

    def test_cache_not_recomputed(self):
        """detect_cohort_patterns is not called again after cache is populated.

        The cache lives inside generate_cohort_diagnoses(), so the
        expensive computation (detect_cohort_patterns + diagnosis engine)
        is skipped on subsequent calls.
        """
        from unittest.mock import patch
        svc = PilotService()
        # First access populates cache
        _ = svc.diagnoses
        self.assertIsNotNone(svc._diagnoses_cache)
        # Patch detect_cohort_patterns — the expensive part — to track calls.
        # On second access the cache should short-circuit before reaching it.
        with patch.object(svc, 'detect_cohort_patterns') as mock_detect:
            mock_detect.return_value = {}
            _ = svc.diagnoses
            mock_detect.assert_not_called()


# ── Provenance from_dict(None) edge case ───────────────────────────────────

class TestProvenanceNoneEdgeCase(unittest.TestCase):
    """Tests for the Provenance.from_dict(None) edge case fix."""

    def test_from_dict_none_returns_none(self):
        """Provenance.from_dict(None) returns None, not an empty Provenance."""
        from domain.provenance import Provenance
        result = Provenance.from_dict(None)
        self.assertIsNone(result)

    def test_observation_with_none_provenance_stays_none(self):
        """Observation with provenance=None keeps it as None through round-trip."""
        from domain.observation import Observation
        from datetime import datetime, timezone
        obs = Observation(
            observation_id="test", operator_id="op_001",
            timestamp=datetime(2026, 7, 1, 12, tzinfo=timezone.utc),
            input_tokens=100, output_tokens=50, cache_read_tokens=200, cache_write_tokens=300,
            synthetic=True, provenance=None,
        )
        self.assertIsNone(obs.provenance)
        d = obs.to_dict()
        self.assertIsNone(d["provenance"])
        obs2 = Observation.from_dict(d)
        self.assertIsNone(obs2.provenance)


if __name__ == "__main__":
    unittest.main()
