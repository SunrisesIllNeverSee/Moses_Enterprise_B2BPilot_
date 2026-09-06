# PILOT_OBJECT.md

> The conceptual Pilot object — the canonical structure that binds a
> pilot's identity, scope, evidence, and decisions.
>
> Per Phase 5: this is a specification, NOT an implementation. The
> schema distinguishes existing field/model, reusable field/model,
> extension required, and genuinely new structure.

## Conceptual structure

```text
PILOT
│
├── identity
├── enterprise
├── population
├── scope
├── duration
├── objectives
├── success_criteria
├── instrumentation
├── reference_field
├── observations
├── baseline
├── findings
├── interventions
├── verification
├── gates
├── decisions
├── evidence
├── lineage
└── readout
```

## Field-by-field analysis

### identity

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `pilot_id` | string | **GENUINELY NEW** | No pilot_id field exists. `PilotConfiguration.config_id` is a config ID, not a pilot identity. |
| `name` | string | Reusable | `PilotConfiguration.name` |
| `created_at` | string (ISO datetime) | Reusable | `PilotConfiguration.created_at` |
| `created_by` | string | Reusable | `PilotConfiguration.created_by` |
| `authorized_by` | string | Reusable | `GovernanceConfig.authorized_by` |

### enterprise

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `tenant_id` | string | Reusable | `CohortConfig.tenant_id`, `Cohort.tenant_id` |
| `enterprise_name` | string | **EXTENSION REQUIRED** | `Cohort.name` exists but is cohort name, not enterprise name |

### population

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `cohort_id` | string | Reusable | `Cohort.cohort_id`, `CohortConfig.cohort_id` |
| `operator_ids` | list[string] | Reusable | `Cohort.operator_ids` |
| `operator_count` | int | Reusable | `Cohort.operators` (count) |
| `teams` | list[string] | Reusable | `Operator.team`, `teams.json` |
| `selection_criteria` | string | **GENUINELY NEW** | No selection criteria field (operators are enumerated, not described by criteria) |

### scope

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `eval_families` | list[string] | Reusable | `PilotConfiguration.eval_families` (list of `EvalFamilySelection`) |
| `commercial_pilot_id` | string (optional) | Reusable | `PilotConfiguration.commercial_pilot_id` |
| `deployment_level` | int (1/2/3) | Reusable | `PilotConfiguration.deployment_level` |
| `pilot_question` | string | **EXTENSION REQUIRED** | `CommercialPilot.question` exists on templates but not on individual pilot configs |

### duration

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `window_start` | date | Reusable | `Cohort.window_start` |
| `window_end` | date | Reusable | `Cohort.window_end` |
| `window_days` | int | Reusable | `CohortConfig.window_days` |
| `extension_periods` | list[dict] | **GENUINELY NEW** | No extension tracking (needed for EXTEND closure outcome) |

### objectives

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `pilot_question` | string | **EXTENSION REQUIRED** | (see scope above) |
| `best_buyer` | string | **EXTENSION REQUIRED** | `CommercialPilot.best_buyer` exists on templates but not on individual configs |

### success_criteria

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `criteria` | list[SuccessCriterion] | **GENUINELY NEW** | No success criteria schema exists. See `SUCCESS_CRITERIA.md`. |
| `locked_at` | string (ISO datetime) | **GENUINELY NEW** | No locking mechanism |
| `locked_by` | string | **GENUINELY NEW** | No locking mechanism |

### instrumentation

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `providers` | list[string] | Reusable | `Observation.platform` (per-observation); `pilot_status().providers` |
| `ingest_adapters` | list[string] | Reusable | `src/ingest/` adapters (fixture, claude, codex, github, api-*) |
| `observation_count` | int | Reusable | `pilot_status().observation_count` |
| `identity_mappings` | list[dict] | Reusable | `OperatorIdentity` registry |

### reference_field

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `reference_id` | string | Reusable | `ReferencePopulation.reference_id` |
| `version` | string | Reusable | `ReferencePopulation.version` |
| `distributions` | dict | Reusable | `ReferencePopulation.distributions` (p0–p100 per metric) |
| `synthetic` | bool | Reusable | `ReferencePopulation.synthetic` |

### observations

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `observations` | list[Observation] | Existing | `Observation` domain object, `DemoRepository.observations` |
| `data_quality` | dict | Existing | `data_quality_summary()` — OK/WARNING/BLOCKING counts |
| `eligibility` | dict[str, QualityResult] | Existing | `eligibility()` / `check_cohort_eligibility()` |

### baseline

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `measurements` | dict[str, list[Measurement]] | Existing | `score_cohort()` — operator_id → list[Measurement] |
| `percentiles` | dict[str, dict[str, Measurement]] | Existing | `percentiles()` |
| `distributions` | dict[str, MetricDistribution] | Existing | `cohort_distributions()` |
| `composite_scores` | dict[str, CompositeScore] | Existing | `cohort_composite_scores()` |
| `snapshot_timestamp` | string | **GENUINELY NEW** | No baseline snapshot timestamp (needed for immutability) |

