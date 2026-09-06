# EXISTING_SURFACE_MAP.md

> Phase 1 inventory of the `_01_platform` repository.
>
> Every row is grounded in actual inspected behavior, not filename inference.
> Runtime validation was performed by instantiating `PilotService` and
> exercising each surface. Test suite: 676 passing (2026-09-06).

## Method

1. Enumerated all source modules (`src/**/*.py`), tests, schemas, scripts, and demo data.
2. Read `MANIFEST.yaml` for the package's self-declared module map.
3. Instantiated `PilotService` (the shared service layer) and exercised every public method referenced by CLI/TUI/MCP.
4. Ran `python3 -m pytest tests/ -q` → 676 passed.
5. Validated demo data record counts directly from `demo_data/` files.
6. Mapped each capability to its pilot lifecycle stage (see `PILOT_LIFECYCLE.md`).

## Repository topology

| Layer | Path | Role |
|---|---|---|
| Domain models | `src/domain/` (30 modules) | Canonical entity definitions (Observation, Operator, Cohort, Measurement, Intervention, Lineage, Outcome, etc.) |
| Metrics engine | `src/metrics/` | ScoringEngine + MetricRegistry (5 canonical metrics, registry v0.2) |
| Ingest | `src/ingest/` | Fixture/Claude/Codex/GitHub adapters + API adapters (Claude/Codex/Groq) + validation |
| Repository | `src/repository/` | DemoRepository (in-memory from JSON/CSV) + SQLiteRepository (persistent) |
| Analysis | `src/analysis/` (16 modules) | Divergence, percentiles, distributions, eligibility, data quality, verifier, replication, org topology, similarity, context architecture, longitudinal, team composition, dependency risk, learning curve, operator-system decomposition, outcome correlation |
| Diagnostics | `src/diagnostics/` | PatternEngine (pattern detection) + DiagnosisEngine (hypothesis generation) |
| Interventions | `src/interventions/` | Registry (12-entry catalog) + Manager (assign/recommend) |
| Workflow | `src/workflow/` | WorkflowFitEngine (stage fit with sample-size gates) |
| Outcomes | `src/outcomes/` | JoinEngine + Governance + CrossAnalysis (ASSOCIATION only) |
| Benchmark | `src/benchmark/` | BenchmarkEngine (13 benchmark classes, selection algorithm §7.14) |
| Governance | `src/governance/` | Enforcement (purpose/disclosure/consent/bias/challenge/correction) + DecisionUse + ManagerObjects |
| Config | `src/config/` | PilotConfigurator + EvalRegistry (15 eval families) + PilotRegistry (12 commercial pilots) + Validation |
| Reporting | `src/reporting/` (6 modules) | Exporters, executive brief, dashboard, decision report, config report, PDF |
| Service | `src/service.py` (1792 lines) | PilotService — single shared service layer for all interfaces |
| CLI | `src/cli/main.py` (1272 lines) | `enterprise` CLI — 14 command groups |
| TUI | `src/tui/app.py` (512 lines) | 12-screen rich TUI console |
| MCP | `src/mcp_server/server.py` (1055 lines) | 26 registered tools (10 read + 3 write + 13 additional) |
| Demo entry | `src/enterprise_demo.py` | Legacy 7-command demo CLI (delegates to PilotService) |

## Capability inventory

