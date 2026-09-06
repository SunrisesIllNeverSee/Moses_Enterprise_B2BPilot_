# FIRST_CUSTOMER_READINESS.md

> What must be true before Upsilon can responsibly begin its first
> real enterprise pilot.
>
> This document answers one narrow question. It is NOT a production
> readiness checklist. It is NOT a scalability checklist. It is the
> minimum bar for running a legitimate, governed pilot with a real
> customer's real data.

## Classification

Items are classified into four categories. The categories MUST NOT
be mixed — they represent different maturity targets.

| Category | Meaning |
|---|---|
| **BLOCKING** | Cannot run a legitimate pilot without this. No workaround acceptable. |
| **REQUIRED BUT MANUAL IS ACCEPTABLE** | Must be done, but can be done manually (document, spreadsheet, human process) for the first pilot. Platform automation not required. |
| **HARDENING RECOMMENDED** | Should be done before the first pilot if possible, but does not block if time-constrained. Risk is documented and accepted. |
| **POST-PILOT / SCALE REQUIREMENT** | Not needed for the first pilot. Required before scaling to multiple pilots or production deployment. |

---

## BLOCKING

These items MUST be resolved before the first real customer pilot.
No workaround is acceptable.

| # | Item | Why it blocks | Resolution |
|---|---|---|---|
| B1 | Governance gates enforced for real data | Real customer data cannot be ingested without consent, disclosure, and purpose limitation. The `skip_governance=True` bypass MUST NOT be used for real customers. | Remove `--skip-governance` for non-synthetic pilots. Use `enterprise ingest <provider> --purpose <purpose_id>` without the bypass flag. The gates exist (`src/governance/enforcement.py`) — they must be exercised. |
| B2 | Success criteria locked before measurement | Without locked criteria, Gate 3 cannot evaluate. No valid closure decision is possible. The pilot cannot terminate in a decision. | Lock success criteria in the Pilot Charter document BEFORE any telemetry collection. Record `locked_at` and `locked_by`. Manual is acceptable — the charter is a document, not yet a platform object. |
| B3 | Decision Authority identified and separate from Pilot Creator | The person who makes the closure decision must be different from the person who defines the pilot. Without separation of concerns, the decision is not independent. | Identify a Decision Authority before Gate 1. Record in the charter. |
| B4 | Employee disclosure and consent obtained | Real customer operators must be disclosed to (AI usage is being measured, developmental not personnel) and consent obtained per the consent model. Without this, the pilot is a privacy violation. | Customer discloses to employees before Day 1. Consent is recorded per the consent model (opt_in/opt_out/mandated). |
| B5 | Pseudonymous operator IDs | Real customer operators must not be identified by name or email in any Upsilon data structure. Operator IDs must be pseudonymous (e.g., `op_001`). | Map real identities to pseudonymous IDs before ingestion. Use `OperatorIdentity` for cross-system mapping. |
| B6 | No raw content stored | Observations store token counts and `raw_source_reference` pointers only. No prompts, responses, or other raw content is stored. | Confirm the ingestion path does not store raw content. The `Observation` dataclass (`src/domain/observation.py`) does not have a raw content field. |
| B7 | Provider telemetry access confirmed | The customer must be able to provide telemetry from at least one supported provider (ChatGPT, Claude, Codex, GitHub Copilot, Cursor). Without telemetry, there is no pilot. | Confirm access path (file export or API) during customer intake (`CUSTOMER_INTAKE.md`). |

> **7 BLOCKING items.** All are governance/process items, not
> platform code changes. The platform's analytical capability is
> ready — the governance and process layer must be enforced.

---

## REQUIRED BUT MANUAL IS ACCEPTABLE

These items MUST be done for the first pilot, but can be done
manually. Platform automation is not required.

| # | Item | Manual approach | Platform automation (future) |
|---|---|---|---|
| M1 | Pilot Charter created | Create as a document per `pilot/governance/PILOT_CHARTER.md`. Record all fields manually. | T1.1: `pilot_id` field on `PilotConfiguration` |
| M2 | Pilot ID assigned | Assign manually (e.g., `ACME-001` format). Thread through artifacts manually. | T1.1: `PilotId` value object |
| M3 | Success criteria locked | Record in the charter document with `locked_at` timestamp and `locked_by` identity. | T1.2: `SuccessCriteria` dataclass + `lock_success_criteria()` |
| M4 | Gate 1 evaluated | Decision Authority reviews the charter and selects LAUNCH/LAUNCH_WITH_CONDITIONS/DEFER/DECLINE. Record as a document. | T1.3: `evaluate_gate_1()` method |
| M5 | Gate 2 evaluated at checkpoints | Pilot Creator reviews data sufficiency, quality, participation, governance, protocol. Record as a document. | T1.3: `evaluate_gate_2()` method |
| M6 | Gate 3 evaluated | Decision Authority reviews evidence vs locked criteria. Selects STOP/EXTEND/EXPAND/DEPLOY. Record as a document. | T1.3: `evaluate_gate_3()` method |
| M7 | Decision Record created | Create as a document per `pilot/schemas/DECISION_RECORD_SCHEMA.md`. Mark `immutable: true`. | T1.4: `DecisionRecord` dataclass + `create_decision_record()` |
| M8 | Pilot state tracked | Track current stage manually (DEFINE/INSTRUMENT/BASELINE/DIAGNOSE/INTERVENE/VERIFY/READOUT/DECIDE). Record in a status document. | T1.5: `PilotStateMachine` |
| M9 | Baseline snapshot saved | Save baseline output to a timestamped file. Do not recompute after saving. | T2.1 (partial): immutable baseline snapshot mechanism |
| M10 | authorized_by recorded on interventions | Record in the intervention assignment document. CLI/MCP already enforces this for new assignments. | T1.6: `authorized_by` field on `Intervention` domain object |
| M11 | Artifact archive maintained | Store all stage artifacts as files in a pilot-specific directory. | T2.3: SQLite persistence for pilot governance objects |
| M12 | Audit log maintained | Record all governance actions (charter creation, criteria locking, gate evaluation, decision) in a manual audit log. | T3.2: Extend `GovernanceAuditLog` to cover pilot governance actions |

