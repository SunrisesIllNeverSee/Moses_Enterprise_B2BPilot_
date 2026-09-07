# DRIFT_AND_CONTRADICTIONS.md

> Drifts and contradictions between the original dossier, the current
> platform, and the canonization package.
>
> This document is NON-CANONICAL. It records conflicts that should be
> resolved or explicitly accepted before the pilot package is frozen.
> It does NOT override any canonical document.
>
> Each drift is grounded in repository evidence. Where the evidence is
> ambiguous, the entry is marked **UNRESOLVED**.

## Method

Each drift is identified by:
1. The original state (what the dossier or spec intended).
2. The current state (what the codebase/demo/reports show).
3. The contradiction or gap.
4. The recommended resolution.
5. The status (RESOLVED, ACCEPTED, OPEN, or UNRESOLVED).

### Status classifications

| Status | Meaning |
|---|---|
| **RESOLVED** | The drift has been addressed in the canonization package. |
| **ACCEPTED** | The drift is acknowledged and accepted as-is with documented rationale. |
| **OPEN** | The drift is known but not yet resolved. Action required. |
| **UNRESOLVED** | The drift cannot be fully characterized from available evidence. |

---

## Drift 1 — The flagship demo changed markets

**Original state:** The deep-dive review
(`review/UPSILON_ORIGINAL_TO_CURRENT_DEEP_DIVE_REVIEW.md` §2, §17)
states the original SignalAF commercial field dossier specified a
nontechnical or mixed-role workforce (Sales, Marketing, Operations,
Finance, People/Administration, Support) as the first commercial
beachhead, and "explicitly argued against allowing the flagship
50-person demonstration to become 50 developers."

**Current state:** The demo fixture (`demo_data/operators.json`)
contains 50 operators with the following department distribution:

| Department | Count |
|---|---|
| Product Engineering | 18 |
| Platform / Infrastructure | 10 |
| Data / Analytics | 8 |
| Product / Design | 6 |
| Customer Engineering / Support | 4 |
| Operations / GTM | 4 |

The default workflow is `software_dev_v1` (Software Development). The
demo is described as "Acme AI-Enabled Software Company"
(`demo_data/graphics/g09_sample_customer_report.md`).

**Contradiction:** The technical build succeeded while the flagship
commercial proof shifted toward software engineering. The original
mixed-role beachhead is not represented in the demo fixture.

**Recommended resolution:** Per the deep-dive review (§17): do NOT
destroy the existing fixture — it is a valuable technical stress test.
Preserve it as `ACME-TECH-001` and create a second fixture
`ACME-MIXED-ROLE-001` that restores the original nontechnical
commercial beachhead with adequate workflow-stage evidence.

**Status:** OPEN — neither `ACME-TECH-001` nor `ACME-MIXED-ROLE-001`
exist in `examples/`. The current `examples/ACME-001/` uses the
existing technical fixture. This is a Priority 5 item in the
deep-dive review's build order.

> **UNRESOLVED:** The specific spec statement mandating a mixed-role
> beachhead could not be located in the available `_specs/` documents.
> The `_specs/02_ENTERPRISE_DEMO_DATA_SPEC.md` describes the demo as
> "Acme AI-Enabled Software Company," suggesting the technical shift
> may have occurred at the spec level. The original SignalAF
> commercial field dossier is not present in the repository to
> confirm. See `ORIGINAL_DOSSIER_TRACEABILITY.md` requirement #3.

---

## Drift 2 — The report layer outran the evidence (12,842 vs 1,668)

**Original state:** The static sample customer report
(`demo_data/graphics/g09_sample_customer_report.md`) claims:

> **Observations:** 12,842 interaction-level records

It also claims divergence counts of:

| Quadrant | Count | Percentage |
|---|---|---|
| HIGH_USAGE_LOW_OPERATION | 13 | 26% |
| LOW_USAGE_HIGH_OPERATION | 11 | 22% |
| MIXED | 24 | 48% |
| LOW_LOW | 2 | 4% |

**Current state:** The executable demo contains 1,668 canonical
observation records (`demo_data/observations.jsonl`). The runtime
divergence analysis produces:

| Quadrant | Count |
|---|---|
| HIGH_USAGE_LOW_OPERATION | 3 |
| LOW_USAGE_HIGH_OPERATION | 5 |
| MIXED | 30 |
| LOW_LOW | 12 |

