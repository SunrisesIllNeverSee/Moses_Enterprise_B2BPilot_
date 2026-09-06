# IMPLEMENTATION_REVIEW_MEMO.md

> Final review memo for the `pilot/` canonization package.
>
> This memo addresses the eight required sections (A–H) from the
> original prompt.

## A. What Upsilon already has

Upsilon has a materially implemented measurement, diagnosis, intervention,
verification, and reporting platform. The core capability is strong:

1. **Measurement engine** (`src/metrics/`): 5 canonical metrics
   (leverage, yield, token_snr, log_leverage, construction) computed
   from observations. Registry v0.2. 676 passing tests.

2. **Ingestion** (`src/ingest/`): 11 adapters (fixture, claude, codex,
   github, api-claude, api-codex, api-groq). Full canonical ingest
   emits Observation + System + Session + Task + Artifact + Lineage.

3. **Analysis** (`src/analysis/`): 16 modules covering divergence,
   percentiles, distributions, eligibility, data quality, verifier,
   replication, org topology, similarity, context architecture,
   longitudinal, team composition, dependency risk, learning curve,
   operator-system decomposition, outcome correlation.

4. **Diagnostics** (`src/diagnostics/`): 6 pattern detectors, hypothesis
   generation with evidence + alternatives. All HYPOTHESIS status.

5. **Interventions** (`src/interventions/`): 12-entry catalog, pattern→
   intervention mapping, assignment with authorization enforcement.

6. **Verification** (`src/analysis/verifier.py`): Pre/post deltas, target
   + non-target metrics, outcome correlations, ASSOCIATION-only.

7. **Reporting** (`src/reporting/`): 6 modules — pilot markdown, executive
   brief, decision report, dashboard, PDF, exporters.

8. **Governance** (`src/governance/`): Purpose limitation, disclosure,
   consent, bias review, challenge, correction. Decision-use labels
   (DEVELOPMENTAL, ASSOCIATION, HYPOTHESIS).

9. **Service layer** (`src/service.py`): `PilotService` — shared service
   for CLI, TUI, MCP. 50+ public methods.

10. **Interface surfaces**: CLI (17 command groups), TUI (12 screens),
    MCP (27 tools + 6 resources).

Evidence: `EXISTING_SURFACE_MAP.md`, `PILOT_CAPABILITY_MAP.md`, runtime
validation (2026-09-06), 676 passing tests.

## B. What existed but was not recognized as part of the pilot

Several existing capabilities were not previously framed as pilot
lifecycle components:

1. **PilotConfiguration** (`src/domain/pilot_configuration.py`): A
   complete pilot configuration object with eval families, cohort,
   gates, outcome join, governance, and reference population sections.
   This is the raw material for a Pilot Charter — it was not recognized
   as such.

2. **Commercial pilot registry** (`src/config/pilot_registry.py`): 12
   commercial pilot templates with questions, best buyers, eval families,
   and deployment levels. These are pilot archetypes — they were not
   recognized as charter templates.

3. **Eval registry** (`src/config/eval_registry.py`): 15 eval families
   with implementation status and service method mappings. These define
   which analytical capabilities are active in a pilot — they were not
   recognized as pilot scope selectors.

4. **Production gates** (`src/domain/production_gate.py`): 3 operator-
   level gate rules. These are workflow routing gates — they were not
   distinguished from pilot-level decision gates.

5. **Preferred manager objects** (`src/governance/manager_objects.py`):
   8 developmental objects. These are pilot readout components — they
   were not recognized as part of the READOUT stage.

6. **Decision report** (`src/reporting/decision_report.py`): Translates
   measurement vocabulary to decision vocabulary. This is a READOUT
   component — it was not recognized as part of the pilot lifecycle.

7. **Replication engine** (`src/analysis/replication.py`): Tests
   descriptive stability across splits. This is a VERIFY component —
   it was not integrated into the standard verification flow.

8. **Outcome correlation** (`src/analysis/outcome_correlation.py`):
   Connects lineage to outcomes. This is a VERIFY/READOUT component —
   it was not framed as part of the pilot lifecycle.

9. **SQLiteRepository** (`src/repository/sqlite_repository.py`):
   Persistent storage. This is the foundation for pilot state
   persistence — it was not used for pilot governance objects.

10. **OperatorIdentity** (`src/domain/operator_identity.py`): Cross-
    system identity resolution with conflict detection. This is an
    INSTRUMENT component — it was not recognized as part of the pilot
    lifecycle.

## C. What is missing only as canon/governance

These items require specification and binding, not new analytical
capability:

1. **Pilot identity** (`pilot_id`): A string field that binds a pilot
   to its charter, state, evidence, and decisions. No new capability —
   just an ID field threaded through existing structures.

