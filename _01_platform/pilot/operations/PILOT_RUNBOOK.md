# PILOT_RUNBOOK.md

> The master operational playbook for executing an Upsilon Enterprise
> Pilot from initial customer qualification through final decision.
>
> Someone who understands Upsilon but has never personally run a pilot
> should be able to follow this runbook and execute one without relying
> on undocumented tribal knowledge.
>
> This runbook TRANSLATES the canonical stage specifications
> (`pilot/stages/`) into executable procedures. It does NOT redefine
> stages, gates, or artifacts. For canonical definitions, see
> `pilot/UPSILON_PILOT_SPEC.md`, `pilot/PILOT_LIFECYCLE.md`, and
> `pilot/governance/`.

## How to use this runbook

1. Read `pilot/UPSILON_PILOT_SPEC.md` first — understand what a pilot
   is and is not.
2. Follow this runbook sequentially. Each section maps to a lifecycle
   stage and references the supporting checklist.
3. At each gate, stop and execute the gate review procedure
   (`GATE_REVIEW_RUNBOOK.md`).
4. Do not skip stages. Do not skip gates. Do not continue without
   producing the required artifact.
5. If you cannot complete a stage, escalate per
   `governance/DECISION_GATES.md` Gate 2 outcomes.

## Roles

| Role | Responsibility | When involved |
|---|---|---|
| Pilot Creator | Defines the pilot, creates charter, locks success criteria | DEFINE |
| Decision Authority | Approves launch, makes closure decision | Gate 1, Gate 3 |
| Pilot Operator (Upsilon side) | Runs the platform, ingests data, generates reports | All stages |
| Customer Sponsor | Authorizes operator participation, consents to governance | DEFINE, INSTRUMENT |
| Customer Operators | Provide telemetry (passive — no active task required) | INSTRUMENT onward |

> For the first real customer pilot, the Pilot Creator and Pilot
> Operator may be the same person. The Decision Authority MUST be a
> different person from the Pilot Creator (separation of concerns).

## Pre-flight

Before starting, confirm:

- [ ] Upsilon platform is installed and `pytest tests/ -q` passes
  (currently 676 tests)
- [ ] `enterprise` CLI is on PATH (`./enterprise --help` works)
- [ ] Customer has been qualified per `CUSTOMER_INTAKE.md`
- [ ] `PRE_PILOT_CHECKLIST.md` is complete

## Stage-by-stage procedure

### Stage 00 — DEFINE

**Goal:** Create a bounded pilot charter with locked success criteria.

**Procedure:**

1. Identify the customer's pilot question. Match it to a commercial
   pilot template (`enterprise configure list-pilots`) or build an
   à la carte configuration (`enterprise configure from-evals`).
2. Define the population boundary:
   - Operator count (25–100, per `CohortConfig.min/max_operators`)
   - Selection criteria (which operators, why)
   - Teams to be included
3. Define the duration boundary:
   - Window start date
   - Window end date (default 30 days; intervention pilots need
     follow-up window, typically +14 days)
4. Select eval families (`enterprise configure from-evals --evals
   EVAL-001,EVAL-002,...`). See `src/config/eval_registry.py` for
   the 15 eval families and their dependencies.
5. Define success criteria. Each criterion needs:
   - `criterion_id` (e.g., SC-001)
   - `metric` (canonical metric or derived measure)
   - `threshold` (numeric)
   - `direction` (above/below)
   - `aggregation` (cohort_median, cohort_p10, target_group_delta, etc.)
   - `rationale` (why this criterion matters)
   - `closure_mapping` (which outcomes this informs)
6. Lock success criteria BEFORE any measurement. Record `locked_at`
   and `locked_by`.
7. Set governance metadata:
   - `decision_use_default`: DEVELOPMENTAL (never PERSONNEL)
   - `privacy_class`: pseudonymous_real (for real customers)
   - `synthetic`: false
   - `purpose_id`: record the processing purpose
   - `consent_model`: opt_in / opt_out / mandated
