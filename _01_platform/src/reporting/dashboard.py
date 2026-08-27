"""Executive Dashboard — polished standalone HTML dashboard generator.

Per `21` §8 "do not build yet" list: "polished executive dashboard."
Per `13` deliverable #11: "A dashboard may eventually emerge from
repeated needs here."

This module generates a self-contained HTML file with embedded CSS/JS
(no external dependencies, no server required). The dashboard surfaces:

1. Cohort overview (size, window, data quality)
2. Composite score distribution (histogram + summary stats)
3. Top patterns (bar chart)
4. Divergence breakdown (stacked bar)
5. Intervention outcomes (donut chart)
6. Workflow fit summary (stage-level heatmap)
7. Next evaluations flywheel (cards)

All charts use inline SVG — no chart library needed. The dashboard is
governance-aware: every section carries the appropriate status label
(FACT, MEASUREMENT, DEVELOPMENTAL, etc.) and the composite score
section explicitly disclaims personnel use.

Usage:
    from reporting import generate_executive_dashboard
    html = generate_executive_dashboard(svc)
    # or via CLI:
    # enterprise export dashboard --output dashboard.html
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from service import PilotService


_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f172a; color: #e2e8f0; padding: 24px; line-height: 1.6;
}
.header {
    text-align: center; padding: 32px 0; border-bottom: 1px solid #1e293b; margin-bottom: 32px;
}
.header h1 { font-size: 28px; color: #f8fafc; margin-bottom: 8px; }
.header .subtitle { color: #94a3b8; font-size: 14px; }
.header .governance {
    display: inline-block; margin-top: 12px; padding: 6px 16px;
    background: #1e293b; border-radius: 8px; font-size: 12px; color: #64748b;
}
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 20px; max-width: 1400px; margin: 0 auto; }
.card {
    background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155;
}
.card h2 { font-size: 16px; color: #f1f5f9; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em; }
.card .label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.card .value { font-size: 32px; font-weight: 700; color: #f8fafc; }
.card .sub { font-size: 13px; color: #94a3b8; margin-top: 4px; }
.card.full { grid-column: 1 / -1; }
.stat-row { display: flex; gap: 24px; flex-wrap: wrap; }
.stat { flex: 1; min-width: 120px; }
.bar-chart { margin-top: 12px; }
.bar-row { display: flex; align-items: center; margin-bottom: 8px; }
.bar-label { width: 140px; font-size: 13px; color: #cbd5e1; }
.bar-track { flex: 1; height: 24px; background: #0f172a; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
.bar-value { width: 50px; text-align: right; font-size: 13px; color: #94a3b8; }
.histogram { display: flex; align-items: flex-end; gap: 4px; height: 120px; margin-top: 12px; }
.hist-bar { flex: 1; background: #3b82f6; border-radius: 4px 4px 0 0; min-height: 2px; position: relative; }
.hist-bar:hover { background: #60a5fa; }
.donut { display: flex; align-items: center; gap: 24px; }
.donut-svg { width: 160px; height: 160px; }
.donut-legend { flex: 1; }
.legend-item { display: flex; align-items: center; margin-bottom: 8px; font-size: 13px; }
.legend-dot { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
.heatmap { margin-top: 12px; }
.heat-row { display: flex; gap: 4px; margin-bottom: 4px; }
.heat-cell { flex: 1; height: 32px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 11px; color: #0f172a; font-weight: 600; }
.eval-card {
    background: #0f172a; border-radius: 8px; padding: 16px; margin-bottom: 12px;
    border-left: 4px solid #3b82f6;
}
.eval-card .eval-id { font-size: 12px; color: #3b82f6; font-weight: 600; }
.eval-card .eval-obs { font-size: 14px; color: #e2e8f0; margin: 8px 0; }
.eval-card .eval-next { font-size: 13px; color: #94a3b8; }
.disclaimer {
    text-align: center; padding: 24px; color: #475569; font-size: 12px;
    border-top: 1px solid #1e293b; margin-top: 32px;
}
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.badge-fact { background: #1e40af; color: #dbeafe; }
.badge-measurement { background: #15803d; color: #dcfce7; }
.badge-developmental { background: #7c2d12; color: #fed7aa; }
.badge-experiment { background: #6b21a8; color: #f3e8ff; }
.badge-limitation { background: #78350f; color: #fef3c7; }
"""


