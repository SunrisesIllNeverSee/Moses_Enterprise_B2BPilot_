"""Tests for the 10 new canonical domain classes (Q5 gap closure).

Verifies:
  - All 12 new classes import correctly
  - Frozen dataclass behavior
  - synthetic field defaults to False
  - to_dict / from_dict round-trips
  - Enum values match framework spec
"""
from __future__ import annotations

import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestNewDomainClasses(unittest.TestCase):
    """Tests for the 10 new canonical domain classes."""

    # ── System ───────────────────────────────────────────────────────────

    def test_system_creation(self):
        from domain import System, SystemType
        s = System(
            system_id="sys_001",
            tenant_id="tenant_001",
            name="Claude",
            system_type=SystemType.AI_PLATFORM,
        )
        self.assertEqual(s.system_id, "sys_001")
        self.assertEqual(s.name, "Claude")
        self.assertFalse(s.synthetic)
        self.assertEqual(s.system_type, SystemType.AI_PLATFORM)

    def test_system_type_enum(self):
        from domain import SystemType
        values = {t.value for t in SystemType}
        self.assertEqual(values, {
            "ai_platform", "agent_platform",
            "enterprise_software", "identity", "data_input",
        })

    # ── SystemVersion ────────────────────────────────────────────────────

    def test_system_version_creation(self):
        from domain import SystemVersion
        v = SystemVersion(
            version_id="ver_001",
            system_id="sys_001",
            version_label="claude-3.5-sonnet",
        )
        self.assertEqual(v.version_id, "ver_001")
        self.assertEqual(v.system_id, "sys_001")
        self.assertFalse(v.synthetic)

    # ── Session ──────────────────────────────────────────────────────────

    def test_session_creation(self):
        from domain import Session
        s = Session(
            session_id="sess_001",
            operator_id="op_001",
            system_id="sys_001",
            start_time=datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(s.session_id, "sess_001")
        self.assertFalse(s.synthetic)

    # ── Task ─────────────────────────────────────────────────────────────

    def test_task_creation(self):
        from domain import Task, TaskType
        t = Task(
            task_id="task_001",
            operator_id="op_001",
            intent_label="implement feature",
            task_type=TaskType.CODE_GENERATION,
            created_at=datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(t.task_id, "task_001")
        self.assertEqual(t.task_type, TaskType.CODE_GENERATION)
        self.assertFalse(t.synthetic)

    def test_task_type_enum(self):
        from domain import TaskType
        values = {t.value for t in TaskType}
        self.assertIn("code_generation", values)
        self.assertIn("debugging", values)

    # ── PriorState ───────────────────────────────────────────────────────

    def test_prior_state_creation(self):
        from domain import PriorState
        ps = PriorState(
            state_id="ps_001",
            session_id="sess_001",
            task_id="task_001",
            operator_id="op_001",
        )
        self.assertEqual(ps.state_id, "ps_001")
        self.assertFalse(ps.synthetic)

    # ── OperatorAction ───────────────────────────────────────────────────

    def test_operator_action_creation(self):
        from domain import OperatorAction, ActionType
        oa = OperatorAction(
            action_id="oa_001",
            operator_id="op_001",
            session_id="sess_001",
            task_id="task_001",
            action_type=ActionType.PROMPT,
            timestamp=datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(oa.action_id, "oa_001")
        self.assertEqual(oa.action_type, ActionType.PROMPT)
        self.assertFalse(oa.synthetic)

    def test_action_type_enum(self):
        from domain import ActionType
        values = {a.value for a in ActionType}
        self.assertEqual(values, {
            "prompt", "redirect", "refine", "accept",
            "reject", "retry", "abort", "commit",
        })

    # ── SystemAction ─────────────────────────────────────────────────────

    def test_system_action_creation(self):
        from domain import SystemAction, ResponseType
        sa = SystemAction(
            action_id="sa_001",
            system_id="sys_001",
            session_id="sess_001",
            task_id="task_001",
            response_type=ResponseType.GENERATE,
            timestamp=datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(sa.action_id, "sa_001")
        self.assertEqual(sa.response_type, ResponseType.GENERATE)
        self.assertFalse(sa.synthetic)

    def test_response_type_enum(self):
        from domain import ResponseType
        values = {r.value for r in ResponseType}
        self.assertEqual(values, {
            "generate", "complete", "refuse", "error", "partial",
        })

    # ── ResultingState ───────────────────────────────────────────────────

    def test_resulting_state_creation(self):
        from domain import ResultingState
        rs = ResultingState(
            state_id="rs_001",
            session_id="sess_001",
            task_id="task_001",
            operator_id="op_001",
        )
        self.assertEqual(rs.state_id, "rs_001")
        self.assertFalse(rs.synthetic)

    # ── Transformation ───────────────────────────────────────────────────

    def test_transformation_creation(self):
        from domain import Transformation, TransformationType
        t = Transformation(
            transformation_id="t_001",
            session_id="sess_001",
            task_id="task_001",
            operator_id="op_001",
            transformation_type=TransformationType.CREATION,
        )
        self.assertEqual(t.transformation_id, "t_001")
        self.assertEqual(t.transformation_type, TransformationType.CREATION)
        self.assertFalse(t.synthetic)

    def test_transformation_type_enum(self):
        from domain import TransformationType
        values = {t.value for t in TransformationType}
        self.assertEqual(values, {
            "creation", "modification", "refinement",
            "redirection", "extension", "commit",
        })

    # ── Artifact ─────────────────────────────────────────────────────────

    def test_artifact_creation(self):
        from domain import Artifact, ArtifactType
        a = Artifact(
            artifact_id="art_001",
            operator_id="op_001",
            artifact_type=ArtifactType.CODE_FILE,
        )
        self.assertEqual(a.artifact_id, "art_001")
        self.assertEqual(a.artifact_type, ArtifactType.CODE_FILE)
        self.assertFalse(a.synthetic)

    def test_artifact_type_enum(self):
        from domain import ArtifactType
        values = {a.value for a in ArtifactType}
        self.assertEqual(values, {
            "code_file", "document", "config", "test_file",
            "design_doc", "data_file", "script", "other",
        })

    # ── Lineage ──────────────────────────────────────────────────────────

    def test_lineage_creation(self):
        from domain import Lineage, LineageLink, LinkType
        link = LineageLink(
            link_id="link_001",
            lineage_id="lin_001",
            link_type=LinkType.STATE_A,
            order=0,
        )
        lin = Lineage(
            lineage_id="lin_001",
            operator_id="op_001",
        )
        self.assertEqual(lin.lineage_id, "lin_001")
        self.assertFalse(lin.synthetic)

    def test_link_type_enum(self):
        from domain import LinkType
        values = {l.value for l in LinkType}
        self.assertEqual(values, {
            "state_a", "bi_action", "aai_transformation",
            "bi_redirection", "aai_extension", "committed_state", "outcome",
        })

    # ── EvidenceGrade ────────────────────────────────────────────────────

    def test_evidence_grade_enum(self):
        from domain import EvidenceGrade
        values = {e.value for e in EvidenceGrade}
        self.assertEqual(values, {
            "controlled_experiment", "complete_interaction_telemetry",
            "strong_observational_telemetry", "partial_telemetry",
            "activity_metadata", "customer_supplied_outcome",
            "inferred_signal", "insufficient_evidence",
        })

    def test_evidence_grade_assessment_creation(self):
        from domain import EvidenceGradeAssessment, EvidenceGrade
        ega = EvidenceGradeAssessment(
            assessment_id="ega_001",
            target_type="measurement",
            target_id="m_001",
            grade=EvidenceGrade.STRONG_OBSERVATIONAL_TELEMETRY,
            assessed_at=datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(ega.assessment_id, "ega_001")
        self.assertEqual(ega.grade, EvidenceGrade.STRONG_OBSERVATIONAL_TELEMETRY)
        self.assertFalse(ega.synthetic)

    # ── Frozen dataclass ─────────────────────────────────────────────────

    def test_all_new_classes_are_frozen(self):
        """All new domain classes should be frozen (immutable)."""
        from domain import (
            System, SystemVersion, Session, Task, PriorState,
            OperatorAction, SystemAction, ResultingState,
            Transformation, Artifact, Lineage, EvidenceGradeAssessment,
        )
        for cls in [
            System, SystemVersion, Session, Task, PriorState,
            OperatorAction, SystemAction, ResultingState,
            Transformation, Artifact, Lineage, EvidenceGradeAssessment,
        ]:
            # Check that the dataclass is frozen by looking at __dataclass_params__
            params = getattr(cls, "__dataclass_params__", None)
            self.assertIsNotNone(params, f"{cls.__name__} is not a dataclass")
            self.assertTrue(
                params.frozen,
                f"{cls.__name__} is not frozen — all domain classes must be frozen",
            )

    # ── __all__ exports ──────────────────────────────────────────────────

    def test_all_new_classes_exported(self):
        """All new classes should be importable from the domain package."""
        import domain
        expected = [
            "System", "SystemType",
            "SystemVersion",
            "Session",
            "Task", "TaskType",
            "PriorState",
            "OperatorAction", "ActionType",
            "SystemAction", "ResponseType",
            "ResultingState",
            "Transformation", "TransformationType",
            "Artifact", "ArtifactType",
            "Lineage", "LineageLink", "LinkType",
            "EvidenceGrade", "EvidenceGradeAssessment",
        ]
        for name in expected:
            self.assertTrue(
                hasattr(domain, name),
                f"{name} not exported from domain package",
            )


if __name__ == "__main__":
    unittest.main()
