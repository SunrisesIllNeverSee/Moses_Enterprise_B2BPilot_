# DECISION_GATES.md

> Three formal decision gates govern the pilot lifecycle. Each gate has
> defined inputs, outcomes, and consequences.

## Overview

| Gate | Stage | Question | Outcomes |
|---|---|---|---|
| GATE 1 — LAUNCH READINESS | End of DEFINE | Is this a valid, instrumentable pilot? | LAUNCH, LAUNCH_WITH_CONDITIONS, DEFER, DECLINE |
| GATE 2 — PILOT HEALTH | During INTERVENE / VERIFY | Is the pilot still a valid experiment? | CONTINUE, ADJUST, ESCALATE, TERMINATE |
| GATE 3 — CLOSURE / SCALE | End of READOUT → DECIDE | Did the evidence meet the locked success criteria? | STOP, EXTEND, EXPAND, DEPLOY |

---

## GATE 1 — LAUNCH READINESS

### When

End of the DEFINE stage, before INSTRUMENT begins.

### Question

> Is this a valid, instrumentable pilot?

### Inputs

- Pilot Charter (identity, scope, question, governance)
- Success criteria (locked before measurement)
- Population boundary (operator count, selection criteria)
- Duration boundary (start/end dates)
- Governance clearance (purpose, disclosure, consent)
- Configuration validation result

### Evaluation criteria

1. **Validity**: The pilot question is clear and answerable with the
   selected eval families.
2. **Boundedness**: Population and duration are explicitly bounded.
3. **Instrumentability**: The population can be observed with sufficient
   coverage (provider access, operator identities resolvable).
4. **Governance**: Purpose limitation, employee disclosure, and consent
   gates are satisfiable.
5. **Success criteria**: Criteria are locked, measurable, and
   decision-oriented.
6. **Authorization**: An authorized approver has signed off.

### Outcomes

| Outcome | Meaning | Next action |
|---|---|---|
| **LAUNCH** | All criteria met. Proceed to INSTRUMENT. | Begin telemetry collection |
| **LAUNCH_WITH_CONDITIONS** | Minor gaps that can be addressed during INSTRUMENT. Proceed with documented conditions. | Begin telemetry collection; address conditions |
| **DEFER** | Gaps that must be addressed before launch but are addressable. Do not proceed yet. | Address gaps; re-evaluate Gate 1 |
| **DECLINE** | Fundamental issues that cannot be addressed. The pilot is not valid. | Document why; do not proceed |

### Existing implementation

**NOT IMPLEMENTED.** No pilot-level launch readiness gate exists. The
platform has `ConfigValidator.validate()` for configuration validation
(errors + warnings), but this is not a formal gate with outcomes. The
3 existing `GateRule` objects (GATE-001/002/003) are operator-level
routing gates, not pilot-level decision gates.

---

## GATE 2 — PILOT HEALTH

### When

During INTERVENE and VERIFY, at regular checkpoints (e.g., weekly or at
intervention milestones).

### Question

> Is the pilot still a valid experiment?

> **This is NOT an intervention-performance gate.** It does not evaluate
> whether interventions are working. It evaluates whether the pilot itself
> remains a valid experiment.

### Inputs

- Observation count vs expected (sufficient data flowing?)
- Data quality trend (are BLOCKING issues emerging?)
- Operator participation (are operators still providing telemetry?)
- Governance compliance (are consent/purpose gates still satisfied?)
- Protocol adherence (are interventions following pre-declared targets?)

### Evaluation criteria

1. **Data sufficiency**: Observations are flowing at expected rate.
2. **Data quality**: No new BLOCKING issues.
3. **Participation**: Operators have not dropped below minimum threshold.
4. **Governance**: Consent has not been withdrawn; purpose is still valid.
5. **Protocol**: Interventions are following their pre-declared targets
   and windows.

### Outcomes

