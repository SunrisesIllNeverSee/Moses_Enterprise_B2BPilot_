# B2B Lead Handoff — 2026-09-02

## Session chain

Aug 28 – Sep 2, 2026. Commits `2ef3c5d` through `862dfc2` on `main`.

Repository: `https://github.com/SunrisesIllNeverSee/Moses_Enterprise_B2BPilot_.git`
Branch: `main` (HEAD: `862dfc2`)

---

## What was built this session chain

### Analytics & observability
- Cloudflare analytics worker with KV storage, server-side bot detection, per-zone dashboards
- Crawl-to-referral ratio tracking across `mos2es.org`, `mos2es.com`, `signalaf.com`
- Markdown content negotiation for AI agents (`Accept: text/markdown`)
- Analytics dashboard with tabbed interface

### Schema & SEO/AEO/GEO
- Full schema.org rollout with moses namespace + canon fields (all 6 domains pass)
- Entity stacking: Organization, founder, Wikidata knowsAbout, competitor about
- 50-keyword research CSV + Semrush Keyword Strategy Builder integration
- AI agent discovery surfaces: `llms.txt`, `agent.json`, `agent-card.json`, `agent-skills/`, `auth.md`, `openapi.json`

### Homepage & commercial repositioning
- Homepage rebuilt to 6 sections (Hero, Problem, What Upsilon measures, Baseline Assessment, Privacy, Ecosystem)
- "Killer Experiment" renamed to "Baseline Assessment" across all pages and agent-facing files
- Single commercial offer: 30-day Baseline Assessment, starting at $15K, one team/one workflow
- Stale pricing removed ($45K, $150K, "6 commercial packages", "Four engagement tiers")
- Clean URLs site-wide (`.html` stripped from all internal links)

### Concept consolidation (Sep 2)
- 24 concept pages → 3 robust pages:
  - `/concepts/metrics` — 8 Upsilon metrics + 5 framework definitions
  - `/concepts/ai-evaluation` — four-layer landscape, tools, frameworks, compliance, trends
  - `/concepts/confirmation-hacking` — methodology risk (renamed from confirmation-hacking-ai-evaluation)
- 22 old URLs have 301 redirects in promo worker
- Metric formulas aligned with owner-approved canon:
  - Yield: `(R × O) / I²` (was `O / (I + O + R + W)`)
  - Leverage: `R / I` (was `(R + W) / I`)
  - SNR: `O / (I + O)` (was `O / (I + O + R)`)
  - Added Velocity, 10xDEV, Scale V (were in canon but missing from site)
  - Removed Composite Score/ODI (not in canon)
- `llms.txt`: 24 → 3 concept entries. `sitemap.xml`: 24 → 3 concept URLs.
- 79 files changed, +1,291 / −7,842 lines

---

## Repository structure

