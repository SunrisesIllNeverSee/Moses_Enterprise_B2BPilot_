# Upsilon Enterprise Pilot — Canonical Definition

This directory is the canonical definition, governance model, execution
protocol, reference implementation, and implementation specification
for an Upsilon Enterprise Pilot.

## What a pilot is

An Upsilon Enterprise Pilot is a bounded, instrumented evaluation of how
a real organization operates AI. It establishes a measurable baseline,
identifies actionable operating differences, applies controlled
interventions where appropriate, verifies resulting changes, and
terminates in an evidence-backed decision to stop, extend, expand, or
deploy.

A pilot is NOT:
- Data collection without a decision
- Report generation without governance
- An ongoing monitoring program without closure
- A personnel evaluation tool
- A leaderboard or ranking system
- A self-service signup flow
- Generic project-management infrastructure

## What a pilot is not

| Not a pilot | Why |
|---|---|
| Data collection without a decision | A pilot must terminate in a decision (STOP/EXTEND/EXPAND/DEPLOY) |
| Report generation without governance | A pilot requires charter, locked success criteria, and gate evaluation |
| Ongoing monitoring without closure | A pilot is bounded — it has a start date, end date, and closure date |
| Personnel evaluation | All outputs are DEVELOPMENTAL — no personnel evaluations, no punitive labels |
| Leaderboard | No bottom-employee leaderboards; composite scores are cohort distributions, not individual rankings |
| Self-service signup | Pilot legitimacy comes from governance, not self-service |
| Project management | A pilot is an evaluation, not a project-management tool |

## Lifecycle

Every pilot progresses through eight stages:

```text
DEFINE → INSTRUMENT → BASELINE → DIAGNOSE → INTERVENE → VERIFY → READOUT → DECIDE
```

See `PILOT_LIFECYCLE.md` for the full lifecycle specification and
`stages/` for per-stage documents.

## Three gates

Three formal decision gates govern the pilot lifecycle:

| Gate | Stage | Question | Outcomes |
|---|---|---|---|
| Gate 1 — Launch Readiness | End of DEFINE | Is this a valid, instrumentable pilot? | LAUNCH, LAUNCH_WITH_CONDITIONS, DEFER, DECLINE |
| Gate 2 — Pilot Health | During INTERVENE/VERIFY | Is the pilot still a valid experiment? | CONTINUE, ADJUST, ESCALATE, TERMINATE |
| Gate 3 — Closure / Scale | End of READOUT → DECIDE | Did the evidence meet the locked success criteria? | STOP, EXTEND, EXPAND, DEPLOY |

See `governance/DECISION_GATES.md` for the full gate specification.

## Four closure outcomes

Every pilot terminates in one of four closure outcomes:

| Outcome | Meaning |
|---|---|
| STOP | Did not meet success criteria. Discontinue. |
| EXTEND | Shows promise but missing evidence. Extend with bounded extension period. |
| EXPAND | Met success criteria. Expand to larger scope. |
| DEPLOY | Met success criteria. Transition to production. |

No pilot continues indefinitely. See `governance/CLOSURE_OUTCOMES.md`
for the full outcome specification.

## Document authority

This package is the controlling specification for:
- What constitutes an Upsilon Enterprise Pilot
- Pilot stages
- Pilot states
- Pilot artifacts
- Pilot gates
- Pilot success criteria
- Intervention records
- Verification outcomes
- Pilot closure decisions
- Pilot Mode requirements

It does NOT override existing measurement/scoring definitions. The 5
canonical metrics (leverage, yield, token_snr, log_leverage,
construction) and their formulas are defined in
`src/metrics/registry.py` and `demo_data/metric_registry.json` (v0.2)
and remain unchanged.

## ACME-001

The ACME-001 reference pilot uses the existing synthetic enterprise
demonstration to illustrate the full pilot lifecycle. It exposes gaps
rather than concealing them.

See `examples/ACME-001/` for the complete reference pilot.

**ACME-001 completion status:**
- DEFINE through READOUT: COMPLETE (with governance gaps documented)
- DECIDE: CANNOT COMPLETE (no closure decision capability exists)

## Current implementation maturity

