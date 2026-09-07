# Upsilon Original to Current Deep Dive Review

## How to Use This Review

This review should serve as the lead decision memo for the new `/pilot/` canonization package. It is not a replacement product specification, a new metric authority, or permission to change runtime behavior. Its purpose is to identify what the original SignalAF commercial dossier intended, what the current Upsilon `_01_platform` actually implements, where the two have drifted, and which gaps are real enough to enter the build plan.

The review should feed five downstream documents directly:

| Canonization artifact | What this review should contribute |
|---|---|
| `context/ORIGINAL_DOSSIER_TRACEABILITY.md` | A requirement-by-requirement map from the August 17 dossier to current code, tests, demo behavior, reports, and operating surfaces. |
| `context/DRIFT_AND_CONTRADICTIONS.md` | The mixed-role-to-technical demo shift, the 12,842-versus-1,668 reporting contradiction, gate terminology collisions, fixture-label ambiguity, and other unresolved conflicts. |
| `context/PILOT_PROOF_POINTS.md` | Capabilities that are genuinely executable or demonstrated, including the end-to-end pipeline, measurement engine, intervention verification, evidence grading, and offline report generation. |
| `implementation/GAP_REGISTER.md` | Only capabilities that are missing, partial, manual, simulated, under-evidenced, or insufficiently production-hardened. |
| `implementation/PILOT_MODE_BUILD_PLAN.md` | The smallest implementation delta needed to make a running enterprise pilot a first-class governed runtime object. |

Use the following order of operations:

```text
ORIGINAL DOSSIER
      ↓
THIS DEEP-DIVE REVIEW
      ↓
inventory and traceability
      ↓
drift and contradiction review
      ↓
canonize Pilot v1
      ↓
ACME-001 governed dry run
      ↓
freeze proven gaps
      ↓
implement the minimal Pilot Mode delta
      ↓
first real customer pilot
```

The key discipline is to avoid turning every incomplete commercial or operational artifact into a new software subsystem. First prove what already exists. Then run the existing platform through `ACME-001`. Anything the reference pilot cannot legitimately complete becomes a candidate gap. Only after that gap freeze should implementation begin.

## Executive Verdict

**The original idea did not get lost. A large percentage of it became real software.**

In several areas, the current platform is well beyond what the original commercial dossier requested. Development outran the pilot and commercial architecture surrounding the engine; it did not fail to produce the engine.

Three conditions create the impression that Upsilon is not yet a complete pilot:

1. The pilot engine exists, but an active customer pilot is not yet a first-class runtime object.
2. The flagship synthetic demonstration drifted away from the original mixed-role commercial beachhead.
3. The presentation and report layer has partially drifted away from executable evidence.

The correct next move is not another analytical subsystem. The correct move is to canonize what exists, repair the evidence and lifecycle seams, and run the current platform through `ACME-001` as a governed pilot.

## 1. Where the Product Started

The August 17 SignalAF commercial field dossier was not merely a proposal to measure AI usage. It already described a closed-loop commercial system:

```text
BASELINE
    ↓
DIAGNOSE
    ↓
INTERVENE
    ↓
REMEASURE
    ↓
IMPROVE
```

Its commercial promise was effectively:

> Measure the baseline. Find where people and workflows accelerate or stall. Improve the bottom of the distribution. Re-measure.

That system maps closely to the enterprise pilot lifecycle now being formalized:

```text
DEFINE
→ INSTRUMENT
→ BASELINE
→ DIAGNOSE
→ INTERVENE
→ VERIFY
→ READOUT
→ DECIDE
```

The `/pilot/` architecture is therefore not a new product being invented around Upsilon. It recovers and formalizes the product already implicit in the original design.

## 2. What the Original Dossier Specified

### Commercial category

The proposed category was **AI Operator Evals**, not generic AI analytics, employee monitoring, productivity tracking, or model benchmarking. The thing being evaluated was the human-system operating relationship.

### Pilot boundary

The intended pilot was already bounded around:

- 25 to 100 active AI users;
- approximately 30 days;
- real AI usage;
- team and cohort evaluation;
- baseline measurement;
- targeted intervention;
- remeasurement;
- a buyer-facing outcome and continuation decision.

### Original beachhead

The original commercial beachhead was deliberately a nontechnical or mixed-role workforce. The flagship synthetic enterprise was intended to represent functions such as:

- Sales;
- Marketing;
- Operations;
- Finance and business roles;
- Support;
- People and administration.

