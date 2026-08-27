"""ConfigValidator — validates pilot configuration compatibility rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from domain.pilot_configuration import PilotConfiguration
from .eval_registry import EVAL_FAMILIES

@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    def to_dict(self) -> dict:
        return {"valid": self.valid, "errors": list(self.errors), "warnings": list(self.warnings)}

class ConfigValidator:
    @staticmethod
    def validate(config: PilotConfiguration) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        enabled_ids = config.enabled_eval_ids()
        enabled_set = set(enabled_ids)
        if "EVAL-002" in enabled_set and "EVAL-001" not in enabled_set:
            errors.append("EVAL-002 requires EVAL-001 — cannot measure divergence without baseline.")
        if "EVAL-007" in enabled_set and config.cohort.window_days < 14:
            errors.append(f"EVAL-007 requires pre/post windows of >=14 days. Current: {config.cohort.window_days}.")
        if "EVAL-008" in enabled_set and not config.workflow.workflow_id:
            errors.append("EVAL-008 requires a workflow definition.")
        if "EVAL-010" in enabled_set and "EVAL-006" not in enabled_set:
            errors.append("EVAL-010 requires EVAL-006 — cannot assess concentration without composition.")
        if "EVAL-011" in enabled_set and "EVAL-007" not in enabled_set:
            errors.append("EVAL-011 requires EVAL-007 — development loop needs intervention.")
        if "EVAL-012" in enabled_set and not config.governance.authorized_by:
            errors.append("EVAL-012 requires governance.authorized_by — experiments need authorization.")
        if "EVAL-013" in enabled_set:
            warnings.append("EVAL-013 (Org AI Topology) is not yet implemented.")
        if "EVAL-014" in enabled_set:
            warnings.append("EVAL-014 (Operator Similarity Search) is not yet implemented.")
        if config.gates.enabled:
            metric_to_evals = {"leverage": {"EVAL-001","EVAL-003","EVAL-005"},"yield": {"EVAL-001","EVAL-003","EVAL-005"},"construction": {"EVAL-001","EVAL-003"},"token_snr": {"EVAL-001","EVAL-003","EVAL-005"}}
            for rule in config.gates.rules:
                producing = metric_to_evals.get(rule.metric_id, set())
                if producing and not (enabled_set & producing):
                    errors.append(f"Gate {rule.rule_id} gates on '{rule.metric_id}' but no enabled eval produces it. Enable one of: {sorted(producing)}.")
        if config.outcome_join.enabled and "EVAL-001" not in enabled_set and "EVAL-002" not in enabled_set:
            errors.append("Outcome join requires EVAL-001 or EVAL-002 — need baseline before correlating outcomes.")
        level_1_evals = {"EVAL-001","EVAL-002","EVAL-003","EVAL-004","EVAL-006","EVAL-008","EVAL-009","EVAL-010"}
        if config.deployment_level >= 2 and not (enabled_set - level_1_evals):
            warnings.append(f"Deployment level {config.deployment_level} selected but all evals work at Level 1.")
        for sel in config.eval_families:
            if sel.enabled and sel.eval_id not in EVAL_FAMILIES:
                errors.append(f"Unknown eval ID: {sel.eval_id}")
        if config.deployment_level not in (1, 2, 3):
            errors.append(f"Invalid deployment level: {config.deployment_level}. Must be 1, 2, or 3.")
        if config.cohort.window_days < 7 or config.cohort.window_days > 90:
            errors.append(f"Invalid window_days: {config.cohort.window_days}. Must be 7-90.")
        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
