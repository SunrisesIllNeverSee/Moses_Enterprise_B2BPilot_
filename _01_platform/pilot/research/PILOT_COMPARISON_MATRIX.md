# PILOT_COMPARISON_MATRIX.md

> Structural comparison of the Upsilon Enterprise Pilot protocol against
> external pilot/evaluation frameworks.
>
> Purpose: detect structural omissions in the Upsilon pilot protocol by
> comparing its architecture against established frameworks.
>
> This is NOT competitor positioning. It is architectural comparison.

## Comparison frameworks

| Framework | Type | Why included |
|---|---|---|
| A/B testing (standard) | Statistical evaluation | The most common bounded evaluation; baseline for comparison |
| Clinical trial (Phase II) | Medical evaluation | Gold standard for bounded, governed, evidence-backed evaluation |
| Design pilot (HCI) | User experience evaluation | Common in enterprise software; bounded UX evaluation |
| Proof of Concept (PoC) | Enterprise IT evaluation | Common enterprise IT evaluation; bounded capability demonstration |
| Upsilon Enterprise Pilot | AI operating evaluation | The protocol defined in this package |

## Comparison matrix

| Dimension | A/B testing | Clinical trial (Phase II) | Design pilot (HCI) | Proof of Concept (PoC) | Upsilon Enterprise Pilot |
|---|---|---|---|---|---|
| **Scope** | Two variants compared | Drug efficacy + safety | UX hypothesis tested | Technical capability demonstrated | AI operating behavior measured |
| **Duration** | Hours to weeks | Months to years | Weeks | Weeks to months | 30 days (baseline) + 14 days (post) |
| **Users** | Random sample | Patient cohort | User panel | Customer team | Operator cohort (25–100) |
| **Real data** | Yes | Yes | Yes (with consent) | Yes | Yes (with governance gates) |
| **Onboarding** | Random assignment | Enrollment + informed consent | Recruitment + consent | Customer engagement | Charter + governance clearance + identity resolution |
| **Instrumentation** | Event tracking | Clinical measurements | UX telemetry | System monitoring | Provider telemetry (file/API) + observation schema |
| **Success criteria** | Statistical significance | Primary + secondary endpoints | UX metrics + thresholds | Capability demonstrated | Locked before measurement (5 canonical metrics + thresholds) |
| **Milestones** | Pre/post measurement | Enrollment → treatment → follow-up | Design → test → iterate | Setup → demo → evaluate | DEFINE → INSTRUMENT → BASELINE → DIAGNOSE → INTERVENE → VERIFY → READOUT → DECIDE |
| **KPIs** | Conversion rate, lift | Response rate, survival | Task completion, satisfaction | Performance, reliability | Leverage, yield, token_snr, construction, composite |
| **Governance** | IRB (if human subjects) | FDA/EMA + IRB | IRB (if human subjects) | Customer agreement | Purpose limitation + disclosure + consent + bias review + challenge + correction |
| **Intervention** | Treatment variant | Drug dose | UX change | Configuration change | 12-entry catalog (CTX/FRM/MOD/AGT/REV/STD/COA/LRN/STG) |
| **Evidence** | Statistical test | Clinical data + safety profile | UX metrics + qualitative | Demo + performance data | Measurements + diagnoses + verification results + outcome correlations |
| **Readout** | Test results | Clinical study report | UX report | Demo report | Pilot markdown + executive brief + decision report + dashboard |
| **Decision gates** | Stop test | Phase transition (II→III) | Iterate or ship | Adopt or reject | Gate 1 (Launch) + Gate 2 (Health) + Gate 3 (Closure) |
| **Scale decision** | Roll out or not | Phase III or stop | Ship or iterate | Deploy or shelve | STOP / EXTEND / EXPAND / DEPLOY |

## Structural observations

### What Upsilon has that others don't

1. **Canonical metric registry.** Upsilon defines 5 canonical metrics
   (leverage, yield, token_snr, log_leverage, construction) that are
   computed identically across all pilots. Most other frameworks use
   ad-hoc metrics per evaluation.

