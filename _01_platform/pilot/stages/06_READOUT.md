# Stage 06 — READOUT

## Purpose

Synthesize all pilot evidence into a coherent, decision-oriented readout.
Translate measurement vocabulary into decision vocabulary. Surface the
8 preferred manager objects. Communicate what was found, what changed,
and what should happen next.

## Governing question

> What does the evidence say, and what decision does it support?

## Inputs

- Baseline measurements (from BASELINE)
- Diagnostic findings (from DIAGNOSE)
- Intervention records (from INTERVENE)
- Verification results (from VERIFY)
- Outcome correlations and joins (from VERIFY)
- Success criteria (locked at DEFINE)

## Upsilon actions

1. Generate pilot markdown readout via `export_pilot_markdown()` —
   full pilot status with data quality, workforce operating map, medians,
   percentiles.
2. Generate executive brief via `export_executive_brief()` — decisions,
   next experiments, next-evaluations flywheel (3-4 evidence-backed
   observations mapped to eval families).
3. Generate decision report via `build_decision_report()` — translates
   measurement vocabulary to decision vocabulary with developmental action
   recommendations.
4. Surface preferred manager objects via `preferred_manager_objects()` —
   8 developmental objects:
   - Development groups
   - Fastest improvers
   - Stalled cohorts
   - Workflow bottlenecks
   - Tool/model fit opportunities
   - Training candidates
   - Peer support matches
   - Remeasurement queue
5. Generate hypothesis map via `export_hypothesis_map()` — maps detected
   patterns to eval families.
6. Generate re-measurement report via `export_remeasurement_report()` —
   post-intervention re-measurement summary.
7. Generate executive dashboard via `generate_executive_dashboard()` —
   HTML dashboard with bar charts, histograms, donut charts, heatmaps.
8. Export data in JSON/CSV/Markdown via `export_cohort_json/csv/markdown()`,
   `export_operator_json/markdown()`.
9. Generate PDF report via `render_sample_report_pdf()` /
   `render_markdown_pdf()`.
10. Compare evidence against success criteria locked at DEFINE.

## Existing implementation

| Capability | Implementation | Evidence |
|---|---|---|
| Pilot markdown readout | `export_pilot_markdown()` | `src/reporting/exporters.py`; output: `demo_data/graphics/demo_full_pilot_readout.md` |
| Executive brief | `export_executive_brief()` | `src/reporting/executive_brief.py` |
| Decision report | `build_decision_report()` | `src/reporting/decision_report.py` |
| Preferred manager objects | `compute_preferred_manager_objects()` — 8 objects | `src/governance/manager_objects.py` |
| Hypothesis map | `export_hypothesis_map()` | `src/reporting/exporters.py` |
| Re-measurement report | `export_remeasurement_report()` | `src/reporting/exporters.py` |
| Executive dashboard (HTML) | `generate_executive_dashboard()` | `src/reporting/dashboard.py` |
| Data export | `export_cohort_json/csv/markdown()`, `export_operator_json/markdown()` | `src/reporting/exporters.py` |
| PDF report | `render_sample_report_pdf()` | `src/reporting/pdf.py` |
| CLI surface | `enterprise export pilot/brief/hypothesis-map/remeasurement/dashboard/cohort/operator` | `src/cli/main.py` |
| TUI surface | Screen E (Export) | `src/tui/app.py` |
| MCP surface | `get_executive_dashboard` | `src/mcp_server/server.py` |

## Checklist

- [ ] Pilot markdown readout generated
- [ ] Executive brief generated (with next-evaluations flywheel)
- [ ] Decision report generated (measurement → decision vocabulary)
- [ ] Preferred manager objects surfaced (8 developmental objects)
- [ ] Hypothesis map generated
- [ ] Re-measurement report generated
- [ ] Evidence compared against locked success criteria
- [ ] All claims labeled with correct decision-use (DEVELOPMENTAL, ASSOCIATION)
- [ ] No personnel evaluations or punitive labels
- [ ] No causal claims (ASSOCIATION only)

## Required evidence

- Pilot readout document (markdown)
- Executive brief (with next-evaluations flywheel)
- Decision report (with developmental action recommendations)
- Preferred manager objects (8 objects)
- Evidence-vs-success-criteria comparison table

## Artifact

**Pilot Readout** — the synthesized evidence-backed summary. See
`examples/ACME-001/07_PILOT_READOUT.md`.

## Exit criteria

- All configured eval families have readout output
- Evidence is compared against success criteria
- All claims carry correct decision-use labels
- No personnel evaluations, punitive labels, or causal claims
- Readout is reviewable by the decision authority

## Failure states

- Evidence insufficient to compare against success criteria
- Readout contains causal claims (governance violation)
- Readout contains personnel evaluations or punitive labels
- Decision report cannot translate findings to actions (may indicate
  wrong eval family selection)

## Next stage

→ **07_DECIDE** — make the evidence-backed terminal decision.
