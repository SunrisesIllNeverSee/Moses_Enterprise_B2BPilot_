# REPORTING_INTEGRITY_INVARIANTS.md

> The 12 reporting integrity invariants from the deep-dive review
> (§18), with traceability to canonical status.
>
> This document is NON-CANONICAL. It records the invariants
> recommended by the deep-dive review and maps each to its current
> canonical status. Invariants that are already canonical are marked;
> invariants that are proposed but not yet canonical are marked as
> PROPOSED.
>
> These invariants are more important than adding another evaluation
> family. They protect the integrity of every customer-facing output.

## Purpose

The deep-dive review
(`review/UPSILON_ORIGINAL_TO_CURRENT_DEEP_DIVE_REVIEW.md` §18)
identifies 12 reporting integrity invariants that "should become
non-negotiable requirements for Pilot v1." This document preserves
those invariants, traces each to its current canonical status, and
identifies which are already enforced vs which are proposed additions.

## Canonical status classifications

| Status | Meaning |
|---|---|
| **CANONICAL** | The invariant is already enforced or stated in a canonical document. |
| **CANONICAL (PARTIAL)** | The invariant is partially stated in canonical documents but not fully enforced. |
| **PROPOSED** | The invariant is recommended by the deep-dive review but not yet canonical. |

---

## The 12 invariants

### INV-1 — Every number in a pilot readout must originate from canonical pilot evidence or canonical pilot state

**Invariant:** No number in any customer-facing output may be
fabricated, hand-edited, or sourced from a stale static artifact. Every
quantitative claim must trace to a canonical measurement, computation,
or governance state.

**Current evidence:**
- `src/reporting/exporters.py`: `export_pilot_markdown(svc)` generates
  from runtime `PilotService` data.
- `pilot/UPSILON_PILOT_SPEC.md`: required property #8 (evidence-backed
  readout).
- **VIOLATED** by `demo_data/graphics/g09_sample_customer_report.md`
  which claims 12,842 observations vs the runtime 1,668. See
  `DRIFT_AND_CONTRADICTIONS.md` Drift 2.

**Status:** CANONICAL (PARTIAL) — the principle is stated in the spec
but the static report violates it.

---

### INV-2 — All presentation formats must derive from one report model

**Invariant:**

```text
Pilot evidence and state
        ↓
   Report model
    ├── Markdown
    ├── HTML
    └── PDF
```

No presentation format may have an independent source. Markdown, HTML,
and PDF must all render from the same canonical report model.

**Current evidence:**
- `src/reporting/exporters.py`: runtime Markdown from `PilotService`.
- `src/reporting/pdf.py`: `render_sample_report_pdf()` renders from
  static `g09_sample_customer_report.md`, NOT from the runtime report
  model.
- **VIOLATED** — the PDF path has an independent source. See
  `DRIFT_AND_CONTRADICTIONS.md` Drift 3.

**Status:** PROPOSED — the one-report-model principle is not stated
in any canonical document. The current implementation violates it.

---

### INV-3 — A handwritten or static sample report must never be an independent source for a customer-facing PDF

**Invariant:** Static sample reports may exist for documentation or
historical reference, but they must never be rendered to PDF as though
they were runtime evidence.

**Current evidence:**
- `src/reporting/pdf.py` lines 215-233: `render_sample_report_pdf()`
  defaults to `demo_data/graphics/g09_sample_customer_report.md` as
  the source.
- CLI `enterprise export dashboard` calls
  `render_sample_report_pdf()` with the static path.
- **VIOLATED** — the static report is the default PDF source.

**Status:** PROPOSED — this invariant is not stated in any canonical
document. The current implementation violates it.

---

### INV-4 — Fixture ground truth must be labeled separately from Upsilon inference

**Invariant:** Synthetic fixture metadata (e.g., `pattern_demo`
archetype labels) must be visibly distinguished from analytical
outputs inferred by the platform. Outputs that use fixture ground
truth must carry a label such as "FIXTURE GROUND TRUTH — not inferred
by Upsilon."

