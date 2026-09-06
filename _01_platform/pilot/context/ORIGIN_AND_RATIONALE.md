# ORIGIN_AND_RATIONALE.md

> Reconstructed rationale for why major Upsilon pilot capabilities
> exist.
>
> This document is NON-CANONICAL. It explains reasoning behind
> canonical decisions. It does NOT override any canonical document.
>
> Rationale is reconstructed from available repository evidence
> (source code, comments, docstrings, demo data, test names, MANIFEST
> references). Where intent cannot be established from evidence, the
> entry is marked **UNRESOLVED**.

## Method

For each capability, the rationale is reconstructed from:
1. Source code docstrings and comments
2. Test names and test coverage
3. Demo data structure and content
4. MANIFEST.yaml spec references (spec docs 00–23)
5. Domain object structure and field names
6. Governance enforcement behavior

Where the evidence clearly establishes intent, the rationale is
stated. Where the evidence is ambiguous or absent, the entry is
marked **UNRESOLVED**.

---

## Baseline measurement

**Capability:** Compute canonical metrics (leverage, yield,
token_snr, log_leverage, construction) for all operators over a
bounded window.

**Evidence:**
- `src/metrics/engine.py`: `ScoringEngine.score_operator()` /
  `score_cohort()`
- `src/metrics/registry.py`: `MetricRegistry` with 5 canonical
  metrics, registry v0.2
- `schemas/metric_registry.json`: metric definitions with formulas
- MANIFEST spec 03: "Canonical Metric Registry"
- Test: `tests/test_metrics.py`, `tests/test_engine.py`

**Rationale:** A pilot requires a measurable starting point. Without
a baseline, there is no "before" to compare against. The 5 canonical
metrics were chosen to capture distinct dimensions of AI operating
behavior: value extraction (leverage), productivity (yield), signal
quality (token_snr), scale (log_leverage), and original work
(construction). The metric registry is frozen (v0.2) to ensure
cross-pilot comparability.

**Status:** ESTABLISHED

---

## Operator versus cohort measurement

**Capability:** Measure both individual operators and the cohort as
a whole.

**Evidence:**
- `src/metrics/engine.py`: `score_operator()` (individual) +
  `score_cohort()` (cohort)
- `src/analysis/distributions.py`: `compute_cohort_distributions()`
  (cohort-level)
- `src/analysis/percentiles.py`: `compute_percentiles()` (individual
  within cohort)
- `src/metrics/composite_score.py`: composite score per operator +
  `composite_score_summary()` (cohort distribution, NOT leaderboard)
- Governance: `DecisionUse.DEVELOPMENTAL` — no personnel evaluations

**Rationale:** Individual measurement is needed for diagnosis and
intervention targeting. Cohort measurement is needed for baseline
distributions, benchmarking, and success criteria evaluation. The
distinction is governance-critical: individual scores are
DEVELOPMENTAL (coaching, not personnel evaluation), while cohort
distributions are the basis for percentile ranks and success
criteria.

**Status:** ESTABLISHED

---

## Reference benchmarking

**Capability:** Compare operators against a reference population
using percentile distributions and benchmark class selection.

**Evidence:**
- `src/domain/reference_population.py`: `ReferencePopulation` with
  p0–p100 percentile distributions per metric
- `src/benchmark/engine.py`: `BenchmarkEngine` with 13 benchmark
  classes, selection algorithm (§7.14), bootstrap CIs
- `demo_data/reference_field.json`: synthetic reference field
  (derived from acme_50 cohort)
- MANIFEST spec 07: "CLI Command Spec" (§7 covers the `benchmark`
  command — "Benchmark engine (§7) — compared to what?")

**Rationale:** Raw metric values are meaningless without a
comparison. "Leverage of 12" is high or low depending on the
reference population. Benchmarking provides legitimate comparison
classes (peer, self_vs_prior, role, team, etc.) with uncertainty
estimates. The selection algorithm chooses the most appropriate
class per operator. No false leaderboards — composite scores are
distributions, not rankings.

