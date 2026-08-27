"""Exporters — produce JSON, CSV, and Markdown reports from PilotService.

Each exporter takes a PilotService and returns a string. Report objects carry
status labels per `13`: FACT, MEASUREMENT, DERIVED, HYPOTHESIS, RECOMMENDATION,
EXPERIMENT, OUTCOME, LIMITATION.
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from service import PilotService


def export_cohort_json(svc: "PilotService") -> str:
    """Export full cohort data as JSON."""
    c = svc.cohort
    dists = svc.cohort_distributions()
    div = svc.divergence()
    medians = svc.cohort_medians()
    return json.dumps({
        "report_type": "cohort_export",
        "cohort_id": c.cohort_id,
        "window": {"start": c.window_start.isoformat(), "end": c.window_end.isoformat()},
        "operators": len(svc.operators),
        "metric_registry_version": svc.engine.registry.registry_version,
        "reference_field_version": svc.reference_population.version,
        "medians": medians,
        "distributions": {k: v.to_dict() for k, v in dists.items()},
        "divergence": [
            {
                "operator_id": r.operator_id,
                "usage_percentile": r.usage_percentile,
                "yield_percentile": r.yield_percentile,
                "leverage_percentile": r.leverage_percentile,
                "divergence_pp": r.divergence_pp,
                "divergence_class": r.divergence_class,
            }
            for r in div
        ],
        "synthetic": True,
    }, indent=2, ensure_ascii=False)


def export_cohort_csv(svc: "PilotService") -> str:
    """Export cohort operator metrics as CSV."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=[
        "operator_id", "team", "leverage", "yield", "token_snr",
        "log_leverage", "construction", "leverage_percentile",
        "yield_percentile", "divergence_class",
    ])
    w.writeheader()
    pcts = svc.percentiles()
    div_map = {r.operator_id: r for r in svc.divergence()}
    op_teams = {o.operator_id: o.team for o in svc.operators}

    for oid in svc.operator_ids:
        ms = svc.score_operator(oid)
        m_map = {m.metric_id: m for m in ms}
        pct = pcts.get(oid, {})
        div = div_map.get(oid)
        w.writerow({
            "operator_id": oid,
            "team": op_teams.get(oid, ""),
            "leverage": m_map.get("leverage").value if m_map.get("leverage") else "",
            "yield": m_map.get("yield").value if m_map.get("yield") else "",
            "token_snr": m_map.get("token_snr").value if m_map.get("token_snr") else "",
            "log_leverage": m_map.get("log_leverage").value if m_map.get("log_leverage") else "",
            "construction": m_map.get("construction").value if m_map.get("construction") else "",
            "leverage_percentile": pct.get("leverage_percentile").value if pct.get("leverage_percentile") else "",
            "yield_percentile": pct.get("yield_percentile").value if pct.get("yield_percentile") else "",
            "divergence_class": div.divergence_class if div else "",
        })
    return buf.getvalue()


def export_cohort_markdown(svc: "PilotService") -> str:
    """Export cohort summary as a Markdown report."""
    c = svc.cohort
    medians = svc.cohort_medians()
    dists = svc.cohort_distributions()
    div_counts = svc.divergence_counts()
    dq = svc.data_quality_summary()

    lines = [
        f"# Cohort Report: {c.cohort_id}",
        "",
        f"**[FACT]** Window: {c.window_start} to {c.window_end}",
        f"**[FACT]** Operators: {len(svc.operators)}",
        f"**[FACT]** Metric registry version: {svc.engine.registry.registry_version}",
        f"**[FACT]** Reference field version: {svc.reference_population.version}",
        f"**[FACT]** Synthetic: YES",
        "",
        "## Median Metrics",
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
        "## Distributions",
        "",
    ])
    for mid, dist in dists.items():
        lines.append(f"### {mid}")
        lines.append(f"- **[MEASUREMENT]** count: {dist.count}")
        lines.append(f"- **[MEASUREMENT]** min: {dist.min_val}, p10: {dist.p10}, p25: {dist.p25}")
        lines.append(f"- **[MEASUREMENT]** median: {dist.median}, p75: {dist.p75}, p90: {dist.p90}")
        lines.append(f"- **[MEASUREMENT]** max: {dist.max_val}")
        lines.append(f"- **[DERIVED]** mean: {dist.mean}, std: {dist.std}")
        if dist.outliers:
            lines.append(f"- **[LIMITATION]** outliers: {', '.join(dist.outliers)}")
        lines.append("")

    lines.extend([
        "## Usage vs Operation Divergence",
        "",
        "| Class | Count |",
        "|-------|-------|",
    ])
    for cls, count in sorted(div_counts.items()):
        lines.append(f"| {cls} | {count} |")

    lines.extend([
        "",
        "## Data Quality",
        "",
        f"- **[MEASUREMENT]** OK: {dq.get('OK', 0)}",
        f"- **[MEASUREMENT]** WARNING: {dq.get('WARNING', 0)}",
        f"- **[MEASUREMENT]** BLOCKING: {dq.get('BLOCKING', 0)}",
        "",
        "---",
        "*This report was generated from synthetic demo data. All values are placeholders.*",
    ])
    return "\n".join(lines) + "\n"


