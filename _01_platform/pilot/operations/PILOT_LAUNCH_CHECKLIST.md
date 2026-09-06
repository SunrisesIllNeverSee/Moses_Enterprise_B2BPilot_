# PILOT_LAUNCH_CHECKLIST.md

> Checklist of items that must be true BEFORE launching an Upsilon
> Enterprise Pilot (i.e., before Gate 1 can return LAUNCH or
> LAUNCH_WITH_CONDITIONS).
>
> This checklist is executed at the end of the DEFINE stage. See
> `PILOT_RUNBOOK.md` Stage 00 for the full DEFINE procedure.

## Charter completeness

- [ ] Pilot ID assigned (e.g., ACME-001 format: `^[A-Z]+-\d{3}$`)
- [ ] Enterprise name recorded
- [ ] Tenant ID recorded
- [ ] Cohort ID recorded
- [ ] Pilot question stated (what decision will this pilot inform?)
- [ ] Best buyer identified (from commercial pilot template or
  manually)
- [ ] Created by recorded
- [ ] Authorized by recorded (Decision Authority — different from
  Pilot Creator)

## Population boundary

- [ ] Operator count confirmed (25–100)
- [ ] Operator IDs enumerated or selection criteria defined
- [ ] Teams identified
- [ ] Selection criteria documented (why these operators)

## Duration boundary

- [ ] Window start date set
- [ ] Window end date set
- [ ] Window days confirmed (default 30)
- [ ] Follow-up window defined (if intervention pilot — typically
  +14 days)

## Scope

- [ ] Eval families selected (EVAL-001 through EVAL-015)
- [ ] Commercial pilot template referenced (if applicable)
- [ ] Deployment level set (1=baseline, 2=intervention, 3=production)

## Success criteria (CRITICAL — must be locked before measurement)

- [ ] Each criterion has: criterion_id, metric, threshold, direction,
  aggregation, rationale, closure_mapping
- [ ] Criteria are measurable (reference specific metrics, not vague
  goals)
- [ ] Criteria are bounded (reference the pilot's population and
  duration)
- [ ] Criteria are decision-oriented (map to STOP/EXTEND/EXPAND/DEPLOY)
- [ ] Criteria are developmental (measure operating behavior, not
  personnel performance)
- [ ] `locked_at` timestamp recorded (MUST precede any measurement)
- [ ] `locked_by` identity recorded

> **If success criteria are not locked, Gate 1 cannot return LAUNCH.**
> This is the most common failure state. Do not proceed without
> locked criteria.

## Governance

- [ ] `decision_use_default` = DEVELOPMENTAL
- [ ] `privacy_class` = pseudonymous_real (for real customers)
- [ ] `synthetic` = false (for real customers)
- [ ] `purpose_id` recorded
- [ ] `consent_model` set (opt_in / opt_out / mandated)
- [ ] Employee disclosure plan confirmed (customer will disclose to
  operators)
- [ ] Consent collection plan confirmed

## Configuration validation

- [ ] `enterprise configure validate` passes with no errors
  (warnings are acceptable)
- [ ] Configuration saved (JSON file)
- [ ] Metric registry version confirmed (0.2)
- [ ] Reference field version confirmed

## Technical readiness

- [ ] Provider telemetry access path confirmed (file export or API)
- [ ] API keys obtained (if API ingestion)
- [ ] Operator identity mapping approach confirmed
- [ ] Data storage path confirmed (SQLite for persistence)

## Gate 1 evaluation

- [ ] All above items complete
- [ ] Gate 1 review executed per `GATE_REVIEW_RUNBOOK.md`
- [ ] Gate 1 outcome recorded:
  - [ ] LAUNCH — all criteria met, proceed to INSTRUMENT
  - [ ] LAUNCH_WITH_CONDITIONS — minor gaps, proceed with documented
    conditions
  - [ ] DEFER — gaps must be addressed before launch, do not proceed
  - [ ] DECLINE — fundamental issues, pilot is not valid

## If LAUNCH or LAUNCH_WITH_CONDITIONS

- [ ] Pilot Charter artifact created and stored
- [ ] Gate 1 record created and stored
- [ ] Customer notified of launch
- [ ] Operators notified (if applicable per consent model)
- [ ] Proceed to Stage 01 — INSTRUMENT (`PILOT_RUNBOOK.md`)

## If DEFER

- [ ] Document gaps that must be addressed
- [ ] Set re-evaluation date
- [ ] Do NOT begin telemetry collection
- [ ] Re-execute this checklist after gaps are addressed

## If DECLINE

- [ ] Document why the pilot is not valid
- [ ] Do NOT proceed
- [ ] Consider whether a different scope or question could produce a
  valid pilot

## Implementation note

> The platform does not yet implement `pilot_id`, success criteria
> locking, or Gate 1 evaluation as runtime objects. For the first
> real pilot, this checklist is executed manually:
> - The Pilot Charter is created as a document (see
>   `pilot/governance/PILOT_CHARTER.md` for the structure)
> - Success criteria are locked by recording them in the charter
>   document with a timestamp
> - Gate 1 is evaluated by the Decision Authority reviewing the
>   charter
> See `FIRST_CUSTOMER_READINESS.md` for details.
