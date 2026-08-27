### =================================================================
### MO§ES™ 30-DAY PILOT READOUT
### Synthetic Demonstration Report — Acme AI-Enabled Software Company
### =================================================================

**Report ID:** MOS-PILOT-2026-08-21-ACME50
**Cohort:** acme_50 (synthetic)
**Operators:** 50
**Teams:** 6
**AI Systems:** 3 primary (Claude, Codex, ChatGPT) + 3 secondary (Cursor, Copilot, Gemini)
**Baseline window:** 2026-07-01 to 2026-07-30 (30 days)
**Post-intervention window:** 2026-08-01 to 2026-08-14 (14 days)
**Observations:** 12,842 interaction-level records
**Metric registry version:** 0.2
**Reference field version:** public_field_2026-08-17
**Status:** SYNTHETIC PRODUCT FIXTURE — NOT CUSTOMER DATA

---

### 1. Executive Summary

This report presents the results of a 30-day MO§ES™ pilot evaluation of 50
AI-assisted operators across 6 teams at Acme AI-Enabled Software Company. The
evaluation measured operator-level AI interaction quality using the MO§ES
canonical metric set (Upsilon, Leverage, Yield, Token SNR, Construction),
benchmarked operators against a reference field, diagnosed operating patterns,
applied 12 interventions, and re-evaluated after a 14-day post-intervention
window.

**Three headline findings:**

1. **Usage does not equal Operation.** 13 operators (26%) show high AI usage but
   low operator evaluation scores (HIGH_USAGE_LOW_OPERATION divergence class).
   11 operators (22%) show the opposite: low usage but high operation. A
   conventional adoption dashboard would misidentify both groups. The
   highest-usage operator (signal-0008917623, 100th percentile usage) ranks
   in the bottom 5 for Yield. The lowest-usage operator in the top Yield
   quartile (signal-0005671234, 4th percentile usage) would be invisible on
   any adoption dashboard.

2. **Capability concentration risk.** 42% of high-Leverage capability
   (Leverage > 20.0) is concentrated in 6 operators across 4 teams. The
   departure of any single one of these 6 operators would reduce
   organizational AI-leverage capacity by approximately 7 percentage points.
   No team has built redundancy around these operators.

3. **Interventions show mixed results — honestly.** Of 12 interventions
   applied, 7 produced improvement (58.3%), 2 showed no change (16.7%), and
   3 degraded (25.0%). The persistent-context intervention (CTX-001) helped
   operators with low baseline Leverage but degraded one operator who already
   had strong context management. This is not a uniform win, and the report
   does not present it as one.

**What this report does NOT establish:**
- Employee productivity or work quality
- Intelligence or skill in general
- Causal benefit of high Yield or Leverage
- Permanent job or workflow placement recommendations
- That any operator should be hired, fired, promoted, or demoted

**Evidence grade summary:**
- Findings 1-2 (descriptive): Rung 6 — Strong observational telemetry
- Finding 3 (intervention): Rung 7 — Complete interaction + outcome (no control group)
- All numbers carry their evidence grade inline

---

### 2. Cohort Overview

| Metric | Value |
|--------|-------|
| Total operators | 50 |
| Active operators (baseline) | 50 (100%) |
| Teams | 6 |
| AI systems (primary) | 3 (Claude, Codex, ChatGPT) |
| AI systems (secondary) | 3 (Cursor, Copilot, Gemini) |
| Baseline observations | 12,842 |
| Baseline window | 2026-07-01 to 2026-07-30 |
| Post-intervention window | 2026-08-01 to 2026-08-14 |
| Interventions applied | 12 |
| Metric registry | v0.2 |
| Reference field | public_field_2026-08-17 |

**Team composition:**

| Team | Operators | Median Leverage | Median Yield | Primary platforms |
|------|-----------|-----------------|--------------|-------------------|
| Product Engineering | 18 | 12.19 | 6.01 | Claude (8), Codex (7), ChatGPT (3) |
| Platform / Infrastructure | 10 | 12.07 | 6.01 | Claude (4), Codex (3), ChatGPT (3) |
| Data / Analytics | 8 | 12.06 | 5.84 | ChatGPT (4), Codex (3), Claude (1) |
| Product / Design | 6 | 4.93 | 5.52 | Codex (4), ChatGPT (1), Claude (1) |
| Customer Engineering / Support | 4 | 23.51 | 9.16 | Claude (2), Codex (1), ChatGPT (1) |
| Operations / GTM | 4 | 12.16 | 6.67 | ChatGPT (3), Codex (1) |