2. **Developmental doctrine.** Upsilon explicitly labels all outputs as
   DEVELOPMENTAL (not PERSONNEL). No bottom-employee leaderboards, no
   punitive labels. Clinical trials have similar protections (patient
   safety), but enterprise software evaluations typically don't.

3. **ASSOCIATION-only claims.** Upsilon explicitly prohibits causal
   claims. All outcome correlations are ASSOCIATION. Clinical trials
   can establish causation (randomized controlled); A/B tests can
   establish causation (random assignment). Upsilon cannot and does not
   claim to.

4. **Preferred manager objects.** Upsilon surfaces 8 developmental
   objects for manager use (development groups, fastest improvers,
   stalled cohorts, workflow bottlenecks, tool/model fit, training
   candidates, peer support, remeasurement queue). No other framework
   produces this specific set of developmental objects.

5. **Lineage tracking.** Upsilon tracks observation → transformation →
   artifact → outcome lineage. Most other frameworks track only
   input → output.

### What others have that Upsilon is missing

1. **Statistical significance testing.** A/B tests and clinical trials
   use formal statistical tests (t-test, chi-square, survival analysis).
   Upsilon computes deltas and bootstrap CIs but does not perform formal
   hypothesis testing on intervention outcomes.

2. **Random assignment.** Clinical trials and A/B tests use random
   assignment to establish causation. Upsilon does not randomly assign
   interventions — assignments are based on diagnostic hypotheses. This
   is by design (ASSOCIATION-only) but limits causal inference.

3. **Control group.** Clinical trials and A/B tests have control groups.
   Upsilon does not have a control group — all interventions are
   applied to operators who need them. This is by design but limits
   causal inference.

4. **Pre-registration.** Clinical trials pre-register their protocol
   before enrollment. Upsilon's success criteria locking is analogous
   but not yet implemented (GAP-003).

5. **Formal closure decision.** Clinical trials have formal phase
   transitions (II→III or stop). A/B tests have stop/roll-out decisions.
   Upsilon defines STOP/EXTEND/EXPAND/DEPLOY but does not yet implement
   them (GAP-007).

### Structural omissions detected

| Omission | Severity | Other frameworks that have it | Upsilon gap |
|---|---|---|---|
| No formal statistical significance testing | Medium | A/B testing, clinical trial | Not in scope (ASSOCIATION-only by design) but could strengthen verification |
| No random assignment | Low | A/B testing, clinical trial | By design (diagnostic-driven, not random) |
| No control group | Low | A/B testing, clinical trial | By design (all operators who need interventions get them) |
| No pre-registration of protocol | High | Clinical trial | GAP-003 (success criteria locking) — being addressed in T1.2 |
| No formal closure decision | High | Clinical trial, A/B testing | GAP-007 (decision record) — being addressed in T1.4 |
| No formal phase transition | Medium | Clinical trial | GAP-008 (state machine) — being addressed in T1.5 |
| No adverse event reporting | Medium | Clinical trial | Negative outcomes are representable (NEGATIVE) but no formal adverse event reporting workflow |

## Conclusion

The Upsilon Enterprise Pilot protocol is structurally sound. Its
lifecycle (DEFINE → INSTRUMENT → BASELINE → DIAGNOSE → INTERVENE →
VERIFY → READOUT → DECIDE) covers the same stages as established
evaluation frameworks. Its governance model (charter, success criteria,
gates, closure outcomes) is analogous to clinical trial governance.

The main structural omissions are:
1. **Success criteria locking** (analogous to pre-registration) — being
   addressed in T1.2
2. **Formal closure decision** (analogous to phase transition) — being
   addressed in T1.4
3. **Pilot state machine** (analogous to phase tracking) — being
   addressed in T1.5

These are all CANON gaps — they require specification and binding, not
new analytical capability. The platform's measurement, diagnostic,
intervention, and verification capabilities are comparable to or
stronger than other frameworks.

The intentional omissions (no random assignment, no control group, no
causal claims) are by design — Upsilon is an observational evaluation,
not a randomized controlled trial. This is appropriate for its purpose
(measuring real AI operating behavior, not establishing causation).