8. Validate the configuration (`enterprise configure validate`).
9. Create the Pilot Charter artifact (see
   `governance/PILOT_CHARTER.md` and `schemas/PILOT_CHARTER_SCHEMA.md`).
10. **GATE 1 — LAUNCH READINESS:** Execute the gate review procedure
    (`GATE_REVIEW_RUNBOOK.md`). Record the outcome (LAUNCH,
    LAUNCH_WITH_CONDITIONS, DEFER, or DECLINE).

**Required artifact:** Pilot Charter (with locked success criteria)

**Supporting checklist:** `PRE_PILOT_CHECKLIST.md`,
`PILOT_LAUNCH_CHECKLIST.md`

**Commands/surfaces:**
- `enterprise configure list-pilots` — list 12 commercial pilot templates
- `enterprise configure list-evals` — list 15 eval families
- `enterprise configure from-pilot --pilot-id 1` — build from template
- `enterprise configure from-evals --evals EVAL-001,EVAL-002` — à la carte
- `enterprise configure validate` — validate configuration
- `enterprise configure show` — display current configuration
- TUI screen C (Configure)
- MCP `create_pilot_configuration`, `validate_pilot_configuration`

> **Implementation gap:** The platform does not yet implement
> `pilot_id`, success criteria locking, or Gate 1 evaluation. For the
> first real pilot, these are handled manually (see
> `FIRST_CUSTOMER_READINESS.md`). The charter is created as a
> document, not yet as a platform object.

### Stage 01 — INSTRUMENT

**Goal:** Collect telemetry from the customer's operator population.

**Procedure:**

1. Resolve operator identities. For each operator, map their
   system-specific IDs (e.g., ChatGPT email, Claude account) to
   canonical operator IDs (`op_001`, `op_002`, ...). Use
   `OperatorIdentity` with conflict detection.
2. Obtain provider telemetry. Choose the ingestion path based on
   available data:
   - **Provider file export:** `enterprise ingest claude/codex/github
     --file <path> --full` — parse provider export files
   - **Provider API:** `enterprise ingest api-claude/api-codex/api-groq
     --operator <id> --days 30` — live API ingestion (requires API key)
   - **Fixture (demo only):** `enterprise ingest fixture` — load
     synthetic demo data
3. Run governance checks BEFORE ingestion. For real customers, do NOT
   use `--skip-governance`. The platform will block ingestion if
   purpose/disclosure/consent gates are not satisfied.
4. Validate observations (`enterprise ingest validate`). Check for:
   - Missingness
   - Impossible values
   - Duplicates
   - Provenance
   - Source confidence
   - Sparse operators
5. Check data quality (`enterprise validate outcomes`). Confirm:
   - 0 BLOCKING issues
   - WARNING count is acceptable (warnings are expected for real data)
6. Confirm sufficient observations. Rule of thumb: minimum 20
   observations per operator over the baseline window.
7. Record the Instrumentation Readiness artifact.

**Required artifact:** Instrumentation Readiness Record

**Commands/surfaces:**
- `enterprise ingest <provider> --file <path> --full --purpose <purpose_id>`
- `enterprise ingest api-claude --operator <id> --days 30`
- `enterprise ingest validate`
- `enterprise validate outcomes`
- TUI screen 9 (Data Quality)
- MCP `check_ingestion_governance`, `get_data_quality`

> **Implementation gap:** API ingestion is in stub mode and has not
> been tested with real provider APIs. Cross-system identity
> resolution exists but has no real mapping workflow. See
> `FIRST_CUSTOMER_READINESS.md`.

### Stage 02 — BASELINE

**Goal:** Compute canonical metrics for all eligible operators.

**Procedure:**

1. Score the cohort (`enterprise score cohort`). This computes all 5
   canonical metrics (leverage, yield, token_snr, log_leverage,
   construction) for all operators over the baseline window.