def export_operator_json(svc: "PilotService", operator_id: str) -> str:
    """Export a single operator profile as JSON."""
    profile = svc.operator_profile(operator_id)
    elig = svc.operator_eligibility(operator_id)
    profile["eligibility"] = elig.to_dict()
    return json.dumps(profile, indent=2, ensure_ascii=False)


def export_operator_markdown(svc: "PilotService", operator_id: str) -> str:
    """Export a single operator profile as Markdown."""
    profile = svc.operator_profile(operator_id)
    if "error" in profile:
        return f"# Error\n\n{profile['error']}\n"

    op = profile["operator"]
    ms = profile["measurements"]
    pcts = profile["percentiles"]
    diags = profile["diagnoses"]
    elig = svc.operator_eligibility(operator_id)

    lines = [
        f"# Operator Profile: {op['pseudonym']}",
        "",
        f"**[FACT]** Operator ID: {op['operator_id']}",
        f"**[FACT]** Team: {op.get('team', 'N/A')}",
        f"**[FACT]** Role family: {op.get('role_family', 'N/A')}",
        f"**[FACT]** Pattern fixture: {op.get('pattern_demo', 'N/A')}",
        f"**[FACT]** Synthetic: YES",
        f"**[MEASUREMENT]** Eligibility: {'ELIGIBLE' if elig.passed else 'BLOCKED'} — {elig.reason}",
        "",
        "## Canonical Metrics",
        "",
        "| Metric | Value | Status | Eligibility |",
        "|--------|-------|--------|-------------|",
    ]
    for m in ms:
        val = f"{m['value']:.4f}" if m.get("value") is not None else "N/A"
        lines.append(f"| {m['metric_id']} | {val} | {m['status']} | {m['eligibility']} |")

    lines.extend(["", "## Reference Percentiles", "", "| Metric | Percentile |", "|--------|-----------|"])
    for mid, pct in pcts.items():
        lines.append(f"| {mid} | {pct['value']:.1f} |")

    if diags:
        lines.extend(["", "## Diagnostic Hypotheses", "", f"**[GOVERNANCE]** Decision use: {decision_use_label_diagnosis()}", ""])
        for d in diags:
            lines.append(f"### {d['pattern_id']}")
            lines.append(f"**[HYPOTHESIS]** Status: {d['status'].upper()}")
            lines.append(f"**[HYPOTHESIS]** Confidence: {d['confidence']}")
            lines.append(f"**[HYPOTHESIS]** Evidence: {d['evidence']}")
            if d.get("recommended_interventions"):
                lines.append(f"**[RECOMMENDATION]** Interventions: {', '.join(d['recommended_interventions'])}")
            lines.append("**[LIMITATION]** This is a hypothesis, not a causal finding.")
            lines.append("")

    lines.extend([
        "---",
        "*This profile was generated from synthetic demo data.*",
    ])
    return "\n".join(lines) + "\n"


