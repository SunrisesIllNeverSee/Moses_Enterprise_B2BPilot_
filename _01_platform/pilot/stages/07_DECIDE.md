# Stage 07 — DECIDE

## Purpose

Make the evidence-backed terminal decision. Every pilot terminates in a
decision: STOP, EXTEND, EXPAND, or DEPLOY. No pilot continues indefinitely.

## Governing question

> Given the evidence compared against the locked success criteria, what
> is the decision?

## Inputs

- Pilot readout (from READOUT)
- Evidence-vs-success-criteria comparison
- Gate 3 (CLOSURE / SCALE) evaluation

## Upsilon actions

1. Evaluate **GATE 3 (CLOSURE / SCALE)** — compare evidence against the
   criteria locked before launch.
2. Select a closure outcome:
   - **STOP**: The pilot did not meet success criteria. Discontinue. Document
     findings and lessons learned.
   - **EXTEND**: The pilot shows promise but is missing evidence. Extend with
     a defined extension period, new evidence requirement, and new closure
     date. No indefinite extension.
   - **EXPAND**: The pilot met success criteria. Expand to a larger
     population, longer duration, or additional eval families.
   - **DEPLOY**: The pilot met success criteria and the organization is
     ready for production deployment. Transition to production.
3. Document the decision with:
   - Decision rationale
   - Evidence cited
   - Success criteria comparison
   - Conditions (if any)
   - Next steps
4. Record the decision as an immutable `DecisionRecord`.
5. Archive the pilot for institutional memory.

## Existing implementation

| Capability | Implementation | Evidence |
|---|---|---|
| Gate 3 (CLOSURE / SCALE) | **NOT IMPLEMENTED** — no pilot-level closure gate exists | — |
| Closure outcomes | **NOT IMPLEMENTED** — no STOP/EXTEND/EXPAND/DEPLOY decision record | — |
| Decision record | **NOT IMPLEMENTED** — no `DecisionRecord` schema or persistence | — |
| Pilot archive | **NOT IMPLEMENTED** — no pilot archive or institutional memory | — |
| Production transition | `deployment_level` (1/2/3) in `PilotConfiguration` — but no transition checklist or deployment gate | `src/domain/pilot_configuration.py` |

> **This is the single largest gap in the platform.** The entire pilot
> lifecycle exists from DEFINE through READOUT, but there is no formal
> closure decision. Pilots do not terminate. See `GAP_REGISTER.md` and
> `PILOT_MODE_BUILD_PLAN.md`.

## Checklist

- [ ] Gate 3 (CLOSURE / SCALE) evaluated
- [ ] Closure outcome selected (STOP / EXTEND / EXPAND / DEPLOY)
- [ ] Decision rationale documented
- [ ] Evidence cited (specific verification results, readout sections)
- [ ] Success criteria comparison documented
- [ ] Conditions documented (if EXTEND or EXPAND with conditions)
- [ ] Extension period defined (if EXTEND — no indefinite extension)
- [ ] New closure date set (if EXTEND)
- [ ] Decision record persisted (immutable)
- [ ] Pilot archived for institutional memory

## Required evidence

- Gate 3 evaluation result
- Decision record (closure outcome + rationale + evidence + conditions)
- Success criteria comparison table
- Extension plan (if EXTEND)
- Deployment plan (if DEPLOY)
- Expansion plan (if EXPAND)
- Lessons learned (if STOP)

## Artifact

**Decision Record** — the immutable terminal decision. See
`examples/ACME-001/08_DECISION_RECORD.md` and
`schemas/DECISION_RECORD_SCHEMA.md`.

## Exit criteria

- A closure outcome is selected and documented
- Decision record is persisted and immutable
- All evidence is cited
- If EXTEND: extension period + new closure date + missing evidence defined
- Pilot is archived

## Failure states

- No closure outcome selected (indefinite pilot — not permitted)
- EXTEND without extension period or new closure date (not permitted)
- Decision not backed by evidence
- Success criteria not compared
- Decision record not persisted

## Next stage

→ **Terminal**. The pilot is complete. If EXTEND, return to the appropriate
stage (usually INSTRUMENT or BASELINE) with the new window. If EXPAND,
return to DEFINE with the expanded scope. If DEPLOY, transition to
production. If STOP, archive and document lessons learned.