2. Compute percentiles (`enterprise compare cohort`). Maps each
   operator's metrics to reference-population percentiles.
3. Compute cohort distributions. Confirm medians match expectations.
4. Compute composite developmental scores
   (`enterprise score composite-summary`). Confirm the summary is a
   distribution, NOT a leaderboard.
5. Check eligibility (`enterprise verify operator`). Confirm all
   operators meet minimum observation count and non-null metrics.
6. Benchmark against reference population
   (`enterprise benchmark cohort`). Confirm benchmark class selection
   (peer/self_vs_prior/role/etc.).
7. Record the Baseline Snapshot artifact. Include a timestamp — the
   baseline must be immutable for valid pre/post comparison.

**Required artifact:** Baseline Snapshot (with timestamp)

**Commands/surfaces:**
- `enterprise score cohort`
- `enterprise score composite-summary`
- `enterprise compare cohort`
- `enterprise benchmark cohort --metric leverage`
- `enterprise verify operator <id>`
- TUI screens 2 (Cohort), 3 (Operator)
- MCP `get_operator_profile`, `get_cohort_distribution`,
  `compare_operator_to_reference`, `get_composite_score_summary`

> **Implementation gap:** No immutable baseline snapshot mechanism.
   The baseline is recomputed each `PilotService` instantiation. For
   the first real pilot, save the baseline output to a timestamped
   file manually. See `FIRST_CUSTOMER_READINESS.md`.

### Stage 03 — DIAGNOSE

**Goal:** Identify actionable operating differences and hypotheses.

**Procedure:**

1. Detect patterns (`enterprise diagnose cohort`). The PatternEngine
   detects 6 pattern types: P-CTX-01, P-CTX-02, P-BURN-01,
   P-HIDDEN-01, P-MODEL-01, P-STAGE-01.
2. Generate diagnoses (`enterprise diagnose cohort`). The
   DiagnosisEngine produces hypotheses with evidence + alternatives.
   All diagnoses carry HYPOTHESIS status — never CONFIRMED.
3. Analyze divergence (`enterprise compare usage-operation`).
   Classifies operators into 4 quadrants: HIGH_USAGE_LOW_OPERATION,
   LOW_USAGE_HIGH_OPERATION, LOW_LOW, MIXED.
4. Analyze workflow fit (`enterprise workflow fit`). Computes
   provisional stage fit with sample-size gates (min 5 observations).
5. Map org topology (`enterprise compare topology`). Team-level
   distributions, capability concentration, single points of failure.
6. Run additional analyses as needed:
   - Context architecture (`enterprise score operator <id>`)
   - Longitudinal movement (service method)
   - Team composition (`enterprise compare teams`)
   - Dependency risk (service method)
   - Learning curve (service method)
   - Operator similarity (`enterprise compare similarity`)
   - Operator×System decomposition (`enterprise compare operator-system`)
7. Record the Diagnostic Findings artifact.

**Required artifact:** Diagnostic Findings

**Commands/surfaces:**
- `enterprise diagnose cohort`
- `enterprise compare usage-operation`
- `enterprise workflow fit`
- `enterprise compare topology`
- `enterprise compare teams`
- `enterprise compare similarity`
- `enterprise compare operator-system`
- TUI screens 4 (Divergence), 5 (Diagnose), 6 (Workflow)
- MCP `get_diagnostics`, `find_usage_operation_divergence`,
  `get_workflow_fit`, `get_org_topology`, `get_operator_similarity`,
  `get_operator_system_decomposition`

### Stage 04 — INTERVENE

**Goal:** Apply controlled interventions with declared targets.

**Procedure:**

1. Review the intervention catalog (`enterprise intervention catalog`).
   12 entries: CTX-001/002/003, FRM-001/002, MOD-001, AGT-001,
   REV-001, STD-001, COA-001, LRN-001, STG-001.
2. Review recommended interventions from diagnoses. Each diagnosis
   carries `recommended_interventions`.