The dossier explicitly argued against allowing the flagship 50-person demonstration to become 50 developers. That is one of the clearest points of later drift.

## 3. Original Doctrine That Survived

### Development, not punishment

The dossier's operating doctrine was to **raise the floor rather than rank people for punishment**. It favored managerial objects such as:

- stalled cohorts;
- fastest improvers;
- workflow bottlenecks;
- training candidates;
- tool-fit opportunities;
- development groups;
- peer-support matches;
- remeasurement queues.

The current platform materially implements this doctrine through governance enforcement, decision-use classification, manager-facing objects, and production-gate concepts. It distinguishes developmental, research, and workflow uses from personnel uses and carries warnings around inappropriate decision use.

**Assessment: 5/5 concept fidelity; 4/5 production hardening.**

The remaining work is mostly enterprise control infrastructure:

- persistent governance and audit events;
- customer attestation;
- role-based access control;
- role-specific visibility;
- durable decision-use records.

This is hardening work, not conceptual redesign.

## 4. Original Roadmap Compared With Current State

The original technical roadmap was approximately:

### P0 Sellable pilot

- adapters and import;
- canonical snapshots;
- 50-person simulator;
- cohort calculations;
- role and team comparisons;
- trajectory analysis;
- raise-the-floor report;
- executive reporting;
- CLI and TUI.

### P1 Intervention product

- workflow-stage mapping;
- deterministic recommendation rules;
- intervention ledger;
- pre/post remeasurement;
- similarity analysis;
- learning curves.

### P2 Enterprise productization

- continuous ingest;
- web interface;
- SSO and RBAC;
- configurable policies;
- MO§ES appliance deployment;
- private benchmark network.

### Current conclusion

| Original phase | Current assessment |
|---|---|
| P0 | Essentially built. |
| P1 | Mostly built and, in several areas, exceeded. |
| P2 | Partially represented in architecture, but not productionized. |

This is a substantially different conclusion from calling the platform a CLI that only pretends to be a pilot.

## 5. Executable Evidence

The review run recorded:

```text
674 passed
2 skipped
```

The current archive contains a substantial executable system rather than a set of screens pointing at static fixtures. The implementation includes domain models, repositories, configuration, ingestion adapters, measurement and analysis engines, workflow analysis, intervention management, outcomes, governance, reporting, CLI, TUI, and MCP surfaces.

The test result is important evidence of implementation breadth, but it should not be mistaken for evidence that every customer-facing pilot claim is production-ready. Test maturity, demo maturity, customer-evidence maturity, and enterprise-operational maturity must remain separate assessments.

## 6. Measurement Engine

The current metric registry contains canonical implementations for:

- Leverage;
- Yield;
- Token SNR;
- Log Leverage or 10xDEV;
- Construction.

The platform has correctly avoided falsely canonizing unresolved measures:

- Velocity;
- Compression Operating Ratio;
- Stability.

**Assessment: 5/5.**

The unresolved status of these three measures is healthier than false precision. The `/pilot/` package must not silently redefine them or treat their absence as a reason to create substitute formulas.

## 7. Cohort and Operator Intelligence

The current system materially exceeds the original P0 requirements. It includes:

- cohort analysis;
- operator profiles;
- percentile positioning;
- usage-versus-operation divergence;
- longitudinal movement;
- learning curves;
- team composition;
- operator similarity;
- organizational topology;
- capability dependency risk;
- context architecture;
- operator, system, and operator-by-system decomposition.

One of the strongest recovered ideas in the original dossier was to separate operator effect, system or model effect, and operator-by-system interaction. That concept is now implemented through operator-system analysis. Other ideas that began as strategic strengthening—topology, similarity, team composition, and learning curves—also became formal evaluation families.

**Assessment: 5/5.**

## 8. Eval System and Commercial Pilot Architecture

The platform contains 15 evaluation families:

1. Operator Baseline
2. Usage vs Operation Divergence
3. Context Architecture
4. Longitudinal Movement
5. Platform or Model Sensitivity
6. Cohort Composition
7. Intervention Response
8. Workflow Stage Fit
9. Team Composition
10. Capability Dependency Risk
11. Development Engine
12. Experiment as Product
13. Organizational AI Topology
14. Operator Similarity Search
15. AI Learning Curve

It also contains a second abstraction: 12 packaged commercial pilot types, including baseline, capability distribution, adoption and adaptation, training evaluation, model or tool evaluation, agent adoption, workflow diagnostic, team comparison, experiments, monitoring, meta-pilot validation, and vendor or consultancy verification.