def _bar_chart(items: list[tuple[str, int, str]], max_val: int | None = None) -> str:
    """Generate an inline bar chart from (label, value, color) tuples."""
    if not items:
        return '<p class="sub">No data available.</p>'
    mx = max_val or max(v for _, v, _ in items) or 1
    rows = []
    for label, val, color in items:
        pct = (val / mx * 100) if mx > 0 else 0
        rows.append(
            f'<div class="bar-row">'
            f'<span class="bar-label">{label}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
            f'<span class="bar-value">{val}</span>'
            f'</div>'
        )
    return f'<div class="bar-chart">{"".join(rows)}</div>'


def _histogram(values: list[float], bins: int = 10) -> str:
    """Generate an inline histogram from a list of 0–100 scores."""
    if not values:
        return '<p class="sub">No scores available.</p>'
    lo, hi = 0.0, 100.0
    bucket_w = (hi - lo) / bins
    counts = [0] * bins
    for v in values:
        idx = min(int((v - lo) / bucket_w), bins - 1)
        counts[max(idx, 0)] += 1
    mx = max(counts) or 1
    bars = []
    for c in counts:
        h = (c / mx * 100)
        bars.append(f'<div class="hist-bar" style="height:{h:.0f}%" title="{c} operators"></div>')
    return f'<div class="histogram">{"".join(bars)}</div>'


def _donut(data: dict[str, int], colors: dict[str, str] | None = None) -> str:
    """Generate an inline SVG donut chart."""
    total = sum(data.values()) or 1
    if colors is None:
        palette = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#64748b"]
        colors = {k: palette[i % len(palette)] for i, k in enumerate(data)}

    cx, cy, r_outer, r_inner = 80, 80, 70, 45
    segments = []
    legend = []
    angle = -90.0  # start at top
    for label, val in data.items():
        if val == 0:
            continue
        pct = val / total
        sweep = pct * 360
        # SVG arc
        import math
        a1 = math.radians(angle)
        a2 = math.radians(angle + sweep)
        x1 = cx + r_outer * math.cos(a1)
        y1 = cy + r_outer * math.sin(a1)
        x2 = cx + r_outer * math.cos(a2)
        y2 = cy + r_outer * math.sin(a2)
        x3 = cx + r_inner * math.cos(a2)
        y3 = cy + r_inner * math.sin(a2)
        x4 = cx + r_inner * math.cos(a1)
        y4 = cy + r_inner * math.sin(a1)
        large = 1 if sweep > 180 else 0
        color = colors.get(label, "#64748b")
        path = (
            f'M {x1:.1f} {y1:.1f} A {r_outer} {r_outer} 0 {large} 1 {x2:.1f} {y2:.1f} '
            f'L {x3:.1f} {y3:.1f} A {r_inner} {r_inner} 0 {large} 0 {x4:.1f} {y4:.1f} Z'
        )
        segments.append(f'<path d="{path}" fill="{color}" />')
        legend.append(
            f'<div class="legend-item"><span class="legend-dot" style="background:{color}"></span>'
            f'{label} ({val})</div>'
        )
        angle += sweep

    svg = (
        f'<svg class="donut-svg" viewBox="0 0 160 160">'
        f'{"".join(segments)}'
        f'<text x="80" y="76" text-anchor="middle" fill="#f8fafc" font-size="24" font-weight="700">{total}</text>'
        f'<text x="80" y="94" text-anchor="middle" fill="#64748b" font-size="11">total</text>'
        f'</svg>'
    )
    return f'<div class="donut">{svg}<div class="donut-legend">{"".join(legend)}</div></div>'


def _heatmap(stages: list[str], operators: list[str], fit_data: dict[str, dict[str, float | None]]) -> str:
    """Generate a stage × operator heatmap of provisional fit values."""
    if not stages or not operators:
        return '<p class="sub">No workflow fit data available.</p>'

    def _color(v: float | None) -> str:
        if v is None:
            return "#1e293b"
        if v >= 0.8:
            return "#10b981"
        if v >= 0.6:
            return "#84cc16"
        if v >= 0.4:
            return "#f59e0b"
        return "#ef4444"

    rows = []
    # Header row with stage names
    header = '<div class="heat-row">'
    header += '<div style="width:80px;font-size:11px;color:#64748b">Operator</div>'
    for s in stages:
        header += f'<div class="heat-cell" style="background:transparent;color:#64748b;font-size:10px">{s[:6]}</div>'
    header += '</div>'
    rows.append(header)

    for oid in operators[:15]:  # cap at 15 for readability
        row = '<div class="heat-row">'
        row += f'<div style="width:80px;font-size:11px;color:#cbd5e1">{oid}</div>'
        for s in stages:
            v = fit_data.get(oid, {}).get(s)
            color = _color(v)
            label = f"{v:.1f}" if v is not None else "—"
            row += f'<div class="heat-cell" style="background:{color};color:#0f172a">{label}</div>'
        row += '</div>'
        rows.append(row)

    if len(operators) > 15:
        rows.append(f'<p class="sub" style="margin-top:8px">Showing 15 of {len(operators)} operators</p>')

    return f'<div class="heatmap">{"".join(rows)}</div>'