| Area | Maturity | Evidence |
|---|---|---|
| Measurement & scoring | STRONG | 5 canonical metrics, 676 passing tests, all 50 demo operators scored |
| Diagnosis | STRONG | 6 pattern detectors, 56 diagnoses generated, all HYPOTHESIS |
| Intervention | STRONG | 12-entry catalog, 12 interventions with declared targets |
| Verification | STRONG | Pre/post deltas, outcome correlations, ASSOCIATION-only |
| Reporting | STRONG | Markdown, executive brief, dashboard, PDF, decision report |
| Governance labels | STRONG | DEVELOPMENTAL, ASSOCIATION, HYPOTHESIS enforced |
| Pilot identity | MISSING | No pilot_id, no pilot binding |
| Success criteria | MISSING | No schema, no locking mechanism |
| Decision gates | MISSING | No pilot-level gates (operator-level gates exist) |
| Closure decision | MISSING | No decision record, no STOP/EXTEND/EXPAND/DEPLOY |
| Pilot state machine | MISSING | No state tracking, no transition enforcement |

See `PILOT_CAPABILITY_MAP.md` for the full capability matrix and
`implementation/GAP_REGISTER.md` for the complete gap register.

## How to execute a pilot

The `operations/` directory translates the canonical stage
specifications into executable procedures. It answers: how does an
operator actually run an Upsilon Enterprise Pilot from initial
customer qualification through final decision?

- **`operations/PILOT_RUNBOOK.md`** is the master operational playbook.
  Someone who understands Upsilon but has never personally run a pilot
  should be able to follow it end-to-end.
- **`operations/FIRST_CUSTOMER_READINESS.md`** answers what must be
  true before Upsilon can responsibly begin its first real enterprise
  pilot (BLOCKING / REQUIRED BUT MANUAL / HARDENING RECOMMENDED /
  POST-PILOT / SCALE).

Operations documents are procedural, not canonical. They translate
`stages/` and `governance/` into checklists, commands, and
responsibilities. If a conflict arises, the canonical documents
prevail.

## Design history (non-canonical)

The `context/` directory preserves design reasoning, proof points,
unresolved questions, and architectural history. It is explicitly
NON-CANONICAL. Material in `context/` may explain why canonical
decisions were made, but it does NOT override the Upsilon Pilot
Specification, governance documents, stage specifications, schemas,
or accepted decision records.

- **`context/PILOT_PROOF_POINTS.md`** catalogs demonstrated
  capabilities to prevent already-built capabilities from being
  forgotten or unnecessarily rebuilt.
- **`context/DECISION_LOG.md`** records consequential pilot-architecture
  decisions.

## How developers should use this package

1. **Read `UPSILON_PILOT_SPEC.md`** for the canonical pilot definition.
2. **Read `PILOT_LIFECYCLE.md`** for the eight-stage lifecycle.
3. **Read `governance/`** for charter, success criteria, gates, closure
   outcomes, and state machine.
4. **Read `schemas/`** for the formal schemas of pilot objects.
5. **Read `implementation/EXISTING_SURFACE_MAP.md`** to understand what
   already exists in the platform.
6. **Read `implementation/PILOT_MODE_BUILD_PLAN.md`** for the
   implementation delta required for formal Pilot Mode.
7. **Read `examples/ACME-001/`** for a complete reference pilot that
   exposes gaps.
8. **Read `operations/PILOT_RUNBOOK.md`** if you need to execute a
   pilot.
9. **Read `operations/FIRST_CUSTOMER_READINESS.md`** before onboarding
   the first real customer.
10. **Do NOT modify runtime code** until this package has been reviewed
    and the implementation plan is approved.

## Package structure

