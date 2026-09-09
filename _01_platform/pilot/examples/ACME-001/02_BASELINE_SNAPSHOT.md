# ACME-001 — Baseline Snapshot

> **COMPLETE** — all 50 operators scored, percentiles computed,
> distributions computed. All values validated from runtime on 2026-09-06.

## Cohort overview

| Field | Value | Source |
|---|---|---|
| Cohort ID | acme_50 | `PilotService.cohort.cohort_id` |
| Window | 2026-07-01 to 2026-07-30 (30 days) | `PilotService.cohort.window_start/end` |
| Operators | 50 | `PilotService.operators` |
| Teams | 6 | `PilotService.teams` |
| Observations | 1,668 | `PilotService.observations` |
| Metric registry | 0.2 | `PilotService.engine.registry.registry_version` |
| Reference field | public_field_2026-08-17 | `PilotService.reference_population.version` |

## Canonical metrics

5 canonical metrics computed for all 50 operators:

| Metric | Formula | Status | Unit |
|---|---|---|---|
| leverage | R/I | CANONICAL | ratio |
| yield | (R×O)/(I²) | CANONICAL | ratio |
| token_snr | O/(I+O) | CANONICAL_WITH_INTERPRETATION_LIMIT | share |
| log_leverage | log10(R/I) | CANONICAL | log10_ratio |
| construction | W/R | CANONICAL_WITH_INTERPRETATION_LIMIT | ratio |

Source: `src/metrics/registry.py`, `demo_data/metric_registry.json`

## Cohort distributions

| Metric | Median | p10 | p90 | Source |
|---|---|---|---|---|
| leverage | 12.177 | 3.545 | 29.4947 | `PilotService.cohort_medians()` + `reference_field.json` |
| yield | 6.0072 | 0.7139 | 15.961 | Same |
| token_snr | 0.3417 | 0.1691 | 0.5295 | Same |
| construction | 1.7338 | 0.8248 | 4.023 | Same |

> Values match `demo_data/cohort.json` medians and `demo_data/reference_field.json`
> percentiles, confirming measurement consistency.

## Composite developmental scores

| Field | Value | Source |
|---|---|---|
| Score ID | dev_index | `COMPOSITE_ID` |
| Score name | AI Operator Development Index | `COMPOSITE_NAME` |
| Label | DEVELOPMENTAL — cohort distribution, not individual ranking | `PilotService.composite_score_summary()` |
| Weights | leverage 0.30, yield 0.30, token_snr 0.20, construction 0.20 | `PilotService.composite_score_summary().weights` |

> Composite scores are computed for all 50 operators but are NOT surfaced
> as a leaderboard. Per governance: no bottom-employee leaderboard, no
> punitive labels.

## Eligibility

| Field | Value | Source |
|---|---|---|
| Eligible operators | 50 / 50 (100%) | `PilotService.eligibility()` |
| Eligibility criteria | Minimum observation count, non-null metrics | `src/analysis/eligibility.py` |

## Data quality

| Severity | Count |
|---|---|
| OK | 50 |
| WARNING | 1,882 |
| BLOCKING | 0 |

(See `01_INSTRUMENTATION_READINESS.md` for breakdown.)

## Reference population

| Field | Value | Source |
|---|---|---|
| Reference ID | public_field | `ReferencePopulation.reference_id` |
| Version | public_field_2026-08-17 | `ReferencePopulation.version` |
| Synthetic | true | `ReferencePopulation.synthetic` |
| Description | **SYNTHETIC / NOT PRODUCTION.** Synthetic reference field derived from the acme_50 cohort. For real customer pilots, an external reference field is required. | `demo_data/reference_field.json` |

> **Known limitation:** The reference field is synthetic, derived from
> the demo cohort itself. This means benchmarking compares operators
> against themselves, not against an external reference. For real
> customer pilots, an external reference field is required.

## Baseline snapshot timestamp

> **MISSING.** The platform does not record a baseline snapshot timestamp.
> The baseline is recomputed on each `PilotService` instantiation from
> the demo data. For a real pilot, the baseline snapshot should be
> immutable and timestamped.

## What this baseline reveals

1. **Measurement is complete and consistent.** All 50 operators are
   scored with 5 canonical metrics. Medians match the reference field.
2. **Data quality is acceptable** (0 BLOCKING, warnings are expected
   for synthetic data).
3. **The reference field is synthetic** — a known limitation that
   affects benchmarking validity.
4. **No immutable baseline snapshot** — the baseline is recomputed
   each time, not persisted as an immutable record.
