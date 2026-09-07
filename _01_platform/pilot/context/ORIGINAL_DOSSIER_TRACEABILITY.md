# ORIGINAL_DOSSIER_TRACEABILITY.md

> Requirement-by-requirement map from the August 17 original dossier
> to current code, tests, demo behavior, reports, and operating
> surfaces.
>
> This document is NON-CANONICAL. It traces original intent to current
> implementation. It does NOT override any canonical document.
>
> The "original dossier" refers to the August 17, 2026 SignalAF
> commercial field dossier and the accompanying build-package specs
> (`_specs/00_README.md` through `_specs/23_SAMPLE_OPERATOR_PROFILE.md`,
> `MANIFEST.yaml`). The dossier is not present in the repository as a
> single file; its requirements are distributed across the 24 spec
> documents and the manifest. This traceability map reconstructs
> requirements from those specs and maps each to current evidence.
>
> Where a requirement cannot be traced to a specific spec statement,
> the entry is marked **UNRESOLVED**.

## Method

For each original requirement:
1. The source spec is identified (by spec number and title).
2. The current implementation is located (code, test, demo, report,
   surface, or missing).
3. The traceability status is classified.

### Status classifications

| Status | Meaning |
|---|---|
| **TRACED** | Requirement is implemented and demonstrable. |
| **TRACED (PARTIAL)** | Requirement is implemented but incomplete or under-hardened. |
| **TRACED (SIMULATED)** | Requirement is implemented for synthetic demo only; not production-proven. |
| **NOT TRACED** | Requirement is not implemented or cannot be located. |
| **UNRESOLVED** | Requirement cannot be established from available spec evidence. |

---

## 1. Commercial category — AI Operator Evals

**Source:** `_specs/01_ENTERPRISE_WEBSITE_BUILD_SPEC.md` (product
definition); `_specs/12_PRIVACY_GOVERNANCE_SPEC.md` (development
doctrine).

**Original requirement:** The product category is AI Operator Evals —
evaluating the human-system operating relationship, not generic AI
analytics, employee monitoring, productivity tracking, or model
benchmarking.

**Current evidence:**
- `src/metrics/registry.py`: 5 canonical metrics measure operator
  behavior (leverage, yield, token_snr, log_leverage, construction),
  not raw usage or productivity.
- `src/analysis/divergence.py`: separates usage from operation
  (HIGH_USAGE_LOW_OPERATION vs LOW_USAGE_HIGH_OPERATION).
- `src/governance/enforcement.py`: enforces DEVELOPMENTAL decision-use,
  prohibits PERSONNEL evaluation.
- `pilot/UPSILON_PILOT_SPEC.md`: defines the pilot as an evaluation of
  "how a real organization operates AI."

**Status:** TRACED

---

## 2. Pilot boundary — 25 to 100 operators, ~30 days

**Source:** `_specs/05_PILOT_PHASES_IMPLEMENTATION_PLAN.md` ("25–100
AI users, 30-day baseline cohort"); `_specs/20_PILOT_OPERATING_PLAYBOOK.md`
("identify 25–100 participants").

**Original requirement:** The pilot is bounded around 25–100 active AI
users, approximately 30 days, real AI usage, team and cohort
evaluation, baseline measurement, targeted intervention, remeasurement,
and a buyer-facing outcome and continuation decision.

**Current evidence:**
- `src/domain/pilot_configuration.py`: `CohortConfig(min_operators=25,
  max_operators=100, window_days=30)`.
- `demo_data/cohort.json`: 50 operators, 30-day window
  (2026-07-01 to 2026-07-30).
- `pilot/UPSILON_PILOT_SPEC.md`: required properties #1 (bounded
  population) and #2 (bounded duration).
- `pilot/governance/PILOT_CHARTER.md`: charter requires population and
  duration boundaries.

**Status:** TRACED

---

## 3. Original beachhead — mixed-role workforce