The distinction is valuable, but the naming and runtime relationship need to be explicit.

## 9. The Central Architectural Cleanup

Three separate concepts currently sit too close to the word `pilot`:

```text
CommercialPilotTemplate
        ↓
PilotConfiguration
        ↓
PilotRun
```

### CommercialPilotTemplate

The kind of engagement being offered, such as an AI Training Evaluation Pilot.

### PilotConfiguration

The selected evaluation families, population, window, reference field, policies, workflow, outcome joins, gates, governance settings, and other customer-specific launch choices.

### PilotRun

The actual governed engagement, for example:

```text
ACME-001
September 1–30
Current stage: DIAGNOSE
Next decision gate: September 16
```

The platform already has the first two concepts. The third is the missing connective tissue and the single most important architectural finding in this review.

## 10. Preserve and Freeze PilotConfiguration

`PilotConfiguration` is much closer to complete than earlier discussions assumed. It already represents:

- evaluation-family selection;
- cohort size;
- 30-day window;
- deployment level;
- workflow;
- analytical routing gates;
- outcome joins;
- governance;
- reference population;
- commercial pilot selection.

Do not replace it with a giant new pilot object. At launch, freeze or version the configuration as the immutable measurement contract. Introduce `PilotRun` or `EnterprisePilot` as the runtime and control object that references that configuration.

## 11. Minimal PilotRun Shape

The missing object should be thin. It should coordinate existing systems rather than reproduce them.

```text
PilotRun
│
├── pilot_id
├── configuration_id
├── customer
├── decision_owner
├── start_date
├── target_end_date
├── current_stage
├── objectives
├── success_criteria
├── milestones
├── baseline_reference
├── findings
├── interventions
├── verification_results
├── pilot_gate_reviews
├── blockers
├── evidence_refs
├── current_status
└── final_decision
```

This is a control plane over the measurement engine, not another analytical database.

## 12. Why the Platform Does Not Yet Feel Like a Pilot

The current Pilot TUI screen reports measurement status such as cohort, window, operators, providers, observations, metric registry, reference population, interventions, and data quality.

A pilot control surface must also report engagement state:

```text
ACME-001

DAY 12 / 30

CURRENT STAGE
DIAGNOSE

OBJECTIVES
3 / 5 achieved

BASELINE
FROZEN

FINDINGS
5 material

INTERVENTIONS
3 proposed
0 authorized

NEXT GATE
Pilot Health — September 17

FINAL DECISION
PENDING
```

That relatively thin addition changes the meaning of the entire application. It gives the analytical platform a beginning, a controlled progression, decision points, and an explicit termination condition.

## 13. End-to-End Demonstration

The current demo executes the following pipeline:

```text
LOAD
EVALUATE
BENCHMARK
DIAGNOSE
OPERATOR × SYSTEM
INTERVENE
RE-EVALUATE
OUTCOME LINEAGE
REPORT
PDF
VISUALIZE
```

The reviewed run completed with:

- 50 operators;
- 12 interventions;
- 39 diagnoses during the complete run;
- 50 outcome lineages;
- 50 outcomes;
- 12 outcome correlations;
- 20 graphics.

Intervention verification produced differentiated outcomes:

- 5 `SUCCESS`;
- 2 `PARTIAL`;
- 2 `NO_EFFECT`;
- 3 `NEGATIVE`.

This is strong demonstration behavior precisely because it does not claim every intervention worked. It shows measurable outcome differentiation rather than a predetermined success story.

## 14. Evidence and Causality Discipline

The platform distinguishes:

- evidence grade;
- claim status;
- hypotheses;
- associations;
- outcome lineage;
- replication;
- data quality.

The outcome system does not automatically turn correlation into causation. The demo outcome analysis identifies observational evidence and association-level claims.

**Assessment: 5/5.**

This is a major maturation of the original idea and should become a central commercial proof point.

## 15. Original Acceptance Test

| Original acceptance question | Current status | Grade |
|---|---|---:|
| Who is improving fastest? | Learning curve and longitudinal analysis | **5/5** |
| Who has high usage but stalled operation? | Divergence engine | **5/5** |
| Who has low volume but strong development? | Composable from divergence and longitudinal analysis | **4/5** |
| Which workflow stage causes cross-role stall? | Workflow engine exists; present evidence is weak or provisional | **3/5** |
| Did a cohort change after an intervention? | Comparison, verification, and intervention systems | **5/5** |
| Does one tool or model fit a cohort better? | Operator-system analysis and model sensitivity | **4–5/5** |
| What is measured versus not measured? | Evidence grades, governance, data quality, and claim status | **5/5** |
| Can the core report run with external AI disabled? | Yes | **5/5** |

