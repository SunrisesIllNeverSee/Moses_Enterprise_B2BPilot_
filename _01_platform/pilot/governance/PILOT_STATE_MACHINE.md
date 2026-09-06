# PILOT_STATE_MACHINE.md

> The canonical state machine for an Upsilon Enterprise Pilot.
>
> Every pilot transitions through these states. No state may be skipped.
> Transitions are gated by the decision gates defined in
> `DECISION_GATES.md`.

## State diagram

```text
                    ┌─────────┐
                    │ DEFINED │ ← Gate 1: LAUNCH or LAUNCH_WITH_CONDITIONS
                    └────┬────┘
                         ↓
                  ┌──────────────┐
                  │ INSTRUMENTED │
                  └──────┬───────┘
                         ↓
                  ┌───────────┐
                  │ BASELINED │
                  └─────┬─────┘
                        ↓
                  ┌────────────┐
                  │ DIAGNOSED  │
                  └─────┬──────┘
                        ↓
                  ┌──────────────┐
            ┌────→│ INTERVENING  │←── Gate 2: CONTINUE or ADJUST
            │     └──────┬───────┘
            │            ↓
            │     ┌────────────┐
            │     │  VERIFYING  │
            │     └──────┬─────┘
            │            ↓
            │     ┌────────────┐
            │     │  READOUT    │
            │     └──────┬─────┘
            │            ↓
            │     ┌────────────┐
            │     │  DECIDING   │ ← Gate 3: STOP / EXTEND / EXPAND / DEPLOY
            │     └──────┬─────┘
            │            ↓
            │     ┌────────────┐
            │     │  TERMINATED │
            │     └────────────┘
            │
            └── Gate 2: ADJUST (return to INTERVENE with adjusted protocol)

Gate 2: ESCALATE → pause (hold state, await decision authority)
Gate 2: TERMINATE → jump to DECIDING (premature closure)
Gate 3: EXTEND → return to INSTRUMENTED or BASELINED with new window
Gate 3: EXPAND → new pilot (new charter, new ID)
Gate 3: DEPLOY → transition to production (terminal)
Gate 3: STOP → TERMINATED (terminal)
```

## States

| State | Description | Entry condition | Exit condition |
|---|---|---|---|
| DEFINED | Pilot charter created, success criteria locked, configuration validated | Gate 1: LAUNCH or LAUNCH_WITH_CONDITIONS | Telemetry collection begins |
| INSTRUMENTED | Telemetry collected and validated for the population | Sufficient observations, no BLOCKING quality issues | Baseline metrics computed |
| BASELINED | Canonical metrics computed for all eligible operators | All eligible operators scored, distributions computed | Diagnostic analysis complete |
| DIAGNOSED | Patterns detected, hypotheses generated, divergence analyzed | All active eval families produced results | Interventions assigned (or no interventions needed) |
| INTERVENING | Controlled interventions applied with declared targets | Interventions assigned, Gate 2: CONTINUE | Follow-up windows complete |
| VERIFYING | Pre/post deltas computed, outcomes correlated | All interventions verified, all closed | Readout generated |
| READOUT | Evidence synthesized into decision-oriented readout | All reporting complete, evidence compared to criteria | Gate 3 evaluated |
| DECIDING | Gate 3 evaluated, closure outcome selected | Decision record created | Decision documented and archived |
| TERMINATED | Pilot is complete. Decision record is immutable. | Closure outcome recorded | (terminal) |

## Transitions

| From | To | Trigger | Gate |
|---|---|---|---|
| (none) | DEFINED | Pilot charter created + configuration validated | Gate 1: LAUNCH/LAUNCH_WITH_CONDITIONS |
| DEFINED | INSTRUMENTED | Telemetry collection begins | — |
| INSTRUMENTED | BASELINED | Baseline metrics computed | — |
| BASELINED | DIAGNOSED | Diagnostic analysis complete | — |
| DIAGNOSED | INTERVENING | Interventions assigned | Gate 2: CONTINUE |
| INTERVENING | VERIFYING | Follow-up windows complete | Gate 2: CONTINUE |
| VERIFYING | READOUT | All interventions verified + closed | — |
| READOUT | DECIDING | Readout generated + evidence compared | — |
| DECIDING | TERMINATED | Closure outcome recorded | Gate 3: STOP/DEPLOY |
| DECIDING | INSTRUMENTED | Gate 3: EXTEND (new window) | Gate 3: EXTEND |
| DECIDING | (new pilot) | Gate 3: EXPAND (new charter) | Gate 3: EXPAND |
| INTERVENING | INTERVENING | Gate 2: ADJUST (adjusted protocol) | Gate 2: ADJUST |
| INTERVENING | DECIDING | Gate 2: TERMINATE (premature closure) | Gate 2: TERMINATE |
| INTERVENING | (paused) | Gate 2: ESCALATE (await decision authority) | Gate 2: ESCALATE |
| (paused) | INTERVENING | Decision authority responds | — |

## Invariants

1. **No state may be skipped.** A pilot cannot go from BASELINED to
   INTERVENING without passing through DIAGNOSED.
2. **Gate 1 must pass before INSTRUMENTED.** No telemetry collection
   without a valid charter.
3. **Gate 2 is evaluated during INTERVENING and VERIFYING.** The pilot
   can be terminated early if it is no longer a valid experiment.
4. **Gate 3 must produce a terminal decision.** No indefinite DECIDING
   state.
5. **EXTEND returns to INSTRUMENTED or BASELINED** with a new window —
   not to DEFINED (the charter is not re-created, only the window is
   extended).
6. **EXPAND creates a new pilot.** The expanded pilot has its own charter,
   ID, and success criteria.
7. **TERMINATED is immutable.** Once a pilot is terminated, its decision
   record cannot be changed.

## Current implementation status

**NOT IMPLEMENTED.** The platform has no explicit state machine. The
demo flow (`enterprise demo full`) runs 10 steps linearly but does not
track state, persist it, or enforce transitions. `pilot_status()` returns
a snapshot but does not include a `current_stage` or `state` field.

This is a P1 gap — see `GAP_REGISTER.md` and `PILOT_MODE_BUILD_PLAN.md`.