**Source:** The deep-dive review
(`review/UPSILON_ORIGINAL_TO_CURRENT_DEEP_DIVE_REVIEW.md` §2) states
the original dossier "explicitly argued against allowing the flagship
50-person demonstration to become 50 developers." The specific spec
statement could not be located in the available `_specs/` documents.

**Original requirement:** The flagship synthetic enterprise should
represent nontechnical or mixed-role functions (Sales, Marketing,
Operations, Finance, Support, People/Administration), not 50
developers.

**Current evidence:**
- `demo_data/operators.json`: 50 operators with departments dominated
  by Product Engineering (18), Platform/Infrastructure (10),
  Data/Analytics (8), Product/Design (6), Customer Engineering/Support
  (4), Operations/GTM (4).
- `demo_data/workflows.json`: default workflow is `software_dev_v1`
  (Software Development).

**Status:** NOT TRACED — the current fixture is a technical/software
engineering cohort, not a mixed-role commercial beachhead. See
`DRIFT_AND_CONTRADICTIONS.md` Drift 1.

> **UNRESOLVED:** The specific spec statement mandating a mixed-role
> beachhead could not be located in the available `_specs/` documents.
> The deep-dive review asserts this was the original intent. The
> `_specs/02_ENTERPRISE_DEMO_DATA_SPEC.md` describes the demo as
> "Acme AI-Enabled Software Company," which suggests the technical
> shift may have occurred at the spec level, not only in
> implementation. The original SignalAF commercial field dossier
> (referenced as `signalaf_commercial_field_dossier_2026-08-17_v4.zip`
> in the review) is not present in the repository to confirm.

---

## 4. Closed-loop commercial system — baseline to remeasurement

**Source:** `_specs/12_PRIVACY_GOVERNANCE_SPEC.md` ("Commercial loop:
baseline → diagnose → intervene → re-measure → raise the floor");
`_specs/05_PILOT_PHASES_IMPLEMENTATION_PLAN.md` (P0/P1/P2 phases).

**Original requirement:** The product is a closed-loop system:
BASELINE → DIAGNOSE → INTERVENE → REMEASURE → IMPROVE.

**Current evidence:**
- `src/metrics/engine.py`: `score_cohort()` (baseline).
- `src/diagnostics/pattern_engine.py` + `diagnosis_engine.py`
  (diagnose).
- `src/interventions/registry.py` + `manager.py` (intervene).
- `src/analysis/verifier.py`: `PrePostVerifier` (remeasure).
- `src/governance/manager_objects.py`: 8 preferred manager objects
  (improve/raise-the-floor).
- `pilot/PILOT_LIFECYCLE.md`: 8-stage lifecycle
  (DEFINE→INSTRUMENT→BASELINE→DIAGNOSE→INTERVENE→VERIFY→READOUT→DECIDE).

**Status:** TRACED

---

## 5. Development doctrine — raise the floor, not rank for punishment

**Source:** `_specs/12_PRIVACY_GOVERNANCE_SPEC.md` ("Preferred manager
objects" + "avoid-list").

**Original requirement:** The operating doctrine is to raise the floor
rather than rank people for punishment. Manager-facing objects should
include stalled cohorts, fastest improvers, workflow bottlenecks,
training candidates, tool-fit opportunities, development groups,
peer-support matches, and remeasurement queues.

**Current evidence:**
- `src/governance/manager_objects.py`: `preferred_manager_objects()`
  returns 8 objects: development_groups, fastest_improvers,
  stalled_cohorts, workflow_bottlenecks,
  tool_model_fit_opportunities, training_candidates,
  peer_support_matches, remeasurement_queue.
- `src/governance/enforcement.py`: enforces
  `DecisionUse.DEVELOPMENTAL`, prohibits `PERSONNEL`.
- `src/benchmark/engine.py`: `no_false_leaderboards: True`.
- `src/metrics/composite_score.py`: composite is a distribution, not a
  ranking; label is "DEVELOPMENTAL."
- `pilot/UPSILON_PILOT_SPEC.md`: prohibited property #3 (no personnel
  evaluations, no punitive labels, no bottom-employee leaderboards).

**Status:** TRACED

---

## 6. Canonical metrics — 5 frozen metrics

**Source:** `_specs/03_CANONICAL_METRIC_REGISTRY.md`;
`schemas/metric_registry.json` (registry v0.2).

**Original requirement:** Canonical metrics for leverage, yield,
token_snr, log_leverage (10xDEV), and construction. Unresolved metrics
(velocity, compression_operating_ratio, stability) should not be
falsely canonized.

**Current evidence:**
- `schemas/metric_registry.json`: registry v0.2 with 5 CANONICAL
  metrics + 3 NEEDS_CANONICAL_LOCK metrics.
- `src/metrics/registry.py`: `MetricRegistry` with v0.2.
- `src/metrics/engine.py`: `ScoringEngine` computes all 5.
- `pilot/UPSILON_PILOT_SPEC.md`: required property #4 (canonical
  measurement, 5 metrics, NOT configurable).