**Cohort medians (all 50 operators):**

| Metric | Value | Formula |
|--------|-------|---------|
| Median Leverage | 12.177 | R/I |
| Median Yield | 6.007 | (R x O) / I^2 |
| Median Token SNR | 0.342 | O / (I+O) |
| Median Construction | 1.734 | W/R |
| Median 10xDEV (log10 Leverage) | 1.086 | log10(R/I) |

---

### 3. Key Findings

#### Finding 1: Usage-vs-Operation Divergence

**Evidence grade: Rung 6 — Strong observational telemetry**

Using fresh interaction volume (input + output tokens) as a usage measure and
Yield as an operation quality measure:

| Divergence class | Count | % | Description |
|-----------------|-------|---|-------------|
| HIGH_USAGE_LOW_OPERATION | 13 | 26% | High token volume, low Yield — "burning tokens without structure" |
| LOW_USAGE_HIGH_OPERATION | 11 | 22% | Low token volume, high Yield — "efficient, possibly underutilized" |
| MIXED | 24 | 48% | Moderate on both or divergent in complex ways |
| LOW_LOW | 2 | 4% | Low usage and low operation — disengaged or early-stage |

**Signature examples:**

| Operator (pseudonym) | Usage pctile | Yield pctile | Leverage | Divergence | Interpretation |
|---------------------|-------------|-------------|----------|------------|----------------|
| signal-0008917623 | 100.0 | 4.1 | 3.40 | HIGH_USAGE_LOW_OPERATION | Highest usage in cohort, bottom-5 Yield. Token volume does not translate to operator quality. |
| signal-0002410503 | 18.4 | 71.4 | 23.91 | LOW_USAGE_HIGH_OPERATION | Low usage, top-quartile Yield. Invisible on adoption dashboards. |
| signal-0005671234 | 4.1 | 83.7 | 18.16 | LOW_USAGE_HIGH_OPERATION | Near-lowest usage, top Yield. Extremely efficient. |
| signal-0003459812 | 32.7 | 91.8 | 29.31 | LOW_USAGE_HIGH_OPERATION | Moderate usage, highest Yield in cohort. |
| signal-0001234567 | 22.4 | 65.3 | 24.10 | MIXED | Good balance of usage and operation. |

**Why this matters:** A conventional AI adoption dashboard would rank
signal-0008917623 as the #1 AI user in the organization. MO§ES reveals that
this operator's Yield is in the bottom 5%. Simultaneously, the most efficient
operators (signal-0005671234, signal-0002410503) would be invisible on any
adoption dashboard because their usage volume is low. The divergence is not a
performance verdict — it is a diagnostic queue.

#### Finding 2: Capability Concentration

**Evidence grade: Rung 6 — Strong observational telemetry**

High-Leverage capability (Leverage > 20.0) is concentrated in 6 operators:

| Operator (pseudonym) | Team | Leverage | Yield | Archetype | % of org high-Lev |
|---------------------|------|----------|-------|-----------|-------------------|
| signal-0004567890 | Data/Analytics | 30.48 | 16.76 | recursive_builder | 16.7% |
| signal-0008901234 | Operations | 29.69 | 16.18 | recursive_builder | 16.3% |
| signal-0003459812 | Product Eng | 29.31 | 15.96 | recursive_builder | 16.1% |
| signal-0001234567 | Product Eng | 24.10 | 9.08 | context_compounder | 13.2% |
| signal-0002410503 | Product Eng | 23.91 | 9.18 | context_compounder | 13.1% |
| signal-0006789012 | Customer Eng | 23.51 | 9.16 | context_compounder | 12.9% |

**Total:** 6 operators hold 42% of the organization's high-Leverage capability.

**Concentration risk assessment:**
- No team has built redundancy around these operators
- 3 of the 6 are recursive_builders (same archetype) — a shared-mode dependency
- 2 of the 6 are on the same team (Product Engineering) — team-level concentration
- The Customer Engineering team (4 operators) has 1 operator holding 100% of the
  team's high-Leverage capability — single-point-of-failure

**What this does NOT mean:** This is a descriptive observation about the
distribution of AI-leverage capability in the current window. It is not an
employee evaluation. It does not mean these operators are "better" — it means
the organization's AI-leverage capacity is not evenly distributed, which has
implications for continuity planning and knowledge transfer.