3. For each intervention to be applied:
   - Confirm the target operator
   - Confirm the catalog entry (`--plan <catalog_id>`)
   - Confirm the target metric (`--target-metric <metric>`)
   - Confirm the follow-up window (`--followup-days <N>`)
   - Confirm authorization (`--authorized-by <identity>`)
   - Assign: `enterprise intervention assign <operator_id> --plan
     <catalog_id> --target-metric <metric> --followup-days <N>
     --authorized-by <identity>`
4. **GATE 2 — PILOT HEALTH:** Execute the gate review procedure at
   regular checkpoints (weekly or at intervention milestones). Record
   the outcome (CONTINUE, ADJUST, ESCALATE, TERMINATE).
5. Record the Intervention Records artifact.

**Required artifact:** Intervention Records (with authorized_by)

**Supporting runbook:** `INTERVENTION_RUNBOOK.md`

**Commands/surfaces:**
- `enterprise intervention catalog`
- `enterprise intervention recommend` (if available)
- `enterprise intervention assign <operator_id> --plan <catalog_id> --target-metric <metric> --followup-days <N> --authorized-by <identity>`
- `enterprise intervention close <intervention_id> --outcome <SUCCESS/PARTIAL/NO_EFFECT/NEGATIVE>`
- TUI screen 7 (Interventions)
- MCP `assign_intervention`, `close_intervention`,
  `get_intervention_status`

> **Implementation gap:** `authorized_by` is enforced in the CLI/MCP
> layer but not on the `Intervention` domain object itself. For the
> first real pilot, record `authorized_by` in the intervention
> record manually if using programmatic assignment.

### Stage 05 — VERIFY

**Goal:** Measure results against pre-declared targets.

**Procedure:**

1. Wait for follow-up windows to complete (typically 14–30 days post
   intervention start).
2. Ingest follow-up telemetry (same as Stage 01, for the follow-up
   window).
3. Verify each intervention
   (`enterprise verify intervention <intervention_id>`). Computes
   target + non-target metric deltas between baseline and follow-up
   windows.
4. Verify all interventions
   (`enterprise verify intervention` for each, or batch via service
   method `verify_all_interventions()`).
5. Compute outcome correlations through lineage
   (`enterprise lineage outcomes`). Connects lineage micro_eval to
   Outcome nodes. All claims are ASSOCIATION, never CAUSATION.
6. **GATE 2 — PILOT HEALTH:** Execute the gate review procedure.
   Confirm the pilot is still a valid experiment.
7. (Recommended) Run replication on key findings
   (`PilotService.replicate_finding()`). Tests descriptive stability
   across window/cohort splits.
8. Record the Verification Results artifact.

**Required artifact:** Verification Results

**Commands/surfaces:**
- `enterprise verify intervention <intervention_id>`
- `enterprise lineage outcomes`
- `enterprise lineage show <operator_id>`
- TUI screen 8 (Verify)
- MCP `verify_change`, `get_outcome_correlation`,
  `get_lineage_chain`, `get_lineage_summary`

> **Implementation gap:** Replication is not integrated into the
> standard verification flow. For the first real pilot, run
> replication manually via `PilotService.replicate_finding()`.

### Stage 06 — READOUT

**Goal:** Synthesize evidence into a decision-oriented readout.

**Procedure:**

1. Generate the pilot markdown readout
   (`enterprise export pilot`). Full pilot status with data quality,
   workforce operating map, medians, percentiles.
2. Generate the executive brief
   (`enterprise export brief`). Decisions, next experiments,
   next-evaluations flywheel.
3. Generate the decision report
   (`PilotService.decision_report()`). Translates measurement
   vocabulary to decision vocabulary with developmental action
   recommendations.
4. Generate preferred manager objects
   (`PilotService.preferred_manager_objects()`). 8 developmental
   objects: development groups, fastest improvers, stalled cohorts,
   workflow bottlenecks, tool/model fit, training candidates, peer
   support, remeasurement queue.