**Status:** TRACED

---

## 7. Cohort and operator intelligence

**Source:** `_specs/18_ENTERPRISE_EVAL_CATALOG.md` (15 eval families);
`_specs/14_PRODUCT_OBJECT_MODEL.md` (domain objects).

**Original requirement:** Cohort analysis, operator profiles,
percentile positioning, usage-vs-operation divergence, longitudinal
movement, learning curves, team composition, operator similarity,
organizational topology, capability dependency risk, context
architecture, operator×system decomposition.

**Current evidence:**
- `src/analysis/`: 16 modules (divergence, percentiles, distributions,
  eligibility, data_quality, verifier, replication, org_topology,
  similarity, context_architecture, longitudinal, team_composition,
  dependency_risk, learning_curve, operator_system,
  outcome_correlation).
- `src/config/eval_registry.py`: 15 eval families, all
  `implemented=True, implementation_status="full"`.
- `PilotService`: exposes all analyses via service methods.

**Status:** TRACED

---

## 8. Intervention product — 12-entry catalog with pre/post verification

**Source:** `_specs/09_DIAGNOSTIC_INTERVENTION_REGISTRY.md`;
`_specs/05_PILOT_PHASES_IMPLEMENTATION_PLAN.md` (P1).

**Original requirement:** Workflow-stage mapping, deterministic
recommendation rules, intervention ledger, pre/post remeasurement,
similarity analysis, learning curves.

**Current evidence:**
- `src/interventions/registry.py`: 12-entry fixed catalog
  (CTX/FRM/MOD/AGT/REV/STD/COA/LRN/STG) with pattern→intervention
  mapping.
- `src/interventions/manager.py`: `InterventionManager.assign()` /
  `close()`.
- `src/analysis/verifier.py`: `PrePostVerifier` computes target +
  non-target deltas.
- `src/analysis/similarity.py`: operator similarity search.
- `src/analysis/learning_curve.py`: learning curve analysis.
- `pilot/UPSILON_PILOT_SPEC.md`: required property #6 (controlled
  interventions) and #7 (pre/post verification).

**Status:** TRACED

---

## 9. Evidence and causality discipline

**Source:** `_specs/17_PROOF_AND_CLAIMS_REGISTRY.md`;
`_specs/12_PRIVACY_GOVERNANCE_SPEC.md` (decision-use restrictions).

**Original requirement:** Evidence grades, claim status, hypotheses,
associations, outcome lineage, replication, data quality. No
correlation-to-causation inflation.

**Current evidence:**
- `src/outcomes/governance.py`: enforces ASSOCIATION-only, never
  CAUSATION.
- `src/analysis/outcome_correlation.py`: `EvidenceGrade.OBSERVATIONAL`,
  ASSOCIATION claims.
- `src/analysis/replication.py`: `ReplicationEngine` for descriptive
  stability.
- `src/analysis/data_quality.py`: 6 checks with OK/WARNING/BLOCKING
  severity.
