# Stage 03 — DIAGNOSE

## Purpose

Identify actionable operating differences: where does this population diverge
from expected patterns, what hypotheses explain the divergence, and which
interventions might address them. Diagnoses are hypotheses, never causal
findings.

## Governing question

> What actionable operating differences exist, and what hypotheses explain
> them?

## Inputs

- Baseline measurements (from BASELINE)
- Reference population percentiles
- Workflow observations (if workflow analysis is active)
- Observation-level data (for pattern detection)

## Upsilon actions

1. Compute usage-vs-operation divergence via `compute_divergence()` —
   classifies operators into 4 quadrants (HIGH_USAGE_LOW_OPERATION,
   LOW_USAGE_HIGH_OPERATION, LOW_LOW, MIXED) with pp delta.
2. Detect patterns via `PatternEngine.detect_patterns()` / 
   `detect_cohort_patterns()` — 6 pattern detectors:
   - P-CTX-01: low context reuse
   - P-CTX-02: context resets/handoffs
   - P-BURN-01: rich input / weak output (burning tokens)
   - P-HIDDEN-01: hidden high-performer (low usage, high operation)
   - P-MODEL-01: model sensitivity
   - P-STAGE-01: stage specialization
3. Generate diagnoses via `DiagnosisEngine.generate_diagnoses()` / 
   `generate_cohort_diagnoses()` — every diagnosis carries:
   - Evidence (what was observed)
   - Alternatives (what else could explain it)
   - Status: HYPOTHESIS (never CONFIRMED)
   - Confidence (developmental, not causal)
   - Recommended interventions (from catalog)
4. Analyze workflow fit via `WorkflowFitEngine` — provisional stage fit
   with sample-size gates (min 5 observations).
5. Compute org topology via `compute_org_topology()` — team-level
   distributions, capability concentration (Gini), single points of failure.
6. Compute operator similarity via `compute_operator_similarity()` —
   nearest comparable operators by metric profile.
7. Compute operator×system decomposition via
   `compute_operator_system_decomposition()` — separates operator/system/
   interaction effects.
8. Compute context architecture, longitudinal movement, team composition,
   dependency risk, learning curve as configured by eval family selections.
9. Benchmark operators via `BenchmarkEngine` — 13 benchmark classes with
   selection algorithm and bootstrap CIs.

## Existing implementation

| Capability | Implementation | Evidence |
|---|---|---|
| Divergence | `compute_divergence()` — 4 quadrants | `src/analysis/divergence.py`; runtime: 5/3/12/30 distribution |
| Pattern detection | `PatternEngine` — 6 patterns | `src/diagnostics/pattern_engine.py`; runtime: 56 patterns across 39 operators |
| Diagnosis generation | `DiagnosisEngine` — hypotheses with evidence + alternatives | `src/diagnostics/diagnosis_engine.py`; runtime: 56 diagnoses |
| Workflow fit | `WorkflowFitEngine` with sample-size gates | `src/workflow/fit_engine.py` |
| Org topology | `compute_org_topology()` — Gini, SPOF, complementarity | `src/analysis/org_topology.py` |
| Operator similarity | `compute_operator_similarity()` — Euclidean on percentile rank | `src/analysis/similarity.py` |
| Operator×System | `compute_operator_system_decomposition()` | `src/analysis/operator_system.py` |
| Context architecture | `compute_context_architecture()` | `src/analysis/context_architecture.py` |
| Longitudinal movement | `compute_longitudinal_movement()` | `src/analysis/longitudinal.py` |
| Team composition | `compute_team_composition()` | `src/analysis/team_composition.py` |
| Dependency risk | `compute_dependency_risk()` | `src/analysis/dependency_risk.py` |
| Learning curve | `compute_learning_curve()` | `src/analysis/learning_curve.py` |
| Benchmarking | `BenchmarkEngine` — 13 classes, selection algorithm §7.14 | `src/benchmark/engine.py`; runtime: 50 operators benchmarked |
| Task context adjustment | `context_adjustment()` — difficulty-aware normalization | `src/domain/context.py` |
| CLI surface | `enterprise compare usage-operation/topology/similarity/operator-system`, `diagnose`, `benchmark`, `workflow fit` | `src/cli/main.py` |
| TUI surface | Screens 4 (Divergence), 5 (Diagnose), 6 (Workflow) | `src/tui/app.py` |
| MCP surface | `find_usage_operation_divergence`, `get_diagnostics`, `get_workflow_fit`, `get_org_topology`, `get_operator_similarity`, `get_operator_system_decomposition` | `src/mcp_server/server.py` |

## Checklist

- [ ] Divergence analysis complete (all operators classified)
- [ ] Pattern detection complete (all 6 detectors run)
- [ ] Diagnoses generated (all carry HYPOTHESIS status + evidence + alternatives)
- [ ] Workflow fit computed (if workflow eval active)
- [ ] Org topology computed (if topology eval active)
- [ ] Operator similarity computed (if similarity eval active)
- [ ] Operator×System decomposition computed (if multi-system operators exist)
- [ ] Benchmarking complete (benchmark class selected per operator)
- [ ] Findings documented as hypotheses (never causal claims)

## Required evidence

- Divergence results (operator → quadrant + pp delta)
- Detected patterns (operator → pattern_id + evidence)
- Diagnoses (operator → hypothesis + evidence + alternatives + recommended interventions)
- Workflow fit report (stage → top operators + sample size)
- Org topology map (team → distributions + concentration + SPOF)
- Benchmark results (operator → selected class + percentile rank + CI)

## Artifact

**Diagnostic Findings** — the collection of hypotheses and operating
differences. See `examples/ACME-001/03_DIAGNOSTIC_FINDINGS.md`.

## Exit criteria

- All active eval families have produced results
- All diagnoses carry HYPOTHESIS status (no CONFIRMED)
- All outcome claims labeled ASSOCIATION (no CAUSATION)
- Findings are actionable (each diagnosis has recommended interventions)

## Failure states

- No patterns detected (may indicate data quality issues or a uniformly
  operating population — not necessarily a failure, but requires
  investigation)
- Insufficient data for workflow fit (sample size below minimum)
- Benchmark selection fails for all operators (no legitimate comparison
  class)
- Diagnosis engine errors (fall back to repo diagnoses or investigate)

## Next stage

→ **04_INTERVENE** — apply controlled interventions where diagnoses
suggest actionable changes.
