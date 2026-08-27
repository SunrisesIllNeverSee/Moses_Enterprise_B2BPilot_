# MO§ES™ Enterprise — AI Operator Evaluation Platform

> **Live: [mos2es.org](https://mos2es.org)** — Systems intelligence for the human-AI operating system.
> The new standard in performative metrics and benchmarks for AI operators.
> Baselines system intelligence for everyday operations and AI workflows.
> _Content-free token telemetry. Never your prompts._

<div align="center">

**Enterprise AI operator evaluation. Measure how people operate AI — not the AI model itself.**

MO§ES™ curates a company's system intelligence — how effectively people drive AI systems across tools, tasks, workflows, and conditions. The same way BI sees the business, MO§ES™ sees how the business operates AI.

[![live](https://img.shields.io/badge/live-mos2es.org-gold.svg?style=flat-square)](https://mos2es.org)
[![enterprise](https://img.shields.io/badge/demo-enterprise.mos2es.org-blue.svg?style=flat-square)](https://enterprise.mos2es.org)
[![MCP](https://img.shields.io/badge/MCP-27%20tools-green.svg?style=flat-square)](https://mcp.mos2es.org/mcp)
[![demo](https://img.shields.io/badge/demo-11%20steps-orange.svg?style=flat-square)](https://mos2es.org/demo)
[![tests](https://img.shields.io/badge/tests-527%20pass-brightgreen.svg?style=flat-square)](#run-the-test-suite)
[![license](https://img.shields.io/badge/license-PolyForm%20NC-orange.svg?style=flat-square)](./LICENSE)
[![deploy](https://img.shields.io/badge/deploy-Cloudflare-F38020.svg?style=flat-square&logo=cloudflare&logoColor=white)](https://cloudflare.com)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![MCP](https://img.shields.io/badge/protocol-MCP-purple.svg?style=flat-square)](https://modelcontextprotocol.io)

</div>

<p align="center">
  <a href="https://mos2es.org/contact"><img src="https://img.shields.io/badge/Book%20a%20Demo-Baseline%20Your%20System%20 Intelligence-gold?style=for-the-badge&labelColor=1a1a1a&color=daa520" alt="Book a Demo" /></a>
  &nbsp;
  <a href="https://mos2es.org/demo"><img src="https://img.shields.io/badge/Run%20the%20Demo-11%20step%20pipeline-blue?style=for-the-badge&labelColor=1a1a1a" alt="Run the Demo" /></a>
</p>

## Table of Contents

- [What is MO§ES™?](#what-is-moses)
- [The MO§ES™ ecosystem](#the-moses-ecosystem)
- [Live surfaces](#live-surfaces)
- [Quick start](#quick-start)
- [The 11-step demo pipeline](#the-11-step-demo-pipeline)
- [The 5 canonical metrics](#the-5-canonical-metrics)
- [Repository structure](#repository-structure)
- [MCP server](#mcp-server)
- [Cloudflare Workers](#cloudflare-workers)
- [Key conventions](#key-conventions)
- [Complement, don't replace](#complement-dont-replace)
- [License](#license)

---

## What is MO§ES™?

MO§ES™ is an enterprise AI operator evaluation platform. It measures how **people operate AI systems** — not the AI models themselves, not usage volume, not self-reported proficiency. Using content-free token telemetry (input, output, cache read, cache write — no prompt text, no response text), MO§ES™ baselines system intelligence across:

- **Operators** — how effectively individuals drive AI
- **Teams** — cohort distributions and capability topology
- **Workflows** — where AI fits in the work, not just whether it's used
- **Organizations** — cross-team benchmarking and capability mapping

The platform builds **bespoke evals** around your workflows, roles, and AI systems, benchmarks performance against internal and external reference populations, diagnoses capability gaps and divergence patterns, tests targeted interventions, and re-measures what changes.

### The positioning

**BI sees the business. MO§ES™ sees how the business operates AI.**

LMSYS benchmarks models. Braintrust evaluates product outputs. Langfuse traces LLM calls. WakaTime tracks time. CostHawk tracks spend. None of them see the system intelligence of everyday operations and AI workflows. MO§ES™ is the missing layer.

## The MO§ES™ ecosystem

| Repo / Site | What it is | URL |
|-------------|-----------|-----|
| **MO§ES™ Enterprise** (this repo) | The platform — Python eval engine, CLI, MCP server, demo, promo, enterprise demo, workers | [mos2es.org](https://mos2es.org) |
| **SigRank SignalAF** | The public leaderboard — operator rankings by token cascade efficiency | [signalaf.com](https://signalaf.com) |
| **SigRank MCP** | The instrument — extracts token pillars, computes cascade, submits to leaderboard | `npx sigrank` |
| **SIGNOMY** | Governed AI agent marketplace — ranked agents form teams, run missions, earn revenue | [signomy.xyz](https://signomy.xyz) |
| **SigEconomy** | Public LLM operator evals — read-only leaderboard, SEO/AEO surface | [sigeconomy.com](https://sigeconomy.com) |

## Live surfaces

| Surface | URL | What |
|---------|-----|------|
| Promo site | https://mos2es.org | Marketing, methodology, demo, comparisons, booking |
| Enterprise demo | https://enterprise.mos2es.org | Interactive product walkthrough (evaluate → diagnose → workflow → compare) |
| MCP server | https://mcp.mos2es.org/mcp | 27-tool MCP server (22 read + 5 write), streamable HTTP |
| MCP server info | https://mcp.mos2es.org/ | Server info JSON (version, tool count, transport) |
| MCP server card | https://mcp.mos2es.org/.well-known/mcp/server-card.json | Full server card with all tool schemas |
| OpenAPI spec | https://mos2es.org/openapi.json | REST API specification |
| LLM guidance | https://mos2es.org/llms.txt | llms.txt for AI agents and crawlers |
| Sitemap | https://mos2es.org/sitemap.xml | XML sitemap |
| Book a demo | https://mos2es.org/contact | B2B demo booking with structured intake form |

## Quick start

### Run the demo (one-liner, no clone needed)

```bash
curl -sL https://mos2es.org/demo/run.py | python3 -
```

This clones the repo to a temp directory, installs `rich`, and runs the full 11-step demo pipeline. Requires Python 3.10+ and git.

### Clone and run

```bash
git clone https://github.com/SunrisesIllneverSee/Moses_Enterprise_B2BPilot_.git
cd Moses_Enterprise_B2BPilot_/_01_platform
pip install rich
python3 -m src.cli.main demo full
```

### Run the test suite

```bash
cd _01_platform
python3 -m pytest tests/ -q
# 527 tests pass
```

### Run the MCP server locally

```bash
cd _01_platform
pip install mcp
python3 -m src.mcp_server.server
```

### Use the remote MCP server

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "moses": {
      "url": "https://mcp.mos2es.org/mcp",
      "transport": "http"
    }
  }
}
```

Or call tools directly:

```bash
curl -s -D /tmp/h -X POST https://mcp.mos2es.org/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' > /dev/null
SID=$(grep -i "^mcp-session-id:" /tmp/h | tr -d '\r\n' | sed 's/.*: //')
curl -s -X POST https://mcp.mos2es.org/mcp \
  -H "Content-Type: application/json" -H "MCP-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python3 -m json.tool
```

## The 11-step demo pipeline

| Step | Name | What it does |
|------|------|-------------|
| 1 | LOAD | Load 50-operator synthetic cohort |
| 2 | EVALUATE | Compute per-observation metrics |
| 3 | BENCHMARK | Compute percentile positions |
| 4 | DIAGNOSE | Run pattern detectors |
| 5 | OPERATOR×SYSTEM | Decompose operator vs system effects |
| 6 | INTERVENE | Assign targeted interventions |
| 7 | RE-EVALUATE | Re-measure post-intervention |
| 8 | OUTCOME LINEAGE | Trace observations → transformations → artifacts → outcomes |
| 9 | REPORT | Generate markdown + PDF pilot readout |
| 10 | VISUALIZE | Generate 9 architecture diagrams |
| 11 | DASHBOARD | Export executive HTML dashboard |

The demo runs on fully synthetic data. No real operators, no real prompt text, no real API calls. Deterministic — running twice produces identical results.

## The 5 canonical metrics

| Metric | What it measures |
|--------|-----------------|
| **Yield** | Fraction of AI output that survives to committed state |
| **Leverage** | Output value per token consumed |
| **Token SNR** | Signal-to-noise ratio in token usage |
| **Construction** | Fraction of output built incrementally vs replaced |
| **Divergence** | Gap between usage patterns and operational patterns |

**15 evaluation families. 13 benchmark classes. 4 measurement levels (Operator, Team, Workflow, Organization).**

## Repository structure

```
_01_platform/          Python platform (the product)
  src/                 Source code (domain, metrics, analysis, diagnostics, CLI, MCP server)
  tests/               527 tests
  demo_data/           Synthetic demo cohort (50 operators, 1,668 observations)
  scripts/             Utility scripts
  schemas/             JSON schemas

_02_demo-website/      Enterprise demo site (enterprise.mos2es.org)
_03_promo-site/        Promo site (mos2es.org)
  vs/                  16 competitor comparison pages
  alternatives/        8 alternatives listicle pages
  concepts/            10 concept explainer pages
  guides/              4 how-to guides
  demo/run.py          One-liner demo runner
  .well-known/mcp.json MCP server discovery

_04_onepager/          One-pager site

_workers/              Cloudflare Workers
  promo-worker/        mos2es.org worker (static assets + AEO/SEO/GEO headers)
  moses-worker/        enterprise.mos2es.org worker (static assets)
  onepager-worker/     One-pager worker (static assets)
  mcp-worker/          MCP server worker (computes live from raw data, 27 tools)
```

## MCP server

The MCP server exposes **27 tools** (22 read + 5 write) over streamable HTTP at `https://mcp.mos2es.org/mcp`. No authentication required for the public server.

**Read tools** include: cohort stats, operator profiles, metric distributions, benchmark positions, divergence findings, intervention outcomes, outcome lineage, workflow fit, org topology, and more.

**Write tools** include: create intervention, assign intervention, record outcome, create eval configuration, create pilot configuration.

The server computes live from raw observation data — no pre-computed results. Every call runs the actual scoring, benchmarking, and diagnostic engines.

### Server card

```bash
curl -s https://mcp.mos2es.org/.well-known/mcp/server-card.json | python3 -m json.tool
```

Returns the full server card with all 27 tool schemas, transport info, and metadata.

## Cloudflare Workers

Four Workers deploy from this repo:

| Worker | Domain | What |
|--------|--------|------|
| `moses-promo` | mos2es.org | Promo site + AEO/SEO/GEO headers + agent discoverability (llms.txt, sitemap, OpenAPI, MCP links) |
| `moses` | enterprise.mos2es.org | Enterprise demo site |
| `moses-onepager` | (workers.dev) | One-pager |
| `moses-mcp` | mcp.mos2es.org | MCP server (27 tools, live computation) |

### Deploy

```bash
npm install -g wrangler

cd _workers/promo-worker && wrangler deploy
cd _workers/moses-worker && wrangler deploy
cd _workers/onepager-worker && wrangler deploy
cd _workers/mcp-worker && wrangler deploy
```

### MCP worker data sync

The MCP worker computes live from raw data files (`observations.js`, `lineages.js`) auto-generated from the platform's demo data. To regenerate after updating demo data:

```bash
cd _workers/mcp-worker/src
python3 -c "
import json
with open('../../../_01_platform/demo_data/observations.jsonl') as f:
    data = [json.loads(l) for l in f if l.strip()]
with open('observations.js', 'w') as f:
    f.write('export default '); json.dump(data, f); f.write(';\n')
with open('../../../_01_platform/demo_data/lineages.jsonl') as f:
    data = [json.loads(l) for l in f if l.strip()]
with open('lineages.js', 'w') as f:
    f.write('export default '); json.dump(data, f); f.write(';\n')
"
```

## Key conventions

- **Brand:** MO§ES™ (use the section sign §)
- **All outcome claims are ASSOCIATION, never CAUSATION** unless backed by a controlled experiment
- **Composite score is DEVELOPMENTAL, never PERSONNEL** — no punitive use, no employee leaderboard
- **Operator similarity is metric similarity, NOT personality matching**
- **Content-free telemetry** — no prompt text, no output bodies, no code content in observations
- **No prompt-content surveillance** — operator performance is observable from token structure alone
- **Governance-ready** — evidence labels (DEVELOPMENTAL, HYPOTHESIS, ASSOCIATION) on every output

## Complement, don't replace

MO§ES™ works alongside your existing BI, eval suites, observability tools, and productivity analytics. It measures the systems intelligence layer they can't see. Not a replacement — the missing piece.

### Five pillars

| # | Pillar | What |
|---|--------|------|
| 1 | **Systems Intelligence** | MO§ES™ sees the human-AI operating system the way BI sees the business. Operator performance, workflow fit, tool selection, capability distribution, intervention outcomes — all measured from structure, not content. |
| 2 | **Standard Operational Performative Metrics** | 5 canonical metrics. 15 eval families. 13 benchmark classes. 4 measurement levels. An open, documented spec for measuring how humans operate AI. The reference implementation is MO§ES™. |
| 3 | **Bespoke Enterprise Evals** | Your company should not inherit someone else's definition of AI proficiency. Evals built around your workflows, roles, models, and performance questions. |
| 4 | **Complement, Don't Replace** | Works alongside your existing BI, eval suites, observability tools, and productivity analytics. The missing piece, not a replacement. |
| 5 | **Privacy-First / Governance** | Content-free token telemetry. No prompt text. No surveillance. DEVELOPMENTAL / HYPOTHESIS / ASSOCIATION evidence labels on every output. Governance-ready out of the box. |

## License

PolyForm Noncommercial 1.0.0 — see [LICENSE](./LICENSE). Personal use, research, and noncommercial use permitted. Commercial use requires a license. Patent pending.

---

<div align="center">

**[mos2es.org](https://mos2es.org)** · **[Book a demo](https://mos2es.org/contact)** · **[Run the demo](https://mos2es.org/demo)** · **[MCP server](https://mcp.mos2es.org/mcp)**

Built by Deric J. McHenry — Ello Cello LLC

</div>
