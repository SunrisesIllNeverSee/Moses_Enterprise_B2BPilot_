# DECISION_LOG.md

> Consequential pilot-architecture decisions for the Upsilon
> Enterprise Pilot.
>
> This document is NON-CANONICAL. It records decisions and their
> rationale. The canonical specifications live in
> `pilot/UPSILON_PILOT_SPEC.md`, `pilot/governance/`, and
> `pilot/stages/`.
>
> Do NOT turn ordinary implementation changes into architectural
> decision records. Only consequential decisions that shaped the
> pilot design belong here.

## Format

| Date | Decision | Alternatives | Reason | Status | Supersedes |
|---|---|---|---|---|---|

## Decisions

| Date | Decision | Alternatives | Reason | Status | Supersedes |
|---|---|---|---|---|---|
| 2026-08-17 | Enterprise pilots may be concierge/high-touch | (a) Self-service signup flow; (b) Hybrid self-service + concierge | The first pilots require expert configuration, governance setup, and interpretation. Self-service would produce invalid pilots (no locked criteria, no governance, no decision authority). Concierge ensures quality and validity. Self-service may be added post-scale if warranted. | ACCEPTED | — |
| 2026-08-17 | Self-service is not required for pilot legitimacy | (a) Require self-service before any pilot; (b) Self-service optional | A pilot's legitimacy comes from bounded scope, locked criteria, governance, and terminal decision — not from how the customer signs up. Requiring self-service would delay the first pilot indefinitely for a feature that does not affect pilot validity. | ACCEPTED | — |
| 2026-08-17 | The pilot terminates in a decision | (a) Ongoing monitoring without closure; (b) Optional closure | Without a terminal decision, a pilot is indistinguishable from a monitoring program. The four closure outcomes (STOP/EXTEND/EXPAND/DEPLOY) force evidence-backed decisions and prevent indefinite pilots. This is the defining property of an Upsilon Enterprise Pilot. | ACCEPTED | — |
| 2026-08-17 | Success criteria should be locked before evaluation | (a) Lock after measurement (post-hoc); (b) No formal locking | Post-hoc criteria adjustment is confirmation bias — criteria can be redefined to match whatever was measured. Locking before measurement ensures the evaluation is honest and the decision is evidence-backed. | ACCEPTED | — |
| 2026-08-17 | Upsilon Pilot Mode is primarily an orchestration/control layer over existing capabilities | (a) Rebuild all capabilities from scratch; (b) Build new analytical capabilities | The platform already has 676 passing tests, 5 canonical metrics, 12 interventions, 6 pattern detectors, pre/post verification, outcome correlation, reporting, and governance enforcement. Rebuilding would waste demonstrated capability. Pilot Mode adds pilot identity, success criteria, gates, decision records, and state machine — the governance/orchestration layer that is missing. | ACCEPTED | — |
| 2026-08-17 | Functioning analytical surfaces should be reused rather than rebuilt | (a) Rebuild TUI/CLI/MCP surfaces; (b) New pilot-specific surfaces | The 12-screen TUI, 17 CLI command groups, and 27 MCP tools are demonstrated and tested. Pilot Mode adds a governance screen and pilot context fields to existing surfaces — it does not replace them. | ACCEPTED | — |
| 2026-08-17 | ACME-001 is the canonical synthetic reference pilot | (a) No reference pilot; (b) Use a real customer as reference | A synthetic reference is reproducible — anyone can run the demo and verify the same values. A real customer pilot cannot be shared publicly. ACME-001 demonstrates the full lifecycle (with illustrative gates/decision) and exposes gaps honestly. | ACCEPTED | — |
| 2026-08-17 | All diagnoses are HYPOTHESIS, never CONFIRMED | (a) Allow CONFIRMED status; (b) No status tracking | Upsilon is observational, not experimental. Interventions are assigned based on hypotheses, not random assignment. Claiming CONFIRMED would overstate the evidence. HYPOTHESIS is the honest representation. | ACCEPTED | — |
| 2026-08-17 | All outcome claims are ASSOCIATION, never CAUSATION | (a) Allow CAUSATION claims; (b) No claim-type enforcement | Without random assignment, causation cannot be established. ASSOCIATION is the honest representation. The governance enforcement layer (`src/outcomes/governance.py`) enforces this. | ACCEPTED | — |
| 2026-08-17 | All evaluations are DEVELOPMENTAL, never PERSONNEL | (a) Allow PERSONNEL decision-use; (b) No decision-use tracking | Personnel evaluation creates legal exposure, destroys trust, and misuses the platform. DEVELOPMENTAL use (coaching, enablement, workflow improvement) is the legitimate purpose. The governance enforcement layer enforces this. | ACCEPTED | — |
| 2026-08-17 | The 5 canonical metrics are frozen at registry v0.2 | (a) Allow metric evolution; (b) Per-pilot metric definitions | Cross-pilot comparability requires stable metric definitions. If metrics change, baselines from different pilots cannot be compared. The frozen registry ensures longitudinal comparability. | ACCEPTED | — |
| 2026-08-17 | The 12-entry intervention catalog is fixed | (a) Configurable catalog; (b) Per-pilot custom interventions | A fixed catalog ensures interventions are standardized and comparable across pilots. Custom interventions would make cross-pilot comparison impossible and introduce uncontrolled variation. | ACCEPTED | — |
| 2026-08-17 | Composite score is a distribution, not a leaderboard | (a) Rank operators 1–N; (b) No composite | Leaderboards create competitive dynamics that undermine developmental purpose. A distribution (medians, percentiles, p10/p90) provides measurement without ranking. `no_false_leaderboards: True` is enforced in the benchmark engine. | ACCEPTED | — |
| 2026-08-17 | No raw content is stored — token counts and pointers only | (a) Store raw prompts/responses; (b) Store summaries | Raw content creates privacy risk, storage bloat, and potential for content-based personnel evaluation. Token counts + `raw_source_reference` pointers provide measurement without exposure. The `Observation` dataclass has no raw content field. | ACCEPTED | — |
| 2026-08-17 | Operator IDs are pseudonymous | (a) Real names/emails; (b) Anonymized (no mapping) | Pseudonymous IDs (op_001) protect privacy while allowing cross-system identity mapping. Fully anonymized IDs would prevent identity resolution. Real IDs would create privacy risk. `OperatorIdentity` provides the mapping. | ACCEPTED | — |
| 2026-09-06 | Pilot package is documentation/specification first, runtime second | (a) Implement runtime first; (b) Simultaneous docs + runtime | The canon must be established before implementation. Implementing without canon produces unreviewable code. The package documents what exists, what is missing, and what is needed — then the build plan implements the minimal delta. | ACCEPTED | — |
| 2026-09-06 | The pilot package does not modify runtime | (a) Modify runtime during canonization; (b) Modify runtime after review | Per the original task: "Do not make runtime changes until this package has been completed and reviewed." Canonization is documentation. Runtime changes are a separate phase (T1/T2/T3). | ACCEPTED | — |
| 2026-09-06 | Three maturity targets are separated | (a) Single target; (b) Two targets (before/after first customer) | T1 (ACME reference completion), T2 (first real customer), T3 (scalable production) have different requirements. Conflating them produces either over-engineering (T3 features for T1) or under-engineering (T1 features for T3). | ACCEPTED | — |
| 2026-09-06 | EXTEND is a closure decision that creates an extension phase, not a terminal state | (a) EXTEND is terminal (new pilot chartered); (b) EXTEND is non-terminal (pilot continues indefinitely) | EXTEND preserves the charter and success criteria (which were locked before measurement) while extending the window to collect missing evidence. It is a decision (the pilot evaluated and chose to extend) but not a termination (the pilot continues). If criteria are wrong, the correct outcome is STOP + new charter. | ACCEPTED | — |
| 2026-09-06 | Operations directory translates canon into executable procedures | (a) Operations as canonical specification; (b) No operations docs | The canon defines WHAT a pilot is. Operations defines HOW to execute one. Mixing them produces documents that are neither canonical nor operational. Separating them keeps canon stable while operations can evolve with experience. | ACCEPTED | — |
| 2026-09-06 | Context directory is explicitly non-canonical | (a) Context as canonical; (b) No context docs | Design history, proof points, open questions, and decision rationale are valuable but not normative. Making them canonical would freeze reasoning that should be able to evolve. The non-canonical warning in `context/README.md` prevents context from overriding canon. | ACCEPTED | — |