The original acceptance test was strong, and the present implementation satisfies most of it.

## 16. Workflow Analysis Is Built but Under-Demonstrated

The current demo workflow analysis produced approximately:

- 220 provisional observations;
- 130 insufficient observations;
- 0 fully supported fit claims.

This is not an analytical failure. The system is correctly refusing to turn underpowered evidence into a supported finding.

Commercially, however, this means Workflow Fit is implemented as an analytical capability but is not yet strongly demonstrated by the current fixture.

**Assessment: 3/5 demonstrated maturity.**

Improve the evidence through one or more of:

- greater sample density;
- longer observation duration;
- stronger stage-event coverage;
- a better predeclared experimental structure.

Do not weaken the evidence threshold merely to make the demo look better.

## 17. Drift Analysis

### Drift 1 The flagship demo changed markets

The original dossier selected nontechnical and mixed-role enterprise workers as the first commercial wedge. The current 50-operator fixture is dominated by:

- Product Engineering: 18;
- Platform and Infrastructure: 10;
- Data and Analytics: 8;
- Product and Design: 6;
- Customer Engineering and Support: 4;
- Operations and GTM: 4.

Its default workflow is `software_dev_v1`.

The technical build succeeded while the flagship commercial proof shifted toward software engineering.

Do not destroy this fixture. It has become a valuable technical stress test. Preserve two explicit reference proofs:

```text
examples/
├── ACME-TECH-001/
└── ACME-MIXED-ROLE-001/
```

The technical fixture should prove rich telemetry, model sensitivity, workflow instrumentation, interventions, artifacts, and operator-system decomposition. The commercial north-star fixture should return to Sales, Marketing, Operations, Finance, People or Administration, and Support.

### Drift 2 The report layer outran the evidence

The packaged static customer report at `demo_data/graphics/g09_sample_customer_report.md` claims 12,842 observations and approximately:

- 13 high-usage or low-operation operators;
- 11 low-usage or high-operation operators.

The current executable demo contains 1,668 canonical observation records and produces approximately:

- 3 high-usage or low-operation;
- 5 low-usage or high-operation;
- 30 mixed;
- 12 low-low.

There may once have been an upstream 12,842-interaction fixture, but that evidence is not present or traceable in the reviewed archive. As packaged, the rich static report and executable dataset are not synchronized.

This is the most urgent technical-integrity problem in the current platform.

### Drift 3 The PDF can bypass runtime truth

The full demo generates a runtime Markdown pilot readout from current evidence. The sample PDF path can then render the static sample report rather than the newly generated runtime report.

That permits two independent paths:

```text
runtime truth
      ↓
generated Markdown
```

and:

```text
stale static Markdown
      ↓
customer PDF
```

This must be removed. The engine can be correct while the strongest customer-facing proof is wrong.

**Priority: P0 and urgent.**

### Drift 4 Archetype labels mix ground truth with inference

The static report contains archetype analysis. Current code includes archetype-like fixture labels through `Operator.pattern_demo`, and team composition can use them. These are synthetic ground-truth labels, not a canonical classifier inferred from operator telemetry.

That is acceptable for a synthetic fixture, but the two categories must be visibly distinguished:

```text
FIXTURE GROUND TRUTH
```

versus:

```text
UPSILON INFERENCE
```

### Drift 5 Some original ontology did not survive

The reviewed current platform does not contain canonical equivalents for the complete original developmental vocabulary, including the Trans Ladder and labels such as Seeker, Refiner, Bearer, Igniter, Base, Power, Arch, and Transmitter.

Underlying ideas survived through longitudinal movement, learning curves, trajectory, similarity, and the development engine. The original ontology itself appears to have been abandoned or deferred.

Do not automatically restore it. First determine whether it improves measurement or merely adds product language. If it is not empirically necessary, preserve it in context or research material until validated.

### Drift 6 Gate now means two different things

The current platform already contains gates used for analytical or operator routing:

```text
metric threshold
      ↓
developmental action, review, or intervention
```

The enterprise pilot architecture also needs decision gates such as:

