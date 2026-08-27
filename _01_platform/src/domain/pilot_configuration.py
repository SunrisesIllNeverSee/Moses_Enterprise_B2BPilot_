"""PilotConfiguration — the configuration object for a bespoke pilot.

Per the bespoke pilot menu system design. A PilotConfiguration specifies:
    - Selected eval families (which EVAL-001–EVAL-015 are active)
    - Cohort parameters (size, window)
    - Deployment level (1/2/3)
    - Production gates (which gate rules to enable, what thresholds)
    - Outcome join configuration (if external KPIs are included)
    - Workflow definition (custom or default software_dev_v1)
    - Governance metadata (synthetic flag, decision-use labels)

The configuration is saveable/loadable as JSON. Constraints:
    - The canonical metrics (5) are NOT configurable — they are the product.
    - The intervention catalog (12) is NOT configurable — it is fixed.
    - Gates ARE configurable (threshold values, enable/disable per rule).
    - Cohort, workflow, reference population, and outcome joins ARE configurable.
    - All configurations carry governance metadata.
    - No causal claims — outcome joins are always ASSOCIATION.
    - Diagnoses are always HYPOTHESIS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass(frozen=True, slots=True)
class EvalFamilySelection:
    """One eval family selection in a pilot configuration."""
    eval_id: str
    enabled: bool = True
    notes: str = ""

    def to_dict(self) -> dict:
        return {"eval_id": self.eval_id, "enabled": self.enabled, "notes": self.notes}

    @classmethod
    def from_dict(cls, d: dict) -> "EvalFamilySelection":
        return cls(eval_id=d["eval_id"], enabled=d.get("enabled", True), notes=d.get("notes", ""))


@dataclass(frozen=True, slots=True)
class CohortConfig:
    """Cohort parameters for a pilot configuration."""
    window_days: int = 30
    min_operators: int = 25
    max_operators: int = 100
    cohort_id: str = ""
    tenant_id: str = ""
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    synthetic: bool = True

    def to_dict(self) -> dict:
        return {
            "cohort_id": self.cohort_id, "tenant_id": self.tenant_id,
            "window_days": self.window_days, "window_start": self.window_start,
            "window_end": self.window_end, "min_operators": self.min_operators,
            "max_operators": self.max_operators, "synthetic": self.synthetic,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CohortConfig":
        return cls(
            window_days=d.get("window_days", 30), min_operators=d.get("min_operators", 25),
            max_operators=d.get("max_operators", 100), cohort_id=d.get("cohort_id", ""),
            tenant_id=d.get("tenant_id", ""), window_start=d.get("window_start"),
            window_end=d.get("window_end"), synthetic=d.get("synthetic", True),
        )


@dataclass(frozen=True, slots=True)
class WorkflowConfig:
    """Workflow definition for a pilot configuration."""
    workflow_id: str = "software_dev_v1"
    custom_stages: Optional[List[dict]] = None

    def to_dict(self) -> dict:
        return {"workflow_id": self.workflow_id, "custom_stages": list(self.custom_stages) if self.custom_stages else None}

    @classmethod
    def from_dict(cls, d: dict) -> "WorkflowConfig":
        return cls(workflow_id=d.get("workflow_id", "software_dev_v1"), custom_stages=d.get("custom_stages"))


@dataclass(frozen=True, slots=True)
class GateRuleConfig:
    """One gate rule in a pilot configuration."""
    rule_id: str
    metric_id: str
    threshold: float
    direction: str
    action: str
    is_percentile: bool = True
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id, "metric_id": self.metric_id, "threshold": self.threshold,
            "direction": self.direction, "action": self.action, "is_percentile": self.is_percentile,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GateRuleConfig":
        return cls(
            rule_id=d["rule_id"], metric_id=d["metric_id"], threshold=d["threshold"],
            direction=d["direction"], action=d["action"], is_percentile=d.get("is_percentile", True),
            description=d.get("description", ""),
        )


@dataclass(frozen=True, slots=True)
class GatesConfig:
    """Gate configuration for a pilot configuration."""
    enabled: bool = False
    rules: List[GateRuleConfig] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"enabled": self.enabled, "rules": [r.to_dict() for r in self.rules]}

    @classmethod
    def from_dict(cls, d: dict) -> "GatesConfig":
        return cls(enabled=d.get("enabled", False), rules=[GateRuleConfig.from_dict(r) for r in d.get("rules", [])])


@dataclass(frozen=True, slots=True)
class OutcomeJoinConfig:
    """Outcome join configuration for a pilot configuration."""
    enabled: bool = False
    outcome_csv_path: str = ""
    outcome_metrics: List[str] = field(default_factory=list)
    label: str = "ASSOCIATION — never CAUSATION"

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled, "outcome_csv_path": self.outcome_csv_path,
            "outcome_metrics": list(self.outcome_metrics), "label": self.label,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OutcomeJoinConfig":
        return cls(
            enabled=d.get("enabled", False), outcome_csv_path=d.get("outcome_csv_path", ""),
            outcome_metrics=list(d.get("outcome_metrics", [])),
            label=d.get("label", "ASSOCIATION — never CAUSATION"),
        )


@dataclass(frozen=True, slots=True)
class GovernanceConfig:
    """Governance metadata for a pilot configuration."""
    synthetic: bool = True
    decision_use_default: str = "DEVELOPMENTAL"
    authorized_by: str = ""
    privacy_class: str = "pseudonymous_synthetic"

    def to_dict(self) -> dict:
        return {
            "synthetic": self.synthetic, "decision_use_default": self.decision_use_default,
            "authorized_by": self.authorized_by, "privacy_class": self.privacy_class,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GovernanceConfig":
        return cls(
            synthetic=d.get("synthetic", True), decision_use_default=d.get("decision_use_default", "DEVELOPMENTAL"),
            authorized_by=d.get("authorized_by", ""), privacy_class=d.get("privacy_class", "pseudonymous_synthetic"),
        )


@dataclass(frozen=True, slots=True)
class ReferencePopulationConfig:
    """Reference population configuration for a pilot configuration."""
    reference_id: str = ""
    version: str = ""
    custom_distributions_path: str = ""

    def to_dict(self) -> dict:
        return {
            "reference_id": self.reference_id, "version": self.version,
            "custom_distributions_path": self.custom_distributions_path,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ReferencePopulationConfig":
        return cls(
            reference_id=d.get("reference_id", ""), version=d.get("version", ""),
            custom_distributions_path=d.get("custom_distributions_path", ""),
        )


@dataclass(frozen=True, slots=True)
class PilotConfiguration:
    """The complete configuration for a bespoke pilot."""
    config_id: str
    mode: str
    eval_families: List[EvalFamilySelection]
    cohort: CohortConfig = field(default_factory=CohortConfig)
    deployment_level: int = 1
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    gates: GatesConfig = field(default_factory=GatesConfig)
    outcome_join: OutcomeJoinConfig = field(default_factory=OutcomeJoinConfig)
    governance: GovernanceConfig = field(default_factory=GovernanceConfig)
    reference_population: ReferencePopulationConfig = field(default_factory=ReferencePopulationConfig)
    commercial_pilot_id: Optional[str] = None
    name: str = ""
    description: str = ""
    created_at: str = ""
    created_by: str = ""

    def to_dict(self) -> dict:
        return {
            "config_id": self.config_id, "name": self.name, "description": self.description,
            "mode": self.mode, "commercial_pilot_id": self.commercial_pilot_id,
            "eval_families": [e.to_dict() for e in self.eval_families],
            "cohort": self.cohort.to_dict(), "deployment_level": self.deployment_level,
            "workflow": self.workflow.to_dict(), "gates": self.gates.to_dict(),
            "outcome_join": self.outcome_join.to_dict(), "governance": self.governance.to_dict(),
            "reference_population": self.reference_population.to_dict(),
            "created_at": self.created_at, "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PilotConfiguration":
        return cls(
            config_id=d["config_id"], mode=d["mode"],
            eval_families=[EvalFamilySelection.from_dict(e) for e in d["eval_families"]],
            cohort=CohortConfig.from_dict(d.get("cohort", {})),
            deployment_level=d.get("deployment_level", 1),
            workflow=WorkflowConfig.from_dict(d.get("workflow", {})),
            gates=GatesConfig.from_dict(d.get("gates", {})),
            outcome_join=OutcomeJoinConfig.from_dict(d.get("outcome_join", {})),
            governance=GovernanceConfig.from_dict(d.get("governance", {})),
            reference_population=ReferencePopulationConfig.from_dict(d.get("reference_population", {})),
            commercial_pilot_id=d.get("commercial_pilot_id"),
            name=d.get("name", ""), description=d.get("description", ""),
            created_at=d.get("created_at", ""), created_by=d.get("created_by", ""),
        )

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "PilotConfiguration":
        import json
        return cls.from_dict(json.loads(json_str))

    def enabled_eval_ids(self) -> List[str]:
        return [e.eval_id for e in self.eval_families if e.enabled]