## How to use this document

1. **Before making a consequential decision**, check if it is
   already recorded here. Do not re-decide settled questions.
2. **When making a consequential decision**, add it with the date,
   alternatives, reason, and status.
3. **When a decision is superseded**, do NOT delete it. Mark the
   old decision as SUPERSEDED and add the new decision with
   `Supersedes` pointing to the old one.
4. **Do not add ordinary implementation changes.** A decision to
   rename a variable or refactor a function is NOT an architectural
   decision. Only decisions that shape the pilot design belong here.

## What qualifies as a consequential decision

A decision is consequential if it:
- Affects the pilot lifecycle, governance, or closure semantics
- Affects cross-pilot comparability (metrics, interventions, schemas)
- Affects privacy, consent, or governance enforcement
- Affects the relationship between canon, operations, and runtime
- Affects what is in scope vs out of scope for Pilot Mode
- Cannot be reversed without significant cost

A decision is NOT consequential if it:
- Is an implementation detail (variable names, file organization)
- Can be reversed with a small code change
- Affects only one pilot, not the pilot framework
- Is a bug fix

## What this document does NOT do

- Does not define specifications (see `pilot/UPSILON_PILOT_SPEC.md`)
- Does not define governance (see `pilot/governance/`)
- Does not define the build plan (see
  `pilot/implementation/PILOT_MODE_BUILD_PLAN.md`)
- Does not track open questions (see `OPEN_QUESTIONS.md`)
- Does not catalog proof points (see `PILOT_PROOF_POINTS.md`)
