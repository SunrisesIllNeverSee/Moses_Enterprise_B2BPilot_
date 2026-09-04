# AGENTS.md

## Upsilon Architecture Context (2026-08-28)

**Architecture:** `MO§ES → Upsilon → SigRank | SignalAF`

- **Upsilon** = measurement engine / enterprise product (the engine that measures)
- **SigRank** = public leaderboard / benchmark / proof surface (live at signalaf.com)
- **SignalAF** = public distribution / platform brand
- **Yield (Υ)** = metric inside Upsilon: `(cache_read × output) / input²`
- **MO§ES™** = governance framework / methodology

**Owner clarification (2026-08-28):** The primary change is the Upsilon pilot.
agent-universe and sigrank-app changes are minimal — just pointing toward the
pilot and establishing architecture context. All repos get this context so they
understand where it came from and don't try rewriting everything every time.

**Do NOT:**
- Rename package/repo/CLI names (sigrank-app, sigrank-mcp, npx sigrank) — these are technical identifiers
- Rename "SigRank" where it means the public leaderboard/benchmark
- Conflate "Upsilon" (product) with "Yield" (metric) — they are different things
- Mass-rewrite historical/archive content to conform to new branding
- Change patent claims without legal review

**Preserved:**
- `npx sigrank` CLI command
- `sigrank` npm package name
- `sigrank-app`, `sigrank-mcp` repo names
- All URLs (signalaf.com, sigeconomy.com, mos2es.org, signomy.xyz)
- "SigRank leaderboard/board/ranks" references
- Historical and archive content

**Canon source:** Search Authority (commit 790d403). Load canon context before
modifying product definitions, metrics, or terminology:
```bash
export SEARCH_AUTHORITY_PATH="${SEARCH_AUTHORITY_PATH:-$HOME/Developer/_control/search-authority}"
python3 "$SEARCH_AUTHORITY_PATH/canon_cli.py" context sigrank
python3 "$SEARCH_AUTHORITY_PATH/canon_cli.py" context upsilon
```


## Filesystem MCP — REQUIRED for file operations

This is a core framework/search/ello/product repository. When performing
file operations, prefer the Filesystem MCP tools over ad-hoc shell commands:

- `list_directory` / `directory_tree` — structured directory traversal
- `search_files` — glob-pattern file search within allowed paths
- `read_multiple_files` — batch file reads (failures do not stop the batch)
- `edit_file` with `dryRun: true` — preview structural changes before applying

Allowed paths: ~/Developer, ~/.config/devin, ~/.config/sigrank, ~/Desktop

For single-file reads and edits, native tools are acceptable. For multi-file
operations, directory exploration, and structural changes, use the Filesystem MCP.


## Context7 MCP — REQUIRED before writing library code

This repo writes code against external libraries. Before using a library API
that may have changed since training data cutoff, query Context7 to verify
the current pattern:

1. resolve-library-id — find the library (e.g. "Cloudflare Workers", "Supabase")
2. query-docs — ask the specific question (e.g. "KV write limits free tier")

Key libraries in this stack:
- Cloudflare Workers: /websites/developers_cloudflare_workers
- Cloudflare KV: /llmstxt/developers_cloudflare_kv_llms_txt
- Supabase: /supabase/supabase
- Next.js: /vercel/next.js
- Hono: /websites/hono_dev
- Playwright: /microsoft/playwright
- Pydantic: /pydantic/pydantic
- Python: /python/cpython

Do not rely on training data for library APIs. Do not call more than 3 times
per question.


## Repomix MCP — Codebase orientation

When starting work in this repo or picking up a handoff, use Repomix MCP to
pack the codebase and grep for key patterns (function names, formulas, config,
dependencies) to orient yourself in 2-3 calls instead of reading files one
by one. Useful for canon alignment audits (grep for formula implementations
and compare against Search Authority definitions) and cross-repo consistency
checks.


## MCP Server Recommendations for This Repo

Full index: `_workspace/MCP_INDEX.md`

**Primary (use regularly):**
- `moses-search` / `sigeconomy-search` / `signalaf-search` — AI Search bindings for all three domains
- `posthog` — product analytics, traffic, events for deployed workers
- `ds-server` — Plotly charts for operator telemetry visualization
- `sigadmin` — operator admin (lookup, reparse, retire, CRM scan)
- `codebase-memory` — index multi-worker repo for cross-file call tracing
- `indexnow` — submit new/changed URLs to Bing/Yandex for instant indexing
- `gsc-seo-mos2es-org` — Google Search Console data for mos2es.org

**Secondary (use as needed):**
- `context7` — verify Cloudflare Workers/KV/Hono API patterns before writing
- `repomix` — pack codebase for handoffs or cross-repo audits
- `knowledge-graph` — map MOSES ecosystem entities and relationships
- `brave-search` — competitive research, find similar tools/benchmarks
- `web-scrape` — extract content from competitor sites for comparison
- `no-slop` / `ai-slop-checker` — check promo/demo copy for AI writing tells

**Not needed here:**
- `supabase` / `vercel` — those are for the sigrank-app repo
- `blender` / `worldmonitor` — unrelated to this repo