#### Finding 3: Intervention Results

**Evidence grade: Rung 7 — Complete interaction + outcome (no control group)**

12 interventions were applied on day 21 (2026-08-01). Results after 14-day
post-intervention window:

| Classification | Count | % | Description |
|---------------|-------|---|-------------|
| improved_internal_and_external | 5 | 41.7% | Both MO§ES metrics and external outcomes improved |
| improved_internal_only | 2 | 16.7% | MO§ES metrics improved, external outcomes unchanged |
| no_change | 2 | 16.7% | No significant change in either |
| degraded | 3 | 25.0% | MO§ES metrics declined |

**Intervention type breakdown:**

| Intervention | Catalog ID | Target pattern | Applied to | Success | No effect | Degraded |
|-------------|-----------|----------------|------------|---------|-----------|----------|
| Persistent Context Setup | CTX-001 | P-CTX-01 (low leverage) | 5 ops | 2 | 0 | 3 |
| Decomposition / Framing | FRM-001 | P-BURN-01 (high burn) | 2 ops | 1 | 0 | 1 |
| Context Optimization Action | COA-001 | P-BURN-01 (high burn) | 4 ops | 2 | 1 | 0 |
| Model Routing Test | MOD-001 | P-MODEL-01 (model sens.) | 1 op | 0 | 1 | 0 |

**Key intervention findings:**

1. **CTX-001 (persistent context) has a dual effect.** It helped
   signal-0007890123 (Leverage +55%, from 10.20 to 15.82) and
   signal-0008901234 (Leverage +55%, from 3.51 to 5.44). But it degraded
   signal-0002345678 (Leverage -18%, from 5.11 to 4.19) and
   signal-0007890123 (Leverage -18%, from 3.49 to 2.86). The operators who
   degraded already had moderate context management — the intervention may
   have disrupted their existing workflow.

2. **COA-001 (context optimization) was the most consistently effective.** 2
   of 4 operators improved on both internal and external metrics.
   signal-0006789012 improved Yield by 55% and reduced cycle time by 15.4%.

3. **MOD-001 (model routing) showed no effect.** signal-0002345678 (already
   high-Leverage at 23.37) did not benefit from model routing. This suggests
   model routing interventions should target operators with model sensitivity
   patterns, not already-stable operators.

4. **Internal metric improvement does not equal external outcome improvement.**
   2 operators improved on MO§ES metrics but not on external outcomes. 1
   operator (signal-0008917623) improved on external cycle time (-13.3%) but
   showed only modest internal improvement. This confirms the importance of
   keeping internal metrics and external outcomes logically separate.

---

### 4. Operator × System Matrix (Excerpt)

**Evidence grade: Rung 6 — Strong observational telemetry**

Composite performance/fit score (0-100) for 10 representative operators across
3 primary AI systems. Score = 0.4 x Leverage percentile + 0.4 x Yield
percentile + 0.2 x stability score.

| Operator (pseudonym) | Team | Archetype | Claude | Codex | ChatGPT | Best fit |
|---------------------|------|-----------|--------|-------|---------|----------|
| signal-0002410503 | Product Eng | context_compounder | 82 | 78 | 45 | Claude |
| signal-0008917623 | Product Eng | high_volume_burner | 28 | 22 | 18 | Claude (least weak) |
| signal-0003459812 | Product Eng | recursive_builder | 65 | 90 | 55 | Codex |
| signal-0005671234 | Product Eng | efficient_minimalist | 88 | 85 | 72 | Claude |
| signal-0001234567 | Product Eng | context_compounder | 80 | 84 | 48 | Codex |
| signal-0007890123 | Platform/Infra | high_volume_burner | 25 | 20 | 15 | Claude (least weak) |
| signal-0002345678 | Data/Analytics | kinetic_generator | 42 | 38 | 35 | Claude |
| signal-0004567890 | Data/Analytics | recursive_builder | 60 | 95 | 58 | Codex |
| signal-0006789012 | Customer Eng | context_compounder | 78 | 76 | 50 | Claude |
| signal-0008901234 | Operations | context_compounder | 82 | 80 | 52 | Claude |

**Legend:** Strong (75-100) | Good (60-74) | Moderate (40-59) | Weak (25-39) | Poor (0-24)

**Key interaction effects:**

