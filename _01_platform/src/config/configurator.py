"""PilotConfigurator — maps outcomes/evals to a PilotConfiguration."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional
from domain.pilot_configuration import (
    PilotConfiguration, EvalFamilySelection, CohortConfig, WorkflowConfig,
    GatesConfig, OutcomeJoinConfig, GovernanceConfig, ReferencePopulationConfig,
    GateRuleConfig,
)
from .eval_registry import EVAL_FAMILIES, get_eval
from .pilot_registry import COMMERCIAL_PILOTS, get_pilot

_DEFAULT_GATE_RULES = [
    GateRuleConfig("GATE-001","leverage",10,"below","FLAG_FOR_REVIEW",True,"Flag operators below 10th percentile in leverage."),
    GateRuleConfig("GATE-002","yield",10,"below","ROUTE_TO_INTERVENTION",True,"Route operators below 10th percentile in yield to intervention."),
    GateRuleConfig("GATE-003","construction",25,"below","NOTIFY",True,"Notify when operators fall below 25th percentile in construction."),
]

class PilotConfigurator:
    @staticmethod
    def from_outcome(pilot_id: str, config_id: str = "", name: str = "", description: str = "",
                     cohort: Optional[CohortConfig] = None, gates_enabled: bool = False,
                     outcome_join_enabled: bool = False, outcome_csv_path: str = "",
                     outcome_metrics: Optional[List[str]] = None, authorized_by: str = "",
                     created_by: str = "") -> PilotConfiguration:
        pilot = get_pilot(pilot_id)
        if not config_id: config_id = f"cfg_pilot_{pilot_id}"
        if not name: name = pilot.name
        if not description: description = pilot.question
        return PilotConfiguration(
            config_id=config_id, mode="outcome_packaged", commercial_pilot_id=pilot_id,
            name=name, description=description,
            eval_families=[EvalFamilySelection(eval_id=eid, enabled=True) for eid in pilot.eval_families],
            cohort=cohort or CohortConfig(window_days=30, synthetic=True),
            deployment_level=pilot.deployment_level, workflow=WorkflowConfig(),
            gates=GatesConfig(enabled=gates_enabled, rules=list(_DEFAULT_GATE_RULES) if gates_enabled else []),
            outcome_join=OutcomeJoinConfig(enabled=outcome_join_enabled, outcome_csv_path=outcome_csv_path, outcome_metrics=outcome_metrics or []),
            governance=GovernanceConfig(synthetic=True, decision_use_default="DEVELOPMENTAL", authorized_by=authorized_by),
            created_at=datetime.now(timezone.utc).isoformat(), created_by=created_by,
        )

    @staticmethod
    def from_alacarte(eval_ids: List[str], config_id: str = "", name: str = "", description: str = "",
                      cohort: Optional[CohortConfig] = None, deployment_level: int = 1,
                      workflow: Optional[WorkflowConfig] = None, gates_enabled: bool = False,
                      gate_rules: Optional[List[GateRuleConfig]] = None,
                      outcome_join_enabled: bool = False, outcome_csv_path: str = "",
                      outcome_metrics: Optional[List[str]] = None, authorized_by: str = "",
                      created_by: str = "") -> PilotConfiguration:
        for eid in eval_ids:
            if eid not in EVAL_FAMILIES:
                raise ValueError(f"Unknown eval ID: {eid}. Valid IDs: {list(EVAL_FAMILIES.keys())}")
        if not config_id: config_id = f"cfg_alacarte_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        if not name: name = "Custom — " + ", ".join(eval_ids)
        return PilotConfiguration(
            config_id=config_id, mode="a_la_carte", commercial_pilot_id=None,
            name=name, description=description,
            eval_families=[EvalFamilySelection(eval_id=eid, enabled=True) for eid in eval_ids],
            cohort=cohort or CohortConfig(window_days=30, synthetic=True),
            deployment_level=deployment_level, workflow=workflow or WorkflowConfig(),
            gates=GatesConfig(enabled=gates_enabled, rules=gate_rules if gate_rules is not None else (list(_DEFAULT_GATE_RULES) if gates_enabled else [])),
            outcome_join=OutcomeJoinConfig(enabled=outcome_join_enabled, outcome_csv_path=outcome_csv_path, outcome_metrics=outcome_metrics or []),
            governance=GovernanceConfig(synthetic=True, decision_use_default="DEVELOPMENTAL", authorized_by=authorized_by),
            created_at=datetime.now(timezone.utc).isoformat(), created_by=created_by,
        )

    @staticmethod
    def save(config: PilotConfiguration, file_path: str) -> str:
        from pathlib import Path
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(config.to_json(), encoding="utf-8")
        return str(p)

    @staticmethod
    def load(file_path: str) -> PilotConfiguration:
        from pathlib import Path
        return PilotConfiguration.from_json(Path(file_path).read_text(encoding="utf-8"))
