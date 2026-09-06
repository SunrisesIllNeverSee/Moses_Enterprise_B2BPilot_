# OPEN_QUESTIONS.md

> Unresolved design questions for the Upsilon Enterprise Pilot.
>
> This document is NON-CANONICAL. It tracks questions that have not
> been resolved. Resolved questions should be moved to
> `DECISION_LOG.md` with the resolution date.
>
> An open question is NOT a defect — it is a design question where
> the answer is not yet established or where multiple valid answers
> exist.

## How to use this document

1. When a design question arises, add it here with context.
2. When a question is resolved, move it to `DECISION_LOG.md` with
   the resolution date and rationale.
3. Do not leave resolved questions here — they belong in the
   decision log.

## Open questions

### OQ-001 — Composite score weight rationale

**Question:** Why are the composite developmental score weights
0.30/0.30/0.20/0.20 (leverage/yield/token_snr/construction)? Why is
log_leverage excluded from the composite?

**Context:** `src/metrics/composite_score.py` defines
`compute_composite_score()` with these weights. The weights are not
documented in source comments, test names, or spec references.
log_leverage is a canonical metric but is not in the composite.

**Why it matters:** If the weights are arbitrary, they may need
validation. If they are empirical, the validation should be
documented. If log_leverage is excluded for a reason, the reason
should be recorded.

**Status:** UNRESOLVED (see `ORIGIN_AND_RATIONALE.md`)

---

### OQ-002 — Pattern detector threshold rationale

**Question:** What is the rationale for the specific threshold values
in each of the 6 pattern detectors?

**Context:** `src/diagnostics/pattern_engine.py` defines 6 pattern
detectors (P-CTX-01, P-CTX-02, P-BURN-01, P-HIDDEN-01, P-MODEL-01,
P-STAGE-01). Each uses specific threshold values (e.g., leverage
percentile cutoffs for P-CTX-01). The thresholds are in the source
code but their rationale is not documented.

**Why it matters:** If thresholds are too aggressive, too many
operators are flagged. If too conservative, patterns are missed. The
thresholds should be validated against real data (not just the
synthetic demo).

**Status:** UNRESOLVED (see `ORIGIN_AND_RATIONALE.md`)

---

### OQ-003 — External reference field construction

**Question:** How should the external reference field for real
customer pilots be constructed?