**Status:** ESTABLISHED

**Known limitation:** The current reference field is synthetic
(derived from the demo cohort itself). An external reference field
is needed for real-customer pilots (see
`pilot/PILOT_EXTERNAL_BENCHMARKS.md`).

---

## Divergence detection

**Capability:** Classify operators into usage-vs-operation divergence
quadrants.

**Evidence:**
- `src/analysis/divergence.py`: `compute_divergence()` classifies
  into 4 quadrants (HIGH_USAGE_LOW_OPERATION,
  LOW_USAGE_HIGH_OPERATION, LOW_LOW, MIXED)
- CLI: `enterprise compare usage-operation`
- TUI: screen 4 (Divergence)
- MCP: `find_usage_operation_divergence`
- MANIFEST spec 18: "Enterprise Eval Catalog" — EVAL-002

**Rationale:** High AI usage does not equal high AI value. An
operator who uses AI heavily but produces weak outputs
(HIGH_USAGE_LOW_OPERATION) is "burning tokens." An operator who uses
AI lightly but produces strong outputs (LOW_USAGE_HIGH_OPERATION) is
a "hidden high-performer." Divergence detection surfaces these
patterns, which raw usage metrics miss.

**Status:** ESTABLISHED

---

## Workflow diagnosis

**Capability:** Analyze workflow stage fit and identify bottlenecks.

**Evidence:**
- `src/workflow/fit_engine.py`: `WorkflowFitEngine` with sample-size
  gates (min 5 observations per stage)
- `src/domain/workflow.py`: `Workflow` with 7 stages (discovery →
  requirements → architecture → implementation → testing → review →
  release)
- `demo_data/workflows.json`: 4 workflows (software_dev_v1,
  design_sprint_v1, data_analysis_v1, incident_response_v1)
- CLI: `enterprise workflow fit`
- TUI: screen 6 (Workflow)
- MCP: `get_workflow_fit`
- MANIFEST spec 10: "Workflow Stage Taxonomy"

**Rationale:** If strong operators stall at the same workflow stage,
the constraint is the workflow, not the operator. Workflow diagnosis
distinguishes operator-level issues from workflow-level issues,
preventing misattribution of systemic problems to individual
operators.

**Status:** ESTABLISHED

---

## Targeted interventions

**Capability:** Apply controlled interventions with pre-declared
target metrics and follow-up windows.

**Evidence:**
- `src/interventions/registry.py`: 12-entry fixed catalog
  (CTX/FRM/MOD/AGT/REV/STD/COA/LRN/STG)
- `src/interventions/manager.py`: `InterventionManager.assign()` /
  `close()`
- Pattern → intervention mapping in registry
- CLI: `enterprise intervention assign/close` (requires
  `--authorized-by`)
- MCP: `assign_intervention`, `close_intervention`
- MANIFEST spec 09: "Diagnostic + Intervention Registry"

**Rationale:** Diagnosis without action is just observation.
Interventions translate diagnostic hypotheses into controlled
changes. The pre-declared target metric and follow-up window are
critical for valid verification — without them, any post-intervention
change could be attributed to the intervention (confirmation bias).
The 12-entry fixed catalog ensures interventions are standardized
and comparable across pilots.

**Status:** ESTABLISHED

---

## Pre/post comparison

**Capability:** Compute target and non-target metric deltas between
baseline and follow-up windows.

**Evidence:**
- `src/analysis/verifier.py`: `PrePostVerifier` computes
  `VerificationResult` with `MetricDelta` list (absolute + percent
  delta)
- `src/service.py`: `verify_intervention()` /
  `verify_all_interventions()`
- CLI: `enterprise verify intervention`
- TUI: screen 8 (Verify)
- MCP: `verify_change`
- MANIFEST spec 18: EVAL-007 "Intervention Response"