2. **Success criteria schema**: A dataclass with criterion list,
   threshold, direction, aggregation. No new analytical capability —
   uses existing metric computations for evaluation.

3. **Success criteria locking**: A `locked_at`/`locked_by` field and a
   `lock_success_criteria()` method. No new capability — just a
   freeze mechanism.

4. **Gate records**: A dataclass with gate_type, outcome, conditions,
   criteria_evaluation. Gate 3 reuses `evaluate_success_criteria()`.
   No new analytical capability.

5. **Decision record**: A dataclass with closure_outcome, rationale,
   evidence_cited. No new capability — just a record.

6. **Pilot state machine**: An enum and transition rules. No new
   capability — just state tracking.

7. **Pilot charter**: A formal document binding identity, scope,
   objectives, success criteria, governance. No new capability — just
   a structured definition.

8. **Closure outcomes** (STOP/EXTEND/EXPAND/DEPLOY): Four enum values
   with documentation. No new capability — just a decision vocabulary.

9. **Enterprise name field**: A string field. No new capability.

10. **Selection criteria field**: A string field. No new capability.

## D. What requires small integration work

These items require wiring existing capabilities into the pilot
lifecycle:

1. **CLI/TUI/MCP surfaces for governance objects**: New commands/screens/
   tools for charter creation, criteria locking, gate evaluation,
   decision recording. The patterns exist — just new endpoints.

2. **Replication integration**: `ReplicationEngine` exists but is not
   run as part of standard verification. Add `replicate_key_findings()`
   to the VERIFY stage.

3. **authorized_by on Intervention domain object**: CLI/MCP enforces it,
   but the domain object doesn't have the field. Add it to the dataclass.

4. **claim_type field on findings**: ASSOCIATION is hardcoded in
   governance. Make it an explicit field on findings.

5. **finding_id on DetectedPattern**: `Diagnosis` has `diagnosis_id` but
   `DetectedPattern` does not have an explicit ID. Add one.

6. **Immutable baseline snapshot**: Baseline is recomputed each time.
   Add a timestamped snapshot mechanism.

7. **End date on Intervention**: Computed (start_date + followup_days)
   but not stored. Add it to the dataclass.

## E. What is genuinely missing

These items have no existing implementation to build on:

1. **Decision record**: No `DecisionRecord` schema, no closure outcome
   enum, no `create_decision_record()` method. Must be built from
   scratch. (Small — dataclass + validation.)

2. **Multi-pilot management**: One pilot per `PilotService` instance.
   No pilot registry, no pilot archive. Must be built from scratch.
   (Medium — architecture change.)

3. **Access control for governance actions**: No role system. Must be
   built from scratch. (Medium — new role system.)

4. **Pilot archive + institutional memory**: No archive for terminated
   pilots, no cross-pilot findings database. Must be built from scratch.
   (Medium — new archive + database.)

> Note: Even these "genuinely missing" items are straightforward to
> implement. They do not require new analytical capability — they are
> governance infrastructure.

## F. ACME-001 completion status

| Stage | Status | Evidence |
|---|---|---|
| DEFINE (Charter) | PARTIAL | Charter fields exist in PilotConfiguration but no formal charter with locked success criteria |
| INSTRUMENT (Readiness) | COMPLETE | 1,668 observations ingested, validated, governance-checked (bypassed for demo) |
| BASELINE (Snapshot) | COMPLETE | 50 operators scored, percentiles computed, distributions computed |
| DIAGNOSE (Findings) | COMPLETE | 56 patterns, 56 diagnoses, divergence, workflow fit, topology, benchmarks |
| INTERVENE (Interventions) | COMPLETE | 12 interventions with declared targets, diverse outcomes (5 SUCCESS, 2 PARTIAL, 2 NO_EFFECT, 3 NEGATIVE) |
| VERIFY (Verification) | COMPLETE | 12 verification results with target + non-target deltas, outcome correlations |
| READOUT (Readout) | COMPLETE | Markdown readout, executive brief, decision report, dashboard, preferred manager objects |
| DECIDE (Decision) | CANNOT COMPLETE | No closure decision capability exists. No Gate 3. No STOP/EXTEND/EXPAND/DEPLOY. |

**ACME-001 can complete DEFINE through READOUT** (7 of 8 stages) with
real computed evidence. It **cannot complete DECIDE** because the
platform has no closure decision capability.

The ACME-001 reference pilot exposes this gap rather than concealing it.
The illustrative Gate 3 and Decision Record documents show what the
closure would look like if the capability existed, while clearly
labeling them as illustrative.

## G. First-real-customer blockers

Only blockers that would prevent a legitimate enterprise pilot:

