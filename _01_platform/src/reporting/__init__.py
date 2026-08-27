"""Reporting — export pilot data in JSON, CSV, and Markdown formats.

P0-F: produces the deliverables cataloged in `13_ENTERPRISE_REPORTING_DELIVERABLES.md`.
All exporters take a PilotService and return a string.
"""
from __future__ import annotations

from .exporters import (
    export_cohort_json, export_cohort_csv, export_cohort_markdown,
    export_operator_json, export_operator_markdown,
    export_pilot_markdown, export_data_quality_markdown,
    export_intervention_outcomes_markdown,
    export_hypothesis_map, export_remeasurement_report,
    export_preferred_manager_objects_markdown,
    decision_use_label_diagnosis, decision_use_label_intervention,
    decision_use_label_outcome_join, decision_use_label_personnel,
    export_artifacts, export_lineages, export_canonical_inventory,
)
from .executive_brief import export_executive_brief
from .config_report import export_configuration_report
from .dashboard import generate_executive_dashboard
from .decision_report import (
    build_decision_report,
    build_operator_decision_report,
    build_cohort_decision_report,
    export_decision_report_markdown,
)

__all__ = [
    "export_cohort_json", "export_cohort_csv", "export_cohort_markdown",
    "export_operator_json", "export_operator_markdown",
    "export_pilot_markdown", "export_data_quality_markdown",
    "export_intervention_outcomes_markdown",
    "export_hypothesis_map", "export_remeasurement_report",
    "export_preferred_manager_objects_markdown",
    "decision_use_label_diagnosis", "decision_use_label_intervention",
    "decision_use_label_outcome_join", "decision_use_label_personnel",
    "export_executive_brief",
    "export_configuration_report",
    "generate_executive_dashboard",
    "export_artifacts", "export_lineages", "export_canonical_inventory",
    "build_decision_report",
    "build_operator_decision_report",
    "build_cohort_decision_report",
    "export_decision_report_markdown",
]