**Contradiction:** The static report and the executable dataset are
not synchronized. The static report claims 12,842 observations and
divergence counts that do not match the runtime. There may once have
been an upstream 12,842-interaction fixture, but that evidence is not
present or traceable in the current archive.

**Recommended resolution:** Per the deep-dive review (§17, Drift 2,
Priority 0): regenerate all sample outputs from executable canonical
evidence. The static report must either be regenerated from the
current runtime or clearly labeled as a historical artifact that does
not represent current executable evidence.

**Status:** OPEN — the static report has not been regenerated. This
is the most urgent technical-integrity problem identified by the
deep-dive review. See `REPORTING_INTEGRITY_INVARIANTS.md` invariants
#1, #2, and #3.

---

## Drift 3 — The PDF can bypass runtime truth

**Original state:** The deep-dive review (§17, Drift 3) identifies two
independent report paths:

```text
runtime truth → generated Markdown (export_pilot_markdown)
```

and:

```text
stale static Markdown (g09_sample_customer_report.md) → customer PDF
```

**Current state:** `src/reporting/pdf.py` contains
`render_sample_report_pdf()` which renders the static
`demo_data/graphics/g09_sample_customer_report.md` to PDF. The CLI
`enterprise export dashboard` path generates runtime Markdown via
`export_pilot_markdown(svc)`. These are two independent paths that
can produce contradictory customer-facing outputs.

**Contradiction:** The engine can be correct while the strongest
customer-facing proof (the PDF) is wrong, because the PDF renders a
static report that may not match runtime evidence.

**Recommended resolution:** Per the deep-dive review (Priority 0,
item 4 and 5): lock reporting invariants. Require one canonical
report model. Eliminate the static-report-to-customer-PDF bypass.
All presentation formats (Markdown, HTML, PDF) must derive from the
same report model, which originates from canonical pilot evidence
and state.

**Status:** OPEN — the PDF bypass has not been removed. This is
classified as P0 and urgent by the deep-dive review. See
`REPORTING_INTEGRITY_INVARIANTS.md` invariants #2 and #3.

---

## Drift 4 — Archetype labels mix ground truth with inference

**Original state:** The `_specs/02_ENTERPRISE_DEMO_DATA_SPEC.md` §8
defines 9 "Synthetic Operator Archetypes" (Context Compounder,
High-Volume Burner, Efficient Minimalist, Kinetic Generator,
Recursive Builder, Deep Reader/Context Consumer, Unstable Explorer,
Balanced Generalist, Declining/Workflow-Fractured) and explicitly
states: "Use these as **demo generation patterns**, not necessarily
official public SigRank archetypes."

**Current state:** `src/domain/operator.py` has a `pattern_demo`
field (line 27): `pattern_demo: Optional[str] = None  # archetype
label (demo only)`. The demo fixture populates this with 9 archetype
labels. `src/analysis/team_composition.py` uses `pattern_demo` for
archetype coverage and complementarity analysis.

**Contradiction:** The `pattern_demo` labels are synthetic
ground-truth metadata assigned at fixture generation time. They are
NOT inferred from operator telemetry by the platform. However, the
team composition analysis uses them as though they were analytical
outputs. The two categories (fixture ground truth vs Upsilon
inference) are not visibly distinguished in the output.

**Recommended resolution:** Per the deep-dive review (§17, Drift 4):
fixture ground truth must be labeled separately from Upsilon
inference. Outputs that use `pattern_demo` should carry a visible
label such as "FIXTURE GROUND TRUTH — not inferred by Upsilon."

**Status:** OPEN — the distinction is not surfaced in outputs. The
`pattern_demo` field is labeled "demo only" in the source code, but
this label does not propagate to team composition outputs or reports.

---

## Drift 5 — Some original ontology did not survive (Trans Ladder)

**Original state:** The deep-dive review (§17, Drift 5) references an
original developmental ontology including the "Trans Ladder" and
labels such as Seeker, Refiner, Bearer, Igniter, Base, Power, Arch,
and Transmitter.

**Current state:** None of these terms appear in the codebase, demo
data, or spec files. The underlying ideas survived through
longitudinal movement (`src/analysis/longitudinal.py`), learning
curves (`src/analysis/learning_curve.py`), trajectory, similarity
(`src/analysis/similarity.py`), and the development engine
(`src/config/eval_registry.py` EVAL-011). The original ontology
itself was not implemented.

**Contradiction:** The original developmental vocabulary was
abandoned or deferred. The concepts survived but the labels did not.

