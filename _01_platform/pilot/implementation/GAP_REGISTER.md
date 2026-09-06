# GAP_REGISTER.md

> The complete register of gaps between the current platform and the
> canonical Upsilon Enterprise Pilot protocol.
>
> Each gap is classified by type and severity, mapped to a pilot stage,
> and assigned to one of three maturity targets. The three maturity
> targets are kept separate — they must not be mixed.

## Gap classification

| Type | Description |
|---|---|
| CANON | Missing canonical definition/governance artifact (specification gap) |
| RUNTIME | Missing runtime behavior (state tracking, persistence, multi-pilot) |
| DATA | Missing or synthetic data structure/content (reference field, baseline snapshot, demo fields) |
| GOVERNANCE | Missing governance enforcement or process (gates, consent, audit, archive) |
| UX | Missing CLI/TUI/MCP surface for an existing or required capability |
| CUSTOMER_ONBOARDING | Missing workflow for real-customer onboarding (identity, consent) |
| SECURITY | Missing access control or authorization for sensitive actions |
| PRIVACY | Missing privacy enforcement for real-customer data |
| EVIDENCE | Missing evidence artifact, record, or integration into the evidence chain |
| REPORTING | Missing reporting or readout capability |
| PRODUCTION_HARDENING | Capability exists but needs production hardening for real-customer use |

## Severity scale

| Severity | Meaning |
|---|---|
| CRITICAL | Blocks the maturity target entirely — cannot proceed without it |
| HIGH | Blocks a required lifecycle stage or gate |
| MEDIUM | Degrades lifecycle completeness but does not block |
| LOW | Quality/polish — does not block any stage |

---

## Required before ACME reference completion

> These gaps must be closed before the ACME-001 reference pilot can be
> claimed as completing the full lifecycle (including DECIDE). They are
> CANON, GOVERNANCE, RUNTIME, UX, and EVIDENCE gaps — no new analytical
> capability is required.

| ID | Gap | Stage | Existing support | Severity | Type | Required action | Blocking real pilot? |
|---|---|---|---|---|---|---|---|
| GAP-001 | No pilot_id — pilots have no unique identity | DEFINE | `PilotConfiguration.config_id` exists but is a config ID, not a pilot identity; `PilotService` has no pilot identity | HIGH | CANON | Add `PilotId` value object + thread through `PilotConfiguration` and `PilotService` | Yes (T2) — evidence cannot be bound to a specific pilot |
| GAP-002 | No success criteria schema | DEFINE | `PilotConfiguration` has eval family selections but no success criteria with thresholds | HIGH | CANON | Define `SuccessCriterion` + `SuccessCriteria` dataclasses | Yes (T2) — Gate 3 cannot evaluate without criteria |
| GAP-003 | No success criteria locking mechanism | DEFINE | No `locked_at`/`locked_by` fields; no `lock_success_criteria()` method | CRITICAL | GOVERNANCE | Add `lock_success_criteria()` method that freezes criteria before measurement | Yes (T2) — without locked criteria, Gate 3 is invalid |
| GAP-004 | No Gate 1 (Launch Readiness) | DEFINE | `ConfigValidator.validate()` produces errors/warnings but not gate outcomes | HIGH | GOVERNANCE | Add `evaluate_gate_1()` returning LAUNCH/LAUNCH_WITH_CONDITIONS/DEFER/DECLINE | Yes (T2) — no formal launch authorization |
| GAP-005 | No Gate 2 (Pilot Health) | INTERVENE / VERIFY | `pilot_status()` provides snapshot but no gate evaluation | MEDIUM | GOVERNANCE | Add `evaluate_gate_2()` returning CONTINUE/ADJUST/ESCALATE/TERMINATE | No — pilot can proceed without health gate, but experiment validity is at risk |
| GAP-006 | No Gate 3 (Closure / Scale) | DECIDE | No pilot-level closure gate; no success criteria to evaluate against | CRITICAL | GOVERNANCE | Add `evaluate_gate_3()` returning STOP/EXTEND/EXPAND/DEPLOY | Yes (T2) — pilot cannot terminate in a decision |
| GAP-007 | No decision record | DECIDE | No `DecisionRecord` schema, no closure outcome, no STOP/EXTEND/EXPAND/DEPLOY | CRITICAL | CANON | Define `DecisionRecord` dataclass + `create_decision_record()` method | Yes (T2) — closure decision is not documented or immutable |
| GAP-008 | No pilot state machine | ALL | No `PilotState` enum, no state tracking, no transition enforcement | HIGH | RUNTIME | Define `PilotState` enum + `PilotStateMachine` with transition rules | Yes (T2) — cannot enforce stage order or prevent skipping |
| GAP-009 | No pilot-level gate records | GATES | Operator-level `GateResult` exists but pilot-level `GateRecord` does not | HIGH | EVIDENCE | Define `GateRecord` dataclass; record gate outcomes as immutable evidence | Yes (T2) — gate outcomes are not auditable |
| GAP-010 | No CLI/TUI/MCP surface for governance objects | ALL | No commands for charter creation, criteria locking, gate evaluation, decision recording | HIGH | UX | Add CLI `pilot charter/criteria/gate/decide`; TUI governance screen; MCP tools | No — governance objects can be created programmatically, but operator access is missing |
| GAP-025 | No pilot question on individual configs | DEFINE | `CommercialPilot.question` exists on templates but not on individual `PilotConfiguration` | MEDIUM | CANON | Add `pilot_question` field to `PilotConfiguration` | No — does not block, but charter is incomplete without it |
| GAP-026 | No enterprise_name field | DEFINE | `Cohort.name` is cohort name, not enterprise name | LOW | CANON | Add `enterprise_name` field to `PilotConfiguration` or `Cohort` | No — does not block, but charter is incomplete without it |
| GAP-027 | No selection_criteria field | DEFINE | Operators are enumerated, not described by selection criteria | LOW | CANON | Add `selection_criteria` field to `PilotConfiguration` | No — does not block, but charter is incomplete without it |
| GAP-028 | No extension period tracking | DECIDE | No `extension_periods` field for EXTEND closure outcome | MEDIUM | CANON | Add `extension_periods` list to `DecisionRecord` or `PilotConfiguration` | No — does not block initial pilot, but blocks valid EXTEND |
| GAP-029 | No finding_id on detected patterns | DIAGNOSE | `DetectedPattern` has no explicit ID; `Diagnosis` has `diagnosis_id` | LOW | EVIDENCE | Add `finding_id` field to `DetectedPattern` | No — does not block, but evidence citation is weakened |
| GAP-030 | No claim_type field on findings | DIAGNOSE | ASSOCIATION is hardcoded in governance, not an explicit field on findings | LOW | EVIDENCE | Add `claim_type` field to findings (default ASSOCIATION) | No — does not block, but evidence semantics are implicit |