| Blocker | Gap ID | Why it blocks | Build plan item |
|---|---|---|---|
| No locked success criteria | GAP-003 | Without locked criteria, Gate 3 cannot evaluate. No valid closure decision possible. | T1.2 |
| No Gate 3 (Closure / Scale) | GAP-006 | Without Gate 3, the pilot cannot terminate in a decision. | T1.3 |
| No decision record | GAP-007 | Without a decision record, the closure decision is not documented or immutable. | T1.4 |
| No pilot identity | GAP-001 | Without pilot_id, evidence cannot be bound to a specific pilot. | T1.1 |
| No pilot state machine | GAP-008 | Without state tracking, the pilot cannot enforce stage transitions or prevent skipping. | T1.5 |
| Synthetic reference field | GAP-012 | Without an external reference, benchmarking is self-referential. Percentile ranks are inflated. | T2.1 |
| Governance gates bypassed | GAP-013 | Without real governance enforcement, real customer data could be ingested without consent. | T2.2 |
| No persistent pilot state | GAP-014 | Without persistence, pilot state is lost on restart. Governance objects are not auditable. | T2.3 |
| API ingestion untested | GAP-016 | Without tested API ingestion, real provider telemetry may fail. | T2.5 |

> **9 blockers** prevent the first real customer pilot. 5 are T1 gaps
> (2 CANON, 2 GOVERNANCE, 1 RUNTIME — T1.1–T1.5) addressable in the T1
> maturity target. 4 are T2 gaps (1 DATA, 1 PRIVACY, 1 RUNTIME, 1
> PRODUCTION_HARDENING — T2.1, T2.2, T2.3, T2.5) addressable in the T2
> maturity target.

## H. Recommended implementation order

```text
Phase 1 — T1: ACME reference completion (CANON/GOVERNANCE/RUNTIME/UX/EVIDENCE gaps)
  1. T1.1 Pilot identity binding        [small]
  2. T1.2 Success criteria schema + locking  [medium]
  3. T1.3 Gate records                  [medium, depends on T1.2]
  4. T1.4 Decision record               [small, depends on T1.3]
  5. T1.5 Pilot state machine           [small]
  6. T1.6 CLI/TUI/MCP surfaces          [medium, depends on T1.1–T1.5]

  → ACME-001 can complete full lifecycle including DECIDE

Phase 2 — T2: First real customer pilot (DATA/PRIVACY/PRODUCTION_HARDENING/CUSTOMER_ONBOARDING gaps)
  7. T2.1 Real external reference field       [medium-high]
  8. T2.2 Real governance gate enforcement    [medium]
  9. T2.3 Persistent pilot state              [medium]
  10. T2.5 Real provider API ingestion        [medium]
  11. T2.4 Cross-system identity resolution   [small-medium]
  12. T2.6 Replication workflow               [small]

  → First real customer pilot possible

Phase 3 — T3: Scalable production deployment
  13. T3.1 Multi-pilot management             [medium]
  14. T3.2 Audit trail                        [small]
  15. T3.3 Access control                     [medium]
  16. T3.5 Production transition checklist    [small]
  17. T3.4 Pilot archive + institutional memory  [medium]

  → Scalable production deployment
```

**Rationale for this order:**

1. **T1 first** because CANON/GOVERNANCE/RUNTIME gaps are the cheapest
   to fix (no new analytical capability) and they unblock the ACME
   reference pilot's full lifecycle completion.

2. **T2 second** because DATA/PRIVACY/PRODUCTION_HARDENING gaps require
   real data and real APIs. They depend on T1 being complete (governance
   objects must exist before they can be persisted and enforced).

3. **T3 last** because scalability requires both T1 (governance objects)
   and T2 (persistence, real data) to be complete.

## Summary

The `pilot/` package is a canonization artifact, not a feature build.
It defines the canonical Upsilon Enterprise Pilot protocol, maps
existing platform capabilities into that protocol, identifies gaps
(mostly CANON/GOVERNANCE/EVIDENCE, not genuinely missing), and provides
a build plan separated into three maturity targets.

The platform's measurement, diagnostic, intervention, verification, and
reporting capabilities are strong (scores 4–5 on 18 of 26 requirements).
The gaps are in the governance layer (pilot identity, success criteria,
gates, decisions, state machine) — items that require specification and
binding, not new analytical capability.

The ACME-001 reference pilot demonstrates that the platform can complete
7 of 8 lifecycle stages with real computed evidence. The 8th stage
(DECIDE) cannot be completed because the closure decision capability
does not exist — but this is addressable in the T1 maturity target with
~6 small-medium implementation items.

**No runtime files were modified.** This package is documentation-only.
All metric definitions, scoring formulas, intervention catalog entries,
governance labels, and synthetic data are preserved unchanged. The
676-test suite continues to pass.

The package is ready for review.