def export_pilot_markdown(svc: "PilotService") -> str:
    """Export a full pilot summary as Markdown (deliverable #1 + #2)."""
    status = svc.pilot_status()
    dq = svc.data_quality()
    dists = svc.cohort_distributions()
    medians = svc.cohort_medians()

    lines = [
        f"# Pilot Status: {status['cohort_id']}",
        "",
        f"**[FACT]** Window: {status['window']['start']} to {status['window']['end']}",
        f"**[FACT]** Eligible operators: {status['eligible_operators']}/{status['total_operators']}",
        f"**[FACT]** Providers: {', '.join(status['providers'])}",
        f"**[FACT]** Observations: {status['observation_count']}",
        f"**[FACT]** Metric registry: {status['metric_registry_version']}",
        f"**[FACT]** Reference field: {status['reference_field_version']}",
        f"**[FACT]** Active interventions: {status['active_interventions']}",
        f"**[FACT]** Synthetic: YES",
        "",
        "## Data Quality + Eligibility",
        "",
        "| Check | OK | Warning | Blocking |",
        "|-------|-----|---------|----------|",
    ]
    for check_name, results in dq.items():
        ok = sum(1 for r in results if r.passed and r.severity.value == "OK")
        warn = sum(1 for r in results if r.severity.value == "WARNING")
        block = sum(1 for r in results if r.severity.value == "BLOCKING")
        lines.append(f"| {check_name} | {ok} | {warn} | {block} |")

    lines.extend(["", "## Workforce Operating Map", "", "| Metric | Median | p10 | p90 |", "|--------|--------|-----|------|"])
    for mid in ("leverage", "yield", "token_snr", "construction"):
        dist = dists.get(mid)
        if dist:
            lines.append(f"| {mid} | {dist.median} | {dist.p10} | {dist.p90} |")

    lines.extend([
        "",
        "---",
        "*This report was generated from synthetic demo data. All values are placeholders.*",
    ])
    return "\n".join(lines) + "\n"


def export_data_quality_markdown(svc: "PilotService") -> str:
    """Export the Data Quality + Eligibility Report (deliverable #1)."""
    dq = svc.data_quality()
    summary = svc.data_quality_summary()
    elig = svc.eligibility()

    lines = [
        "# Data Quality + Eligibility Report",
        "",
        f"**[FACT]** Cohort: {svc.cohort.cohort_id}",
        f"**[FACT]** Synthetic: YES",
        "",
        "## Summary",
        "",
        f"- **[MEASUREMENT]** OK: {summary.get('OK', 0)}",
        f"- **[MEASUREMENT]** WARNING: {summary.get('WARNING', 0)}",
        f"- **[MEASUREMENT]** BLOCKING: {summary.get('BLOCKING', 0)}",
        "",
        "## Eligibility",
        "",
        "| Operator | Passed | Severity | Reason |",
        "|----------|--------|----------|--------|",
    ]
    for oid, r in sorted(elig.items()):
        lines.append(f"| {oid} | {'YES' if r.passed else 'NO'} | {r.severity.value} | {r.reason} |")

    lines.extend(["", "## Detailed Checks", ""])
    for check_name, results in dq.items():
        if not results:
            continue
        lines.append(f"### {check_name}")
        lines.append("")
        for r in results:
            label = "OK" if r.passed else r.severity.value
            lines.append(f"- **[{label}]** {r.operator_id}: {r.reason}")
        lines.append("")

    lines.extend([
        "---",
        "*This report was generated from synthetic demo data.*",
    ])
    return "\n".join(lines) + "\n"


