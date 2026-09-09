#!/usr/bin/env python3
"""
add-canon-provenance.py — Add canon-backed provenance fields to mos2es.org pages.

Adds sourceSystem, canonBacked, and authorityApprovalRef to the
SoftwareApplication JSON-LD block on pages that are missing them.

Also updates the SoftwareApplication @id from the local #software id
to the canonical entity id (https://mos2es.com/ontology/0.1/entity/moses).

Usage:
    python3 scripts/add-canon-provenance.py [--dry-run]
"""

import json
import re
import sys
from pathlib import Path

PROMO_SITE = Path(__file__).resolve().parent.parent / "_03_promo-site"

CANON_ENTITY_ID = "https://mos2es.com/ontology/0.1/entity/moses"
CANON_FIELDS = {
    "sourceSystem": "search-authority",
    "canonBacked": True,
    "authorityApprovalRef": "APPROVAL-2026-08-14-001 (ID-MOSES-001)",
}

DRY_RUN = "--dry-run" in sys.argv


def process_file(filepath):
    """Add canon provenance fields to SoftwareApplication blocks."""
    content = filepath.read_text(encoding="utf-8")
    
    # Skip if already has canonBacked
    if "canonBacked" in content:
        return False, "already has canonBacked"
    
    # Find JSON-LD blocks
    pattern = r'(<script[^>]*type="application/ld\+json"[^>]*>)(.*?)(</script>)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return False, "no JSON-LD block found"
    
    json_str = match.group(2)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return False, "JSON parse error"
    
    entities = data if isinstance(data, list) else [data]
    modified = False
    
    for ent in entities:
        if not isinstance(ent, dict):
            continue
        if ent.get("@type") == "SoftwareApplication":
            # Update @id to canonical entity id
            old_id = ent.get("@id", "")
            if old_id == "https://mos2es.org/#software":
                ent["@id"] = CANON_ENTITY_ID
                modified = True
            elif old_id != CANON_ENTITY_ID:
                # Unexpected @id, skip
                continue
            
            # Add canon fields
            for key, val in CANON_FIELDS.items():
                if key not in ent:
                    ent[key] = val
                    modified = True
    
    if not modified:
        return False, "no SoftwareApplication block to update"
    
    # Re-serialize
    new_json = json.dumps(data, indent=2, ensure_ascii=False)
    new_content = content[:match.start(2)] + new_json + content[match.end(2):]
    
    if DRY_RUN:
        print(f"  [DRY RUN] Would update: {filepath.name}")
    else:
        filepath.write_text(new_content, encoding="utf-8")
        print(f"  Updated: {filepath.name}")
    
    return True, "updated"


def main():
    print(f"{'DRY RUN: ' if DRY_RUN else ''}Adding canon provenance to mos2es.org pages")
    print(f"Site: {PROMO_SITE}")
    print()
    
    html_files = sorted(PROMO_SITE.rglob("*.html"))
    updated = 0
    skipped = 0
    errors = 0
    
    for f in html_files:
        rel = f.relative_to(PROMO_SITE)
        try:
            changed, msg = process_file(f)
            if changed:
                updated += 1
            else:
                if "already has canonBacked" in msg:
                    skipped += 1
                elif "no SoftwareApplication" in msg:
                    skipped += 1
                else:
                    print(f"  SKIP: {rel} — {msg}")
                    skipped += 1
        except Exception as e:
            print(f"  ERROR: {rel} — {e}")
            errors += 1
    
    print(f"\nResults: {updated} updated, {skipped} skipped, {errors} errors")


if __name__ == "__main__":
    main()
