# SOURCES.md

> Sources consulted for the pilot comparison matrix and external
> benchmark analysis.
>
> These sources inform the structural comparison, not competitor
> positioning. The comparison focuses on architecture, not market
> positioning.

## Methodology sources

### Bounded evaluation frameworks

| Source | Type | Relevance |
|---|---|---|
| Kohavi, T., et al. "Trustworthy Online Controlled Experiments" (2020) | Book | A/B testing methodology — the standard for bounded online evaluation |
| Friedman, L., et al. "Fundamentals of Clinical Trials" (2015) | Book | Clinical trial methodology — gold standard for governed evaluation |
| Nielsen, J. "Usability Engineering" (1993) | Book | HCI design pilot methodology — bounded UX evaluation |
| Pressman, R. "Software Engineering: A Practitioner's Approach" | Book | PoC methodology in enterprise IT |

### Governance frameworks

| Source | Type | Relevance |
|---|---|---|
| FDA "Guidance for Industry: Clinical Trial Endpoints" | Regulatory | Decision gate structure (primary/secondary endpoints) |
| ICH-E9 "Statistical Principles for Clinical Trials" | Regulatory | Pre-registration and protocol locking |
| EU GDPR "Articles 6, 7, 22" | Regulatory | Purpose limitation, consent, automated decision-making |
| NIST "AI Risk Management Framework" (2023) | Standard | AI governance principles |

### Measurement science

| Source | Type | Relevance |
|---|---|---|
| Stevens, S. "On the Theory of Scales of Measurement" (1946) | Paper | Measurement scale types (ratio, interval, ordinal, nominal) |
| Cronbach, L. "Coefficient Alpha and the Internal Structure of Tests" (1951) | Paper | Reliability of composite measures |
| Messick, S. "Validity of Psychological Assessment" (1995) | Paper | Validity framework for composite scores |

## Internal sources (repository evidence)

| Source | Path | Relevance |
|---|---|---|
| AGENTS.md | `_01_platform/AGENTS.md` | Repository operating instructions |
| MANIFEST.yaml | `_01_platform/MANIFEST.yaml` | Package self-declaration (modules, tests, demo data) |
| Metric registry | `_01_platform/demo_data/metric_registry.json` | 5 canonical metric definitions (v0.2) |
| Demo manifest | `_01_platform/demo_data/demo_manifest.json` | ACME demo data specification |
| Cohort data | `_01_platform/demo_data/cohort.json` | ACME-001 cohort definition |
| Reference field | `_01_platform/demo_data/reference_field.json` | Synthetic reference population |
| Pilot configuration | `_01_platform/src/domain/pilot_configuration.py` | PilotConfiguration dataclass |
| Production gate | `_01_platform/src/domain/production_gate.py` | Operator-level gate rules |
| Eval registry | `_01_platform/src/config/eval_registry.py` | 15 eval families |
| Pilot registry | `_01_platform/src/config/pilot_registry.py` | 12 commercial pilot templates |
| Governance enforcement | `_01_platform/src/governance/enforcement.py` | Purpose/disclosure/consent/bias/challenge/correction |
| Service layer | `_01_platform/src/service.py` | PilotService — shared service for CLI/TUI/MCP |
| Test suite | `_01_platform/tests/` | 676 tests (all passing) |

## Validation sources (runtime evidence)

| Validation | Date | Method | Result |
|---|---|---|---|
| Test suite | 2026-09-06 | `python3 -m pytest tests/ -q` | 676 passed |
| Pilot status | 2026-09-06 | `PilotService.pilot_status()` | 50 operators, 1668 observations, 12 interventions |
| Cohort medians | 2026-09-06 | `PilotService.cohort_medians()` | leverage 12.177, yield 6.0072, token_snr 0.3417, construction 1.7338 |
| Divergence counts | 2026-09-06 | `PilotService.divergence_counts()` | 5 LO-USAGE/HI-OP, 3 HI-USAGE/LO-OP, 12 LO/LO, 30 MIXED |
| Pattern detection | 2026-09-06 | `PilotService.detect_cohort_patterns()` | 56 patterns across 39 operators |
| Diagnosis generation | 2026-09-06 | `PilotService.generate_cohort_diagnoses()` | 56 diagnoses (all HYPOTHESIS) |
| Verification | 2026-09-06 | `PilotService.verify_all_interventions()` | 12 results (5 SUCCESS, 2 PARTIAL, 2 NO_EFFECT, 3 NEGATIVE) |
| Gate evaluation | 2026-09-06 | `PilotService.evaluate_cohort_gates()` | 150 evaluations, 25 fired, 13 operators flagged |
| Benchmark summary | 2026-09-06 | `PilotService.benchmark_summary("leverage")` | 50 operators, peer class selected |

## Notes on source quality

- **Internal sources** are primary evidence — they are the actual
  implementation and data being evaluated.
- **Validation sources** are runtime-verified — values were confirmed
  by instantiating `PilotService` and exercising each surface.
- **Methodology sources** are established references in their respective
  fields. They inform the structural comparison but do not define the
  Upsilon protocol (which is defined in `UPSILON_PILOT_SPEC.md`).
- **No competitor product sources** are included — this is an
  architectural comparison, not market positioning.
