# ACME-001 — Intervention Records

> **COMPLETE** — 12 interventions assigned with declared targets and
> follow-up windows. All values validated from runtime on 2026-09-06.

## Intervention catalog (12 entries)

| ID | Name | Class | Target metric | Typical followup days | Source |
|---|---|---|---|---|---|
| CTX-001 | Persistent Project Context | workflow | leverage | 14 | `src/interventions/registry.py` |
| CTX-002 | Context Handoff Template | workflow | leverage | 14 | Same |
| CTX-003 | Memory Tool Trial | tooling | leverage | 21 | Same |
| FRM-001 | Task Decomposition Guide | guide | yield | 14 | Same |
| FRM-002 | Acceptance-Criteria Template | guide | yield | 14 | Same |
| MOD-001 | Model Routing Trial | tooling | yield | 21 | Same |
| AGT-001 | Agent/Tool Selection Review | tooling | yield | 14 | Same |
| REV-001 | Verification Loop | workflow | token_snr | 14 | Same |
| STD-001 | Standard Project Scaffold | workflow | any | 21 | Same |
| COA-001 | Operator Coaching Session | human | yield | 30 | Same |
| LRN-001 | External Training Assignment | partner | any | 90 | Same |
| STG-001 | Stage Placement Trial | workflow | yield | 21 | Same |

> `target_metric = any` means `InterventionCatalogEntry.target_metric`
> is `None` — any metric is accepted by
> `InterventionRegistry.validate_target_metric()`. `typical_followup_days`
> is the catalog default; the actual follow-up window is set at
> assignment time.

## Pattern → intervention mapping

| Pattern | Recommended interventions | Source |
|---|---|---|
| P-CTX-01 | CTX-001, CTX-002, CTX-003 | `src/interventions/registry.py` |
| P-CTX-02 | FRM-001, MOD-001 | Same |
| P-BURN-01 | COA-001, CTX-001, FRM-002 | Same |
| P-MODEL-01 | MOD-001, AGT-001 | Same |

## Assigned interventions (12)

All 12 interventions are pre-loaded from `demo_data/interventions.json`:

| ID | Operator | Catalog | Pattern | Target metric | Start date | Followup days | Outcome | Source |
|---|---|---|---|---|---|---|---|---|
| int_001 | op_047 | COA-001 | P-BURN-01 | yield | 2026-08-01 | 14 | PARTIAL | `PilotService.interventions` |
| int_002 | op_004 | COA-001 | P-BURN-01 | yield | 2026-08-01 | 14 | NO_EFFECT | Same |
| int_003 | op_030 | COA-001 | P-BURN-01 | yield | 2026-08-01 | 14 | SUCCESS | Same |
| int_004 | op_045 | COA-001 | P-BURN-01 | yield | 2026-08-01 | 14 | SUCCESS | Same |
| int_005 | op_031 | CTX-001 | P-CTX-01 | leverage | 2026-08-01 | 14 | NEGATIVE | Same |
| int_006 | op_038 | FRM-001 | P-BURN-01 | yield | 2026-08-01 | 14 | NEGATIVE | Same |
| int_007 | op_010 | CTX-001 | P-CTX-01 | leverage | 2026-08-01 | 14 | SUCCESS | Same |
| int_008 | op_026 | CTX-001 | P-CTX-01 | leverage | 2026-08-01 | 14 | SUCCESS | Same |
| int_009 | op_025 | MOD-001 | P-MODEL-01 | yield | 2026-08-01 | 14 | NO_EFFECT | Same |
| int_010 | op_020 | CTX-001 | P-CTX-01 | leverage | 2026-08-01 | 14 | NEGATIVE | Same |
| int_011 | op_029 | FRM-001 | P-BURN-01 | yield | 2026-08-01 | 14 | SUCCESS | Same |
| int_012 | op_005 | CTX-001 | P-CTX-01 | leverage | 2026-08-01 | 14 | PARTIAL | Same |

## Outcome distribution

| Outcome | Count | Source |
|---|---|---|
| SUCCESS | 5 | `PilotService.interventions` (synthetic_outcome) |
| PARTIAL | 2 | Same |
| NO_EFFECT | 2 | Same |
| NEGATIVE | 3 | Same |

> Negative outcomes (NO_EFFECT, NEGATIVE) are representable and
> reportable. They are not hidden. This is correct governance.

## Authorization

| Field | Value | Status |
|---|---|---|
| Authorized by | (not recorded on interventions) | **MISSING** — demo data does not include authorized_by |
| Authorization enforced | Yes (in CLI/MCP layer) | `src/cli/main.py` `intervention assign --authorized-by` |
| Decision use | WORKFLOW_EXPERIMENTATION | `decision_use_for_intervention()` |

> **Gap:** The demo interventions do not record `authorized_by`. The
> CLI/MCP layer enforces authorization for new assignments, but the
> pre-loaded demo data does not include it. For a real pilot, every
> intervention must have an authorized_by recorded.

## Experiments

| Field | Value | Source |
|---|---|---|
| Experiments created | 0 (in demo) | `PilotService.experiments` |
| Experiment capability | Implemented | `PilotService.create_experiment()` |

## What these interventions reveal

1. **Intervention assignment is complete.** 12 interventions with declared
   target_metric, followup_days, and reason_pattern.
2. **Outcomes are diverse** — 5 SUCCESS, 2 PARTIAL, 2 NO_EFFECT, 3 NEGATIVE.
   This is realistic and demonstrates that negative outcomes are
   representable.
3. **Authorization is missing** on demo data — a gap for real pilots.
4. **Interventions are pre-loaded**, not assigned through the live
   assignment workflow. The live workflow (`assign_intervention()`)
   requires authorized_by and enforces it, but the demo bypasses this.