- Launch Readiness;
- Pilot Health;
- Closure and Scale.

These are different concepts and should not overload the same model. Distinguish `MeasurementGate` or `OperatorRoutingGate` from `PilotDecisionGate`.

### Drift 7 Pilot names three different layers

Commercial product templates, launch configuration, and active engagement state are all close to the word `pilot`. The canonization package should lock their names and relationships before new runtime classes or schemas are created.

## 18. Reporting Integrity Invariants

The following invariants should become non-negotiable requirements for Pilot v1:

1. **Every number in a pilot readout must originate from canonical pilot evidence or canonical pilot state.**
2. **All presentation formats must derive from one report model.**

   ```text
   Pilot evidence and state
           ↓
      Report model
       ├── Markdown
       ├── HTML
       └── PDF
   ```

3. **A handwritten or static sample report must never be an independent source for a customer-facing PDF.**
4. **Fixture ground truth must be labeled separately from Upsilon inference.**
5. **Observational association must never be presented as causal proof.**
6. **Unresolved metrics must remain unresolved unless the measurement authority explicitly canonizes them.**
7. **A baseline must be frozen and referenced before an intervention can claim pre/post change.**
8. **Every intervention must identify its hypothesis, target, authorization, evidence window, verification result, and evidence references.**
9. **The launch configuration must be immutable or versioned; material mid-pilot changes must be recorded, not silently applied.**
10. **Measurement gates and pilot decision gates must remain distinct types.**
11. **Synthetic demonstration results must not be represented as customer proof.**
12. **A pilot must terminate in an explicit decision: `STOP`, `EXTEND`, `EXPAND`, or `DEPLOY`.**

These invariants are more important than adding another evaluation family.

## 19. Success Criteria Already Exist

The original dossier already supplied a strong starting set of success criteria.

### Product criteria

- at least 90 percent usable cohort telemetry;
- stable normalization and provenance;
- meaningful operator differentiation;
- identifiable longitudinal movement;
- at least one actionable workflow or development finding;
- intervention candidates accepted;
- remeasurement demonstrated.

### Commercial criteria

- the buyer quickly understands the distinction from native analytics;
- the buyer identifies organizational questions that existing tools do not answer;
- the buyer wants repeated measurement or continuation.

Do not invent success criteria from scratch. Extract them into `pilot/governance/SUCCESS_CRITERIA.md` and decide which are:

- global pilot criteria;
- commercial-template criteria;
- customer-defined criteria.

## 20. Data Quality

The reviewed pilot status reported:

- 50 `OK`;
- 1,882 warnings;
- 0 blocking failures.

The warning count is primarily composed of:

- 1,668 missing `source_confidence` values;
- 214 impossible-value warnings associated with zero-token days.

The data-quality architecture is working, but the flagship fixture does not showcase it well.

The demo generator should populate structured source confidence and provenance. It should also distinguish legitimate zero-activity days from truly impossible measurements where appropriate. A flagship demonstration should show strict quality controls and explain intentional exceptions; it should not require an operator to dismiss a large unexplained warning count.

## 21. Real Instrumentation

The ingestion architecture is real and includes adapters or routes for sources such as:

- Claude exports;
- OpenAI and Codex;
- GitHub Copilot;
- Groq;
- CSV and JSON.

This is meaningful implementation, but source adapters and first-customer readiness are not the same thing. Live ingestion still needs deployment-specific validation, credential and secret handling, identity reconciliation, durable scheduling or collection, replay and deduplication behavior, customer-data boundary verification, source confidence, and operational recovery procedures.

**Assessment: implemented architecture; partial production readiness.**

This is one of the genuine first-customer gaps. It should be proven through a controlled instrumentation readiness test rather than addressed by building another generic ingestion framework.

## 22. What Is Implemented, Partial, Simulated, Manual, or Missing

