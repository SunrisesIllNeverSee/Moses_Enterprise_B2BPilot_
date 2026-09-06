# PILOT_CAPABILITY_MAP.md

> Phase 2 — pilot capability maturity matrix.
>
> Every score is supported by repository evidence (file paths, runtime
> validation, test results). See `EXISTING_SURFACE_MAP.md` for the full
> inventory.

## Maturity scale

| Score | Label | Meaning |
|---:|---|---|
| 5 | STRONG | Materially implemented and demonstrated |
| 4 | BUILT | Implemented but customer/production hardening remains |
| 3 | PARTIAL | Meaningful implementation exists but lifecycle integration is incomplete |
| 2 | THIN | Mostly procedural/manual/conceptual |
| 1 | WRAPPER MISSING | Underlying capability exists but pilot abstraction does not |
| 0 | MISSING | Underlying capability is absent |

## Capability matrix

| Requirement | What it means | How Upsilon satisfies it | Evidence | Score | Hardening needed | Priority |
|---|---|---|---|---:|---|---|
| Bounded population | Pilot operates on a fixed, named operator set | `Cohort.operator_ids` is a fixed list; `CohortConfig.min/max_operators` (25–100); 12 commercial pilot templates define population expectations | `src/domain/cohort.py`, `src/domain/pilot_configuration.py`, `src/config/pilot_registry.py`; runtime: 50 operators in `acme_50` | 5 | Real-customer cohort creation workflow (currently demo-only data loading) | P2 |
| Bounded duration | Pilot has explicit start/end dates | `Cohort.window_start`/`window_end` (date objects); `CohortConfig.window_days` (default 30); followup_days on interventions | `src/domain/cohort.py`, `src/domain/intervention.py`; runtime: 2026-07-01 to 2026-07-30 | 5 | Multi-window scheduling for longitudinal pilots | P2 |
| Instrumentation | Telemetry collection from provider sources | Fixture/Claude/Codex/GitHub file adapters + Claude/Codex/Groq API adapters (stub + live mode). Full canonical ingest emits Observation + System + Session + Task + Artifact + Lineage | `src/ingest/` (11 modules); CLI `ingest`; MCP `get_pilot_status` | 4 | Live API key testing with real provider APIs; rate-limit handling; error retry | P1 |
| Observation collection | Structured telemetry records with token counts | `Observation` dataclass (I/O/R/W tokens, model, platform, timestamp, source_confidence, raw_source_reference). JSON schema validated | `src/domain/observation.py`, `schemas/observation.schema.json`; runtime: 1668 observations | 5 | Real-provider schema drift handling | P2 |
| Privacy boundary | Pseudonymity, no raw content, governance gates | Pseudonymous operator IDs (op_001–op_050); `synthetic: true` on all objects; `privacy_class: pseudonymous_synthetic`; no raw content in observations (token counts + pointer only); `GovernanceEnforcement` with purpose/disclosure/consent gates | `src/domain/operator.py`, `src/governance/enforcement.py`, `src/mcp_server/server.py` | 4 | Real-customer consent workflow; employee disclosure acknowledgment process; data retention policy | P1 |
| Data quality | Automated quality checks with severity levels | 6 checks (missingness, impossible_values, duplicates, provenance, source_confidence, sparse_operators) with OK/WARNING/BLOCKING severity. `validate_observations()` + `run_all_quality_checks()` | `src/analysis/data_quality.py`, `src/ingest/validate.py`; runtime: 50 OK, 1882 WARNING, 0 BLOCKING | 5 | Real-data quality threshold calibration; blocking-gate enforcement on production data | P2 |
| Baseline | Measurable starting point with canonical metrics | `ScoringEngine.score_operator/cohort()` computes 5 canonical metrics (leverage, yield, token_snr, log_leverage, construction) from observations over cohort window. Reference population percentiles computed | `src/metrics/engine.py`, `src/metrics/registry.py`, `src/analysis/percentiles.py`; runtime: all 50 operators scored, medians match reference field | 5 | Real external reference field (current is synthetic, derived from demo cohort itself) | P1 |
| Cohort analysis | Population-level distributions and statistics | `compute_cohort_distributions()` (median, IQR, p10/p90), `cohort_medians()`, `compare_teams()`, `org_topology()` | `src/analysis/distributions.py`, `src/analysis/org_topology.py`, `src/analysis/team_composition.py` | 5 | None — fully implemented | P3 |
| Operator analysis | Per-operator metric profiles with percentiles | `score_operator()` + `compute_percentiles()` + `operator_profile()` (metrics + percentiles + diagnoses). Composite developmental score | `src/metrics/engine.py`, `src/analysis/percentiles.py`, `src/metrics/composite_score.py` | 5 | None — fully implemented | P3 |
| Benchmarking | Legitimate comparison classes with uncertainty | `BenchmarkEngine` with 13 benchmark classes, selection algorithm (§7.14), bootstrap CIs, percentile ranks. No false leaderboards | `src/benchmark/engine.py`; runtime: 50 operators benchmarked (peer class selected for all) | 4 | Real reference population (current benchmark uses cohort-as-reference); self-vs-prior window data | P1 |
| Divergence | Usage vs operation gap analysis | `compute_divergence()` classifies into 4 quadrants (HIGH_USAGE_LOW_OPERATION, LOW_USAGE_HIGH_OPERATION, LOW_LOW, MIXED) with pp delta | `src/analysis/divergence.py`; runtime: 5 LO-USAGE/HI-OP, 3 HI-USAGE/LO-OP, 12 LO/LO, 30 MIXED | 5 | None — fully implemented | P3 |
| Diagnosis | Hypothesis generation from detected patterns | `PatternEngine` detects 6 patterns (P-CTX-01, P-CTX-02, P-BURN-01, P-HIDDEN-01, P-MODEL-01, P-STAGE-01). `DiagnosisEngine` generates hypotheses with evidence + alternatives + HYPOTHESIS status + recommended interventions | `src/diagnostics/pattern_engine.py`, `src/diagnostics/diagnosis_engine.py`; runtime: 56 patterns, 56 diagnoses across 39 operators | 5 | Additional pattern detectors for real-customer workflows | P2 |
| Workflow analysis | Stage-level fit and bottleneck detection | `WorkflowFitEngine` with sample-size gates (min 5). 4 workflows (software_dev, design_sprint, data_analysis, incident_response). `workflow_fit_by_stage()` | `src/workflow/fit_engine.py`, `src/domain/workflow.py`; runtime: 4 workflows, 7 stages each | 4 | Custom workflow definition UI for customer-specific processes | P2 |
| Intervention | Controlled changes with declared target + window | 12-entry catalog (CTX/FRM/MOD/AGT/REV/STD/COA/LRN/STG). `assign_intervention()` requires authorized_by + target_metric + followup_days. `close_intervention()` with SUCCESS/PARTIAL/NO_EFFECT/NEGATIVE outcomes | `src/interventions/registry.py`, `src/interventions/manager.py`, `src/service.py`; runtime: 12 interventions | 5 | Real intervention execution tracking (currently outcomes are declared, not measured from execution) | P1 |
| Pre/post comparison | Baseline vs follow-up metric deltas | `PrePostVerifier` computes target + non-target metric deltas between baseline and follow-up windows. `VerificationResult` with `MetricDelta` list (absolute + percent delta) | `src/analysis/verifier.py`; runtime: 12 verification results | 5 | Automated follow-up window scheduling; statistical significance testing | P2 |
| Verification | Evidence-backed change confirmation | `verify_intervention()` / `verify_all_interventions()` + `ReplicationEngine` (window/cohort split replication) + outcome correlation through lineage | `src/analysis/verifier.py`, `src/analysis/replication.py`, `src/analysis/outcome_correlation.py` | 4 | Causal inference methods (currently ASSOCIATION only — by design, but causal validation is a future capability) | P2 |
| Lineage | Observation → transformation → artifact → outcome chain | `Lineage` domain object with BI→AAI→committed-state→outcome link sequence. `lineage_chain()` builds full chain. 50 lineages in demo | `src/domain/lineage.py`, `src/service.py`; runtime: 50 lineages, 50 outcomes linked | 4 | Real-provider lineage extraction (currently synthetic) | P1 |
| Success criteria | Locked-before-measurement objectives | `PilotConfiguration` carries eval family selections + governance metadata. `COMMERCIAL_PILOTS` define questions + eval families. But: no explicit success-criteria-threshold locking before measurement | `src/domain/pilot_configuration.py`, `src/config/pilot_registry.py` | 2 | Success criteria schema + pre-launch locking mechanism + gate-3 comparison | P1 |
| Milestones | Stage-completion checkpoints | Lifecycle stages are implicit in the demo flow (`demo full` runs 10 steps). No explicit milestone tracking or persistence | `src/cli/main.py` `_demo_full()` | 1 | Milestone records tied to pilot_id + stage + evidence | P1 |
| Pilot state | Current stage, progress, blockers | `pilot_status()` returns cohort/window/eligible/providers/observations/quality/interventions. But: no explicit stage state machine, no "current stage" field, no blocker tracking | `src/service.py` `pilot_status()` | 2 | Pilot state machine + stage tracking + blocker registry | P1 |
| Decision gates | Formal go/no-go checkpoints | 3 production gate rules (GATE-001/002/003) for operator-level routing. But: no pilot-level decision gates (launch readiness, pilot health, closure/scale) | `src/domain/production_gate.py` | 2 | Three pilot-level decision gates (LAUNCH/HEALTH/CLOSURE) with defined outcomes | P1 |
| Progress/status | Real-time pilot progress visibility | `pilot_status()` provides snapshot. TUI screen 1 shows status. But: no stage progress display, no lifecycle visualization | `src/service.py`, `src/tui/app.py` screen 1 | 3 | Lifecycle progress display (✓/→/○ stage indicators) + pilot_id binding | P1 |
| Readout | Evidence-backed pilot summary | `export_pilot_markdown()`, `export_executive_brief()`, `generate_executive_dashboard()`, `export_hypothesis_map()`, `export_remeasurement_report()`, `build_decision_report()`, `preferred_manager_objects()` | `src/reporting/` (6 modules) | 5 | Real-customer branding + custom report templates | P2 |
| Pilot closure | Terminal decision (stop/extend/expand/deploy) | No closure decision record exists. Pilots do not terminate in a formal decision. `results.json` has classifications but no closure outcome | — | 0 | Closure decision record schema + gate-3 evaluation + outcome documentation | P1 |
| Institutional memory | Past pilot findings inform future pilots | No cross-pilot memory. Each `PilotService` instance is independent. No pilot archive or findings database | — | 0 | Pilot archive + findings database + cross-pilot pattern library | P2 |
| Production transition | Path from pilot to production deployment | `SQLiteRepository` provides persistence. `deployment_level` (1/2/3) in `PilotConfiguration`. But: no production transition checklist or deployment gate | `src/repository/sqlite_repository.py`, `src/domain/pilot_configuration.py` | 2 | Production transition checklist + deployment gate + handoff artifact | P2 |

