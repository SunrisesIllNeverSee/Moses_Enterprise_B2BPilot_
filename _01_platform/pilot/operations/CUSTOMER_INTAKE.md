# CUSTOMER_INTAKE.md

> Procedure for qualifying a potential customer for an Upsilon
> Enterprise Pilot.
>
> This is a concierge/high-touch process. Self-service signup is NOT
> required for pilot legitimacy (see `pilot/context/DECISION_LOG.md`).

## Purpose

Customer intake determines whether a potential customer is a good
candidate for an Upsilon Enterprise Pilot and, if so, which commercial
pilot template best fits their question.

## Intake procedure

### Step 1 — Discovery call

**Goal:** Understand the customer's question and context.

Ask:
1. What AI tools are your operators using? (ChatGPT, Claude, Codex,
   GitHub Copilot, Cursor, other)
2. How many operators are using AI? (Need 25–100 for a valid pilot)
3. What is your question? What decision are you trying to make?
4. Who is the decision-maker? (Head of AI, CIO, L&D, Transformation,
   Procurement)
5. What is your timeline? (Need 30 days baseline + 14 days follow-up
   for intervention pilots)
6. Have you tried to measure AI usage before? What did you find?
7. What would make this pilot a success for you?

**Output:** Discovery notes. Match the customer's question to a
commercial pilot template:

| Customer question | Matching template | Template ID |
|---|---|---|
| "What does our AI workforce actually look like?" | AI Workforce Operating Baseline | 1 |
| "Do we have organizational capability or a few power users?" | AI Capability Distribution | 2 |
| "Are people adapting, or simply using the tools?" | AI Adoption & Adaptation | 3 |
| "Did our training actually change how people operate AI?" | AI Training Evaluation | 4 |
| "What changes when we introduce Model A, Model B or Tool X?" | Model / Tool Evaluation | 5 |
| "Is agent capability becoming organizational?" | Agent Adoption | 6 |
| "Is the constraint the operator, the tool or the workflow?" | Workflow Diagnostic | 7 |
| "Why do teams using the same AI stack operate differently?" | Team AI Operating Comparison | 8 |
| "What changed when we introduced X?" | Experiments | 9 |
| "How is our AI operating population changing month over month?" | Monitor | 10 |
| "Does this metric predict something we already care about?" | Meta-Pilot (Validation) | 11 |
| "Are our outsourced AI vendors actually delivering quality?" | Vendor / Consultancy Verification | 12 |

> See `src/config/pilot_registry.py` for the full 12-template
> registry with questions, best buyers, when-to-pitch, eval families,
> and deployment levels.

### Step 2 — Feasibility assessment

**Goal:** Determine whether the customer can actually run a pilot.

Check:
1. **Population size:** 25–100 operators using AI? (Below 25 is too
   small for statistical validity. Above 100 should be subsetted.)
2. **Provider access:** Can the customer provide telemetry? Either:
   - Provider file exports (Claude, Codex, GitHub), OR
   - Provider API access (Claude, Codex, Groq — requires API keys)
3. **Operator consent:** Can the customer disclose to employees that
   AI usage is being measured (developmental, not personnel
   evaluation)?
4. **Duration commitment:** Can the customer commit to a bounded
   pilot (30 days baseline + 14 days follow-up)?
5. **Decision authority:** Is there a decision-maker who will
   receive the readout and make a closure decision?

**Output:** Feasibility assessment (GO / NO-GO).

### Step 3 — Scope definition

**Goal:** Define the pilot scope.

Define:
1. **Population:** Which operators, which teams, selection criteria
2. **Duration:** Window start, window end, follow-up window (if
   intervention pilot)
3. **Eval families:** Which of the 15 eval families are active
   (determined by the commercial pilot template or à la carte
   selection)
4. **Success criteria:** What evidence will support each closure
   outcome (STOP/EXTEND/EXPAND/DEPLOY)
5. **Governance:** Privacy class, consent model, purpose ID,
   authorized_by

**Output:** Draft Pilot Charter (see
`pilot/governance/PILOT_CHARTER.md`).

### Step 4 — Governance setup

**Goal:** Establish governance clearance before any data collection.

1. Record the processing purpose (`purpose_id`)
2. Confirm employee disclosure will be made by the customer
3. Confirm consent model (opt_in / opt_out / mandated)
4. Confirm `decision_use_default` is DEVELOPMENTAL
5. Confirm `privacy_class` is pseudonymous_real
6. Confirm `synthetic` is false
7. Record `authorized_by` (the Decision Authority)

**Output:** Governance metadata ready for Gate 1.

## Disqualification criteria

A customer is NOT a good candidate for an Upsilon Enterprise Pilot if:

1. **Too few operators:** Fewer than 25 AI operators
2. **No provider access:** Cannot provide telemetry from any
   supported provider
3. **No decision authority:** No one is willing to make a closure
   decision
4. **Personnel evaluation intent:** Customer wants to evaluate
   individual employees (Upsilon is DEVELOPMENTAL only)
5. **No bounded duration:** Customer wants ongoing monitoring with
   no closure (Upsilon pilots terminate in a decision)
6. **No consent path:** Customer cannot disclose to employees or
   obtain consent

## What this intake does NOT do

- Does not create a Pilot Charter (that happens in DEFINE — see
  `PILOT_RUNBOOK.md`)
- Does not validate the configuration (that happens in
  `PILOT_LAUNCH_CHECKLIST.md`)
- Does not evaluate Gate 1 (that happens in
  `GATE_REVIEW_RUNBOOK.md`)
- Does not handle billing or contracts (out of scope — see
  `pilot/context/DECISION_LOG.md`)