> **12 REQUIRED BUT MANUAL items.** All can be done with documents
> and spreadsheets for the first pilot. Platform automation is
> planned in T1/T2/T3 (see
> `pilot/implementation/PILOT_MODE_BUILD_PLAN.md`).

---

## HARDENING RECOMMENDED

These items should be done before the first pilot if possible, but
do not block if time-constrained. The risk of skipping must be
documented and accepted.

| # | Item | Risk if skipped | Hardening action |
|---|---|---|---|
| H1 | External reference field obtained | Benchmarking compares operators against themselves (synthetic reference derived from cohort). Percentile ranks are inflated. Benchmark class selection is all `peer`. | Construct or obtain an external reference field from aggregated anonymized data or a public benchmark source. See `pilot/PILOT_EXTERNAL_BENCHMARKS.md`. |
| H2 | API ingestion tested with real provider APIs | API adapters are in stub mode. Live mode has not been tested. Real provider telemetry may fail due to rate limits, schema drift, or unhandled errors. | Test live ingestion with each provider API before the pilot. Handle rate limits, errors, retries. See `pilot/implementation/HARDENING_PLAN.md` H4. |
| H3 | Cross-system identity mapping workflow | `OperatorIdentity` exists with conflict detection but no real mapping workflow. Real customers have operators across multiple systems with different identifiers. | Build identity mapping workflow (CSV upload, API, or manual) with validation. See `pilot/implementation/HARDENING_PLAN.md`. |
| H4 | Replication run on key findings | `ReplicationEngine` exists but is not integrated into standard verification. Findings are less robust without replication. | Run `PilotService.replicate_finding()` on top 5 findings during VERIFY. See `pilot/implementation/PILOT_MODE_BUILD_PLAN.md` T2.6. |
| H5 | Persistent pilot state (SQLite) | Demo uses in-memory `DemoRepository`. Pilot state is lost on restart. Governance objects are not auditable across sessions. | Use `SQLiteRepository` with `--persist` flag. Add pilot governance tables. See `pilot/implementation/HARDENING_PLAN.md` H3. |

> **5 HARDENING RECOMMENDED items.** If skipped, document the risk
> and proceed. The pilot can still produce valid evidence — the
> risk is to benchmarking validity, ingestion reliability, and
> state persistence, not to governance validity.

---

## POST-PILOT / SCALE REQUIREMENT

These items are NOT needed for the first pilot. They are required
before scaling to multiple concurrent pilots or production
deployment.

| # | Item | When needed | Build plan item |
|---|---|---|---|
| S1 | Multi-pilot management | When running 2+ concurrent pilots | T3.1 |
| S2 | Access control (role system) | When multiple users access the platform | T3.3 |
| S3 | Pilot archive + institutional memory | When terminated pilots should inform future pilots | T3.4 |
| S4 | Cross-pilot findings database | When patterns recur across pilots | T3.4 |
| S5 | Production transition checklist | When DEPLOY outcome is selected | T3.5 |
| S6 | Audit trail (automated) | When manual audit log is insufficient for compliance | T3.2 |
| S7 | Self-service signup | NOT REQUIRED for pilot legitimacy. Pilots are concierge/high-touch. | Not in scope |
| S8 | Billing system | NOT REQUIRED for pilot legitimacy. Commercial terms are handled outside the platform. | Not in scope |
| S9 | Customer portal | NOT REQUIRED for pilot legitimacy. Customer interaction is via the Upsilon operator. | Not in scope |

> **9 POST-PILOT / SCALE items.** None block the first pilot.
> Self-service signup, billing, and customer portal are explicitly
> NOT first-pilot blockers — pilots are concierge/high-touch, and
> commercial terms are handled outside the platform.

---

## Summary

| Category | Count | Blocks first pilot? |
|---|---|---|
| BLOCKING | 7 | Yes |
| REQUIRED BUT MANUAL IS ACCEPTABLE | 12 | No (manual workaround) |
| HARDENING RECOMMENDED | 5 | No (risk documented) |
| POST-PILOT / SCALE REQUIREMENT | 9 | No |

**The first real customer pilot can begin when:**
1. All 7 BLOCKING items are resolved (governance/process, not code)
2. All 12 REQUIRED BUT MANUAL items have a manual approach defined
3. HARDENING RECOMMENDED items are addressed or their risk is
   documented and accepted

**The platform's analytical capability is ready.** The 676-test suite
passes. The 5 canonical metrics, 12-entry intervention catalog, 6
pattern detectors, pre/post verification, outcome correlation,
reporting, and governance enforcement are all implemented and
demonstrated via the ACME-001 reference pilot.

**The gap is governance and process, not code.** The BLOCKING items
are about enforcing existing governance gates, locking success
criteria, obtaining consent, and protecting privacy — not about
building new analytical capability.

## What this document does NOT do

- Does not define the pilot lifecycle (see `pilot/PILOT_LIFECYCLE.md`)
- Does not define gates (see `pilot/governance/DECISION_GATES.md`)
- Does not define the build plan (see
  `pilot/implementation/PILOT_MODE_BUILD_PLAN.md`)
- Does not define the gap register (see
  `pilot/implementation/GAP_REGISTER.md`)
- Does not classify self-service/billing/portal as blockers (per
  `pilot/context/DECISION_LOG.md` — pilots are concierge)