**Recommended resolution:** Per the deep-dive review: do NOT
automatically restore the ontology. First determine whether it
improves measurement or merely adds product language. If it is not
empirically necessary, preserve it in context or research material
until validated.

**Status:** UNRESOLVED — the original ontology's source (SignalAF
commercial field dossier) is not present in the repository. The
terms cannot be traced to any available spec. See
`ORIGINAL_DOSSIER_TRACEABILITY.md` requirement #17 and
`OPEN_QUESTIONS.md` OQ-011.

---

## Drift 6 — Gate now means two different things

**Original state:** The platform already contains operator-level
"gates" in `src/domain/production_gate.py` (GATE-001, GATE-002,
GATE-003) that route operators to coaching/review based on metric
thresholds.

**Current state:** The canonization package defines pilot-level
"decision gates" in `pilot/governance/DECISION_GATES.md` (Gate 1 —
Launch Readiness, Gate 2 — Pilot Health, Gate 3 — Closure/Scale).
These are a different concept — they govern the pilot lifecycle, not
individual operator routing.

**Contradiction:** The word "gate" is overloaded. Operator-level
routing gates and pilot-level decision gates are different types
that should not be conflated.

**Recommended resolution:** Per the deep-dive review (§17, Drift 6):
distinguish `MeasurementGate` or `OperatorRoutingGate` from
`PilotDecisionGate`. The canonization package partially addresses
this — `pilot/governance/DECISION_GATES.md` explicitly states:

> "These are operator-level routing gates... The three pilot-level
> decision gates defined here are a different layer."

However, the type-level distinction is not yet formalized in code or
schemas. The build plan (`implementation/PILOT_MODE_BUILD_PLAN.md`
T1.3) should enforce the distinction at the runtime level.

**Status:** RESOLVED (at the documentation level) / OPEN (at the
runtime level) — the canonization package distinguishes the concepts
in prose, but the runtime types are not yet separated. This is a
Priority 1 item (build plan T1.3).

---

## Drift 7 — Pilot names three different layers

**Original state:** The deep-dive review (§9) identifies three
separate concepts that all sit close to the word "pilot":

1. **CommercialPilotTemplate** — the kind of engagement being offered
   (e.g., "AI Training Evaluation Pilot"). Implemented in
   `src/config/pilot_registry.py` as `CommercialPilot` with 12
   templates.
2. **PilotConfiguration** — the selected eval families, population,
   window, reference field, policies, workflow, outcome joins, gates,
   governance settings. Implemented in
   `src/domain/pilot_configuration.py` as `PilotConfiguration`.
3. **PilotRun** — the actual governed engagement (e.g., ACME-001,
   September 1–30, current stage: DIAGNOSE). NOT implemented.

**Current state:** The first two concepts exist. The third
(`PilotRun` / `EnterprisePilot`) is the missing connective tissue.
The build plan (`implementation/PILOT_MODE_BUILD_PLAN.md` T1.1)
proposes adding `PilotId` as a value object and threading it through
`PilotConfiguration` and `PilotService`, but does not yet formalize
the three-layer separation as an architectural decision.

**Contradiction:** The word "pilot" is overloaded across three
layers. Without formal separation, runtime classes and schemas may
conflate them.

**Recommended resolution:** Per the deep-dive review (§9, §10, §11):
lock the names and relationships before new runtime classes are
created. Freeze `PilotConfiguration` as the immutable measurement
contract. Introduce `PilotRun` as a thin control plane object that
references the frozen configuration. Do NOT replace
`PilotConfiguration` with a giant new pilot object.

**Status:** RESOLVED (at the decision level) —
`context/DECISION_LOG.md` records the decision "Upsilon Pilot Mode is
primarily an orchestration/control layer over existing capabilities"
and "Functioning analytical surfaces should be reused rather than
rebuilt." The build plan implements the thin `PilotRun` approach.
However, the three-layer naming is not yet formalized as a canonical
architecture document. See `OPEN_QUESTIONS.md` OQ-012.

---

## Additional contradictions

### C1 — Test count: 676 vs 674 vs 147