| Capability | Existing implementation | Files | CLI/TUI surface | Runtime status | Pilot stage |
|---|---|---|---|---|---|
| Pilot identity / cohort definition | `Cohort` domain object with cohort_id, tenant_id, window, operator_ids. `PilotConfiguration` domain object with eval selections, cohort config, gates, governance metadata. | `src/domain/cohort.py`, `src/domain/pilot_configuration.py`, `src/config/pilot_registry.py` | CLI `pilot init/status`, `cohort list/show`, `configure from-pilot/from-evals`; TUI screen 1 (Pilot), screen C (Configure); MCP `get_pilot_status`, `list_pilot_options`, `create_pilot_configuration` | Working — 50-operator cohort loaded from `demo_data/cohort.json`; 12 commercial pilot templates + 15 eval families registered | DEFINE |
| Bounded population | `Cohort.operator_ids` (fixed list), `CohortConfig.min_operators`/`max_operators` (25–100 defaults) | `src/domain/cohort.py`, `src/domain/pilot_configuration.py` | CLI `cohort list/show`; TUI screen 2 | Working — 50 operators bounded in `acme_50` cohort | DEFINE |
| Bounded duration | `Cohort.window_start`/`window_end` (date objects), `CohortConfig.window_days` (default 30) | `src/domain/cohort.py` | CLI `pilot status`; TUI screen 1 | Working — 2026-07-01 to 2026-07-30 (30 days) | DEFINE |
| Operator model | `Operator` dataclass: operator_id, pseudonym, team, role_family, level, primary_platform, pattern_demo, synthetic | `src/domain/operator.py` | CLI `score operator`; TUI screen 3 | Working — 50 operators with pseudonymous IDs (op_001–op_050) | DEFINE / INSTRUMENT |
| Tenant model | `Tenant` dataclass | `src/domain/tenant.py` | Not directly surfaced | Defined but not exercised in demo (single tenant `acme`) | DEFINE |
| Telemetry ingestion (fixture) | `FixtureAdapter` loads observations from JSONL/CSV demo data | `src/ingest/fixture.py` | CLI `ingest fixture`; MCP indirect | Working — 1668 observations loaded | INSTRUMENT |
| Telemetry ingestion (provider file) | `ClaudeAdapter`, `CodexAdapter`, `GitHubAdapter` parse provider export files | `src/ingest/claude.py`, `src/ingest/codex.py`, `src/ingest/github.py` | CLI `ingest claude/codex/github-copilot --full` | Working — adapters parse provider exports into canonical objects | INSTRUMENT |
| Telemetry ingestion (provider API) | `ClaudeApiAdapter`, `CodexApiAdapter`, `GroqApiAdapter` — stub mode without API key, live mode with key | `src/ingest/api_claude.py`, `src/ingest/api_codex.py`, `src/ingest/api_groq.py`, `src/ingest/api_base.py` | CLI `ingest api-claude/api-codex/api-groq` | Working in stub mode; live mode requires API key + provider API access (not exercised in demo) | INSTRUMENT |
| Full canonical ingest | Adapters emit Observation + System + SystemVersion + Session + Task + Artifact + Lineage via `ingest_full()` | `src/ingest/claude.py`, `src/ingest/codex.py`, `src/ingest/github.py` | CLI `ingest --full` | Working — `IngestResult.canonical_object_count()` returns typed objects | INSTRUMENT |
| Observation schema | `Observation` dataclass: operator_id, I/O/R/W tokens, model, platform, timestamp, source_confidence, raw_source_reference. JSON schema at `schemas/observation.schema.json` | `src/domain/observation.py`, `schemas/observation.schema.json` | CLI `ingest validate` | Working — schema validation via `validate_observations()` | INSTRUMENT |
| Observation validation | `validate_observations()` checks missingness, impossible values, duplicates, provenance, source confidence, sparse operators | `src/ingest/validate.py`, `src/analysis/data_quality.py` | CLI `ingest validate`, `validate outcomes`; TUI screen 9; MCP `get_data_quality` | Working — 6 quality checks; demo: 50 OK, 1882 WARNING, 0 BLOCKING | INSTRUMENT / BASELINE |
| Privacy boundary | Pseudonymous operator IDs (op_001–op_050), `synthetic: true` flags on all objects, `privacy_class: pseudonymous_synthetic` in governance annotations. No raw content stored — only token counts + `raw_source_reference` pointer | `src/domain/operator.py`, `src/governance/enforcement.py`, `src/mcp_server/server.py` | Governance annotations on every CLI/MCP response | Working — pseudonymity enforced; no PII in observation schema | INSTRUMENT |
| Governance enforcement | `GovernanceEnforcement` with PurposeLimitationGate, DisclosureGate, ConsentManager, BiasReviewManager, ChallengeManager, CorrectionManager, GovernanceAuditLog | `src/governance/enforcement.py` (900+ lines) | CLI `ingest --purpose`; MCP `check_ingestion_governance` | Working — gates block ingestion when purpose/disclosure/consent not met; audit log records all actions | INSTRUMENT / GOVERNANCE |
| Decision-use labels | `DecisionUse` enum (DEVELOPMENTAL, WORKFLOW_EXPERIMENTATION, ASSOCIATION, PERSONNEL_PROHIBITED). Every diagnostic/intervention/outcome surface carries a label | `src/governance/decision_use.py` | All CLI/TUI/MCP surfaces | Working — labels present on all surfaces | GOVERNANCE |
| Metric registry | `MetricRegistry` with 5 canonical metrics (leverage, yield, token_snr, log_leverage, construction) + 2 unresolved (velocity, compression_operating_ratio). Registry v0.2 | `src/metrics/registry.py`, `src/metrics/formulas.py`, `demo_data/metric_registry.json`, `schemas/metric_registry.json` | CLI `metrics registry/explain`; MCP implicit | Working — 5 canonical metrics computed from observations | BASELINE |
| Scoring engine | `ScoringEngine.score_operator()` computes all canonical metrics from observations over a window. `score_cohort()` for all operators | `src/metrics/engine.py` | CLI `score operator/cohort`; TUI screen 3; MCP `get_operator_profile` | Working — all 50 operators scored; values match `cohort.json` medians | BASELINE |
| Composite score | `compute_composite_score()` combines 4 metrics into 0–100 developmental index via reference-population percentile normalization. Labeled DEVELOPMENTAL, never PERSONNEL | `src/metrics/composite_score.py` | CLI `score composite/composite-summary`; MCP `get_composite_score`, `get_composite_score_summary` | Working — cohort composite scores computed; summary returns distribution stats (no leaderboard) | BASELINE |
| Reference field / benchmarking | `ReferencePopulation` with percentile distributions (p0–p100) for each metric. `BenchmarkEngine` with 13 benchmark classes + selection algorithm (§7.14) + bootstrap CIs | `src/domain/reference_population.py`, `src/benchmark/engine.py`, `demo_data/reference_field.json` | CLI `benchmark operator/cohort/summary`, `compare cohort`; TUI screen 3; MCP `compare_operator_to_reference` | Working — reference field v`public_field_2026-08-17` (synthetic, derived from acme_50 cohort itself); benchmark selects `peer` class for all 50 operators | BASELINE / DIAGNOSE |
| Percentile computation | `compute_percentiles()` maps each operator's metrics to reference-population percentiles | `src/analysis/percentiles.py` | CLI `compare cohort`; TUI screens 2, 3 | Working — percentiles computed for all operators | BASELINE |
| Cohort distributions | `compute_cohort_distributions()` produces median, IQR, p10/p90 for each metric | `src/analysis/distributions.py` | CLI `compare cohort`; MCP `get_cohort_distribution` | Working — distributions computed; medians match reference field | BASELINE |
| Divergence analysis | `compute_divergence()` classifies operators into 4 quadrants (HIGH_USAGE_LOW_OPERATION, LOW_USAGE_HIGH_OPERATION, LOW_LOW, MIXED) based on usage vs yield percentiles | `src/analysis/divergence.py` | CLI `compare usage-operation`; TUI screen 4; MCP `find_usage_operation_divergence` | Working — demo: 5 LO-USAGE/HI-OP, 3 HI-USAGE/LO-OP, 12 LO/LO, 30 MIXED | DIAGNOSE |
| Eligibility checking | `check_eligibility()` / `check_cohort_eligibility()` — minimum observation count, non-null metrics | `src/analysis/eligibility.py` | CLI `verify operator`; TUI screen 8; MCP `verify_change` | Working — 50/50 eligible in demo | BASELINE / VERIFY |
| Data quality checks | 6 checks: missingness, impossible_values, duplicates, provenance, source_confidence, sparse_operators. Severity: OK/WARNING/BLOCKING | `src/analysis/data_quality.py` | CLI `validate outcomes`; TUI screen 9; MCP `get_data_quality` | Working — demo: 50 OK, 1882 WARNING (source_confidence + impossible_values), 0 BLOCKING | BASELINE / VERIFY |
| Pattern detection | `PatternEngine` detects P-CTX-01, P-CTX-02, P-BURN-01, P-HIDDEN-01, P-MODEL-01, P-STAGE-01 patterns from metrics + observations + workflow observations | `src/diagnostics/pattern_engine.py` (446 lines) | CLI `diagnose`; MCP `get_diagnostics` | Working — 56 patterns detected across 39 operators in demo | DIAGNOSE |
| Diagnosis generation | `DiagnosisEngine` generates hypotheses from detected patterns. Every diagnosis: evidence + alternatives + status=HYPOTHESIS + recommended interventions | `src/diagnostics/diagnosis_engine.py` | CLI `diagnose cohort/operator`; TUI screen 5; MCP `get_diagnostics` | Working — 56 diagnoses generated; all carry HYPOTHESIS status | DIAGNOSE |
| Intervention catalog | 12-entry fixed catalog: CTX-001/002/003, FRM-001/002, MOD-001, AGT-001, REV-001, STD-001, COA-001, LRN-001, STG-001. Pattern→intervention mapping | `src/interventions/registry.py` | CLI `intervention catalog`; MCP `get_intervention_status` | Working — 12 catalog entries with type, target metric, followup days | DIAGNOSE / INTERVENE |
| Intervention assignment | `InterventionManager.assign()` creates interventions with declared target_metric + followup_days. Requires `authorized_by` in CLI/MCP | `src/interventions/manager.py`, `src/service.py` | CLI `intervention assign/close`; MCP `assign_intervention`, `close_intervention` | Working — authorization enforced; demo has 12 pre-loaded interventions | INTERVENE |
| Intervention outcomes | `InterventionOutcome` enum: SUCCESS/PARTIAL/NO_EFFECT/NEGATIVE. `close_intervention()` persists outcome | `src/domain/intervention.py`, `src/service.py` | CLI `intervention close`; MCP `close_intervention` | Working — demo outcomes: 5 SUCCESS, 2 PARTIAL, 2 NO_EFFECT, 3 NEGATIVE | INTERVENE / VERIFY |
| Pre/post verification | `PrePostVerifier` computes target + non-target metric deltas between baseline and follow-up windows. `VerificationResult` with `MetricDelta` list | `src/analysis/verifier.py` | CLI `verify intervention`; TUI screen 8; MCP `verify_change` | Working — 12 verification results computed; target + non-target deltas present | VERIFY |
| Post-intervention results | `demo_data/results.json` — 12 pre-computed results with internal_deltas, external_deltas, classification | `demo_data/results.json` | CLI `demo full` step 7 | Working — classifications: 5 improved_internal_and_external, 2 improved_internal_only, 2 no_change, 3 degraded | VERIFY |
| Outcome correlation | `compute_outcome_correlation()` connects lineage micro_eval to Outcome nodes (quality score, cycle time). Labeled ASSOCIATION, evidence grade OBSERVATIONAL | `src/analysis/outcome_correlation.py`, `src/service.py` | CLI `lineage outcomes`; MCP `get_outcome_correlation` | Working — 50 lineages, 50 outcomes linked; correlations computed | VERIFY / READOUT |
| Outcome join engine | `OutcomeJoinEngine` joins external outcome CSVs to internal metric deltas. `OutcomeGovernance` enforces ASSOCIATION-only | `src/outcomes/join_engine.py`, `src/outcomes/governance.py` | CLI `ingest github`, `export pilot`; MCP `attach_outcome_dataset` | Working — external outcomes CSV supported; ASSOCIATION label enforced | VERIFY / READOUT |
| Intervention × outcome cross-analysis | `InterventionOutcomeAnalyzer` wires pre/post verifier to outcome join engine | `src/outcomes/cross_analysis.py` | CLI indirect; service method `intervention_outcome_analysis()` | Working — cross-analysis produces ASSOCIATION-labeled results | VERIFY / READOUT |
| Lineage tracking | `Lineage` domain object with BI→AAI→committed-state→outcome link sequence. 50 lineages in demo | `src/domain/lineage.py`, `src/repository/demo_repository.py` | CLI `lineage show/summary`; MCP `get_lineage_chain`, `get_lineage_summary` | Working — full lineage chains with micro_eval metrics | BASELINE / VERIFY |
| Artifact tracking | `Artifact` domain object (200 artifacts in demo) with artifact_type, operator_id, workflow_stage | `src/domain/artifact.py`, `src/repository/demo_repository.py` | CLI indirect; service `artifacts_for()` | Working — 200 artifacts loaded | INSTRUMENT / BASELINE |
| Workflow model | `Workflow` with stages (discovery→requirements→architecture→implementation→testing→review→release). 4 workflows in demo (software_dev_v1, design_sprint_v1, data_analysis_v1, incident_response_v1) | `src/domain/workflow.py`, `demo_data/workflows.json` | CLI `workflow show`; TUI screen 6; MCP `get_workflow_fit` | Working — 4 workflows with 7 stages each | DEFINE / DIAGNOSE |
| Workflow fit analysis | `WorkflowFitEngine` computes provisional stage fit with sample-size gates (min 5 observations). `WorkflowObservation` records | `src/workflow/fit_engine.py`, `src/domain/workflow.py` | CLI `workflow fit`; TUI screen 6; MCP `get_workflow_fit` | Working — fit computed per stage; sample-size gates enforced | DIAGNOSE |
| Org topology | `compute_org_topology()` — team-level distributions, capability concentration (Gini), platform adoption, single points of failure, cross-team complementarity | `src/analysis/org_topology.py` | CLI `compare topology`; MCP `get_org_topology` | Working — structural map produced (not a ranking) | DIAGNOSE |
| Operator similarity | `compute_operator_similarity()` — normalized Euclidean distance across 5 canonical metrics via percentile rank | `src/analysis/similarity.py` | CLI `compare similarity`; MCP `get_operator_similarity` | Working — nearest neighbors computed | DIAGNOSE |
| Operator×System decomposition | `compute_operator_system_decomposition()` — separates operator/system/interaction effects for operators on 2+ systems | `src/analysis/operator_system.py` | CLI `compare operator-system`; MCP `get_operator_system_decomposition` | Working — decomposition computed | DIAGNOSE |
| Context architecture | `compute_context_architecture()` — reuse ratio, construction ratio, context efficiency, pattern classification | `src/analysis/context_architecture.py` | CLI `score operator`; MCP `get_operator_profile` | Working — per-operator context patterns | DIAGNOSE |
| Longitudinal movement | `compute_longitudinal_movement()` — metric deltas, trend direction, band movement, stability over N sub-windows | `src/analysis/longitudinal.py` | CLI indirect; service method | Working — 3-window movement computed | DIAGNOSE / VERIFY |
| Team composition | `compute_team_composition()` — archetype distribution, coverage gaps, complementarity (Shannon evenness) | `src/analysis/team_composition.py` | CLI `compare teams`; MCP `get_cohort_overview` | Working — per-team analysis | DIAGNOSE |
| Dependency risk | `compute_dependency_risk()` — per-metric Gini across teams, single-point-of-failure detection (>40% concentration) | `src/analysis/dependency_risk.py` | CLI indirect; service method | Working — risk summary produced | DIAGNOSE |
| Learning curve | `compute_learning_curve()` — improvement rate, curve shape (linear/diminishing/accelerating/flat), 95% CI, plateau detection | `src/analysis/learning_curve.py` | CLI indirect; service method | Working — 4-window trajectory modeled | DIAGNOSE / VERIFY |
| Replication | `ReplicationEngine` — replicates findings across window/cohort splits. Descriptive stability, NOT causal validation | `src/analysis/replication.py` | CLI indirect; service method `replicate_finding()` | Working — pattern + divergence replication supported | VERIFY |
| Production gates | 3 default gate rules (GATE-001/002/003): leverage <p10 → FLAG_FOR_REVIEW, yield <p10 → ROUTE_TO_INTERVENTION, construction <p25 → NOTIFY. `GateAction` enum, `GateResult` with DEVELOPMENTAL label | `src/domain/production_gate.py` | CLI `gate rules/operator/cohort`; TUI screen G; MCP indirect | Working — 150 gate evaluations (3 rules × 50 operators), 25 fired, 13 operators flagged | GOVERNANCE / INTERVENE |
| Task context adjustment | `TaskContext` + `context_adjustment()` — difficulty-aware metric normalization bounded [0.5x, 2.0x] | `src/domain/context.py` | CLI indirect; service methods `context_adjustment()`, `score_operator_with_context()` | Working — multiplicative normalization for fair benchmarking | DIAGNOSE / VERIFY |
| Cross-system identity | `OperatorIdentity` — maps system-specific IDs to canonical operator IDs. `IdentityConflictError` on conflicting mappings | `src/domain/operator_identity.py` | CLI indirect; service methods `add_operator_identity()`, `resolve_operator_identity()` | Working — conflict detection prevents mis-attribution | INSTRUMENT |
| Preferred manager objects | 8 developmental objects (development groups, fastest improvers, stalled cohorts, workflow bottlenecks, tool/model fit, training candidates, peer support, remeasurement queue) | `src/governance/manager_objects.py` | CLI indirect; service method `preferred_manager_objects()` | Working — positive developmental doctrine surfaced | READOUT |
| Decision report | `build_decision_report()` translates measurement vocabulary to decision vocabulary with developmental action recommendations | `src/reporting/decision_report.py` | CLI indirect; service method `decision_report()` | Working — per-operator and cohort-level decision reports | READOUT |
| Executive brief | `export_executive_brief()` — decisions, next experiments, next-evaluations flywheel (3-4 evidence-backed observations mapped to eval families) | `src/reporting/executive_brief.py` | CLI `export brief`; TUI screen E; MCP `get_executive_dashboard` | Working — brief generated from live service data | READOUT |
| Pilot markdown readout | `export_pilot_markdown()` — full pilot status with data quality, workforce operating map, medians, percentiles | `src/reporting/exporters.py` | CLI `export pilot`; TUI screen E | Working — readout generated; saved to `demo_data/graphics/demo_full_pilot_readout.md` | READOUT |
| Data quality markdown | `export_data_quality_markdown()` — quality check summary in markdown | `src/reporting/exporters.py` | CLI `export pilot` (bundled) | Working | READOUT |
| Hypothesis map | `export_hypothesis_map()` — maps detected patterns to eval families | `src/reporting/exporters.py` | CLI `export hypothesis-map` | Working | READOUT |
| Re-measurement report | `export_remeasurement_report()` — post-intervention re-measurement summary | `src/reporting/exporters.py` | CLI `export remeasurement` | Working | VERIFY / READOUT |
| Executive dashboard (HTML) | `generate_executive_dashboard()` — HTML dashboard with bar charts, histograms, donut charts, heatmaps | `src/reporting/dashboard.py` | CLI `export dashboard` | Working — HTML generated | READOUT |
| PDF report | `render_sample_report_pdf()` / `render_markdown_pdf()` — PDF rendering of sample customer report | `src/reporting/pdf.py` | CLI `demo report` | Working — PDF generated from markdown | READOUT |
| Export (JSON/CSV/MD) | `export_cohort_json/csv/markdown()`, `export_operator_json/markdown()`, `export_artifacts()`, `export_lineages()`, `export_canonical_inventory()` | `src/reporting/exporters.py` | CLI `export cohort/operator/pilot`; TUI screen E | Working — all formats supported | READOUT / EXPORT |
| Pilot configurator | `PilotConfigurator.from_outcome()` / `from_alacarte()` — builds `PilotConfiguration` from commercial pilot template or eval family selection. Save/load/validate | `src/config/configurator.py`, `src/config/validation.py` | CLI `configure`; TUI screen C; MCP `create_pilot_configuration`, `validate_pilot_configuration` | Working — 12 commercial pilots + 15 eval families; validation produces errors + warnings | DEFINE |
| SQLite persistence | `SQLiteRepository` — persistent storage with insert_observations, insert_workflow_observation, attach_outcome_dataset, experiments, outcome_datasets | `src/repository/sqlite_repository.py` | CLI `ingest --db --persist` | Working — persistence path available but demo uses in-memory DemoRepository | PRODUCTION_HARDENING |
| Demo data generator | `scripts/generate_demo_data.py` — generates synthetic cohort, operators, observations, interventions, outcomes | `scripts/generate_demo_data.py` | Manual script execution | Working — seed 50030 produces deterministic data | INSTRUMENT |
| Demo extension generator | `demo_data/generate_extensions.py` — adds artifacts, lineages, outcomes, new workflows, stage events | `demo_data/generate_extensions.py` | Manual script execution | Working — Q14 gap closure extensions | INSTRUMENT |
| Follow-up telemetry | `scripts/add_followup_telemetry.py` — adds post-intervention observations | `scripts/add_followup_telemetry.py` | Manual script execution | Working | INTERVENE / VERIFY |
| Test suite | 19 test files, 676 tests covering engine, metrics, domain, governance, CLI, TUI audit, integration, eval families, SQLite, operator identity | `tests/` | `python3 -m pytest tests/` | Working — 676 passed | VERIFICATION |
| Schemas | `observation.schema.json` (JSON Schema for observations), `metric_registry.json` (metric definitions) | `schemas/` | CLI `ingest validate` | Working — schema validation enforced | INSTRUMENT / BASELINE |

