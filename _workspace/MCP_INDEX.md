# MCP Server Index

65 configured MCP servers across 15 categories. 40 active in current session.

---

## 1. Cloud Infrastructure & Deployment

| Server | Purpose | Status |
|--------|---------|--------|
| `cloudflare` | Cloudflare Workers/Pages/KV/R2 management via remote MCP | active (tools unavailable — auth refresh needed) |
| `cloudflare-observability` | Cloudflare logs, traces, metrics for deployed workers | active (tools unavailable — auth refresh needed) |
| `vercel` | Vercel project deploy, docs search, git integration | active |
| `supabase` | Supabase database, auth, migrations for sigrank-app | active (tools unavailable — auth refresh needed) |

**Best repos:** `Moses_Enterprise_B2BPilot_` (workers), `_01_sigrank-app` (Next.js + Supabase)

---

## 2. AI Search (MOSES Ecosystem)

| Server | Purpose | Status |
|--------|---------|--------|
| `moses-search` | Semantic search over mos2es.org content | active (Cloudflare AI Search) |
| `sigeconomy-search` | Semantic search over sigeconomy.com content | active (Cloudflare AI Search) |
| `signalaf-search` | Semantic search over signalaf.com content | active (Cloudflare AI Search) |

**Best repos:** `Moses_Enterprise_B2BPilot_/_workers/analytics-worker` (bindings), all public-facing repos for content verification

---

## 3. SEO & Web Indexing

| Server | Purpose | Status |
|--------|---------|--------|
| `gsc-seo` | Google Search Console — general (all properties) | active |
| `gsc-seo-mos2es-com` | GSC scoped to mos2es.com | active |
| `gsc-seo-mos2es-org` | GSC scoped to mos2es.org | active |
| `gsc-seo-mos2es-xyz` | GSC scoped to mos2es.xyz | active |
| `gsc-seo-sigeconomy` | GSC scoped to sigeconomy.com | active |
| `gsc-seo-signomy` | GSC scoped to signomy.xyz | active |
| `indexnow` | IndexNow + Google Indexing API for instant crawl submission | active |

**Best repos:** `1_mos2es-site` (mos2es.com SEO), `_01_sigrank-app` (sigeconomy/signalaf SEO), `1_agent-universe` (signomy.xyz SEO), `1_application-hub` (mos2es.xyz SEO)

---

## 4. Web Search & Content Extraction

| Server | Purpose | Status |
|--------|---------|--------|
| `brave-search` | Brave web, image, video, news, local search | active |
| `web-scrape` | Extract clean markdown from web pages, metadata, structured data | active |
| `markitdown` | Convert any URL or file (PDF, DOCX, HTML) to markdown | active |
| `apify` | Apify actor marketplace for structured web scraping at scale | active (tools unavailable — auth refresh needed) |

**Best repos:** All repos — use for competitive research, content audits, scraping competitor sites

---

## 5. Browser Automation

| Server | Purpose | Status |
|--------|---------|--------|
| `playwright` | Playwright browser automation — navigate, click, fill, screenshot | active |
| `chrome-devtools` | Chrome DevTools Protocol — inspect, evaluate JS, network throttle | active |
| `skyvern` | Browser automation via remote MCP | active (tools unavailable) |

**Best repos:** All repos — use for E2E testing, visual verification, debugging live sites

---

## 6. Code & Repository Intelligence

| Server | Purpose | Status |
|--------|---------|--------|
| `gitmcp` | Search GitHub repo docs and code semantically | active |
| `repomix` | Pack entire codebase into single file for AI analysis | active |
| `codebase-memory` | Index repos into knowledge graph for cross-file tracing | active |
| `filesystem` | Direct file system read/write/edit within allowed dirs | active |

**Best repos:** All repos — `codebase-memory` especially for `Moses_Enterprise_B2BPilot_` (multi-worker tracing), `repomix` for handoffs

---

## 7. Knowledge & Memory

| Server | Purpose | Status |
|--------|---------|--------|
| `knowledge-graph` | Entity/relation graph — create entities, relations, observations | active |
| `santismm-knowledge` | SANTISMM knowledge corpus — multi-domain search | active |
| `screenpipe` | Search screen text, audio transcriptions, meetings, input events | active |

**Best repos:** `Moses_Enterprise_B2BPilot_` (map MOSES ecosystem entities), `search-authority` (canon relationships)

---

## 8. Data Science & Visualization

| Server | Purpose | Status |
|--------|---------|--------|
| `ds-server` | Interactive Plotly charts — histogram, scatter, box, line, heatmap, bar, scatter matrix | active |
| `tooluniverse` | Meta-tool — list, search, and execute tools from a tool universe | active |

**Best repos:** `Moses_Enterprise_B2BPilot_` (operator telemetry visualization), `_01_sigrank-app` (benchmark charts)

---

## 9. Analytics & Product Intelligence

| Server | Purpose | Status |
|--------|---------|--------|
| `posthog` | PostHog product analytics — events, funnels, experiments, session replay | active |
| `crowdreply` | CrowdReply social listening — brand monitoring, mentions, sentiment | active |
| `promptwatch` | Prompt monitoring and observability | active |