**Rationale:** Without pre/post comparison, there is no evidence
that an intervention produced change. Target metric deltas show
whether the intervention moved the intended metric. Non-target
metric deltas reveal side effects (e.g., a yield intervention may
degrade token_snr). Both are needed for a complete picture.

**Status:** ESTABLISHED

---

## Verification

**Capability:** Confirm evidence-backed change with ASSOCIATION-only
claims.

**Evidence:**
- `src/analysis/verifier.py`: `PrePostVerifier`
- `src/analysis/replication.py`: `ReplicationEngine` (descriptive
  stability across splits)
- `src/analysis/outcome_correlation.py`: connects lineage to
  outcomes, `EvidenceGrade.OBSERVATIONAL`
- `src/outcomes/governance.py`: enforces ASSOCIATION-only
- Governance: `DecisionUse.ASSOCIATION` — never CAUSATION

**Rationale:** Upsilon is an observational evaluation, not a
randomized controlled trial. Interventions are assigned based on
diagnostic hypotheses, not random assignment. Therefore, all
outcome claims are ASSOCIATION, never CAUSATION. This is a
governance constraint, not a limitation — it is the honest
representation of what the evidence supports.

**Status:** ESTABLISHED

---

## Data-quality gates

**Capability:** Automated quality checks with severity levels
(OK/WARNING/BLOCKING).

**Evidence:**
- `src/analysis/data_quality.py`: 6 checks (missingness,
  impossible_values, duplicates, provenance, source_confidence,
  sparse_operators)
- `src/ingest/validate.py`: `validate_observations()`
- CLI: `enterprise validate outcomes`, `enterprise ingest validate`
- TUI: screen 9 (Data Quality)
- MCP: `get_data_quality`
- MANIFEST spec 11: "Measurement Science Validation Plan"

**Rationale:** Garbage in, garbage out. Without data quality gates,
metric values may be computed from incomplete, impossible, or
duplicated observations, producing misleading results. The
OK/WARNING/BLOCKING severity scale distinguishes between "proceed
with caution" (WARNING) and "do not proceed" (BLOCKING).

**Status:** ESTABLISHED

---

## Lineage

**Capability:** Track observation → transformation → artifact →
outcome chains.

**Evidence:**
- `src/domain/lineage.py`: `Lineage` domain object with
  BI→AAI→committed-state→outcome link sequence
- `src/service.py`: `lineage_chain()`, `lineage_summary()`,
  `lineages_for()`
- `demo_data/lineages.jsonl`: 50 lineages
- CLI: `enterprise lineage show/summary/outcomes`
- MCP: `get_lineage_chain`, `get_lineage_summary`
- MANIFEST spec 14: "Product Object Model"

**Rationale:** Connecting operating behavior (observations) to
downstream consequences (outcomes) is what makes Upsilon valuable
to decision-makers. Without lineage, metric improvements are
abstract. With lineage, a yield improvement can be correlated
(ASSOCIATION, not causation) to a quality score improvement or
cycle time reduction.

**Status:** ESTABLISHED

---

## Final enterprise decision

**Capability (specified, not yet implemented):** Gate 3 evaluation
producing STOP/EXTEND/EXPAND/DEPLOY.

**Evidence:**
- `pilot/governance/DECISION_GATES.md`: Gate 3 specification
- `pilot/governance/CLOSURE_OUTCOMES.md`: four closure outcomes
- `pilot/schemas/DECISION_RECORD_SCHEMA.md`: formal schema
- `pilot/implementation/GAP_REGISTER.md`: GAP-006, GAP-007 (missing)
- `pilot/implementation/PILOT_MODE_BUILD_PLAN.md`: T1.3, T1.4 (build
  plan)
- ACME-001 `08_DECISION_RECORD.md`: illustrative only