## Interface surface summary

### CLI commands (`enterprise`)

| Command | Subcommands | Pilot stage |
|---|---|---|
| `pilot` | init, status | DEFINE |
| `cohort` | list, show | DEFINE / BASELINE |
| `ingest` | fixture, claude, codex, github, github-copilot, validate, api-claude, api-codex, api-groq | INSTRUMENT |
| `score` | operator, cohort, composite, composite-summary | BASELINE |
| `metrics` | registry, explain | BASELINE |
| `compare` | cohort, usage-operation, teams, models, topology, similarity, operator-system | BASELINE / DIAGNOSE |
| `benchmark` | operator, cohort, summary | BASELINE / DIAGNOSE |
| `diagnose` | cohort, operator | DIAGNOSE |
| `workflow` | show, fit, import, observe | DEFINE / DIAGNOSE |
| `intervention` | catalog, recommend, assign, close | INTERVENE |
| `verify` | operator, intervention | VERIFY |
| `export` | cohort, operator, pilot, brief, hypothesis-map, remeasurement, dashboard | READOUT / EXPORT |
| `validate` | outcomes | BASELINE / VERIFY |
| `gate` | rules, operator, cohort | GOVERNANCE |
| `configure` | list-pilots, list-evals, from-pilot, from-evals, show, validate, report | DEFINE |
| `demo` | status, full, report, graphics | READOUT |
| `lineage` | show, summary, outcomes | BASELINE / VERIFY |