```
Moses_Enterprise_B2BPilot_/
├── AGENTS.md                    — Upsilon architecture context + canon rules
├── ECOSYSTEM_SCHEMA_MATRIX.md   — schema validation status for all 6 domains
├── README.md
├── _01_platform/                — Python platform (CLI, TUI, MCP, metrics, demo data)
│   ├── src/
│   │   ├── cli/main.py          — `enterprise` CLI entry point
│   │   ├── service.py           — PilotService
│   │   ├── domain/              — domain models
│   │   ├── metrics/             — metric computation
│   │   ├── repository/          — data access
│   │   ├── analysis/            — diagnostics, benchmarking
│   │   ├── ingest/              — telemetry ingestion
│   │   ├── reporting/           — report generation
│   │   ├── interventions/       — intervention testing
│   │   ├── workflow/            — workflow fit analysis
│   │   ├── outcomes/            — outcome lineage
│   │   ├── tui/                 — terminal UI
│   │   └── mcp_server/          — MCP server scaffold
│   ├── tests/                   — 19 test files, all passing
│   ├── demo_data/               — 50-operator synthetic cohort
│   ├── pyproject.toml           — package: enterprise-operator-intelligence-demo v0.4.0
│   └── requirements.txt         — rich>=13
├── _02_demo-website/            — enterprise demo (served by moses-worker)
│   ├── index.html               — dashboard
│   ├── evaluate.html            — operator evaluation
│   ├── compare.html             — operator comparison
│   ├── diagnose.html            — diagnostics
│   ├── develop.html             — interventions
│   ├── workflow.html            — workflow fit
│   ├── data.html                — data explorer
│   ├── verify.html              — verification
│   ├── enterprise.html          — enterprise view
│   ├── pilot.html               — pilot management
│   ├── product.html             — product overview
│   ├── methodology.html         — methodology
│   ├── research.html            — research
│   └── contact.html             — contact
├── _03_promo-site/              — promotional site (served by promo-worker)
│   ├── index.html               — homepage (6 sections)
│   ├── product.html             — product page
│   ├── methodology.html         — methodology page
│   ├── research.html            — research page
│   ├── commercial-offer.html    — $15K Baseline Assessment
│   ├── pilot-readout.html       — pilot readout sample
│   ├── killer-experiment.html   — Baseline Assessment (legacy URL, content updated)
│   ├── contact.html, about.html, privacy.html, docs.html, faq.html, demo.html
│   ├── concepts/                — 3 consolidated pages (metrics, ai-evaluation, confirmation-hacking)
│   ├── blog/                    — 6 blog posts
│   ├── guides/                  — 4 guide pages
│   ├── vs/                      — 16 competitor comparison pages
│   ├── alternatives/            — 6 alternatives pages
│   ├── .well-known/             — agent discovery (agent.json, agent-card.json, agent-skills/, auth.md)
│   ├── llms.txt                 — LLM-readable site summary
│   ├── sitemap.xml              — sitemap
│   ├── openapi.json             — OpenAPI spec
│   ├── analytics-beacon.js      — client-side analytics beacon
│   └── style.css                — Upsilon type system
├── _04_onepager/                — one-page summary
├── _workers/                    — Cloudflare Workers
│   ├── promo-worker/            — mos2es.org (static assets + clean URLs + redirects)
│   ├── moses-worker/            — enterprise.mos2es.org (demo site)
│   ├── mcp-worker/              — mcp.mos2es.org (MCP server, 27+ tools)
│   ├── analytics-worker/        — analytics + dashboard + crawl control
│   └── onepager-worker/         — one-pager
├── _workspace/                  — session artifacts
│   ├── handoffs/                — this file
│   ├── prompts/                 — prompt handoffs (for other agents/sessions)
│   ├── scratch/                 — scratch notes
│   ├── content-briefs/          — SEO content briefs
│   └── keywords/                — keyword research CSVs
├── scripts/
│   └── update-enterprise-jsonld.py
├── glama.json
└── server.json
```

---

## Architecture

```
MO§ES™ (governance framework)
  ↓ governs
Upsilon (measurement engine / enterprise product)
  ↓ produces results for
SigRank (public leaderboard / proof surface → signalaf.com)
  ↓ distributed via
SignalAF (public distribution / platform brand)
```

### Domains

| Domain | Worker | Content | Purpose |
|---|---|---|---|
| `mos2es.org` | `moses-promo` | `_03_promo-site/` | Public marketing, docs, SEO/AEO/GEO |
| `enterprise.mos2es.org` | `moses` | `_02_demo-website/` | Interactive enterprise demo |
| `mcp.mos2es.org` | `moses-mcp` | MCP server | AI-agent-facing MCP service (27+ tools) |
| Analytics routes | `moses-analytics` | — | Analytics, crawl control, dashboards |

---

## Signing in

### Cloudflare (Workers deploy)

```bash
# Wrangler is installed at ~/.local/bin/wrangler
# Already authenticated via OAuth token (burnmydays@proton.me)
# Account ID: 8251078af351cd5b19cb73a3435e446f

wrangler whoami                    # verify auth
wrangler deploy                    # deploy a worker (run from worker dir)
wrangler tail                      # live logs
wrangler kv:namespace list         # list KV namespaces
```

