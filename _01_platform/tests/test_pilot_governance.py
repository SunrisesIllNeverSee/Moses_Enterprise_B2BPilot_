"""Tests for Pilot Mode governance lifecycle (T1.1–T1.6).

Covers:
    - PilotState enum and PilotStateMachine transitions
    - SuccessCriterion / SuccessCriteria schema + locking
    - GateRecord + evaluate_gate_1/2/3
    - DecisionRecord + create_decision_record
    - PilotRun control-plane object + PilotId validation
    - PilotConfiguration new fields (pilot_id, enterprise_name, etc.)
    - PilotService governance methods
    - CLI pilot governance commands
    - MCP governance tools
    - CanonicalReport (reporting invariant)
    - PDF reporting invariant (no static default)
"""
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from domain import (
    PilotState, PilotStateMachine, InvalidTransitionError,
    SuccessCriterion, SuccessCriteria, CriterionDirection, CriterionAggregation,
    CriterionTier, CriterionStatus, evaluate_criterion, evaluate_criteria,
    GateRecord, GateType, Gate1Outcome, Gate2Outcome, Gate3Outcome,
    ExtendRequirements, evaluate_gate_1, evaluate_gate_2, evaluate_gate_3,
    DecisionRecord, ClosureOutcome, ExtendPlan, ExpandPlan, DeployPlan,
    StopLessons, create_decision_record,
    PilotRun, Milestone, Blocker, validate_pilot_id, create_pilot_run,
    PilotConfiguration, EvalFamilySelection,
)
from service import PilotService
from mcp_server import call_tool_directly
from cli.main import main as cli_main
from reporting import build_canonical_report, render_canonical_markdown


