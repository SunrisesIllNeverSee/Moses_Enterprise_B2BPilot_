# PILOT_CHARTER.md

> The immutable definition record for an Upsilon Enterprise Pilot.
>
> Created at the DEFINE stage. Locked before measurement begins. Not
> modified after launch without a documented amendment.

## Purpose

The Pilot Charter is the governing document that bounds the pilot. It
records what is being evaluated, why, for whom, for how long, with what
success criteria, and under what governance constraints. It is the
artifact that Gate 1 (LAUNCH READINESS) evaluates.

## Structure

A Pilot Charter contains:

### 1. Identity

| Field | Description |
|---|---|
| `pilot_id` | Unique identifier (e.g., `ACME-001`) |
| `enterprise` | Tenant / organization name |
| `cohort_id` | Cohort identifier (e.g., `acme_50`) |
| `created_at` | Creation timestamp |
| `created_by` | Author identity |
| `authorized_by` | Approver identity (required for launch) |

### 2. Scope

| Field | Description |
|---|---|
| `population` | Operator set (count, selection criteria, IDs if enumerated) |
| `duration` | Window start, window end, total days |
| `eval_families` | Selected EVAL-001–EVAL-015 IDs |
| `commercial_pilot_id` | If from a template (1–12) |
| `deployment_level` | 1 (baseline), 2 (intervention), 3 (production) |

### 3. Question

| Field | Description |
|---|---|
| `pilot_question` | The decision this pilot will inform |
| `best_buyer` | The role that benefits most (from commercial pilot template) |

### 4. Success criteria

| Field | Description |
|---|---|
| `criteria` | List of measurable criteria, each with: metric, threshold, direction, rationale |
| `locked_at` | Timestamp when criteria were locked (must be before measurement) |
| `locked_by` | Identity that locked the criteria |

> Success criteria MUST be locked before any measurement. If criteria
> are not locked, the pilot cannot pass Gate 1.

### 5. Governance

| Field | Description |
|---|---|
| `decision_use_default` | DEVELOPMENTAL (never PERSONNEL) |
| `privacy_class` | pseudonymous_synthetic (demo) or pseudonymous_real (production) |
| `synthetic` | Boolean — true for demo, false for real customer |
| `purpose_id` | Processing purpose (for governance gates) |
| `consent_model` | opt_in / opt_out / mandated (for governance gates) |

### 6. Configuration reference

| Field | Description |
|---|---|
| `config_json` | The full `PilotConfiguration` JSON (saved separately) |
| `metric_registry_version` | The metric registry version used (e.g., 0.2) |
| `reference_field_version` | The reference population version |

### 7. Gate 1 result

| Field | Description |
|---|---|
| `gate_1_outcome` | LAUNCH / LAUNCH_WITH_CONDITIONS / DEFER / DECLINE |
| `gate_1_conditions` | If LAUNCH_WITH_CONDITIONS, what conditions must be met |
| `gate_1_evaluated_at` | Timestamp |
| `gate_1_evaluated_by` | Evaluator identity |

## Amendment policy

The charter is immutable after Gate 1 approval. Any change requires:
1. A documented amendment with rationale
2. Re-evaluation of Gate 1
3. Re-approval by the authorized approver

Success criteria, once locked, cannot be amended. If the criteria are
wrong, the pilot must be STOPPED and a new pilot chartered.

## Relationship to existing implementation

| Charter field | Existing implementation | Status |
|---|---|---|
| Identity | `PilotConfiguration.config_id`, `created_by` | Partial — no `pilot_id` or `authorized_by` at charter level |
| Scope | `CohortConfig`, `EvalFamilySelection`, `deployment_level` | Existing — fully configurable |
| Question | `CommercialPilot.question` | Existing — from commercial pilot template |
| Success criteria | **NOT IMPLEMENTED** | Missing — no success-criteria schema or locking mechanism |
| Governance | `GovernanceConfig` | Existing — synthetic, decision_use, privacy_class, authorized_by |
| Config reference | `PilotConfiguration.to_json()` | Existing — full config saved as JSON |
| Gate 1 result | **NOT IMPLEMENTED** | Missing — no pilot-level launch readiness gate |

See `schemas/PILOT_CHARTER_SCHEMA.md` for the formal schema.