1. **Recursive builders excel on Codex.** signal-0003459812 and
   signal-0004567890 score 25-35 points higher on Codex than Claude. Codex's
   codebase-aware context handling appears to complement the recursive builder
   pattern. **Recommendation:** route recursive builders to Codex as primary.

2. **Context compounders are platform-flexible.** signal-0002410503,
   signal-0001234567, signal-0006789012, and signal-0008901234 all score well
   on both Claude and Codex (76-84 range) but poorly on ChatGPT (45-52). The
   context compounding pattern works on systems with strong context retention
   but not on ChatGPT's session-scoped context model.

3. **High-volume burners struggle everywhere.** signal-0008917623 and
   signal-0007890123 score below 30 on all three systems. The problem is the
   operator pattern (high input, weak reuse, low Yield), not the system.
   **Recommendation:** system routing will not fix this — the intervention
   should target the operator's context management behavior (COA-001 or
   FRM-001).

4. **ChatGPT is uniformly weaker for these archetypes.** No operator scores
   above 72 on ChatGPT. This may reflect ChatGPT's context model (session-scoped,
   less persistent) rather than model capability. **Recommendation:** if
   ChatGPT is the enterprise standard, investigate whether persistent context
   tools (custom GPTs, memory features) close the gap.

---

### 5. Capability Distribution

**Evidence grade: Rung 6 — Strong observational telemetry**

**Leverage distribution (50 operators, baseline window):**

```
Leverage (R/I)
  30 +                                              #  3
  27 +                                          #   #
  24 +                              #   #       #   #
  21 +                              #   #       #   #
  18 +                          #   #   #       #   #
  15 +                      #   #   #   #       #   #
  12 +  #   #   #   #   #   #   #   #   #   #   #   #
   9 +  #   #   #   #   #   #   #   #   #   #   #   #
   6 +  #   #   #   #   #   #   #   #   #   #   #   #
   3 +  #   #   #   #   #   #   #   #   #   #   #   #
     +--+---+---+---+---+---+---+---+---+---+---+---+-->
       3   6   9  12  15  18  21  24  27  30

  Bins: 3-6 (5 ops), 6-9 (1 op), 9-12 (2 ops), 12-15 (2 ops),
        15-18 (1 op), 18-21 (0 ops), 21-24 (0 ops), 24-27 (6 ops),
        27-30 (0 ops), 30+ (3 ops)

  Median: 12.18    Mean: 14.52    Std: 8.74
  P25: 9.85    P75: 23.51    P90: 29.49
```

**Archetype distribution:**

| Archetype | Count | Median Leverage | Median Yield | Description |
|-----------|-------|-----------------|--------------|-------------|
| context_compounder | 7 | 23.91 | 9.08 | High cache read, moderate input, stable |
| high_volume_burner | 6 | 3.47 | 0.69 | Very high tokens, weak reuse, low Yield |
| efficient_minimalist | 5 | 18.16 | 11.70 | Low volume, strong output, high efficiency |
| kinetic_generator | 6 | 4.94 | 5.55 | High output, moderate input, low persistence |
| recursive_builder | 7 | 29.52 | 15.65 | High cache write+read, improving leverage |
| volatile_switcher | 5 | 10.02 | 5.44 | High variance, model switching, inconsistent |
| balanced_operator | 6 | 12.19 | 6.01 | Moderate across all dimensions, stable |
| improving_operator | 4 | 12.35 | 5.59 | Metrics improving over baseline window |
| declining_operator | 3 | 12.07 | 6.55 | Metrics weakening over baseline window |

**Stability distribution:**
- High stability (coefficient of variation < 0.3): 18 operators (36%)
- Moderate stability (CV 0.3-0.6): 22 operators (44%)
- Low stability (CV > 0.6): 10 operators (20%)

---

### 6. Workflow Diagnostic

**Evidence grade: Rung 6 — Strong observational telemetry (stage events) +
Rung 4 (stage-fit scores are demo hypotheses)**

**Workflow:** Software Development (software_dev_v1) — 7 stages

| Stage | Events | Operators active | Median fit score | Bottleneck? |
|-------|--------|-----------------|------------------|-------------|
| discovery | 142 | 38 | 0.71 | No |
| requirements | 98 | 28 | 0.68 | Mild — low participation |
| architecture | 76 | 22 | 0.74 | No |
| implementation | 218 | 47 | 0.62 | YES — oversubscribed, lowest fit |
| testing | 134 | 35 | 0.69 | No |
| review | 52 | 14 | 0.81 | YES — underserved, highest fit |
| release | 38 | 12 | 0.76 | No |

