# GATE_REVIEW_RUNBOOK.md

> Operational procedure for executing the three pilot-level decision
> gates.
>
> This runbook TRANSLATES the canonical gate specifications
> (`pilot/governance/DECISION_GATES.md`) into executable review
> procedures. It does NOT redefine gate outcomes or criteria.

## Prerequisites

Before any gate review:
- [ ] The reviewer understands the gate's purpose and outcomes
  (`pilot/governance/DECISION_GATES.md`)
- [ ] The reviewer has access to all required inputs
- [ ] The reviewer is the appropriate authority (see below)

## Gate authority

| Gate | Reviewer | When |
|---|---|---|
| Gate 1 — Launch Readiness | Decision Authority | End of DEFINE |
| Gate 2 — Pilot Health | Pilot Creator (with Decision Authority if ESCALATE) | During INTERVENE/VERIFY |
| Gate 3 — Closure / Scale | Decision Authority | End of READOUT → DECIDE |

> The Decision Authority for Gate 1 and Gate 3 MUST be different
> from the Pilot Creator (separation of concerns). Gate 2 may be
> reviewed by the Pilot Creator, with escalation to the Decision
> Authority if needed.

---

## Gate 1 — Launch Readiness

### When

End of the DEFINE stage, before INSTRUMENT begins.

### Question

> Is this a valid, instrumentable pilot?

### Required inputs

- Pilot Charter (identity, scope, question, governance)
- Success criteria (locked before measurement)
- Population boundary (operator count, selection criteria)
- Duration boundary (start/end dates)
- Governance clearance (purpose, disclosure, consent)
- Configuration validation result

### Review procedure

1. **Review the Pilot Charter.** Confirm all required fields are
   present (see `PILOT_LAUNCH_CHECKLIST.md`).
2. **Verify success criteria are locked.** Confirm `locked_at`
   precedes any measurement. If criteria are not locked, the gate
   CANNOT return LAUNCH.
3. **Verify population boundedness.** Confirm 25–100 operators with
   explicit selection criteria.
4. **Verify duration boundedness.** Confirm explicit start and end
   dates.
5. **Verify governance clearance.** Confirm purpose_id, consent
   model, and employee disclosure plan.
6. **Verify instrumentability.** Confirm provider access path and
   operator identity mapping approach.
7. **Verify authorization.** Confirm `authorized_by` is recorded and
   is the Decision Authority.
8. **Select outcome.**

### Outcome selection

| Condition | Outcome |
|---|---|
| All criteria met | **LAUNCH** — proceed to INSTRUMENT |
| Minor gaps addressable during INSTRUMENT | **LAUNCH_WITH_CONDITIONS** — proceed with documented conditions |
| Gaps must be addressed before launch | **DEFER** — do not proceed; address gaps; re-evaluate |
| Fundamental issues cannot be addressed | **DECLINE** — pilot is not valid; do not proceed |

### Recording

Record the Gate 1 outcome:
- `gate_id`: e.g., `gate-1-ACME-001`
- `pilot_id`: e.g., `ACME-001`
- `gate_type`: `LAUNCH_READINESS`
- `outcome`: LAUNCH / LAUNCH_WITH_CONDITIONS / DEFER / DECLINE
- `conditions`: (if LAUNCH_WITH_CONDITIONS) list of conditions
- `evaluated_at`: timestamp
- `evaluated_by`: Decision Authority identity
- `rationale`: why this outcome was selected

> See `pilot/schemas/GATE_RECORD_SCHEMA.md` for the formal schema.

---

## Gate 2 — Pilot Health

### When

During INTERVENE and VERIFY, at regular checkpoints (see
`PILOT_CADENCE.md` — typically weekly or at intervention milestones).

### Question

> Is the pilot still a valid experiment?

> **This is NOT an intervention-performance gate.** It does not
> evaluate whether interventions are working. It evaluates whether
> the pilot itself remains a valid experiment.

### Required inputs

- Observation count vs expected
- Data quality trend (OK/WARNING/BLOCKING over time)
- Operator participation (eligible operators / total)
- Governance compliance (consent still valid, purpose still valid)
- Protocol adherence (interventions following pre-declared targets)

### Review procedure

1. **Check data sufficiency.** Are observations flowing at the
   expected rate? (Use `enterprise pilot status` or
   `PilotService.pilot_status()`)
2. **Check data quality.** Are there new BLOCKING issues? (Use
   `enterprise validate outcomes` or `PilotService.data_quality_summary()`)
3. **Check participation.** Have operators dropped below the minimum
   threshold? (Use `PilotService.eligibility()`)
4. **Check governance.** Has consent been withdrawn? Is the purpose
   still valid?
5. **Check protocol.** Are interventions following their pre-declared
   targets and windows?
6. **Select outcome.**

### Outcome selection

| Condition | Outcome | Next action |
|---|---|---|
| All checks pass | **CONTINUE** | Proceed to next checkpoint |
| Minor issues require protocol adjustment | **ADJUST** | Adjust protocol; document; continue |
| Significant issues require decision authority input | **ESCALATE** | Pause; escalate to Decision Authority |
| Pilot is no longer a valid experiment | **TERMINATE** | Stop; document; proceed to premature DECIDE |

### ADJUST examples

- Extend a follow-up window by 7 days (operator was on vacation)
- Add missing observations from a provider export gap
- Re-run data quality checks after a provider schema change

### ESCALATE examples

