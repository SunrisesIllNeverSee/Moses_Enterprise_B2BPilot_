# Stage 05 — VERIFY

## Purpose

Measure the results of interventions against their pre-declared targets.
Compute pre/post metric deltas, check target and non-target metrics, and
correlate operating patterns with external outcomes through lineage.

## Governing question

> Did the interventions produce measurable change, and is the change
> attributable to the target metric?

## Inputs

- Interventions with declared target_metric + followup_days (from INTERVENE)
- Baseline measurements (from BASELINE)
- Follow-up observations (collected during/after intervention window)
- External outcome data (if outcome join is configured)

## Upsilon actions

1. Verify each intervention via `verify_intervention()` / 
   `verify_all_interventions()` — `PrePostVerifier` computes:
   - Target metric delta (absolute + percent change)
   - Non-target metric deltas (to detect side effects)
   - Baseline vs follow-up window comparison
   - `VerificationResult` with `MetricDelta` list
2. Close interventions with outcomes via `close_intervention()` —
   SUCCESS / PARTIAL / NO_EFFECT / NEGATIVE.
3. Replicate findings via `replicate_finding()` — tests whether descriptive
   findings (patterns, divergence) are stable across window/cohort splits.
   Descriptive stability, NOT causal validation.
4. Correlate outcomes via `outcome_correlation()` — connects lineage
   micro_eval metrics to Outcome nodes (quality score, cycle time).
   Labeled ASSOCIATION, evidence grade OBSERVATIONAL.
5. Join external outcomes via `join_outcomes()` — `OutcomeJoinEngine` joins
   external outcome CSVs to internal metric deltas. ASSOCIATION only.
6. Cross-analyze via `intervention_outcome_analysis()` — wires pre/post
   verifier to outcome join engine. ASSOCIATION only.
7. Compute longitudinal movement via `compute_longitudinal_movement()` —
   metric deltas, trend direction, band movement over sub-windows.
8. Compute learning curves via `compute_learning_curve()` — improvement
   rate, curve shape, 95% CI, plateau detection.

## Existing implementation

| Capability | Implementation | Evidence |
|---|---|---|
| Pre/post verification | `PrePostVerifier.verify()` — target + non-target deltas | `src/analysis/verifier.py`; runtime: 12 verification results |
| Intervention closure | `close_intervention()` — SUCCESS/PARTIAL/NO_EFFECT/NEGATIVE | `src/service.py`; runtime: 5 SUCCESS, 2 PARTIAL, 2 NO_EFFECT, 3 NEGATIVE |
| Replication | `ReplicationEngine` — window/cohort split replication | `src/analysis/replication.py` |
| Outcome correlation | `compute_outcome_correlation()` — lineage → outcome | `src/analysis/outcome_correlation.py`; runtime: 50 lineages, 50 outcomes |
| Outcome join | `OutcomeJoinEngine` — external CSV join, ASSOCIATION only | `src/outcomes/join_engine.py`, `src/outcomes/governance.py` |
| Cross-analysis | `InterventionOutcomeAnalyzer` | `src/outcomes/cross_analysis.py` |
| Longitudinal movement | `compute_longitudinal_movement()` | `src/analysis/longitudinal.py` |
| Learning curve | `compute_learning_curve()` | `src/analysis/learning_curve.py` |
| Post-intervention results | `demo_data/results.json` — 12 pre-computed results | Direct file read; classifications: 5 improved_internal_and_external, 2 improved_internal_only, 2 no_change, 3 degraded |
| CLI surface | `enterprise verify operator/intervention`, `lineage outcomes` | `src/cli/main.py` |
| TUI surface | Screen 8 (Verify) | `src/tui/app.py` |
| MCP surface | `verify_change`, `get_outcome_correlation`, `get_lineage_chain` | `src/mcp_server/server.py` |

## Checklist

- [ ] All interventions verified (target + non-target deltas computed)
- [ ] All interventions closed with declared outcome
- [ ] Replication run for key findings (stability checked)
- [ ] Outcome correlation computed (if outcomes available)
- [ ] External outcome join completed (if configured)
- [ ] Cross-analysis completed (if both internal + external data)
- [ ] All results labeled ASSOCIATION (no CAUSATION claims)
- [ ] Longitudinal movement computed (if multi-window data)

## Required evidence

- `VerificationResult` per intervention (target delta, non-target deltas,
  baseline/follow-up windows)
- `InterventionOutcome` per intervention (SUCCESS/PARTIAL/NO_EFFECT/NEGATIVE)
- `ReplicationResult` for key findings (split stability)
- `OutcomeCorrelationResult` (if outcomes available)
- `OutcomeJoinResult` list (if external outcomes joined)
- `InterventionOutcomeResult` list (if cross-analysis run)

## Artifact

**Verification Results** — the evidence-backed change measurements. See
`examples/ACME-001/05_VERIFICATION_RESULTS.md` and
`schemas/VERIFICATION_SCHEMA.md`.

## Exit criteria

- All interventions have verification results
- All interventions have closed outcomes
- Target metric deltas computed for all interventions
- Non-target metric deltas checked (side effects documented)
- All claims labeled ASSOCIATION (no CAUSATION)

## Failure states

- Insufficient follow-up data (follow-up window too short or no observations)
- All interventions show NO_EFFECT (may indicate wrong target metric or
  insufficient intervention intensity — not necessarily a pilot failure)
- Negative outcomes (interventions degraded performance — document and
  investigate)
- Replication fails (findings not stable across splits — reduces confidence)
- Causal claims attempted (governance violation — must be blocked)

## Next stage

→ **06_READOUT** — synthesize findings into an evidence-backed pilot
readout.
