# PILOT_MODE_BUILD_PLAN.md

> The minimal implementation delta required to establish a formal
> `Pilot Mode` in the Upsilon platform.
>
> This plan is separated into three maturity targets. Items in different
> targets MUST NOT be mixed.

## Design principle

> **Integrate, don't duplicate.** The platform already has rich
> measurement, diagnostic, intervention, verification, and reporting
> capability. Pilot Mode adds the governance layer (pilot identity,
> state machine, gates, success criteria, decisions) that binds these
> capabilities into a formal pilot lifecycle. It does not re-implement
> measurements, diagnoses, or interventions.

## Maturity targets

| Target | Description | When required |
|---|---|---|
| **T1: ACME reference completion** | Make the ACME-001 reference pilot complete the full lifecycle including DECIDE | Before claiming the reference pilot is complete |
| **T2: First real customer pilot** | Make a real customer pilot possible with real data, real governance, real closure | Before onboarding the first real customer |
| **T3: Scalable production deployment** | Make Pilot Mode scalable to multiple concurrent pilots with persistence and audit | Before deploying to production at scale |

---

## Pilot Mode control surface

> Pilot Mode should make Upsilon understand: "I am currently executing
> Pilot `<pilot_id>`." The control surface is an orchestration layer
> that binds pilot context to existing analytical screens — it does NOT
> re-implement those screens.

### Lifecycle display

When Pilot Mode is active, the operator sees the current lifecycle stage
at a glance:

```text
✓ DEFINE
✓ INSTRUMENT
✓ BASELINE
→ DIAGNOSE
○ INTERVENE
○ VERIFY
○ READOUT
○ DECIDE
```

- `✓` = stage complete (gate passed, artifact produced)
- `→` = current stage (in progress)
- `○` = not yet started

The lifecycle display is the top-level Pilot Mode indicator. It is
rendered in the TUI header and available as a CLI status command and MCP
tool.

### Control surface fields

The Pilot Mode control surface exposes 17 fields that together answer
"what is the state of this pilot?":

| # | Field | Source (existing or new) | TUI screen | CLI command | MCP tool |
|---|---|---|---|---|---|
| 1 | Enterprise | NEW: `PilotConfiguration.enterprise_name` (GAP-026) | Screen 1 (Pilot) | `pilot status` | `get_pilot_status` (extend) |
| 2 | Pilot ID | NEW: `PilotId` value object (GAP-001) | Screen 1 (Pilot) | `pilot status` | `get_pilot_status` (extend) |
| 3 | Current day / duration | EXISTING: `Cohort.window_start`/`window_end` + computed day | Screen 1 (Pilot) | `pilot status` | `get_pilot_status` (extend) |
| 4 | Current stage | NEW: `PilotStateMachine.current_state` (GAP-008) | Screen 1 (Pilot) + lifecycle display | `pilot status` | `get_pilot_status` (extend) |
| 5 | Operator participation | EXISTING: `pilot_status().eligible_operators` / total | Screen 1 (Pilot) | `pilot status` | `get_pilot_status` |
| 6 | Observation count | EXISTING: `pilot_status().observation_count` | Screen 1 (Pilot) | `pilot status` | `get_pilot_status` |
| 7 | Data-quality state | EXISTING: `data_quality_summary()` (OK/WARNING/BLOCKING) | Screen 9 (Data Quality) | `validate outcomes` | `get_data_quality` |
| 8 | Reference field | EXISTING: `ReferencePopulation.reference_id` + `version` + `synthetic` | Screen 3 (Operator) | `benchmark summary` | `compare_operator_to_reference` |
| 9 | Objectives | NEW: `PilotConfiguration.pilot_question` (GAP-025) | Screen C (Configure) | `configure show` | `create_pilot_configuration` (extend) |
| 10 | Success criteria | NEW: `SuccessCriteria` dataclass (GAP-002, GAP-003) | NEW: Governance screen | `pilot criteria show` | `lock_success_criteria` (new) |
| 11 | Completed milestones | NEW: milestone records tied to `pilot_id` + stage (GAP-008) | Lifecycle display | `pilot milestones` | `get_pilot_milestones` (new) |
| 12 | Current findings | EXISTING: `detect_cohort_patterns()` + `generate_cohort_diagnoses()` | Screen 5 (Diagnose) | `diagnose cohort` | `get_diagnostics` |
| 13 | Interventions | EXISTING: `PilotService.interventions` | Screen 7 (Interventions) | `intervention catalog` | `get_intervention_status` |
| 14 | Verification state | EXISTING: `verify_all_interventions()` | Screen 8 (Verify) | `verify intervention` | `verify_change` |
| 15 | Next gate | NEW: derived from `PilotStateMachine.current_state` (GAP-004/005/006) | Lifecycle display + NEW governance screen | `pilot gate next` | `evaluate_gate` (new) |
| 16 | Outstanding blockers | NEW: blocker registry tied to `pilot_id` (GAP-008) | NEW: Governance screen | `pilot blockers` | `get_pilot_blockers` (new) |
| 17 | Final decision status | NEW: `DecisionRecord.closure_outcome` or "pending" (GAP-007) | NEW: Governance screen | `pilot decide` | `create_decision_record` (new) |

