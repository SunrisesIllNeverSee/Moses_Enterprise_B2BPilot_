# ACME-001 — Pilot Charter

> **PARTIAL** — charter fields exist in the platform's `PilotConfiguration`
> but no formal charter with locked success criteria exists. This document
> is a retrospective construction from the demo data.

## Identity

| Field | Value | Source |
|---|---|---|
| Pilot ID | ACME-001 | **Illustrative** — no pilot_id field exists in platform |
| Name | Acme 50 AI Workforce Operating Baseline | `Cohort.name` = "Acme 50" |
| Created at | 2026-08-17 | `demo_manifest.json` (demo data generation date) |
| Created by | demo_generator | `scripts/generate_demo_data.py` |
| Authorized by | (not recorded) | **MISSING** — no authorized_by on charter |

## Enterprise

| Field | Value | Source |
|---|---|---|
| Tenant ID | acme | `Cohort.tenant_id` |
| Enterprise name | Acme | **Illustrative** — derived from tenant_id |

## Population

| Field | Value | Source |
|---|---|---|
| Cohort ID | acme_50 | `Cohort.cohort_id` |
| Operator count | 50 | `Cohort.operators` |
| Operator IDs | op_001 through op_050 | `Cohort.operator_ids` |
| Teams | 6 (Product Engineering, Product/Design, Data/Analytics, Platform/Infrastructure, Operations/GTM, Customer Engineering/Support) | `PilotService.teams` |
| Selection criteria | (not recorded) | **MISSING** — operators enumerated, not described by criteria |

## Duration

| Field | Value | Source |
|---|---|---|
| Window start | 2026-07-01 | `Cohort.window_start` |
| Window end | 2026-07-30 | `Cohort.window_end` |
| Window days | 30 | `CohortConfig.window_days` (default) |
| Baseline days | 30 | `demo_manifest.json` |
| Post days | 14 | `demo_manifest.json` |

## Scope

| Field | Value | Source |
|---|---|---|
| Eval families | EVAL-001 through EVAL-015 (all implemented) | `src/config/eval_registry.py` — all 15 marked `implemented: True, implementation_status: "full"` |
| Commercial pilot ID | 1 (AI Workforce Operating Baseline) | **Illustrative** — matches demo characteristics |
| Deployment level | 1 (baseline) | **Illustrative** — matches commercial pilot #1 |

## Objectives

| Field | Value | Source |
|---|---|---|
| Pilot question | "What does our AI workforce actually look like?" | `CommercialPilot.question` for pilot #1 |
| Best buyer | Head of AI / Transformation | `CommercialPilot.best_buyer` for pilot #1 |

## Success criteria

> **CANNOT BE COMPLETED.** The platform does not implement success-criteria
> locking. No success criteria were defined before measurement. This is
> a fundamental gap — without locked success criteria, Gate 3 cannot
> compare evidence against criteria.

| Field | Value | Status |
|---|---|---|
| Criteria | (not defined) | **MISSING** |
| Locked at | (not locked) | **MISSING** |
| Locked by | (not recorded) | **MISSING** |

**Illustrative criteria** (what should have been locked before measurement):

| ID | Metric | Threshold | Direction | Aggregation | Rationale |
|---|---|---|---|---|---|
| SC-001 | cohort_median_leverage | 10.0 | above | cohort_median | Establishes meaningful value extraction per input token |
| SC-002 | eligible_operator_rate | 0.80 | above | cohort | Ensures sufficient data quality |
| SC-003 | divergence_rate | 0.30 | below | cohort | High divergence indicates inconsistent patterns |

**Measured against illustrative criteria:**
- SC-001: median leverage = 12.177 → MET (above 10.0)
- SC-002: eligible rate = 50/50 = 1.0 → MET (above 0.80)
- SC-003: divergence rate = (5+3+12)/50 = 0.40 → MISSED (above 0.30)

> These criteria were NOT locked before measurement. This comparison is
> illustrative only and would be invalid for a real Gate 3 evaluation.

## Governance

| Field | Value | Source |
|---|---|---|
| Decision use default | DEVELOPMENTAL | `GovernanceConfig.decision_use_default` |
| Privacy class | pseudonymous_synthetic | `GovernanceConfig.privacy_class` |
| Synthetic | true | `GovernanceConfig.synthetic` |
| Purpose ID | (not set) | **MISSING** — no purpose_id for demo |
| Consent model | (not set) | **MISSING** — no consent model for demo |

## Configuration reference

| Field | Value | Source |
|---|---|---|
| Metric registry version | 0.2 | `MetricRegistry.registry_version` |
| Reference field version | public_field_2026-08-17 | `ReferencePopulation.version` |
| Config JSON | (not saved as separate file) | `PilotConfiguration` is in-memory for demo |

## Gate 1 result

> **CANNOT BE COMPLETED.** No pilot-level Gate 1 (Launch Readiness)
> exists in the platform.

| Field | Value | Status |
|---|---|---|
| Outcome | (not evaluated) | **MISSING** |
| Conditions | (not evaluated) | **MISSING** |
| Evaluated at | (not evaluated) | **MISSING** |
| Evaluated by | (not evaluated) | **MISSING** |

**Illustrative Gate 1 result:** LAUNCH_WITH_CONDITIONS
- Condition 1: Lock success criteria before any future pilot
- Condition 2: Set authorized_by on charter
- Condition 3: Define purpose_id and consent model for governance gates

## What this charter reveals

1. The platform has the **data structures** for most charter fields
   (cohort, operators, window, eval families, governance metadata).
2. The platform is **missing** pilot_id, enterprise_name, selection_criteria,
   success criteria (with locking), authorized_by (at charter level),
   purpose_id, consent model, and Gate 1 result.
3. The **success criteria gap is critical** — without locked criteria,
   the pilot cannot produce a valid closure decision.
