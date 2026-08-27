"""Tests for governance enforcement — the 6 items added to spec 12.

Covers: purpose limitation, employee disclosure, consent, bias review,
right to challenge, correction process, and the unified facade.
"""
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from governance.enforcement import (
    GovernanceEnforcement,
    ProcessingPurpose,
    PurposeLimitationGate,
    DisclosureGate,
    ConsentModel,
    ConsentState,
    ConsentManager,
    BiasSeverity,
    BiasReviewReport,
    BiasReviewManager,
    Challenge,
    ChallengeStatus,
    ChallengeResolution,
    ChallengeManager,
    CorrectionType,
    CorrectionStatus,
    CorrectionRecord,
    CorrectionManager,
    GovernanceAuditLog,
)


# ─── 1. Purpose limitation ───────────────────────────────────────────

class TestPurposeLimitation:
    def test_ingestion_blocked_without_purpose(self):
        gate = PurposeLimitationGate()
        ok, reason = gate.check_ingestion("")
        assert not ok
        assert "No processing purpose" in reason

    def test_ingestion_blocked_with_unknown_purpose(self):
        gate = PurposeLimitationGate()
        ok, reason = gate.check_ingestion("unknown_purpose")
        assert not ok
        assert "Unknown purpose" in reason

    def test_ingestion_permitted_with_declared_purpose(self):
        gate = PurposeLimitationGate()
        purpose = ProcessingPurpose(
            purpose_id="pilot_001",
            description="Baseline operator evaluation",
            eval_questions=["EVAL-001", "EVAL-002"],
        )
        gate.declare_purpose(purpose)
        ok, reason = gate.check_ingestion("pilot_001")
        assert ok
        assert "pilot_001" in reason

    def test_computation_blocked_outside_scope(self):
        gate = PurposeLimitationGate()
        purpose = ProcessingPurpose(
            purpose_id="pilot_001",
            description="Baseline",
            eval_questions=["EVAL-001"],
        )
        gate.declare_purpose(purpose)
        ok, reason = gate.check_computation("pilot_001", "EVAL-007")
        assert not ok
        assert "not in declared scope" in reason

    def test_computation_permitted_within_scope(self):
        gate = PurposeLimitationGate()
        purpose = ProcessingPurpose(
            purpose_id="pilot_001",
            description="Baseline",
            eval_questions=["EVAL-001", "EVAL-002"],
        )
        gate.declare_purpose(purpose)
        ok, _ = gate.check_computation("pilot_001", "EVAL-001")
        assert ok

    def test_purpose_serialization(self):
        purpose = ProcessingPurpose(
            purpose_id="p1", description="Test",
            eval_questions=["EVAL-001"],
        )
        d = purpose.to_dict()
        restored = ProcessingPurpose.from_dict(d)
        assert restored.purpose_id == "p1"
        assert restored.eval_questions == ["EVAL-001"]


# ─── 2. Employee disclosure ──────────────────────────────────────────

class TestEmployeeDisclosure:
    def test_ingestion_blocked_without_notification(self):
        gate = DisclosureGate()
        ok, reason = gate.check_ingestion("op_001")
        assert not ok
        assert "not been notified" in reason

    def test_ingestion_blocked_pending_acknowledgment(self):
        gate = DisclosureGate()
        gate.notify("op_001")
        ok, reason = gate.check_ingestion("op_001")
        assert not ok
        assert "pending" in reason

    def test_ingestion_permitted_after_acknowledgment(self):
        gate = DisclosureGate()
        gate.notify("op_001")
        gate.acknowledge("op_001")
        ok, reason = gate.check_ingestion("op_001")
        assert ok
        assert "acknowledged" in reason

    def test_ingestion_blocked_after_decline(self):
        gate = DisclosureGate()
        gate.notify("op_001")
        gate.decline("op_001")
        ok, reason = gate.check_ingestion("op_001")
        assert not ok
        assert "declined" in reason

    def test_acknowledge_without_notify_raises(self):
        gate = DisclosureGate()
        try:
            gate.acknowledge("op_001")
            assert False, "Should have raised"
        except ValueError:
            pass

    def test_disclosure_template_exists(self):
        gate = DisclosureGate()
        record = gate.notify("op_001")
        assert "MO§ES™" in record.notification_text
        assert "NOT collected" in record.notification_text