- `src/domain/lineage.py`: BI→AAI→committed-state→outcome chain.
- `src/diagnostics/diagnosis_engine.py`: all diagnoses are HYPOTHESIS,
  never CONFIRMED.
- `pilot/UPSILON_PILOT_SPEC.md`: required property #5 (HYPOTHESIS
  status) and prohibited property #2 (no causal claims).

**Status:** TRACED

---

## 10. Operator, system, and operator×system decomposition

**Source:** The deep-dive review (§7) identifies this as "one of the
strongest recovered ideas in the original dossier." The specific spec
reference is `_specs/18_ENTERPRISE_EVAL_CATALOG.md` EVAL-005 (Platform
/ Model Sensitivity).

**Original requirement:** Separate operator effect, system/model
effect, and operator×system interaction effect.

**Current evidence:**
- `src/analysis/operator_system.py`: `operator_system_decomposition()`
  separates operator/system/interaction effects for operators on 2+
  systems.
- `src/config/eval_registry.py`: EVAL-005 "Platform / Model
  Sensitivity" maps to `operator_system_decomposition`.
- CLI: `enterprise compare operator-system`.
- MCP: `get_operator_system_decomposition`.

**Status:** TRACED

---

## 11. Reporting deliverables — 12 P0/P1/P2 outputs

**Source:** `_specs/13_ENTERPRISE_REPORTING_DELIVERABLES.md`.

**Original requirement:** 12 deliverables: data quality report,
workforce operating map, divergence report, cohort comparison,
operator profiles, hypothesis map, intervention plan, re-measurement
report, workflow fit, outcome validation, executive brief,
next-evaluations flywheel.

**Current evidence:**
- `src/reporting/exporters.py`: `export_pilot_markdown()`,
  `export_data_quality_markdown()`, `export_hypothesis_map()`,
  `export_remeasurement_markdown()`.
- `src/reporting/executive_brief.py`: executive brief.
- `src/reporting/decision_report.py`: decision report.
- `src/reporting/pdf.py`: PDF rendering (see
  `DRIFT_AND_CONTRADICTIONS.md` Drift 3 for integrity issue).
- CLI: `enterprise export pilot|brief|hypothesis-map|remeasurement|
  dashboard`.

**Status:** TRACED (PARTIAL) — reporting outputs exist but the
static sample report (`g09_sample_customer_report.md`) can diverge
from runtime evidence. See `DRIFT_AND_CONTRADICTIONS.md` Drift 2 and
Drift 3.

---

## 12. Operating surfaces — CLI, TUI, MCP

**Source:** `_specs/06_TUI_PRODUCT_SPEC.md`,
`_specs/07_CLI_COMMAND_SPEC.md`, `_specs/08_MCP_TOOL_SPEC.md`.

**Original requirement:** CLI, TUI, and MCP as pilot interfaces.

**Current evidence:**
- `src/cli/main.py`: 17 command groups.
- `src/tui/app.py`: 12 screens (512 lines).
- `src/mcp_server/server.py`: 27 tools (21 read + 6 write) + 6
  resources.
- `tests/tui_audit.py`: validates TUI screen structure.

**Status:** TRACED

---

## 13. Governance — privacy, consent, disclosure, bias review

**Source:** `_specs/12_PRIVACY_GOVERNANCE_SPEC.md`.

**Original requirement:** Purpose limitation, employee disclosure,
consent, bias review, right to challenge, correction process,
provenance, decision-use classification.

**Current evidence:**
- `src/governance/enforcement.py` (936 lines):
  PurposeLimitationGate, DisclosureGate, ConsentManager,
  BiasReviewManager, ChallengeManager, CorrectionManager,
  GovernanceAuditLog.
- `src/domain/observation.py`: `raw_source_reference` pointer, no raw
  content field.
- `src/domain/operator_identity.py`: pseudonymous IDs with
  cross-system mapping.
- `pilot/UPSILON_PILOT_SPEC.md`: required property #10 (governance
  compliance).