| Capability | State | Review conclusion |
|---|---|---|
| Canonical core metrics | Implemented | Strong; unresolved metrics correctly remain uncanonized. |
| Cohort and operator analysis | Implemented | Strong and beyond the original P0 scope. |
| Fifteen evaluation families | Implemented | Broad analytical product architecture. |
| Twelve commercial pilot templates | Implemented | Useful offer layer; naming should be cleaned up. |
| `PilotConfiguration` | Implemented and partial | Rich launch configuration exists; freeze and version it rather than replace it. |
| `PilotRun` or `EnterprisePilot` | Missing | Most important connective object. |
| Baseline, diagnosis, intervention, verification | Implemented | Executed end to end in the synthetic demo. |
| Intervention outcome differentiation | Demonstrated | Success, partial, no-effect, and negative results are all represented. |
| Evidence grade and claim status | Implemented | Strong causality discipline. |
| Workflow fit | Implemented but under-demonstrated | Current fixture produces no fully supported fit claims. |
| Data-quality gates | Implemented | Architecture is strong; fixture provenance is noisy. |
| Live source adapters | Implemented and partial | Real architecture; customer deployment path needs hardening and validation. |
| Mixed-role commercial fixture | Missing | Original beachhead is no longer the flagship demo. |
| Technical synthetic fixture | Implemented | Preserve as a technical stress test. |
| Archetype ground truth | Simulated | Valid fixture metadata, but not an inferred classifier. |
| Customer-facing report model | Partial | Runtime Markdown exists, but static report and PDF paths can diverge. |
| Report evidence lineage | Defective | P0 integrity issue. |
| Pilot stages and milestones | Conceptual and partial | Capabilities exist, but active lifecycle state is not first-class. |
| Pilot decision gates | Missing or conflated | Must be separated from measurement routing gates. |
| Pilot success criteria | Defined in source doctrine, not fully operationalized | Recover and tier rather than reinvent. |
| Final stop, extend, expand, deploy decision | Missing as runtime closure | Must become mandatory. |
| Customer-facing progress status | Thin | Current status is measurement-centric, not engagement-centric. |
| Persistent governance audit trail | Partial | Doctrine and enforcement concepts exist; enterprise durability is incomplete. |
| RBAC, SSO, and role visibility | Partial or missing | P2 productionization work, not required to prove the first concierge pilot if controlled manually. |
| Pilot operating runbook | Missing | Needed to run the first customer consistently. |
| Self-service signup and onboarding | Not required for Pilot v1 | A legitimate enterprise pilot may be high-touch and vendor-operated. |

## 23. Maturity Map

The scores below distinguish code existence from demonstrated customer readiness.

| Area | Maturity | Why |
|---|---:|---|
| Measurement engine | **5/5** | Canonical metrics, registry discipline, and strong execution. |
| Cohort and operator intelligence | **5/5** | Broad, executable analysis that exceeds the original roadmap. |
| Evaluation-family architecture | **5/5** | Fifteen formal families plus commercial packaging. |
| Evidence and causality discipline | **5/5** | Grades, claim status, lineage, replication, and observational labeling. |
| End-to-end synthetic execution | **5/5** | Full pipeline completes with differentiated intervention outcomes. |
| Pilot configuration | **4/5** | Rich configuration exists; launch freeze, versioning, and runtime linkage remain. |
| Development-not-punishment governance | **5/5 concept; 4/5 hardening** | Doctrine survived; persistence, attestation, and access control remain. |
| Intervention product | **4/5** | Ledger and verification behavior exist; real-customer authorization and operations need proof. |
| Workflow-fit demonstration | **3/5** | Engine is appropriately conservative, but fixture evidence is underpowered. |
| Data-quality demonstration | **4/5 architecture; 3/5 fixture** | Strong controls are obscured by noisy synthetic provenance. |
| Live instrumentation readiness | **3/5** | Adapters exist; first-customer operations are not yet proven. |
| Customer report integrity | **2/5** | Strong output capability is undermined by divergent static and runtime sources. |
| Active pilot lifecycle | **2/5** | Lifecycle is implicit across capabilities but not represented as runtime state. |
| Customer pilot operating system | **2/5** | Charter, cadence, gates, closure, and runbook need formalization. |
| Enterprise production controls | **2–3/5** | Structural elements exist; SSO, RBAC, continuous operations, and durable governance remain P2 work. |

## 24. Pilot Proof Points

The following are defensible proof points for the canonization package:

1. Upsilon executes a complete baseline-to-verification analytical loop.
2. The engine analyzes both cohorts and individual operators.
3. It distinguishes usage from operating development rather than treating adoption as value.
4. It separates operator, system, and operator-by-system effects.
5. It supports intervention records and pre/post verification.
6. It produces success, partial, no-effect, and negative verification outcomes rather than forcing success.
7. It maintains evidence grades, claim status, lineage, and association-versus-causation discipline.
8. It can produce the core report without external AI dependency.
9. It includes a substantive automated test suite.
10. It already contains most of the original sellable-pilot and intervention-product roadmap.

