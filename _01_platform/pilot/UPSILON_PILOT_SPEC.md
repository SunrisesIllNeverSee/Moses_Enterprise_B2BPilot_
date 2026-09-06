# UPSILON_PILOT_SPEC.md

> The canonical definition of an Upsilon Enterprise Pilot.

## Definition

An Upsilon Enterprise Pilot is a bounded, instrumented evaluation of how
a real organization operates AI, establishing a measurable baseline,
identifying actionable operating differences, applying controlled
interventions where appropriate, verifying resulting changes, and
terminating in an evidence-backed decision to stop, extend, expand, or
deploy.

## Required properties

Every Upsilon Enterprise Pilot MUST have:

1. **Bounded population.** A fixed, named operator set (25–100
   operators) with explicit selection criteria.

2. **Bounded duration.** An explicit start date and end date. No
   indefinite pilots.

3. **Locked success criteria.** Measurable criteria defined and locked
   BEFORE any measurement. Criteria cannot be amended after launch.

4. **Canonical measurement.** The 5 canonical metrics (leverage, yield,
   token_snr, log_leverage, construction) computed identically across
   all pilots. Metric definitions are NOT configurable.

5. **Diagnostic hypotheses.** Pattern detection and diagnosis generation
   produce HYPOTHESIS-status findings. Never CONFIRMED. Never causal.

6. **Controlled interventions.** Interventions from the 12-entry catalog
   with pre-declared target_metric and followup_days. Authorized before
   execution.

7. **Pre/post verification.** Target and non-target metric deltas
   computed between baseline and follow-up windows. All claims are
   ASSOCIATION, never CAUSATION.

8. **Evidence-backed readout.** Synthesized readout with decision
   vocabulary translation, preferred manager objects, and evidence-vs-
   criteria comparison.

9. **Terminal decision.** Gate 3 evaluation produces STOP, EXTEND,
   EXPAND, or DEPLOY. No pilot continues without a closure decision.

10. **Governance compliance.** Purpose limitation, employee disclosure,
    consent, bias review, right to challenge, and correction process
    enforced. All outputs labeled DEVELOPMENTAL (never PERSONNEL).

## Prohibited properties

An Upsilon Enterprise Pilot MUST NOT:

1. **Continue indefinitely.** Every pilot has a closure date. If the
   closure date is reached without a decision, the default is STOP.

2. **Make causal claims.** All outcome correlations are ASSOCIATION.
   Causation is not claimed, implied, or supported.

3. **Evaluate personnel.** All outputs are DEVELOPMENTAL. No personnel
   evaluations, no punitive labels, no bottom-employee leaderboards.

4. **Redefine metrics.** The 5 canonical metrics and their formulas are
   fixed. Pilots do not modify metric definitions.

5. **Skip stages.** The eight-stage lifecycle is sequential. No stage
   may be skipped.

6. **Amend success criteria after measurement.** Criteria are locked
   before measurement. If criteria are wrong, the pilot must be STOPPED
   and a new pilot chartered.

7. **Make decisions without evidence.** The closure decision must cite
   specific evidence artifacts (findings, verification results, readout
   sections).

8. **Extend without requirements.** An EXTEND outcome must include
   explicit reason, missing evidence, new evidence requirement,
   extension period, and new closure date. No indefinite extension.

## Relationship to existing platform

| Spec property | Existing implementation | Status |
|---|---|---|
| Bounded population | `Cohort.operator_ids`, `CohortConfig.min/max_operators` | Existing |
| Bounded duration | `Cohort.window_start/end`, `CohortConfig.window_days` | Existing |
| Locked success criteria | — | MISSING (GAP-002, GAP-003) |
| Canonical measurement | `ScoringEngine`, `MetricRegistry` (v0.2, 5 metrics) | Existing |
| Diagnostic hypotheses | `PatternEngine`, `DiagnosisEngine` (HYPOTHESIS status) | Existing |
| Controlled interventions | `InterventionRegistry` (12 entries), `InterventionManager` | Existing |
| Pre/post verification | `PrePostVerifier`, ASSOCIATION enforced | Existing |
| Evidence-backed readout | `export_pilot_markdown()`, `export_executive_brief()`, `decision_report()` | Existing |
| Terminal decision | — | MISSING (GAP-007) |
| Governance compliance | `GovernanceEnforcement`, `DecisionUse` labels | Existing (bypassed in demo) |

## Canonical metrics (preserved)

The 5 canonical metrics are defined in `src/metrics/registry.py` and
`demo_data/metric_registry.json` (v0.2). They are NOT redefined here.
They are NOT configurable. They are:

| Metric | Formula | Status |
|---|---|---|
| leverage | R/I | CANONICAL |
| yield | (R×O)/(I²) | CANONICAL |
| token_snr | O/(I+O) | CANONICAL_WITH_INTERPRETATION_LIMIT |
| log_leverage | log10(R/I) | CANONICAL |
| construction | W/R | CANONICAL_WITH_INTERPRETATION_LIMIT |

Where:
- I = input tokens
- O = output tokens
- R = reused context tokens
- W = written (generated) tokens

> These formulas are preserved from the existing implementation. This
> spec does NOT redefine them. Any conflict between this spec and
> `src/metrics/registry.py` should be resolved in favor of the existing
> implementation.

## Intervention catalog (preserved)

The 12-entry intervention catalog is defined in
`src/interventions/registry.py`. It is NOT redefined here. It is NOT
configurable. The entries are:

CTX-001, CTX-002, CTX-003, FRM-001, FRM-002, MOD-001, AGT-001, REV-001,
STD-001, COA-001, LRN-001, STG-001

> This catalog is preserved from the existing implementation. This
> spec does NOT redefine it.

## Authority

This specification is the controlling definition for what constitutes
an Upsilon Enterprise Pilot. It supersedes any conflicting documentation
in the repository regarding pilot definition, lifecycle, or governance.

It does NOT supersede:
- `src/metrics/registry.py` (metric definitions)
- `src/interventions/registry.py` (intervention catalog)
- `src/governance/decision_use.py` (decision-use labels)
- `src/governance/enforcement.py` (governance enforcement)
- Any existing domain object definitions in `src/domain/`

If a conflict is found between this spec and an existing implementation,
the conflict must be documented before the spec or implementation is
changed.