### Google Search Console (GSC)

GSC is verified via service account + DNS. Toolkit lives outside this repo:

```bash
export GSC_SA_KEY=~/.config/sigrank/gsc-sa.json
cd ~/Developer/active/SigRank-repos/scripts/gsc

node gsc.mjs sitemaps:list          # registered sitemaps + error counts
node gsc.mjs sitemaps:submit        # resubmit sitemap.xml
node gsc.mjs sitemaps:delete <url>  # remove a stale sitemap
node gsc.mjs index <url> [url...]   # push URL(s) to Indexing API
node gsc.mjs inspect <url>          # URL inspection (verdict + coverage)
node gsc.mjs check:index --push     # inspect all sitemap URLs + auto-push unindexed
node gsc.mjs analytics 28           # clicks/impressions last N days
```

GSC property: `sc-domain:signalaf.com` (Domain property).

### Search Authority (canon)

```bash
export SEARCH_AUTHORITY_PATH="${SEARCH_AUTHORITY_PATH:-$HOME/Developer/_control/search-authority}"

python3 "$SEARCH_AUTHORITY_PATH/canon_cli.py" context sigrank
python3 "$SEARCH_AUTHORITY_PATH/canon_cli.py" context upsilon
python3 "$SEARCH_AUTHORITY_PATH/canon_cli.py" context moses
python3 "$SEARCH_AUTHORITY_PATH/canon_cli.py" context ecosystem

# MCP server alternative:
python3 "$SEARCH_AUTHORITY_PATH/canon_mcp.py"

# Validate canon:
python3 "$SEARCH_AUTHORITY_PATH/canon_cli.py" validate
```

**Load canon context before modifying:** metric formulas, product definitions, taxonomy, methodology, ecosystem relationships, terminology, public positioning.

### Git

```bash
cd ~/Developer/active/b2bpilot/Moses_Enterprise_B2BPilot_
git remote -v    # origin → github.com/SunrisesIllNeverSee/Moses_Enterprise_B2BPilot_.git
git pull origin main
git push origin main
```

---

## Running things locally

### Python platform CLI

```bash
cd ~/Developer/active/b2bpilot/Moses_Enterprise_B2BPilot_/_01_platform

# Run the CLI
PYTHONPATH=src python3 -m cli.main --help
PYTHONPATH=src python3 -m cli.main pilot
PYTHONPATH=src python3 -m cli.main demo status
PYTHONPATH=src python3 -m cli.main demo full
PYTHONPATH=src python3 -m cli.main --json metrics

# Run tests
PYTHONPATH=src python3 -m pytest tests/ -v          # all 19 tests
PYTHONPATH=src python3 -m pytest tests/test_engine.py -q
```

### Cloudflare Workers (local dev)

```bash
cd ~/Developer/active/b2bpilot/Moses_Enterprise_B2BPilot_/_workers/promo-worker
wrangler dev --port 8787

cd ../mcp-worker
wrangler dev --port 8788

cd ../analytics-worker
wrangler dev --port 8789

cd ../moses-worker
wrangler dev --port 8790
```

### Deploy workers

```bash
cd ~/Developer/active/b2bpilot/Moses_Enterprise_B2BPilot_/_workers/promo-worker
wrangler deploy

cd ../mcp-worker && wrangler deploy
cd ../analytics-worker && wrangler deploy
cd ../moses-worker && wrangler deploy
```

---

## To-do list

### Immediate (blocking / unfinished from this session)

1. **Deploy the promo worker** — the 22 new 301 redirects for old concept URLs are in `_workers/promo-worker/src/index.js` but NOT yet deployed to Cloudflare. Old concept URLs will 404 until deploy.
   ```bash
   cd _workers/promo-worker && wrangler deploy
   ```

