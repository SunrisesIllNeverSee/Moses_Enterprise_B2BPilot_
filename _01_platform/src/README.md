---
type: Reference
title: Source — README
description: README for the source tree: domain model, metric engine, repository, analysis, diagnostics, interventions, workflow, outcomes, service layer, CLI/TUI/MCP, reporting, website. Covers P0 through P2. Active.
tags: [b2bpilot, src, source, readme, domain, metrics, engine, p0, p1, p2]
timestamp: 2026-08-17
last_touched: 2026-08-18 09:34 UTC
---

# Source

## Package structure

```
src/
  domain/            — P0-A: canonical entity model (14 entities)
    observation.py     — I/O/R/W telemetry event
    operator.py        — pseudonymous operator identity
    cohort.py          — cohort definition + window
    measurement.py     — canonical metric measurement
    reference_population.py — public field for percentile comparison
    quality_result.py  — data quality result (OK/WARNING/BLOCKING)
    tenant.py          — enterprise tenant
    pattern.py         — detected operating pattern
    diagnosis.py       — diagnostic hypothesis (evidence + alternatives + HYPOTHESIS)
    intervention.py    — intervention object + 12-entry catalog
    outcome_join.py    — external outcome join result (ASSOCIATION)
    workflow.py        — 7-stage workflow definition
    report.py          — export report status

  metrics/           — P0-B: canonical metric engine
    formulas.py        — pure formula functions (L, Y, S, D, C) with domain guards
    engine.py          — ScoringEngine: observations → Measurement objects
    registry.py        — loads/validates schemas/metric_registry.json (v0.2)

  ingest/            — P0-C: provider telemetry adapters
    fixture.py         — reads observations.jsonl from demo_data
    claude.py          — parses Claude usage export JSON
    codex.py           — parses Codex/OpenAI usage CSV
    validate.py        — schema-conformance validation

  repository/        — data-access layer
    demo_repository.py — loads demo_data/ into domain objects

  analysis/          — P0-D + P1-D: analysis + verification
    divergence.py      — usage-vs-operation divergence
    percentiles.py     — field position against reference population
    distributions.py   — cohort metric distributions (median, p10, p90)
    eligibility.py     — operator eligibility checks
    data_quality.py    — missingness, schema warnings, provenance
    verifier.py        — P1-D: pre/post verification (target + non-target deltas)

  diagnostics/       — P1-A + P1-B: pattern detection + diagnosis
    pattern_engine.py  — detects P-CTX-01, P-CTX-02, P-BURN-01, P-HIDDEN-01
    diagnosis_engine.py — generates Diagnosis objects (evidence + alternatives + HYPOTHESIS)

  interventions/     — P1-C: intervention registry + management
    registry.py        — 12-entry catalog per `09` (CTX, FRM, MOD, AGT, REV, STD, COA, LRN, STG)
    manager.py         — recommend/assign/close; requires target_metric + followup_days

  workflow/          — P2-A: workflow fit analysis
    fit_engine.py      — 7-stage fit with observation count, uncertainty, sample-size gate

  outcomes/          — P2-B: external outcome joins
    governance.py      — governance metadata; causal_claim_permitted always False
    join_engine.py     — joins external CSV outcomes to internal deltas; ASSOCIATION only

  service.py         — PilotService: shared service layer for CLI/TUI/MCP
                       (all P0 + P1 + P2 methods)

  cli/               — P0-E: `enterprise` CLI per `07` spec
    main.py            — argparse-based CLI with --json mode

  tui/               — P0-E: TUI per `06` spec
    app.py             — 10-screen rich-based console

  mcp_server/        — P0-E: MCP server per `08` spec (named mcp_server to avoid shadowing the mcp SDK)
    server.py          — 13 tools (10 read + 3 write) + 5 resources, governance annotations
                         supports MCP SDK v2.0.0 (MCPServer) + fallback direct-call
                         (spec 08 lists 6 resources; `enterprise://cohort/{cohort_id}` not yet registered)

  reporting/         — P0-F: export formats per `13` spec
    exporters.py       — JSON, CSV, Markdown exporters

  enterprise_demo.py   — legacy CLI/TUI entry point (calls PilotService)
```

## Website

```
website/
  index.html         — homepage (hook + product story + live demo stats)
  product.html       — full product walkthrough with real demo data
  pilot.html         — 30-day pilot (9 phases, 10 deliverables, 3 interfaces)
  methodology.html   — measurement science + privacy + data surfaces + research stack
  style.css          — shared stylesheet
```

Static HTML/CSS, no framework, no build step. Deployable to any host.

## Architecture rules (per `21`)

- CLI/TUI/MCP all call `PilotService`; none implement business logic independently.
- `ScoringEngine` is the single canonical scoring path — no other module computes metrics.
- `metrics/formulas.py` contains the pure formula functions; `metrics/engine.py` wraps them.
- The metric registry (`schemas/metric_registry.json`) is authoritative.
- Ingest adapters normalize provider telemetry into `Observation` objects.
- Every response carries governance annotations (synthetic marker, registry version, window, reference version, privacy class, validation status).
- Diagnostics are hypotheses, not causal findings.
- Outcome joins are labeled ASSOCIATION — never CAUSATION.
- Unresolved metrics (Velocity, Compression, Stability) are not implemented as locked canonical formulas.

## Running

### CLI (per `07` spec)
```bash
python3 -m cli.main pilot status
python3 -m cli.main score operator op_031
python3 -m cli.main compare usage-operation
python3 -m cli.main diagnose operator op_031
python3 -m cli.main workflow show
python3 -m cli.main intervention catalog
python3 -m cli.main export pilot --format md
```

### TUI (per `06` spec)
```bash
python3 -m tui.app
```

### MCP server (per `08` spec)
```bash
# Requires MCP Python SDK (pip install mcp)
python3 -m mcp_server.server

# Or directly:
python3 src/mcp_server/server.py
```

Claude Desktop config:
```json
{
  "mcpServers": {
    "moses": {
      "command": "/path/to/python3",
      "args": ["/path/to/src/mcp_server/server.py"]
    }
  }
}
```

### Website
```bash
cd website && python3 -m http.server 8765
# Open http://localhost:8765
```

### Legacy demo
```bash
python3 src/enterprise_demo.py summary
python3 src/enterprise_demo.py operator op_031
```

## Test suite

```bash
python3 -m pytest tests/ -q
# 81/81 passing (55 P0 + 26 P1/P2 acceptance tests)
```
