# INTERVENTION_RUNBOOK.md

> Operational procedure for planning, assigning, executing, and
> closing interventions during Stage 04 — INTERVENE.
>
> This runbook TRANSLATES the canonical stage specification
> (`pilot/stages/04_INTERVENE.md`) into executable steps. It does NOT
> redefine the intervention catalog or governance labels.

## Prerequisites

Before starting INTERVENE:

- [ ] DEFINE complete, Gate 1 passed
- [ ] INSTRUMENT complete — telemetry collected and validated
- [ ] BASELINE complete — all operators scored
- [ ] DIAGNOSE complete — patterns detected, diagnoses generated
- [ ] Diagnoses reviewed — recommended interventions identified

## Intervention catalog

The 12-entry intervention catalog is defined in
`src/interventions/registry.py`. It is NOT configurable. The entries:

| ID | Name | Class | Target metric | Typical followup days | Reason pattern |
|---|---|---|---|---|---|
| CTX-001 | Persistent Project Context | workflow | leverage | 14 | low leverage |
| CTX-002 | Context Handoff Template | workflow | leverage | 14 | resets/handoffs |
| CTX-003 | Memory Tool Trial | tooling | leverage | 21 | low reuse |
| FRM-001 | Task Decomposition Guide | guide | yield | 14 | rich input/weak output |
| FRM-002 | Acceptance-Criteria Template | guide | yield | 14 | retry/rework |
| MOD-001 | Model Routing Trial | tooling | yield | 21 | model sensitivity |
| AGT-001 | Agent/Tool Selection Review | tooling | yield | 14 | tool mismatch |
| REV-001 | Verification Loop | workflow | token_snr | 14 | high generation/weak review |
| STD-001 | Standard Project Scaffold | workflow | any | 21 | volatility |
| COA-001 | Operator Coaching Session | human | yield | 30 | unresolved pattern |
| LRN-001 | External Training Assignment | partner | any | 90 | skill gap outside operator telemetry |
| STG-001 | Stage Placement Trial | workflow | yield | 21 | stage specialization |

> `target_metric = any` means `InterventionCatalogEntry.target_metric`
> is `None` — any metric is accepted by
> `InterventionRegistry.validate_target_metric()`. `typical_followup_days`
> is the catalog default; the actual follow-up window is set at
> assignment time via `--followup-days`.

### Pattern → intervention mapping

| Pattern | Recommended interventions |
|---|---|
| P-CTX-01 (low context reuse) | CTX-001, CTX-002, CTX-003 |
| P-CTX-02 (context resets/handoffs) | FRM-001, MOD-001 |
| P-BURN-01 (rich input/weak output) | COA-001, CTX-001, FRM-002 |
| P-MODEL-01 (model sensitivity) | MOD-001, AGT-001 |
| P-STAGE-01 (stage specialization) | STG-001 |

## Planning procedure

### Step 1 — Review diagnoses

For each operator with a diagnosis:
1. Review the detected pattern (`diagnosis.pattern_id`)
2. Review the recommended interventions
   (`diagnosis.recommended_interventions`)
3. Review the hypothesis and evidence
4. Decide whether to intervene or observe

> Not every diagnosis requires an intervention. Some operators may
> have patterns that are acceptable for their role. Use judgment.

### Step 2 — Select interventions

For each intervention:
1. Confirm the catalog entry matches the diagnosis pattern
2. Confirm the target metric is appropriate
3. Confirm the follow-up window is achievable within the pilot
   duration
4. Confirm the intervention is actionable (the customer can actually
   execute it)

### Step 3 — Confirm authorization

Every intervention requires `authorized_by`. The authorizer is:
- The Decision Authority (for pilot-level interventions), OR
- A designated delegate (e.g., customer sponsor, L&D lead)

> Authorization is enforced in the CLI/MCP layer. Do NOT use
> programmatic assignment without recording `authorized_by`.

## Assignment procedure

