# CLOSURE_OUTCOMES.md

> Every pilot terminates in a decision. There are exactly four closure
> outcomes. No pilot continues indefinitely.

## The four closure outcomes

### STOP

**Meaning:** The pilot did not meet its success criteria. The evidence
does not support continuing, expanding, or deploying. Discontinue the
pilot.

**When to choose STOP:**
- Majority of success criteria were MISSED
- A critical criterion was MISSED
- The pilot question cannot be answered with the available evidence
- The intervention produced no measurable change or negative change
- Governance violations occurred that invalidate the experiment

**Required documentation:**
- Findings summary (what was measured, what was found)
- Lessons learned (what the pilot revealed, even in failure)
- Success criteria comparison (which were MET, MISSED, PARTIAL)
- Root cause analysis (why criteria were missed)
- Recommendation (whether to charter a new pilot with different scope)

**Next steps:** Archive the pilot. Document lessons learned for
institutional memory. Consider chartering a new pilot with revised scope
or success criteria.

---

### EXTEND

**Meaning:** The pilot shows promise but is missing evidence. The
evidence is insufficient for a DEPLOY or EXPAND decision but sufficient
to justify continued evaluation.

**When to choose EXTEND:**
- Majority of success criteria were PARTIAL (close but not sufficient)
- Specific evidence is missing (e.g., follow-up window too short)
- The pilot question is partially answered but needs more data
- Interventions show promising trends but need more time

**Required documentation (ALL five — no exceptions):**
1. **Explicit reason**: Why the evidence is insufficient. Which criteria
   were PARTIAL or MISSED and why.
2. **Missing evidence**: What specific evidence is needed to reach a
   DEPLOY/EXPAND/STOP decision.
3. **New evidence requirement**: How the missing evidence will be
   collected (which eval families, which window, which operators).
4. **Extension period**: How long the extension will last, in days.
5. **New closure date**: The specific date for Gate 3 re-evaluation.

> **No indefinite extension.** An EXTEND without all five requirements
> is invalid. If the requirements cannot be specified, the correct
> outcome is STOP, not EXTEND.

**Next steps:** Continue the pilot with the extension parameters. Return
to the appropriate stage (usually INSTRUMENT or BASELINE) with the new
window. Re-evaluate Gate 3 at the new closure date.

---

### EXPAND

**Meaning:** The pilot met its success criteria. The evidence supports
expanding to a larger population, longer duration, or additional eval
families. The pilot question is answered positively but the scope should
be broadened before a DEPLOY decision.

**When to choose EXPAND:**
- All or majority of success criteria were MET
- The pilot question is answered positively for the bounded population
- The organization wants to test the findings at larger scale
- Additional eval families should be activated

**Required documentation:**
- Success criteria comparison (all MET criteria documented)
- Expansion scope (new population, new duration, new eval families)
- Expansion rationale (why expansion is the right next step vs DEPLOY)
- New success criteria for the expanded pilot (locked before measurement)

**Next steps:** Charter a new pilot (new Pilot Charter) with the expanded
scope. The expanded pilot is a new pilot with its own ID, charter, and
success criteria — not a continuation of the current pilot.

---

### DEPLOY

**Meaning:** The pilot met its success criteria and the organization is
ready for production deployment. The pilot question is answered positively
and the findings should transition to ongoing production use.

**When to choose DEPLOY:**
- All critical success criteria were MET
- The pilot question is answered positively
- The organization has the infrastructure for production deployment
- The governance framework supports ongoing production use

**Required documentation:**
- Success criteria comparison (all MET criteria documented)
- Production transition plan (what changes from pilot to production)
- Deployment checklist (infrastructure, governance, monitoring)
- Ongoing monitoring plan (how production use will be monitored)
- Rollback plan (what happens if production deployment encounters issues)

**Next steps:** Execute the production transition plan. The pilot
transitions from a bounded evaluation to ongoing production use. A new
"production pilot" or "monitoring pilot" (Commercial Pilot #10) may be
chartered for ongoing monitoring.

---

## Decision authority

The closure decision is made by the **decision authority** — the role
identified in the Pilot Charter as `authorized_by` or a designated
successor. The decision authority:

1. Reviews the pilot readout
2. Reviews the evidence-vs-success-criteria comparison
3. Reviews the Gate 3 evaluation
4. Selects a closure outcome
5. Signs the Decision Record

The decision authority is accountable for the closure decision. The
platform provides evidence; the decision authority makes the decision.

## No indefinite pilot state

> A pilot that has not reached a closure decision by its closure date
> is in violation of the pilot protocol. The decision authority must
> evaluate Gate 3 and select an outcome. If the decision authority
> cannot decide, the default outcome is **STOP** (with documentation of
> why a decision could not be reached).

This rule exists to prevent "zombie pilots" — pilots that continue
indefinitely without ever reaching a decision. Every pilot must terminate.