### Existing screen mapping

The control plane sits ABOVE existing TUI/CLI/MCP screens. It does not
replace them. The mapping:

| Pilot stage | Existing TUI screen | Existing CLI command | Existing MCP tool |
|---|---|---|---|
| DEFINE | Screen C (Configure) | `configure from-pilot/from-evals/show` | `create_pilot_configuration`, `validate_pilot_configuration` |
| INSTRUMENT | Screen 1 (Pilot) | `ingest fixture/claude/codex/github` | `get_pilot_status` |
| BASELINE | Screen 2 (Cohort), Screen 3 (Operator) | `score operator/cohort`, `compare cohort`, `benchmark` | `get_operator_profile`, `get_cohort_distribution`, `compare_operator_to_reference` |
| DIAGNOSE | Screen 4 (Divergence), Screen 5 (Diagnose), Screen 6 (Workflow) | `diagnose cohort/operator`, `compare usage-operation/topology`, `workflow fit` | `get_diagnostics`, `find_usage_operation_divergence`, `get_workflow_fit`, `get_org_topology` |
| INTERVENE | Screen 7 (Interventions) | `intervention catalog/recommend/assign/close` | `get_intervention_status`, `assign_intervention`, `close_intervention` |
| VERIFY | Screen 8 (Verify) | `verify operator/intervention` | `verify_change`, `get_outcome_correlation` |
| READOUT | Screen E (Export) | `export pilot/brief/dashboard` | `get_executive_dashboard` |
| DECIDE | NEW: Governance screen | `pilot gate evaluate`, `pilot decide` | `evaluate_gate`, `create_decision_record` |

> **Do not rebuild functioning analytical screens.** The objective is
> orchestration and pilot context, not duplication. The control plane
> adds:
> 1. A lifecycle display (✓/→/○) in the TUI header
> 2. A new governance screen for charter, criteria, gates, and decision
> 3. Pilot context fields (pilot_id, enterprise, stage) threaded into
>    existing screens
> 4. New CLI commands and MCP tools only for governance objects

### Implementation note

The control surface is built from T1 items (GAP-001, GAP-008, GAP-002,
GAP-003, GAP-004/005/006, GAP-007, GAP-010). It is not a separate build
phase — it is the user-facing surface of the T1 governance layer. When
T1 is complete, the control surface is complete.

---

## T1: ACME reference completion

> Required before the ACME-001 reference pilot can be claimed as complete.

### T1.1 — Pilot identity binding

**What:** Add a `pilot_id` field that binds a pilot to its charter, state,
evidence, and decisions.

**Why:** Currently, `PilotService` is a service layer with no pilot
identity. Each instance is independent. There is no way to track which
pilot a set of measurements, diagnoses, or interventions belongs to.

**How:**
- Add `PilotId` value object (str, pattern `^[A-Z]+-\d{3}$`)
- Add `pilot_id` field to `PilotConfiguration` (optional, defaults to
  generated ID)
- Add `pilot_id` parameter to `PilotService.__init__()` (optional,
  defaults to "DEMO")
- Thread `pilot_id` through to intervention, verification, and report
  outputs

**Effort:** Small — mostly threading an ID through existing structures.

**Files affected:** `src/domain/pilot_configuration.py`, `src/service.py`

### T1.2 — Success criteria schema + locking

**What:** Add a `SuccessCriteria` dataclass with criterion list, locked_at,
locked_by. Add a `lock_success_criteria()` method that freezes criteria
before measurement.