# ─── 3. Consent ──────────────────────────────────────────────────────

class TestConsent:
    def test_opt_in_blocks_pending(self):
        mgr = ConsentManager(default_model=ConsentModel.OPT_IN)
        mgr.set_model("op_001", ConsentModel.OPT_IN, ConsentState.PENDING)
        ok, reason = mgr.check_ingestion("op_001")
        assert not ok
        assert "pending" in reason

    def test_opt_in_permits_after_grant(self):
        mgr = ConsentManager(default_model=ConsentModel.OPT_IN)
        mgr.set_model("op_001", ConsentModel.OPT_IN, ConsentState.PENDING)
        mgr.grant("op_001")
        ok, _ = mgr.check_ingestion("op_001")
        assert ok

    def test_opt_out_permits_by_default(self):
        mgr = ConsentManager(default_model=ConsentModel.OPT_OUT)
        ok, _ = mgr.check_ingestion("op_001")
        assert ok

    def test_withdrawal_blocks_and_queues_deletion(self):
        mgr = ConsentManager(default_model=ConsentModel.OPT_OUT)
        mgr.withdraw("op_001", reason="Operator requested withdrawal")
        ok, reason = mgr.check_ingestion("op_001")
        assert not ok
        assert "withdrawn" in reason
        assert "op_001" in mgr.deletion_queue

    def test_corporate_authorization_permits(self):
        mgr = ConsentManager(default_model=ConsentModel.CORPORATE_AUTHORIZATION)
        mgr.set_model("op_001", ConsentModel.CORPORATE_AUTHORIZATION, ConsentState.GRANTED)
        ok, _ = mgr.check_ingestion("op_001")
        assert ok

    def test_consent_serialization(self):
        mgr = ConsentManager()
        mgr.grant("op_001", "test grant")
        record = mgr.get_record("op_001")
        d = record.to_dict()
        restored = type(record).from_dict(d)
        assert restored.operator_id == "op_001"
        assert restored.state == ConsentState.GRANTED


# ─── 4. Bias review ──────────────────────────────────────────────────

class TestBiasReview:
    def test_no_bias_by_default(self):
        mgr = BiasReviewManager()
        assert not mgr.is_biased("leverage")

    def test_severe_unmitigated_flags_bias(self):
        mgr = BiasReviewManager()
        report = BiasReviewReport(
            review_id="br_001",
            review_type="measurement",
            target_id="leverage",
            severity=BiasSeverity.SEVERE,
            findings=["Leverage systematically disadvantages operators using models with different tokenization"],
            mitigated=False,
        )
        mgr.submit_review(report)
        assert mgr.is_biased("leverage")
        assert mgr.check_downgrade("leverage")

    def test_mitigated_bias_does_not_flag(self):
        mgr = BiasReviewManager()
        report = BiasReviewReport(
            review_id="br_001",
            review_type="measurement",
            target_id="leverage",
            severity=BiasSeverity.MODERATE,
            findings=["Some bias found"],
            mitigated=True,
            mitigation_plan=["Adjusted normalization"],
        )
        mgr.submit_review(report)
        assert not mgr.is_biased("leverage")

    def test_low_severity_does_not_flag(self):
        mgr = BiasReviewManager()
        report = BiasReviewReport(
            review_id="br_001",
            review_type="telemetry",
            target_id="claude_adapter",
            severity=BiasSeverity.LOW,
        )
        mgr.submit_review(report)
        assert not mgr.is_biased("claude_adapter")

    def test_reviews_for_target(self):
        mgr = BiasReviewManager()
        mgr.submit_review(BiasReviewReport(review_id="br_1", review_type="measurement", target_id="yield"))
        mgr.submit_review(BiasReviewReport(review_id="br_2", review_type="measurement", target_id="yield"))
        assert len(mgr.reviews_for_target("yield")) == 2


