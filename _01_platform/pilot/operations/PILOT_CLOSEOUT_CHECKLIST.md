# PILOT_CLOSEOUT_CHECKLIST.md

> Checklist for closing out an Upsilon Enterprise Pilot after Gate 3
> has produced a closure decision (STOP / EXTEND / EXPAND / DEPLOY).
>
> This checklist is executed at the end of Stage 07 — DECIDE. See
> `PILOT_RUNBOOK.md` Stage 07 for the DECIDE procedure.

## Prerequisites

- [ ] Gate 3 evaluated per `GATE_REVIEW_RUNBOOK.md`
- [ ] Closure outcome selected (STOP / EXTEND / EXPAND / DEPLOY)
- [ ] Decision Record created (see
  `pilot/schemas/DECISION_RECORD_SCHEMA.md`)

## Universal closeout (all outcomes)

- [ ] Decision Record created with all required fields
- [ ] Decision Record is immutable (`immutable: true`)
- [ ] Gate 3 record created and stored
- [ ] Evidence cited in the Decision Record (specific artifacts)
- [ ] Success criteria comparison recorded (per-criterion
  MET/MISSED/PARTIAL)
- [ ] Pilot Charter archived (the original charter, unchanged)
- [ ] All stage artifacts archived (charter, instrumentation
  readiness, baseline snapshot, diagnostic findings, intervention
  records, verification results, gate records, readout, decision
  record)
- [ ] Customer notified of the decision
- [ ] Decision communicated in person (call or meeting), not just
  emailed
- [ ] Pilot marked as TERMINATED in records

## If STOP

- [ ] Findings summary documented (what was measured, what was found)
- [ ] Lessons learned documented (what the pilot revealed, even in
  failure)
- [ ] Root cause analysis documented (why criteria were missed)
- [ ] Recommendation documented (whether to charter a new pilot with
  different scope)
- [ ] All `stop_lessons` fields completed in the Decision Record:
  - [ ] `findings_summary`
  - [ ] `lessons_learned` (list)
  - [ ] `root_cause_analysis`
  - [ ] `recommendation`
- [ ] Customer debriefed on lessons learned
- [ ] Pilot archived for institutional memory

## If EXTEND

- [ ] All five EXTEND requirements documented in the Decision Record:
  - [ ] `explicit_reason` (why evidence is insufficient)
  - [ ] `missing_evidence` (what specific evidence is needed)
  - [ ] `new_evidence_requirement` (how it will be collected)
  - [ ] `extension_period_days` (how long the extension will last)
  - [ ] `new_closure_date` (specific date for Gate 3 re-evaluation)
- [ ] Extension period is bounded (no indefinite extension)
- [ ] New closure date is specific and recorded
- [ ] Customer notified of extension and new closure date
- [ ] Plan for returning to INSTRUMENT or BASELINE with new window
- [ ] Gate 2 checkpoints scheduled for the extension period
- [ ] Current evidence preserved (do not discard baseline/diagnosis
  data)

> EXTEND returns to INSTRUMENT or BASELINE with a new window. The
> charter is NOT re-created. Success criteria are NOT amended (they
> were locked before measurement). If the criteria are wrong, the
> pilot must be STOPPED and a new pilot chartered.

## If EXPAND

- [ ] Expansion scope documented in the Decision Record:
  - [ ] `new_population` (new operator set or expanded count)
  - [ ] `new_duration_days` (new window length)
  - [ ] `new_eval_families` (additional eval families)
  - [ ] `new_pilot_id` (the ID for the expanded pilot)
- [ ] Expansion rationale documented (why expansion is the right
  next step vs DEPLOY)
- [ ] New success criteria defined for the expanded pilot (locked
  before measurement)
- [ ] New Pilot Charter planned for the expanded pilot
- [ ] Current pilot archived (it is terminated — EXPAND creates a
  new pilot)
- [ ] Customer notified that a new pilot will be chartered

> EXPAND creates a NEW pilot with its own charter, ID, and success
> criteria. The current pilot is terminated. Do NOT continue the
> current pilot under the expanded scope.

## If DEPLOY

- [ ] Production transition plan documented in the Decision Record:
  - [ ] `production_transition_checklist` (list)
  - [ ] `monitoring_plan` (how production use will be monitored)
  - [ ] `rollback_plan` (what happens if deployment encounters issues)
- [ ] All critical success criteria were MET
- [ ] Infrastructure readiness confirmed
- [ ] Governance framework supports ongoing production use
- [ ] Ongoing monitoring plan defined (may charter Commercial Pilot
  #10 "Monitor" for ongoing monitoring)
- [ ] Customer notified of production transition
- [ ] Production transition timeline communicated
- [ ] Pilot archived (it is terminated — DEPLOY transitions to
  production)

## Artifact archive

Archive the following artifacts (all are immutable once the pilot is
terminated):

| Artifact | Stage | Format |
|---|---|---|
| Pilot Charter | DEFINE | Document + JSON config |
| Gate 1 Record | DEFINE | Document |
| Instrumentation Readiness Record | INSTRUMENT | Document |
| Baseline Snapshot | BASELINE | Document + data |
| Diagnostic Findings | DIAGNOSE | Document + data |
| Intervention Records | INTERVENE | Document + data |
| Gate 2 Records | INTERVENE/VERIFY | Documents |
| Verification Results | VERIFY | Document + data |
| Pilot Readout | READOUT | Document + reports |
| Gate 3 Record | DECIDE | Document |
| Decision Record | DECIDE | Document (immutable) |

> For the first real pilot, artifacts are stored as files. Future
> implementation will persist to SQLite (see
> `pilot/implementation/PILOT_MODE_BUILD_PLAN.md` T2.3).

## Customer deliverables

Provide the customer with:

- [ ] Executive brief (`enterprise export brief`)
- [ ] Pilot markdown readout (`enterprise export pilot`)
- [ ] Decision report (`PilotService.decision_report()`)
- [ ] Evidence-vs-criteria comparison (from the readout)
- [ ] Closure decision document (the Decision Record)
- [ ] (Optional) Executive dashboard (`enterprise export dashboard`)
- [ ] (Optional) Operator profiles (anonymized, developmental)

> All deliverables are DEVELOPMENTAL. No personnel evaluations. No
> bottom-employee leaderboards. No punitive labels.

## Post-pilot

- [ ] Pilot archived for institutional memory
- [ ] Lessons learned recorded (even for successful pilots)
- [ ] Cross-pilot findings database updated (when implemented — see
  `pilot/implementation/PILOT_MODE_BUILD_PLAN.md` T3.4)
- [ ] Customer follow-up scheduled (30 days post-decision for DEPLOY;
  at new closure date for EXTEND)
- [ ] Internal retrospective scheduled (Pilot Creator + Pilot
  Operator + Decision Authority)

## What this checklist does NOT cover

- Gate 3 evaluation procedure (see `GATE_REVIEW_RUNBOOK.md`)
- Decision Record schema (see `pilot/schemas/DECISION_RECORD_SCHEMA.md`)
- Closure outcome definitions (see
  `pilot/governance/CLOSURE_OUTCOMES.md`)
- Production transition checklist (to be defined — see
  `pilot/implementation/PILOT_MODE_BUILD_PLAN.md` T3.5)