**Why:** Without locked success criteria, Gate 3 cannot evaluate the
pilot. This is the critical governance gap.

**How:**
- Define `SuccessCriterion` dataclass (criterion_id, metric, threshold,
  direction, aggregation, rationale, closure_mapping)
- Define `SuccessCriteria` dataclass (criteria list, locked_at, locked_by)
- Add `success_criteria` field to `PilotConfiguration`
- Add `lock_success_criteria(criteria, locked_by)` method to
  `PilotService` — sets locked_at, raises if already locked
- Add `evaluate_success_criteria(measurements)` method — compares
  measured values against locked criteria, returns MET/MISSED/PARTIAL

**Effort:** Medium — new dataclass + evaluation logic, but no new
analytical capability (uses existing metric computations).

**Files affected:** `src/domain/pilot_configuration.py`, `src/service.py`

### T1.3 — Gate records

**What:** Add `GateRecord` dataclass and `evaluate_gate_1()`,
`evaluate_gate_2()`, `evaluate_gate_3()` methods.

**Why:** Pilot-level decision gates do not exist. Without them, the
pilot cannot formally launch, check health, or close.

**How:**
- Define `GateRecord` dataclass (gate_id, pilot_id, gate_type, outcome,
  conditions, criteria_evaluation, extend_requirements, rationale,
  evidence_cited, evaluated_at, evaluated_by)
- `evaluate_gate_1()`: check charter validity, success criteria locked,
  governance clearance → LAUNCH/LAUNCH_WITH_CONDITIONS/DEFER/DECLINE
- `evaluate_gate_2()`: check data sufficiency, quality, participation,
  governance, protocol → CONTINUE/ADJUST/ESCALATE/TERMINATE
- `evaluate_gate_3()`: evaluate success criteria (MET/MISSED/PARTIAL),
  aggregate → STOP/EXTEND/EXPAND/DEPLOY

**Effort:** Medium — new dataclass + gate evaluation logic. Gate 3
reuses `evaluate_success_criteria()` from T1.2.

**Files affected:** `src/domain/gate_record.py` (new), `src/service.py`

### T1.4 — Decision record

**What:** Add `DecisionRecord` dataclass and `create_decision_record()`
method.

**Why:** The platform has no closure decision capability. This is the
single largest gap.

**How:**
- Define `DecisionRecord` dataclass (decision_id, pilot_id,
  closure_outcome, rationale, evidence_cited,
  success_criteria_comparison, gate_3_record_id, conditions,
  extend_plan, expand_plan, deploy_plan, stop_lessons, decided_at,
  decided_by, immutable)
- `create_decision_record(outcome, rationale, evidence, ...)`: creates
  an immutable decision record
- Validate outcome-specific requirements (EXTEND needs extend_plan,
  EXPAND needs expand_plan, DEPLOY needs deploy_plan, STOP needs
  stop_lessons)

**Effort:** Small — new dataclass + validation. No new analytical
capability.

**Files affected:** `src/domain/decision_record.py` (new),
`src/service.py`

### T1.5 — Pilot state machine

**What:** Add `PilotState` enum and `PilotStateMachine` that tracks
current state and enforces valid transitions.

**Why:** The platform has no explicit state machine. Pilots do not
track their current stage or enforce transition rules.

**How:**
- Define `PilotState` enum (DEFINED, INSTRUMENTED, BASELINED, DIAGNOSED,
  INTERVENING, VERIFYING, READOUT, DECIDING, TERMINATED)
- Define `PilotStateMachine` with `current_state`, `transition_to()`,
  `can_transition_to()`
- Enforce transition rules from `PILOT_STATE_MACHINE.md`
- Add `pilot_state` field to `PilotService`

**Effort:** Small — state machine is straightforward.

**Files affected:** `src/domain/pilot_state.py` (new), `src/service.py`

### T1.6 — CLI/TUI/MCP surfaces for new governance objects

**What:** Add CLI commands, TUI screens, and MCP tools for the new
governance objects (charter, success criteria, gates, decision).

**Why:** The new governance objects need to be accessible through the
existing interface surfaces.

**How:**
- CLI: `enterprise pilot charter/create`, `pilot criteria lock`,
  `pilot gate evaluate`, `pilot decide`
- TUI: Add governance screen (charter, criteria, gates, decision)
- MCP: `create_pilot_charter`, `lock_success_criteria`,
  `evaluate_gate`, `create_decision_record`

