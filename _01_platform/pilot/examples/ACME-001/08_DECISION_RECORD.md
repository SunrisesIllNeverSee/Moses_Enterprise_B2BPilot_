# ACME-001 — Decision Record

> **ILLUSTRATIVE ONLY.** The platform does not implement closure decisions.
> No `DecisionRecord` schema, no Gate 3 evaluation, no STOP/EXTEND/EXPAND/
> DEPLOY outcome exists. This document is a retrospective construction to
> show what the decision record would look like if the capability existed.
>
> See `schemas/DECISION_RECORD_SCHEMA.md` for the formal schema and
> `governance/CLOSURE_OUTCOMES.md` for the outcome definitions.

## Decision record (illustrative)

```json
{
  "decision_id": "decision-ACME-001",
  "pilot_id": "ACME-001",
  "closure_outcome": "EXTEND",
  "rationale": "ACME-001 demonstrates strong measurement capability: 50 operators scored with 5 canonical metrics, 56 diagnostic hypotheses generated, 12 interventions verified with target + non-target deltas. However, the pilot cannot produce a valid closure decision because success criteria were not locked before measurement. The illustrative criteria comparison (2 MET, 1 MISSED) is invalid without locked criteria. EXTEND with a 30-day extension to: (1) lock success criteria, (2) run replication on key findings, (3) obtain an external reference field, (4) re-evaluate divergence after a longer window.",
  "evidence_cited": [
    {
      "evidence_type": "baseline_metric",
      "evidence_id": "cohort_median_leverage",
      "description": "Median leverage 12.177 (above illustrative threshold 10.0)"
    },
    {
      "evidence_type": "baseline_metric",
      "evidence_id": "eligible_operator_rate",
      "description": "50/50 operators eligible (above illustrative threshold 0.80)"
    },
    {
      "evidence_type": "finding",
      "evidence_id": "divergence_rate",
      "description": "Divergence rate 0.40 (above illustrative threshold 0.30)"
    },
    {
      "evidence_type": "verification",
      "evidence_id": "verification_summary",
      "description": "5 SUCCESS, 2 PARTIAL, 2 NO_EFFECT, 3 NEGATIVE outcomes"
    },
    {
      "evidence_type": "readout_section",
      "evidence_id": "preferred_manager_objects",
      "description": "8 developmental objects surfaced for manager use"
    }
  ],
  "success_criteria_comparison": [
    {
      "criterion_id": "SC-001",
      "metric": "cohort_median_leverage",
      "threshold": 10.0,
      "direction": "above",
      "measured_value": 12.177,
      "result": "MET",
      "notes": "ILLUSTRATIVE ONLY — criteria were not locked before measurement"
    },
    {
      "criterion_id": "SC-002",
      "metric": "eligible_operator_rate",
      "threshold": 0.80,
      "direction": "above",
      "measured_value": 1.0,
      "result": "MET",
      "notes": "ILLUSTRATIVE ONLY — criteria were not locked before measurement"
    },
    {
      "criterion_id": "SC-003",
      "metric": "divergence_rate",
      "threshold": 0.30,
      "direction": "below",
      "measured_value": 0.40,
      "result": "MISSED",
      "notes": "ILLUSTRATIVE ONLY — criteria were not locked before measurement"
    }
  ],
  "gate_3_record_id": "gate-3-ACME-001",
  "conditions": [
    "Lock success criteria before next measurement",
    "Run replication on top 5 findings",
    "Obtain or construct an external reference field",
    "Re-evaluate divergence after a longer observation window"
  ],
  "extend_plan": {
    "explicit_reason": "Success criteria were not locked before measurement, making Gate 3 evaluation invalid. Divergence rate (0.40) exceeds the illustrative threshold (0.30). The reference field is synthetic (derived from the cohort itself), limiting benchmarking validity. Replication was not run.",
    "missing_evidence": "1. Locked success criteria. 2. Replication results for key findings. 3. External reference field. 4. Longer-window divergence measurement.",
    "new_evidence_requirement": "1. Define and lock 3-5 success criteria before any future measurement. 2. Run replication on top 5 findings using window/cohort splits. 3. Obtain or construct an external reference field (not derived from the pilot cohort). 4. Extend observation window by 30 days and re-measure divergence.",
    "extension_period_days": 30,
    "new_closure_date": "2026-09-29"
  },
  "decided_at": "2026-09-06T00:00:00Z",
  "decided_by": "illustrative",
  "immutable": true
}
```

## Why EXTEND

| Factor | Assessment |
|---|---|
| Measurement capability | STRONG — 50 operators scored, 56 diagnoses, 12 interventions verified |
| Diagnostic capability | STRONG — 6 pattern detectors, divergence, workflow, topology, benchmarks |
| Intervention capability | STRONG — 12 interventions with declared targets, diverse outcomes |
| Verification capability | STRONG — target + non-target deltas, outcome correlations |
| Readout capability | STRONG — markdown, executive brief, decision report, dashboard |
| Success criteria locking | **MISSING** — criteria not locked before measurement |
| Gate 1 (Launch Readiness) | **MISSING** — no pilot-level gate |
| Gate 2 (Pilot Health) | **MISSING** — no pilot-level gate |
| Gate 3 (Closure / Scale) | **MISSING** — no pilot-level gate |
| Closure decision | **MISSING** — no decision record capability |
| External reference field | **MISSING** — reference is synthetic (derived from cohort) |
| Replication | **NOT RUN** — capability exists but not exercised |

**Assessment:** The measurement/diagnostic/intervention/verification/readout
pipeline is strong. The governance layer (success criteria, gates, closure
decision) is missing. EXTEND is appropriate to address governance gaps
while preserving the measurement investment.

## Why not STOP

The pilot demonstrates substantial capability. The gaps are governance
gaps, not measurement failures. STOPPING would discard the measurement
investment without addressing the governance gaps.

## Why not DEPLOY

DEPLOY requires all critical success criteria to be MET. Criteria were
not locked, so no valid MET assessment is possible. Additionally, the
reference field is synthetic and replication was not run.

## Why not EXPAND

EXPAND requires success criteria to be MET. Same issue as DEPLOY —
criteria not locked, no valid MET assessment.

## What this decision record reveals

1. **The platform CANNOT produce a valid closure decision.** This is
   the single largest gap. Without locked success criteria and Gate 3
   evaluation, no STOP/EXTEND/EXPAND/DEPLOY outcome can be validly
   selected.
2. **The EXTEND outcome is illustrative.** It documents what a
   reasonable decision would look like given the evidence, but it is
   not a valid gate evaluation because the criteria were not locked.
3. **The governance gaps are addressable.** The missing items (success
   criteria schema, gate records, decision records) are canon/governance
   gaps — they require specification and binding, not new analytical
   capability.
4. **The measurement investment should be preserved.** The pilot
   demonstrates strong measurement capability. EXTEND (rather than STOP)
   preserves this investment while addressing governance gaps.
