# INTERVENTION_SCHEMA.md

> Formal schema for an intervention record — a controlled change applied
> to an operator with a pre-declared target metric and follow-up window.

## Schema (JSON Schema draft-07)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "InterventionRecord",
  "type": "object",
  "required": ["intervention_id", "pilot_id", "operator_id", "catalog_id", "target_metric", "followup_days", "start_date", "authorized_by", "synthetic"],
  "properties": {
    "intervention_id": {
      "type": "string",
      "description": "Unique intervention identifier"
    },
    "pilot_id": {
      "type": "string",
      "description": "The pilot this intervention belongs to"
    },
    "operator_id": {
      "type": "string",
      "description": "The operator receiving the intervention"
    },
    "catalog_id": {
      "type": "string",
      "enum": ["CTX-001", "CTX-002", "CTX-003", "FRM-001", "FRM-002", "MOD-001", "AGT-001", "REV-001", "STD-001", "COA-001", "LRN-001", "STG-001"],
      "description": "Intervention catalog entry ID"
    },
    "catalog_name": {
      "type": "string",
      "description": "Human-readable catalog entry name"
    },
    "catalog_type": {
      "type": "string",
      "enum": ["workflow", "tooling", "guide", "human", "review", "standard", "coaching", "learning", "stage"],
      "description": "Intervention type"
    },
    "reason_pattern": {
      "type": "string",
      "description": "Pattern ID that prompted this intervention (e.g., P-BURN-01)"
    },
    "reason_finding_id": {
      "type": "string",
      "description": "Finding ID that prompted this intervention (if available)"
    },
    "target_metric": {
      "type": "string",
      "enum": ["leverage", "yield", "token_snr", "log_leverage", "construction"],
      "description": "Pre-declared target metric (locked before execution)"
    },
    "followup_days": {
      "type": "integer",
      "minimum": 1,
      "description": "Pre-declared follow-up window in days (locked before execution)"
    },
    "start_date": {
      "type": "string",
      "format": "date",
      "description": "Intervention start date"
    },
    "end_date": {
      "type": "string",
      "format": "date",
      "description": "Intervention end date (start_date + followup_days)"
    },
    "authorized_by": {
      "type": "string",
      "description": "Identity that authorized this intervention (required)"
    },
    "outcome": {
      "type": "string",
      "enum": ["SUCCESS", "PARTIAL", "NO_EFFECT", "NEGATIVE", "PENDING"],
      "description": "Declared outcome. PENDING until closed."
    },
    "closed_at": {
      "type": "string",
      "format": "date-time",
      "description": "When the intervention was closed with an outcome"
    },
    "closed_by": {
      "type": "string",
      "description": "Identity that closed the intervention"
    },
    "synthetic": {
      "type": "boolean",
      "description": "True if intervention is from synthetic/demo data"
    },
    "decision_use": {
      "type": "string",
      "enum": ["WORKFLOW_EXPERIMENTATION", "DEVELOPMENTAL"],
      "description": "Decision-use label (never PERSONNEL)"
    }
  }
}
```

## Relationship to existing implementation

| Schema field | Existing source | Status |
|---|---|---|
| `intervention_id` | `Intervention.intervention_id` | Existing |
| `pilot_id` | — | Genuinely new (no pilot binding) |
| `operator_id` | `Intervention.operator_id` | Existing |
| `catalog_id` | `Intervention.catalog_id` | Existing |
| `catalog_name` | `InterventionCatalogEntry.name` | Existing (on catalog entry) |
| `catalog_type` | `InterventionCatalogEntry.type` | Existing (on catalog entry) |
| `reason_pattern` | `Intervention.reason_pattern` | Existing |
| `reason_finding_id` | — | Genuinely new (no finding binding) |
| `target_metric` | `Intervention.target_metric` | Existing |
| `followup_days` | `Intervention.followup_days` | Existing |
| `start_date` | `Intervention.start_date` | Existing |
| `end_date` | Computed (start_date + followup_days) | Extension required (not stored) |
| `authorized_by` | Enforced in CLI/MCP layer, not stored on Intervention | Extension required |
| `outcome` | `Intervention.synthetic_outcome` (InterventionOutcome enum) | Existing |
| `closed_at` | — | Genuinely new |
| `closed_by` | — | Genuinely new |
| `synthetic` | `Intervention.synthetic` | Existing |
| `decision_use` | `decision_use_for_intervention()` → WORKFLOW_EXPERIMENTATION | Existing (governance helper) |

## Governance constraints

1. `target_metric` and `followup_days` MUST be declared before execution
   (locked at assignment time).
2. `authorized_by` is required — no intervention without authorization.
3. `outcome` must be one of SUCCESS/PARTIAL/NO_EFFECT/NEGATIVE. PENDING
   is the initial state before closure.
4. `decision_use` must never be PERSONNEL. Interventions are
   WORKFLOW_EXPERIMENTATION or DEVELOPMENTAL.
5. Negative outcomes (NO_EFFECT, NEGATIVE) are representable and
   reportable — they are not failures to hide.
