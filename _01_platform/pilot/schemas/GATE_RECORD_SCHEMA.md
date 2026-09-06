# GATE_RECORD_SCHEMA.md

> Formal schema for a gate record — the outcome of evaluating a pilot-level
> decision gate (Gate 1, Gate 2, or Gate 3).

## Schema (JSON Schema draft-07)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GateRecord",
  "type": "object",
  "required": ["gate_id", "pilot_id", "gate_type", "outcome", "evaluated_at", "evaluated_by"],
  "properties": {
    "gate_id": {
      "type": "string",
      "description": "Unique gate record identifier"
    },
    "pilot_id": {
      "type": "string",
      "description": "The pilot this gate belongs to"
    },
    "gate_type": {
      "type": "string",
      "enum": ["LAUNCH_READINESS", "PILOT_HEALTH", "CLOSURE_SCALE"],
      "description": "Gate 1, Gate 2, or Gate 3"
    },
    "outcome": {
      "type": "string",
      "description": "Gate outcome (enum depends on gate_type)",
      "_gate_1_enum": ["LAUNCH", "LAUNCH_WITH_CONDITIONS", "DEFER", "DECLINE"],
      "_gate_2_enum": ["CONTINUE", "ADJUST", "ESCALATE", "TERMINATE"],
      "_gate_3_enum": ["STOP", "EXTEND", "EXPAND", "DEPLOY"]
    },
    "conditions": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Conditions if LAUNCH_WITH_CONDITIONS or ADJUST"
    },
    "criteria_evaluation": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "criterion_id": {"type": "string"},
          "result": {"type": "string", "enum": ["MET", "MISSED", "PARTIAL"]},
          "measured_value": {"type": ["number", "null"]},
          "threshold": {"type": "number"},
          "direction": {"type": "string", "enum": ["above", "below"]}
        }
      },
      "description": "Per-criterion evaluation (Gate 3 only)"
    },
    "extend_requirements": {
      "type": "object",
      "description": "Required if outcome is EXTEND (Gate 3)",
      "required": ["explicit_reason", "missing_evidence", "new_evidence_requirement", "extension_period_days", "new_closure_date"],
      "properties": {
        "explicit_reason": {"type": "string"},
        "missing_evidence": {"type": "string"},
        "new_evidence_requirement": {"type": "string"},
        "extension_period_days": {"type": "integer", "minimum": 1},
        "new_closure_date": {"type": "string", "format": "date"}
      }
    },
    "rationale": {
      "type": "string",
      "description": "Why this outcome was selected"
    },
    "evidence_cited": {
      "type": "array",
      "items": {"type": "string"},
      "description": "IDs of evidence artifacts cited (finding IDs, verification IDs, readout sections)"
    },
    "evaluated_at": {
      "type": "string",
      "format": "date-time"
    },
    "evaluated_by": {
      "type": "string",
      "description": "Identity that evaluated the gate"
    },
    "decision_authority": {
      "type": "string",
      "description": "Identity that approved the gate outcome (may differ from evaluator)"
    }
  }
}
```

## Gate-type-specific outcome validation

The `outcome` field's allowed values depend on `gate_type`:

| gate_type | Allowed outcomes |
|---|---|
| `LAUNCH_READINESS` | LAUNCH, LAUNCH_WITH_CONDITIONS, DEFER, DECLINE |
| `PILOT_HEALTH` | CONTINUE, ADJUST, ESCALATE, TERMINATE |
| `CLOSURE_SCALE` | STOP, EXTEND, EXPAND, DEPLOY |

If `gate_type` is `CLOSURE_SCALE` and `outcome` is `EXTEND`, then
`extend_requirements` MUST be present with ALL five required fields.

## Relationship to existing implementation

| Schema field | Existing source | Status |
|---|---|---|
| `gate_id` | — | Genuinely new |
| `pilot_id` | — | Genuinely new |
| `gate_type` | — | Genuinely new (no pilot-level gate types) |
| `outcome` | — | Genuinely new (no pilot-level gate outcomes) |
| `conditions` | — | Genuinely new |
| `criteria_evaluation` | — | Genuinely new (no success criteria evaluation) |
| `extend_requirements` | — | Genuinely new |
| `rationale` | — | Genuinely new |
| `evidence_cited` | — | Genuinely new |
| `evaluated_at/by` | — | Genuinely new |
| `decision_authority` | — | Genuinely new |

> **This entire schema is genuinely new.** No pilot-level gate records
> exist in the current implementation. The 3 existing `GateRule` objects
> are operator-level routing gates — a different layer entirely.

## Relationship to operator-level gates

The existing `GateResult` in `src/domain/production_gate.py` is an
**operator-level** gate result (rule_id, operator_id, metric_id, metric_value,
threshold, fired, action). It is NOT a pilot-level gate record.

The `GateRecord` schema defined here is a **pilot-level** gate record
that governs the pilot lifecycle. Both layers coexist:

- Operator-level `GateResult`: routes individual operators to
  coaching/review/intervention.
- Pilot-level `GateRecord`: governs pilot launch, health, and closure.
