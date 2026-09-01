# PAGE_SCHEMA_MATRIX.md — mos2es.org

> Schema rollout completion gate for the mos2es.org public-facing site.
> Generated 2026-09-01. All JSON-LD blocks validated.

## Canonical entities

These entities are canon-backed, sourced from Search Authority, and appear
across pages with consistent `@id` references.

| Entity | @type | @id | sourceSystem | canonBacked | authorityApprovalRef |
|--------|-------|-----|-------------|-------------|---------------------|
| Ello Cello LLC | Organization | `https://mos2es.org/#org` | search-authority | true | APPROVAL-2026-08-14-001 (ID-ELLO-001) |
| MOSES (application) | SoftwareApplication | `https://mos2es.com/ontology/0.1/entity/moses` | search-authority | true | APPROVAL-2026-08-14-001 (ID-MOSES-001) |
| mos2es.org site | WebSite | `https://mos2es.org/#website` | search-authority | true | APPROVAL-2026-08-14-001 (ID-ELLO-001) |

### Entity relationships

```
Organization (#org)
  ├── associatedWith → SoftwareApplication (entity/moses)
  ├── founder → Person (ORCID 0009-0002-9904-5390)
  └── owns → WebSite (enterprise.mos2es.org, mcp.mos2es.org, signalaf.com, signomy.xyz, sigeconomy.com)

SoftwareApplication (entity/moses)
  ├── publisher → Organization (#org)
  └── associatedWith → Organization (#org)

WebSite (#website)
  ├── publisher → Organization (#org)
  └── associatedWith → [Organization (#org), SoftwareApplication (entity/moses)]
```

## moses namespace context

All canonical entity blocks use the extended `@context`:

```json
{
  "@vocab": "https://schema.org/",
  "moses": "https://mos2es.com/ontology/0.1/",
  "sourceSystem": "moses:sourceSystem",
  "canonBacked": "moses:canonBacked",
  "authorityApprovalRef": "moses:authorityApprovalRef",
  "associatedWith": "moses:associatedWith"
}
```

Page-specific types (AboutPage, ContactPage, FAQPage, etc.) use plain
`"https://schema.org"` context. They are local page schema, not canonical
entities. They link to canonical entities via `about`, `mentions`,
`mainEntity`, `provider`, `publisher`, `brand`, or `creator` references.

BreadcrumbList blocks use plain context and carry no canon fields (navigation
only).

## Per-page schema matrix

| Page | Canonical entities | Page-specific type | Canon-backed | about/mentions ref | Breadcrumb | Valid JSON |
|------|-------------------|-------------------|-------------|-------------------|------------|------------|
| index.html | Organization, WebSite, SoftwareApplication | — | YES | — | — | YES |
| about.html | Organization, WebSite | AboutPage | YES | mainEntity→#org | YES | YES |
| product.html | Organization, WebSite, SoftwareApplication | Service | YES | about→entity/moses | YES | YES |
| pilot.html | Organization, WebSite | — | YES | — | YES | YES |
| pilot-readout.html | Organization, WebSite | Dataset | YES | about→entity/moses | YES | YES |
| methodology.html | Organization, WebSite | DefinedTermSet | YES | about→entity/moses | YES | YES |
| demo.html | Organization, WebSite, SoftwareApplication | — | YES | — | YES | YES |
| research.html | Organization, WebSite | ScholarlyArticle, CreativeWork | YES | mentions→#org | YES | YES |
| contact.html | Organization, WebSite | ContactPage | YES | mainEntity→#org | YES | YES |
| docs.html | Organization, WebSite | TechArticle | YES | about→entity/moses | YES | YES |
| faq.html | Organization, WebSite | FAQPage | YES | mentions→entity/moses | YES | YES |
| privacy.html | Organization, WebSite | PrivacyPolicy | YES | about→#org | YES | YES |
| commercial-offer.html | Organization, WebSite | Product x3 | YES | about→entity/moses | YES | YES |
| killer-experiment.html | Organization, WebSite | Product | YES | about→entity/moses | YES | YES |
| upsilon-logo-concepts.html | — | — | — | — | — | — |

## Completion checklist

- [x] Defined profile in moses-integration (full-moses/reference)
- [x] Correct Organization / SoftwareApplication entity separation
- [x] Search Authority-backed canonical facts (sourceSystem, canonBacked)
- [x] Page-specific Schema.org types preserved
- [x] `sourceSystem` on all canonical entities
- [x] `canonBacked` on all canonical entities
- [x] `authorityApprovalRef` on all canonical entities
- [x] `moses:` namespace where custom relationships are used
- [x] `about` / `mentions` pointing to canonical entity URIs on page-specific types
- [x] Rendered HTML validation (all JSON-LD blocks parse as valid JSON)
- [x] `PAGE_SCHEMA_MATRIX.md` created
- [ ] Deployment/live verification (pending deploy)

## Notes

- `upsilon-logo-concepts.html` is an internal design page with no JSON-LD. Not
  a public-facing content page. Excluded from schema rollout.
- `BreadcrumbList` blocks are navigation aids, not canonical entities. They use
  plain context and carry no canon fields by design.
- The `CreativeWork` block on `research.html` retains a string `about` field
  ("AI governance enforcement architecture") for the patent description and
  adds `mentions` → `#org` for the canonical entity link.
- The `ContactPage` block embeds a full Organization object in `mainEntity`
  rather than a reference. This is pre-existing and functionally correct, though
  a reference (`{"@id": "https://mos2es.org/#org"}`) would be cleaner.