The following are not yet defensible as customer proof without qualification:

- the stale 12,842-observation report;
- fully supported workflow-fit findings from the current fixture;
- inferred archetypes where the source is `pattern_demo` fixture metadata;
- production-ready live instrumentation across every listed adapter;
- a complete governed pilot lifecycle;
- a deployment or scale recommendation produced by a first-class closure gate.

## 25. What Is Actually Missing

### Missing now

- a first-class `PilotRun` or `EnterprisePilot` object;
- canonical pilot stages, transitions, and state rules;
- distinct pilot decision gates;
- charter, scope lock, baseline freeze, and closeout artifacts;
- active objectives, milestones, blockers, and next-gate status;
- explicit final decision state: stop, extend, expand, or deploy;
- one report model feeding Markdown, HTML, and PDF;
- a mixed-role commercial reference fixture;
- an ACME-001 governed reference run;
- an operational runbook for executing the first customer pilot.

### Partial or requiring hardening

- live instrumentation and onboarding validation;
- source-confidence and provenance completeness;
- workflow-fit evidence density;
- durable governance events and audit trail;
- customer attestation and decision-use controls;
- RBAC and role-specific visibility;
- persistent runtime state and stage-transition history;
- customer-facing pilot progress and health status.

### Not required before the first pilot

- self-service signup;
- a full web application;
- a new analytical subsystem;
- restoration of unvalidated legacy ontology;
- premature canonization of unresolved metrics;
- a private benchmark network;
- complete continuous-enterprise deployment infrastructure.

A first real pilot may be concierge-operated. The standard is not whether the customer clicks every button; it is whether the engagement is bounded, instrumented, governed, evidence-backed, and ends in a defensible decision.

## 26. Recommended Build Order

### Priority 0 Establish truth and prevent contradictory output

1. **Freeze the reviewed archives and current runtime behavior.** Do not silently change metrics or scoring while canonization is underway.
2. **Create `ORIGINAL_DOSSIER_TRACEABILITY.md`.** Map every material original requirement to code, test, demo, report, manual operation, or missing state.
3. **Create `DRIFT_AND_CONTRADICTIONS.md`.** Record the demo-market shift, observation-count contradiction, divergence-count contradiction, PDF source problem, gate collision, fixture/inference ambiguity, and deferred ontology.
4. **Lock reporting invariants.** Require one canonical report model and eliminate the static-report-to-customer-PDF bypass.
5. **Regenerate all sample outputs from executable canonical evidence.** Sample Markdown, HTML, PDF, and visual summaries must agree.

### Priority 1 Canonize the pilot before adding runtime code

6. **Define Pilot v1.** Lock the lifecycle, states, allowed transitions, required artifacts, evidence requirements, and closure decisions.
7. **Separate the three pilot layers.** Canonize `CommercialPilotTemplate`, `PilotConfiguration`, and `PilotRun`.
8. **Separate gate types.** Canonize measurement or operator-routing gates independently from pilot decision gates.
9. **Recover and tier success criteria.** Divide them into global, template-specific, and customer-specific criteria.
10. **Define integrity invariants.** Include baseline freeze, configuration versioning, intervention authorization, claim-status discipline, and report lineage.

### Priority 2 Force the existing platform through ACME-001

11. **Create the ACME-001 charter and launch configuration.** Use the existing synthetic system first; do not wait for new analytics.
12. **Execute every pilot stage.** Define, instrument, baseline, diagnose, intervene, verify, read out, and decide.
13. **Produce every required artifact.** If an artifact must be created manually, mark it manual; if the platform cannot support it, mark it missing.
14. **Run all pilot decision gates.** Record inputs, decision owner, outcome, rationale, and evidence references.
15. **Close ACME-001 with one explicit decision.** The synthetic reference run still must terminate in `STOP`, `EXTEND`, `EXPAND`, or `DEPLOY`.

### Priority 3 Freeze the genuine gap register

16. **Convert only failed or manual ACME-001 steps into implementation gaps.** Do not list speculative conveniences as blockers.
17. **Prioritize by integrity and first-customer necessity.** Reporting lineage and lifecycle control outrank new analysis or self-service polish.
18. **Assign acceptance evidence to every gap.** Each item must state how completion will be demonstrated.

### Priority 4 Implement the minimal Pilot Mode delta

