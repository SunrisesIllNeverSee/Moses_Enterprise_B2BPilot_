#!/usr/bin/env python3
"""Enterprise pilot demo — CLI/TUI entry point.

P0-B refactor: this now calls the shared PilotService layer instead of
reading pre-baked CSVs directly. All metric values are COMPUTED from
telemetry observations via the ScoringEngine (closing gap #4).
"""
from datetime import date
from pathlib import Path
import sys

# Ensure src/ is on the path for imports.
_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from service import PilotService

console = Console()


def _service() -> PilotService:
    return PilotService()


def summary():
    svc = _service()
    s = svc.cohort_summary_raw
    c = svc.cohort
    medians = svc.cohort_medians()
    div_counts = svc.divergence_counts()
    console.print(Panel.fit(
        f"[bold]SYNTHETIC ENTERPRISE PILOT[/bold]\n"
        f"Cohort: {c.cohort_id} | Operators: {len(svc.operators)} | "
        f"Window: {c.window_start}/{c.window_end}\n"
        f"Registry: {s.get('metric_registry_version', '0.2')}\n"
        f"Median Leverage: {medians.get('leverage', 0):.3f}x | "
        f"Median Yield: {medians.get('yield', 0):.3f}"
    ))
    t = Table(title="Usage vs Operation divergence (computed)")
    t.add_column("Class"); t.add_column("Operators", justify="right")
    for k, v in sorted(div_counts.items()):
        t.add_row(k, str(v))
    console.print(t)


def usage_vs_operation():
    svc = _service()
    results = svc.divergence()
    t = Table(title="Largest Usage ↔ Yield Divergences (SYNTHETIC, computed)")
    for c in ["Operator", "Team", "Usage %ile", "Yield %ile", "Leverage %ile", "Δ pp", "Class"]:
        t.add_column(c)
    for r in results[:18]:
        op = svc.get_operator(r.operator_id)
        team = op.team if op else ""
        t.add_row(
            r.operator_id, team,
            f"{r.usage_percentile:.1f}", f"{r.yield_percentile:.1f}",
            f"{r.leverage_percentile:.1f}" if r.leverage_percentile is not None else "—",
            f"{r.divergence_pp:+.1f}", r.divergence_class,
        )
    console.print(t)


def operator(op):
    svc = _service()
    op_obj = svc.get_operator(op)
    if not op_obj:
        console.print(f"Unknown operator {op}")
        return
    ms = svc.score_operator(op)
    pcts = svc.percentiles().get(op, {})
    console.print(Panel.fit(
        f"[bold]{op_obj.pseudonym}[/bold] | {op_obj.team} | {op_obj.role_family}\n"
        f"Pattern fixture: {op_obj.pattern_demo} | Synthetic: YES"
    ))
    t = Table()
    t.add_column("Measurement"); t.add_column("Value"); t.add_column("Status")
    status_labels = {
        "CANONICAL": "CANONICAL",
        "CANONICAL_WITH_INTERPRETATION_LIMIT": "INTERPRETATION_LIMIT",
        "DERIVED_ENTERPRISE": "DEMO DERIVED",
    }
    for m in ms:
        label = m.metric_id.replace("_", " ").title()
        val = f"{m.value:.4f}" if m.value is not None else "N/A"
        t.add_row(label, val, status_labels.get(m.status.value, m.status.value))
    # Add percentile rows
    for mid in ("leverage_percentile", "yield_percentile"):
        pm = pcts.get(mid)
        if pm:
            t.add_row(mid.replace("_", " ").title(), f"{pm.value:.1f}", "DEMO DERIVED")
    console.print(t)


def diagnose(op):
    svc = _service()
    diags = svc.diagnoses_for(op)
    if not diags:
        console.print("No demo diagnostic hypotheses for this operator.")
        return
    for d in diags:
        console.print(Panel(
            f"[bold]{d.pattern_id}[/bold]  [yellow]{d.status.value.upper()}[/yellow]\n"
            f"Evidence: {d.evidence}\n"
            f"Demo confidence: {d.confidence}\n"
            f"Intervention candidates: {', '.join(d.recommended_interventions)}\n\n"
            f"This is a hypothesis, not a causal finding."
        ))