**Current evidence:**
- `src/domain/operator.py` line 27: `pattern_demo: Optional[str] =
  None  # archetype label (demo only)`.
- `src/analysis/team_composition.py`: uses `pattern_demo` for
  archetype coverage without distinguishing ground truth from
  inference in the output.
- `pilot/UPSILON_PILOT_SPEC.md`: does not address fixture-vs-inference
  labeling.

**Status:** PROPOSED — the distinction is in the source code comment
but not in canonical documents or output labeling. See
`DRIFT_AND_CONTRADICTIONS.md` Drift 4.

---

### INV-5 — Observational association must never be presented as causal proof

**Invariant:** All outcome correlations are ASSOCIATION. Causation is
not claimed, implied, or supported. No presentation format may
represent observational association as causal proof.

**Current evidence:**
- `pilot/UPSILON_PILOT_SPEC.md`: prohibited property #2 ("no causal
  claims").
- `src/outcomes/governance.py`: enforces ASSOCIATION-only.
- `src/analysis/outcome_correlation.py`: `EvidenceGrade.OBSERVATIONAL`,
  ASSOCIATION claims.
- `pilot/governance/SUCCESS_CRITERIA.md`: criteria measure operating
  behavior, not causal proof.

**Status:** CANONICAL — already enforced in spec, governance, and
code.

---

### INV-6 — Unresolved metrics must remain unresolved unless the measurement authority explicitly canonizes them

**Invariant:** Metrics marked NEEDS_CANONICAL_LOCK (velocity,
compression_operating_ratio, stability) must not be silently
redefined or treated as canonical. The pilot package must not create
substitute formulas.

**Current evidence:**
- `schemas/metric_registry.json`: 3 metrics with status
  `NEEDS_CANONICAL_LOCK`.
- `pilot/UPSILON_PILOT_SPEC.md`: required property #4 (5 canonical
  metrics, NOT configurable); canonical metrics table lists only the 5
  CANONICAL metrics.
- `pilot/context/ORIGIN_AND_RATIONALE.md`: notes the unresolved status
  is "healthier than false precision."

**Status:** CANONICAL — the spec preserves the 5 canonical metrics and
does not redefine the 3 unresolved ones.

---

### INV-7 — A baseline must be frozen and referenced before an intervention can claim pre/post change

**Invariant:** The baseline snapshot must be immutable. Pre/post
verification must reference the frozen baseline, not a recomputed
snapshot. No intervention outcome may claim change without a frozen
baseline reference.

**Current evidence:**
- `pilot/UPSILON_PILOT_SPEC.md`: required property #7 (pre/post
  verification between baseline and follow-up windows).
- `src/analysis/verifier.py`: `PrePostVerifier` computes deltas
  between baseline and follow-up.
- `pilot/operations/FIRST_CUSTOMER_READINESS.md` M9: "Save baseline
  output to a timestamped file. Do not recompute after saving."
- **GAP** — `pilot/operations/PILOT_RUNBOOK.md` notes: "No immutable
  baseline snapshot mechanism. The baseline is recomputed each
  `PilotService` instantiation."

**Status:** CANONICAL (PARTIAL) — the principle is stated in the spec
and operations docs, but the runtime does not enforce baseline
freezing. See `implementation/GAP_REGISTER.md` and
`FIRST_CUSTOMER_READINESS.md` M9.

---

### INV-8 — Every intervention must identify its hypothesis, target, authorization, evidence window, verification result, and evidence references

**Invariant:** No intervention may exist without: a diagnostic
hypothesis, a pre-declared target metric, authorization
(`authorized_by`), a defined evidence window (follow-up days), a
verification result, and evidence references.

**Current evidence:**
- `pilot/UPSILON_PILOT_SPEC.md`: required property #6 (controlled
  interventions with pre-declared `target_metric` and
  `followup_days`, authorized before execution).
- `src/interventions/manager.py`: `assign()` requires `catalog_id`,
  `target_metric`, `followup_days`.
