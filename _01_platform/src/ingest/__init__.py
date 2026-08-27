"""Ingest adapters — normalize provider telemetry into Observation objects.

P0-C: one fixture adapter + two real-provider adapters (Claude JSON, Codex CSV).
P1+: API-based adapters for live telemetry (Claude API, OpenAI/Codex API, Groq API).
All adapters produce `domain.Observation` objects conforming to
`schemas/observation.schema.json`.

Architecture:
    ingest/base.py       — IngestAdapter base class + IngestResult
    ingest/fixture.py    — reads observations.jsonl from demo_data
    ingest/claude.py     — parses Claude usage export JSON (file-based)
    ingest/codex.py      — parses Codex usage CSV (file-based)
    ingest/validate.py   — schema-conformance validation
    ingest/api_base.py   — ApiAdapter base class (stub + live modes)
    ingest/api_claude.py — Claude API adapter (Anthropic Messages API)
    ingest/api_codex.py  — OpenAI/Codex API adapter (usage API)
    ingest/api_groq.py   — Groq API adapter (OpenAI-compatible, for testing)

Usage (file-based):
    from ingest import FixtureAdapter, ClaudeAdapter, CodexAdapter
    adapter = FixtureAdapter()
    result = adapter.ingest("path/to/data")
    observations = result.observations  # list[Observation]

Usage (API-based):
    from ingest import ClaudeApiAdapter, GroqApiAdapter
    adapter = GroqApiAdapter()  # stub mode if no GROQ_API_KEY set
    result = adapter.fetch("op_001", days=30)
    observations = result.observations
"""
from __future__ import annotations

from .base import IngestAdapter, IngestResult
from .fixture import FixtureAdapter
from .claude import ClaudeAdapter
from .codex import CodexAdapter
from .github import GitHubAdapter
from .validate import validate_observations
from .api_base import ApiAdapter
from .api_claude import ClaudeApiAdapter
from .api_codex import CodexApiAdapter
from .api_groq import GroqApiAdapter

__all__ = [
    "IngestAdapter", "IngestResult",
    "FixtureAdapter", "ClaudeAdapter", "CodexAdapter", "GitHubAdapter",
    "validate_observations",
    "ApiAdapter",
    "ClaudeApiAdapter", "CodexApiAdapter", "GroqApiAdapter",
]
