# MOSES Enterprise B2B Pilot

**Enterprise AI Operator Evaluation** — measure the operating system behind enterprise AI.

MOSES is a platform for evaluating how human operators use AI tools (ChatGPT, Claude, Codex, Copilot, Cursor) across five canonical metrics, then benchmarking, diagnosing, intervening, and re-measuring. It ships as a Python platform, a CLI, an MCP server with 27 tools, and three Cloudflare Worker-deployed websites.

## Live surfaces

| Surface | URL | What |
|---------|-----|------|
| Promo site | https://mos2es.org | Marketing, docs, demo instructions |
| Enterprise demo | https://enterprise.mos2es.org | Interactive product demo |
| MCP server | https://mcp.mos2es.org/mcp | 27-tool MCP server (22 read + 5 write) |
| MCP health | https://mcp.mos2es.org/ | Server info JSON |

## Repository structure

```
_01_platform/          Python platform (the product)
  src/                 Source code (domain, metrics, analysis, diagnostics, CLI, MCP server)
  tests/               527 tests
  demo_data/           Synthetic demo cohort (50 operators, 1668 observations)
  scripts/             Utility scripts
  schemas/             JSON schemas

_02_demo-website/      Enterprise demo site (enterprise.mos2es.org)
_03_promo-site/        Promo site (mos2es.org)
  demo/run.py          One-liner demo runner
  .well-known/mcp.json MCP server discovery

_04_onepager/          One-pager site

_workers/              Cloudflare Workers
  promo-worker/        mos2es.org worker (static assets + AEO enhancements)
  moses-worker/        enterprise.mos2es.org worker (static assets)
  onepager-worker/     One-pager worker (static assets)
  mcp-worker/          MCP server worker (computes live from raw data, 27 tools)
```

## Quick start

### Run the demo

```bash
# One-liner (no clone needed)
curl -sL https://mos2es.org/demo/run.py | python3 -

# Or clone and run
git clone https://github.com/SunrisesIllneverSee/Moses_Enterprise_B2BPilot_.git
cd Moses_Enterprise_B2BPilot_/_01_platform
pip install rich
python3 -m src.cli.main demo full
```

The demo runs 11 steps (load, evaluate, benchmark, diagnose, operator x system, intervene, re-evaluate, outcome lineage, report, visualize) and produces a markdown + PDF pilot readout.

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

## Deploy the workers

```bash
# Install wrangler if needed
npm install -g wrangler

# Deploy each worker
cd _workers/promo-worker && wrangler deploy
cd _workers/moses-worker && wrangler deploy
cd _workers/onepager-worker && wrangler deploy
cd _workers/mcp-worker && wrangler deploy
```

## MCP worker data sync

The MCP worker at `_workers/mcp-worker/` computes live from raw data files (`observations.js`, `lineages.js`) that are auto-generated from the platform's demo data. To regenerate after updating demo data:

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

## The 5 canonical metrics

| Metric | What it measures |
|--------|-----------------|
| Yield | Fraction of AI output that survives to committed state |
| Leverage | Output value per token consumed |
| Token SNR | Signal-to-noise ratio in token usage |
| Construction | Fraction of output built incrementally vs replaced |
| Divergence | Gap between usage patterns and operational patterns |

## Key conventions

- **Brand:** MOSES (use the section sign)
- **All outcome claims are ASSOCIATION, never CAUSATION** unless backed by a controlled experiment
- **Composite score is DEVELOPMENTAL, never PERSONNEL** — no punitive use, no leaderboard
- **Operator similarity is metric similarity, NOT personality matching**
- **Content-free telemetry** — no prompt text, no output bodies, no code content in observations

## License

See [LICENSE](LICENSE).