| Outcome | Meaning | Next action |
|---|---|---|
| **CONTINUE** | Pilot is healthy. Proceed as planned. | Continue to next checkpoint |
| **ADJUST** | Minor issues that require protocol adjustment (e.g., extend a follow-up window). Document and continue. | Adjust protocol; document; continue |
| **ESCALATE** | Significant issues that require decision authority input (e.g., participation dropped, governance concern). Pause and escalate. | Pause; escalate to decision authority |
| **TERMINATE** | The pilot is no longer a valid experiment (e.g., consent withdrawn, data quality unrecoverable, protocol violation). Stop immediately. | Stop; document; proceed to premature DECIDE |

### Existing implementation

**NOT IMPLEMENTED.** No pilot-health gate exists. The platform has
`pilot_status()` which provides a snapshot (observation count, data
quality, eligible operators), but no formal gate evaluation with
outcomes.

---

## GATE 3 — CLOSURE / SCALE

### When

End of READOUT, before DECIDE is finalized.

### Question

> Did the evidence meet the locked success criteria?

### Inputs

- Pilot readout (all evidence synthesized)
- Success criteria (locked at DEFINE, before measurement)
- Verification results (intervention outcomes)
- Evidence-vs-criteria comparison table

### Evaluation criteria

Each success criterion is evaluated as MET, MISSED, or PARTIAL:

1. **MET**: The measured value satisfies the threshold and direction.
2. **MISSED**: The measured value does not satisfy the threshold.
3. **PARTIAL**: The measured value is close but not sufficient (within
   a configurable tolerance band).

The gate aggregates criterion results:

| Criterion aggregate | Supported outcome |
|---|---|
| All criteria MET | DEPLOY or EXPAND |
| Majority MET, minority PARTIAL | EXPAND or EXTEND |
| Majority PARTIAL or mixed | EXTEND (with specific missing evidence) |
| Majority MISSED | STOP or EXTEND (with fundamental review) |
| Critical criterion MISSED | STOP |

### Outcomes

| Outcome | Meaning | Requirements |
|---|---|---|
| **STOP** | The pilot did not meet success criteria. Discontinue. | Document findings and lessons learned |
| **EXTEND** | The pilot shows promise but is missing evidence. | **MUST include**: explicit reason, missing evidence, new evidence requirement, extension period, new closure date. No indefinite extension. |
| **EXPAND** | The pilot met success criteria. Expand to larger population, longer duration, or additional eval families. | Define expansion scope |
| **DEPLOY** | The pilot met success criteria and the organization is ready for production. | Production transition plan |

### EXTEND requirements

An EXTEND result MUST include ALL of:

1. **Explicit reason**: Why the evidence is insufficient (which criteria
   were MISSED or PARTIAL).
2. **Missing evidence**: What specific evidence is needed.
3. **New evidence requirement**: How the missing evidence will be collected.
4. **Extension period**: How long the extension will last (in days).
5. **New closure date**: The new date for Gate 3 re-evaluation.

> No indefinite pilot state. Every EXTEND must have a bounded extension
> and a new closure date.

### Existing implementation

**NOT IMPLEMENTED.** No pilot-level closure gate exists. The platform
has `results.json` with intervention classifications (improved_internal_only,
improved_internal_and_external, no_change, degraded), but no formal
closure decision with STOP/EXTEND/EXPAND/DEPLOY outcomes.

---

## Relationship to existing operator-level gates

The platform has 3 existing `GateRule` objects (GATE-001/002/003) in
`src/domain/production_gate.py`. These are **operator-level routing
gates** (FLAG_FOR_REVIEW, ROUTE_TO_INTERVENTION, NOTIFY) — they flag
individual operators for coaching/review based on metric thresholds.

The three pilot-level decision gates defined here are a **different
layer**. They govern the pilot lifecycle itself, not individual operator
routing. Both layers coexist:

- **Pilot-level gates** (this document): govern the pilot lifecycle
  (launch, health, closure).
- **Operator-level gates** (existing): route individual operators to
  coaching/review/intervention based on metric thresholds.

Do not conflate the two.
