# HARDENING_PLAN.md

> Production hardening plan for real-customer pilot deployment.
>
> This plan covers PRODUCTION_HARDENING, DATA, and PRIVACY gaps from
> `GAP_REGISTER.md` — capabilities that exist but need production
> hardening for real-customer use. It does NOT cover CANON, GOVERNANCE,
> RUNTIME, UX, or EVIDENCE gaps (see `PILOT_MODE_BUILD_PLAN.md`).

## Hardening areas

### H1 — Real external reference field (GAP-012)

**Current state:** `ReferencePopulation` is synthetic, derived from the
acme_50 cohort itself. All 50 operators are benchmarked using the `peer`
class (compared against each other).

**Hardening required:**
1. Construct an external reference field from aggregated, anonymized
   data across multiple cohorts (with consent and governance)
2. OR obtain a public reference field from a benchmark source
3. Version the reference field and record its provenance
4. Validate that the external reference field produces different
   benchmark class selections (not all `peer`)
5. Document the reference field's limitations and appropriate use

**Risk if not hardened:** Benchmarking compares operators against
themselves, which inflates percentile ranks and reduces benchmarking
validity. Real customer pilots would produce misleading benchmarks.

**Test plan:**
- Construct test reference field from 2+ cohorts
- Verify benchmark class selection changes (not all `peer`)
- Verify percentile ranks differ from self-benchmark
- Document reference field provenance

### H2 — Real governance gate enforcement (GAP-013)

**Current state:** Demo bypasses governance gates with
`skip_governance=True`. Purpose limitation, employee disclosure, and
consent gates are implemented but not exercised.

**Hardening required:**
1. Remove `skip_governance=True` bypass for non-synthetic pilots
2. Implement consent recording workflow (operator acknowledges consent)
3. Implement employee disclosure acknowledgment process (manager
   acknowledges disclosure to employees)
4. Implement purpose limitation registration (purpose_id recorded
   before ingestion)
5. Test that governance gates block ingestion when not satisfied
6. Test that governance gates permit ingestion when satisfied

**Risk if not hardened:** Real customer data could be ingested without
proper governance clearance, creating privacy and compliance violations.

**Test plan:**
- Test ingestion blocked without purpose_id
- Test ingestion blocked without disclosure acknowledgment
- Test ingestion blocked without consent
- Test ingestion permitted with all gates satisfied
- Test audit log records all gate evaluations

### H3 — Persistent pilot state (GAP-014)

**Current state:** Demo uses in-memory `DemoRepository`. Pilot state,
charter, success criteria, gates, and decisions are not persisted.
`SQLiteRepository` exists but is not used for pilot governance objects.

**Hardening required:**
1. Add pilot state, charter, success criteria, gates, decisions tables
   to `SQLiteRepository`
2. Add load/save methods for each governance object
3. Add `--persist` flag to CLI pilot commands
4. Test that pilot state survives service restart
5. Test that governance objects are persisted and loadable
6. Implement pilot archive for terminated pilots

**Risk if not hardened:** Pilot state is lost on service restart.
Governance objects (charter, criteria, gates, decisions) are not
auditable. Real customer pilots require persistence for compliance.

**Test plan:**
- Test pilot state persisted to SQLite
- Test pilot state loaded from SQLite after restart
- Test governance objects (charter, criteria, gates, decisions) persisted
- Test audit trail of all governance actions

### H4 — Real provider API ingestion (GAP-016)

**Current state:** API adapters (`ClaudeApiAdapter`, `CodexApiAdapter`,
`GroqApiAdapter`) exist in stub mode. Live mode requires API keys and
has not been tested with real provider APIs.

**Hardening required:**
1. Obtain API keys for each provider (Claude, Codex, Groq)
2. Test live ingestion with real data
3. Handle rate limits (exponential backoff, retry queue)
4. Handle errors (API errors, network errors, schema drift)
5. Validate observation schema against real provider data
6. Test full canonical ingest with real API data (Observation + System +
   Session + Task + Artifact + Lineage)
7. Document API key management and rotation

**Risk if not hardened:** API ingestion may fail with real provider
APIs due to rate limits, schema drift, or unhandled errors. Real
customer pilots depend on reliable telemetry ingestion.

**Test plan:**
- Test live ingestion with each provider API
- Test rate limit handling (mock rate limit responses)
- Test error handling (mock API errors, network errors)
- Test schema validation against real provider data
- Test full canonical ingest with real API data

### H5 — authorized_by recording (GAP-024)

**Current state:** CLI/MCP enforces `authorized_by` for new intervention
assignments, but pre-loaded demo data does not include it.

**Hardening required:**
1. Add `authorized_by` field to `Intervention` domain object
2. Require `authorized_by` for all intervention assignments (not just
   CLI/MCP layer)
3. Test that intervention assignment fails without `authorized_by`
4. Backfill demo data with `authorized_by` (for consistency)

**Risk if not hardened:** Interventions could be assigned without
authorization in programmatic use (bypassing CLI/MCP enforcement).

**Test plan:**
- Test intervention assignment fails without `authorized_by`
- Test intervention assignment succeeds with `authorized_by`
- Test `authorized_by` is persisted and auditable

## Hardening priority

| Hardening area | Priority | Maturity target | Risk if skipped |
|---|---|---|---|
| H1 Real external reference field | P1 | T2 | Misleading benchmarks |
| H2 Real governance gate enforcement | P1 | T2 | Privacy/compliance violations |
| H3 Persistent pilot state | P1 | T2 | State loss, no audit trail |
| H4 Real provider API ingestion | P1 | T2 | Ingestion failure |
| H5 authorized_by recording | P2 | T2 | Unauthorized interventions |

## What this plan does NOT include

- No new analytical capability (measurement, diagnosis, intervention,
  verification, reporting are all existing)
- No changes to existing metric definitions or scoring formulas
- No changes to existing governance labels
- No signup/auth/billing/customer portals
- No generic project-management infrastructure