**Effort:** Medium — wiring to existing CLI/TUI/MCP patterns.

**Files affected:** `src/cli/main.py`, `src/tui/app.py`,
`src/mcp_server/server.py`

### T1 summary

| Item | Effort | Files |
|---|---|---|
| T1.1 Pilot identity binding | Small | `pilot_configuration.py`, `service.py` |
| T1.2 Success criteria schema + locking | Medium | `pilot_configuration.py`, `service.py` |
| T1.3 Gate records | Medium | `gate_record.py` (new), `service.py` |
| T1.4 Decision record | Small | `decision_record.py` (new), `service.py` |
| T1.5 Pilot state machine | Small | `pilot_state.py` (new), `service.py` |
| T1.6 CLI/TUI/MCP surfaces | Medium | `main.py`, `app.py`, `server.py` |

**Total T1 effort:** ~6 items, mostly small-medium. No new analytical
capability — all governance/canon layer.

---

## T2: First real customer pilot

> Required before onboarding the first real customer.

### T2.1 — Real external reference field

**What:** Obtain or construct an external reference field that is NOT
derived from the pilot cohort itself.

**Why:** The current reference field is synthetic, derived from the
acme_50 cohort. Benchmarking compares operators against themselves.
For a real customer, an external reference is needed for valid
benchmarking.

**How:**
- Construct a reference field from aggregated, anonymized data across
  multiple cohorts (with consent and governance)
- OR obtain a public reference field from a benchmark source
- Version the reference field and record its provenance

**Effort:** Medium-High — requires data aggregation, governance, and
validation.

### T2.2 — Real governance gate enforcement

**What:** Enforce governance gates (purpose, disclosure, consent) for
real customer data, not just demo bypass.

**Why:** The demo bypasses governance gates (`skip_governance=True`).
Real customer pilots require purpose limitation, employee disclosure,
and consent to be satisfied before ingestion.

**How:**
- Remove `skip_governance=True` bypass for non-synthetic pilots
- Implement consent recording workflow
- Implement employee disclosure acknowledgment process
- Implement purpose limitation registration

**Effort:** Medium — gates are implemented, need real workflow
integration.

### T2.3 — Persistent pilot state

**What:** Persist pilot state, charter, success criteria, gates, and
decision records to SQLite (not just in-memory).

**Why:** The demo uses in-memory storage. Real pilots need persistence
to survive service restarts and support audit.

**How:**
- Add pilot state, charter, criteria, gates, decisions tables to
  `SQLiteRepository`
- Add load/save methods for each governance object
- Add `--persist` flag to CLI pilot commands

**Effort:** Medium — `SQLiteRepository` exists, needs new tables.

### T2.4 — Cross-system identity resolution

**What:** Real cross-system identity mapping (e.g., mapping
"alice@company.com" in ChatGPT to canonical "alice").

**Why:** The demo uses single-system pseudonymous IDs. Real customers
have operators across multiple systems with different identifiers.

**How:**
- `OperatorIdentity` registry already exists with conflict detection
- Need real identity mapping workflow (CSV upload, API, or manual)
- Need identity resolution validation

**Effort:** Small-Medium — `OperatorIdentity` exists, needs workflow.

### T2.5 — Real provider API ingestion

**What:** Test and validate live API ingestion with real provider APIs
(Claude, Codex, Groq).

**Why:** API adapters exist in stub mode. Live mode requires API keys
and has not been tested with real provider APIs.

**How:**
- Obtain API keys for each provider
- Test live ingestion with real data
- Handle rate limits, errors, retries
- Validate observation schema against real provider data

**Effort:** Medium — adapters exist, need real API testing.

### T2.6 — Replication workflow

**What:** Run replication on key findings as part of the standard
VERIFY stage.

**Why:** Replication capability exists (`ReplicationEngine`) but was
not run for ACME-001. Real pilots should replicate key findings to
test descriptive stability.

**How:**
- Add `replicate_key_findings()` to `PilotService`
- Define which findings are "key" (top 5 by confidence, or all
  findings that led to interventions)
- Add replication results to verification readout

**Effort:** Small — `ReplicationEngine` exists, needs integration.

### T2 summary