**T1 summary: 16 gaps.** 3 CRITICAL, 6 HIGH, 3 MEDIUM, 4 LOW. All are
CANON/GOVERNANCE/RUNTIME/UX/EVIDENCE — no new analytical capability.

---

## Required before first real customer pilot

> These gaps must be closed before onboarding the first real customer.
> They include DATA, PRIVACY, PRODUCTION_HARDENING, and
> CUSTOMER_ONBOARDING gaps. T1 must be complete first — governance
> objects must exist before they can be persisted and enforced.

| ID | Gap | Stage | Existing support | Severity | Type | Required action | Blocking real pilot? |
|---|---|---|---|---|---|---|---|
| GAP-011 | No immutable baseline snapshot | BASELINE | Baseline is recomputed each `PilotService` instantiation; no timestamped immutable snapshot | MEDIUM | DATA | Add timestamped baseline snapshot mechanism; persist snapshot at BASELINE completion | Yes — baseline must be immutable for valid pre/post comparison |
| GAP-012 | Synthetic reference field | BASELINE / DIAGNOSE | `ReferencePopulation` is derived from acme_50 cohort itself, not external | HIGH | DATA | Construct or obtain an external reference field (aggregated anonymized or public) | Yes — benchmarking is self-referential without it |
| GAP-013 | Governance gates bypassed in demo | INSTRUMENT | `skip_governance=True` for demo; purpose/disclosure/consent not enforced | CRITICAL | PRIVACY | Remove bypass for non-synthetic pilots; enforce consent/disclosure/purpose gates | Yes — real customer data cannot be ingested without consent |
| GAP-014 | No persistent pilot state | ALL | Demo uses in-memory `DemoRepository`; `SQLiteRepository` exists but not used for pilot governance objects | HIGH | RUNTIME | Add pilot state/charter/criteria/gates/decisions tables to `SQLiteRepository` | Yes — pilot state is lost on restart; governance objects are not auditable |
| GAP-015 | No cross-system identity workflow | INSTRUMENT | `OperatorIdentity` exists with conflict detection but no real mapping workflow | MEDIUM | CUSTOMER_ONBOARDING | Build identity mapping workflow (CSV upload, API, or manual) with validation | Yes — real customers have operators across multiple systems |
| GAP-016 | API ingestion not tested with real APIs | INSTRUMENT | API adapters exist in stub mode; live mode not tested | HIGH | PRODUCTION_HARDENING | Test live ingestion with real provider APIs; handle rate limits, errors, retries | Yes — real provider telemetry may fail without testing |
| GAP-017 | Replication not integrated into VERIFY | VERIFY | `ReplicationEngine` exists but not run as part of standard verification | MEDIUM | EVIDENCE | Add `replicate_key_findings()` to `PilotService`; run as part of VERIFY stage | No — pilot can proceed without replication, but findings are less robust |
| GAP-024 | authorized_by not recorded on demo interventions | INTERVENE | CLI/MCP enforces authorized_by for new assignments but demo data does not include it | LOW | DATA | Add `authorized_by` to demo intervention records; enforce on domain object | No — does not block real pilots (enforced at assignment time), but demo is inconsistent |

**T2 summary: 8 gaps.** 1 CRITICAL, 3 HIGH, 3 MEDIUM, 1 LOW.

---

## Required before scalable production deployment

