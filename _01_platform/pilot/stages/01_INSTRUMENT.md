# Stage 01 — INSTRUMENT

## Purpose

Collect telemetry from the defined population during the defined window.
Establish the observation stream that will feed all downstream measurement,
diagnosis, and verification.

## Governing question

> Can we observe the population's AI operating behavior with sufficient
> coverage and quality to measure?

## Inputs

- Validated `PilotConfiguration` (from DEFINE)
- Operator identities (pseudonymous IDs, cross-system identity mappings)
- Provider access (file exports or API credentials)
- Governance clearance (purpose, disclosure, consent)

## Upsilon actions

1. Resolve operator identities across systems via `add_operator_identity()`
   / `resolve_operator_identity()` — maps system-specific IDs to canonical
   operator IDs.
2. Ingest telemetry via file adapters (`FixtureAdapter`, `ClaudeAdapter`,
   `CodexAdapter`, `GitHubAdapter`) or API adapters (`ClaudeApiAdapter`,
   `CodexApiAdapter`, `GroqApiAdapter`).
3. Full canonical ingest (`ingest_full()`) emits Observation + System +
   SystemVersion + Session + Task + Artifact + Lineage objects.
4. Validate observations via `validate_observations()` — checks missingness,
   impossible values, duplicates, provenance, source confidence.
5. Run governance checks via `check_ingestion_governance()` — purpose
   limitation, employee disclosure, consent gates block ingestion if not met.
6. Persist observations via `SQLiteRepository.insert_observations()` (if
   persistence enabled).

## Existing implementation

| Capability | Implementation | Evidence |
|---|---|---|
| File ingest (fixture) | `FixtureAdapter.ingest()` loads from JSONL/CSV | `src/ingest/fixture.py` |
| File ingest (provider) | `ClaudeAdapter`, `CodexAdapter`, `GitHubAdapter` parse provider exports | `src/ingest/claude.py`, `src/ingest/codex.py`, `src/ingest/github.py` |
| API ingest | `ClaudeApiAdapter`, `CodexApiAdapter`, `GroqApiAdapter` — stub mode without key, live mode with key | `src/ingest/api_*.py` |
| Full canonical ingest | `ingest_full()` returns typed canonical objects | `src/ingest/claude.py`, `src/ingest/codex.py` |
| Observation schema | `Observation` dataclass + JSON Schema | `src/domain/observation.py`, `schemas/observation.schema.json` |
| Validation | `validate_observations()` + `validate_against_schema_file()` | `src/ingest/validate.py` |
| Governance gates | `GovernanceEnforcement.check_ingestion()` — purpose/disclosure/consent | `src/governance/enforcement.py` |
| Cross-system identity | `OperatorIdentity` with conflict detection | `src/domain/operator_identity.py` |
| Persistence | `SQLiteRepository.insert_observations()` | `src/repository/sqlite_repository.py` |
| CLI surface | `enterprise ingest fixture/claude/codex/github/api-*` | `src/cli/main.py` |
| MCP surface | indirect via service | `src/mcp_server/server.py` |

## Checklist

- [ ] Operator identities resolved (cross-system mappings added)
- [ ] Telemetry ingested from all relevant providers
- [ ] Observations validated (no blocking errors)
- [ ] Governance gates passed (purpose, disclosure, consent)
- [ ] Observation count meets minimum threshold for measurement
- [ ] Data quality checks run (no BLOCKING severity)

## Required evidence

- `IngestResult` with observation count, errors, warnings
- Validation result (errors list, warnings list)
- Governance check result (permitted, reasons)
- Data quality summary (OK/WARNING/BLOCKING counts)

## Artifact

**Instrumentation Readiness Record** — confirms the observation stream is
sufficient for baseline measurement. See
`examples/ACME-001/01_INSTRUMENTATION_READINESS.md`.

## Exit criteria

- Observation count ≥ minimum for eligibility (per `EligibilityConfig`)
- No BLOCKING data quality issues
- Governance gates satisfied
- All active providers ingested

## Failure states

- Insufficient observations (sparse operators)
- BLOCKING data quality issues (missingness, impossible values)
- Governance gates blocked (no purpose, no disclosure, no consent)
- Provider API access failure
- Identity conflicts (same system ID mapped to different operators)

## Next stage

→ **02_BASELINE** — compute canonical metrics and establish the measurable
baseline.