def export_intervention_outcomes_markdown(svc: "PilotService", results: list) -> str:
    """Export intervention × outcome cross-analysis as Markdown.

    Per P2: every result is labeled ASSOCIATION — never CAUSATION.
    Internal metric deltas and external outcome deltas are shown side-by-side.
    """
    lines = [
        "# Intervention × Outcome Analysis",
        "",
        f"**[FACT]** Cohort: {svc.cohort.cohort_id}",
        f"**[FACT]** Synthetic: YES",
        f"**[LIMITATION]** All results labeled ASSOCIATION — never CAUSATION.",
        f"**[GOVERNANCE]** Decision use: {decision_use_label_intervention()}",
        "",
    ]

    for r in results:
        if isinstance(r, dict):
            r_dict = r
        else:
            r_dict = r.to_dict()

        lines.extend([
            f"## {r_dict['intervention_id']} — Operator {r_dict['operator_id']}",
            "",
            f"**[EXPERIMENT]** Intervention with predeclared target metric: {r_dict['target_metric']}",
            f"**[FACT]** Sample size: {r_dict['sample_size']}",
            "",
            "### Internal Metric Deltas (from telemetry)",
            "",
            "| Metric | % Delta |",
            "|--------|---------|",
        ])
        for mid, delta in r_dict.get("internal_metric_deltas", {}).items():
            val = f"{delta:+.1f}%" if delta is not None else "N/A"
            lines.append(f"| {mid} | {val} |")

        lines.extend([
            "",
            "### External Outcome Deltas (from customer data)",
            "",
            "| Outcome Metric | Value |",
            "|----------------|-------|",
        ])
        for mid, val in r_dict.get("external_outcome_deltas", {}).items():
            v = f"{val:.2f}" if val is not None else "N/A"
            lines.append(f"| {mid} | {v} |")

        lines.extend([
            "",
            f"**[OUTCOME]** Claim type: {r_dict['claim_type']}",
            f"**[LIMITATION]** A correlation between an intervention and a business metric is not proof that the intervention caused the business change.",
            "",
        ])

    lines.extend([
        "---",
        "*This report was generated from synthetic demo data. All results are ASSOCIATION, not CAUSATION.*",
    ])
    return "\n".join(lines) + "\n"


# ── Deliverable #6: Hypothesis Map ───────────────────────────────────────

def export_hypothesis_map(svc) -> str:
    """Deliverable #6: Strength/Weakness Hypothesis Map.

    Per `13` §6: Pattern → evidence → alternative explanation → intervention candidate.
    Each diagnosis is labeled HYPOTHESIS — never PROVEN.
    """
    diags = svc.diagnoses
    lines = [
        "# Hypothesis Map — Strength/Weakness Diagnostics",
        "",
        f"**[FACT]** Cohort: {svc.cohort.cohort_id}",
        f"**[FACT]** Window: {svc.cohort.window_start} to {svc.cohort.window_end}",
        f"**[FACT]** Total hypotheses: {len(diags)}",
        f"**[LIMITATION]** All diagnoses are HYPOTHESIS — not causal findings.",
        f"**[GOVERNANCE]** Decision use: {decision_use_label_diagnosis()}",
        "",
    ]

    # Group by operator
    by_op: dict[str, list] = {}
    for d in diags:
        by_op.setdefault(d.operator_id, []).append(d)

    for oid in sorted(by_op.keys()):
        op_diags = by_op[oid]
        lines.append(f"## Operator {oid}")
        lines.append("")
        for d in op_diags:
            d_dict = d.to_dict() if hasattr(d, "to_dict") else d
            lines.extend([
                f"### {d_dict.get('pattern_id', 'unknown')}",
                f"**[HYPOTHESIS]** Status: {d_dict.get('status', 'HYPOTHESIS')}",
                f"**[MEASUREMENT]** Evidence: {d_dict.get('evidence', 'N/A')}",
                f"**[HYPOTHESIS]** Confidence: {d_dict.get('confidence', 'N/A')}",
                f"**[RECOMMENDATION]** Interventions: {', '.join(d_dict.get('recommended_interventions', []))}",
                "",
            ])

    lines.extend([
        "---",
        "*This report was generated from synthetic demo data. "
        "All diagnoses are HYPOTHESIS — not causal findings.*",
    ])
    return "\n".join(lines) + "\n"


# ── Deliverable #8: Re-measurement Report ────────────────────────────────