class TestPilotState(unittest.TestCase):
    """Tests for PilotState enum and PilotStateMachine."""

    def test_all_nine_states_exist(self):
        states = [PilotState.DEFINED, PilotState.INSTRUMENTED, PilotState.BASELINED,
                  PilotState.DIAGNOSED, PilotState.INTERVENING, PilotState.VERIFYING,
                  PilotState.READOUT, PilotState.DECIDING, PilotState.TERMINATED]
        self.assertEqual(len(states), 9)

    def test_state_machine_starts_in_defined(self):
        sm = PilotStateMachine(pilot_id="ACME-001")
        self.assertEqual(sm.current_state, PilotState.DEFINED)

    def test_valid_forward_transition(self):
        sm = PilotStateMachine(pilot_id="ACME-001")
        sm.transition_to(PilotState.INSTRUMENTED)
        self.assertEqual(sm.current_state, PilotState.INSTRUMENTED)

    def test_invalid_skip_transition_raises(self):
        sm = PilotStateMachine(pilot_id="ACME-001")
        with self.assertRaises(InvalidTransitionError):
            sm.transition_to(PilotState.INTERVENING)  # skip 3 states

    def test_terminated_is_terminal(self):
        sm = PilotStateMachine(pilot_id="ACME-001", current_state=PilotState.TERMINATED)
        # No valid transitions from TERMINATED
        self.assertFalse(sm.can_transition_to(PilotState.DEFINED))
        self.assertFalse(sm.can_transition_to(PilotState.INSTRUMENTED))

    def test_history_is_recorded(self):
        sm = PilotStateMachine(pilot_id="ACME-001")
        sm.transition_to(PilotState.INSTRUMENTED, rationale="Telemetry collection started")
        sm.transition_to(PilotState.BASELINED, rationale="Baseline computed")
        self.assertEqual(len(sm.history), 2)
        self.assertEqual(sm.history[0].from_state, PilotState.DEFINED)
        self.assertEqual(sm.history[1].to_state, PilotState.BASELINED)

    def test_lifecycle_display(self):
        sm = PilotStateMachine(pilot_id="ACME-001", current_state=PilotState.DIAGNOSED)
        display = sm.lifecycle_display()
        self.assertEqual(len(display), 9)
        # DEFINED, INSTRUMENTED, BASELINED should be complete
        self.assertEqual(display[0]["status"], "complete")
        self.assertEqual(display[2]["status"], "complete")
        # DIAGNOSED should be current
        self.assertEqual(display[3]["status"], "current")
        # INTERVENING and beyond should be pending
        self.assertEqual(display[4]["status"], "pending")

    def test_state_machine_serialization(self):
        sm = PilotStateMachine(pilot_id="ACME-001")
        sm.transition_to(PilotState.INSTRUMENTED)
        d = sm.to_dict()
        sm2 = PilotStateMachine.from_dict(d)
        self.assertEqual(sm2.current_state, PilotState.INSTRUMENTED)
        self.assertEqual(len(sm2.history), 1)

    def test_checkpoint_and_resume(self):
        """Durable execution (HRN-010): checkpoint to disk, resume after crash."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            ckpt_path = f.name
        os.unlink(ckpt_path)  # remove so resume starts fresh
        try:
            # No checkpoint → fresh state machine
            sm = PilotStateMachine.resume(ckpt_path)
            self.assertEqual(sm.current_state, PilotState.DEFINED)
            # Transition with checkpoint
            sm.transition_to(PilotState.INSTRUMENTED, checkpoint_path=ckpt_path)
            sm.transition_to(PilotState.BASELINED, checkpoint_path=ckpt_path)
            self.assertEqual(sm.current_state, PilotState.BASELINED)
            # Simulate crash: resume from disk
            sm2 = PilotStateMachine.resume(ckpt_path)
            self.assertEqual(sm2.current_state, PilotState.BASELINED)
            self.assertEqual(len(sm2.history), 2)
            self.assertEqual(sm2.pilot_id, sm.pilot_id)
            # Continue from resumed state
            sm2.transition_to(PilotState.DIAGNOSED, checkpoint_path=ckpt_path)
            self.assertEqual(sm2.current_state, PilotState.DIAGNOSED)
            # Verify the resumed history carried forward
            sm3 = PilotStateMachine.resume(ckpt_path)
            self.assertEqual(len(sm3.history), 3)
            self.assertEqual(sm3.current_state, PilotState.DIAGNOSED)
        finally:
            if os.path.exists(ckpt_path):
                os.unlink(ckpt_path)

    def test_resume_nonexistent_returns_fresh(self):
        """Resume with no checkpoint file returns a fresh DEFINED state machine."""
        import tempfile
        ckpt = os.path.join(tempfile.gettempdir(), "nonexistent_ckpt_12345.json")
        self.assertFalse(os.path.exists(ckpt))
        sm = PilotStateMachine.resume(ckpt)
        self.assertEqual(sm.current_state, PilotState.DEFINED)

    def test_resume_corrupted_raises(self):
        """Resume with a corrupted checkpoint raises ValueError."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("{not valid json")
            ckpt_path = f.name
        try:
            with self.assertRaises(ValueError):
                PilotStateMachine.resume(ckpt_path)
        finally:
            os.unlink(ckpt_path)


class TestSuccessCriteria(unittest.TestCase):
    """Tests for SuccessCriterion, SuccessCriteria, and evaluation."""

    def _make_criterion(self, cid="SC-001", metric="eligible_fraction",
                        threshold=0.9, direction=CriterionDirection.at_least,
                        tolerance_band=0.0):
        return SuccessCriterion(
            criterion_id=cid, metric=metric, threshold=threshold,
            direction=direction, aggregation=CriterionAggregation.fraction,
            rationale="At least 90% usable cohort telemetry",
            tolerance_band=tolerance_band,
        )

    def test_criterion_serialization(self):
        c = self._make_criterion()
        d = c.to_dict()
        self.assertEqual(d["criterion_id"], "SC-001")
        self.assertEqual(d["direction"], "at_least")
        c2 = SuccessCriterion.from_dict(d)
        self.assertEqual(c2.criterion_id, c.criterion_id)
        self.assertEqual(c2.direction, c.direction)

    def test_criteria_unlocked_by_default(self):
        sc = SuccessCriteria.unlocked([self._make_criterion()])
        self.assertFalse(sc.is_locked)

    def test_lock_sets_timestamp(self):
        sc = SuccessCriteria.unlocked([self._make_criterion()])
        locked = sc.lock(locked_by="alice")
        self.assertTrue(locked.is_locked)
        self.assertEqual(locked.locked_by, "alice")
        self.assertTrue(locked.locked_at)

    def test_double_lock_raises(self):
        sc = SuccessCriteria.unlocked([self._make_criterion()])
        locked = sc.lock(locked_by="alice")
        with self.assertRaises(ValueError):
            locked.lock(locked_by="bob")

    def test_evaluate_met(self):
        c = self._make_criterion(threshold=0.9)
        result = evaluate_criterion(c, measured_value=0.95)
        self.assertEqual(result.status, CriterionStatus.MET)

    def test_evaluate_missed(self):
        c = self._make_criterion(threshold=0.9)
        result = evaluate_criterion(c, measured_value=0.5)
        self.assertEqual(result.status, CriterionStatus.MISSED)

    def test_evaluate_partial(self):
        c = self._make_criterion(threshold=0.9, tolerance_band=0.05)
        result = evaluate_criterion(c, measured_value=0.87)
        self.assertEqual(result.status, CriterionStatus.PARTIAL)

    def test_evaluate_not_evaluated(self):
        c = self._make_criterion()
        result = evaluate_criterion(c, measured_value=None)
        self.assertEqual(result.status, CriterionStatus.NOT_EVALUATED)

    def test_evaluate_criteria_requires_lock(self):
        sc = SuccessCriteria.unlocked([self._make_criterion()])
        with self.assertRaises(ValueError):
            evaluate_criteria(sc, {"SC-001": 0.95})

    def test_evaluate_criteria_aggregate(self):
        c1 = self._make_criterion("SC-001", threshold=0.9)
        c2 = self._make_criterion("SC-002", threshold=0.5)
        sc = SuccessCriteria.unlocked([c1, c2]).lock("alice")
        ev = evaluate_criteria(sc, {"SC-001": 0.95, "SC-002": 0.3})
        self.assertEqual(ev.met_count, 1)
        self.assertEqual(ev.missed_count, 1)
        self.assertFalse(ev.all_met)


class TestGateRecords(unittest.TestCase):
    """Tests for GateRecord and gate evaluation functions."""

    def test_gate_1_launch(self):
        record = evaluate_gate_1(
            pilot_id="ACME-001", evaluated_by="alice",
            charter_valid=True, success_criteria_locked=True,
            population_bounded=True, duration_bounded=True,
            governance_cleared=True, authorized=True,
        )
        self.assertEqual(record.outcome, Gate1Outcome.LAUNCH.value)
        self.assertEqual(record.gate_type, GateType.GATE_1_LAUNCH_READINESS)

    def test_gate_1_decline(self):
        record = evaluate_gate_1(
            pilot_id="ACME-001", evaluated_by="alice",
            charter_valid=False, success_criteria_locked=False,
            population_bounded=False, duration_bounded=False,
            governance_cleared=False, authorized=False,
        )
        self.assertEqual(record.outcome, Gate1Outcome.DECLINE.value)

    def test_gate_1_launch_with_conditions(self):
        record = evaluate_gate_1(
            pilot_id="ACME-001", evaluated_by="alice",
            charter_valid=True, success_criteria_locked=True,
            population_bounded=True, duration_bounded=True,
            governance_cleared=True, authorized=True,
            instrumentable=False,
            conditions=["Need to verify provider access"],
        )
        self.assertEqual(record.outcome, Gate1Outcome.LAUNCH_WITH_CONDITIONS.value)

    def test_gate_2_continue(self):
        record = evaluate_gate_2(
            pilot_id="ACME-001", evaluated_by="bob",
            data_sufficient=True, no_blocking_quality=True,
            participation_ok=True, governance_ok=True, protocol_ok=True,
        )
        self.assertEqual(record.outcome, Gate2Outcome.CONTINUE.value)

    def test_gate_2_terminate(self):
        record = evaluate_gate_2(
            pilot_id="ACME-001", evaluated_by="bob",
            data_sufficient=True, no_blocking_quality=True,
            participation_ok=True, governance_ok=False, protocol_ok=True,
        )
        self.assertEqual(record.outcome, Gate2Outcome.TERMINATE.value)

    def test_gate_3_deploy(self):
        c = SuccessCriterion("SC-001", "eligible_fraction", 0.9,
                             CriterionDirection.at_least, CriterionAggregation.fraction)
        sc = SuccessCriteria.unlocked([c]).lock("alice")
        ev = evaluate_criteria(sc, {"SC-001": 0.95})
        record = evaluate_gate_3(
            pilot_id="ACME-001", evaluated_by="carol",
            criteria_eval=ev,
        )
        self.assertEqual(record.outcome, Gate3Outcome.DEPLOY.value)

    def test_gate_3_stop(self):
        c1 = SuccessCriterion("SC-001", "metric_a", 0.9,
                              CriterionDirection.at_least, CriterionAggregation.fraction)
        c2 = SuccessCriterion("SC-002", "metric_b", 0.8,
                              CriterionDirection.at_least, CriterionAggregation.fraction)
        sc = SuccessCriteria.unlocked([c1, c2]).lock("alice")
        ev = evaluate_criteria(sc, {"SC-001": 0.3, "SC-002": 0.2})
        record = evaluate_gate_3(
            pilot_id="ACME-001", evaluated_by="carol",
            criteria_eval=ev,
        )
        self.assertEqual(record.outcome, Gate3Outcome.STOP.value)

    def test_gate_3_extend_requires_requirements(self):
        c1 = SuccessCriterion("SC-001", "metric_a", 0.9,
                              CriterionDirection.at_least, CriterionAggregation.fraction,
                              tolerance_band=0.1)
        c2 = SuccessCriterion("SC-002", "metric_b", 0.8,
                              CriterionDirection.at_least, CriterionAggregation.fraction,
                              tolerance_band=0.1)
        sc = SuccessCriteria.unlocked([c1, c2]).lock("alice")
        # Values within tolerance band → PARTIAL (not all MET, not majority MISSED)
        ev = evaluate_criteria(sc, {"SC-001": 0.85, "SC-002": 0.75})
        with self.assertRaises(ValueError):
            evaluate_gate_3(
                pilot_id="ACME-001", evaluated_by="carol",
                criteria_eval=ev,
            )

    def test_gate_3_extend_with_requirements(self):
        c1 = SuccessCriterion("SC-001", "metric_a", 0.9,
                              CriterionDirection.at_least, CriterionAggregation.fraction,
                              tolerance_band=0.1)
        c2 = SuccessCriterion("SC-002", "metric_b", 0.8,
                              CriterionDirection.at_least, CriterionAggregation.fraction,
                              tolerance_band=0.1)
        sc = SuccessCriteria.unlocked([c1, c2]).lock("alice")
        ev = evaluate_criteria(sc, {"SC-001": 0.85, "SC-002": 0.75})
        ext_req = ExtendRequirements(
            reason="Close but insufficient",
            missing_evidence="Need 2 more weeks of data",
            new_evidence_requirement="Continue telemetry collection",
            extension_period_days=14,
            new_closure_date="2026-10-15",
        )
        record = evaluate_gate_3(
            pilot_id="ACME-001", evaluated_by="carol",
            criteria_eval=ev, extend_requirements=ext_req,
        )
        self.assertEqual(record.outcome, Gate3Outcome.EXTEND.value)
        self.assertIsNotNone(record.extend_requirements)

    def test_gate_record_serialization(self):
        record = evaluate_gate_1(
            pilot_id="ACME-001", evaluated_by="alice",
            charter_valid=True, success_criteria_locked=True,
            population_bounded=True, duration_bounded=True,
            governance_cleared=True, authorized=True,
        )
        d = record.to_dict()
        r2 = GateRecord.from_dict(d)
        self.assertEqual(r2.gate_id, record.gate_id)
        self.assertEqual(r2.outcome, record.outcome)


class TestDecisionRecord(unittest.TestCase):
    """Tests for DecisionRecord and create_decision_record."""

    def test_stop_requires_lessons(self):
        with self.assertRaises(ValueError):
            create_decision_record(
                pilot_id="ACME-001",
                closure_outcome=ClosureOutcome.STOP,
                rationale="Did not meet criteria",
                decided_by="carol",
                gate_3_record_id="GATE3-ACME-001",
            )

    def test_stop_with_lessons(self):
        record = create_decision_record(
            pilot_id="ACME-001",
            closure_outcome=ClosureOutcome.STOP,
            rationale="Did not meet criteria",
            decided_by="carol",
            gate_3_record_id="GATE3-ACME-001",
            stop_lessons=StopLessons(
                key_findings="Low adoption",
                lessons_learned="Need better training",
                recommendation="Re-evaluate after training program",
            ),
        )
        self.assertEqual(record.closure_outcome, ClosureOutcome.STOP)
        self.assertTrue(record.immutable)
        self.assertIsNotNone(record.stop_lessons)

    def test_deploy_requires_plan(self):
        with self.assertRaises(ValueError):
            create_decision_record(
                pilot_id="ACME-001",
                closure_outcome=ClosureOutcome.DEPLOY,
                rationale="Met all criteria",
                decided_by="carol",
                gate_3_record_id="GATE3-ACME-001",
            )

    def test_deploy_with_plan(self):
        record = create_decision_record(
            pilot_id="ACME-001",
            closure_outcome=ClosureOutcome.DEPLOY,
            rationale="Met all criteria",
            decided_by="carol",
            gate_3_record_id="GATE3-ACME-001",
            deploy_plan=DeployPlan(
                production_transition="Move to production monitoring",
                owner="ops-team",
                timeline="30 days",
                monitoring_plan="Weekly health checks",
            ),
        )
        self.assertEqual(record.closure_outcome, ClosureOutcome.DEPLOY)
        self.assertIsNotNone(record.deploy_plan)

    def test_extend_requires_plan(self):
        with self.assertRaises(ValueError):
            create_decision_record(
                pilot_id="ACME-001",
                closure_outcome=ClosureOutcome.EXTEND,
                rationale="Need more data",
                decided_by="carol",
                gate_3_record_id="GATE3-ACME-001",
            )

    def test_decision_record_serialization(self):
        record = create_decision_record(
            pilot_id="ACME-001",
            closure_outcome=ClosureOutcome.STOP,
            rationale="Did not meet criteria",
            decided_by="carol",
            gate_3_record_id="GATE3-ACME-001",
            stop_lessons=StopLessons(
                key_findings="Low adoption",
                lessons_learned="Need better training",
                recommendation="Re-evaluate after training program",
            ),
        )
        d = record.to_dict()
        r2 = DecisionRecord.from_dict(d)
        self.assertEqual(r2.closure_outcome, ClosureOutcome.STOP)
        self.assertEqual(r2.stop_lessons.key_findings, "Low adoption")


class TestPilotRun(unittest.TestCase):
    """Tests for PilotRun, PilotId validation, and lifecycle."""

    def test_valid_pilot_id(self):
        self.assertEqual(validate_pilot_id("ACME-001"), "ACME-001")

    def test_invalid_pilot_id_lowercase(self):
        with self.assertRaises(ValueError):
            validate_pilot_id("acme-001")

    def test_invalid_pilot_id_no_dash(self):
        with self.assertRaises(ValueError):
            validate_pilot_id("ACME001")

    def test_invalid_pilot_id_wrong_digits(self):
        with self.assertRaises(ValueError):
            validate_pilot_id("ACME-01")

    def test_create_pilot_run(self):
        run = create_pilot_run(
            pilot_id="ACME-001",
            configuration_id="CONFIG-001",
            customer="Acme Corp",
            decision_owner="alice@acme.com",
            start_date="2026-09-01",
            target_end_date="2026-09-30",
            objectives="Measure AI workforce baseline",
        )
        self.assertEqual(run.pilot_id, "ACME-001")
        self.assertEqual(run.current_stage, PilotState.DEFINED)
        self.assertFalse(run.is_terminated)
        self.assertIsNone(run.final_decision)

    def test_add_milestone(self):
        run = create_pilot_run(
            pilot_id="ACME-001", configuration_id="CONFIG-001",
            customer="Acme", decision_owner="alice",
            start_date="2026-09-01", target_end_date="2026-09-30",
        )
        ms = run.add_milestone("INSTRUMENTED", "Telemetry collection complete")
        self.assertEqual(len(run.milestones), 1)
        self.assertEqual(ms.stage, "INSTRUMENTED")

    def test_add_and_resolve_blocker(self):
        run = create_pilot_run(
            pilot_id="ACME-001", configuration_id="CONFIG-001",
            customer="Acme", decision_owner="alice",
            start_date="2026-09-01", target_end_date="2026-09-30",
        )
        blk = run.add_blocker("Missing Claude export data")
        self.assertEqual(len(run.blockers), 1)
        self.assertFalse(blk.resolved)
        run.resolve_blocker(blk.blocker_id)
        self.assertTrue(run.blockers[0].resolved)

    def test_engagement_status(self):
        run = create_pilot_run(
            pilot_id="ACME-001", configuration_id="CONFIG-001",
            customer="Acme Corp", decision_owner="alice",
            start_date="2026-09-01", target_end_date="2026-09-30",
            objectives="Measure baseline",
        )
        status = run.engagement_status()
        self.assertEqual(status["pilot_id"], "ACME-001")
        self.assertEqual(status["customer"], "Acme Corp")
        self.assertEqual(status["current_stage"], "DEFINED")
        self.assertEqual(status["final_decision"], "PENDING")
        self.assertEqual(status["baseline"], "NOT_SET")

    def test_pilot_run_serialization(self):
        run = create_pilot_run(
            pilot_id="ACME-001", configuration_id="CONFIG-001",
            customer="Acme", decision_owner="alice",
            start_date="2026-09-01", target_end_date="2026-09-30",
            objectives="Test",
        )
        run.add_milestone("DEFINED", "Pilot created")
        d = run.to_dict()
        run2 = PilotRun.from_dict(d)
        self.assertEqual(run2.pilot_id, "ACME-001")
        self.assertEqual(len(run2.milestones), 1)


class TestPilotConfigurationNewFields(unittest.TestCase):
    """Tests for new PilotConfiguration fields."""

    def test_new_fields_default_empty(self):
        config = PilotConfiguration(
            config_id="CONFIG-001", mode="bespoke",
            eval_families=[EvalFamilySelection("EVAL-001")],
        )
        self.assertIsNone(config.pilot_id)
        self.assertEqual(config.enterprise_name, "")
        self.assertEqual(config.pilot_question, "")
        self.assertEqual(config.best_buyer, "")
        self.assertFalse(config.success_criteria.is_locked)

    def test_new_fields_serialization(self):
        config = PilotConfiguration(
            config_id="CONFIG-001", mode="bespoke",
            eval_families=[EvalFamilySelection("EVAL-001")],
            pilot_id="ACME-001",
            enterprise_name="Acme Corp",
            pilot_question="What does our AI workforce look like?",
            best_buyer="Head of AI",
        )
        d = config.to_dict()
        self.assertEqual(d["pilot_id"], "ACME-001")
        self.assertEqual(d["enterprise_name"], "Acme Corp")
        self.assertEqual(d["pilot_question"], "What does our AI workforce look like?")
        self.assertEqual(d["best_buyer"], "Head of AI")
        # Round-trip
        config2 = PilotConfiguration.from_dict(d)
        self.assertEqual(config2.pilot_id, "ACME-001")
        self.assertEqual(config2.enterprise_name, "Acme Corp")


class TestPilotServiceGovernance(unittest.TestCase):
    """Tests for PilotService governance methods."""

    def setUp(self):
        self.svc = PilotService()

    def test_no_active_pilot_by_default(self):
        self.assertIsNone(self.svc.pilot_run)

    def test_create_pilot(self):
        run = self.svc.create_pilot(
            pilot_id="ACME-001", configuration_id="CONFIG-001",
            customer="Acme", decision_owner="alice",
            start_date="2026-09-01", target_end_date="2026-09-30",
        )
        self.assertEqual(run.pilot_id, "ACME-001")
        self.assertEqual(self.svc.pilot_run.pilot_id, "ACME-001")

    def test_extended_status_includes_engagement(self):
        self.svc.create_pilot(
            pilot_id="ACME-001", configuration_id="CONFIG-001",
            customer="Acme", decision_owner="alice",
            start_date="2026-09-01", target_end_date="2026-09-30",
        )
        status = self.svc.get_pilot_status_extended()
        self.assertEqual(status["pilot_mode"], "active")
        self.assertEqual(status["pilot_id"], "ACME-001")
        self.assertIsNotNone(status["engagement_status"])

    def test_lock_success_criteria(self):
        self.svc.create_pilot(
            pilot_id="ACME-001", configuration_id="CONFIG-001",
            customer="Acme", decision_owner="alice",
            start_date="2026-09-01", target_end_date="2026-09-30",
        )
        criteria = [SuccessCriterion(
            "SC-001", "eligible_fraction", 0.9,
            CriterionDirection.at_least, CriterionAggregation.fraction,
        )]
        locked = self.svc.lock_success_criteria(criteria, locked_by="alice")
        self.assertTrue(locked.is_locked)
        self.assertTrue(self.svc.success_criteria.is_locked)

    def test_gate_evaluation_without_pilot_raises(self):
        with self.assertRaises(ValueError):
            self.svc.evaluate_pilot_gate_1(evaluated_by="alice")

    def test_full_lifecycle(self):
        """Test the full pilot lifecycle end-to-end."""
        self.svc.create_pilot(
            pilot_id="ACME-001", configuration_id="CONFIG-001",
            customer="Acme", decision_owner="alice",
            start_date="2026-09-01", target_end_date="2026-09-30",
            objectives="Measure AI workforce baseline",
        )
        # Lock success criteria
        criteria = [SuccessCriterion(
            "SC-001", "eligible_fraction", 0.9,
            CriterionDirection.at_least, CriterionAggregation.fraction,
            tolerance_band=0.05,
        )]
        self.svc.lock_success_criteria(criteria, locked_by="alice")

        # Gate 1 — Launch
        g1 = self.svc.evaluate_pilot_gate_1(evaluated_by="alice")
        self.assertEqual(g1.outcome, Gate1Outcome.LAUNCH.value)

        # Advance through stages
        self.svc.advance_pilot_stage(rationale="Telemetry collected")
        self.svc.advance_pilot_stage(rationale="Baseline computed")
        self.svc.advance_pilot_stage(rationale="Diagnosis complete")
        self.svc.advance_pilot_stage(gate_label="Gate 2: CONTINUE", rationale="Interventions assigned")

        # Gate 2 — Continue (need to be in INTERVENING)
        self.assertEqual(self.svc.pilot_run.current_stage, PilotState.INTERVENING)
        g2 = self.svc.evaluate_pilot_gate_2(evaluated_by="bob")
        self.assertEqual(g2.outcome, Gate2Outcome.CONTINUE.value)

        # Advance to DECIDING
        self.svc.advance_pilot_stage(gate_label="Gate 2: CONTINUE", rationale="Interventions complete")
        self.svc.advance_pilot_stage(rationale="Verification complete")
        self.svc.advance_pilot_stage(rationale="Readout generated")
        self.assertEqual(self.svc.pilot_run.current_stage, PilotState.DECIDING)

        # Gate 3 — Deploy (all criteria met)
        g3 = self.svc.evaluate_pilot_gate_3(
            evaluated_by="carol",
            measured_values={"SC-001": 0.95},
        )
        self.assertEqual(g3.outcome, Gate3Outcome.DEPLOY.value)

        # Create decision
        record = self.svc.create_pilot_decision(
            closure_outcome=ClosureOutcome.DEPLOY,
            rationale="All success criteria met",
            decided_by="carol",
            deploy_plan=DeployPlan(
                production_transition="Move to production",
                owner="ops-team",
                timeline="30 days",
                monitoring_plan="Weekly checks",
            ),
        )
        self.assertEqual(record.closure_outcome, ClosureOutcome.DEPLOY)
        self.assertEqual(self.svc.pilot_run.current_stage, PilotState.TERMINATED)
        self.assertEqual(self.svc.pilot_run.final_decision, "DEPLOY")


class TestMCPGovernanceTools(unittest.TestCase):
    """Tests for MCP governance tools."""

    def test_create_pilot_charter(self):
        result = call_tool_directly(
            "create_pilot_charter",
            pilot_id="ACME-001",
            configuration_id="CONFIG-001",
            customer="Acme",
            decision_owner="alice",
            start_date="2026-09-01",
            target_end_date="2026-09-30",
        )
        self.assertEqual(result["pilot_id"], "ACME-001")
        self.assertEqual(result["current_stage"], "DEFINED")

    def test_get_pilot_lifecycle(self):
        call_tool_directly(
            "create_pilot_charter",
            pilot_id="ACME-002",
            configuration_id="CONFIG-001",
            customer="Acme",
            decision_owner="alice",
            start_date="2026-09-01",
            target_end_date="2026-09-30",
        )
        result = call_tool_directly("get_pilot_lifecycle")
        self.assertEqual(result["pilot_id"], "ACME-002")
        self.assertEqual(result["current_state"], "DEFINED")

    def test_get_pilot_engagement(self):
        call_tool_directly(
            "create_pilot_charter",
            pilot_id="ACME-003",
            configuration_id="CONFIG-001",
            customer="Acme Corp",
            decision_owner="alice",
            start_date="2026-09-01",
            target_end_date="2026-09-30",
            objectives="Test pilot",
        )
        result = call_tool_directly("get_pilot_engagement")
        self.assertEqual(result["pilot_id"], "ACME-003")
        self.assertEqual(result["customer"], "Acme Corp")

    def test_lock_success_criteria(self):
        call_tool_directly(
            "create_pilot_charter",
            pilot_id="ACME-004",
            configuration_id="CONFIG-001",
            customer="Acme",
            decision_owner="alice",
            start_date="2026-09-01",
            target_end_date="2026-09-30",
        )
        result = call_tool_directly(
            "lock_success_criteria",
            criteria=[{
                "criterion_id": "SC-001",
                "metric": "eligible_fraction",
                "threshold": 0.9,
                "direction": "at_least",
                "aggregation": "fraction",
            }],
            locked_by="alice",
        )
        self.assertTrue(result["is_locked"])

    def test_get_canonical_report(self):
        result = call_tool_directly("get_canonical_report")
        self.assertIn("cohort_id", result)
        self.assertIn("observation_count", result)


class TestCanonicalReport(unittest.TestCase):
    """Tests for the canonical report model (reporting invariant)."""

    def test_build_canonical_report(self):
        svc = PilotService()
        report = build_canonical_report(svc)
        self.assertTrue(report.cohort_id)
        self.assertGreater(report.operator_count, 0)
        self.assertGreater(report.observation_count, 0)

    def test_render_canonical_markdown(self):
        svc = PilotService()
        report = build_canonical_report(svc)
        md = render_canonical_markdown(report)
        self.assertIn("MO§ES™", md)
        self.assertIn("Data Quality", md)
        self.assertIn("SYNTHETIC", md)


class TestPDFReportingInvariant(unittest.TestCase):
    """Tests for the PDF reporting invariant (Drift 3 fix)."""

    def test_pdf_without_source_raises(self):
        """The static sample report is no longer a valid default source."""
        from reporting.pdf import render_sample_report_pdf
        with self.assertRaises(ValueError):
            render_sample_report_pdf()

    def test_pdf_with_runtime_markdown(self):
        """PDF can be rendered from runtime-generated markdown."""
        from reporting.pdf import render_sample_report_pdf
        md = "# Test Report\n\nThis is a runtime-generated report."
        try:
            path = render_sample_report_pdf(
                output_path="/tmp/test_report.pdf",
                runtime_markdown=md,
            )
            self.assertTrue(Path(path).exists())
        except ImportError:
            # WeasyPrint not installed in test env — skip
            pass


class TestCLIGovernance(unittest.TestCase):
    """Tests for CLI pilot governance commands."""

    def test_cli_pilot_status(self):
        rc = cli_main(["--json", "pilot", "status"])
        self.assertEqual(rc, 0)

    def test_cli_pilot_report(self):
        rc = cli_main(["--json", "pilot", "report", "--format", "json"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