### TUI screens (12)

| Key | Screen | Pilot stage |
|---|---|---|
| 1 | Pilot (status) | DEFINE / BASELINE |
| 2 | Cohort (percentiles + divergence) | BASELINE / DIAGNOSE |
| 3 | Operator (metrics + eligibility) | BASELINE / DIAGNOSE |
| 4 | Divergence (usage vs operation) | DIAGNOSE |
| 5 | Diagnose (hypotheses) | DIAGNOSE |
| 6 | Workflow (stage fit) | DIAGNOSE |
| 7 | Interventions (catalog + assignments) | INTERVENE |
| 8 | Verify (pre/post) | VERIFY |
| 9 | Data Quality | BASELINE / VERIFY |
| G | Gates (production gates) | GOVERNANCE |
| C | Configure (bespoke pilot menu) | DEFINE |
| E | Export | READOUT / EXPORT |

### MCP tools (26 registered)

| Tool | Type | Pilot stage |
|---|---|---|
| get_pilot_status | read | DEFINE / BASELINE |
| get_operator_profile | read | BASELINE / DIAGNOSE |
| compare_operator_to_reference | read | BASELINE |
| get_cohort_distribution | read | BASELINE |
| find_usage_operation_divergence | read | DIAGNOSE |
| get_diagnostics | read | DIAGNOSE |
| get_workflow_fit | read | DIAGNOSE |
| get_intervention_status | read | INTERVENE |
| verify_change | read | VERIFY |
| get_data_quality | read | BASELINE / VERIFY |
| get_composite_score | read | BASELINE |
| get_composite_score_summary | read | BASELINE |
| get_executive_dashboard | read | READOUT |
| get_cohort_overview | read | BASELINE |
| assign_intervention | write | INTERVENE |
| close_intervention | write | INTERVENE / VERIFY |
| create_experiment | write | INTERVENE |
| record_workflow_observation | write | INSTRUMENT / DIAGNOSE |
| attach_outcome_dataset | write | VERIFY |
| list_pilot_options | read | DEFINE |
| create_pilot_configuration | write | DEFINE |
| validate_pilot_configuration | read | DEFINE |
| get_operator_system_decomposition | read | DIAGNOSE |
| get_lineage_chain | read | BASELINE / VERIFY |
| get_lineage_summary | read | BASELINE |
| get_outcome_correlation | read | VERIFY / READOUT |
| get_org_topology | read | DIAGNOSE |
| get_operator_similarity | read | DIAGNOSE |