### findings

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `divergence_results` | list[DivergenceResult] | Existing | `divergence()` |
| `detected_patterns` | dict[str, list[DetectedPattern]] | Existing | `detect_cohort_patterns()` |
| `diagnoses` | dict[str, list[Diagnosis]] | Existing | `generate_cohort_diagnoses()` |
| `workflow_fit` | WorkflowFitReport | Existing | `workflow_fit_report()` |
| `org_topology` | dict | Existing | `org_topology()` |
| `benchmark_results` | list[dict] | Existing | `benchmark_cohort()` |

### interventions

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `interventions` | list[Intervention] | Existing | `PilotService.interventions` |
| `experiments` | list[dict] | Existing | `PilotService.experiments` |

### verification

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `verification_results` | list[VerificationResult] | Existing | `verify_all_interventions()` |
| `outcome_correlation` | dict | Existing | `outcome_correlation()` |
| `outcome_joins` | list[OutcomeJoinResult] | Existing | `join_outcomes()` |
| `replication_results` | list[ReplicationResult] | **EXTENSION REQUIRED** | `replicate_finding()` exists but returns single result, not a list per pilot |

### gates

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `operator_gates` | dict[str, list[GateResult]] | Existing | `evaluate_cohort_gates()` |
| `gate_1_result` | GateRecord | **GENUINELY NEW** | No pilot-level Gate 1 record |
| `gate_2_results` | list[GateRecord] | **GENUINELY NEW** | No pilot-level Gate 2 records |
| `gate_3_result` | GateRecord | **GENUINELY NEW** | No pilot-level Gate 3 record |

### decisions

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `decision_record` | DecisionRecord | **GENUINELY NEW** | No decision record exists |
| `closure_outcome` | enum (STOP/EXTEND/EXPAND/DEPLOY) | **GENUINELY NEW** | No closure outcome field |

### evidence

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `artifacts` | list[Artifact] | Existing | `PilotService.artifacts` |
| `lineages` | list[Lineage] | Existing | `PilotService.lineages` |
| `outcomes` | list[Outcome] | Existing | `PilotService.outcomes` |
| `readout_documents` | list[dict] | **EXTENSION REQUIRED** | Multiple report generators exist but no document registry per pilot |

### lineage

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `lineage_chains` | dict[str, dict] | Existing | `lineage_chain(operator_id)` |
| `lineage_summary` | dict | Existing | `lineage_summary()` |

### readout

| Field | Type | Status | Existing implementation |
|---|---|---|---|
| `pilot_markdown` | string | Existing | `export_pilot_markdown()` |
| `executive_brief` | string | Existing | `export_executive_brief()` |
| `decision_report` | dict | Existing | `decision_report()` |
| `preferred_manager_objects` | dict | Existing | `preferred_manager_objects()` |
| `hypothesis_map` | string | Existing | `export_hypothesis_map()` |
| `remeasurement_report` | string | Existing | `export_remeasurement_report()` |

## Summary

| Status | Count | Fields |
|---|---:|---|
| Existing | 30 | observations, data_quality, eligibility, measurements, percentiles, distributions, composite_scores, divergence_results, detected_patterns, diagnoses, workflow_fit, org_topology, benchmark_results, interventions, experiments, verification_results, outcome_correlation, outcome_joins, operator_gates, artifacts, lineages, outcomes, lineage_chains, lineage_summary, pilot_markdown, executive_brief, decision_report, preferred_manager_objects, hypothesis_map, remeasurement_report |
| Reusable | 23 | name, created_at, created_by, authorized_by, tenant_id, cohort_id, operator_ids, operator_count, teams, eval_families, commercial_pilot_id, deployment_level, window_start, window_end, window_days, providers, ingest_adapters, observation_count, identity_mappings, reference_id, version, distributions, synthetic |
| Extension required | 5 | enterprise_name, pilot_question (appears in scope + objectives), best_buyer, replication_results (list), readout_documents registry |
| Genuinely new | 12 | pilot_id, selection_criteria, extension_periods, criteria, locked_at, locked_by, snapshot_timestamp, gate_1_result, gate_2_results, gate_3_result, decision_record, closure_outcome |

**Total: 70 unique fields.** (30+23+5+12 = 70) `pilot_question` appears
in both the scope and objectives sections but is counted once.

## Design principle

> **Avoid creating duplicate representations of state already present
> elsewhere.** The Pilot object binds existing domain objects to a
> pilot_id and adds the governance layer (charter, success criteria,
> gates, decisions). It does not re-implement measurements, diagnoses,
> or interventions — those are existing domain objects referenced by
> the pilot.
