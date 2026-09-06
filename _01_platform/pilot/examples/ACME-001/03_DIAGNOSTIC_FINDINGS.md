# ACME-001 — Diagnostic Findings

> **COMPLETE** — 56 patterns detected, 56 diagnoses generated, divergence
> analyzed, workflow fit computed, org topology mapped, benchmarks run.
> All values validated from runtime on 2026-09-06.

## Divergence analysis

Usage vs operation divergence for all 50 operators:

| Class | Count | Source |
|---|---|---|
| LOW_USAGE_HIGH_OPERATION | 5 | `PilotService.divergence_counts()` |
| HIGH_USAGE_LOW_OPERATION | 3 | Same |
| LOW_LOW | 12 | Same |
| MIXED | 30 | Same |

> 30 operators are in the MIXED class (no strong divergence), 5 are
> hidden high-performers (low usage, high operation), 3 are burning
> tokens (high usage, low operation), and 12 are low on both dimensions.

## Pattern detection

| Field | Value | Source |
|---|---|---|
| Total patterns detected | 56 | `PilotService.detect_cohort_patterns()` |
| Operators with patterns | 39 / 50 | Same |
| Pattern types | P-CTX-01, P-CTX-02, P-BURN-01, P-HIDDEN-01, P-MODEL-01, P-STAGE-01 | `src/diagnostics/pattern_engine.py` |

### Pattern descriptions

| Pattern | Description | Source |
|---|---|---|
| P-CTX-01 | Low context reuse (leverage below threshold) | `src/diagnostics/pattern_engine.py` |
| P-CTX-02 | Context resets/handoffs (construction below threshold) | Same |
| P-BURN-01 | Rich input / weak output (yield below threshold despite usage) | Same |
| P-HIDDEN-01 | Hidden high-performer (low usage, high operation) | Same |
| P-MODEL-01 | Model sensitivity (metric variance across models) | Same |
| P-STAGE-01 | Stage specialization (metric concentration in specific workflow stages) | Same |

## Diagnoses

| Field | Value | Source |
|---|---|---|
| Total diagnoses | 56 | `PilotService.generate_cohort_diagnoses()` |
| Status | All HYPOTHESIS | `DiagnosisStatus.HYPOTHESIS` |
| Evidence | Present on all | `Diagnosis.evidence` |
| Alternatives | Present (may be empty list if no alternatives) | `Diagnosis.alternatives` |
| Recommended interventions | Present on all | `Diagnosis.recommended_interventions` |

> All diagnoses carry HYPOTHESIS status. None are CONFIRMED. All are
> developmental hypotheses, not causal findings.

### Sample diagnosis

```json
{
  "diagnosis_id": "diag_000",
  "operator_id": "op_002",
  "pattern_id": "P-HIDDEN-01",
  "hypothesis": "usage pct 18.4 vs yield pct 71.4",
  "confidence": 0.6,
  "status": "hypothesis",
  "evidence": "usage pct 18.4 vs yield pct 71.4",
  "alternatives": [],
  "recommended_interventions": ["STG-001"],
  "synthetic": true
}
```

Source: `demo_data/diagnoses.json` (pre-baked; superseded by computed 56
diagnoses from `PilotService.generate_cohort_diagnoses()`)

## Workflow fit

| Field | Value | Source |
|---|---|---|
| Workflows | 4 (software_dev_v1, design_sprint_v1, data_analysis_v1, incident_response_v1) | `PilotService.workflows` |
| Stages per workflow | 7 (discovery → requirements → architecture → implementation → testing → review → release) | `demo_data/workflows.json` |
| Sample-size gate | Minimum 5 observations per stage | `WorkflowFitEngine` (min_sample_rule) |
| Fit computation | Provisional fit per operator per stage | `PilotService.workflow_fit_by_stage()` |

## Org topology

| Field | Value | Source |
|---|---|---|
| Topology type | Structural map (NOT a ranking) | `PilotService.org_topology()` |
| Contents | Team-level distributions, capability concentration (Gini), platform adoption, single points of failure, cross-team complementarity | `src/analysis/org_topology.py` |

## Benchmarking

| Field | Value | Source |
|---|---|---|
| Operators benchmarked | 50 | `PilotService.benchmark_summary("leverage")` |
| Benchmark classes selected | peer: 50 | Same |
| Percentile rank distribution | min/median/max computed | Same |
| No false leaderboards | True | `benchmark_summary().no_false_leaderboards` |

> All 50 operators were benchmarked using the `peer` class (compared
> against cohort peers). The selection algorithm (§7.14) selected `peer`
> because no prior-window data or matched-task data is available.

## Operator×System decomposition

| Field | Value | Source |
|---|---|---|
| Decomposition | Operator effect + System effect + Operator×System interaction | `PilotService.operator_system_decomposition()` |
| Systems compared | chatgpt, claude, codex, copilot, cursor | Same |

## Additional analyses (all computed)

| Analysis | Source |
|---|---|
| Context architecture | `PilotService.context_architecture()` |
| Longitudinal movement | `PilotService.longitudinal_movement()` |
| Team composition | `PilotService.team_composition()` |
| Dependency risk | `PilotService.dependency_risk()` |
| Learning curve | `PilotService.learning_curve()` |
| Operator similarity | `PilotService.operator_similarity()` |

## What these findings reveal

1. **Diagnostic capability is strong.** 6 pattern detectors, hypothesis
   generation with evidence + alternatives, divergence analysis, workflow
   fit, org topology, benchmarking, and 7 additional analyses are all
   implemented and produce real results.
2. **All findings are HYPOTHESIS** — no causal claims. This is correct
   governance.
3. **Benchmarking is limited by the synthetic reference field.** All
   operators are benchmarked as `peer` (against each other) because no
   external reference or prior-window data exists.
4. **39 of 50 operators have detected patterns.** 11 operators have no
   detected patterns — they may be uniformly operating or fall outside
   pattern thresholds.
