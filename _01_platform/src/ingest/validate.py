"""Validation — checks Observation objects against observation.schema.json.

Validates that observations conform to the canonical schema before they enter
the scoring pipeline. P0 acceptance: "commands return non-zero exit code on
schema/provenance errors."
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Tuple

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.observation import Observation


def validate_observations(observations: List[Observation]) -> Tuple[List[str], List[str]]:
    """Validate observations against the canonical schema.

    Returns (errors, warnings). Errors are schema violations that should
    block processing. Warnings are soft issues worth reporting.
    """
    errors: List[str] = []
    warnings: List[str] = []

    seen_ids = set()
    for i, obs in enumerate(observations):
        # Required fields
        if not obs.observation_id:
            errors.append(f"Observation {i}: missing observation_id")
        if not obs.operator_id:
            errors.append(f"Observation {i}: missing operator_id")
        if obs.timestamp is None:
            errors.append(f"Observation {i}: missing timestamp")

        # Non-negative token counts (also enforced by Observation.__post_init__,
        # but double-check in case objects were constructed bypassing the guard)
        if obs.input_tokens < 0:
            errors.append(f"Observation {i}: negative input_tokens")
        if obs.output_tokens < 0:
            errors.append(f"Observation {i}: negative output_tokens")
        if obs.cache_read_tokens < 0:
            errors.append(f"Observation {i}: negative cache_read_tokens")
        if obs.cache_write_tokens < 0:
            errors.append(f"Observation {i}: negative cache_write_tokens")

        # Duplicate IDs
        if obs.observation_id in seen_ids:
            errors.append(f"Observation {i}: duplicate observation_id '{obs.observation_id}'")
        seen_ids.add(obs.observation_id)

        # Synthetic flag must be present (boolean)
        if obs.synthetic is None:
            warnings.append(f"Observation {i}: synthetic flag is None")

        # Provenance should be set
        if not obs.provenance:
            warnings.append(f"Observation {i}: no provenance set")

    return errors, warnings


def validate_against_schema_file(observations: List[Observation], schema_path: str) -> Tuple[List[str], List[str]]:
    """Validate observations and also check the schema file exists and is well-formed."""
    errors, warnings = validate_observations(observations)

    p = Path(schema_path)
    if not p.exists():
        errors.append(f"Schema file not found: {p}")
    else:
        try:
            with open(p) as f:
                schema = json.load(f)
            required = schema.get("required", [])
            for i, obs in enumerate(observations):
                d = obs.to_dict()
                for field in required:
                    if field not in d or d[field] is None:
                        errors.append(f"Observation {i}: missing required schema field '{field}'")
        except json.JSONDecodeError as e:
            errors.append(f"Schema file parse error: {e}")

    return errors, warnings