2. **GSC sitemap resubmit** — after deploy, resubmit sitemap and push the 3 new concept URLs:
   ```bash
   export GSC_SA_KEY=~/.config/sigrank/gsc-sa.json
   cd ~/Developer/active/SigRank-repos/scripts/gsc
   node gsc.mjs sitemaps:submit
   node gsc.mjs index https://mos2es.org/concepts/metrics https://mos2es.org/concepts/ai-evaluation https://mos2es.org/concepts/confirmation-hacking
   node gsc.mjs check:index --push
   ```

### Short-term (content / cleanup)

3. **`killer-experiment.html` path rename** — content says "Baseline Assessment" but URL is still `/killer-experiment`. Rename file to `baseline-assessment.html`, add 301 redirect in promo worker, update all internal links, update sitemap + llms.txt.

4. **Blog post formula audit** — `blog/performative-benchmarks-vs-self-report.html` still has old formulas (`O / (I + O + R + W)` etc.) in its prose. Left as historical content per AGENTS.md, but may want a separate pass to align with canon or add a note.

5. **MCP worker metric formulas** — the MCP worker (`_workers/mcp-worker/src/index.js`) tool descriptions still reference old metric names and formulas (e.g., `leverage, yield, token_snr, log_leverage, construction` and the old composite score weights). Should be updated to canon: Yield `(R×O)/I²`, Leverage `R/I`, SNR `O/(I+O)`, plus Velocity, 10xDEV, Scale V.

6. **Enterprise demo site formulas** — `_02_demo-website/` pages may still reference old formulas. Audit and align with canon.

7. **Platform code formulas** — `_01_platform/src/metrics/` may use old formulas. Audit against canon. The canonical test in sigrank-app uses `Yield = (cache_read × output) / input²` — the platform should match.

### Medium-term (growth / SEO)

8. **Homepage review** — the homepage title/description were manually edited to "Enterprise AI Operator Intelligence" / "Nonlinear intelligence from linear telemetry." Review in browser to confirm the full homepage reads coherently.

9. **Semrush audit follow-up** — re-run Semrush site audit after deploy to verify the concept consolidation didn't introduce new errors.

10. **Blog expansion** — 6 blog posts on `mos2es.org`. Consider adding posts targeting the consolidated concept keywords (AI evaluation, AI evaluation tools, AI evaluation frameworks) that now redirect to the single `/concepts/ai-evaluation` page.

11. **Internal linking audit** — verify that the 16 `/vs/` comparison pages and 6 `/alternatives/` pages link to the new consolidated concept pages with correct anchors.

### Long-term (platform / product)

12. **Upsilon pilot readiness** — the Python platform (`_01_platform/`) has a 50-operator synthetic demo. Prepare for real pilot deployment: telemetry ingestion from real providers, cohort management, reporting pipeline.

13. **MCP server production hardening** — the MCP worker has 27+ tools but tool descriptions reference old formulas. Update tool schemas, test against real MCP clients, publish updated `server-card.json`.

14. **Analytics dashboard expansion** — the Cloudflare analytics dashboard tracks crawl/pageview data. Consider adding AEO-specific metrics (AI overview appearances, citation tracking) as those tools become available.

---

## Scratch / business notes

### Current commercial offer

- **Product:** 30-day Baseline Assessment
- **Price:** Starting at $15K
- **Scope:** One team, one workflow
- **Deliverable:** Baseline metrics + diagnostics + one targeted intervention recommendation
- **Evidence grade:** ASSOCIATION (not CAUSATION without controlled experiment)
- **Extended engagement:** Discussed after baseline, not advertised as predefined tiers

### Canon-critical formulas (owner-approved, do not change without owner directive)

| Metric | Formula | Notes |
|---|---|---|
| Yield (Υ) | `(cache_read × output) / max(input, 1)²` | Signature Upsilon metric. Cascade: Transmission × Commitment × Reuse. |
| SNR | `output / (input + output)` | Output share of fresh flow |
| Velocity | `output / max(input, 1)` | Output per fresh input |
| Leverage | `cache_read / max(input, 1)` | Cache reuse per fresh input |
| 10xDEV | `log₁₀(leverage)` | Logarithmic cascade summary |
| Scale V | `log₁₀(input + output + cache_create + cache_read)` | Log token volume |
| Construction | `cache_write / cache_read` | New context per read |
| Efficiency | `(cache_read + cache_create + output) / max(input, 1) / 4` | Display diagnostic only |