# ─── 5. Right to challenge ───────────────────────────────────────────

class TestChallenge:
    def test_submit_creates_pending_challenge(self):
        mgr = ChallengeManager()
        c = mgr.submit("ch_001", "op_001", "meas_001", "measurement", "I think this is wrong")
        assert c.status == ChallengeStatus.SUBMITTED
        assert c.is_unresolved
        assert c.requires_downgrade

    def test_start_review_updates_status(self):
        mgr = ChallengeManager()
        mgr.submit("ch_001", "op_001", "meas_001", "measurement", "Wrong")
        c = mgr.start_review("ch_001", reviewer="analyst_1")
        assert c.status == ChallengeStatus.UNDER_REVIEW
        assert c.reviewer == "analyst_1"

    def test_resolve_upheld(self):
        mgr = ChallengeManager()
        mgr.submit("ch_001", "op_001", "meas_001", "measurement", "Wrong")
        mgr.start_review("ch_001", "analyst_1")
        c = mgr.resolve("ch_001", ChallengeResolution.UPHELD, "Data was incorrect")
        assert c.status == ChallengeStatus.RESOLVED
        assert c.resolution == ChallengeResolution.UPHELD
        assert not c.is_unresolved
        assert not c.requires_downgrade
        assert c.resolved_at is not None

    def test_resolve_not_upheld(self):
        mgr = ChallengeManager()
        mgr.submit("ch_001", "op_001", "meas_001", "measurement", "Wrong")
        c = mgr.resolve("ch_001", ChallengeResolution.NOT_UPHELD, "Data verified correct")
        assert c.resolution == ChallengeResolution.NOT_UPHELD

    def test_has_unresolved_challenge(self):
        mgr = ChallengeManager()
        mgr.submit("ch_001", "op_001", "meas_001", "measurement", "Wrong")
        assert mgr.has_unresolved_challenge("meas_001")
        mgr.resolve("ch_001", ChallengeResolution.UPHELD)
        assert not mgr.has_unresolved_challenge("meas_001")

    def test_challenges_for_operator(self):
        mgr = ChallengeManager()
        mgr.submit("ch_1", "op_001", "meas_1", "measurement", "A")
        mgr.submit("ch_2", "op_001", "meas_2", "measurement", "B")
        mgr.submit("ch_3", "op_002", "meas_3", "measurement", "C")
        assert len(mgr.challenges_for_operator("op_001")) == 2
        assert len(mgr.challenges_for_operator("op_002")) == 1

    def test_challenge_serialization(self):
        mgr = ChallengeManager()
        c = mgr.submit("ch_001", "op_001", "meas_001", "measurement", "Wrong")
        d = c.to_dict()
        restored = Challenge.from_dict(d)
        assert restored.challenge_id == "ch_001"
        assert restored.operator_id == "op_001"


# ─── 6. Correction process ───────────────────────────────────────────

class TestCorrection:
    def test_full_correction_workflow(self):
        mgr = CorrectionManager()
        r = mgr.identify("corr_001", "observation", "obs_001",
                         CorrectionType.FACTUAL_ERROR, "Token count was wrong")
        assert r.status == CorrectionStatus.IDENTIFIED

        r = mgr.quarantine("corr_001")
        assert r.status == CorrectionStatus.QUARANTINED
        assert mgr.is_quarantined("obs_001")

        r = mgr.correct("corr_001")
        assert r.status == CorrectionStatus.CORRECTED
        assert r.corrected_at is not None

        r = mgr.propagate("corr_001", ["meas_001", "meas_002", "diag_001"])
        assert r.status == CorrectionStatus.PROPAGATED
        assert len(r.propagated_results) == 3

        r = mgr.notify("corr_001", ["operator", "customer"])
        assert r.status == CorrectionStatus.NOTIFIED
        assert "operator" in r.notified_parties

        r = mgr.log("corr_001")
        assert r.status == CorrectionStatus.LOGGED

    def test_quarantine_blocks_target(self):
        mgr = CorrectionManager()
        mgr.identify("corr_001", "observation", "obs_001",
                     CorrectionType.DATA_QUALITY_ERROR, "Missing sessions")
        mgr.quarantine("corr_001")
        assert mgr.is_quarantined("obs_001")

    def test_correction_serialization(self):
        mgr = CorrectionManager()
        mgr.identify("corr_001", "measurement", "meas_001",
                     CorrectionType.COMPUTATION_ERROR, "Bad formula")
        r = mgr.get_correction("corr_001")
        d = r.to_dict()
        restored = CorrectionRecord.from_dict(d)
        assert restored.correction_id == "corr_001"
        assert restored.correction_type == CorrectionType.COMPUTATION_ERROR


