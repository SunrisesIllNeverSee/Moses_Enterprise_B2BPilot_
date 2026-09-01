# ECOSYSTEM_SCHEMA_MATRIX.md — MOSES Public Ecosystem

> Schema rollout completion gate across all public-facing domains.
> Generated 2026-09-01.

## Ecosystem audit matrix

| DOMAIN | PROFILE | PAGES | CANON BACKED | LIVE VALID | STATUS |
|--------|---------|-------|-------------|-----------|--------|
| mos2es.org | full-moses/reference | 14 | YES | pending deploy | PASS (local) |
| mos2es.com | full-moses/reference | 13 with JSON-LD (of 74) | PARTIAL | unknown | NEEDS WORK |
| signomy.xyz | signomy/civitae | 2 | NO | unknown | NO SCHEMA |
| signalaf.com | sigrank/operator | 0 static (Next.js app) | N/A | unknown | NO STATIC SCHEMA |
| sigeconomy.com | economy/sigrank | repo not found | N/A | N/A | NOT FOUND |
| mos2es.xyz | AQUA/application | repo not found | N/A | N/A | NOT FOUND |
| mos2es.io | redirect/alias | N/A | N/A | N/A | N/A (alias only) |

## Per-domain detail

### mos2es.org — PASS (local)

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
- **Deployment verification:** pending deploy
- See: [PAGE_SCHEMA_MATRIX.md](./_03_promo-site/PAGE_SCHEMA_MATRIX.md)

### mos2es.com — NEEDS WORK

- **Repo:** `_1_moses/1_mos2es-site/`
- **Profile:** full-moses/reference
- **Files with JSON-LD:** 13 of 74 HTML files
- **Total JSON-LD blocks:** 37
- **moses namespace blocks:** 7 of 37
- **Blocks with sourceSystem/canonBacked/authorityApprovalRef:** 2 of 37
- **Blocks with associatedWith:** 0 of 37
- **WebSite blocks:** all use plain `https://schema.org` context, no canon fields
- **Build system:** Eleventy (.eleventy.js injects Organization #org at build time)
- **Issues:**
  1. WebSite blocks need moses namespace + canon fields
  2. Most page-specific blocks (WebPage, Article, VideoObject, Dataset, ProfilePage) use plain context with no about/mentions references
  3. associatedWith unused across all blocks
  4. 61 HTML files have no JSON-LD at all
- **Recommendation:** apply same fix pattern as mos2es.org in a separate PR

### signomy.xyz — NO SCHEMA

- **Repo:** `_5_Signomy/2_mos2es_signomy/`
- **Profile:** signomy/civitae
- **HTML files:** 2 (index.html, architecture.html)
- **JSON-LD blocks:** 0
- **Status:** no schema markup exists. Needs schema added from scratch.
- **Recommendation:** define signomy profile in moses-integration, then add JSON-LD blocks

### signalaf.com — NO STATIC SCHEMA

- **Repo:** `active/SigRank-repos/_01_sigrank-app/` (Next.js app)
- **Profile:** sigrank/operator
- **Static HTML with JSON-LD:** 0
- **Runtime JSON-LD:** `components/seo/JsonLd.tsx` component exists, `lib/jsonld.ts` has schema definitions (sourceSystem, canonBacked, authorityApprovalRef)
- **Status:** Next.js app has JSON-LD infrastructure but it is not wired into static HTML pages
- **Recommendation:** wire JsonLd component into page routes, verify rendered output

### sigeconomy.com — NOT FOUND

- **Repo:** not found in `~/Developer/`
- **Profile:** economy/sigrank
- **Status:** no local repository. May be deployed from a different location or not yet built.
- **Recommendation:** locate the deployment source or confirm if this domain is redirect-only

### mos2es.xyz — NOT FOUND

- **Repo:** not found in `~/Developer/`
- **Profile:** AQUA/application
- **Status:** no local repository. May be deployed from a different location or not yet built.
- **Recommendation:** locate the deployment source or confirm if this domain is redirect-only

### mos2es.io — N/A (alias only)

- **Profile:** redirect/alias only
- **Status:** likely minimal or no schema needed. Confirmed as redirect/alias in estate report.

## Completion gate criteria

Per the schema rollout plan, each site should have:

- [x] = completed, [ ] = not done

| Criterion | mos2es.org | mos2es.com | signomy.xyz | signalaf.com |
|-----------|-----------|-----------|------------|-------------|
| Defined profile in moses-integration | [x] | [x] | [ ] | [ ] |
| Correct Organization / product entity separation | [x] | [ ] | [ ] | [ ] |
| Search Authority-backed canonical facts | [x] | [ ] | [ ] | [ ] |
| Page-specific Schema.org types preserved | [x] | [x] | [ ] | [ ] |
| sourceSystem on canonical entities | [x] | [ ] | [ ] | [ ] |
| canonBacked on canonical entities | [x] | [ ] | [ ] | [ ] |
| authorityApprovalRef on canonical entities | [x] | [ ] | [ ] | [ ] |
| moses: namespace where custom relationships used | [x] | [ ] | [ ] | [ ] |
| about / mentions to canonical entity URIs | [x] | [ ] | [ ] | [ ] |
| Rendered HTML validation | [x] | [ ] | [ ] | [ ] |
| PAGE_SCHEMA_MATRIX.md | [x] | [ ] | [ ] | [ ] |
| Deployment/live verification | [ ] | [ ] | [ ] | [ ] |

## Recommended next steps

1. **mos2es.com:** Apply the same WebSite/canon-field fix pattern as mos2es.org.
   This is the highest-impact next step since the site already has 37 JSON-LD
   blocks that mostly need canon field upgrades.

2. **signomy.xyz:** Define the signomy/civitae profile in moses-integration, then
   add JSON-LD blocks to index.html and architecture.html from scratch.

3. **signalaf.com:** Wire the existing `JsonLd.tsx` component into the Next.js
   app's page routes and verify rendered HTML output.

4. **sigeconomy.com / mos2es.xyz:** Locate deployment sources or confirm
   redirect-only status.

5. **Deployment verification:** After deploying mos2es.org, verify live JSON-LD
   using Google's Rich Results Test or Schema.org validator.
