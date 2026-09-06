# context/ — Design History and Reasoning

> **WARNING: NON-CANONICAL.**
>
> Material in this directory records design history and reasoning. It
> may explain why canonical decisions were made, but it does NOT
> override the Upsilon Pilot Specification, governance documents,
> stage specifications, schemas, or accepted decision records.
>
> If a conflict is found between this directory and any canonical
> document (`pilot/UPSILON_PILOT_SPEC.md`, `pilot/governance/`,
> `pilot/stages/`, `pilot/schemas/`), the canonical document
> prevails. This directory is explanatory, not normative.

## Purpose

The `context/` directory preserves design reasoning, proof points,
unresolved questions, and architectural history that contributed to
the pilot design. It exists to:

1. **Prevent knowledge loss.** When the original designers are no
   longer available, the reasoning behind canonical decisions should
   be recoverable.
2. **Prevent unnecessary rebuilds.** Already-built capabilities
   should not be forgotten and rebuilt. `PILOT_PROOF_POINTS.md`
   catalogs demonstrated capabilities.
3. **Surface unresolved questions.** `OPEN_QUESTIONS.md` tracks
   design questions that have not been resolved.
4. **Record consequential decisions.** `DECISION_LOG.md` captures
   architectural decisions that shaped the pilot design.

## What belongs here

- Design rationale for canonical decisions
- Proof points demonstrating existing capabilities
- Open questions and unresolved design issues
- Architectural decision records (consequential decisions only)

## What does NOT belong here

- Canonical definitions (those go in `pilot/UPSILON_PILOT_SPEC.md`)
- Governance specifications (those go in `pilot/governance/`)
- Stage specifications (those go in `pilot/stages/`)
- Schemas (those go in `pilot/schemas/`)
- Operational procedures (those go in `pilot/operations/`)
- Implementation plans (those go in `pilot/implementation/`)
- Ordinary implementation changes (those go in git history)

## Files

| File | Purpose |
|---|---|
| `ORIGIN_AND_RATIONALE.md` | Why major pilot capabilities exist (reconstructed from repository evidence) |
| `PILOT_PROOF_POINTS.md` | Strongest demonstrated capabilities of the current platform |
| `OPEN_QUESTIONS.md` | Unresolved design questions |
| `DECISION_LOG.md` | Consequential pilot-architecture decisions |

## Relationship to canonical documents

```text
Canonical (normative)              Context (explanatory)
─────────────────────              ─────────────────────
pilot/UPSILON_PILOT_SPEC.md        context/ORIGIN_AND_RATIONALE.md
pilot/PILOT_LIFECYCLE.md           context/DECISION_LOG.md
pilot/governance/                  context/OPEN_QUESTIONS.md
pilot/stages/                      context/PILOT_PROOF_POINTS.md
pilot/schemas/
pilot/operations/
pilot/implementation/
```

> Canonical documents define WHAT the pilot is. Context documents
> explain WHY it is that way. If you need to know the rules, read
> canonical. If you need to know the reasoning, read context.