| Item | Effort | Priority |
|---|---|---|
| T2.1 Real external reference field | Medium-High | P1 |
| T2.2 Real governance gate enforcement | Medium | P1 |
| T2.3 Persistent pilot state | Medium | P1 |
| T2.4 Cross-system identity resolution | Small-Medium | P2 |
| T2.5 Real provider API ingestion | Medium | P1 |
| T2.6 Replication workflow | Small | P2 |

---

## T3: Scalable production deployment

> Required before deploying Pilot Mode to production at scale.

### T3.1 — Multi-pilot management

**What:** Support multiple concurrent pilots with isolation.

**Why:** The current architecture supports one pilot per `PilotService`
instance. Production needs multiple concurrent pilots.

**How:**
- `PilotService` takes `pilot_id` and loads only that pilot's data
- Pilot registry tracks all active pilots
- Pilot archive stores terminated pilots

**Effort:** Medium — architecture change to multi-pilot.

### T3.2 — Audit trail

**What:** Complete audit trail for all pilot actions (charter creation,
criteria locking, gate evaluation, decision recording).

**Why:** Production pilots require auditability for governance
compliance.

**How:**
- `GovernanceAuditLog` already exists — extend it to cover pilot
  governance actions
- All gate evaluations, criteria locking, and decisions are logged

**Effort:** Small — `GovernanceAuditLog` exists, needs extension.

### T3.3 — Access control

**What:** Role-based access control for pilot actions (charter creation,
criteria locking, gate evaluation, decision recording).

**Why:** Not all users should be able to create pilots, lock criteria,
or make closure decisions.

**How:**
- Define roles: pilot_creator, pilot_analyst, pilot_decision_authority
- Enforce role checks on governance actions

**Effort:** Medium — new role system.

### T3.4 — Pilot archive + institutional memory

**What:** Archive terminated pilots and build a cross-pilot findings
database.

**Why:** Institutional memory — past pilot findings should inform
future pilots. Currently no cross-pilot memory exists.

**How:**
- Pilot archive stores terminated pilots (charter, evidence, decision)
- Findings database indexes findings across pilots
- Cross-pilot pattern library identifies recurring patterns

**Effort:** Medium — new archive + database.

### T3.5 — Production transition checklist

**What:** Formal production transition checklist for DEPLOY closure
outcome.

**Why:** DEPLOY requires a production transition plan. Currently no
checklist exists.

**How:**
- Define production transition checklist (infrastructure, governance,
  monitoring, rollback)
- Integrate with DEPLOY decision record

**Effort:** Small — checklist definition.

### T3 summary

| Item | Effort | Priority |
|---|---|---|
| T3.1 Multi-pilot management | Medium | P2 |
| T3.2 Audit trail | Small | P2 |
| T3.3 Access control | Medium | P2 |
| T3.4 Pilot archive + institutional memory | Medium | P3 |
| T3.5 Production transition checklist | Small | P2 |

---

## Implementation order

```text
T1.1 Pilot identity binding
  ↓
T1.2 Success criteria schema + locking
  ↓
T1.3 Gate records  ←  depends on T1.2 (Gate 3 uses success criteria)
  ↓
T1.4 Decision record  ←  depends on T1.3 (decision references Gate 3)
  ↓
T1.5 Pilot state machine
  ↓
T1.6 CLI/TUI/MCP surfaces  ←  depends on T1.1–T1.5
  ↓
─── T1 complete: ACME reference can complete full lifecycle ───
  ↓
T2.1 Real external reference field
T2.2 Real governance gate enforcement
T2.3 Persistent pilot state
T2.5 Real provider API ingestion
  ↓
T2.4 Cross-system identity resolution
T2.6 Replication workflow
  ↓
─── T2 complete: first real customer pilot possible ───
  ↓
T3.1 Multi-pilot management
T3.2 Audit trail
T3.3 Access control
T3.4 Pilot archive + institutional memory
T3.5 Production transition checklist
  ↓
─── T3 complete: scalable production deployment ───
```

## What this plan does NOT include

- No new analytical capability (measurement, diagnosis, intervention,
  verification, reporting are all existing)
- No new metric definitions (5 canonical metrics are preserved)
- No new intervention catalog entries (12 entries are preserved)
- No changes to existing scoring formulas
- No changes to existing governance labels (DEVELOPMENTAL, ASSOCIATION,
  HYPOTHESIS)
- No signup/auth/billing/customer portals (per prompt constraints)
- No generic project-management infrastructure (per prompt constraints)