def workflow():
    svc = _service()
    by_stage = svc.workflow_fit_by_stage()
    t = Table(title="Software Development Workflow Fit — SYNTHETIC / PROVISIONAL")
    t.add_column("Stage"); t.add_column("Top observed operators")
    for stage_id in sorted(by_stage.keys()):
        top = by_stage[stage_id][:5]
        t.add_row(stage_id, ", ".join(
            f"{w.operator_id} ({w.provisional_fit:.3f})" for w in top if w.provisional_fit is not None
        ))
    console.print(t)


def interventions():
    svc = _service()
    ivs = svc.interventions
    t = Table(title="Interventions — SYNTHETIC")
    for c in ["ID", "Operator", "Catalog", "Pattern", "Target", "Outcome fixture"]:
        t.add_column(c)
    for iv in ivs:
        t.add_row(
            iv.intervention_id, iv.operator_id, iv.catalog_id,
            iv.reason_pattern, iv.target_metric, iv.synthetic_outcome.value,
        )
    console.print(t)


def verify():
    svc = _service()
    # Pre/post verification: re-score operators who had interventions and
    # compare baseline vs follow-up windows.
    ivs = svc.interventions
    c = svc.cohort
    t = Table(title="Pre/Post Verification — SYNTHETIC (computed)")
    for col in ["Operator", "Intervention", "Lev base→follow", "Yield base→follow"]:
        t.add_column(col)
    for iv in ivs:
        obs = svc.repo.observations_for(iv.operator_id)
        # Baseline: cohort window. Follow-up: intervention start + followup_days.
        baseline = svc.engine.score_operator(iv.operator_id, obs, c.window_start, c.window_end)
        follow_end = iv.start_date.toordinal() + iv.followup_days
        follow_end_date = date.fromordinal(follow_end)
        followup = svc.engine.score_operator(iv.operator_id, obs, iv.start_date, follow_end_date)
        b_lev = next((m for m in baseline if m.metric_id == "leverage"), None)
        f_lev = next((m for m in followup if m.metric_id == "leverage"), None)
        b_yld = next((m for m in baseline if m.metric_id == "yield"), None)
        f_yld = next((m for m in followup if m.metric_id == "yield"), None)
        def fmt(b, f):
            return f"{b.value:.4f}→{f.value:.4f}" if b and f and b.value and f.value else "—"
        t.add_row(iv.operator_id, iv.intervention_id, fmt(b_lev, f_lev), fmt(b_yld, f_yld))
    console.print(t)


def menu():
    while True:
        console.print(
            "\n[bold]1[/bold] Summary  [bold]2[/bold] Divergence  [bold]3[/bold] Operator  "
            "[bold]4[/bold] Diagnose  [bold]5[/bold] Workflow  [bold]6[/bold] Interventions  "
            "[bold]7[/bold] Verify  [bold]0[/bold] Exit"
        )
        c = Prompt.ask("Select")
        if c == "0":
            break
        if c == "1":
            summary()
        elif c == "2":
            usage_vs_operation()
        elif c == "3":
            operator(Prompt.ask("Operator ID", default="op_031"))
        elif c == "4":
            diagnose(Prompt.ask("Operator ID", default="op_031"))
        elif c == "5":
            workflow()
        elif c == "6":
            interventions()
        elif c == "7":
            verify()


def main():
    if len(sys.argv) == 1:
        return menu()
    cmd = sys.argv[1]
    if cmd == "summary":
        summary()
    elif cmd == "usage-vs-operation":
        usage_vs_operation()
    elif cmd == "operator" and len(sys.argv) > 2:
        operator(sys.argv[2])
    elif cmd == "diagnose" and len(sys.argv) > 2:
        diagnose(sys.argv[2])
    elif cmd == "workflow":
        workflow()
    elif cmd == "interventions":
        interventions()
    elif cmd == "verify":
        verify()
    else:
        console.print(
            "Commands: summary | usage-vs-operation | operator <id> | "
            "diagnose <id> | workflow | interventions | verify"
        )
        raise SystemExit(2)


if __name__ == "__main__":
    main()
