# Stage 00 — DEFINE

## Purpose

Establish the bounded scope of the pilot: which enterprise, which population,
which window, which objectives, which success criteria, and which eval
families will be active. The pilot does not exist until it is defined.

## Governing question

> Is this a valid, bounded evaluation with a clear question and locked
> success criteria?

## Inputs

- Enterprise identity (tenant)
- Population boundary (operator set or selection criteria)
- Duration boundary (window start/end)
- Pilot question (what decision will this pilot inform?)
- Success criteria (locked before measurement)
- Selected eval families (EVAL-001–EVAL-015)
- Governance metadata (decision-use default, privacy class, authorized_by)

## Upsilon actions

1. Create or select a `PilotConfiguration` via `PilotConfigurator.from_outcome()`
   (commercial pilot template) or `PilotConfigurator.from_alacarte()` (eval
   family selection).
2. Define cohort parameters via `CohortConfig` (window_days, min/max_operators,
   cohort_id, tenant_id).
3. Select eval families — the 15 eval families (EVAL-001–EVAL-015) determine
   which analytical capabilities are active.
4. Configure production gates via `GatesConfig` (enable/disable, thresholds).
5. Configure outcome join via `OutcomeJoinConfig` (external KPI attachment,
   ASSOCIATION-only).
6. Set governance metadata via `GovernanceConfig` (synthetic flag,
   decision_use_default, authorized_by, privacy_class).
7. Validate configuration via `ConfigValidator.validate()`.
8. Save configuration as JSON for persistence.

## Existing implementation

| Capability | Implementation | Evidence |
|---|---|---|
| Pilot configuration | `PilotConfiguration` dataclass with eval/cohort/gates/outcome/governance/reference sections | `src/domain/pilot_configuration.py` |
| Commercial pilot templates | 12 templates with question, best_buyer, eval_families, deployment_level | `src/config/pilot_registry.py` |
| Eval family registry | 15 eval families with implementation status, service methods, CLI/MCP/TUI surfaces | `src/config/eval_registry.py` |
| Configurator | `from_outcome()` / `from_alacarte()` builders | `src/config/configurator.py` |
| Validation | `ConfigValidator.validate()` → errors + warnings | `src/config/validation.py` |
| CLI surface | `enterprise configure from-pilot/from-evals/show/validate/report` | `src/cli/main.py` |
| TUI surface | Screen C (Configure) — bespoke pilot menu | `src/tui/app.py` |
| MCP surface | `list_pilot_options`, `create_pilot_configuration`, `validate_pilot_configuration` | `src/mcp_server/server.py` |

## Checklist

- [ ] Enterprise/tenant identified
- [ ] Population boundary defined (operator count, selection criteria)
- [ ] Duration boundary defined (start date, end date)
- [ ] Pilot question stated (what decision will this inform?)
- [ ] Success criteria locked (before any measurement)
- [ ] Eval families selected
- [ ] Production gates configured (if enabled)
- [ ] Outcome join configured (if external KPIs)
- [ ] Governance metadata set (authorized_by, privacy_class, decision_use)
- [ ] Configuration validated (no errors)
- [ ] Configuration saved

## Required evidence

- `PilotConfiguration` JSON artifact (saved file)
- Validation result (no errors)
- Pilot charter document (see `governance/PILOT_CHARTER.md`)

## Artifact

**Pilot Charter** — the immutable definition record. See
`governance/PILOT_CHARTER.md` and `schemas/PILOT_CHARTER_SCHEMA.md`.

## Exit criteria

- Configuration is valid (no validation errors)
- Success criteria are locked before measurement
- Authorized approver has signed off
- **GATE 1 (LAUNCH READINESS) passed**: LAUNCH or LAUNCH_WITH_CONDITIONS

## Failure states

- Population too small (< min_operators)
- Duration too short for meaningful measurement
- Success criteria not defined or not locked
- No authorized approver
- Governance gates not satisfied (purpose, disclosure, consent)

## Next stage

→ **01_INSTRUMENT** — begin telemetry collection for the defined population.
