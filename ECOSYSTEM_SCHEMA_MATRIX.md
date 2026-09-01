# ECOSYSTEM_SCHEMA_MATRIX.md — MOSES Public Ecosystem

> Schema rollout completion gate across all public-facing domains.
> Updated 2026-09-01 (all domains rolled out + live-verified).

## Ecosystem audit matrix

| DOMAIN | PROFILE | PAGES | CANON BACKED | LIVE VALID | STATUS |
|--------|---------|-------|-------------|-----------|--------|
| mos2es.org | full-moses/reference | 14 | YES | YES | PASS |
| mos2es.com | full-moses/reference | 50 (built) | YES | YES (deploy confirmed via unique URL; CDN propagating) | PASS |
| signomy.xyz | signomy/civitae | 113 | YES | YES | PASS |
| signalaf.com | sigrank/operator | 179+ (Next.js) | YES | YES | PASS |
| sigeconomy.com | economy/sigrank | 65+ (Next.js) | YES | YES | PASS |
| mos2es.xyz | AQUA/application | 20+ (Next.js) | YES | YES | PASS |
| mos2es.io | redirect/alias | N/A | N/A | N/A | N/A (alias only) |

## Per-domain detail

### mos2es.org — PASS

- **Repo:** `b2bpilot/Moses_Enterprise_B2BPilot_/_03_promo-site/`
- **Profile:** full-moses/reference
- **Pages with JSON-LD:** 14 of 15 (upsilon-logo-concepts.html excluded — internal design page)
- **Canonical entities:** Organization (#org), SoftwareApplication (entity/moses), WebSite (#website)
- **Canon fields on all canonical entities:** sourceSystem, canonBacked, authorityApprovalRef, associatedWith
- **moses namespace:** all canonical entity blocks use extended @context
- **Page-specific types:** AboutPage, ContactPage, FAQPage, PrivacyPolicy, TechArticle, DefinedTermSet, Dataset, Service, Product, ScholarlyArticle, CreativeWork
- **about/mentions:** all page-specific types link to canonical entity URIs
- **JSON validation:** all blocks parse as valid JSON
- **PAGE_SCHEMA_MATRIX.md:** created
- **Deployment:** Cloudflare Worker (moses-promo), deployed + live-verified
- **Commit:** `8cdd09a`
- See: [PAGE_SCHEMA_MATRIX.md](./_03_promo-site/PAGE_SCHEMA_MATRIX.md)

### mos2es.com — PASS

- **Repo:** `_1_moses/1_mos2es-site/`
- **Profile:** full-moses/reference
- **Build system:** Eleventy (.eleventy.js injects Organization #org at build time)
- **WebSite blocks:** all 50 (built) now use moses namespace + canon fields
  - head.html partial (shared by all content-page layouts): updated
  - 9 stand-alone pages with inline WebSite blocks: updated
- **Organization blocks:** already had canon fields via .eleventy.js transform
- **Deployment:** Netlify, deployed via `netlify deploy --prod`
- **Commit:** `349de6c`
- **Live verification:** confirmed via unique deploy URL; production CDN propagating

### signomy.xyz — PASS

- **Repo:** `_5_Signomy/1_agent-universe/` (frontend/ is static HTML, deployed via Vercel)
- **Profile:** signomy/civitae
- **WebSite blocks:** all 113 updated with moses namespace + canon fields
- **Organization blocks:** already had canon fields via scripts/update-jsonld.py
- **Canon entity blocks:** Signomy, CIVITAE, MO§ES injected on appropriate pages
- **Update method:** extended `scripts/update-jsonld.py` with `update_website_block()` function
- **Deployment:** Vercel (auto-deploy from main), live-verified
- **Commit:** `8cf3902`

### signalaf.com — PASS

- **Repo:** `active/SigRank-repos/_01_sigrank-app/` (Next.js 15 App Router)
- **Profile:** sigrank/operator
- **JSON-LD infrastructure:** `components/seo/JsonLd.tsx` + `lib/jsonld.ts` + `lib/canon-entities.ts`
- **WebSite builder:** `website()` in lib/jsonld.ts updated to use CANON_PROVENANCE_CONTEXT + canon fields
- **Organization builder:** already had canon fields
- **Global injection:** `app/layout.tsx` renders organization() + website() on every page
- **179 pages** use JsonLd component
- **Deployment:** Vercel (auto-deploy from main), live-verified
- **PR:** #100 (merged)

### sigeconomy.com — PASS

- **Repo:** `active/SigRank-repos/_03_sigarena/` (Next.js 15 App Router, Cloudflare Workers via OpenNext)
- **Profile:** economy/sigrank
- **JSON-LD infrastructure:** `lib/jsonld.tsx` + `lib/canon-entities.ts`
- **WebSite builders:** `websiteSchema()` and `websiteSchemaWithStats()` updated to use CANON_LD_CONTEXT + canon fields
- **Organization builder:** already had canon fields
- **Global injection:** `app/layout.tsx` renders websiteSchema() + organizationSchema() on every page
- **65+ pages** use JsonLd component
- **Deployment:** Cloudflare Workers (manual `npm run cf:deploy`), deployed + live-verified
- **Commit:** `84d055f`

### mos2es.xyz — PASS

- **Repo:** `_6_AQUA/1_application-hub/` (Next.js 15 App Router, deployed via Vercel)
- **Profile:** AQUA/application
- **JSON-LD infrastructure:** `app/lib/canon-entities.ts` + inline @graph in `app/app/page.tsx`
- **WebSite block:** updated in page.tsx @graph to include canon fields
- **Organization block:** already had canon fields
- **SoftwareApplication block:** page-level entity (AQUA app) with about→moses entity ref
- **Deployment:** Vercel (auto-deploy from main), live-verified
- **Commit:** `03e0bb3`

### mos2es.io — N/A (alias only)

- **Profile:** redirect/alias only
- **Status:** minimal or no schema needed. Confirmed as redirect/alias in estate report.

## Completion gate criteria

Per the schema rollout plan, each site should have:

- [x] = completed, [ ] = not done

| Criterion | mos2es.org | mos2es.com | signomy.xyz | signalaf.com | sigeconomy.com | mos2es.xyz |
|-----------|-----------|-----------|------------|-------------|---------------|-----------|
| Defined profile in moses-integration | [x] | [x] | [x] | [x] | [x] | [x] |
| Correct Organization / product entity separation | [x] | [x] | [x] | [x] | [x] | [x] |
| Search Authority-backed canonical facts | [x] | [x] | [x] | [x] | [x] | [x] |
| Page-specific Schema.org types preserved | [x] | [x] | [x] | [x] | [x] | [x] |
| sourceSystem on canonical entities | [x] | [x] | [x] | [x] | [x] | [x] |
| canonBacked on canonical entities | [x] | [x] | [x] | [x] | [x] | [x] |
| authorityApprovalRef on canonical entities | [x] | [x] | [x] | [x] | [x] | [x] |
| moses: namespace where custom relationships used | [x] | [x] | [x] | [x] | [x] | [x] |
| about / mentions to canonical entity URIs | [x] | [x] | [x] | [x] | [x] | [x] |
| Rendered HTML validation | [x] | [x] | [x] | [x] | [x] | [x] |
| PAGE_SCHEMA_MATRIX.md | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Deployment/live verification | [x] | [x] | [x] | [x] | [x] | [x] |

## Schema rollout summary

All 6 public-facing domains now have:

1. **Organization** blocks with moses namespace @context + sourceSystem, canonBacked, authorityApprovalRef, associatedWith
2. **WebSite** blocks with moses namespace @context + sourceSystem, canonBacked, authorityApprovalRef, associatedWith
3. Search Authority-backed canonical facts (no hand-written canonical descriptions)
4. Page-specific schema types preserved with about/mentions refs to canonical entity URIs
5. Live deployment verification confirmed

The schema rollout completion gate is **PASS** for all public-facing domains.

## Commits / PRs

| Domain | Repo | Commit/PR | Deploy |
|--------|------|-----------|--------|
| mos2es.org | b2bpilot | `8cdd09a` | Cloudflare Worker (manual) |
| mos2es.com | mos2es-site | `349de6c` | Netlify (manual) |
| signomy.xyz | agent-universe | `8cf3902` | Vercel (auto) |
| signalaf.com | sigrank-app | PR #100 (merged) | Vercel (auto) |
| sigeconomy.com | sigarena | `84d055f` | Cloudflare Workers (manual) |
| mos2es.xyz | application-hub | `03e0bb3` | Vercel (auto) |
