"""TUI application — 10-screen pilot console using rich.

Per `06_TUI_PRODUCT_SPEC.md`. All screens call PilotService.
Supports `--theme dark|light` for WCAG AA-compliant colors on both
dark and light terminal backgrounds.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich.columns import Columns
from rich.theme import Theme

from service import PilotService

# ── WCAG AA-compliant color themes ───────────────────────────────────────────
# 256-color values chosen to pass 4.5:1 contrast on their intended background.
# Dark theme: brighter colors for readability on dark terminals.
# Light theme: darker colors for readability on white/light terminals.

_DARK_THEME = Theme({
    "red":       "#ff5f5f",  # 256-color 203 — 5.6:1 on dark
    "green":     "#5fd75f",  # 256-color 77  — 9.0:1 on dark
    "yellow":    "#ffd700",  # 256-color 220 — 11.8:1 on dark
    "blue":      "#87afd7",  # 256-color 110 — 7.5:1 on dark (panel borders)
    "cyan":      "#5fd7d7",  # 256-color 80  — 8.5:1 on dark
    "magenta":   "#af87af",  # 256-color 139 — 6.5:1 on dark
    "bold red":  "#ff5f5f",
    "bold cyan": "#5fd7d7",
    "dim":       "#767676",  # 256-color 242 — 4.5:1 on dark (dim threshold 3:1)
})

_LIGHT_THEME = Theme({
    "red":       "#af0000",  # 256-color 124 — 7.4:1 on white
    "green":     "#008700",  # 256-color 28  — 4.7:1 on white
    "yellow":    "#af5f00",  # 256-color 130 — 4.7:1 on white
    "blue":      "#0000af",  # 256-color 19  — 13.0:1 on white
    "cyan":      "#005f87",  # 256-color 24  — 7.0:1 on white
    "magenta":   "#870087",  # 256-color 90  — 8.8:1 on white
    "bold red":  "#af0000",
    "bold cyan": "#005f87",
    "dim":       "#767676",  # 256-color 242 — 4.5:1 on white
})

_THEMES = {"dark": _DARK_THEME, "light": _LIGHT_THEME}


class TuiApp:
    """The 11-screen pilot analyst console."""

    def __init__(self, data_dir: Optional[str] = None, theme: str = "dark") -> None:
        self.svc = PilotService(data_dir)
        self.theme_name = theme if theme in _THEMES else "dark"
        self.console = Console(theme=_THEMES[self.theme_name])

    def run(self) -> None:
        """Main loop."""
        self.console.clear()
        self.console.print(Panel.fit(
            "[bold]ENTERPRISE OPERATOR INTELLIGENCE[/bold]\n"
            "Synthetic Pilot Console — MO§ES™\n"
            "All data is SYNTHETIC",
            border_style="blue",
        ))
        while True:
            self._show_menu()
            choice = Prompt.ask("Select", default="1")
            if choice == "0":
                break
            handler = {
                "1": self.screen_pilot,
                "2": self.screen_cohort,
                "3": self.screen_operator,
                "4": self.screen_divergence,
                "5": self.screen_diagnose,
                "6": self.screen_workflow,
                "7": self.screen_interventions,
                "8": self.screen_verify,
                "9": self.screen_data_quality,
                "g": self.screen_gates,
                "c": self.screen_configure,
                "e": self.screen_export,
            }.get(choice)
            if handler:
                try:
                    handler()
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")
                Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

    def _show_menu(self) -> None:
        self.console.print(
            "\n[bold cyan]1[/bold cyan] Pilot  "
            "[bold cyan]2[/bold cyan] Cohort  "
            "[bold cyan]3[/bold cyan] Operator  "
            "[bold cyan]4[/bold cyan] Divergence  "
            "[bold cyan]5[/bold cyan] Diagnose\n"
            "[bold cyan]6[/bold cyan] Workflow  "
            "[bold cyan]7[/bold cyan] Interventions  "
            "[bold cyan]8[/bold cyan] Verify  "
            "[bold cyan]9[/bold cyan] Data Quality\n"
            "[bold cyan]g[/bold cyan] Gates  "
            "[bold cyan]c[/bold cyan] Configure  "
            "[bold cyan]e[/bold cyan] Export  "
            "[bold cyan]0[/bold cyan] Exit"
        )

    # ── Screen 1: Pilot ──────────────────────────────────────────────────

    def screen_pilot(self) -> None:
        status = self.svc.pilot_status()
        c = self.svc.cohort
        self.console.print(Panel.fit(
            f"[bold]PILOT STATUS[/bold]\n\n"
            f"Cohort: {status['cohort_id']}\n"
            f"Window: {status['window']['start']} to {status['window']['end']}\n"
            f"Eligible: {status['eligible_operators']}/{status['total_operators']} operators\n"
            f"Providers: {', '.join(status['providers'])}\n"
            f"Observations: {status['observation_count']}\n"
            f"Metric Registry: {status['metric_registry_version']}\n"
            f"Reference Field: {status['reference_field_version']}\n"
            f"Active Interventions: {status['active_interventions']}\n"
            f"Synthetic: YES",
            title="[1] PILOT",
            border_style="blue",
        ))
        dq = status["data_quality"]
        t = Table(title="Data Quality Summary")
        t.add_column("Severity"); t.add_column("Count", justify="right")
        for k in ("OK", "WARNING", "BLOCKING"):
            t.add_row(k, str(dq.get(k, 0)))
        self.console.print(t)

    # ── Screen 2: Cohort ─────────────────────────────────────────────────

    # Abbreviation map for divergence classes (keeps tables narrow)
    _DIV_ABBREV = {
        "HIGH_USAGE_LOW_OPERATION": "HI-USAGE/LO-OP",
        "LOW_USAGE_HIGH_OPERATION": "LO-USAGE/HI-OP",
        "LOW_LOW": "LO/LO",
        "MIXED": "MIXED",
    }

    def screen_cohort(self) -> None:
        pcts = self.svc.percentiles()
        div_map = {r.operator_id: r for r in self.svc.divergence()}
        op_teams = {o.operator_id: o.team for o in self.svc.operators}

        t = Table(title="[2] COHORT — Operators with Percentiles", show_lines=False)
        t.add_column("Operator", no_wrap=True)
        t.add_column("Team")
        t.add_column("Usage %ile", justify="right", no_wrap=True)
        t.add_column("Yield %ile", justify="right", no_wrap=True)
        t.add_column("Lev %ile", justify="right", no_wrap=True)
        t.add_column("SNR", justify="right", no_wrap=True)
        t.add_column("Divergence", no_wrap=True)
        for oid in self.svc.operator_ids:
            ms = self.svc.score_operator(oid)
            m_map = {m.metric_id: m for m in ms}
            pct = pcts.get(oid, {})
            div = div_map.get(oid)
            snr = m_map.get("token_snr")
            t.add_row(
                oid,
                op_teams.get(oid, ""),
                f"{div.usage_percentile:.0f}" if div else "—",
                f"{pct.get('yield_percentile').value:.0f}" if pct.get('yield_percentile') else "—",
                f"{pct.get('leverage_percentile').value:.0f}" if pct.get('leverage_percentile') else "—",
                f"{snr.value:.3f}" if snr and snr.value else "—",
                self._DIV_ABBREV.get(div.divergence_class, div.divergence_class) if div else "—",
            )
        self.console.print(t)

    # ── Screen 3: Operator ───────────────────────────────────────────────

    def screen_operator(self) -> None:
        oid = Prompt.ask("Operator ID", default="op_031")
        op = self.svc.get_operator(oid)
        if not op:
            self.console.print(f"[red]Unknown operator {oid}[/red]")
            return
        ms = self.svc.score_operator(oid)
        pcts = self.svc.percentiles().get(oid, {})
        elig = self.svc.operator_eligibility(oid)

        self.console.print(Panel.fit(
            f"[bold]{op.pseudonym}[/bold] | {op.team} | {op.role_family}\n"
            f"Pattern: {op.pattern_demo} | Synthetic: YES\n"
            f"Eligibility: {'ELIGIBLE' if elig.passed else 'BLOCKED'} — {elig.reason}",
            title=f"[3] OPERATOR {oid}",
        ))

        t = Table(title="Canonical Metrics")
        t.add_column("Metric", no_wrap=True)
        t.add_column("Value", justify="right")
        t.add_column("Status", no_wrap=True)
        t.add_column("Eligibility", no_wrap=True)
        for m in ms:
            val = f"{m.value:.4f}" if m.value is not None else "N/A"
            # Shorten status for display (CANONICAL_WITH_INTERPRETATION_NEEDED → CANONICAL*)
            status = m.status.value
            if status == "CANONICAL_WITH_INTERPRETATION_NEEDED":
                status = "CANONICAL*"
            t.add_row(m.metric_id, val, status, m.eligibility)
        for mid in ("leverage_percentile", "yield_percentile"):
            pm = pcts.get(mid)
            if pm:
                t.add_row(mid, f"{pm.value:.1f}", "DERIVED", pm.eligibility)
        self.console.print(t)
        self.console.print("[dim]  * = CANONICAL_WITH_INTERPRETATION_NEEDED[/dim]")

    # ── Screen 4: Divergence ─────────────────────────────────────────────

    def screen_divergence(self) -> None:
        results = self.svc.divergence()
        counts = self.svc.divergence_counts()

        t = Table(title="[4] DIVERGENCE — Usage vs Operation")
        t.add_column("Class", no_wrap=True); t.add_column("Count", justify="right")
        for k, v in sorted(counts.items()):
            t.add_row(k, str(v))
        self.console.print(t)

        t2 = Table(title="Largest Divergences")
        t2.add_column("Operator", no_wrap=True)
        t2.add_column("Usage %ile", justify="right")
        t2.add_column("Yield %ile", justify="right")
        t2.add_column("Δ pp", justify="right")
        t2.add_column("Class", no_wrap=True)
        for r in results[:15]:
            t2.add_row(
                r.operator_id,
                f"{r.usage_percentile:.1f}",
                f"{r.yield_percentile:.1f}",
                f"{r.divergence_pp:+.1f}",
                self._DIV_ABBREV.get(r.divergence_class, r.divergence_class),
            )
        self.console.print(t2)

    # ── Screen 5: Diagnose ───────────────────────────────────────────────

    def screen_diagnose(self) -> None:
        oid = Prompt.ask("Operator ID (or 'cohort' for all)", default="op_031")
        if oid == "cohort":
            diags = self.svc.diagnoses
        else:
            diags = self.svc.diagnoses_for(oid)
        if not diags:
            self.console.print("[yellow]No diagnostic hypotheses found.[/yellow]")
            return
        for d in diags:
            self.console.print(Panel(
                f"[bold]{d.pattern_id}[/bold]  [yellow]{d.status.value.upper()}[/yellow]\n"
                f"Operator: {d.operator_id}\n"
                f"Evidence: {d.evidence}\n"
                f"Confidence: {d.confidence}\n"
                f"Interventions: {', '.join(d.recommended_interventions)}\n\n"
                f"[red]HYPOTHESIS — not a causal finding[/red]",
                title=f"[5] DIAGNOSE — {d.operator_id}",
            ))

    # ── Screen 6: Workflow ───────────────────────────────────────────────

    def screen_workflow(self) -> None:
        by_stage = self.svc.workflow_fit_by_stage()
        wf = self.svc.workflow
        self.console.print(Panel.fit(
            f"Workflow: {wf.workflow_id} | {len(wf.stages)} stages | Synthetic",
            title="[6] WORKFLOW",
        ))
        t = Table(title="Stage Fit — Top Operators per Stage")
        t.add_column("Stage", no_wrap=True); t.add_column("Top Operators")
        for stage_id in sorted(by_stage.keys()):
            top = by_stage[stage_id][:5]
            t.add_row(stage_id, ", ".join(
                f"{w.operator_id} ({w.provisional_fit:.2f})" for w in top if w.provisional_fit is not None
            ))
        self.console.print(t)

    # ── Screen 7: Interventions ──────────────────────────────────────────

    def screen_interventions(self) -> None:
        ivs = self.svc.interventions
        t = Table(title="[7] INTERVENTIONS — Synthetic")
        for c in ("ID", "Operator", "Catalog", "Pattern", "Target", "Start", "Outcome"):
            t.add_column(c, no_wrap=True)
        for iv in ivs:
            t.add_row(
                iv.intervention_id, iv.operator_id, iv.catalog_id,
                iv.reason_pattern, iv.target_metric,
                iv.start_date.isoformat(), iv.synthetic_outcome.value,
            )
        self.console.print(t)

    # ── Screen 8: Verify ─────────────────────────────────────────────────

    def screen_verify(self) -> None:
        ivs = self.svc.interventions
        c = self.svc.cohort
        t = Table(title="[8] VERIFY — Pre/Post Intervention (computed from telemetry)")
        for col in ("Operator", "Intervention", "Target", "Outcome", "Baseline Lev", "Eligible"):
            t.add_column(col, no_wrap=True)
        for iv in ivs:
            elig = self.svc.operator_eligibility(iv.operator_id)
            ms = self.svc.score_operator(iv.operator_id)
            lev = next((m for m in ms if m.metric_id == "leverage"), None)
            t.add_row(
                iv.operator_id, iv.intervention_id, iv.target_metric,
                iv.synthetic_outcome.value,
                f"{lev.value:.3f}" if lev and lev.value else "—",
                "YES" if elig.passed else "NO",
            )
        self.console.print(t)

    # ── Screen 9: Data Quality ───────────────────────────────────────────

    def screen_data_quality(self) -> None:
        dq = self.svc.data_quality()
        summary = self.svc.data_quality_summary()
        self.console.print(Panel.fit(
            f"OK: {summary.get('OK', 0)} | WARNING: {summary.get('WARNING', 0)} | BLOCKING: {summary.get('BLOCKING', 0)}",
            title="[9] DATA QUALITY",
        ))
        t = Table(title="Checks")
        t.add_column("Check", no_wrap=True); t.add_column("OK", justify="right")
        t.add_column("Warning", justify="right"); t.add_column("Blocking", justify="right")
        for check_name, results in dq.items():
            ok = sum(1 for r in results if r.severity.value == "OK")
            warn = sum(1 for r in results if r.severity.value == "WARNING")
            block = sum(1 for r in results if r.severity.value == "BLOCKING")
            t.add_row(check_name, str(ok), str(warn), str(block))
        self.console.print(t)

    # ── Screen G: Gates ──────────────────────────────────────────────────

    def screen_gates(self) -> None:
        self.console.print(Panel(
            "[bold]Production Gates[/bold]\n"
            "Threshold-based routing — DEVELOPMENTAL use only.\n"
            "Gates route work, not people.",
            title="[G] GATES",
            border_style="yellow",
        ))
        summary = self.svc.evaluate_cohort_gates()
        self.console.print(f"\nTotal evaluations: {summary['total_evaluations']}")
        self.console.print(f"Total fired: [bold red]{summary['total_fired']}[/bold red]")
        self.console.print(f"Operators flagged: [bold]{summary['operators_flagged']}[/bold]")
        if summary.get("by_action"):
            t = Table(title="By Action")
            t.add_column("Action", no_wrap=True)
            t.add_column("Count", justify="right")
            for action, count in summary["by_action"].items():
                t.add_row(action, str(count))
            self.console.print(t)
        fired = summary.get("fired_gates", [])
        if fired:
            t = Table(title="Fired Gates")
            t.add_column("Rule", no_wrap=True)
            t.add_column("Operator", no_wrap=True)
            t.add_column("Metric", no_wrap=True)
            t.add_column("Value", justify="right")
            t.add_column("Threshold", justify="right")
            t.add_column("Action", no_wrap=True)
            for g in fired[:20]:
                t.add_row(
                    g["rule_id"],
                    g["operator_id"],
                    g["metric_id"],
                    f"{g['metric_value']:.2f}" if g["metric_value"] is not None else "N/A",
                    f"{g['threshold']:.2f}",
                    g["action"],
                )
            self.console.print(t)
            if len(fired) > 20:
                self.console.print(f"[dim]... and {len(fired) - 20} more[/dim]")
        else:
            self.console.print("[green]No gates fired.[/green]")

    # ── Screen C: Configure (Bespoke Pilot Menu) ──────────────────────────

    def screen_configure(self) -> None:
        """Bespoke pilot menu — choose by outcome or build à la carte."""
        from config import PilotConfigurator, ConfigValidator, COMMERCIAL_PILOTS, EVAL_FAMILIES

        self.console.print(Panel.fit(
            "[bold]BESPOKE PILOT CONFIGURATOR[/bold]\n\n"
            "Two paths:\n"
            "  1. Choose by outcome (pre-packaged commercial pilots)\n"
            "  2. Build your own (à la carte eval selection)\n\n"
            "All data is SYNTHETIC. All results are DEVELOPMENTAL.",
            title="[C] CONFIGURE",
            border_style="cyan",
        ))
        path = Prompt.ask("Path", choices=["1", "2"], default="1")

        if path == "1":
            # Outcome-packaged: list pilots, pick one
            t = Table(title="Commercial Pilots")
            t.add_column("ID"); t.add_column("Name"); t.add_column("Evals"); t.add_column("Level")
            for pid, p in COMMERCIAL_PILOTS.items():
                t.add_row(pid, p.name, ", ".join(p.eval_families), str(p.deployment_level))
            self.console.print(t)
            pilot_id = Prompt.ask("Pilot ID (1-12)", default="1")
            if pilot_id not in COMMERCIAL_PILOTS:
                self.console.print(f"[red]Unknown pilot: {pilot_id}[/red]")
                return
            gates = Prompt.ask("Enable gates?", choices=["y", "n"], default="n") == "y"
            save_path = Prompt.ask("Save to file (blank=don't save)", default="")
            cfg = PilotConfigurator.from_outcome(
                pilot_id=pilot_id, gates_enabled=gates, created_by="tui",
            )
        else:
            # À la carte: list evals, toggle on/off
            t = Table(title="Eval Families")
            t.add_column("ID"); t.add_column("Name"); t.add_column("Status"); t.add_column("Notes")
            for eid, e in EVAL_FAMILIES.items():
                status = "[green]full[/green]" if e.implementation_status == "full" else \
                         "[yellow]partial[/yellow]" if e.implementation_status == "partial" else \
                         "[red]not implemented[/red]"
                t.add_row(eid, e.name, status, e.description[:60])
            self.console.print(t)
            eval_input = Prompt.ask("Enabled evals (comma-separated)", default="EVAL-001,EVAL-002")
            eval_ids = [e.strip() for e in eval_input.split(",") if e.strip()]
            level = IntPrompt.ask("Deployment level (1-3)", default=1)
            gates = Prompt.ask("Enable gates?", choices=["y", "n"], default="n") == "y"
            save_path = Prompt.ask("Save to file (blank=don't save)", default="")
            try:
                cfg = PilotConfigurator.from_alacarte(
                    eval_ids=eval_ids, deployment_level=level,
                    gates_enabled=gates, created_by="tui",
                )
            except ValueError as e:
                self.console.print(f"[red]Error: {e}[/red]")
                return

        # Validate
        result = ConfigValidator.validate(cfg)
        if result.errors:
            self.console.print("[red]Validation errors:[/red]")
            for err in result.errors:
                self.console.print(f"  [red]✗[/red] {err}")
        else:
            self.console.print("[green]Validation: PASSED[/green]")
        if result.warnings:
            for warn in result.warnings:
                self.console.print(f"  [yellow]⚠[/yellow] {warn}")

        # Show config summary
        self.console.print(Panel.fit(
            f"[bold]Configuration: {cfg.name}[/bold]\n\n"
            f"Config ID: {cfg.config_id}\n"
            f"Mode: {cfg.mode}\n"
            f"Commercial Pilot: {cfg.commercial_pilot_id or 'N/A'}\n"
            f"Eval Families: {', '.join(cfg.enabled_eval_ids())}\n"
            f"Deployment Level: {cfg.deployment_level}\n"
            f"Window: {cfg.cohort.window_days} days\n"
            f"Gates: {'enabled' if cfg.gates.enabled else 'disabled'}\n"
            f"Outcome Join: {'enabled' if cfg.outcome_join.enabled else 'disabled'}\n"
            f"Governance: synthetic={cfg.governance.synthetic}, "
            f"decision_use={cfg.governance.decision_use_default}",
            title="CONFIGURATION SUMMARY",
            border_style="cyan",
        ))

        if save_path:
            PilotConfigurator.save(cfg, save_path)
            self.console.print(f"[green]Saved to: {save_path}[/green]")


    # ── Screen E: Export ─────────────────────────────────────────────────

    def screen_export(self) -> None:
        fmt = Prompt.ask("Format", choices=["json", "csv", "md"], default="md")
        target = Prompt.ask("Export", choices=["cohort", "operator", "pilot", "brief"], default="pilot")
        if target == "operator":
            oid = Prompt.ask("Operator ID", default="op_031")
            output = self.svc.export_operator(oid, fmt)
        elif target == "cohort":
            output = self.svc.export_cohort(fmt)
        elif target == "brief":
            output = self.svc.executive_brief()
        else:
            from reporting import export_pilot_markdown
            output = export_pilot_markdown(self.svc)
        # Print to console (in production, write to file)
        self.console.print(Panel(output[:5000] + ("..." if len(output) > 5000 else ""),
                                 title=f"[E] EXPORT — {target} ({fmt})"))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Enterprise Pilot TUI")
    parser.add_argument("--theme", choices=["dark", "light"], default="dark",
                        help="Color theme (default: dark)")
    parser.add_argument("--data-dir", default=None, help="Data directory")
    args = parser.parse_args()
    app = TuiApp(data_dir=args.data_dir, theme=args.theme)
    app.run()


if __name__ == "__main__":
    main()
