#!/usr/bin/env python3
"""
update-enterprise-jsonld.py — Transform inline JSON-LD in mos2es.org promo-site HTML.

Replaces canon-sensitive identity values with Search Authority-backed values
from master-canon-v1.0.0. Preserves commercial terminology and page-specific schema.

Canon-sensitive replacements:
  Organization #org: name "MO§ES™" → "Ello Cello LLC", add provenance
  SoftwareApplication: @id → canonical entity @id, add provenance

Everything else (WebSite, AboutPage, ContactPage, TechArticle, FAQPage,
BreadcrumbList, Service, Dataset, etc.) is preserved as-is.
"""

import copy
import json
import re
import sys
from pathlib import Path

# ─── Canon-backed values (from master-canon-v1.0.0, SHA fd305af) ───────────

CANON_LD_CONTEXT = {
    "@vocab": "https://schema.org/",
    "moses": "https://mos2es.com/ontology/0.1/",
    "sourceSystem": "moses:sourceSystem",
    "canonBacked": "moses:canonBacked",
    "authorityApprovalRef": "moses:authorityApprovalRef",
    "associatedWith": "moses:associatedWith",
}

CANON_ENTITY_IDS = {
    "ello_cello_llc": "https://mos2es.com/ontology/0.1/entity/ello_cello_llc",
    "moses": "https://mos2es.com/ontology/0.1/entity/moses",
    "deric_j_mchenry": "https://mos2es.com/ontology/0.1/entity/deric_j_mchenry",
}

# ─── Transform logic ────────────────────────────────────────────────────────

def transform_organization(node):
    """Replace canon-sensitive values in Organization #org."""
    if not isinstance(node, dict):
        return node
    if node.get("@type") != "Organization":
        return node
    if "mos2es.org" not in node.get("@id", ""):
        return node

    # Replace canon-sensitive values
    node["@context"] = CANON_LD_CONTEXT
    node["name"] = "Ello Cello LLC"
    node["sourceSystem"] = "search-authority"
    node["canonBacked"] = True
    node["authorityApprovalRef"] = "APPROVAL-2026-08-14-001 (ID-ELLO-001)"
    node["associatedWith"] = {"@id": CANON_ENTITY_IDS["moses"]}

    # Preserve: @id, url, description, founder, contactPoint, address, sameAs
    return node


def transform_software_application(node):
    """Replace canon-sensitive values in SoftwareApplication (MO§ES™ product)."""
    if not isinstance(node, dict):
        return node
    if node.get("@type") != "SoftwareApplication":
        return node
    if node.get("name") != "MO\u00a7ES\u2122":
        return node

    # Replace @id with canonical entity @id
    node["@id"] = CANON_ENTITY_IDS["moses"]
    node["@context"] = CANON_LD_CONTEXT
    node["sourceSystem"] = "search-authority"
    node["canonBacked"] = True
    node["authorityApprovalRef"] = "APPROVAL-2026-08-14-001 (ID-MOSES-001)"

    # Preserve: name, description, applicationCategory, operatingSystem,
    #           offers, publisher, url
    return node


def transform_jsonld(data):
    """Transform a parsed JSON-LD block (object or array)."""
    if isinstance(data, list):
        return [transform_jsonld(item) for item in data]
    if isinstance(data, dict):
        # Check if this is a container with @graph
        if "@graph" in data:
            data["@graph"] = [transform_jsonld(node) for node in data["@graph"]]
            return data

        # Transform based on @type
        if data.get("@type") == "Organization":
            return transform_organization(data)
        if data.get("@type") == "SoftwareApplication":
            return transform_software_application(data)
        return data
    return data


def process_html_file(filepath):
    """Process a single HTML file, transforming inline JSON-LD blocks."""
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    # Find all JSON-LD blocks
    pattern = r'(<script type="application/ld\+json">)(.*?)(</script>)'
    matches = list(re.finditer(pattern, html, re.DOTALL))
    if not matches:
        return False

    modified = False
    for match in matches:
        prefix, json_str, suffix = match.group(1), match.group(2), match.group(3)
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            continue

        original = copy.deepcopy(data)
        transformed = transform_jsonld(data)
        if transformed != original:
            new_json = json.dumps(transformed, indent=2, ensure_ascii=False)
            new_block = f"{prefix}\n{new_json}\n  {suffix}"
            html = html.replace(match.group(0), new_block)
            modified = True

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

    return modified


def main():
    promo_dir = Path(__file__).parent.parent / "_03_promo-site"
    if not promo_dir.exists():
        print(f"ERROR: promo-site directory not found: {promo_dir}")
        sys.exit(1)

    html_files = sorted(promo_dir.glob("*.html"))
    print(f"Found {len(html_files)} HTML files in {promo_dir}")

    modified_count = 0
    for filepath in html_files:
        modified = process_html_file(filepath)
        status = "MODIFIED" if modified else "unchanged"
        print(f"  {filepath.name}: {status}")
        if modified:
            modified_count += 1

    print(f"\n{modified_count} files modified.")


if __name__ == "__main__":
    main()