**Context:** The current reference field is synthetic (derived from
the acme_50 cohort). For real customers, an external reference is
needed. Options include:
- Aggregated anonymized data across multiple cohorts (with consent)
- Public reference field from a benchmark source
- Role-specific reference fields
- Prior-window reference (operator's own prior performance)

**Why it matters:** Without an external reference, benchmarking
compares operators against themselves. Percentile ranks are
inflated. The benchmark class selection algorithm selects `peer` for
all operators because no prior-window or matched-task data is
available.

**Status:** UNRESOLVED — see `pilot/PILOT_EXTERNAL_BENCHMARKS.md`
for the requirement and `pilot/implementation/PILOT_MODE_BUILD_PLAN.md`
T2.1 for the build plan. The construction method is not yet decided.

---

### OQ-004 — Pilot-level gate enforcement location

**Question:** Should pilot-level gates (Gate 1/2/3) be enforced in
the service layer, the CLI/MCP layer, or a separate governance
service?

**Context:** Operator-level gates are enforced in
`src/governance/enforcement.py` and called from `PilotService`.
Intervention authorization is enforced in the CLI/MCP layer but not
on the `Intervention` domain object. Pilot-level gates do not yet
exist.

**Why it matters:** If gates are enforced only in the CLI/MCP layer,
programmatic users (direct `PilotService` access) can bypass them.
If gates are enforced in the service layer, all access paths are
covered but the service becomes more complex. A separate governance
service adds architectural complexity but provides clean separation.

**Status:** UNRESOLVED — the build plan (T1.3) proposes service-layer
enforcement but this has not been decided.

---

### OQ-005 — State machine transition strictness

**Question:** Should the pilot state machine allow skip transitions
(e.g., DEFINE → BASELINE without INSTRUMENT) for baseline-only
pilots?

**Context:** `pilot/governance/PILOT_STATE_MACHINE.md` says "no
state may be skipped." But baseline-only pilots (Commercial Pilot #1)
do not have an INTERVENE or VERIFY stage. The state machine defines
INTERVENING and VERIFYING as states.

**Why it matters:** If the state machine is too strict, baseline-only
pilots cannot complete a valid lifecycle. If too permissive, the
lifecycle discipline is weakened.

**Status:** UNRESOLVED — the state machine documentation says no
skips, but the interaction with baseline-only pilots is not
specified. The build plan (T1.5) does not address this.

---

### OQ-006 — EXTEND semantics and state transition

**Question:** When EXTEND is selected, does the pilot return to
INSTRUMENTED or BASELINED? Is EXTEND a terminal state or a
transition?

**Context:** `pilot/governance/CLOSURE_OUTCOMES.md` says EXTEND
returns to an active state. `pilot/governance/PILOT_STATE_MACHINE.md`
defines `Gate 3: EXTEND → INSTRUMENTED or BASELINED`. But EXTEND is
also one of the four closure outcomes, which are described as
"terminal."

**Why it matters:** If EXTEND is terminal, the pilot is closed and a
new pilot is chartered. If EXTEND is a transition, the pilot
continues with a new window. The semantics affect whether the
charter is preserved or re-created.

**Status:** PARTIALLY RESOLVED — the package's intent is that EXTEND
is a closure decision that creates an extension phase (the pilot
continues with a new window, charter is preserved, success criteria
are NOT amended). But the state machine and closure outcomes
documents use language that could be read either way. The
documentation should be reconciled.

---

### OQ-007 — Consent model selection for first real pilot

**Question:** Which consent model (opt_in / opt_out / mandated)
should be used for the first real customer pilot?

**Context:** `GovernanceConfig.consent_model` supports all three.
The choice depends on the customer's jurisdiction, employment
context, and AI usage policy. GDPR requires opt_in for employee
monitoring in most cases. US employment law varies by state.

**Why it matters:** The wrong consent model could create legal
exposure for the customer and reputational risk for Upsilon.

**Status:** UNRESOLVED — this is a per-customer decision, not a
platform decision. The platform supports all three models. The
customer's legal counsel should advise.

---

### OQ-008 — API ingestion reliability with real providers

**Question:** Will the API ingestion adapters work reliably with
real provider APIs (Claude, Codex, Groq)?

**Context:** API adapters are in stub mode. They produce
deterministic synthetic data for testing. Live mode requires API
keys and has not been tested with real provider APIs. Potential
issues: rate limits, schema drift, pagination, error handling,
authentication.

**Why it matters:** If API ingestion fails, the pilot cannot
collect telemetry. File export is a fallback but may not be
available for all providers.

**Status:** UNRESOLVED — see `pilot/implementation/HARDENING_PLAN.md`
H4 and `pilot/operations/FIRST_CUSTOMER_READINESS.md` H2.

---

### OQ-009 — Cross-system identity mapping workflow

**Question:** How should cross-system operator identity mapping work
for real customers?

**Context:** `OperatorIdentity` exists with conflict detection but
no real mapping workflow. Real customers have operators across
multiple systems (ChatGPT email, Claude account, GitHub username)
with different identifiers. Options include:
- CSV upload with manual mapping
- API-based mapping (if providers expose identity)
- Manual mapping by the customer

**Why it matters:** Without identity mapping, the same operator
appears as multiple operators, inflating counts and distorting
metrics.

**Status:** UNRESOLVED — see `pilot/implementation/PILOT_MODE_BUILD_PLAN.md`
T2.4.

---

### OQ-010 — ACME-001 as canonical reference vs real-pilot template

**Question:** Should ACME-001 remain the canonical synthetic
reference pilot indefinitely, or should it be superseded by the
first real customer pilot?

**Context:** ACME-001 is the canonical reference implementation
using the synthetic demo. It demonstrates the full lifecycle (with
illustrative gates/decision). When the first real customer pilot
completes, should it become the new canonical reference?

**Why it matters:** ACME-001's value is that it is reproducible
(anyone can run the demo). A real customer pilot cannot be shared
publicly. Both may have value as references.

**Status:** UNRESOLVED — likely both should coexist: ACME-001 as
the synthetic reference, and the first real pilot as the real
reference (anonymized).

---

## Resolved questions

(When a question is resolved, move it here with the resolution date
and rationale, then add it to `DECISION_LOG.md`.)

---

## What this document does NOT do

- Does not define specifications (see `pilot/UPSILON_PILOT_SPEC.md`)
- Does not record decisions (see `DECISION_LOG.md`)
- Does not define gaps (see `pilot/implementation/GAP_REGISTER.md`)
- Does not define the build plan (see
  `pilot/implementation/PILOT_MODE_BUILD_PLAN.md`)