> These gaps must be closed before deploying Pilot Mode to production at
> scale. They include RUNTIME, GOVERNANCE, SECURITY, and EVIDENCE gaps.
> T1 and T2 must be complete first.

| ID | Gap | Stage | Existing support | Severity | Type | Required action | Blocking real pilot? |
|---|---|---|---|---|---|---|---|
| GAP-018 | No multi-pilot management | ALL | One pilot per `PilotService` instance; no pilot registry | HIGH | RUNTIME | `PilotService` takes `pilot_id` and loads only that pilot's data; pilot registry tracks all active pilots | No (single pilot) — blocks scale, not first pilot |
| GAP-019 | No pilot-level audit trail | ALL | `GovernanceAuditLog` exists but does not cover pilot governance actions | MEDIUM | GOVERNANCE | Extend `GovernanceAuditLog` to cover charter/criteria/gate/decision actions | No — blocks auditability at scale, not first pilot |
| GAP-020 | No access control for governance actions | ALL | No role system for charter/criteria/gate/decision actions | HIGH | SECURITY | Define roles (pilot_creator, pilot_analyst, pilot_decision_authority); enforce role checks | No — blocks scale, not first pilot (single-operator trust model) |
| GAP-021 | No pilot archive | DECIDE | No archive for terminated pilots; no institutional memory | MEDIUM | GOVERNANCE | Build pilot archive storing terminated pilots (charter, evidence, decision) | No — blocks institutional memory, not first pilot |
| GAP-022 | No cross-pilot findings database | DECIDE | No findings database; each pilot is independent | LOW | EVIDENCE | Build findings database indexing findings across pilots; cross-pilot pattern library | No — blocks institutional memory, not first pilot |
| GAP-023 | No production transition checklist | DECIDE | `deployment_level` exists but no transition checklist or deployment gate | MEDIUM | CANON | Define production transition checklist; integrate with DEPLOY decision record | No — blocks DEPLOY outcome, not first pilot |

**T3 summary: 6 gaps.** 2 HIGH, 3 MEDIUM, 1 LOW.

---

## Priority distribution

| Maturity target | Count | Gap IDs |
|---|---:|---|
| T1 (ACME reference completion) | 16 | GAP-001–010, GAP-025, GAP-026, GAP-027, GAP-028, GAP-029, GAP-030 |
| T2 (First real customer pilot) | 8 | GAP-011, GAP-012, GAP-013, GAP-014, GAP-015, GAP-016, GAP-017, GAP-024 |
| T3 (Scalable production deployment) | 6 | GAP-018, GAP-019, GAP-020, GAP-021, GAP-022, GAP-023 |

**Total: 30 gaps.**

## Type distribution

| Type | Count | Gap IDs |
|---|---:|---|
| CANON | 8 | GAP-001, GAP-002, GAP-007, GAP-023, GAP-025, GAP-026, GAP-027, GAP-028 |
| RUNTIME | 3 | GAP-008, GAP-014, GAP-018 |
| DATA | 3 | GAP-011, GAP-012, GAP-024 |
| GOVERNANCE | 6 | GAP-003, GAP-004, GAP-005, GAP-006, GAP-019, GAP-021 |
| UX | 1 | GAP-010 |
| CUSTOMER_ONBOARDING | 1 | GAP-015 |
| SECURITY | 1 | GAP-020 |
| PRIVACY | 1 | GAP-013 |
| EVIDENCE | 5 | GAP-009, GAP-017, GAP-022, GAP-029, GAP-030 |
| REPORTING | 0 | — |
| PRODUCTION_HARDENING | 1 | GAP-016 |

**Total: 30 gaps.** (8+3+3+6+1+1+1+1+5+0+1 = 30)

## Severity distribution

| Severity | Count | Gap IDs |
|---|---:|---|
| CRITICAL | 4 | GAP-003, GAP-006, GAP-007, GAP-013 |
| HIGH | 11 | GAP-001, GAP-002, GAP-004, GAP-008, GAP-009, GAP-010, GAP-012, GAP-014, GAP-016, GAP-018, GAP-020 |
| MEDIUM | 9 | GAP-005, GAP-011, GAP-015, GAP-017, GAP-019, GAP-021, GAP-023, GAP-025, GAP-028 |
| LOW | 6 | GAP-022, GAP-024, GAP-026, GAP-027, GAP-029, GAP-030 |

**Total: 30 gaps.** (4+11+9+6 = 30)

## Key insight

> **69% of T1 gaps are CANON or GOVERNANCE** (11 of 16) — they require
> specification and binding, not new analytical capability. The platform's
> measurement, diagnostic, intervention, verification, and reporting
> capabilities are strong. The gaps are in the governance layer that
> binds these capabilities into a formal pilot lifecycle.
>
> The T2 gaps are primarily DATA, PRIVACY, and PRODUCTION_HARDENING —
> they require real data, real consent enforcement, and real API testing.
>
> The T3 gaps are RUNTIME, SECURITY, and GOVERNANCE — they require
> multi-pilot architecture, access control, and audit infrastructure for
> scale.
