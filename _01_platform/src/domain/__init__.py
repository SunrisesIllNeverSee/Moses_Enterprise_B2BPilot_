"""Domain model for the enterprise operator intelligence pilot engine.

Implements the canonical entity graph from `14_PRODUCT_OBJECT_MODEL.md`:

    Tenant
     ├─ Cohort
     │   ├─ Operator
     │   │   ├─ Observation
     │   │   ├─ Measurement
     │   │   ├─ Pattern
     │   │   ├─ Diagnosis
     │   │   ├─ Intervention
     │   │   └─ OutcomeJoin
     │   └─ CohortMeasurement
     ├─ Workflow
     │   └─ Stage
     │       └─ WorkflowObservation
     ├─ ReferencePopulation
     └─ Report

P0-A entities (per `21_DEVIN_IMPLEMENTATION_HANDOFF.md`):
    Observation, Operator, Cohort, Measurement, ReferencePopulation, QualityResult.

All entities are frozen dataclasses (immutable value objects) unless noted.
Every entity that can originate from synthetic data carries a `synthetic: bool` field
so the synthetic marker survives import/export (P0 acceptance test).
"""
from __future__ import annotations

from .observation import Observation
from .provenance import Provenance
from .operator import Operator
from .cohort import Cohort
from .measurement import Measurement, MetricStatus
from .reference_population import ReferencePopulation
from .quality_result import QualityResult, QualitySeverity
from .tenant import Tenant
from .pattern import Pattern
from .diagnosis import Diagnosis, DiagnosisStatus, DiagnosticLevel
from .intervention import Intervention, InterventionOutcome
from .outcome_join import OutcomeJoin
from .workflow import Workflow, Stage, WorkflowObservation
from .report import Report
from .production_gate import (
    GateAction,
    GateDirection,
    GateRule,
    GateResult,
    DEFAULT_GATE_RULES,
    evaluate_gate,
    evaluate_all_gates,
    evaluate_cohort_gates,
    summarize_gates,
)
from .pilot_configuration import (
    PilotConfiguration,
    EvalFamilySelection,
    CohortConfig,
    WorkflowConfig,
    GateRuleConfig,
    GatesConfig,
    OutcomeJoinConfig,
    GovernanceConfig,
    ReferencePopulationConfig,
)
from .system import System, SystemType
from .system_version import SystemVersion
from .session import Session
from .task import Task, TaskType
from .prior_state import PriorState
from .operator_action import OperatorAction, ActionType
from .system_action import SystemAction, ResponseType
from .resulting_state import ResultingState
from .transformation import Transformation, TransformationType
from .artifact import Artifact, ArtifactType
from .lineage import Lineage, LineageLink, LinkType
from .outcome import Outcome, OutcomeType, OutcomeStatus
from .evidence_grade import EvidenceGrade, EvidenceGradeAssessment
from .context import TaskContext, adjust_metric_for_context, context_adjustment
from .operator_identity import OperatorIdentity, IdentityConflictError

__all__ = [
    "Observation",
    "Provenance",
    "Operator",
    "Cohort",
    "Measurement",
    "MetricStatus",
    "ReferencePopulation",
    "QualityResult",
    "QualitySeverity",
    "Tenant",
    "Pattern",
    "Diagnosis",
    "DiagnosisStatus",
    "DiagnosticLevel",
    "Intervention",
    "InterventionOutcome",
    "OutcomeJoin",
    "Workflow",
    "Stage",
    "WorkflowObservation",
    "Report",
    "GateAction",
    "GateDirection",
    "GateRule",
    "GateResult",
    "DEFAULT_GATE_RULES",
    "evaluate_gate",
    "evaluate_all_gates",
    "evaluate_cohort_gates",
    "summarize_gates",
    "PilotConfiguration",
    "EvalFamilySelection",
    "CohortConfig",
    "WorkflowConfig",
    "GateRuleConfig",
    "GatesConfig",
    "OutcomeJoinConfig",
    "GovernanceConfig",
    "ReferencePopulationConfig",
    "System",
    "SystemType",
    "SystemVersion",
    "Session",
    "Task",
    "TaskType",
    "PriorState",
    "OperatorAction",
    "ActionType",
    "SystemAction",
    "ResponseType",
    "ResultingState",
    "Transformation",
    "TransformationType",
    "Artifact",
    "ArtifactType",
    "Lineage",
    "LineageLink",
    "LinkType",
    "Outcome",
    "OutcomeType",
    "OutcomeStatus",
    "EvidenceGrade",
    "EvidenceGradeAssessment",
    "TaskContext",
    "adjust_metric_for_context",
    "context_adjustment",
    "OperatorIdentity",
    "IdentityConflictError",
]
