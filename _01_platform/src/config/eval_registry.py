"""Eval family registry — codifies the 15 eval families (EVAL-001–EVAL-015)
and the 10 engine types (§6.1–§6.10) from the MO§ES™ enterprise pilot
readiness framework.

The 15 eval families are the canonical commercial taxonomy (what the buyer
asks). The 10 engine types are the pipeline implementation pattern (how the
engine runs). Every eval family maps to one or more engine types.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass(frozen=True, slots=True)
class EvalFamily:
    eval_id: str
    name: str
    description: str
    implemented: bool
    implementation_status: str
    service_methods: List[str] = field(default_factory=list)
    cli_commands: List[str] = field(default_factory=list)
    mcp_tools: List[str] = field(default_factory=list)
    tui_screens: List[str] = field(default_factory=list)
    requires_pre_post_windows: bool = False
    requires_workflow: bool = False
    engine_types: List[str] = field(default_factory=list)

EVAL_FAMILIES: Dict[str, EvalFamily] = {
    "EVAL-001": EvalFamily("EVAL-001","Operator Baseline","Canonical metrics, eligibility, reference percentiles.",True,"full",["score_operator","percentiles","operator_eligibility","compare_operator_to_reference"],["score operator","compare cohort"],["get_operator_profile","compare_operator_to_reference"],["3"],engine_types=["6.1"]),
    "EVAL-002": EvalFamily("EVAL-002","Usage vs Operation Divergence","Divergence quadrants and outliers.",True,"full",["divergence","divergence_counts"],["compare usage-operation"],["find_usage_operation_divergence"],["4"],engine_types=["6.1"]),
    "EVAL-003": EvalFamily("EVAL-003","Context Architecture","Reuse/construction patterns with provider caveats.",True,"partial",["score_operator","detect_patterns"],["score operator","diagnose operator"],["get_operator_profile","get_diagnostics"],["3","5"],engine_types=["6.2"]),
    "EVAL-004": EvalFamily("EVAL-004","Longitudinal Movement","Metric change, stability, band movement.",True,"partial",["score_operator","replicate_finding"],["score operator"],["get_operator_profile"],["3"],engine_types=["6.4"]),
    "EVAL-005": EvalFamily("EVAL-005","Platform / Model Sensitivity","Within-operator metric differences across models. Operator×System decomposition separates operator, system, and interaction effects.",True,"full",["detect_patterns","score_operator","operator_system_decomposition"],["compare models","compare operator-system","diagnose operator"],["get_diagnostics","get_operator_system_decomposition"],["5"],engine_types=["6.6","6.7"]),
    "EVAL-006": EvalFamily("EVAL-006","Cohort Composition","Distributions, concentration, coverage.",True,"full",["cohort_distributions","cohort_medians","cohort_summary_raw"],["cohort show","compare cohort"],["get_cohort_distribution","get_cohort_overview"],["2"],engine_types=["6.10"]),
    "EVAL-007": EvalFamily("EVAL-007","Intervention Response","Target/non-target metric changes. Outcome correlation through lineage connects operating patterns to downstream consequences (ASSOCIATION, not causation).",True,"full",["assign_intervention","close_intervention","verify_intervention","verify_all_interventions","outcome_correlation","lineage_chain"],["intervention assign","intervention close","verify intervention","lineage show","lineage outcomes"],["assign_intervention","close_intervention","verify_change","get_outcome_correlation","get_lineage_chain","get_lineage_summary"],["7","8"],requires_pre_post_windows=True,engine_types=["6.9"]),
    "EVAL-008": EvalFamily("EVAL-008","Workflow Stage Fit","Provisional/replicated stage relationships.",True,"full",["workflow_fit_report","workflow_fit_by_stage"],["workflow fit"],["get_workflow_fit"],["6"],requires_workflow=True,engine_types=["6.8"]),
    "EVAL-009": EvalFamily("EVAL-009","Team Composition","Coverage and complementarity hypotheses.",True,"partial",["compare_teams"],["compare teams"],["get_cohort_overview"],["2"],engine_types=["6.3"]),
    "EVAL-010": EvalFamily("EVAL-010","Capability Dependency Risk","Single-point-of-failure/coverage risk.",True,"partial",["detect_cohort_patterns"],["diagnose cohort"],["get_diagnostics"],["5"],engine_types=["6.3"]),
    "EVAL-011": EvalFamily("EVAL-011","Development Engine","Diagnosis→intervention→re-measure trajectory.",True,"full",["generate_diagnoses","recommend_interventions","assign_intervention","verify_intervention"],["diagnose","intervention","verify"],["get_diagnostics","assign_intervention","verify_change"],["5","7","8"],requires_pre_post_windows=True,engine_types=["6.9"]),
    "EVAL-012": EvalFamily("EVAL-012","Experiment as Product","Governed enterprise experiment.",True,"full",["create_experiment","experiments"],[],["create_experiment"],[],engine_types=[]),
    "EVAL-013": EvalFamily("EVAL-013","Org AI Topology","Organization-level map of AI operating structure.",True,"full",["org_topology"],["compare topology"],["get_org_topology"],["2"],engine_types=["6.3","6.10"]),
    "EVAL-014": EvalFamily("EVAL-014","Operator Similarity Search","Nearest comparable operators/cohorts.",True,"full",["operator_similarity"],["compare similarity"],["get_operator_similarity"],["3"],engine_types=["6.10"]),
    "EVAL-015": EvalFamily("EVAL-015","AI Learning Curve","Rate/shape of operator change with uncertainty.",True,"partial",["replicate_finding","verify_intervention"],[],["verify_change"],["8"],engine_types=["6.5"]),
}

# Engine type → eval family mapping (the "how" → "what" cross-reference)
ENGINE_TYPE_TO_FAMILIES: Dict[str, List[str]] = {
    "6.1": ["EVAL-001", "EVAL-002"],
    "6.2": ["EVAL-003"],
    "6.3": ["EVAL-009", "EVAL-010"],
    "6.4": ["EVAL-004"],
    "6.5": ["EVAL-015"],
    "6.6": ["EVAL-005"],
    "6.7": ["EVAL-005", "EVAL-006"],
    "6.8": ["EVAL-008"],
    "6.9": ["EVAL-007", "EVAL-011"],
    "6.10": ["EVAL-006", "EVAL-014"],
}

def get_eval(eval_id: str) -> EvalFamily:
    return EVAL_FAMILIES[eval_id]

def all_eval_ids() -> List[str]:
    return list(EVAL_FAMILIES.keys())

def implemented_eval_ids() -> List[str]:
    return [eid for eid, e in EVAL_FAMILIES.items() if e.implemented]

def engine_types_for_eval(eval_id: str) -> List[str]:
    """Return the engine types that produce this eval family."""
    return EVAL_FAMILIES[eval_id].engine_types

def families_for_engine_type(engine_type: str) -> List[str]:
    """Return the eval families produced by this engine type."""
    return ENGINE_TYPE_TO_FAMILIES.get(engine_type, [])