- CLI/MCP: `--authorized-by` is required for assignment.
- `pilot/operations/INTERVENTION_RUNBOOK.md`: documents the full
  intervention record fields.
- **GAP** — `authorized_by` is enforced in CLI/MCP but not on the
  `Intervention` domain object itself. See
  `FIRST_CUSTOMER_READINESS.md` M10.

**Status:** CANONICAL (PARTIAL) — most fields are enforced; the
hypothesis link and `authorized_by` on the domain object are gaps.

---

### INV-9 — The launch configuration must be immutable or versioned; material mid-pilot changes must be recorded, not silently applied

**Invariant:** `PilotConfiguration` is the measurement contract. Once
locked, it must not change silently. Material changes must be recorded
as versioned amendments with timestamps and rationale.

**Current evidence:**
- `pilot/UPSILON_PILOT_SPEC.md`: required property #3 (locked success
  criteria, cannot be amended after launch); prohibited property #6
  (no amending success criteria after measurement).
- `src/domain/pilot_configuration.py`: `PilotConfiguration` exists
  but has no `locked` flag, version field, or amendment tracking.
- `pilot/operations/PILOT_LAUNCH_CHECKLIST.md`: requires
  configuration validation and saving.
- **GAP** — the configuration is not frozen or versioned at runtime.

**Status:** CANONICAL (PARTIAL) — the principle is stated for success
criteria but not for the full configuration. Runtime freezing is not
implemented. See `implementation/PILOT_MODE_BUILD_PLAN.md` T1.1, T1.2.

---

### INV-10 — Measurement gates and pilot decision gates must remain distinct types

**Invariant:** Operator-level routing gates (GATE-001/002/003 in
`src/domain/production_gate.py`) and pilot-level decision gates (Gate
1/2/3 in `pilot/governance/DECISION_GATES.md`) are different concepts.
They must not share the same type, model, or enforcement path.

**Current evidence:**
- `pilot/governance/DECISION_GATES.md`: explicitly states "These are
  operator-level routing gates... The three pilot-level decision
  gates defined here are a different layer."
- `src/domain/production_gate.py`: GATE-001/002/003 for operator
  routing.
- **GAP** — the type-level distinction is not yet formalized in code.
  The build plan (T1.3) should enforce it.

**Status:** CANONICAL (PARTIAL) — the distinction is stated in
canonical documentation but not yet enforced at the runtime type
level. See `DRIFT_AND_CONTRADICTIONS.md` Drift 6.

---

### INV-11 — Synthetic demonstration results must not be represented as customer proof

**Invariant:** Outputs from the synthetic demo fixture must be labeled
as synthetic. No synthetic result may be presented as evidence from a
real customer.

**Current evidence:**
- `demo_data/graphics/g09_sample_customer_report.md`: header states
  "SYNTHETIC PRODUCT FIXTURE — NOT CUSTOMER DATA."
- `_specs/22_SAMPLE_PILOT_READOUT.md`: states "SYNTHETIC PRODUCT
  FIXTURE — NOT CUSTOMER DATA."
- `src/domain/observation.py`: `synthetic` flag on `Observation`.
- `src/metrics/engine.py`: measurements carry `synthetic=True` for
  demo data.
- `pilot/UPSILON_PILOT_SPEC.md`: does not explicitly state this
  invariant.
- `pilot/examples/ACME-001/README.md`: states "All data is
  SYNTHETIC."

**Status:** CANONICAL (PARTIAL) — the synthetic label is present in
demo data and some specs, but the invariant is not stated as a
canonical rule in `UPSILON_PILOT_SPEC.md`.

---

### INV-12 — A pilot must terminate in an explicit decision: STOP, EXTEND, EXPAND, or DEPLOY

**Invariant:** No pilot may continue indefinitely. Every pilot must
reach Gate 3 and produce one of the four closure outcomes. If the
closure date is reached without a decision, the default is STOP.

**Current evidence:**
- `pilot/UPSILON_PILOT_SPEC.md`: required property #9 (terminal
  decision); prohibited property #1 (no indefinite pilots).