**Workflow findings:**

1. **Implementation is the bottleneck stage.** 218 stage events (most of any
   stage) with the lowest median fit score (0.62). 47 of 50 operators
   participate in this stage. The stage is oversubscribed — too many operators
   spending time in implementation, many with poor fit.

2. **Review is underserved.** Only 14 operators participate in review, but
   those who do have the highest median fit score (0.81). This suggests the
   organization has review-capable operators but is not utilizing them
   sufficiently. **Recommendation:** identify operators with high review-fit
   scores and allocate more review work to them.

3. **Requirements has low participation.** Only 28 operators participate in
   requirements, with moderate fit (0.68). This may indicate that requirements
   work is concentrated in a small group, creating a handoff bottleneck between
   requirements and architecture.

4. **Stage-specialist operators exist.** Several operators show
   stage-specific excellence:
   - signal-0001234567: excellent in implementation (fit 0.86), weak in
     discovery (fit 0.42)
   - signal-0002410503: excellent in review (fit 0.84), moderate elsewhere
   - signal-0004567890: excellent in architecture (fit 0.82), weak in testing
     (fit 0.51)

---

### 7. Intervention Comparison

**Evidence grade: Rung 7 — Complete interaction + outcome (no control group)**

**Full intervention results (12 operators):**

| Operator (pseudonym) | Intervention | Baseline Lev | Post Lev | dLev% | Baseline Yield | Post Yield | dYield% | Cycle d% | Quality d% | Classification |
|---------------------|-------------|-------------|----------|-------|---------------|------------|---------|----------|-----------|----------------|
| signal-0008917623 | COA-001 | 12.16 | 12.01 | -1.3% | 6.67 | 8.01 | +20.0% | +4.7% | +1.7% | improved_internal_only |
| signal-0002410503 | COA-001 | 23.92 | 26.78 | +12.0% | 9.13 | 9.31 | +2.0% | +9.7% | +3.4% | no_change |
| signal-0005671234 | COA-001 | 12.06 | 12.38 | +2.7% | 6.09 | 9.44 | +55.0% | +6.2% | +1.3% | improved_int_and_ext |
| signal-0006789012 | COA-001 | 23.51 | 25.31 | +7.6% | 9.16 | 14.20 | +55.0% | -15.4% | +4.8% | improved_int_and_ext |
| signal-0002345678 | CTX-001 | 5.11 | 4.19 | -18.0% | 5.73 | 6.70 | +16.9% | +5.8% | +4.2% | degraded |
| signal-0003459812 | FRM-001 | 29.49 | 31.81 | +7.8% | 16.16 | 13.25 | -18.0% | +4.0% | -1.4% | degraded |
| signal-0007890123 | CTX-001 | 10.20 | 15.82 | +55.0% | 5.60 | 5.93 | +6.0% | +0.8% | +4.6% | improved_int_and_ext |
| signal-0008901234 | CTX-001 | 3.51 | 5.44 | +55.0% | 0.71 | 0.82 | +14.3% | +7.1% | +4.0% | improved_int_and_ext |
| signal-0002345678b | MOD-001 | 23.37 | 23.96 | +2.5% | 8.73 | 8.91 | +2.0% | -1.3% | +1.5% | no_change |
| signal-0007890123b | CTX-001 | 3.49 | 2.86 | -18.0% | 0.71 | 0.84 | +19.3% | -2.1% | +1.0% | degraded |
| signal-0005671234b | FRM-001 | 11.66 | 12.50 | +7.2% | 5.92 | 9.17 | +55.0% | -3.3% | -1.3% | improved_int_and_ext |
| signal-0008917623b | CTX-001 | 3.55 | 4.25 | +20.0% | 0.69 | 0.79 | +13.7% | -13.3% | +2.1% | improved_internal_only |

**Intervention effectiveness summary:**

| Intervention | n | Avg dLev | Avg dYield | Avg cycle d | Avg quality d | Success rate |
|-------------|---|----------|------------|-------------|---------------|-------------|
| CTX-001 (persistent context) | 5 | +18.8% | +11.2% | -1.3% | +2.7% | 40% (2/5) |
| COA-001 (context optimization) | 4 | +5.3% | +33.0% | +1.3% | +2.8% | 50% (2/4) |
| FRM-001 (decomposition/framing) | 2 | +7.5% | +18.5% | +0.4% | -1.4% | 50% (1/2) |
| MOD-001 (model routing) | 1 | +2.5% | +2.0% | -1.3% | +1.5% | 0% (0/1) |