```text
pilot/
├── README.md                          ← this file
├── UPSILON_PILOT_SPEC.md              ← canonical pilot definition
├── PILOT_LIFECYCLE.md                 ← eight-stage lifecycle
├── PILOT_CAPABILITY_MAP.md            ← capability maturity matrix
├── PILOT_EXTERNAL_BENCHMARKS.md       ← external benchmark requirements
│
├── governance/
│   ├── PILOT_CHARTER.md               ← charter specification
│   ├── SUCCESS_CRITERIA.md            ← success criteria specification
│   ├── DECISION_GATES.md              ← three gates specification
│   ├── CLOSURE_OUTCOMES.md            ← four closure outcomes
│   └── PILOT_STATE_MACHINE.md         ← state machine specification
│
├── stages/
│   ├── 00_DEFINE.md
│   ├── 01_INSTRUMENT.md
│   ├── 02_BASELINE.md
│   ├── 03_DIAGNOSE.md
│   ├── 04_INTERVENE.md
│   ├── 05_VERIFY.md
│   ├── 06_READOUT.md
│   └── 07_DECIDE.md
│
├── schemas/
│   ├── PILOT_OBJECT.md                ← conceptual Pilot object
│   ├── PILOT_CHARTER_SCHEMA.md
│   ├── FINDING_SCHEMA.md
│   ├── INTERVENTION_SCHEMA.md
│   ├── VERIFICATION_SCHEMA.md
│   ├── GATE_RECORD_SCHEMA.md
│   └── DECISION_RECORD_SCHEMA.md
│
├── implementation/
│   ├── EXISTING_SURFACE_MAP.md        ← what already exists
│   ├── GAP_REGISTER.md                ← complete gap register
│   ├── HARDENING_PLAN.md              ← production hardening plan
│   └── PILOT_MODE_BUILD_PLAN.md       ← implementation delta
│
├── examples/
│   └── ACME-001/                      ← reference pilot (synthetic)
│       ├── README.md
│       ├── 00_PILOT_CHARTER.md
│       ├── 01_INSTRUMENTATION_READINESS.md
│       ├── 02_BASELINE_SNAPSHOT.md
│       ├── 03_DIAGNOSTIC_FINDINGS.md
│       ├── 04_INTERVENTIONS.md
│       ├── 05_VERIFICATION_RESULTS.md
│       ├── 06_GATE_RECORDS.md
│       ├── 07_PILOT_READOUT.md
│       ├── 08_DECISION_RECORD.md
│       └── 08_ARTIFACT_INDEX.md       ← deviation: not in required
│                                         structure; added to index all
│                                         ACME-001 evidence artifacts
│                                         (see Structural deviations)
│
├── operations/
│   ├── PILOT_RUNBOOK.md               ← master operational playbook
│   ├── PRE_PILOT_CHECKLIST.md         ← platform/operator readiness
│   ├── CUSTOMER_INTAKE.md             ← customer qualification procedure
│   ├── PILOT_LAUNCH_CHECKLIST.md      ← Gate 1 launch readiness
│   ├── PILOT_CADENCE.md               ← checkpoint/gate/communication cadence
│   ├── INTERVENTION_RUNBOOK.md        ← intervention execution procedure
│   ├── GATE_REVIEW_RUNBOOK.md         ← gate review procedure (Gates 1/2/3)
│   ├── PILOT_CLOSEOUT_CHECKLIST.md    ← closeout after closure decision
│   └── FIRST_CUSTOMER_READINESS.md    ← first real pilot readiness bar
│
├── research/
│   ├── PILOT_COMPARISON_MATRIX.md     ← structural comparison
│   └── SOURCES.md                     ← sources consulted
│
├── context/                           ← NON-CANONICAL design history
│   ├── README.md                      ← non-canonical warning
│   ├── ORIGIN_AND_RATIONALE.md        ← why capabilities exist
│   ├── PILOT_PROOF_POINTS.md          ← demonstrated capabilities
│   ├── OPEN_QUESTIONS.md              ← unresolved design questions
│   └── DECISION_LOG.md                ← consequential decisions
│
├── operations/                        ← NON-CANONICAL operational runbooks
│   ├── PILOT_RUNBOOK.md               ← day-to-day pilot operations
│   ├── PILOT_CADENCE.md                ← cadence and timing
│   ├── PRE_PILOT_CHECKLIST.md         ← pre-pilot readiness
│   ├── PILOT_LAUNCH_CHECKLIST.md      ← launch readiness
│   ├── PILOT_CLOSEOUT_CHECKLIST.md    ← closeout steps
│   ├── INTERVENTION_RUNBOOK.md        ← intervention procedures
│   ├── GATE_REVIEW_RUNBOOK.md         ← gate review procedures
│   ├── CUSTOMER_INTAKE.md             ← customer intake process
│   └── FIRST_CUSTOMER_READINESS.md    ← first customer readiness
│
└── review/
    └── IMPLEMENTATION_REVIEW_MEMO.md  ← final review memo
```

## Structural deviations

The following deviations from the required directory structure are
documented per the prompt's "Minor structural changes are permitted if
repository conventions strongly justify them. Document any deviation."

1. **`examples/ACME-001/08_ARTIFACT_INDEX.md`** — Not in the required
   structure. Added to provide a complete index of all evidence
   artifacts (pilot package artifacts, runtime evidence artifacts,
   generated report artifacts, and missing artifacts) produced by the
   ACME-001 reference pilot. This file consolidates the evidence
   inventory that would otherwise be scattered across the other ACME-001
   files, making it easier to verify that ACME-001 exposes gaps rather
   than concealing them. The `review/` directory is also not in the
   required structure — it holds the final review memo required by the
   prompt's "FINAL DELIVERABLE" section.