## Score distribution

| Score | Count | Requirements |
|---:|---:|---|
| 5 | 12 | bounded population, bounded duration, observation collection, data quality, baseline, cohort analysis, operator analysis, divergence, diagnosis, intervention, pre/post comparison, readout |
| 4 | 6 | instrumentation, privacy boundary, benchmarking, workflow analysis, verification, lineage |
| 3 | 1 | progress/status |
| 2 | 4 | success criteria, pilot state, decision gates, production transition |
| 1 | 1 | milestones |
| 0 | 2 | pilot closure, institutional memory |

**Total: 26 requirements.** 18 score 4–5 (strong/built), 1 score 3
(partial), 7 score 0–2 (thin/missing).

## Key findings

1. **Measurement and analysis are strong (scores 4–5).** The platform's core
   value — computing canonical metrics, detecting patterns, generating
   diagnoses, verifying interventions — is materially implemented and
   demonstrated with 676 passing tests. 18 of 26 requirements score 4–5.

2. **Governance is the primary gap (scores 0–2).** Pilot-level decision gates,
   success-criteria locking, pilot state machine, milestone tracking, and
   closure decisions are either missing or thin. These are canon/governance
   gaps — they require specification and binding, not new analytical
   capability.

3. **The pilot abstraction is missing (score 1–2).** The platform has rich
   analytical capability but no `Pilot` object that binds a pilot_id to
   its stage, state, gates, evidence, and decisions. `PilotService` is a
   service layer, not a pilot lifecycle manager.

4. **Production hardening is secondary (score 4).** Instrumentation, privacy,
   benchmarking, and lineage are implemented but need real-customer
   validation. The reference field is synthetic (derived from the demo
   cohort itself), which is a known limitation for benchmarking.