**Key observation:** CTX-001 has the highest average Leverage improvement
(+18.8%) but also the highest variance — it produced both the largest gain
(+55%) and the largest loss (-18%). COA-001 is more consistent: moderate
average improvement with lower variance. This suggests CTX-001 should be
targeted carefully (only for operators with low baseline Leverage and no
existing context management), while COA-001 can be applied more broadly.

---

### 8. Evidence Grades Per Finding

| Finding | Evidence grade | Rung | Why |
|---------|---------------|------|-----|
| Usage-vs-operation divergence | Strong observational telemetry | 6 | Complete I/O/R/W per session for all 50 operators, 12,842 observations |
| Capability concentration | Strong observational telemetry | 6 | Same data source, descriptive distribution analysis |
| Team-level differences | Strong observational telemetry | 6 | Operator profiles grouped by team, complete coverage |
| Operator × System interaction effects | Strong observational telemetry | 6 | Cross-tabulation of operator metrics by primary platform |
| Workflow stage fit | Activity metadata + demo hypothesis | 4 | Stage events are observational; fit scores are demo hypotheses, not validated science |
| Intervention effectiveness | Complete interaction + outcome | 7 | Baseline + post-intervention with external outcomes, but no control group |
| Causal claims about interventions | NOT SUPPORTED | — | Would require Rung 8 (controlled experiment with randomization) |
| Individual operator rankings | NOT EXPOSED TO MANAGEMENT | — | Per governance spec, individual rankings are not shown to management |
| Longitudinal trends | Partial telemetry | 5 | Only 30-day baseline + 14-day post; longer window needed for trend confidence |

---

### 9. Recommendations

**Immediate actions (within 30 days):**

1. **Treat divergence as a diagnostic queue.** The 13 HIGH_USAGE_LOW_OPERATION
   operators are not "underperforming" — they are burning tokens without
   structure. Select 4-5 for a context optimization intervention (COA-001)
   which showed the most consistent improvement in the pilot.

2. **Route recursive builders to Codex.** The operator × system matrix shows
   25-35 point score improvements for recursive builders on Codex vs Claude.
   This is the single highest-impact system routing change available.

3. **Address the review bottleneck.** 14 operators participate in review with
   high fit scores (0.81), but the stage is underserved. Allocate more review
   work to operators with high review-fit scores. This may also relieve
   pressure on the oversubscribed implementation stage.

4. **Build redundancy around capability concentration.** The 6 operators
   holding 42% of high-Leverage capability represent continuity risk. Initiate
   knowledge transfer sessions between these operators and peers in the same
   archetype cluster.

**Near-term actions (30-60 days):**

5. **Run a controlled experiment for CTX-001.** The pilot showed CTX-001 has
   high variance (both +55% and -18% outcomes). A controlled experiment with
   matched control operators would establish causality and identify which
   operator profiles benefit vs degrade.

6. **Investigate ChatGPT context gap.** All archetypes score lower on ChatGPT.
   If ChatGPT is the enterprise standard, test whether persistent context
   tools (custom GPTs, memory features) close the gap for context compounders.

7. **Monitor declining operators.** 3 operators show declining trajectories
   over the baseline window. Flag for observation — if decline continues in the
   next window, investigate whether workflow changes, tool changes, or
   workload changes explain the pattern.

**What NOT to do:**

8. **Do not use operator metrics for performance management.** MO§ES measures
   AI interaction quality, not employee productivity. Using these metrics for
   hiring, firing, promotion, or performance review is explicitly prohibited
   by the governance spec and is not what the system is designed for.

9. **Do not present individual rankings to management.** Individual-level
   rankings are available to the operator and their designated coach only.
   Management sees aggregate distributions, team comparisons, and
   organizational patterns — not leaderboards.

10. **Do not treat stage-fit scores as validated science.** The workflow
    stage-fit scores are demo hypotheses derived from synthetic data. They
    suggest where to look, not what to conclude. Real validation requires
    outcome-linked stage observations over multiple cycles.

---

### 10. Next Measurement Suggestions