### Governance constraints (non-negotiable)

- No prompt or output content collection
- No punitive employee scoring
- No employee ranking by name in management reports
- Association claims labeled ASSOCIATION, not CAUSATION, without controlled experiments
- Evidence labels enforced: PROVEN, MEASURED, OBSERVED, DERIVED, HYPOTHESIS, PILOT
- Decision-use labels: DEVELOPMENTAL, ASSOCIATION, VALIDATION REQUIRED
- Canonical display: MO§ES™ (never MO§E§)
- MO§ES™ evaluates AI operators, not AI models
- Archetype = shape. Class = scale/qualification. Rank = field position.
- The harness may measure authority, but cannot manufacture authority
- Automated systems may not promote claims into owner-approved truth

### Key file locations

| What | Path |
|---|---|
| Promo site | `_03_promo-site/` |
| Enterprise demo | `_02_demo-website/` |
| Python platform | `_01_platform/` |
| Promo worker | `_workers/promo-worker/src/index.js` |
| MCP worker | `_workers/mcp-worker/src/index.js` |
| Analytics worker | `_workers/analytics-worker/src/index.js` |
| Moses worker (demo) | `_workers/moses-worker/src/index.js` |
| llms.txt | `_03_promo-site/llms.txt` |
| sitemap.xml | `_03_promo-site/sitemap.xml` |
| Agent card | `_03_promo-site/.well-known/agent-card.json` |
| Agent manifest | `_03_promo-site/.well-known/agent.json` |
| Agent skills | `_03_promo-site/.well-known/agent-skills/index.json` |
| OpenAPI spec | `_03_promo-site/openapi.json` |
| Canon CLI | `~/Developer/_control/search-authority/canon_cli.py` |
| GSC toolkit | `~/Developer/active/SigRank-repos/scripts/gsc/gsc.mjs` |
| GSC SA key | `~/.config/sigrank/gsc-sa.json` |
| Keyword CSV | `_workspace/keywords/mos2es-keywords.csv` |
| Content brief | `_workspace/content-briefs/ai-evaluation.md` |
| Schema matrix | `ECOSYSTEM_SCHEMA_MATRIX.md` |

### Commit history (this session chain)

```
862dfc2 Consolidate 24 concept pages into 3, align metric formulas with canon
61e418b Strip .html from all internal links — clean URLs site-wide
a814a5f Subpage consistency pass: fix broken links, clean nav/footer, update stale pricing
6583879 Rename Killer Experiment to Baseline Assessment, clean up nav/footer consistency
c350c26 Update nav + messaging across promo-site to match homepage redesign
da63347 Redesign homepage to 6 sections, apply Upsilon type system, reframe commercial offer
ad72e2d Move upsilon-logo-concepts.html out of live promo-site to design reference
c743b0c Update ECOSYSTEM_SCHEMA_MATRIX.md — all 6 domains PASS
8cdd09a Complete schema rollout for mos2es.org with moses namespace + canon fields
a30b667 Switch CF dashboard to zone-level queries with per-zone breakdown
d401de9 Expand CF dashboard to cover all zones, fix token handling
36ca637 Fix double-counting: only fire server-side beacon for bots
b74e19b Add server-side bot detection to capture crawlers that don't run JS
2374695 Add Cloudflare-powered analytics dashboard
0746846 Upgrade analytics dashboard with tabbed interface and new visualizations
5b415f6 Apply Upsilon Commercial Site Patch V3
05d9f4c Consolidate KV operations to stay within free tier limits
13d21c8 Add analytics worker routes for mos2es.com
2ef3c5d Add crawl-to-referral ratio tracking for all 3 sites
6c7ff72 Add markdown content negotiation + enhanced agent tracking
```