def export_remeasurement_report(svc) -> str:
    """Deliverable #8: Re-measurement Report.

    Per `13` §8: Before/after operator measurements and uncertainty.
    Uses the PrePostVerifier to compute target + non-target deltas for
    each intervention.
    """
    ivs = svc.interventions
    lines = [
        "# Re-measurement Report — Pre/Post Intervention",
        "",
        f"**[FACT]** Cohort: {svc.cohort.cohort_id}",
        f"**[FACT]** Window: {svc.cohort.window_start} to {svc.cohort.window_end}",
        f"**[FACT]** Interventions: {len(ivs)}",
        f"**[GOVERNANCE]** Decision use: {decision_use_label_intervention()}",
        "",
    ]

    for iv in ivs:
        try:
            vr = svc.verify_intervention(iv.intervention_id)
        except Exception as e:
            lines.extend([
                f"## {iv.intervention_id} — Operator {iv.operator_id}",
                f"**[LIMITATION]** Verification error: {e}",
                "",
            ])
            continue

        vr_dict = vr.to_dict() if hasattr(vr, "to_dict") else vr
        td = vr_dict.get("target_delta", {})
        lines.extend([
            f"## {iv.intervention_id} — Operator {iv.operator_id}",
            f"**[EXPERIMENT]** Target metric: {vr_dict.get('target_metric', 'N/A')}",
            f"**[FACT]** Outcome: {vr_dict.get('outcome', 'N/A')}",
            f"**[MEASUREMENT]** Target delta: {td.get('percent_delta', 'N/A')}%",
            f"**[FACT]** Summary: {vr_dict.get('summary', 'N/A')}",
            "",
        ])

        # Non-target deltas
        non_target = vr_dict.get("non_target_deltas", [])
        if non_target:
            lines.append("| Metric | % Delta |")
            lines.append("|--------|---------|")
            for nd in non_target:
                lines.append(f"| {nd.get('metric_id', '?')} | {nd.get('percent_delta', 'N/A')}% |")
            lines.append("")

    lines.extend([
        "---",
        "*This report was generated from synthetic demo data. "
        "Metric deltas are MEASUREMENT — not causal claims.*",
    ])
    return "\n".join(lines) + "\n"


# ── Decision-use labels (per `12` §Decision-use restrictions) ──────────────
# These helpers surface the decision-use classification on each product
# surface. They are additive — existing exporter functions are unchanged.
# The preferred-manager-objects exporter below uses them.

def decision_use_label_diagnosis() -> str:
    """Decision-use label for diagnostic surfaces (DEVELOPMENTAL)."""
    from governance import DecisionUse
    return DecisionUse.DEVELOPMENTAL.label()


def decision_use_label_intervention() -> str:
    """Decision-use label for intervention/experiment surfaces (WORKFLOW_EXPERIMENTATION)."""
    from governance import DecisionUse
    return DecisionUse.WORKFLOW_EXPERIMENTATION.label()


def decision_use_label_outcome_join() -> str:
    """Decision-use label for outcome-join surfaces (RESEARCH)."""
    from governance import DecisionUse
    return DecisionUse.RESEARCH.label()


def decision_use_label_personnel() -> str:
    """Decision-use label for personnel-decision surfaces (PERSONNEL — elevated governance)."""
    from governance import DecisionUse
    return DecisionUse.PERSONNEL.label()


def export_preferred_manager_objects_markdown(svc: "PilotService") -> str:
    """Export the 8 preferred manager objects as Markdown (per `12`).

    These are developmental objects, NOT performance rankings. The
    avoid-list (no leaderboard, no punitive labels, no composite score)
    is enforced; this exporter surfaces the positive half of the
    development doctrine.
    """
    objs = svc.preferred_manager_objects()
    lines = [
        "# Preferred Manager Objects",
        "",
        f"**[FACT]** Cohort: {svc.cohort.cohort_id}",
        f"**[FACT]** Synthetic: YES",
        f"**[LIMITATION]** These are developmental objects, NOT performance rankings.",
        f"**[EXPERIMENT]** Decision use: DEVELOPMENTAL — for developmental use; not for personnel decisions.",
        "",
    ]
    object_titles = {
        "development_groups": "Development Groups (cohorts advancing together)",
        "fastest_improvers": "Fastest Improvers (operators with positive trajectory)",
        "stalled_cohorts": "Stalled Cohorts (groups plateaued at the same level)",
        "workflow_bottlenecks": "Workflow Bottlenecks (shared structural friction)",
        "tool_model_fit_opportunities": "Tool/Model-Fit Opportunities (operators whose metrics shift across models)",
        "training_candidates": "Training Candidates (operators whose patterns match an intervention)",
        "peer_support_matches": "Peer-Support Matches (complementary operator profiles)",
        "remeasurement_queue": "Remeasurement Queue (interventions awaiting follow-up)",
    }
    for obj_name, title in object_titles.items():
        findings = objs.get(obj_name, [])
        lines.extend([f"## {title}", "", f"- **[MEASUREMENT]** Count: {len(findings)}", ""])
        if not findings:
            lines.extend(["*No findings for this object in the current window.*", ""])
            continue
        for f in findings:
            lines.append(f"- **[DERIVED]** {f.get('evidence', '')}")
            if "framing" in f:
                lines.append(f"  - *{f['framing']}*")
            if "operator_ids" in f:
                lines.append(f"  - Operators: {', '.join(f['operator_ids'][:10])}{' …' if len(f['operator_ids']) > 10 else ''}")
            elif "operator_id" in f:
                lines.append(f"  - Operator: {f['operator_id']}")
            lines.append("")
    lines.extend([
        "---",
        "*This report was generated from synthetic demo data. All objects are developmental, not rankings.*",
    ])
    return "\n".join(lines) + "\n"