- `pilot/governance/CLOSURE_OUTCOMES.md`: four closure outcomes with
  "no indefinite pilot state" rule.
- `pilot/governance/PILOT_STATE_MACHINE.md`: TERMINATED is the
  terminal state.
- `pilot/governance/DECISION_GATES.md`: Gate 3 evaluates and selects
  outcome.
- **GAP** — Gate 3 evaluation and DecisionRecord are not yet
  implemented as runtime objects.

**Status:** CANONICAL — the invariant is fully stated in canonical
documents. Runtime enforcement is a build plan item (T1.3, T1.4).

---

## Summary

| Invariant | Status | Enforced? |
|---|---|---|
| INV-1 — Numbers from canonical evidence | CANONICAL (PARTIAL) | No (static report violates) |
| INV-2 — One report model | PROPOSED | No (PDF has independent source) |
| INV-3 — No static report to PDF | PROPOSED | No (violated by `pdf.py`) |
| INV-4 — Fixture ground truth labeled | PROPOSED | No (not in outputs) |
| INV-5 — Association never causation | CANONICAL | Yes |
| INV-6 — Unresolved metrics stay unresolved | CANONICAL | Yes |
| INV-7 — Baseline frozen before pre/post | CANONICAL (PARTIAL) | No (runtime gap) |
| INV-8 — Intervention identification | CANONICAL (PARTIAL) | Mostly (domain object gap) |
| INV-9 — Configuration immutable/versioned | CANONICAL (PARTIAL) | No (runtime gap) |
| INV-10 — Gate types distinct | CANONICAL (PARTIAL) | Docs yes, runtime no |
| INV-11 — Synthetic not customer proof | CANONICAL (PARTIAL) | Mostly (not in spec) |
| INV-12 — Terminal decision | CANONICAL | Yes (spec), No (runtime) |

**4 invariants are CANONICAL. 5 are CANONICAL (PARTIAL). 3 are
PROPOSED.**

The 3 PROPOSED invariants (INV-2, INV-3, INV-4) and the PARTIAL
invariants that are violated in practice (INV-1, INV-7, INV-9) are
the most urgent to address. INV-2 and INV-3 are P0 per the deep-dive
review because they affect reporting integrity.

---

## Recommended actions

### P0 — Urgent (reporting integrity)

1. **Promote INV-2 and INV-3 to canonical.** Add the one-report-model
   principle and the no-static-report-to-PDF rule to
   `pilot/UPSILON_PILOT_SPEC.md` or a new
   `pilot/governance/REPORTING_INTEGRITY.md`.
2. **Remove the PDF bypass.** Modify `src/reporting/pdf.py` to render
   from the runtime report model, not the static
   `g09_sample_customer_report.md`.
3. **Regenerate the static report.** Either regenerate
   `g09_sample_customer_report.md` from runtime evidence or label it
   as a historical artifact that must not be used for customer-facing
   PDF.

### P1 — Before first pilot

4. **Promote INV-4 to canonical.** Add fixture-ground-truth labeling
   to the spec.
5. **Enforce INV-7.** Implement immutable baseline snapshot (build
   plan T2.1 partial).
6. **Enforce INV-9.** Implement configuration freezing/versioning
   (build plan T1.1, T1.2).
7. **Enforce INV-10.** Formalize gate type separation in runtime
   (build plan T1.3).

### P2 — Before scale

8. **Promote INV-11 to canonical.** Add the synthetic-not-customer
   rule to the spec explicitly.
9. **Enforce INV-12.** Implement Gate 3 evaluation and
   DecisionRecord (build plan T1.3, T1.4).

---

## What this document does NOT do

- Does not define specifications (see `pilot/UPSILON_PILOT_SPEC.md`)
- Does not define the report model (see `src/reporting/exporters.py`)
- Does not define gaps (see `pilot/implementation/GAP_REGISTER.md`)
- Does not catalog drift (see `DRIFT_AND_CONTRADICTIONS.md`)
- Does not modify canonical documents (PROPOSED invariants require
  canonical promotion before they become normative)