# ─── Audit log ───────────────────────────────────────────────────────

class TestAuditLog:
    def test_log_appends_entries(self):
        log = GovernanceAuditLog()
        log.log("ingestion_permitted", "system", "op_001", "purpose=pilot_001")
        log.log("ingestion_blocked", "system", "op_002", "No consent")
        assert len(log.entries()) == 2

    def test_entries_for_target(self):
        log = GovernanceAuditLog()
        log.log("action1", "system", "op_001")
        log.log("action2", "system", "op_002")
        log.log("action3", "system", "op_001")
        assert len(log.entries_for_target("op_001")) == 2


# ─── Unified facade ──────────────────────────────────────────────────

class TestGovernanceEnforcement:
    def test_check_ingestion_blocks_without_purpose_or_disclosure(self):
        gov = GovernanceEnforcement()
        ok, reasons = gov.check_ingestion("op_001", purpose_id="")
        assert not ok
        assert len(reasons) >= 2  # purpose + disclosure failures

    def test_check_ingestion_permits_with_all_checks_passed(self):
        gov = GovernanceEnforcement()
        # Declare purpose
        gov.purpose_gate.declare_purpose(ProcessingPurpose(
            purpose_id="pilot_001",
            description="Baseline",
            eval_questions=["EVAL-001"],
        ))
        # Notify + acknowledge
        gov.disclosure_gate.notify("op_001")
        gov.disclosure_gate.acknowledge("op_001")
        # Consent (opt_out default, no withdrawal)
        ok, reasons = gov.check_ingestion("op_001", purpose_id="pilot_001")
        assert ok, f"Expected ok but got: {reasons}"

    def test_check_ingestion_blocks_on_consent_withdrawal(self):
        gov = GovernanceEnforcement()
        gov.purpose_gate.declare_purpose(ProcessingPurpose(
            purpose_id="pilot_001", description="Baseline"))
        gov.disclosure_gate.notify("op_001")
        gov.disclosure_gate.acknowledge("op_001")
        gov.consent_manager.withdraw("op_001", "Operator withdrew")
        ok, reasons = gov.check_ingestion("op_001", purpose_id="pilot_001")
        assert not ok
        assert any("withdrawn" in r for r in reasons)

    def test_check_computation_with_bias_downgrade(self):
        gov = GovernanceEnforcement()
        gov.purpose_gate.declare_purpose(ProcessingPurpose(
            purpose_id="pilot_001", description="Baseline",
            eval_questions=["EVAL-001"]))
        gov.bias_review.submit_review(BiasReviewReport(
            review_id="br_001", review_type="measurement",
            target_id="leverage", severity=BiasSeverity.SEVERE,
        ))
        ok, reasons = gov.check_computation("pilot_001", "EVAL-001", target_id="leverage")
        # Purpose check passes, but bias flag is noted
        assert ok  # computation still proceeds, just downgraded
        assert any("bias" in r.lower() for r in reasons)

    def test_audit_log_records_governance_actions(self):
        gov = GovernanceEnforcement()
        gov.check_ingestion("op_001", purpose_id="")
        entries = gov.audit_log.entries()
        assert len(entries) >= 1
        assert any(e.action == "ingestion_blocked" for e in entries)
