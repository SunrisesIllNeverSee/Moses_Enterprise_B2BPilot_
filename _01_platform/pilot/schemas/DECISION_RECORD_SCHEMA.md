# DECISION_RECORD_SCHEMA.md

> Formal schema for a decision record — the immutable terminal decision
> of an Upsilon Enterprise Pilot.

## Schema (JSON Schema draft-07)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DecisionRecord",
  "type": "object",
  "required": ["decision_id", "pilot_id", "closure_outcome", "rationale", "evidence_cited", "success_criteria_comparison", "decided_at", "decided_by"],
  "properties": {
    "decision_id": {
      "type": "string",
      "description": "Unique decision record identifier"
    },
    "pilot_id": {
      "type": "string",
      "description": "The pilot this decision terminates"
    },
    "closure_outcome": {
      "type": "string",
      "enum": ["STOP", "EXTEND", "EXPAND", "DEPLOY"],
      "description": "The terminal closure outcome"
    },
    "rationale": {
      "type": "string",
      "description": "Why this outcome was selected (evidence-based)"
    },
    "evidence_cited": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "evidence_type": {"type": "string", "enum": ["finding", "verification", "readout_section", "gate_record", "baseline_metric"]},
          "evidence_id": {"type": "string"},
          "description": {"type": "string"}
        }
      },
      "description": "Specific evidence artifacts cited in the rationale"
    },
    "success_criteria_comparison": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["criterion_id", "metric", "threshold", "direction", "measured_value", "result"],
        "properties": {
          "criterion_id": {"type": "string"},
          "metric": {"type": "string"},
          "threshold": {"type": "number"},
          "direction": {"type": "string", "enum": ["above", "below"]},
          "measured_value": {"type": ["number", "null"]},
          "result": {"type": "string", "enum": ["MET", "MISSED", "PARTIAL"]},
          "notes": {"type": "string"}
        }
      },
      "description": "Per-criterion comparison of measured vs locked success criteria"
    },
    "gate_3_record_id": {
      "type": "string",
      "description": "ID of the Gate 3 record that produced this decision"
    },
    "conditions": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Conditions attached to the decision (if any)"
    },
    "extend_plan": {
      "type": "object",
      "description": "Required if closure_outcome is EXTEND",
      "required": ["explicit_reason", "missing_evidence", "new_evidence_requirement", "extension_period_days", "new_closure_date"],
      "properties": {
        "explicit_reason": {"type": "string"},
        "missing_evidence": {"type": "string"},
        "new_evidence_requirement": {"type": "string"},
        "extension_period_days": {"type": "integer", "minimum": 1},
        "new_closure_date": {"type": "string", "format": "date"}
      }
    },
    "expand_plan": {
      "type": "object",
      "description": "Required if closure_outcome is EXPAND",
      "properties": {
        "new_population": {"type": "string"},
        "new_duration_days": {"type": "integer"},
        "new_eval_families": {"type": "array", "items": {"type": "string"}},
        "new_pilot_id": {"type": "string"}
      }
    },
    "deploy_plan": {
      "type": "object",
      "description": "Required if closure_outcome is DEPLOY",
      "properties": {
        "production_transition_checklist": {"type": "array", "items": {"type": "string"}},
        "monitoring_plan": {"type": "string"},
        "rollback_plan": {"type": "string"}
      }
    },
    "stop_lessons": {
      "type": "object",
      "description": "Required if closure_outcome is STOP",
      "properties": {
        "findings_summary": {"type": "string"},
        "lessons_learned": {"type": "array", "items": {"type": "string"}},
        "root_cause_analysis": {"type": "string"},
        "recommendation": {"type": "string"}
      }
    },
    "decided_at": {
      "type": "string",
      "format": "date-time",
      "description": "When the decision was made"
    },
    "decided_by": {
      "type": "string",
      "description": "Identity that made the decision (decision authority)"
    },
    "immutable": {
      "type": "boolean",
      "description": "Must be true. Decision records are immutable once created.",
      "const": true
    }
  }
}
```

## Outcome-specific requirements

| closure_outcome | Required additional field |
|---|---|
| `STOP` | `stop_lessons` (findings_summary, lessons_learned, root_cause_analysis, recommendation) |
| `EXTEND` | `extend_plan` (ALL five: explicit_reason, missing_evidence, new_evidence_requirement, extension_period_days, new_closure_date) |
| `EXPAND` | `expand_plan` (new_population, new_duration, new_eval_families, new_pilot_id) |
| `DEPLOY` | `deploy_plan` (production_transition_checklist, monitoring_plan, rollback_plan) |

## Immutability

Decision records are immutable. The `immutable` field MUST be `true`.
If a decision needs to be changed, a new decision record must be created
that supersedes the previous one, with a reference to the superseded
record.

## Relationship to existing implementation

| Schema field | Existing source | Status |
|---|---|---|
| `decision_id` | — | Genuinely new |
| `pilot_id` | — | Genuinely new |
| `closure_outcome` | — | Genuinely new |
| `rationale` | — | Genuinely new |
| `evidence_cited` | — | Genuinely new |
| `success_criteria_comparison` | — | Genuinely new (no success criteria to compare) |
| `gate_3_record_id` | — | Genuinely new |
| `conditions` | — | Genuinely new |
| `extend_plan` | — | Genuinely new |
| `expand_plan` | — | Genuinely new |
| `deploy_plan` | — | Genuinely new |
| `stop_lessons` | — | Genuinely new |
| `decided_at/by` | — | Genuinely new |
| `immutable` | — | Genuinely new |

> **This entire schema is genuinely new.** No decision record exists in
> the current implementation. This is the single largest gap — the
> platform has no terminal decision capability.
