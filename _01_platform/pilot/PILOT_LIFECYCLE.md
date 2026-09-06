# PILOT_LIFECYCLE.md

> The canonical eight-stage lifecycle for an Upsilon Enterprise Pilot.
>
> Every pilot progresses through these stages. No stage may be skipped.
> Transitions are governed by the decision gates defined in
> `governance/DECISION_GATES.md`.

## Lifecycle

```text
DEFINE
  ↓
INSTRUMENT
  ↓
BASELINE
  ↓
DIAGNOSE
  ↓
INTERVENE
  ↓
VERIFY
  ↓
READOUT
  ↓
DECIDE
```

## Stage summary

| Stage | Purpose | Governing question | Gate | Artifact |
|---|---|---|---|---|
| DEFINE | Establish bounded scope, question, success criteria | Is this a valid, instrumentable pilot? | Gate 1 (end) | Pilot Charter |
| INSTRUMENT | Collect telemetry from the population | Can we observe the population's AI operating behavior? | — | Instrumentation Readiness Record |
| BASELINE | Compute canonical metrics for all eligible operators | What does this population's AI operating behavior look like? | — | Baseline Snapshot |
| DIAGNOSE | Identify actionable operating differences and hypotheses | What actionable differences exist, and what hypotheses explain them? | — | Diagnostic Findings |
| INTERVENE | Apply controlled interventions with declared targets | What controlled changes should we apply? | Gate 2 (during) | Intervention Records |
| VERIFY | Measure results against pre-declared targets | Did the interventions produce measurable change? | Gate 2 (during) | Verification Results |
| READOUT | Synthesize evidence into decision-oriented readout | What does the evidence say, and what decision does it support? | — | Pilot Readout |
| DECIDE | Make the evidence-backed terminal decision | Given the evidence, what is the decision? | Gate 3 (end) | Decision Record |

## Existing runtime flow comparison

The platform's existing demo flow (`enterprise demo full`) runs 10 steps:

```text
1. LOAD
2. EVALUATE
3. BENCHMARK
4. DIAGNOSE
5. OPERATOR×SYSTEM
6. INTERVENE
7. RE-EVALUATE
8. OUTCOME LINEAGE
9. REPORT
10. VISUALIZE
```

### Mapping to canonical lifecycle

| Existing step | Canonical stage | Notes |
|---|---|---|
| 1. LOAD | INSTRUMENT | Loads demo data (fixture adapter) |
| 2. EVALUATE | BASELINE | Scores all operators (5 canonical metrics) |
| 3. BENCHMARK | BASELINE / DIAGNOSE | Benchmarks operators against reference population |
| 4. DIAGNOSE | DIAGNOSE | Detects patterns, generates diagnoses |
| 5. OPERATOR×SYSTEM | DIAGNOSE | Operator×System decomposition |
| 6. INTERVENE | INTERVENE | Shows pre-loaded interventions |
| 7. RE-EVALUATE | VERIFY | Computes pre/post deltas |
| 8. OUTCOME LINEAGE | VERIFY | Correlates outcomes through lineage |
| 9. REPORT | READOUT | Generates pilot readout |
| 10. VISUALIZE | READOUT | Generates dashboard |

### Discrepancies

1. **No explicit DEFINE stage.** The demo flow starts at LOAD (INSTRUMENT).
   The pilot is not formally defined — no charter, no locked success
   criteria, no Gate 1 evaluation.

2. **No explicit DECIDE stage.** The demo flow ends at VISUALIZE
   (READOUT). No closure decision is made. No Gate 3 evaluation. No
   STOP/EXTEND/EXPAND/DEPLOY.

3. **No Gate 2 (Pilot Health) evaluation.** The demo flow does not check
   pilot health during INTERVENE or VERIFY.

4. **BENCHMARK spans BASELINE and DIAGNOSE.** In the canonical lifecycle,
   benchmarking is part of BASELINE (computing percentiles) and DIAGNOSE
   (selecting benchmark classes). The demo flow treats it as a separate
   step.

5. **OPERATOR×SYSTEM is a DIAGNOSE sub-step.** In the canonical lifecycle,
   operator×system decomposition is part of DIAGNOSE. The demo flow
   treats it as a separate step.

6. **OUTCOME LINEAGE is a VERIFY sub-step.** In the canonical lifecycle,
   outcome correlation through lineage is part of VERIFY. The demo flow
   treats it as a separate step.

7. **VISUALIZE is a READOUT sub-step.** In the canonical lifecycle,
   dashboard generation is part of READOUT. The demo flow treats it as
   a separate step.

### Conclusion

The existing runtime flow covers INSTRUMENT through READOUT (steps 1–10
map to canonical stages INSTRUMENT through READOUT). It does NOT cover
DEFINE (no charter, no locked criteria) or DECIDE (no closure decision).

The canonical lifecycle is NOT a renaming of the existing flow. It adds
two stages (DEFINE and DECIDE) that the existing flow does not have,
and it adds three gates (Gate 1, Gate 2, Gate 3) that the existing flow
does not evaluate.

## Stage documents

See `stages/` for detailed per-stage documents:
- `stages/00_DEFINE.md`
- `stages/01_INSTRUMENT.md`
- `stages/02_BASELINE.md`
- `stages/03_DIAGNOSE.md`
- `stages/04_INTERVENE.md`
- `stages/05_VERIFY.md`
- `stages/06_READOUT.md`
- `stages/07_DECIDE.md`

## State machine

See `governance/PILOT_STATE_MACHINE.md` for the formal state machine
with states, transitions, and invariants.
