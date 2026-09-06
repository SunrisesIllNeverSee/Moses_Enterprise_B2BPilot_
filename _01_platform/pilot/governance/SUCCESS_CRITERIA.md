# SUCCESS_CRITERIA.md

> Success criteria are locked before measurement. They cannot be amended
> after launch. If the criteria are wrong, the pilot must be STOPPED and
> a new pilot chartered.

## Purpose

Success criteria define what evidence the pilot must produce to support
each closure outcome. They are the benchmark against which Gate 3
(CLOSURE / SCALE) evaluates the pilot.

## Principles

1. **Locked before measurement.** Criteria must be defined and locked
   before any baseline measurement begins. This prevents post-hoc
   criteria adjustment.

2. **Measurable.** Every criterion references a specific metric, threshold,
   and direction. No vague criteria ("improve AI usage").

3. **Bounded.** Criteria reference the pilot's bounded population and
   duration. No criteria that require unbounded data.

4. **Decision-oriented.** Criteria map to closure outcomes. Each criterion
   should help answer: STOP, EXTEND, EXPAND, or DEPLOY?

5. **Developmental.** Criteria measure operating behavior, not personnel
   performance. No criteria that rank or evaluate individual employees.

## Criterion structure

Each success criterion is:

| Field | Description |
|---|---|
| `criterion_id` | Unique ID (e.g., `SC-001`) |
| `metric` | Canonical metric or derived measure (e.g., `leverage`, `yield`, `divergence_rate`) |
| `threshold` | Numeric threshold (e.g., 10.0) |
| `direction` | `above` or `below` |
| `aggregation` | `cohort_median`, `cohort_p10`, `cohort_p90`, `target_group_median`, `target_group_delta` |
| `rationale` | Why this criterion matters for this pilot |
| `closure_mapping` | Which outcomes this criterion informs (STOP/EXTEND/EXPAND/DEPLOY) |

## Example criteria

### For a baseline pilot (Commercial Pilot #1: AI Workforce Operating Baseline)

| ID | Metric | Threshold | Direction | Aggregation | Rationale | Closure mapping |
|---|---|---|---|---|---|---|
| SC-001 | cohort_median_leverage | 10.0 | above | cohort_median | Establishes that the population extracts meaningful value per input token | EXPAND/DEPLOY if met, EXTEND if below |
| SC-002 | eligible_operator_rate | 0.80 | above | cohort | Ensures sufficient data quality for measurement | STOP if below, EXPAND if met |
| SC-003 | divergence_rate | 0.30 | below | cohort | High divergence indicates inconsistent operating patterns | EXTEND if above, DEPLOY if below |

### For an intervention pilot (Commercial Pilot #4: AI Training Evaluation)

| ID | Metric | Threshold | Direction | Aggregation | Rationale | Closure mapping |
|---|---|---|---|---|---|---|
| SC-001 | target_group_yield_delta | 10.0 | above | target_group_delta | Training should produce measurable yield improvement | DEPLOY if met, STOP if not |
| SC-002 | non_target_metric_degradation | 5.0 | below | target_group | Interventions should not degrade non-target metrics | STOP if above, DEPLOY if below |
| SC-003 | intervention_success_rate | 0.50 | above | target_group | Majority of interventions should show positive outcome | EXTEND if below, DEPLOY if met |

## Locking mechanism

Success criteria are locked via the Pilot Charter (see `PILOT_CHARTER.md`).
The `locked_at` timestamp must precede any baseline measurement. The
`locked_by` identity is recorded for audit.

> **Implementation gap:** The platform does not currently implement
> success-criteria locking. `PilotConfiguration` carries eval family
> selections but not explicit success criteria with thresholds. This is
> a P1 gap — see `GAP_REGISTER.md`.

## Gate 3 mapping

Gate 3 (CLOSURE / SCALE) evaluates each criterion:

| Criterion result | Gate 3 contribution |
|---|---|
| All criteria met | Supports DEPLOY or EXPAND |
| Majority met, minority missed | Supports EXTEND (with specific missing evidence) |
| Majority missed | Supports STOP or EXTEND (with fundamental review) |
| Critical criterion missed | Supports STOP |

No criterion result supports indefinite continuation. Every Gate 3
evaluation must produce a terminal decision.
