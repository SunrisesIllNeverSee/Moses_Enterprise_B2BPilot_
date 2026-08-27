"""Fixture adapter — reads observations.jsonl from the demo data directory.

This is the canonical demo-data adapter. It reads the JSONL file produced by
`scripts/generate_demo_data.py` and returns Observation objects directly.
Used for development, testing, and as a reference for other adapters.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.observation import Observation
from .base import IngestAdapter, IngestResult


class FixtureAdapter(IngestAdapter):
    """Reads observations.jsonl from demo_data/."""

    @property
    def name(self) -> str:
        return "fixture"

    def ingest(self, path: str) -> IngestResult:
        """Read observations.jsonl from `path` (file or directory).

        If `path` is a directory, looks for `observations.jsonl` inside it.
        """
        p = Path(path)
        if p.is_dir():
            p = p / "observations.jsonl"
        if not p.exists():
            return IngestResult(
                source=self.name,
                observations=[],
                errors=[f"File not found: {p}"],
            )

        observations: List[Observation] = []
        errors: List[str] = []
        warnings: List[str] = []

        with open(p) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    observations.append(Observation.from_dict(d))
                except Exception as e:
                    errors.append(f"Line {line_num}: {e}")

        if not observations and not errors:
            warnings.append("File contains no observations")

        return IngestResult(
            source=self.name,
            observations=observations,
            errors=errors,
            warnings=warnings,
        )
