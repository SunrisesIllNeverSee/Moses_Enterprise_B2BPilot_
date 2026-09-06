# ACME-001 — Reference Pilot

> The canonical reference implementation of an Upsilon Enterprise Pilot,
> using the existing synthetic enterprise demonstration.
>
> **All data is SYNTHETIC.** ACME-001 is treated as though Acme were a
> real customer, but every value is simulated. The purpose of ACME-001
> is to reveal where the proposed protocol cannot currently be completed.

## Pilot identity

| Field | Value |
|---|---|
| Pilot ID | ACME-001 |
| Enterprise | Acme (tenant: `acme`) |
| Cohort ID | `acme_50` |
| Commercial pilot template | #1 (AI Workforce Operating Baseline) |
| Deployment level | 1 (baseline) |
| Synthetic | YES |

## Validated demo values

All values below were validated from runtime on 2026-09-06 by
instantiating `PilotService` and exercising the platform.

| Characteristic | Prompt-stated | Actual (validated) | Source |
|---|---|---|---|
| Synthetic operators | ~50 | **50** | `PilotService.operators` |
| Teams | 6 | **6** | `PilotService.teams` |
| Telemetry observations | ~12,842 | **1,668** | `PilotService.observations` / `wc -l observations.jsonl` |
| Computed operator metrics | yes | **yes** (5 canonical metrics × 50 operators) | `PilotService.score_cohort()` |
| Reference benchmarking | yes | **yes** (13 benchmark classes, peer class selected) | `PilotService.benchmark_summary()` |
| Interventions | 12 | **12** | `PilotService.interventions` |
| Pre/post results | yes | **yes** (12 verification results) | `PilotService.verify_all_interventions()` |
| Diagnostic surfaces | yes | **yes** (56 patterns, 56 diagnoses across 39 operators) | `PilotService.detect_cohort_patterns()` |
| Verification | yes | **yes** (target + non-target deltas) | `PilotService.verify_intervention()` |
| Data-quality gates | yes | **yes** (6 checks: 50 OK, 1882 WARNING, 0 BLOCKING) | `PilotService.data_quality_summary()` |
| Pilot readout | yes | **yes** (markdown + executive brief + dashboard) | `export_pilot_markdown()` |

> **Discrepancy:** The prompt stated approximately 12,842 telemetry
> observations. The actual count is 1,668. ACME-001 uses the validated
> value.

## Lifecycle completion status

| Stage | Status | Evidence file |
|---|---|---|
| DEFINE (Charter) | **PARTIAL** — charter fields exist in PilotConfiguration but no formal charter with locked success criteria | `00_PILOT_CHARTER.md` |
| INSTRUMENT (Readiness) | **COMPLETE** — 1668 observations ingested, validated, governance-checked | `01_INSTRUMENTATION_READINESS.md` |
| BASELINE (Snapshot) | **COMPLETE** — 50 operators scored, percentiles computed, distributions computed | `02_BASELINE_SNAPSHOT.md` |
| DIAGNOSE (Findings) | **COMPLETE** — 56 patterns, 56 diagnoses, divergence, workflow fit, topology, benchmarks | `03_DIAGNOSTIC_FINDINGS.md` |
| INTERVENE (Interventions) | **COMPLETE** — 12 interventions assigned with declared targets | `04_INTERVENTIONS.md` |
| VERIFY (Verification) | **COMPLETE** — 12 verification results, outcome correlations | `05_VERIFICATION_RESULTS.md` |
| READOUT (Readout) | **COMPLETE** — markdown readout, executive brief, decision report | `07_PILOT_READOUT.md` |
| DECIDE (Decision) | **CANNOT COMPLETE** — no closure decision capability exists | `08_DECISION_RECORD.md` (illustrative only) |
| GATES (Gate Records) | **CANNOT COMPLETE** — no pilot-level gate records exist | `06_GATE_RECORDS.md` (illustrative only) |

## What ACME-001 reveals

1. **The platform can complete DEFINE through READOUT** with real
   computed evidence. The measurement, diagnosis, intervention, and
   verification pipeline is materially implemented.

2. **The platform CANNOT complete DECIDE.** There is no closure decision
   capability. No Gate 3 evaluation. No STOP/EXTEND/EXPAND/DEPLOY
   outcome. No decision record. This is the single largest gap.

3. **The platform CANNOT produce formal gate records.** Gates 1, 2, and
   3 do not exist as pilot-level constructs. The operator-level gates
   (GATE-001/002/003) are a different layer.

4. **Success criteria are not locked.** The pilot has no pre-measurement
   success criteria. This means Gate 3 cannot compare evidence against
   criteria — there are no criteria to compare against.

5. **The reference field is synthetic.** The benchmark reference
   population is derived from the demo cohort itself, not from an
   external reference field. This is a known limitation for real-customer
   pilots.

## Files

| File | Content |
|---|---|
| `00_PILOT_CHARTER.md` | Pilot charter (partial — missing locked success criteria) |
| `01_INSTRUMENTATION_READINESS.md` | Instrumentation readiness record (complete) |
| `02_BASELINE_SNAPSHOT.md` | Baseline snapshot (complete) |
| `03_DIAGNOSTIC_FINDINGS.md` | Diagnostic findings (complete) |
| `04_INTERVENTIONS.md` | Intervention records (complete) |
| `05_VERIFICATION_RESULTS.md` | Verification results (complete) |
| `06_GATE_RECORDS.md` | Gate records (illustrative — gates not implemented) |
| `07_PILOT_READOUT.md` | Pilot readout (complete) |
| `08_DECISION_RECORD.md` | Decision record (illustrative — decision not implemented) |
