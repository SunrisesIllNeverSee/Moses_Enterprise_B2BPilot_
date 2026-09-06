# ACME-001 — Gate Records

> **ILLUSTRATIVE ONLY.** The platform does not implement pilot-level
> decision gates (Gate 1, Gate 2, Gate 3). These records are constructed
> retrospectively to show what the gate records would look like if the
> capability existed.
>
> See `governance/DECISION_GATES.md` for the gate specification and
> `schemas/GATE_RECORD_SCHEMA.md` for the formal schema.

## Gate 1 — Launch Readiness

> **NOT IMPLEMENTED.** No pilot-level launch readiness gate exists.

### Illustrative record

```json
{
  "gate_id": "gate-1-ACME-001",
  "pilot_id": "ACME-001",
  "gate_type": "LAUNCH_READINESS",
  "outcome": "LAUNCH_WITH_CONDITIONS",
  "conditions": [
    "Lock success criteria before any future pilot",
    "Set authorized_by on charter",
    "Define purpose_id and consent model for governance gates"
  ],
  "evaluated_at": "2026-08-17T00:00:00Z",
  "evaluated_by": "demo_generator",
  "rationale": "Cohort, window, eval families, and governance metadata are defined. Success criteria are NOT locked — this is a critical gap. Authorized_by is not recorded. Purpose and consent are not set. Launch with conditions to address these gaps in future pilots."
}
```

### Why LAUNCH_WITH_CONDITIONS (not LAUNCH)

- ✅ Population bounded (50 operators)
- ✅ Duration bounded (30 days)
- ✅ Eval families selected (all 15)
- ✅ Configuration valid
- ❌ Success criteria NOT locked
- ❌ Authorized_by NOT recorded
- ❌ Purpose_id NOT set
- ❌ Consent model NOT set

### Why not DEFER or DECLINE

The demo data is already generated and the pilot is retrospective. For
a real pilot, the missing items would need to be addressed before launch
(DEFER). But since this is a synthetic reference, LAUNCH_WITH_CONDITIONS
is appropriate to document the gaps while allowing the pilot to proceed
for demonstration purposes.

---

## Gate 2 — Pilot Health

> **NOT IMPLEMENTED.** No pilot-level health gate exists.

### Illustrative record

```json
{
  "gate_id": "gate-2-ACME-001-checkpoint-1",
  "pilot_id": "ACME-001",
  "gate_type": "PILOT_HEALTH",
  "outcome": "CONTINUE",
  "evaluated_at": "2026-08-15T00:00:00Z",
  "evaluated_by": "demo_generator",
  "rationale": "Observations flowing at expected rate (1668 total). No BLOCKING data quality issues. All 50 operators eligible. Governance gates bypassed for demo (would need to be satisfied for real pilot). Interventions following pre-declared targets."
}
```

### Why CONTINUE

- ✅ Data sufficiency: 1,668 observations across 50 operators
- ✅ Data quality: 0 BLOCKING issues
- ✅ Participation: 50/50 operators eligible
- ⚠️ Governance: bypassed for demo (gates exist but not exercised)
- ✅ Protocol: interventions have declared targets + followup windows

---

## Gate 3 — Closure / Scale

> **NOT IMPLEMENTED.** No pilot-level closure gate exists. No success
> criteria were locked, so Gate 3 cannot compare evidence against criteria.
> This is the single largest gap in the platform.

### Illustrative record

```json
{
  "gate_id": "gate-3-ACME-001",
  "pilot_id": "ACME-001",
  "gate_type": "CLOSURE_SCALE",
  "outcome": "EXTEND",
  "criteria_evaluation": [
    {
      "criterion_id": "SC-001",
      "metric": "cohort_median_leverage",
      "threshold": 10.0,
      "direction": "above",
      "measured_value": 12.177,
      "result": "MET"
    },
    {
      "criterion_id": "SC-002",
      "metric": "eligible_operator_rate",
      "threshold": 0.80,
      "direction": "above",
      "measured_value": 1.0,
      "result": "MET"
    },
    {
      "criterion_id": "SC-003",
      "metric": "divergence_rate",
      "threshold": 0.30,
      "direction": "below",
      "measured_value": 0.40,
      "result": "MISSED"
    }
  ],
  "extend_requirements": {
    "explicit_reason": "Divergence rate (0.40) exceeds threshold (0.30). 20 of 50 operators show strong usage-operation divergence. Success criteria were not locked before measurement, making this evaluation illustrative only.",
    "missing_evidence": "1. Locked success criteria (criteria were not locked before measurement). 2. Replication of key findings across window/cohort splits. 3. Real external reference field (current reference is synthetic, derived from the cohort itself).",
    "new_evidence_requirement": "1. Lock success criteria before next measurement. 2. Run replication on top 5 findings. 3. Obtain or construct an external reference field. 4. Re-evaluate divergence after a longer observation window.",
    "extension_period_days": 30,
    "new_closure_date": "2026-09-29"
  },
  "rationale": "2 of 3 illustrative criteria MET, 1 MISSED. However, criteria were NOT locked before measurement, making this evaluation invalid for a real decision. The pilot shows meaningful measurement capability but cannot produce a valid closure decision without locked criteria. EXTEND with 30-day extension to address gaps.",
  "evidence_cited": [
    "baseline_snapshot: median leverage 12.177",
    "baseline_snapshot: eligible rate 1.0",
    "diagnostic_findings: divergence rate 0.40",
    "verification_results: 5 SUCCESS, 2 PARTIAL, 2 NO_EFFECT, 3 NEGATIVE"
  ],
  "evaluated_at": "2026-09-06T00:00:00Z",
  "evaluated_by": "illustrative"
}
```

### Why EXTEND (not DEPLOY or STOP)

- 2 of 3 illustrative criteria MET → not STOP
- 1 of 3 illustrative criteria MISSED → not DEPLOY
- Criteria were NOT locked before measurement → evaluation is invalid
- EXTEND with explicit requirements to address gaps

### Why not STOP

The pilot demonstrates strong measurement capability (50 operators scored,
56 diagnoses, 12 interventions verified). The gaps are governance gaps
(locked criteria, replication, external reference), not measurement
failures. EXTEND is appropriate to address governance gaps.

### Critical caveat

> **This Gate 3 evaluation is ILLUSTRATIVE ONLY.** The success criteria
> were not locked before measurement. Without locked criteria, no valid
> Gate 3 evaluation is possible. For a real pilot, criteria MUST be
> locked at DEFINE before any measurement begins.

## What these gate records reveal

1. **No pilot-level gates exist.** The platform has operator-level gates
   (GATE-001/002/003) but not pilot-level decision gates.
2. **No success criteria were locked.** This makes Gate 3 evaluation
   invalid — there are no criteria to compare against.
3. **The platform can produce the evidence** that gates would evaluate
   (baseline metrics, diagnostic findings, verification results), but
   it cannot produce the gate records themselves.
4. **EXTEND is the illustrative outcome** because the measurement
   capability is strong but governance gaps prevent a valid closure
   decision.