**Status:** TRACED (PARTIAL) — governance enforcement exists but
persistence, attestation, and RBAC are not production-hardened. See
`FIRST_CUSTOMER_READINESS.md` HARDENING RECOMMENDED.

---

## 14. Pilot lifecycle — bounded evaluation with terminal decision

**Source:** `_specs/05_PILOT_PHASES_IMPLEMENTATION_PLAN.md`
(P0/P1/P2/P3 phases); `_specs/20_PILOT_OPERATING_PLAYBOOK.md`
(30-day procedure with closeout).

**Original requirement:** The pilot is a bounded evaluation that
terminates in a buyer-facing outcome and continuation decision.

**Current evidence:**
- `pilot/UPSILON_PILOT_SPEC.md`: required property #9 (terminal
  decision: STOP/EXTEND/EXPAND/DEPLOY).
- `pilot/PILOT_LIFECYCLE.md`: 8-stage lifecycle.
- `pilot/governance/DECISION_GATES.md`: 3 pilot-level decision gates.
- `pilot/governance/CLOSURE_OUTCOMES.md`: 4 closure outcomes.
- `pilot/governance/PILOT_STATE_MACHINE.md`: state transitions.

**Status:** TRACED (as specification) / NOT TRACED (as runtime —
pilot-level gates, decision records, and state machine are not yet
implemented as runtime objects; see `implementation/GAP_REGISTER.md`).

---

## 15. Success criteria — locked before measurement

**Source:** `_specs/20_PILOT_OPERATING_PLAYBOOK.md` ("Pilot success
criteria" section); `_specs/12_PRIVACY_GOVERNANCE_SPEC.md`
(development doctrine).

**Original requirement:** Success criteria defined before
instrumentation, including: at least 90% usable cohort telemetry,
stable normalization and provenance, meaningful operator
differentiation, identifiable longitudinal movement, at least one
actionable workflow or development finding, intervention candidates
accepted, remeasurement demonstrated.

**Current evidence:**
- `pilot/governance/SUCCESS_CRITERIA.md`: defines criterion structure
  (criterion_id, metric, threshold, direction, aggregation, rationale,
  closure_mapping) with locking mechanism.
- `pilot/UPSILON_PILOT_SPEC.md`: required property #3 (locked success
  criteria) and prohibited property #6 (no amending after
  measurement).

**Status:** TRACED (PARTIAL) — success criteria are specified but not
yet tiered into global/template/customer-specific categories (see
deep-dive review §19). The original product criteria and commercial
criteria from the dossier are not explicitly recovered into
`SUCCESS_CRITERIA.md`.

---

## 16. Synthetic 50-person fixture

**Source:** `_specs/02_ENTERPRISE_DEMO_DATA_SPEC.md`.

**Original requirement:** A synthetic 50-operator, 30-day enterprise
cohort with 9 archetypes, divergence cases, workflow, interventions,
pre/post, and 16 acceptance tests.

**Current evidence:**
- `demo_data/operators.json`: 50 operators with `pattern_demo`
  archetype labels (9 archetypes: context_compounder,
  high_volume_burner, efficient_minimalist, kinetic_generator,
  recursive_builder, volatile_switcher, balanced_operator,
  improving_operator, declining_operator).
- `demo_data/observations.jsonl`: 1,668 observations.
- `demo_data/workflows.json`: 4 workflows.
- `demo_data/lineages.jsonl`: 50 lineages.
- `demo_data/artifacts.jsonl`: 200 artifacts.
- `scripts/generate_demo_data.py`: generator with seed 50030.

**Status:** TRACED — but see `DRIFT_AND_CONTRADICTIONS.md` Drift 1
(market shift) and Drift 4 (archetype label ambiguity).

---

## 17. Original developmental ontology (Trans Ladder)

**Source:** The deep-dive review (§17, Drift 5) references an original
ontology including the "Trans Ladder" and labels such as Seeker,
Refiner, Bearer, Igniter, Base, Power, Arch, and Transmitter.

