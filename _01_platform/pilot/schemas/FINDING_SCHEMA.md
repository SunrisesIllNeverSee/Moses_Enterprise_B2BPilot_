# FINDING_SCHEMA.md

> Formal schema for a diagnostic finding — a hypothesis generated from
> pattern detection and measurement analysis.

## Schema (JSON Schema draft-07)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Finding",
  "type": "object",
  "required": ["finding_id", "pilot_id", "operator_id", "finding_type", "status", "evidence", "claim_type"],
  "properties": {
    "finding_id": {
      "type": "string",
      "description": "Unique finding identifier"
    },
    "pilot_id": {
      "type": "string",
      "description": "The pilot this finding belongs to"
    },
    "operator_id": {
      "type": "string",
      "description": "The operator this finding applies to"
    },
    "finding_type": {
      "type": "string",
      "enum": ["pattern", "divergence", "diagnosis", "benchmark", "workflow_fit", "topology", "similarity", "decomposition"],
      "description": "The type of finding"
    },
    "pattern_id": {
      "type": "string",
      "description": "Pattern ID if finding_type is pattern or diagnosis (e.g., P-CTX-01)"
    },
    "status": {
      "type": "string",
      "enum": ["HYPOTHESIS", "REPLICATED", "FAILED_REPLICATION"],
      "description": "HYPOTHESIS is the default. REPLICATED means stable across splits. Never CONFIRMED."
    },
    "evidence": {
      "type": "string",
      "description": "What was observed (factual, measurement-based)"
    },
    "evidence_grade": {
      "type": "string",
      "enum": ["OBSERVATIONAL", "CORRELATIONAL", "REPLICATED"],
      "description": "The evidence grade. OBSERVATIONAL is the default."
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Developmental confidence (not causal probability)"
    },
    "alternatives": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Alternative explanations considered"
    },
    "claim_type": {
      "type": "string",
      "enum": ["ASSOCIATION", "DESCRIPTIVE"],
      "description": "ASSOCIATION never CAUSATION. DESCRIPTIVE for pure measurement observations."
    },
    "recommended_interventions": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Catalog IDs of recommended interventions"
    },
    "divergence_class": {
      "type": "string",
      "enum": ["HIGH_USAGE_LOW_OPERATION", "LOW_USAGE_HIGH_OPERATION", "LOW_LOW", "MIXED"],
      "description": "Divergence quadrant if finding_type is divergence"
    },
    "benchmark_class": {
      "type": "string",
      "description": "Selected benchmark class if finding_type is benchmark"
    },
    "percentile_rank": {
      "type": "number",
      "description": "Percentile rank if finding_type is benchmark"
    },
    "synthetic": {
      "type": "boolean",
      "description": "True if finding is from synthetic/demo data"
    },
    "detected_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

## Relationship to existing implementation

| Schema field | Existing source | Status |
|---|---|---|
| `finding_id` | `Diagnosis.diagnosis_id` / `DetectedPattern` (no explicit ID) | Extension required |
| `pilot_id` | — | Genuinely new (no pilot binding) |
| `operator_id` | `Diagnosis.operator_id` / `DivergenceResult.operator_id` | Existing |
| `finding_type` | Implicit (pattern vs divergence vs diagnosis) | Extension required (explicit type field) |
| `pattern_id` | `Diagnosis.pattern_id` / `DetectedPattern.pattern_id` | Existing |
| `status` | `Diagnosis.status` (DiagnosisStatus enum: HYPOTHESIS) | Existing |
| `evidence` | `Diagnosis.evidence` | Existing |
| `evidence_grade` | `EvidenceGrade` enum in `src/domain/evidence_grade.py` | Existing |
| `confidence` | `Diagnosis.confidence` | Existing |
| `alternatives` | `Diagnosis.alternatives` | Existing |
| `claim_type` | Hardcoded ASSOCIATION in governance | Extension required (explicit field) |
| `recommended_interventions` | `Diagnosis.recommended_interventions` | Existing |
| `divergence_class` | `DivergenceResult.divergence_class` | Existing |
| `benchmark_class` | `BenchmarkResult.benchmark_class` | Existing |
| `percentile_rank` | `BenchmarkResult.percentile_rank` | Existing |
| `synthetic` | `Diagnosis.synthetic` | Existing |
| `detected_at` | — | Genuinely new (no timestamp on findings) |

## Governance constraints

1. `status` must never be `CONFIRMED`. Findings are always HYPOTHESIS or
   REPLICATED (stable across splits).
2. `claim_type` must never be `CAUSATION`. All findings are ASSOCIATION
   or DESCRIPTIVE.
3. `evidence_grade` must never exceed `REPLICATED`. No causal grade.
4. `confidence` is developmental confidence, not causal probability.
