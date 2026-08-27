"""Executive Solution Brief — the final pilot readout deliverable.

Per `13_ENTERPRISE_REPORTING_DELIVERABLES.md`:
- Deliverable #11: Executive Solution Brief — "communicates decisions and next
  experiments"
- Deliverable #12: Next Evaluations Flywheel — "3-4 evidence-backed observations
  mapped to specific next evaluations from the eval catalog (`18`)"

The brief includes:
    1. Cohort summary (size, window, data quality)
    2. Key findings (top patterns, divergence counts, concentration)
    3. Intervention results
    4. Workflow fit summary
    5. Next-evaluations flywheel (3-4 observations → eval family mappings)

Each next-evaluation references measured data and maps to an eval family ID
from `18_ENTERPRISE_EVAL_CATALOG.md`. Next evaluations are framed as
experiments, not outcome claims.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from service import PilotService


# Eval family mappings for the next-evaluations flywheel.
# Maps a finding type to the recommended eval family from `18`.
_EVAL_MAPPING = {
    "concentration": ("EVAL-010", "Capability Dependency Risk"),
    "workflow_stall": ("EVAL-008", "Workflow Stage Fit"),
    "model_sensitivity": ("EVAL-005", "Platform / Model Sensitivity"),
    "divergence": ("EVAL-002", "Usage vs Operation Divergence"),
    "longitudinal": ("EVAL-004", "Longitudinal Movement"),
    "intervention_response": ("EVAL-007", "Intervention Response"),
    "cohort_composition": ("EVAL-006", "Cohort Composition"),
    "training": ("EVAL-011", "Development Engine"),
}


def _generate_next_evaluations(svc: "PilotService") -> List[dict]:
    """Generate 3-4 evidence-backed next-evaluation recommendations.

    Each recommendation references measured data and maps to an eval family
    from `18`. Framed as experiments, not outcome claims.

    Per `13` deliverable #12: "Outputs 3–4 evidence-backed observations, each
    mapped to a specific next evaluation from the eval catalog (`18`)."
    """
    recommendations: List[dict] = []
    cohort_patterns = svc.detect_cohort_patterns()
    div_counts = svc.divergence_counts()
    wf_report = svc.workflow_fit_report()

    # 1. Pattern concentration — if a pattern affects many operators
    pattern_counts: Counter = Counter()
    for oid, patterns in cohort_patterns.items():
        for p in patterns:
            pattern_counts[p.pattern_id] += 1

    if pattern_counts:
        top_pattern_id, top_count = pattern_counts.most_common(1)[0]
        if top_count >= 3:
            eval_id, eval_name = _EVAL_MAPPING.get("concentration", ("EVAL-010", "Capability Dependency Risk"))
            recommendations.append({
                "observation": f"Pattern {top_pattern_id} detected in {top_count} of {len(svc.operator_ids)} operators — capability may be concentrated rather than distributed.",
                "next_evaluation": f"{eval_id} ({eval_name}) — matched cohort with pre/post measurement to test whether enablement reduces concentration.",
                "evidence": f"Pattern engine detected {top_pattern_id} in {top_count} operators.",
                "eval_family": eval_id,
            })

    # 2. Divergence — if there are high-usage/low-operation operators
    high_usage_low = div_counts.get("HIGH_USAGE_LOW_OPERATION", 0)
    if high_usage_low >= 2:
        eval_id, eval_name = _EVAL_MAPPING.get("divergence", ("EVAL-002", "Usage vs Operation Divergence"))
        recommendations.append({
            "observation": f"{high_usage_low} operators show high usage but low operating metrics — they may be burning context without output.",
            "next_evaluation": f"{eval_id} ({eval_name}) — targeted intervention cohort to test whether workflow or tooling changes improve operating metrics.",
            "evidence": f"Divergence analysis found {high_usage_low} HIGH_USAGE_LOW_OPERATION operators.",
            "eval_family": eval_id,
        })

    # 3. Workflow fit — if stages have low average provisional fit
    # Uses the workflow fit report's stage-level data (measured, not speculated).
    by_stage = svc.workflow_fit_by_stage()
    low_fit_stages = []
    for stage_id, wobs in by_stage.items():
        fits = [w.provisional_fit for w in wobs if w.provisional_fit is not None]
        if fits:
            avg_fit = sum(fits) / len(fits)
            if avg_fit < 0.7:
                low_fit_stages.append((stage_id, avg_fit, len(wobs)))
    if low_fit_stages:
        # Pick the lowest-fit stage as the most actionable
        low_fit_stages.sort(key=lambda x: x[1])
        worst_stage, worst_avg, worst_count = low_fit_stages[0]
        eval_id, eval_name = _EVAL_MAPPING.get("workflow_stall", ("EVAL-008", "Workflow Stage Fit"))
        recommendations.append({
            "observation": f"Workflow stage '{worst_stage}' has the lowest average provisional fit ({worst_avg:.2f}) across {worst_count} operators — operators may be stalling at this stage.",
            "next_evaluation": f"{eval_id} ({eval_name}) — workflow redesign before additional operator training, with stage-level pre/post measurement.",
            "evidence": f"Workflow fit engine: stage '{worst_stage}' avg provisional fit = {worst_avg:.2f} across {worst_count} operators.",
            "eval_family": eval_id,
        })

    # 4. Intervention outcomes — if there are representable failures
    # Per P1: "intervention failure is representable and reportable."
    # Uses measured intervention outcomes, not speculation.
    failures = [iv for iv in svc.interventions if iv.synthetic_outcome.value in ("NEGATIVE", "NO_EFFECT")]
    if failures:
        eval_id, eval_name = _EVAL_MAPPING.get("intervention_response", ("EVAL-007", "Intervention Response"))
        recommendations.append({
            "observation": f"{len(failures)} interventions resulted in NEGATIVE or NO_EFFECT outcomes — the intervention design may need revision before scaling.",
            "next_evaluation": f"{eval_id} ({eval_name}) — re-measure with revised intervention parameters or alternative catalog entries to test whether a different approach moves the target metric.",
            "evidence": f"{len(failures)} interventions with NEGATIVE/NO_EFFECT outcome status.",
            "eval_family": eval_id,
        })

    # If we still have fewer than 3, add a longitudinal recommendation
    # based on the cohort window (always available — it's measured data).
    if len(recommendations) < 3:
        eval_id, eval_name = _EVAL_MAPPING.get("longitudinal", ("EVAL-004", "Longitudinal Movement"))
        c = svc.cohort
        window_days = (c.window_end - c.window_start).days
        recommendations.append({
            "observation": f"The {window_days}-day baseline window captures a single snapshot — without longitudinal data, trend direction is unknown for all {len(svc.operator_ids)} operators.",
            "next_evaluation": f"{eval_id} ({eval_name}) — extend measurement to a second window and compare per-operator metric movement to distinguish trend from noise.",
            "evidence": f"Baseline window is {window_days} days ({c.window_start} to {c.window_end}); no longitudinal comparison available.",
            "eval_family": eval_id,
        })

    # Cap at 4 per the deliverable spec
    return recommendations[:4]


def export_executive_brief(svc: "PilotService") -> str:
    """Generate the Executive Solution Brief as Markdown.

    Per `13` deliverable #11 + #12: communicates decisions, next experiments,
    and the next-evaluations flywheel.
    """
    status = svc.pilot_status()
    dq = svc.data_quality_summary()
    medians = svc.cohort_medians()
    div_counts = svc.divergence_counts()
    cohort_patterns = svc.detect_cohort_patterns()

    # Count patterns by type
    pattern_counts: Counter = Counter()
    for oid, patterns in cohort_patterns.items():
        for p in patterns:
            pattern_counts[p.pattern_id] += 1

    # Top 3 patterns by operator count
    top_patterns = pattern_counts.most_common(3)

    # Intervention outcomes
    ivs = svc.interventions
    iv_outcomes = Counter(iv.synthetic_outcome.value for iv in ivs)

    # Workflow fit
    wf_report = svc.workflow_fit_report()

    # Next evaluations
    next_evals = _generate_next_evaluations(svc)

    lines = [
        "# Executive Solution Brief",
        "",
        f"**[FACT]** Cohort: {status['cohort_id']}",
        f"**[FACT]** Window: {status['window']['start']} to {status['window']['end']}",
        f"**[FACT]** Operators: {status['total_operators']} ({status['eligible_operators']} eligible)",
        f"**[FACT]** Observations: {status['observation_count']}",
        f"**[FACT]** Metric registry: {status['metric_registry_version']}",
        f"**[FACT]** Reference field: {status['reference_field_version']}",
        f"**[FACT]** Synthetic: YES",
        "",
        "## Data Quality Summary",
        "",
        f"- **[MEASUREMENT]** OK: {dq.get('OK', 0)}",
        f"- **[MEASUREMENT]** WARNING: {dq.get('WARNING', 0)}",
        f"- **[MEASUREMENT]** BLOCKING: {dq.get('BLOCKING', 0)}",
        "",
        "## Workforce Operating Map",
        "",
        "| Metric | Median |",
        "|--------|--------|",
    ]
    for mid in ("leverage", "yield", "token_snr", "construction"):
        val = medians.get(mid)
        cell = f"{val:.4f}" if val is not None else "N/A"
        lines.append(f"| {mid} | {cell} |")

    lines.extend([
        "",
        "## Key Findings",
        "",
    ])

    if top_patterns:
        lines.extend([
            "### Top Patterns (by operator count)",
            "",
            "| Pattern | Operators |",
            "|---------|-----------|",
        ])
        for pid, count in top_patterns:
            lines.append(f"| {pid} | {count} |")
        lines.append("")
    else:
        lines.extend([
            "### Top Patterns",
            "",
            "No patterns detected above threshold.",
            "",
        ])

    lines.extend([
        "### Usage vs Operation Divergence",
        "",
        "| Class | Count |",
        "|-------|-------|",
    ])
    for cls, count in sorted(div_counts.items()):
        lines.append(f"| {cls} | {count} |")

    lines.extend([
        "",
        "## Intervention Results",
        "",
        "| Outcome | Count |",
        "|---------|-------|",
    ])
    for outcome, count in sorted(iv_outcomes.items()):
        lines.append(f"| {outcome} | {count} |")

    lines.extend([
        "",
        "## Workflow Fit Summary",
        "",
        f"- **[MEASUREMENT]** Fit claims: {wf_report.summary.get('fit_claim', 0)}",
        f"- **[MEASUREMENT]** Provisional observations: {wf_report.summary.get('provisional', 0)}",
        f"- **[MEASUREMENT]** Insufficient sample: {wf_report.summary.get('insufficient_sample', 0)}",
        f"- **[LIMITATION]** No fit claim below minimum sample rule ({wf_report.min_sample_rule}).",
        "",
    ])

    # Next Evaluations Flywheel (deliverable #12)
    lines.extend([
        "## Next Evaluations",
        "",
        "Each observation is evidence-backed and maps to a specific eval family from the catalog. Next evaluations are experiments, not outcome claims.",
        "",
    ])

    if next_evals:
        for i, rec in enumerate(next_evals, 1):
            lines.extend([
                f"### {i}. {rec['eval_family']}",
                "",
                f"**[MEASUREMENT]** Observation: {rec['observation']}",
                f"**[EXPERIMENT]** Next evaluation: {rec['next_evaluation']}",
                f"**[MEASUREMENT]** Evidence: {rec['evidence']}",
                "",
            ])
    else:
        lines.extend([
            "No next-evaluation recommendations at this time. Complete the baseline pilot and re-assess.",
            "",
        ])

    lines.extend([
        "---",
        "*This brief was generated from synthetic demo data. All findings are descriptive. Next evaluations are experiments with predeclared metrics, not outcome claims.*",
    ])
    return "\n".join(lines) + "\n"
