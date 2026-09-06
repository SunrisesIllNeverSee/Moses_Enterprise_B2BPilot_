# PRE_PILOT_CHECKLIST.md

> Checklist of items that must be true BEFORE starting the customer
> intake process for an Upsilon Enterprise Pilot.
>
> This is not the launch checklist. This is the readiness checklist
> for the Upsilon operator and the platform.

## Platform readiness

- [ ] Upsilon platform installed and `pytest tests/ -q` passes
  (currently 676 tests)
- [ ] `enterprise` CLI is on PATH and `./enterprise --help` works
- [ ] TUI launches without errors (`./enterprise` with no args, or
  TUI mode)
- [ ] MCP server starts without errors (if MCP integration is used)
- [ ] Demo data loads correctly (`enterprise demo status` shows
  50 operators, 1668 observations, 12 interventions)
- [ ] Metric registry is version 0.2 with 5 canonical metrics
  (`enterprise metrics registry`)
- [ ] Intervention catalog has 12 entries
  (`enterprise intervention catalog`)
- [ ] Reference field is loaded
  (`enterprise benchmark summary --metric leverage`)

## Operator readiness (Upsilon side)

- [ ] Pilot Creator identified (will define the pilot and create
  charter)
- [ ] Decision Authority identified (will approve launch and make
  closure decision — MUST be different from Pilot Creator)
- [ ] Pilot Operator identified (will run the platform — may be same
  as Pilot Creator for first pilot)
- [ ] All roles understand the pilot lifecycle
  (`pilot/PILOT_LIFECYCLE.md`)
- [ ] All roles understand the three gates
  (`pilot/governance/DECISION_GATES.md`)
- [ ] All roles understand the four closure outcomes
  (`pilot/governance/CLOSURE_OUTCOMES.md`)
- [ ] Pilot Creator has read `PILOT_RUNBOOK.md` end-to-end

## Governance readiness

- [ ] Decision-use labels understood (DEVELOPMENTAL, ASSOCIATION,
  HYPOTHESIS — never PERSONNEL, never CAUSATION)
- [ ] Privacy model understood (pseudonymous operator IDs, no raw
  content, token counts + pointer only)
- [ ] Governance gates understood (purpose limitation, employee
  disclosure, consent, bias review, challenge, correction)
- [ ] `skip_governance` bypass is NOT used for real customer data

## Customer readiness (pre-intake)

- [ ] Customer has AI operators using one or more supported providers
  (ChatGPT, Claude, Codex, GitHub Copilot, Cursor)
- [ ] Customer has 25–100 operators who can be included in the pilot
- [ ] Customer has a decision-maker who can serve as Customer Sponsor
- [ ] Customer is willing to commit to a bounded duration (30 days
  baseline + 14 days follow-up for intervention pilots)
- [ ] Customer understands this is an evaluation, not a monitoring
  program
- [ ] Customer understands all outputs are DEVELOPMENTAL (no
  personnel evaluations)

## Technical readiness

- [ ] Provider telemetry access path is identified (file export or
  API)
- [ ] If API: API keys are obtainable for each provider
- [ ] If file export: customer can export provider usage data
- [ ] Operator identity mapping approach is identified (how to map
  system-specific IDs to canonical operator IDs)
- [ ] Data storage path is identified (in-memory for demo, SQLite
  for persistence)

## What this checklist does NOT verify

- Customer qualification (see `CUSTOMER_INTAKE.md`)
- Pilot configuration validity (see `PILOT_LAUNCH_CHECKLIST.md`)
- Gate 1 readiness (see `GATE_REVIEW_RUNBOOK.md`)
- First customer technical blockers (see
  `FIRST_CUSTOMER_READINESS.md`)
