# Stage 02 — BASELINE

## Purpose

Compute the canonical metrics for every eligible operator over the cohort
window. Establish the measurable starting point against which all subsequent
diagnosis, intervention, and verification will be compared.

## Governing question

> What does this population's AI operating behavior actually look like,
> measured canonically?

## Inputs

- Validated observation stream (from INSTRUMENT)
- Cohort window (start/end dates)
- Metric registry (5 canonical metrics)
- Reference population (percentile distributions)

## Upsilon actions

1. Score every operator via `ScoringEngine.score_operator()` — computes
   leverage, yield, token_snr, log_leverage, construction from observations
   over the cohort window.
2. Score the full cohort via `ScoringEngine.score_cohort()`.
3. Compute percentiles via `compute_percentiles()` — maps each operator's
   metrics to reference-population percentiles.
4. Compute cohort distributions via `compute_cohort_distributions()` —
   median, IQR, p10/p90 for each metric.
5. Compute composite developmental scores via `compute_composite_score()` /
   `compute_cohort_composite_scores()` — 0–100 index, DEVELOPMENTAL label.
6. Check eligibility via `check_eligibility()` / `check_cohort_eligibility()`
   — minimum observation count, non-null metrics.
7. Run data quality checks via `run_all_quality_checks()` — 6 checks with
   OK/WARNING/BLOCKING severity.
8. Record the baseline as an immutable snapshot.

## Existing implementation

| Capability | Implementation | Evidence |
|---|---|---|
| Scoring engine | `ScoringEngine.score_operator/cohort()` | `src/metrics/engine.py`; runtime: 50 operators scored |
| Metric registry | 5 canonical metrics (leverage, yield, token_snr, log_leverage, construction), registry v0.2 | `src/metrics/registry.py`, `src/metrics/formulas.py` |
| Percentiles | `compute_percentiles()` | `src/analysis/percentiles.py` |
| Distributions | `compute_cohort_distributions()` | `src/analysis/distributions.py` |
| Composite score | `compute_composite_score()` — 0–100 developmental index | `src/metrics/composite_score.py` |
| Eligibility | `check_eligibility()` / `check_cohort_eligibility()` | `src/analysis/eligibility.py`; runtime: 50/50 eligible |
| Data quality | `run_all_quality_checks()` — 6 checks | `src/analysis/data_quality.py`; runtime: 50 OK, 1882 WARNING, 0 BLOCKING |
| Reference population | `ReferencePopulation` with p0–p100 distributions | `src/domain/reference_population.py`, `demo_data/reference_field.json` |
| CLI surface | `enterprise score operator/cohort/composite`, `validate outcomes` | `src/cli/main.py` |
| TUI surface | Screens 1 (Pilot), 2 (Cohort), 3 (Operator), 9 (Data Quality) | `src/tui/app.py` |
| MCP surface | `get_operator_profile`, `get_cohort_distribution`, `get_data_quality`, `get_composite_score` | `src/mcp_server/server.py` |

## Checklist

- [ ] All eligible operators scored (5 canonical metrics each)
- [ ] Percentiles computed against reference population
- [ ] Cohort distributions computed (median, IQR, p10/p90)
- [ ] Composite developmental scores computed (cohort-level, no leaderboard)
- [ ] Eligibility verified (all operators meet minimum threshold)
- [ ] Data quality checked (no BLOCKING issues)
- [ ] Baseline snapshot recorded (immutable)

## Required evidence

- Per-operator `Measurement` list (5 metrics each, with status + eligibility)
- Cohort distribution statistics (median, p10, p90 per metric)
- Eligibility results (passed/failed per operator)
- Data quality summary (OK/WARNING/BLOCKING counts)
- Composite score summary (distribution stats, no individual ranking)

## Artifact

**Baseline Snapshot** — the immutable record of the cohort's measured
starting point. See `examples/ACME-001/02_BASELINE_SNAPSHOT.md`.

## Exit criteria

- ≥ 80% of operators eligible (configurable threshold)
- No BLOCKING data quality issues
- All 5 canonical metrics computed for eligible operators
- Reference population version recorded

## Failure states

- < 80% eligibility (insufficient observations per operator)
- BLOCKING data quality issues
- Reference population unavailable or invalid
- Metric computation errors (null values for eligible operators)

## Next stage

→ **03_DIAGNOSE** — identify actionable operating differences and hypotheses.
