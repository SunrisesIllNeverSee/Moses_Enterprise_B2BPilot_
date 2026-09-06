# PILOT_CADENCE.md

> Recommended cadence for checkpoints, gate reviews, and customer
> communications throughout an Upsilon Enterprise Pilot.
>
> This is a recommended cadence, not a mandate. Adjust based on the
> pilot's duration, population, and intervention intensity. Gate
> timing is governed by `pilot/governance/DECISION_GATES.md`.

## Standard pilot timeline

```text
Day 0:   DEFINE complete, Gate 1 passed (LAUNCH)
Day 1:   INSTRUMENT begins — telemetry collection starts
Day 7:   Checkpoint 1 — data flow confirmed
Day 14:  Checkpoint 2 — data quality review
Day 21:  Checkpoint 3 — participation check
Day 30:  BASELINE — baseline window ends, metrics computed
Day 31:  DIAGNOSE — patterns detected, diagnoses generated
Day 32:  INTERVENE — interventions assigned (if intervention pilot)
Day 32:  Gate 2 checkpoint 1 — pilot health review
Day 39:  Gate 2 checkpoint 2 — pilot health review
Day 46:  VERIFY — follow-up window ends, verification computed
Day 47:  READOUT — readout generated
Day 48:  DECIDE — Gate 3 evaluated, decision made
Day 48:  Pilot terminated (STOP/EXTEND/EXPAND/DEPLOY)
```

> For a 30-day baseline + 14-day follow-up pilot. Adjust for
> different durations.

## Checkpoint cadence

### During INSTRUMENT (Days 1–30)

| Checkpoint | When | What to check | Action if issue |
|---|---|---|---|
| Data flow | Day 7 | Observations flowing at expected rate | If <50% expected, investigate provider access |
| Data quality | Day 14 | No BLOCKING issues; WARNING count acceptable | If BLOCKING, pause ingestion and resolve |
| Participation | Day 21 | All operators providing telemetry | If operators missing, escalate to customer sponsor |
| Pre-baseline | Day 28 | Sufficient observations for baseline | If insufficient, consider EXTEND before baseline |

### During INTERVENE (Days 32–46)

| Checkpoint | When | What to check | Action if issue |
|---|---|---|---|
| Gate 2 — Health | Day 32 | Pilot is still a valid experiment | CONTINUE / ADJUST / ESCALATE / TERMINATE |
| Intervention adherence | Day 39 | Interventions following pre-declared targets | If protocol violation, ESCALATE |
| Gate 2 — Health | Day 39 | Pilot is still a valid experiment | CONTINUE / ADJUST / ESCALATE / TERMINATE |

### During VERIFY (Days 46–47)

| Checkpoint | When | What to check | Action if issue |
|---|---|---|---|
| Follow-up data | Day 46 | Follow-up observations collected | If missing, EXTEND follow-up window |
| Verification completeness | Day 47 | All interventions verified | If incomplete, document and proceed to READOUT |

## Gate review cadence

| Gate | When | Frequency | Procedure |
|---|---|---|---|
| Gate 1 — Launch Readiness | End of DEFINE | Once | `GATE_REVIEW_RUNBOOK.md` |
| Gate 2 — Pilot Health | During INTERVENE/VERIFY | Weekly or at milestones | `GATE_REVIEW_RUNBOOK.md` |
| Gate 3 — Closure / Scale | End of READOUT → DECIDE | Once | `GATE_REVIEW_RUNBOOK.md` |

> Gate 2 is evaluated at regular checkpoints during INTERVENE and
> VERIFY. It is NOT an intervention-performance gate — it evaluates
> whether the pilot itself remains a valid experiment.

## Customer communication cadence

| Communication | When | Channel | Content |
|---|---|---|---|
| Launch notification | Day 0 | Email + call | Pilot launched, what to expect, timeline |
| Data flow confirmation | Day 7 | Email | Telemetry flowing, no action needed |
| Mid-pilot update | Day 21 | Call | Participation status, any issues, on track |
| Baseline delivered | Day 31 | Call + report | Baseline metrics, initial findings |
| Intervention plan | Day 32 | Call + document | Which interventions, why, expected outcomes |
| Health update | Day 39 | Email | Pilot healthy, interventions in progress |
| Readout scheduled | Day 46 | Email | Readout meeting scheduled for Day 48 |
| Readout delivered | Day 48 | Call + report | Full readout, evidence, decision |
| Decision communicated | Day 48 | Call + document | Closure outcome (STOP/EXTEND/EXPAND/DEPLOY) |

## Operator communication cadence

| Communication | When | Channel | Content |
|---|---|---|---|
| Disclosure | Before Day 1 | Customer internal | AI usage is being measured (developmental, not personnel) |
| Consent | Before Day 1 | Customer internal | Consent per consent model (opt_in/opt_out/mandated) |
| No active task | Days 1–46 | None | Operators do not need to do anything — telemetry is passive |
| Post-pilot | Day 48 | Customer internal | Pilot complete, developmental outcomes shared if appropriate |

> Operators do not need to perform any active task during the pilot.
> Telemetry is collected passively from provider usage. The pilot
> measures how operators already use AI, not how they perform tasks.

## Internal (Upsilon side) cadence

| Activity | When | Who | Output |
|---|---|---|---|
| Daily data check | Days 1–30 | Pilot Operator | Observation count, data quality snapshot |
| Weekly pilot review | Weekly | Pilot Creator + Pilot Operator | Status, issues, blockers |
| Gate 2 review | Day 32, Day 39 | Pilot Creator + Decision Authority | Gate 2 record |
| Pre-readout review | Day 47 | Pilot Creator + Pilot Operator | Readout draft, criteria comparison |
| Gate 3 review | Day 48 | Decision Authority | Gate 3 record, Decision Record |

## Adjusting the cadence

| Situation | Adjustment |
|---|---|
| Longer baseline window (60 days) | Double checkpoint intervals; add Day 45 mid-baseline review |
| Shorter baseline window (14 days) | Checkpoints at Day 3, Day 7, Day 12 |
| No interventions (baseline-only pilot) | Skip INTERVENE and VERIFY checkpoints; go directly to READOUT |
| Multiple intervention waves | Add Gate 2 checkpoint per wave |
| EXTEND outcome | Reset timeline from new INSTRUMENT/BASELINE start; new closure date |

## What this cadence does NOT define

- Gate evaluation criteria (see `pilot/governance/DECISION_GATES.md`)
- Stage completion criteria (see `pilot/stages/`)
- Intervention execution details (see `INTERVENTION_RUNBOOK.md`)
- Closeout procedure (see `PILOT_CLOSEOUT_CHECKLIST.md`)