5. Generate the hypothesis map
   (`enterprise export hypothesis-map`). Maps detected patterns to
   eval families.
6. Generate the re-measurement report
   (`enterprise export remeasurement`). Post-intervention
   re-measurement summary.
7. (Optional) Generate the executive dashboard
   (`enterprise export dashboard`). HTML dashboard with charts.
8. Compare evidence against locked success criteria. For each
   criterion: MET, MISSED, or PARTIAL.
9. Record the Pilot Readout artifact.

**Required artifact:** Pilot Readout (with evidence-vs-criteria
comparison)

**Commands/surfaces:**
- `enterprise export pilot`
- `enterprise export brief`
- `enterprise export hypothesis-map`
- `enterprise export remeasurement`
- `enterprise export dashboard`
- TUI screen E (Export)
- MCP `get_executive_dashboard`

### Stage 07 — DECIDE

**Goal:** Make the evidence-backed terminal decision.

**Procedure:**

1. **GATE 3 — CLOSURE / SCALE:** Execute the gate review procedure.
   Compare evidence against locked success criteria. Select outcome:
   - **STOP:** Did not meet criteria. Discontinue.
   - **EXTEND:** Shows promise but missing evidence. MUST include
     explicit reason, missing evidence, new evidence requirement,
     extension period, new closure date.
   - **EXPAND:** Met criteria. Expand to larger scope. Charter a new
     pilot.
   - **DEPLOY:** Met criteria. Transition to production.
2. Create the Decision Record artifact (see
   `schemas/DECISION_RECORD_SCHEMA.md`). The decision record is
   immutable.
3. Communicate the decision to the customer.
4. If EXTEND: return to Stage 01 (INSTRUMENT) or Stage 02 (BASELINE)
   with the new window. Do NOT re-create the charter.
5. If EXPAND: charter a new pilot with expanded scope. The current
   pilot is terminated.
6. If DEPLOY: execute the production transition plan.
7. If STOP: archive the pilot. Document lessons learned.

**Required artifact:** Decision Record (immutable)

**Supporting checklist:** `PILOT_CLOSEOUT_CHECKLIST.md`

> **Implementation gap:** The platform does not yet implement Gate 3
> evaluation, DecisionRecord, or closure outcomes. For the first
> real pilot, the decision is made by the Decision Authority
> manually, documented per `schemas/DECISION_RECORD_SCHEMA.md`, and
> stored as a file. See `FIRST_CUSTOMER_READINESS.md`.

## Cadence

See `PILOT_CADENCE.md` for the recommended cadence of checkpoints,
gate reviews, and customer communications throughout the pilot.

## Escalation

| Situation | Action |
|---|---|
| Data quality degrades (BLOCKING issues emerge) | Gate 2: ADJUST or ESCALATE |
| Operator participation drops below minimum | Gate 2: ESCALATE |
| Governance gate cannot be satisfied | Gate 2: ESCALATE |
| Success criteria appear unachievable | Continue to Gate 3; do not amend criteria |
| Technical platform failure | Pause pilot; document; resume when resolved |
| Customer wants to change scope mid-pilot | Do NOT amend charter. Complete current pilot. Charter a new pilot for the new scope. |

## What this runbook does NOT cover

- Customer qualification (see `CUSTOMER_INTAKE.md`)
- Pre-pilot readiness (see `PRE_PILOT_CHECKLIST.md`)
- Launch procedure (see `PILOT_LAUNCH_CHECKLIST.md`)
- Intervention execution details (see `INTERVENTION_RUNBOOK.md`)
- Gate review procedure (see `GATE_REVIEW_RUNBOOK.md`)
- Closeout procedure (see `PILOT_CLOSEOUT_CHECKLIST.md`)
- First customer readiness (see `FIRST_CUSTOMER_READINESS.md`)
- Canonical stage definitions (see `pilot/stages/`)
- Governance definitions (see `pilot/governance/`)
- Schema definitions (see `pilot/schemas/`)