19. **Add thin `PilotRun` persistence and stage history.** Reference the frozen `PilotConfiguration`; do not duplicate analytical state.
20. **Add lifecycle commands and status.** Expose stage, objectives, baseline state, findings, interventions, next gate, blockers, and final decision through the existing service layer and then CLI, TUI, or MCP surfaces.
21. **Add pilot decision-gate records.** Preserve owner, evidence, rationale, disposition, timestamp, and required follow-up.
22. **Bind reporting to canonical pilot state.** Render every format from the same report model.
23. **Add minimal operating safeguards.** Configuration versioning, baseline freeze, intervention authorization, and closure validation should be enforced.

### Priority 5 Strengthen the proofs needed for the first real customer

24. **Preserve the technical fixture as `ACME-TECH-001`.** Use it for analytical and telemetry stress testing.
25. **Create `ACME-MIXED-ROLE-001`.** Restore the original nontechnical commercial beachhead and provide adequate workflow-stage evidence.
26. **Clean synthetic provenance.** Populate source confidence and classify valid inactivity separately from impossible data.
27. **Run live instrumentation readiness tests.** Prove selected adapters end to end with identity, provenance, replay, deduplication, and recovery behavior.
28. **Write the operations package.** Include intake, launch, cadence, intervention, gate-review, closeout, and first-customer readiness runbooks.

### Priority 6 Production hardening after the pilot is proven

29. Add durable governance audit events and customer attestations.
30. Add role-based visibility, RBAC, and SSO where required by the target customer.
31. Add continuous ingestion and operational monitoring.
32. Build a web experience only when it materially improves delivery or becomes a customer requirement.
33. Pursue private benchmark networks and broader enterprise productization after the bounded pilot is repeatable.

## 27. Recommended Pilot v1 Lifecycle

| Stage | Purpose | Required outcome |
|---|---|---|
| Define | Lock customer, population, objectives, scope, criteria, and decision owner. | Approved charter and frozen launch configuration. |
| Instrument | Connect real usage and validate identity, coverage, provenance, and data quality. | `INSTRUMENTATION_READY` decision. |
| Baseline | Observe without intervention and establish the reference state. | Frozen baseline with adequate evidence. |
| Diagnose | Identify material cohort, operator, system, and workflow findings. | Evidence-backed diagnostic findings. |
| Intervene | Select and authorize a bounded set of interventions. | Intervention records with hypotheses and owners. |
| Verify | Re-measure and classify observed change. | Verification results with claim status and evidence grade. |
| Readout | Explain where the organization was, what was found, what changed, and what remains. | Canonical customer readout derived from pilot state. |
| Decide | Terminate the bounded evaluation. | `STOP`, `EXTEND`, `EXPAND`, or `DEPLOY`. |

## 28. Pilot Mode Acceptance Criteria

Pilot Mode should be considered minimally complete when:

- a `PilotRun` can be created from a frozen `PilotConfiguration`;
- the active stage and allowed transitions are explicit;
- required artifacts can be attached or referenced;
- baseline state can be frozen and audited;
- findings and interventions can be linked to evidence;
- intervention authorization and verification can be recorded;
- measurement gates and pilot decision gates cannot be confused;
- progress status reports days, objectives, blockers, next gate, and evidence health;
- Markdown, HTML, and PDF readouts derive from one canonical report model;
- the pilot cannot close without a supported final decision;
- ACME-001 can complete the lifecycle without inventing evidence;
- the existing measurement and scoring behavior remains unchanged unless an explicit conflict is documented and approved.

## 29. Final Recommendation

Upsilon already contains the core of a legitimate enterprise pilot: instrumentation architecture, baseline measurement, cohort and operator analysis, benchmarking, diagnosis, workflow analysis, interventions, pre/post verification, data-quality controls, evidence lineage, reporting, and multiple operating surfaces.

What it lacks is the formal wrapper that turns those capabilities into one bounded, governed experiment.

The immediate objective should therefore be:

> Canonize the pilot, restore evidence integrity, instantiate ACME-001, freeze the proven gaps, and build only the thin runtime layer required to operate and close a real engagement.

The platform is not waiting for a new analytical idea. It is waiting for its existing analytical system to be organized into a beginning, a controlled progression, an evidence-backed readout, and a decision endpoint.

## Review Basis

This memo packages the prior deep-dive comparison of:

- `signalaf_commercial_field_dossier_2026-08-17_v4.zip`; and
- `_01_platform.zip`.

Findings and counts are snapshot-specific to those reviewed archives and the recorded review run. The archives remain source evidence and should not be modified during canonization.
