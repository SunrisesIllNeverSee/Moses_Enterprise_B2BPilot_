# VERIFICATION_SCHEMA.md

> Formal schema for a verification result — the pre/post measurement
> of an intervention against its pre-declared target.

## Schema (JSON Schema draft-07)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "VerificationResult",
  "type": "object",
  "required": ["verification_id", "pilot_id", "intervention_id", "operator_id", "target_metric", "baseline_window", "followup_window", "deltas", "outcome", "claim_type"],
  "properties": {
    "verification_id": {
      "type": "string",
      "description": "Unique verification identifier"
    },
    "pilot_id": {
      "type": "string",
      "description": "The pilot this verification belongs to"
    },
    "intervention_id": {
      "type": "string",
      "description": "The intervention being verified"
    },
    "operator_id": {
      "type": "string",
      "description": "The operator who received the intervention"
    },
    "target_metric": {
      "type": "string",
      "description": "The pre-declared target metric"
    },
    "baseline_window": {
      "type": "object",
      "required": ["start", "end"],
      "properties": {
        "start": {"type": "string", "format": "date"},
        "end": {"type": "string", "format": "date"}
      }
    },
    "followup_window": {
      "type": "object",
      "required": ["start", "end"],
      "properties": {
        "start": {"type": "string", "format": "date"},
        "end": {"type": "string", "format": "date"}
      }
    },
    "target_delta": {
      "type": "object",
      "properties": {
        "metric_id": {"type": "string"},
        "baseline_value": {"type": ["number", "null"]},
        "followup_value": {"type": ["number", "null"]},
        "absolute_delta": {"type": ["number", "null"]},
        "percent_delta": {"type": ["number", "null"]}
      }
    },
    "non_target_deltas": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "metric_id": {"type": "string"},
          "baseline_value": {"type": ["number", "null"]},
          "followup_value": {"type": ["number", "null"]},
          "absolute_delta": {"type": ["number", "null"]},
          "percent_delta": {"type": ["number", "null"]}
        }
      },
      "description": "Non-target metric deltas to detect side effects"
    },
    "deltas": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "metric_id": {"type": "string"},
          "baseline_value": {"type": ["number", "null"]},
          "followup_value": {"type": ["number", "null"]},
          "absolute_delta": {"type": ["number", "null"]},
          "percent_delta": {"type": ["number", "null"]}
        }
      },
      "description": "All metric deltas (target + non-target)"
    },
    "outcome": {
      "type": "string",
      "enum": ["SUCCESS", "PARTIAL", "NO_EFFECT", "NEGATIVE"],
      "description": "Declared intervention outcome"
    },
    "classification": {
      "type": "string",
      "enum": ["improved_internal_only", "improved_internal_and_external", "no_change", "degraded"],
      "description": "Classification of the verification result"
    },
    "external_deltas": {
      "type": "object",
      "description": "External outcome deltas (if outcome join configured)"
    },
    "replication_status": {
      "type": "string",
      "enum": ["STABLE", "UNSTABLE", "INSUFFICIENT_DATA", "NOT_REPLICATED"],
      "description": "Whether the finding was stable across splits"
    },
    "claim_type": {
      "type": "string",
      "enum": ["ASSOCIATION", "DESCRIPTIVE"],
      "description": "ASSOCIATION never CAUSATION"
    },
    "evidence_grade": {
      "type": "string",
      "enum": ["OBSERVATIONAL", "CORRELATIONAL", "REPLICATED"]
    },
    "synthetic": {
      "type": "boolean"
    },
    "summary": {
      "type": "string",
      "description": "Human-readable summary of the verification"
    }
  }
}
```

## Relationship to existing implementation

| Schema field | Existing source | Status |
|---|---|---|
| `verification_id` | — | Genuinely new (no explicit ID on VerificationResult) |
| `pilot_id` | — | Genuinely new |
| `intervention_id` | `VerificationResult.intervention_id` | Existing |
| `operator_id` | `VerificationResult.operator_id` | Existing |
| `target_metric` | `VerificationResult.target_metric` | Existing |
| `baseline_window` | `VerificationResult.baseline_window` | Existing |
| `followup_window` | `VerificationResult.followup_window` | Existing |
| `target_delta` | `VerificationResult.target_delta` (MetricDelta) | Existing |
| `non_target_deltas` | `VerificationResult.non_target_deltas` | Existing |
| `deltas` | `VerificationResult.deltas` (list[MetricDelta]) | Existing |
| `outcome` | `Intervention.synthetic_outcome` (InterventionOutcome) | Existing |
| `classification` | `results.json` classification field | Existing (in demo data, not on VerificationResult) |
| `external_deltas` | `results.json` external_deltas field | Existing (in demo data) |
| `replication_status` | `ReplicationResult.status` (ReplicationStatus enum) | Existing (separate object) |
| `claim_type` | Hardcoded ASSOCIATION | Extension required (explicit field) |
| `evidence_grade` | `EvidenceGrade` enum | Existing |
| `synthetic` | `VerificationResult.synthetic` | Existing |
| `summary` | `VerificationResult.summary` | Existing |

## Governance constraints

1. `claim_type` must never be `CAUSATION`. Verification is ASSOCIATION.
2. `outcome` must be declared (SUCCESS/PARTIAL/NO_EFFECT/NEGATIVE) —
   negative outcomes are representable and reportable.
3. `non_target_deltas` must be checked — side effects must be documented.
4. `replication_status` strengthens confidence but never establishes
   causation.