**Rationale:** A pilot that does not terminate in a decision is not
a pilot — it is an ongoing monitoring program. The four closure
outcomes (STOP/EXTEND/EXPAND/DEPLOY) force a decision based on
evidence vs locked success criteria. No indefinite pilot state.
This is the defining property of an Upsilon Enterprise Pilot (see
`pilot/UPSILON_PILOT_SPEC.md`).

**Status:** ESTABLISHED (as specification) / NOT YET IMPLEMENTED
(as runtime)

---

## Capabilities marked UNRESOLVED

### Composite developmental score weighting

**Capability:** Composite score combines 4 metrics into 0–100
developmental index via reference-population percentile normalization.

**Evidence:**
- `src/metrics/composite_score.py`: `compute_composite_score()`
- Weights: leverage 0.30, yield 0.30, token_snr 0.20, construction
  0.20
- `COMPOSITE_ID = "dev_index"`, `COMPOSITE_NAME = "AI Operator
  Development Index"`
- `COMPOSITE_LABEL = "DEVELOPMENTAL — for development use; not a
  personnel performance rating"`

**Rationale:** **UNRESOLVED.** The specific weight choices (0.30/
0.30/0.20/0.20) are not documented in source code comments, test
names, or MANIFEST spec references. The weights may have been chosen
empirically, by expert judgment, or by convention. The rationale
for excluding log_leverage from the composite (it is a canonical
metric but not in the composite) is also not documented.

**Status:** UNRESOLVED

### 6 pattern detector thresholds

**Capability:** PatternEngine detects 6 patterns (P-CTX-01, P-CTX-02,
P-BURN-01, P-HIDDEN-01, P-MODEL-01, P-STAGE-01) from metrics.

**Evidence:**
- `src/diagnostics/pattern_engine.py`: 447 lines, 6 pattern detectors
- Demo: 56 patterns detected across 39 operators

**Rationale:** **UNRESOLVED.** The specific thresholds for each
pattern detector (e.g., what leverage percentile triggers P-CTX-01)
are defined in the source code but the rationale for the threshold
values is not documented. The 6 patterns may have been chosen from
empirical observation, literature, or expert judgment.

**Status:** UNRESOLVED

### 12 commercial pilot templates

**Capability:** 12 commercial pilot templates with questions, best
buyers, eval families, deployment levels.

**Evidence:**
- `src/config/pilot_registry.py`: `COMMERCIAL_PILOTS` dict with 12
  entries
- Each has: pilot_id, name, question, best_buyer, when_to_pitch,
  eval_families, deployment_level, description

**Rationale:** **UNRESOLVED.** The 12 templates appear to be
product/market decisions (which questions to productize, which
buyers to target). The rationale for these specific 12 (vs more or
fewer, vs different questions) is not documented in the repository.
This is likely a business/product decision, not a technical one.

**Status:** UNRESOLVED

### 15 eval families

**Capability:** 15 eval families (EVAL-001 through EVAL-015) defining
which analytical capabilities are active in a pilot.

**Evidence:**
- `src/config/eval_registry.py`: `EVAL_REGISTRY` dict with 15
  entries
- Each has: eval_id, name, description, implemented, implementation
  _status, service_methods, cli_surfaces, mcp_surfaces,
  commercial_pilot_ids, engine_types

**Rationale:** **UNRESOLVED.** The 15 eval families map to
analytical capabilities, but the rationale for this specific
grouping (vs more granular or more coarse) is not documented. The
mapping to engine types (6.1–6.10) suggests a deeper taxonomy, but
the engine type definitions are not in the repository.

**Status:** UNRESOLVED

---

## What this document does NOT do

- Does not define canonical specifications (see
  `pilot/UPSILON_PILOT_SPEC.md`)
- Does not define metrics (see `src/metrics/registry.py`)
- Does not define interventions (see `src/interventions/registry.py`)
- Does not define patterns (see `src/diagnostics/pattern_engine.py`)
- Does not fabricate historical intent (UNRESOLVED entries are
  marked as such)
