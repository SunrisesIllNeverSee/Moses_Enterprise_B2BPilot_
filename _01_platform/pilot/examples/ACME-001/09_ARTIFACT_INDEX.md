# ACME-001 — Artifact Index

> Index of all evidence artifacts produced by the ACME-001 reference pilot.
> All artifacts are SYNTHETIC.

## Pilot package artifacts

| File | Stage | Status | Description |
|---|---|---|---|
| `00_PILOT_CHARTER.md` | DEFINE | PARTIAL | Pilot charter (missing locked success criteria) |
| `01_INSTRUMENTATION_READINESS.md` | INSTRUMENT | COMPLETE | Instrumentation readiness record |
| `02_BASELINE_SNAPSHOT.md` | BASELINE | COMPLETE | Baseline snapshot with cohort distributions |
| `03_DIAGNOSTIC_FINDINGS.md` | DIAGNOSE | COMPLETE | 56 patterns, 56 diagnoses, divergence, topology |
| `04_INTERVENTIONS.md` | INTERVENE | COMPLETE | 12 intervention records with declared targets |
| `05_VERIFICATION_RESULTS.md` | VERIFY | COMPLETE | 12 verification results with target + non-target deltas |
| `06_GATE_RECORDS.md` | GATES | ILLUSTRATIVE | Gate records (gates not implemented) |
| `07_PILOT_READOUT.md` | READOUT | COMPLETE | Pilot readout with evidence summary |
| `08_DECISION_RECORD.md` | DECIDE | ILLUSTRATIVE | Decision record (decision not implemented) |

## Runtime evidence artifacts

| Artifact | Count | Source | Stage |
|---|---|---|---|
| Observations | 1,668 | `demo_data/observations.jsonl` | INSTRUMENT |
| Operators | 50 | `demo_data/operators.json` / `PilotService.operators` | DEFINE |
| Teams | 6 | `demo_data/teams.json` / `PilotService.teams` | DEFINE |
| Workflows | 4 | `demo_data/workflows.json` / `PilotService.workflows` | DEFINE |
| Measurements | 250 (50 operators × 5 metrics) | `PilotService.score_cohort()` | BASELINE |
| Reference population | 1 (synthetic) | `demo_data/reference_field.json` | BASELINE |
| Detected patterns | 56 | `PilotService.detect_cohort_patterns()` | DIAGNOSE |
| Diagnoses | 56 | `PilotService.generate_cohort_diagnoses()` | DIAGNOSE |
| Divergence results | 50 | `PilotService.divergence()` | DIAGNOSE |
| Benchmark results | 50 | `PilotService.benchmark_cohort()` | DIAGNOSE |
| Interventions | 12 | `demo_data/interventions.json` / `PilotService.interventions` | INTERVENE |
| Verification results | 12 | `PilotService.verify_all_interventions()` | VERIFY |
| Post-intervention results | 12 | `demo_data/results.json` | VERIFY |
| Artifacts | 200 | `demo_data/artifacts.jsonl` / `PilotService.artifacts` | INSTRUMENT |
| Lineages | 50 | `demo_data/lineages.jsonl` / `PilotService.lineages` | BASELINE/VERIFY |
| Outcomes | 50 | `demo_data/outcomes.json` / `PilotService.outcomes` | VERIFY |
| Stage events | 482 | `demo_data/stage_events.jsonl` | INSTRUMENT |
| Gate evaluations (operator-level) | 150 (3 rules × 50 operators) | `PilotService.evaluate_cohort_gates()` | GOVERNANCE |
| Gate evaluations fired | 25 | Same | GOVERNANCE |
| Operators flagged | 13 | Same | GOVERNANCE |

## Generated report artifacts

| Report | Format | Source | Stage |
|---|---|---|---|
| Pilot markdown readout | markdown | `export_pilot_markdown()` → `demo_data/graphics/demo_full_pilot_readout.md` | READOUT |
| Executive brief | markdown | `export_executive_brief()` | READOUT |
| Decision report | dict | `decision_report()` | READOUT |
| Preferred manager objects | dict (8 objects) | `preferred_manager_objects()` | READOUT |
| Hypothesis map | markdown | `export_hypothesis_map()` | READOUT |
| Re-measurement report | markdown | `export_remeasurement_report()` | READOUT |
| Executive dashboard | HTML | `generate_executive_dashboard()` | READOUT |
| Composite score summary | dict | `composite_score_summary()` | BASELINE |

## Missing artifacts (governance gaps)

| Artifact | Required for | Status |
|---|---|---|
| Pilot Charter (formal) | DEFINE | PARTIAL — missing locked success criteria, authorized_by |
| Gate 1 Record | DEFINE | MISSING — no pilot-level launch readiness gate |
| Gate 2 Records | INTERVENE/VERIFY | MISSING — no pilot-level health gate |
| Gate 3 Record | DECIDE | MISSING — no pilot-level closure gate |
| Decision Record | DECIDE | MISSING — no closure decision capability |
| Success Criteria (locked) | DEFINE | MISSING — no success-criteria locking mechanism |
| Baseline Snapshot (immutable) | BASELINE | MISSING — no immutable snapshot (recomputed each time) |
| Replication Results | VERIFY | NOT RUN — capability exists but not exercised |
| External Reference Field | BASELINE | MISSING — reference is synthetic (derived from cohort) |

## Data integrity

| Check | Result |
|---|---|
| All demo data files present | ✅ Validated via `PilotService` instantiation |
| Observation count matches | ✅ 1,668 (file) = 1,668 (service) |
| Operator count matches | ✅ 50 (file) = 50 (service) |
| Intervention count matches | ✅ 12 (file) = 12 (service) |
| Cohort medians match reference field | ✅ leverage 12.177, yield 6.0072, token_snr 0.3417, construction 1.7338 |
| Verification outcomes match intervention outcomes | ✅ 5 SUCCESS, 2 PARTIAL, 2 NO_EFFECT, 3 NEGATIVE |
| Test suite passing | ✅ 676 passed |