### Via CLI

```bash
enterprise intervention assign <operator_id> \
  --plan <catalog_id> \
  --target-metric <metric> \
  --followup-days <N> \
  --authorized-by <identity>
```

Example:
```bash
enterprise intervention assign op_047 \
  --plan COA-001 \
  --target-metric yield \
  --followup-days 14 \
  --authorized-by "jane.doe@acme.com"
```

### Via MCP

Call `assign_intervention` with:
- `operator_id`
- `catalog_id`
- `target_metric`
- `followup_days`
- `authorized_by`

### Via TUI

Screen 7 (Interventions) — select operator, select catalog entry,
confirm target metric and follow-up window, enter authorized_by.

### What is recorded

Each assigned intervention records:
- `intervention_id` (auto-generated or supplied)
- `operator_id`
- `catalog_id`
- `reason_pattern`
- `target_metric` (pre-declared — cannot be changed after assignment)
- `start_date`
- `followup_days` (pre-declared — cannot be changed after assignment)
- `synthetic` flag

> The target metric and follow-up window are PRE-DECLARED. They
> cannot be changed after assignment. This is critical for valid
> pre/post verification.

## Execution procedure

Interventions are executed by the customer, not by the Upsilon
platform. The platform records the intervention and measures the
result. The customer is responsible for:

1. Delivering the intervention to the operator (e.g., conducting a
   coaching session, providing a context template, configuring a
   model routing rule)
2. Confirming the intervention was delivered
3. Allowing the operator to operate normally during the follow-up
   window (no special tasks — measure natural behavior change)

> The platform does NOT track intervention delivery. The customer
> confirms delivery. The platform measures the metric change.

## Gate 2 — Pilot Health (during INTERVENE)

At each checkpoint (see `PILOT_CADENCE.md`), evaluate Gate 2:

| Check | Question | CONTINUE if | ADJUST if | ESCALATE if | TERMINATE if |
|---|---|---|---|---|---|
| Data sufficiency | Are observations flowing? | Expected rate | Slightly below | Significantly below | Stopped |
| Data quality | Any BLOCKING issues? | None | Warning trend | New BLOCKING | Unrecoverable |
| Participation | Are operators still providing telemetry? | All eligible | 1–2 dropped | 3+ dropped | Below minimum |
| Governance | Consent still valid? | Yes | N/A | Concern raised | Withdrawn |
| Protocol | Interventions following pre-declared targets? | Yes | Minor deviation | Major deviation | Protocol violation |

Record the Gate 2 outcome per `GATE_REVIEW_RUNBOOK.md`.

## Closing procedure

### Step 1 — Wait for follow-up window

Wait until the follow-up window has elapsed (start_date +
followup_days). Do NOT close an intervention early.

### Step 2 — Close with outcome

```bash
enterprise intervention close <intervention_id> \
  --outcome <SUCCESS|PARTIAL|NO_EFFECT|NEGATIVE>
```

Outcomes:
- **SUCCESS:** Target metric improved meaningfully
- **PARTIAL:** Target metric improved partially
- **NO_EFFECT:** Target metric did not change
- **NEGATIVE:** Target metric degraded

> Negative outcomes are representable and reportable. They are NOT
> hidden. This is correct governance.

### Step 3 — Verify (in Stage 05)

After all interventions are closed, proceed to Stage 05 — VERIFY
(`PILOT_RUNBOOK.md`). Verification computes the actual pre/post
deltas.

## What this runbook does NOT cover

- Diagnostic procedure (see `PILOT_RUNBOOK.md` Stage 03)
- Verification procedure (see `PILOT_RUNBOOK.md` Stage 05)
- Gate 2 evaluation criteria (see `pilot/governance/DECISION_GATES.md`)
- Intervention catalog definitions (see `src/interventions/registry.py`)
- Intervention schema (see `pilot/schemas/INTERVENTION_SCHEMA.md`)
