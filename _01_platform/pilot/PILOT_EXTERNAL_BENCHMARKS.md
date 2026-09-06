# PILOT_EXTERNAL_BENCHMARKS.md

> External benchmark requirements for Upsilon Enterprise Pilots.
>
> The platform's current reference field is synthetic (derived from the
> demo cohort itself). This document specifies what external benchmarks
> are needed for valid real-customer pilots.

## Current state

| Field | Value | Source |
|---|---|---|
| Reference ID | public_field | `ReferencePopulation.reference_id` |
| Version | public_field_2026-08-17 | `ReferencePopulation.version` |
| Synthetic | true | `ReferencePopulation.synthetic` |
| Description | Synthetic reference field derived from the acme_50 cohort | `demo_data/reference_field.json` |
| Benchmark class selected | peer (for all 50 operators) | `PilotService.benchmark_summary()` |

> **Known limitation:** The reference field is synthetic, derived from
> the demo cohort itself. This means benchmarking compares operators
> against themselves, not against an external reference. All 50
> operators are benchmarked using the `peer` class.

## What external benchmarks provide

1. **Valid percentile ranks.** External reference populations provide
   percentile ranks that reflect a broader population, not just the
   pilot cohort. A pilot cohort's median leverage of 12.177 may be
   p50 against itself but p70 against an external reference.

2. **Benchmark class diversity.** With an external reference, the
   benchmark selection algorithm (§7.14) can select classes other than
   `peer` — e.g., `self_vs_prior` (if prior-window data exists),
   `matched_task` (if task-matched reference data exists), `role` (if
   role-specific reference data exists).

3. **Calibration.** External benchmarks calibrate the composite
   developmental score against a broader population, ensuring the
   0–100 index is meaningful across pilots.

## External benchmark requirements

### R1 — Aggregated anonymized reference field

**What:** A reference field constructed from aggregated, anonymized
data across multiple cohorts.

**Requirements:**
- Data from 2+ cohorts (minimum 100 operators total)
- All data pseudonymized (no PII)
- All data governance-compliant (purpose, disclosure, consent)
- Per-metric percentile distributions (p0–p100)
- Versioned with provenance record
- Updated on a defined cadence (e.g., quarterly)

**Risk if not available:** Benchmarking remains self-referential.
Percentile ranks are inflated. Composite scores are not calibrated
across pilots.

### R2 — Public benchmark reference field

**What:** A reference field from a public benchmark source (e.g.,
SigRank public leaderboard data).

**Requirements:**
- Publicly available data
- Per-metric percentile distributions
- Versioned with provenance record
- Documented limitations (e.g., may not represent enterprise AI usage)

**Risk if not available:** No external calibration possible. Pilots
rely on aggregated anonymized reference (R1) only.

### R3 — Role-specific reference distributions

**What:** Per-role reference distributions (e.g., backend engineers,
frontend engineers, data scientists, DevOps).

**Requirements:**
- Role taxonomy aligned with `Operator.role_family`
- Per-role per-metric percentile distributions
- Minimum 25 operators per role for statistical validity
- Versioned with provenance record

**Risk if not available:** `role` benchmark class cannot be selected.
All operators benchmarked as `peer` or `self_vs_prior`.

### R4 — Prior-window reference data

**What:** Per-operator prior-window measurements for `self_vs_prior`
benchmarking.

**Requirements:**
- At least 2 windows of data per operator
- Same metric definitions across windows
- Window boundaries clearly defined
- Data quality checked for each window

**Risk if not available:** `self_vs_prior` benchmark class cannot be
selected. Longitudinal movement is computed but not used for
benchmarking.

## Benchmark class availability matrix

| Benchmark class | Source | Current availability | With R1 | With R2 | With R3 | With R4 |
|---|---|---|---|---|---|---|
| peer | Cohort itself | ✅ | ✅ | ✅ | ✅ | ✅ |
| self_vs_prior | Prior window | ❌ | ❌ | ❌ | ❌ | ✅ |
| matched_task | Task-matched reference | ❌ | ❌ | ❌ | ❌ | ❌ |
| role | Role-specific reference | ❌ | ❌ | ❌ | ✅ | ❌ |
| team | Team within cohort | ✅ (if teams exist) | ✅ | ✅ | ✅ | ✅ |
| cohort | Cohort itself | ✅ | ✅ | ✅ | ✅ | ✅ |
| organization | Org-level reference | ❌ | ✅ (if multi-cohort) | ❌ | ❌ | ❌ |
| system | System-specific reference | ❌ | ❌ | ❌ | ❌ | ❌ |
| workflow | Workflow-specific reference | ❌ | ❌ | ❌ | ❌ | ❌ |

> With R1 (aggregated anonymized reference), the `organization` class
> becomes available if the reference spans multiple cohorts from
> different organizations.

## Implementation priority

| Requirement | Priority | Maturity target | Effort |
|---|---|---|---|
| R1 Aggregated anonymized reference | P1 | T2 | Medium-High |
| R2 Public benchmark reference | P2 | T2 | Low (if public data available) |
| R3 Role-specific reference | P2 | T2 | Medium |
| R4 Prior-window reference | P2 | T2 | Low (if multi-window data available) |

## What this document does NOT specify

- How to construct the reference field (that is an implementation
  detail for the build plan)
- What the percentile distributions should look like (that depends on
  the available data)
- How often to update the reference field (that is an operational
  decision)
- Whether to use R1, R2, R3, or R4 (that depends on what data is
  available for each pilot)

This document specifies WHAT external benchmarks are needed and WHY.
The HOW is in `implementation/PILOT_MODE_BUILD_PLAN.md` (T2.1).