**Original requirement:** **UNRESOLVED.** The specific spec
statements defining this ontology could not be located in the
available `_specs/` documents. The terms do not appear in the
codebase, demo data, or spec files.

**Current evidence:** Not present. The underlying ideas (longitudinal
movement, learning curves, trajectory, similarity, development engine)
survived through eval families, but the original ontology itself was
not implemented.

**Status:** NOT TRACED — the ontology was either abandoned, deferred,
or originated in the SignalAF commercial field dossier (not present in
the repository). See `DRIFT_AND_CONTRADICTIONS.md` Drift 5 and
`OPEN_QUESTIONS.md` OQ-011.

---

## 18. Enterprise productionization (P2)

**Source:** `_specs/05_PILOT_PHASES_IMPLEMENTATION_PLAN.md` (P2);
`_specs/19_INTEGRATION_PRIORITY_MATRIX.md`.

**Original requirement:** Continuous ingest, web interface, SSO and
RBAC, configurable policies, MO§ES appliance deployment, private
benchmark network.

**Current evidence:**
- `src/repository/sqlite_repository.py`: persistence available (demo
  uses in-memory).
- `src/ingest/`: 11 adapters (fixture, claude, codex, github,
  api-claude, api-codex, api-groq).
- Web interface: not implemented.
- SSO/RBAC: not implemented.
- Configurable policies: `PilotConfiguration` with governance config.
- Appliance deployment: not implemented.
- Private benchmark network: not implemented.

**Status:** TRACED (PARTIAL) — P2 is partially represented in
architecture but not productionized. See
`FIRST_CUSTOMER_READINESS.md` POST-PILOT / SCALE REQUIREMENT.

---

## Summary

| # | Requirement | Status |
|---|---|---|
| 1 | Commercial category — AI Operator Evals | TRACED |
| 2 | Pilot boundary — 25–100 operators, ~30 days | TRACED |
| 3 | Original beachhead — mixed-role workforce | NOT TRACED |
| 4 | Closed-loop commercial system | TRACED |
| 5 | Development doctrine — raise the floor | TRACED |
| 6 | Canonical metrics — 5 frozen | TRACED |
| 7 | Cohort and operator intelligence | TRACED |
| 8 | Intervention product — 12-entry catalog | TRACED |
| 9 | Evidence and causality discipline | TRACED |
| 10 | Operator×system decomposition | TRACED |
| 11 | Reporting deliverables — 12 outputs | TRACED (PARTIAL) |
| 12 | Operating surfaces — CLI, TUI, MCP | TRACED |
| 13 | Governance — privacy, consent, disclosure | TRACED (PARTIAL) |
| 14 | Pilot lifecycle — terminal decision | TRACED (spec) / NOT TRACED (runtime) |
| 15 | Success criteria — locked before measurement | TRACED (PARTIAL) |
| 16 | Synthetic 50-person fixture | TRACED |
| 17 | Original developmental ontology (Trans Ladder) | NOT TRACED |
| 18 | Enterprise productionization (P2) | TRACED (PARTIAL) |

**13 of 18 requirements are TRACED. 2 are NOT TRACED. 3 are TRACED
(PARTIAL). 1 is TRACED as specification but NOT TRACED as runtime.**

The NOT TRACED items (mixed-role beachhead, Trans Ladder ontology)
and the PARTIAL items (reporting integrity, governance hardening,
pilot lifecycle runtime, success criteria tiering, P2 productionization)
are the genuine gaps. They are cataloged in
`implementation/GAP_REGISTER.md` and addressed in
`implementation/PILOT_MODE_BUILD_PLAN.md`.

---

## What this document does NOT do

- Does not define specifications (see `pilot/UPSILON_PILOT_SPEC.md`)
- Does not define gaps (see `pilot/implementation/GAP_REGISTER.md`)
- Does not catalog drift (see `DRIFT_AND_CONTRADICTIONS.md`)
- Does not catalog proof points (see `PILOT_PROOF_POINTS.md`)
- Does not fabricate original intent (UNRESOLVED items are marked)