# ── Canonical domain object exporters (artifacts, lineages, inventory) ────

def export_artifacts(svc: "PilotService", fmt: str = "json") -> str:
    """Export artifacts as JSON or CSV.

    Each artifact is a concrete output of AI-assisted work (code file,
    document, config, etc.). Content is NOT stored — only metadata.
    """
    artifacts = svc.artifacts
    if fmt == "json":
        return json.dumps(
            [a.to_dict() for a in artifacts],
            indent=2, ensure_ascii=False,
        )
    elif fmt == "csv":
        buf = io.StringIO()
        fieldnames = [
            "artifact_id", "operator_id", "artifact_type", "synthetic",
            "observation_id", "file_path", "lines_added", "lines_removed",
            "commit_sha", "created_at",
        ]
        w = csv.DictWriter(buf, fieldnames=fieldnames)
        w.writeheader()
        for a in artifacts:
            d = a.to_dict()
            w.writerow(d)
        return buf.getvalue()
    else:
        raise ValueError(f"Unknown format: {fmt}. Available: json, csv")


def export_lineages(svc: "PilotService", fmt: str = "json") -> str:
    """Export lineages as JSON or CSV.

    Each lineage is a chain linking states, actions, transformations,
    artifacts, and outcomes. The micro_eval dict carries aggregate
    micro-evaluation scores for the chain.
    """
    lineages = svc.lineages
    if fmt == "json":
        return json.dumps(
            [l.to_dict() for l in lineages],
            indent=2, ensure_ascii=False,
        )
    elif fmt == "csv":
        buf = io.StringIO()
        fieldnames = [
            "lineage_id", "operator_id", "workflow_id", "workflow_stage",
            "synthetic", "link_count",
        ]
        w = csv.DictWriter(buf, fieldnames=fieldnames)
        w.writeheader()
        for l in lineages:
            d = l.to_dict()
            w.writerow({
                "lineage_id": d["lineage_id"],
                "operator_id": d["operator_id"],
                "workflow_id": d.get("workflow_id", ""),
                "workflow_stage": d.get("workflow_stage", ""),
                "synthetic": d.get("synthetic", ""),
                "link_count": len(d.get("links", [])),
            })
        return buf.getvalue()
    else:
        raise ValueError(f"Unknown format: {fmt}. Available: json, csv")


def export_canonical_inventory(svc: "PilotService") -> dict:
    """Return a dict summarizing all canonical objects now loaded.

    Provides counts of each canonical domain object type available
    through the service layer. Useful for data-availability checks
    and reporting dashboards.
    """
    return {
        "operators": len(svc.operators),
        "observations": len(svc.observations),
        "observations_full": len(svc.observations_full),
        "artifacts": len(svc.artifacts),
        "lineages": len(svc.lineages),
        "outcomes": len(svc.outcomes),
        "teams": len(svc.teams),
        "workflows": len(svc.workflows),
        "systems": len(svc.systems),
        "workflow_observations": len(svc.workflow_observations),
        "diagnoses": len(svc.diagnoses),
        "interventions": len(svc.interventions),
        "cohort_id": svc.cohort.cohort_id,
        "synthetic": True,
    }