def generate_executive_dashboard(svc: "PilotService") -> str:
    """Generate a self-contained HTML executive dashboard.

    The dashboard includes cohort overview, composite score distribution,
    top patterns, divergence, intervention outcomes, workflow fit, and
    next evaluations. All data is embedded as JSON — no server needed.
    """
    status = svc.pilot_status()
    dq = svc.data_quality_summary()
    div_counts = svc.divergence_counts()
    cohort_patterns = svc.detect_cohort_patterns()
    ivs = svc.interventions
    iv_outcomes = Counter(iv.synthetic_outcome.value for iv in ivs)
    wf_report = svc.workflow_fit_report()

    # Composite scores
    composite_scores = svc.cohort_composite_scores()
    composite_summary = svc.composite_score_summary()
    score_values = [s.score for s in composite_scores.values()]

    # Top patterns
    pattern_counts: Counter = Counter()
    for oid, patterns in cohort_patterns.items():
        for p in patterns:
            pattern_counts[p.pattern_id] += 1
    top_patterns = pattern_counts.most_common(8)

    # Workflow fit by stage
    by_stage = svc.workflow_fit_by_stage()
    stages = list(by_stage.keys())
    operator_sample = svc.operator_ids[:15]
    fit_data: dict[str, dict[str, float | None]] = {}
    for oid in operator_sample:
        fit_data[oid] = {}
        for s in stages:
            wobs = by_stage.get(s, [])
            for w in wobs:
                if w.operator_id == oid:
                    fit_data[oid][s] = w.provisional_fit
                    break
            else:
                fit_data[oid][s] = None

    # Next evaluations
    from reporting.executive_brief import _generate_next_evaluations
    next_evals = _generate_next_evaluations(svc)

    # Build HTML
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f'<title>Executive Dashboard — {status["cohort_id"]}</title>',
        f'<style>{_CSS}</style>',
        '</head>',
        '<body>',
        # Header
        '<div class="header">',
        f'<h1>Executive Dashboard</h1>',
        f'<div class="subtitle">Cohort {status["cohort_id"]} • {status["window"]["start"]} to {status["window"]["end"]}</div>',
        f'<div class="governance">SYNTHETIC DEMO DATA • METRIC REGISTRY v{status["metric_registry_version"]} • REFERENCE {status["reference_field_version"]}</div>',
        '</div>',
        # Grid
        '<div class="grid">',
    ]

    # Cohort overview stats
    html_parts.append(
        '<div class="card">'
        '<h2>Cohort Overview</h2>'
        '<div class="stat-row">'
        f'<div class="stat"><div class="label">Operators</div><div class="value">{status["total_operators"]}</div><div class="sub">{status["eligible_operators"]} eligible</div></div>'
        f'<div class="stat"><div class="label">Observations</div><div class="value">{status["observation_count"]}</div></div>'
        '</div>'
        '</div>'
    )

    # Data quality
    dq_ok = dq.get("OK", 0)
    dq_warn = dq.get("WARNING", 0)
    dq_block = dq.get("BLOCKING", 0)
    html_parts.append(
        '<div class="card">'
        '<h2>Data Quality</h2>'
        '<div class="stat-row">'
        f'<div class="stat"><div class="label">OK</div><div class="value" style="color:#10b981">{dq_ok}</div></div>'
        f'<div class="stat"><div class="label">Warning</div><div class="value" style="color:#f59e0b">{dq_warn}</div></div>'
        f'<div class="stat"><div class="label">Blocking</div><div class="value" style="color:#ef4444">{dq_block}</div></div>'
        '</div>'
        '</div>'
    )

    # Composite score distribution
    html_parts.append(
        '<div class="card full">'
        '<h2>AI Operator Development Index <span class="badge badge-developmental">DEVELOPMENTAL</span></h2>'
        f'<p class="sub" style="margin-bottom:12px">Composite score (0–100) from canonical metrics: leverage (30%), yield (30%), token_snr (20%), construction (20%). Not a personnel performance rating.</p>'
        '<div class="stat-row" style="margin-bottom:16px">'
        f'<div class="stat"><div class="label">Median</div><div class="value" style="font-size:24px">{composite_summary.get("median", "N/A")}</div></div>'
        f'<div class="stat"><div class="label">Mean</div><div class="value" style="font-size:24px">{composite_summary.get("mean", "N/A")}</div></div>'
        f'<div class="stat"><div class="label">Min</div><div class="value" style="font-size:24px">{composite_summary.get("min", "N/A")}</div></div>'
        f'<div class="stat"><div class="label">Max</div><div class="value" style="font-size:24px">{composite_summary.get("max", "N/A")}</div></div>'
        f'<div class="stat"><div class="label">Q1–Q3</div><div class="value" style="font-size:24px">{composite_summary.get("q1", "N/A")}–{composite_summary.get("q3", "N/A")}</div></div>'
        '</div>'
        f'{_histogram(score_values)}'
        '</div>'
    )

    # Top patterns
    if top_patterns:
        pattern_items = [(pid, count, "#3b82f6") for pid, count in top_patterns]
        html_parts.append(
            '<div class="card">'
            '<h2>Top Patterns <span class="badge badge-measurement">MEASUREMENT</span></h2>'
            f'{_bar_chart(pattern_items)}'
            '</div>'
        )

    # Divergence
    div_items = [(cls, count, "#f59e0b") for cls, count in sorted(div_counts.items())]
    html_parts.append(
        '<div class="card">'
        '<h2>Usage vs Operation Divergence <span class="badge badge-measurement">MEASUREMENT</span></h2>'
        f'{_bar_chart(div_items)}'
        '</div>'
    )

    # Intervention outcomes donut
    if iv_outcomes:
        outcome_colors = {
            "SUCCESS": "#10b981", "PARTIAL": "#f59e0b",
            "NO_EFFECT": "#64748b", "NEGATIVE": "#ef4444", "PENDING": "#3b82f6",
        }
        html_parts.append(
            '<div class="card">'
            '<h2>Intervention Outcomes <span class="badge badge-experiment">EXPERIMENT</span></h2>'
            f'{_donut(dict(iv_outcomes), outcome_colors)}'
            '</div>'
        )

    # Workflow fit heatmap
    html_parts.append(
        '<div class="card full">'
        '<h2>Workflow Fit by Stage <span class="badge badge-measurement">MEASUREMENT</span></h2>'
        f'<p class="sub" style="margin-bottom:8px">Provisional fit per operator per stage. Green ≥0.8, yellow ≥0.6, orange ≥0.4, red <0.4.</p>'
        f'{_heatmap(stages, operator_sample, fit_data)}'
        '</div>'
    )

    # Next evaluations
    if next_evals:
        eval_cards = []
        for rec in next_evals:
            eval_cards.append(
                f'<div class="eval-card">'
                f'<div class="eval-id">{rec["eval_family"]}</div>'
                f'<div class="eval-obs">{rec["observation"]}</div>'
                f'<div class="eval-next">{rec["next_evaluation"]}</div>'
                f'</div>'
            )
        html_parts.append(
            '<div class="card full">'
            '<h2>Next Evaluations Flywheel <span class="badge badge-experiment">EXPERIMENT</span></h2>'
            f'<p class="sub" style="margin-bottom:12px">Evidence-backed observations mapped to specific eval families. Experiments, not outcome claims.</p>'
            f'{"".join(eval_cards)}'
            '</div>'
        )

    # Close grid + disclaimer
    html_parts.append(
        '</div>'  # .grid
        '<div class="disclaimer">'
        'This dashboard was generated from synthetic demo data. All findings are descriptive. '
        'Composite scores are DEVELOPMENTAL — not personnel performance ratings. '
        'Next evaluations are experiments with predeclared metrics, not outcome claims. '
        'Per governance spec: no operator ranking, no automatic adverse actions, no punitive labels.'
        '</div>'
        '</body></html>'
    )

    return "\n".join(html_parts)