## Demo data inventory (validated 2026-09-06)

| File | Records | Validated via |
|---|---|---|
| `cohort.json` | 1 cohort (acme_50, 50 operators, 2026-07-01 to 2026-07-30) | `PilotService.cohort` |
| `operators.json` | 50 operators, 6 teams | `PilotService.operators` |
| `observations.jsonl` | 1668 observations | `PilotService.observations` |
| `teams.json` | 6 teams | `PilotService.teams` |
| `workflows.json` | 4 workflows | `PilotService.workflows` |
| `interventions.json` | 12 interventions | `PilotService.interventions` |
| `results.json` | 12 post-intervention results | Direct file read |
| `outcomes.json` | 50 outcomes | `PilotService.outcomes` |
| `lineages.jsonl` | 50 lineages | `PilotService.lineages` |
| `artifacts.jsonl` | 200 artifacts | `PilotService.artifacts` |
| `stage_events.jsonl` | 482 stage events | Direct file read |
| `diagnoses.json` | 37 pre-baked diagnoses (superseded by computed 56) | Direct file read |
| `reference_field.json` | 1 reference population (synthetic, derived from acme_50) | `PilotService.reference_population` |
| `metric_registry.json` | 5 canonical + 2 unresolved metrics | `PilotService.engine.registry` |

## Key discrepancy: prompt-stated vs actual demo values

The prompt stated "approximately 12,842 telemetry observations." The actual
count is **1,668 observations** (validated via `PilotService.observations`
and `wc -l demo_data/observations.jsonl`). The ACME-001 reference pilot
uses the validated value.

All other prompt-stated values match:
- 50 synthetic operators ✓
- 6 teams ✓
- 12 interventions ✓
- computed operator metrics ✓
- reference benchmarking ✓
- pre/post results ✓
- diagnostic surfaces ✓
- verification ✓
- data-quality gates ✓
- pilot readout ✓