| Measurement | Why | When | Evidence grade target |
|-------------|-----|------|----------------------|
| Extended baseline (60-day) | Confirm divergence patterns persist beyond 30-day window | Next 60 days | Rung 6 |
| Controlled CTX-001 experiment | Establish causality for context intervention | Next 30 days | Rung 8 |
| Multi-platform observation | Capture operators using secondary platforms (Cursor, Copilot, Gemini) | Next 30 days | Rung 6 |
| Outcome-joined analysis | Join GitHub/Jira data for all 50 operators | Next 30 days | Rung 7 |
| Team-level intervention | Test workflow redesign on implementation bottleneck | Next 45 days | Rung 7 |
| Longitudinal re-evaluation | Re-measure all 50 operators after 60 days | Day 60 | Rung 6 |
| Cross-team collaboration mapping | Map session sharing and project overlap | Next 30 days | Rung 5 |

---

### 11. Data Quality Statement

| Dimension | Status | Notes |
|-----------|--------|-------|
| Observation completeness | 100% of active operators have baseline data | All 50 operators active in baseline window |
| Token pillar coverage | Complete (I/O/R/W) for all observations | All 4 canonical token pillars present |
| Platform coverage | 3 primary platforms fully instrumented | Secondary platforms (Cursor, Copilot, Gemini) not fully captured |
| Temporal coverage | 30/30 baseline days, 14/14 post-intervention days | No gaps in daily coverage |
| Reference field | Synthetic placeholder | Replace with real external reference field before production use |
| External outcomes | 12 of 50 operators (24%) | Only intervention cohort has external outcome data |
| Synthetic marker | All records marked synthetic=true | No risk of synthetic data being mistaken for real customer data |

---

### 12. Methodology Appendix

**Metric definitions (from metric_registry.json v0.2):**

| Metric | Formula | Status | Unit |
|--------|---------|--------|------|
| Leverage | R/I | CANONICAL | ratio |
| Yield | (R x O) / I^2 | CANONICAL | ratio |
| Token SNR | O / (I+O) | CANONICAL_WITH_INTERPRETATION_LIMIT | share |
| 10xDEV (log Leverage) | log10(R/I) | CANONICAL | log10_ratio |
| Construction | W/R | CANONICAL_WITH_INTERPRETATION_LIMIT | ratio |
| Velocity | — | NEEDS_CANONICAL_LOCK | — |
| Stability | — | NEEDS_CANONICAL_LOCK | score |

Where: I = input_tokens, O = output_tokens, R = cache_read_tokens, W = cache_write_tokens

**Upsilon formula:** (cache_read x output) / input^2 — same as Yield in the
current metric registry. The MOSES seed values (1_251_211, 11_296_121,
128_196_310, 2_555_179_769) produce Upsilon = 18436.98 as a reference constant.

**10xDEV formula:** log10(Leverage) = log10(R/I). This transforms the Leverage
ratio into a log scale where each integer increase represents a 10x improvement.

**Reference field:** public_field_2026-08-17 — synthetic distribution derived
from the acme_50 cohort. Percentile breakpoints for Leverage: P0=3.30, P10=3.55,
P25=9.85, P50=12.19, P75=23.51, P90=29.49, P100=30.48.

**Intervention catalog IDs:**
- CTX-001: Persistent Context Setup (project context file, memory tool, session handoff template)
- COA-001: Context Optimization Action (context restructuring for high-burn operators)
- FRM-001: Decomposition / Framing Guide (task decomposition template, staged planning)
- MOD-001: Model Routing Test (route research/build/review to different models)

**Pattern detector IDs:**
- P-BURN-01: High-volume burner pattern (high usage, low Yield)
- P-CTX-01: Low context reuse pattern (low Leverage, low cache hit)
- P-MODEL-01: Model sensitivity pattern (high variance across models)
- P-HIDDEN-01: Hidden capability pattern (low usage, high Yield)

**Report generated by:** MO§ES™ reporting engine v0.2
**Report type:** 30-day pilot readout (synthetic)
**Intended audience:** Enterprise pilot prospect (pre-sales demonstration)
**Distribution:** Sales-authorized, not for external distribution

---

### End of Sample Customer Report

> This report is a synthetic product fixture. All numbers are derived from the
> acme_50 synthetic cohort. No real customer data is used. The report
> structure, evidence grading, and recommendation format are representative of
> what a real pilot deliverable would contain.
