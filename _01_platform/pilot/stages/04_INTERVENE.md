# Stage 04 — INTERVENE

## Purpose

Apply controlled interventions to selected operators based on diagnostic
hypotheses. Each intervention declares its target metric and follow-up
window before execution, ensuring pre/post comparison is possible.

## Governing question

> What controlled changes should we apply, and what do we expect to measure?

## Inputs

- Diagnostic findings with recommended interventions (from DIAGNOSE)
- Intervention catalog (12 entries)
- Authorized approver (required for assignment)
- Baseline measurements (for pre/post comparison)

## Upsilon actions

1. Review recommended interventions via `recommend_interventions()` —
   maps diagnoses to catalog entries.
2. Browse intervention catalog via `intervention_catalog()` — 12 entries
   with type, target metric, followup days.
3. Assign interventions via `assign_intervention()` — requires:
   - `authorized_by` (enforced in CLI/MCP)
   - `operator_id`
   - `catalog_id`
   - `target_metric` (declared before execution)
   - `followup_days` (declared before execution)
   - `reason_pattern` (which diagnosis prompted this)
4. Optionally create predeclared experiments via `create_experiment()` —
   predeclared metrics before execution.
5. Record the intervention as an `Intervention` domain object with
   `synthetic_outcome` (initially unset, updated on close).
6. **GATE 2 (PILOT HEALTH)** should be evaluated before and during
   intervention to ensure the pilot remains a valid experiment.

## Existing implementation

| Capability | Implementation | Evidence |
|---|---|---|
| Intervention catalog | 12 entries: CTX-001/002/003, FRM-001/002, MOD-001, AGT-001, REV-001, STD-001, COA-001, LRN-001, STG-001 | `src/interventions/registry.py` |
| Pattern→intervention mapping | P-CTX-01→[CTX-001,CTX-002,CTX-003], P-CTX-02→[FRM-001,MOD-001], P-BURN-01→[COA-001,CTX-001,FRM-002], P-MODEL-01→[MOD-001,AGT-001] | `src/interventions/registry.py` |
| Recommendation | `recommend_interventions()` | `src/interventions/manager.py`, `src/service.py` |
| Assignment | `assign_intervention()` — requires authorized_by + target_metric + followup_days | `src/service.py` |
| Experiment creation | `create_experiment()` — predeclared metrics | `src/service.py` |
| CLI surface | `enterprise intervention catalog/recommend/assign/close` | `src/cli/main.py` |
| TUI surface | Screen 7 (Interventions) | `src/tui/app.py` |
| MCP surface | `assign_intervention`, `close_intervention`, `create_experiment` | `src/mcp_server/server.py` |

## Checklist

- [ ] Interventions recommended from diagnoses
- [ ] Authorized approver identified for each assignment
- [ ] Each intervention declares target_metric before execution
- [ ] Each intervention declares followup_days before execution
- [ ] Each intervention records reason_pattern (which diagnosis prompted it)
- [ ] Interventions persisted (in-memory or SQLite)
- [ ] Gate 2 (Pilot Health) evaluated — pilot remains valid

## Required evidence

- `Intervention` records (operator, catalog_id, target_metric, followup_days,
  reason_pattern, start_date)
- Authorization records (who approved each intervention)
- Experiment records (if predeclared experiments created)

## Artifact

**Intervention Records** — the set of controlled changes applied. See
`examples/ACME-001/04_INTERVENTIONS.md` and
`schemas/INTERVENTION_SCHEMA.md`.

## Exit criteria

- All interventions have declared target_metric + followup_days
- All interventions have authorized_by recorded
- Intervention count is bounded (not every operator — controlled changes)
- Follow-up windows are scheduled

## Failure states

- No authorized approver (interventions cannot be assigned)
- Target metric not declared (cannot verify without a pre-declared target)
- Follow-up window not defined (cannot compute pre/post comparison)
- Too many interventions (not a controlled experiment — every operator
  intervened)
- Gate 2 fails: TERMINATE (pilot is no longer a valid experiment)

## Next stage

→ **05_VERIFY** — measure the results of interventions against the
pre-declared targets.