**Observation:** The deep-dive review (§5) records "674 passed, 2
skipped." The current platform reports "676 passed" (`pytest tests/
-q`). The MANIFEST.yaml records "total: 147, passing: 147."

**Explanation:** The MANIFEST.yaml is dated 2026-08-17 and reflects
the original build package. The test suite has grown since then. The
deep-dive review was performed on an earlier snapshot. The current
count (676) is authoritative.

**Status:** ACCEPTED — the discrepancy is explained by test suite
growth over time. The MANIFEST.yaml is a historical artifact.

### C2 — Data quality warning count: 1,882 warnings

**Observation:** The runtime data quality summary reports {OK: 50,
WARNING: 1882, BLOCKING: 0}. The deep-dive review (§20) attributes
the warnings to "1,668 missing `source_confidence` values" and "214
impossible-value warnings associated with zero-token days."

**Contradiction:** A flagship demonstration should not require an
operator to dismiss a large unexplained warning count. The data
quality architecture is strong, but the fixture does not showcase it
well.

**Recommended resolution:** Per the deep-dive review (§20, Priority
5): the demo generator should populate structured source confidence
and provenance. It should distinguish legitimate zero-activity days
from truly impossible measurements.

**Status:** OPEN — the fixture provenance has not been cleaned. This
is a Priority 5 item.

### C3 — Workflow fit: 0 supported claims

**Observation:** The runtime workflow fit report produces
`{fit_claim: 0, provisional: 220, insufficient_sample: 130}`. The
deep-dive review (§16) notes "0 fully supported fit claims."

**Contradiction:** Workflow Fit is implemented as an analytical
capability but is not strongly demonstrated by the current fixture.
The system is correctly refusing to turn underpowered evidence into
a supported finding, but this means the commercial proof for
workflow fit is weak.

**Recommended resolution:** Per the deep-dive review (§16): improve
the evidence through greater sample density, longer observation
duration, stronger stage-event coverage, or a better predeclared
experimental structure. Do NOT weaken the evidence threshold.

**Status:** OPEN — the fixture evidence density has not been
improved. This is a Priority 5 item.

### C4 — Success criteria not tiered

**Observation:** The deep-dive review (§19) recommends tiering
success criteria into global pilot criteria, commercial-template
criteria, and customer-defined criteria. The current
`pilot/governance/SUCCESS_CRITERIA.md` defines the criterion
structure and provides examples but does not tier them.

**Contradiction:** The original dossier supplied success criteria at
multiple levels (product criteria, commercial criteria), but the
canonical document does not distinguish these tiers.

**Recommended resolution:** Per the deep-dive review (§19): extract
the original product criteria and commercial criteria into
`SUCCESS_CRITERIA.md` and decide which are global, template-specific,
and customer-specific.

**Status:** OPEN — the tiering has not been done. This is a Priority
1 item. See `OPEN_QUESTIONS.md` OQ-013.

---

## Summary

| Drift/contradiction | Status | Priority |
|---|---|---|
| Drift 1 — Flagship demo changed markets | OPEN | P5 |
| Drift 2 — Report layer outran evidence (12,842 vs 1,668) | OPEN | P0 (urgent) |
| Drift 3 — PDF can bypass runtime truth | OPEN | P0 (urgent) |
| Drift 4 — Archetype labels mix ground truth with inference | OPEN | P1 |
| Drift 5 — Original ontology did not survive (Trans Ladder) | UNRESOLVED | — |
| Drift 6 — Gate means two different things | RESOLVED (docs) / OPEN (runtime) | P1 |
| Drift 7 — Pilot names three different layers | RESOLVED (decision) / OPEN (formalization) | P1 |
| C1 — Test count discrepancy | ACCEPTED | — |
| C2 — Data quality warning count | OPEN | P5 |
| C3 — Workflow fit: 0 supported claims | OPEN | P5 |
| C4 — Success criteria not tiered | OPEN | P1 |

**2 items are P0 (urgent). 4 items are P1. 3 items are P5. 1 is
ACCEPTED. 1 is UNRESOLVED.**

The P0 items (Drift 2 and Drift 3) are reporting integrity problems
that must be resolved before the pilot package can be considered
trustworthy. They are addressed by the reporting integrity
invariants in `REPORTING_INTEGRITY_INVARIANTS.md`.

---

## What this document does NOT do

- Does not define specifications (see `pilot/UPSILON_PILOT_SPEC.md`)
- Does not define gaps (see `pilot/implementation/GAP_REGISTER.md`)
- Does not trace original requirements (see
  `ORIGINAL_DOSSIER_TRACEABILITY.md`)
- Does not catalog proof points (see `PILOT_PROOF_POINTS.md`)
- Does not fabricate original intent (UNRESOLVED items are marked)
