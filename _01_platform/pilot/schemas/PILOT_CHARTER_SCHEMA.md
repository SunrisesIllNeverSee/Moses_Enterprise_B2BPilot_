# PILOT_CHARTER_SCHEMA.md

> Formal schema for the Pilot Charter — the immutable definition record.
> See `governance/PILOT_CHARTER.md` for the narrative specification.

## Schema (JSON Schema draft-07)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PilotCharter",
  "type": "object",
  "required": ["pilot_id", "enterprise", "population", "duration", "objectives", "success_criteria", "governance", "gate_1_result"],
  "properties": {
    "pilot_id": {
      "type": "string",
      "description": "Unique pilot identifier (e.g., ACME-001)",
      "pattern": "^[A-Z]+-\\d{3}$"
    },
    "identity": {
      "type": "object",
      "required": ["name", "created_at", "created_by", "authorized_by"],
      "properties": {
        "name": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "created_by": {"type": "string"},
        "authorized_by": {"type": "string"}
      }
    },
    "enterprise": {
      "type": "object",
      "required": ["tenant_id", "enterprise_name"],
      "properties": {
        "tenant_id": {"type": "string"},
        "enterprise_name": {"type": "string"}
      }
    },
    "population": {
      "type": "object",
      "required": ["cohort_id", "operator_count"],
      "properties": {
        "cohort_id": {"type": "string"},
        "operator_ids": {"type": "array", "items": {"type": "string"}},
        "operator_count": {"type": "integer", "minimum": 1},
        "teams": {"type": "array", "items": {"type": "string"}},
        "selection_criteria": {"type": "string"}
      }
    },
    "duration": {
      "type": "object",
      "required": ["window_start", "window_end", "window_days"],
      "properties": {
        "window_start": {"type": "string", "format": "date"},
        "window_end": {"type": "string", "format": "date"},
        "window_days": {"type": "integer", "minimum": 1}
      }
    },
    "scope": {
      "type": "object",
      "properties": {
        "eval_families": {"type": "array", "items": {"type": "string"}},
        "commercial_pilot_id": {"type": "string"},
        "deployment_level": {"type": "integer", "enum": [1, 2, 3]}
      }
    },
    "objectives": {
      "type": "object",
      "required": ["pilot_question"],
      "properties": {
        "pilot_question": {"type": "string"},
        "best_buyer": {"type": "string"}
      }
    },
    "success_criteria": {
      "type": "object",
      "required": ["criteria", "locked_at", "locked_by"],
      "properties": {
        "criteria": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["criterion_id", "metric", "threshold", "direction", "aggregation", "rationale", "closure_mapping"],
            "properties": {
              "criterion_id": {"type": "string"},
              "metric": {"type": "string"},
              "threshold": {"type": "number"},
              "direction": {"type": "string", "enum": ["above", "below"]},
              "aggregation": {"type": "string", "enum": ["cohort_median", "cohort_p10", "cohort_p90", "target_group_median", "target_group_delta"]},
              "rationale": {"type": "string"},
              "closure_mapping": {"type": "array", "items": {"type": "string", "enum": ["STOP", "EXTEND", "EXPAND", "DEPLOY"]}}
            }
          }
        },
        "locked_at": {"type": "string", "format": "date-time"},
        "locked_by": {"type": "string"}
      }
    },
    "governance": {
      "type": "object",
      "required": ["decision_use_default", "privacy_class", "synthetic"],
      "properties": {
        "decision_use_default": {"type": "string", "enum": ["DEVELOPMENTAL", "WORKFLOW_EXPERIMENTATION", "ASSOCIATION"]},
        "privacy_class": {"type": "string"},
        "synthetic": {"type": "boolean"},
        "purpose_id": {"type": "string"},
        "consent_model": {"type": "string", "enum": ["opt_in", "opt_out", "mandated"]}
      }
    },
    "config_reference": {
      "type": "object",
      "properties": {
        "config_json_path": {"type": "string"},
        "metric_registry_version": {"type": "string"},
        "reference_field_version": {"type": "string"}
      }
    },
    "gate_1_result": {
      "type": "object",
      "required": ["outcome", "evaluated_at", "evaluated_by"],
      "properties": {
        "outcome": {"type": "string", "enum": ["LAUNCH", "LAUNCH_WITH_CONDITIONS", "DEFER", "DECLINE"]},
        "conditions": {"type": "array", "items": {"type": "string"}},
        "evaluated_at": {"type": "string", "format": "date-time"},
        "evaluated_by": {"type": "string"}
      }
    },
    "amendments": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "amendment_id": {"type": "string"},
          "rationale": {"type": "string"},
          "amended_at": {"type": "string", "format": "date-time"},
          "amended_by": {"type": "string"},
          "gate_1_reevaluated": {"type": "boolean"}
        }
      }
    }
  }
}
```

## Relationship to existing implementation

| Schema field | Existing source | Status |
|---|---|---|
| `pilot_id` | — | Genuinely new |
| `identity.name` | `PilotConfiguration.name` | Reusable |
| `identity.created_at/by` | `PilotConfiguration.created_at/by` | Reusable |
| `identity.authorized_by` | `GovernanceConfig.authorized_by` | Reusable |
| `enterprise.tenant_id` | `CohortConfig.tenant_id` | Reusable |
| `enterprise.enterprise_name` | — | Extension required |
| `population.*` | `Cohort` / `CohortConfig` | Reusable |
| `population.selection_criteria` | — | Genuinely new |
| `duration.*` | `Cohort` / `CohortConfig` | Reusable |
| `scope.eval_families` | `PilotConfiguration.eval_families` | Reusable |
| `scope.commercial_pilot_id` | `PilotConfiguration.commercial_pilot_id` | Reusable |
| `scope.deployment_level` | `PilotConfiguration.deployment_level` | Reusable |
| `objectives.pilot_question` | `CommercialPilot.question` (template only) | Extension required |
| `objectives.best_buyer` | `CommercialPilot.best_buyer` (template only) | Extension required |
| `success_criteria.*` | — | Genuinely new |
| `governance.*` | `GovernanceConfig` | Reusable |
| `config_reference.*` | `PilotConfiguration.to_json()` | Reusable |
| `gate_1_result.*` | — | Genuinely new |
| `amendments.*` | — | Genuinely new |
