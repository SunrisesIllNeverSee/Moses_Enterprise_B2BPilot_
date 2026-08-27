---
type: Reference
title: Synthetic Demo Data — README
description: README for the synthetic 50-operator demo dataset matching 02 §26 file layout (JSON/JSONL). All files synthetic; _demo-suffixed fields are not product claims. Active.
tags: [b2bpilot, demo-data, synthetic, readme, fixtures, acme-50]
timestamp: 2026-08-17
last_touched: 2026-08-17 18:41 UTC
---

# Synthetic demo data

All files in this directory are **synthetic** and intended only for product
development, examples, TUI/CLI/MCP testing, and website visuals.

## Canonical file layout (per `02` §26)

| File | Format | Purpose |
|------|--------|---------|
| `cohort.json` | JSON | Cohort metadata + computed medians |
| `operators.json` | JSON | 50 pseudonymous operators |
| `observations.jsonl` | JSONL | 1500 daily token-telemetry observations (I/O/R/W) |
| `daily_aggregates.csv` | CSV | Daily aggregates (same data as observations, tabular) |
| `workflows.json` | JSON | 7-stage software_dev_v1 workflow definition |
| `stage_events.jsonl` | JSONL | 220 workflow-stage fit observations |
| `diagnoses.json` | JSON | 37 hypothetical diagnostic patterns |
| `interventions.json` | JSON | 12 synthetic intervention assignments |
| `results.json` | JSON | Pre/post intervention results (recomputed deltas) |
| `external_outcomes.csv` | CSV | Synthetic external outcome data (cycle time, quality) |
| `reference_field.json` | JSON | Reference population distributions for percentiles |
| `metric_registry.json` | JSON | Copy of `schemas/metric_registry.json` |
| `demo_manifest.json` | JSON | Demo manifest (per `02` §27) |

## Legacy CSV files (kept for backward compatibility)

The original CSV files (`operators.csv`, `daily_telemetry.csv`,
`operator_metrics.csv`, `workflow_fit_observations.csv`, `interventions.csv`,
`post_intervention_results.csv`, `diagnostics.json`, `cohort_summary.json`)
are retained. The canonical layout above is the spec-compliant set.

## Notes

- Metrics are **computed** from `observations.jsonl` via the ScoringEngine,
  not read from pre-baked `operator_metrics.csv`.
- Fields suffixed `_demo` or status `SYNTHETIC_PROVISIONAL` are not product claims.
- The 7 canonical workflow stages (per `10`): discovery, requirements,
  architecture, implementation, testing, review, release.
- Regenerate with: `python3 scripts/generate_demo_data.py`