- Participation dropped from 50 to 35 (3+ operators stopped
  providing telemetry)
- Governance concern raised (operator challenges a diagnosis)
- Protocol deviation detected (intervention target metric changed
  mid-flight)

### TERMINATE examples

- Consent withdrawn by the customer
- Data quality unrecoverable (provider API broken, data corrupted)
- Protocol violation that invalidates the experiment

### Recording

Record the Gate 2 outcome:
- `gate_id`: e.g., `gate-2-ACME-001-checkpoint-1`
- `pilot_id`
- `gate_type`: `PILOT_HEALTH`
- `outcome`: CONTINUE / ADJUST / ESCALATE / TERMINATE
- `conditions`: (if ADJUST) what was adjusted
- `evaluated_at`: timestamp
- `evaluated_by`: Pilot Creator (or Decision Authority if ESCALATE)
- `rationale`: why this outcome was selected

---

## Gate 3 — Closure / Scale

### When

End of READOUT, before DECIDE is finalized.

### Question

> Did the evidence meet the locked success criteria?

### Required inputs

- Pilot readout (all evidence synthesized)
- Success criteria (locked at DEFINE, before measurement)
- Verification results (intervention outcomes)
- Evidence-vs-criteria comparison table

### Review procedure

1. **Review the Pilot Readout.** Confirm all evidence is present
   (baseline, diagnoses, interventions, verification, manager
   objects, decision report).
2. **Review the success criteria.** Confirm they were locked before
   measurement. If criteria were NOT locked, Gate 3 CANNOT produce a
   valid evaluation.
3. **Evaluate each criterion.** For each:
   - Compare measured value against threshold
   - Classify as MET, MISSED, or PARTIAL
   - Record the comparison
4. **Aggregate criterion results.**
5. **Select outcome.**

### Criterion evaluation

| Measured vs threshold | Result |
|---|---|
| Satisfies threshold and direction | MET |
| Does not satisfy threshold | MISSED |
| Close but not sufficient (within tolerance band) | PARTIAL |

### Outcome selection

| Criterion aggregate | Supported outcome |
|---|---|
| All criteria MET | DEPLOY or EXPAND |
| Majority MET, minority PARTIAL | EXPAND or EXTEND |
| Majority PARTIAL or mixed | EXTEND (with specific missing evidence) |
| Majority MISSED | STOP or EXTEND (with fundamental review) |
| Critical criterion MISSED | STOP |

### EXTEND requirements (ALL five — no exceptions)

If EXTEND is selected, the decision record MUST include:

1. **Explicit reason:** Why the evidence is insufficient (which
   criteria were MISSED or PARTIAL)
2. **Missing evidence:** What specific evidence is needed
3. **New evidence requirement:** How the missing evidence will be
   collected
4. **Extension period:** How long the extension will last (in days)
5. **New closure date:** The specific date for Gate 3 re-evaluation

> No indefinite extension. An EXTEND without all five requirements
> is invalid. If the requirements cannot be specified, the correct
> outcome is STOP, not EXTEND.

### Recording

Record the Gate 3 outcome:
- `gate_id`: e.g., `gate-3-ACME-001`
- `pilot_id`
- `gate_type`: `CLOSURE_SCALE`
- `outcome`: STOP / EXTEND / EXPAND / DEPLOY
- `criteria_evaluation`: per-criterion MET/MISSED/PARTIAL
- `extend_requirements`: (if EXTEND) all five fields
- `expand_plan`: (if EXPAND) new scope
- `deploy_plan`: (if DEPLOY) production transition plan
- `stop_lessons`: (if STOP) findings summary, lessons learned
- `evaluated_at`: timestamp
- `evaluated_by`: Decision Authority
- `rationale`: why this outcome was selected
- `evidence_cited`: specific evidence artifacts cited

> See `pilot/schemas/GATE_RECORD_SCHEMA.md` and
> `pilot/schemas/DECISION_RECORD_SCHEMA.md` for the formal schemas.

---

## Post-gate actions

| Gate | Outcome | Next action |
|---|---|---|
| Gate 1 | LAUNCH | Proceed to INSTRUMENT |
| Gate 1 | LAUNCH_WITH_CONDITIONS | Proceed to INSTRUMENT; address conditions |
| Gate 1 | DEFER | Address gaps; re-evaluate Gate 1 |
| Gate 1 | DECLINE | Do not proceed; document why |
| Gate 2 | CONTINUE | Proceed to next checkpoint |
| Gate 2 | ADJUST | Adjust protocol; document; continue |
| Gate 2 | ESCALATE | Pause; escalate to Decision Authority |
| Gate 2 | TERMINATE | Stop; proceed to premature DECIDE |
| Gate 3 | STOP | Archive pilot; document lessons learned |
| Gate 3 | EXTEND | Return to INSTRUMENT/BASELINE with new window |
| Gate 3 | EXPAND | Charter new pilot with expanded scope |
| Gate 3 | DEPLOY | Execute production transition plan |

## Implementation note

> The platform does not yet implement pilot-level gate evaluation as
> runtime objects. For the first real pilot, gates are evaluated
> manually:
> - The reviewer follows this procedure
> - The gate record is created as a document (see
>   `pilot/schemas/GATE_RECORD_SCHEMA.md` for the structure)
> - The decision record is created as a document (see
>   `pilot/schemas/DECISION_RECORD_SCHEMA.md`)
> See `FIRST_CUSTOMER_READINESS.md` for details.