**Best repos:** `_01_sigrank-app` (PostHog analytics), `Moses_Enterprise_B2BPilot_` (traffic analysis via PostHog)

---

## 10. MOSES/SigRank Business Logic

| Server | Purpose | Status |
|--------|---------|--------|
| `sigadmin` | Operator admin — lookup, reparse, choose_ratio, retire, CRM inbox/scan, case files | active |

**Best repos:** `SigRank-gtm` (outreach/GTM), `Moses_Enterprise_B2BPilot_` (operator data), `_01_sigrank-app` (leaderboard data)

---

## 11. Writing Quality

| Server | Purpose | Status |
|--------|---------|--------|
| `no-slop` | Strip AI writing tells from text, return 0-100 slop score | active |
| `ai-slop-checker` | Score prose 0-100 on human-readability, grade landing page copy | active |

**Best repos:** `1_mos2es-site` (marketing copy), `_01_sigrank-app` (landing pages), `Moses_Enterprise_B2BPilot_/_03_promo-site` (promo copy)

---

## 12. Creative & 3D

| Server | Purpose | Status |
|--------|---------|--------|
| `blender` | Blender 3D — scene info, code execution, Polyhaven assets | active |

**Best repos:** N/A (standalone creative work)

---

## 13. External Data & Monitoring

| Server | Purpose | Status |
|--------|---------|--------|
| `worldmonitor` | Toronto Police data, market data (equities, commodities, crypto, gold premiums) | active |

**Best repos:** N/A (external data source)

---

## 14. Documentation Lookup

| Server | Purpose | Status |
|--------|---------|--------|
| `context7` | Resolve and query up-to-date docs for any library/framework | active |

**Best repos:** All repos — use before writing code that uses any library (Next.js, Supabase, Cloudflare, etc.)

---

## 15. File Organization

| Server | Purpose | Status |
|--------|---------|--------|
| `file-organizer` | File organization tool | active (tools unavailable) |
| `studious-organizer` | Studious funicular file organizer | active (tools unavailable) |

**Best repos:** N/A (system-level utility)

---

## Repo-to-MCP Mapping

### `1_mos2es-site` (mos2es.com — static site)
**Primary:** `gsc-seo-mos2es-com`, `indexnow`, `moses-search`, `no-slop`, `ai-slop-checker`, `web-scrape`
**Secondary:** `brave-search`, `markitdown`, `context7`, `playwright`, `chrome-devtools`

### `Moses_Enterprise_B2BPilot_` (Cloudflare workers)
**Primary:** `cloudflare`, `cloudflare-observability`, `moses-search`, `sigeconomy-search`, `signalaf-search`, `posthog`, `ds-server`, `sigadmin`, `codebase-memory`
**Secondary:** `context7`, `repomix`, `knowledge-graph`

### `_01_sigrank-app` (sigeconomy.com / signalaf.com — Next.js)
**Primary:** `supabase`, `vercel`, `gsc-seo-sigeconomy`, `sigeconomy-search`, `signalaf-search`, `posthog`, `indexnow`, `no-slop`, `ai-slop-checker`
**Secondary:** `context7`, `playwright`, `chrome-devtools`, `web-scrape`

### `1_agent-universe` (signomy.xyz)
**Primary:** `gsc-seo-signomy`, `web-scrape`, `markitdown`, `no-slop`
**Secondary:** `brave-search`, `context7`

### `1_application-hub` (AQUA / mos2es.xyz)
**Primary:** `gsc-seo-mos2es-xyz`, `moses-search`, `web-scrape`
**Secondary:** `context7`, `playwright`

### `SigRank-gtm` (outreach/GTM)
**Primary:** `sigadmin`, `brave-search`, `web-scrape`, `screenpipe`
**Secondary:** `crowdreply`, `posthog`

### `search-authority` (canon)
**Primary:** `knowledge-graph`, `santismm-knowledge`, `markitdown`
**Secondary:** `brave-search`, `gitmcp`

---

## Servers With Auth Issues (need refresh)

These servers are configured but their tools could not be listed — likely need re-authentication:

- `cloudflare` — re-auth at https://dash.cloudflare.com
- `cloudflare-observability` — same Cloudflare account
- `supabase` — re-auth at https://supabase.com
- `apify` — re-auth at https://apify.com
- `skyvern` — check remote MCP connection
- `file-organizer` — check local server process
- `studious-organizer` — check local server process
- `moses-search` / `sigeconomy-search` / `signalaf-search` — AI Search endpoints (work via Workers bindings, not direct MCP)

---

## Not Currently Active (in config but not loaded this session)

These are in `mcp_config.json` but not loaded as available servers:

`academia`, `ariadne`, `aurelius`, `blogging`, `book-writer`, `chart`, `civitae`, `cloudflare-bindings`, `cloudflare-builds`, `cloudflare-docs`, `crowdreply`, `data-science`, `datacite`, `deepwiki`, `ds-mcp`, `framesmith`, `moses-governance`, `openseo`, `paper-search`, `paperforge`, `promptwatch`, `signomy`, `slidev`, `uno`, `wiki`, `zenodo`

---

*Generated 2026-09-04. Update when MCP configs change.*
