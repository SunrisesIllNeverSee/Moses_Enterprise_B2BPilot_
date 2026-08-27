"""Configuration export report — generates a Markdown report from a PilotConfiguration.

Per the bespoke pilot menu system design (Phase 6). The report documents:
    - Selected evals and their service methods
    - Cohort parameters
    - Deployment level
    - Gates configuration
    - Outcome join configuration
    - Governance metadata
    - Maps each eval to CLI commands and MCP tools
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.pilot_configuration import PilotConfiguration


def export_configuration_report(config: "PilotConfiguration") -> str:
    """Generate a Markdown configuration report from a PilotConfiguration."""
    from config import EVAL_FAMILIES, COMMERCIAL_PILOTS

    lines = [
        "# Pilot Configuration Report",
        "",
        f"**Config ID:** {config.config_id}",
        f"**Name:** {config.name or '(unnamed)'}",
        f"**Mode:** {config.mode}",
        f"**Created:** {config.created_at or '(not set)'}",
        f"**Created by:** {config.created_by or '(not set)'}",
        "",
        "---",
        "",
        "## Selected Eval Families",
        "",
        "| Eval | Name | Status | Service Methods |",
        "|------|------|--------|-----------------|",
    ]

    for sel in config.eval_families:
        if not sel.enabled:
            continue
        e = EVAL_FAMILIES.get(sel.eval_id)
        if e:
            status = e.implementation_status
            methods = ", ".join(e.service_methods) if e.service_methods else "—"
        else:
            status = "unknown"
            methods = "—"
        lines.append(f"| {sel.eval_id} | {e.name if e else sel.eval_id} | {status} | {methods} |")

    lines.extend([
        "",
        "## Cohort Parameters",
        "",
        f"- **Window:** {config.cohort.window_days} days",
        f"- **Operators:** {config.cohort.min_operators}–{config.cohort.max_operators}",
        f"- **Cohort ID:** {config.cohort.cohort_id or '(auto)'}",
        f"- **Synthetic:** {config.cohort.synthetic}",
        "",
        "## Deployment Level",
        "",
        f"Level {config.deployment_level}",
        "",
    ])

    level_desc = {
        1: "Canonical Telemetry — token counts only, no prompt content.",
        2: "API Enriched — adds timestamps, sessions, model/tool/agent data.",
        3: "Integrated / Governed — continuous measurement, customer-defined thresholds.",
    }
    lines.append(f"*{level_desc.get(config.deployment_level, 'Unknown level.')}*")
    lines.append("")

    # Gates
    lines.extend(["## Production Gates", "", f"**Enabled:** {config.gates.enabled}", ""])
    if config.gates.enabled and config.gates.rules:
        lines.extend([
            "| Gate | Metric | Threshold | Direction | Action | Description |",
            "|------|--------|-----------|-----------|--------|-------------|",
        ])
        for rule in config.gates.rules:
            lines.append(
                f"| {rule.rule_id} | {rule.metric_id} | {rule.threshold} | "
                f"{rule.direction} | {rule.action} | {rule.description} |"
            )
        lines.append("")
        lines.append("*Gates are DEVELOPMENTAL — they route work, not people.*")
        lines.append("")

    # Outcome join
    lines.extend(["## Outcome Join", "", f"**Enabled:** {config.outcome_join.enabled}", ""])
    if config.outcome_join.enabled:
        lines.extend([
            f"- **CSV Path:** {config.outcome_join.outcome_csv_path or '(not set)'}",
            f"- **Outcome Metrics:** {', '.join(config.outcome_join.outcome_metrics) or '(auto-detect)'}",
            f"- **Label:** {config.outcome_join.label}",
            "",
            "**[LIMITATION]** All outcome joins are ASSOCIATION — never CAUSATION.",
            "",
        ])

    # Governance
    lines.extend([
        "## Governance",
        "",
        f"- **Synthetic:** {config.governance.synthetic}",
        f"- **Decision Use:** {config.governance.decision_use_default}",
        f"- **Authorized By:** {config.governance.authorized_by or '(not set)'}",
        f"- **Privacy Class:** {config.governance.privacy_class}",
        "",
    ])

    # Commercial pilot reference
    if config.commercial_pilot_id:
        pilot = COMMERCIAL_PILOTS.get(config.commercial_pilot_id)
        if pilot:
            lines.extend([
                "## Commercial Pilot Reference",
                "",
                f"- **Pilot ID:** {pilot.pilot_id}",
                f"- **Name:** {pilot.name}",
                f"- **Question:** {pilot.question}",
                f"- **Best Buyer:** {pilot.best_buyer}",
                "",
            ])

    # Deliverables
    lines.extend([
        "## Deliverables",
        "",
        "This pilot configuration will produce:",
        "",
    ])
    enabled_ids = config.enabled_eval_ids()
    deliverables = []
    if "EVAL-001" in enabled_ids:
        deliverables.append("- Operator baseline metrics and percentiles")
    if "EVAL-002" in enabled_ids:
        deliverables.append("- Usage vs operation divergence report")
    if "EVAL-003" in enabled_ids:
        deliverables.append("- Context architecture patterns")
    if "EVAL-004" in enabled_ids:
        deliverables.append("- Longitudinal movement analysis")
    if "EVAL-005" in enabled_ids:
        deliverables.append("- Platform/model sensitivity comparison")
    if "EVAL-006" in enabled_ids:
        deliverables.append("- Cohort composition distributions")
    if "EVAL-007" in enabled_ids:
        deliverables.append("- Intervention response measurements")
    if "EVAL-008" in enabled_ids:
        deliverables.append("- Workflow stage fit report")
    if "EVAL-009" in enabled_ids:
        deliverables.append("- Team composition comparison")
    if "EVAL-010" in enabled_ids:
        deliverables.append("- Capability dependency risk assessment")
    if "EVAL-011" in enabled_ids:
        deliverables.append("- Development engine trajectory")
    if "EVAL-012" in enabled_ids:
        deliverables.append("- Experiment report")
    if "EVAL-013" in enabled_ids:
        deliverables.append("- Org AI topology map (not yet implemented)")
    if "EVAL-014" in enabled_ids:
        deliverables.append("- Operator similarity search (not yet implemented)")
    if "EVAL-015" in enabled_ids:
        deliverables.append("- AI learning curve analysis")
    if config.gates.enabled:
        deliverables.append("- Production gate evaluation results")
    if config.outcome_join.enabled:
        deliverables.append("- Outcome join correlation report (ASSOCIATION)")
    lines.extend(deliverables)
    lines.append("")

    # CLI and MCP mapping
    lines.extend([
        "---",
        "",
        "## CLI and MCP Tool Mapping",
        "",
        "| Eval | CLI Commands | MCP Tools |",
        "|------|--------------|-----------|",
    ])
    for sel in config.eval_families:
        if not sel.enabled:
            continue
        e = EVAL_FAMILIES.get(sel.eval_id)
        if e:
            cli = ", ".join(e.cli_commands) if e.cli_commands else "—"
            mcp = ", ".join(e.mcp_tools) if e.mcp_tools else "—"
            lines.append(f"| {sel.eval_id} | {cli} | {mcp} |")
    lines.extend(["", "---", ""])

    # Governance footer
    lines.extend([
        "*This configuration was generated from synthetic demo data. "
        "All results are DEVELOPMENTAL. Diagnoses are HYPOTHESIS. "
        "Outcome joins are ASSOCIATION — never CAUSATION.*",
    ])

    return "\n".join(lines) + "\n"
