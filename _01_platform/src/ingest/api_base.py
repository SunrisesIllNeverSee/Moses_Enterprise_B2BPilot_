"""API-based ingest adapters — pull telemetry from provider APIs.

These adapters extend the file-based adapters with live API connections.
Each adapter has a stub mode (returns synthetic data) and a live mode
(calls the real API). The Groq adapter is provided for testing since
Groq offers a free tier with OpenAI-compatible token usage reporting.

Architecture:
    ingest/api_base.py   — ApiAdapter base class (stub + live modes)
    ingest/api_claude.py — Claude API adapter (Anthropic Messages API usage)
    ingest/api_codex.py  — OpenAI/Codex API adapter (usage API)
    ingest/api_groq.py   — Groq API adapter (OpenAI-compatible, for testing)

All API adapters produce the same canonical Observation objects as the
file-based adapters. The difference is the data source: file adapters
read exports, API adapters call live endpoints.

Stub mode: returns deterministic synthetic observations for testing
without API credentials. Enabled when no API key is provided.

Live mode: calls the real API endpoint. Requires an API key in the
constructor or via environment variable.
"""
from __future__ import annotations

import sys
from abc import abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from .base import IngestAdapter, IngestResult
from domain.observation import Observation


class ApiAdapter(IngestAdapter):
    """Base class for API-based ingest adapters.

    Subclasses implement `_fetch_live()` for real API calls and
    `_fetch_stub()` for synthetic test data. The adapter automatically
    selects stub mode when no API key is available.
    """

    def __init__(self, api_key: Optional[str] = None, stub: Optional[bool] = None) -> None:
        import os
        if api_key is not None:
            self._api_key = api_key
        else:
            self._api_key = os.environ.get(self._env_key_name(), "")
        # If stub is not explicitly set, use stub mode when no key is available.
        if stub is not None:
            self._stub_mode = stub
        else:
            self._stub_mode = not bool(self._api_key)

    @property
    def is_stub(self) -> bool:
        return self._stub_mode

    @abstractmethod
    def _env_key_name(self) -> str:
        """Environment variable name for the API key."""
        ...

    @abstractmethod
    def _fetch_live(self, operator_id: str, days: int) -> List[dict]:
        """Fetch raw usage records from the live API.

        Returns a list of dicts with keys: timestamp, input_tokens,
        output_tokens, cache_read_tokens, cache_write_tokens, model,
        session_id.
        """
        ...

    @abstractmethod
    def _fetch_stub(self, operator_id: str, days: int) -> List[dict]:
        """Generate synthetic usage records for testing."""
        ...

    def _default_collection_method(self) -> str:
        return "api_live" if not self._stub_mode else "api_stub"

    def ingest(self, path: str) -> IngestResult:
        """File-based ingest — delegates to file adapter.

        For API adapters, `path` is ignored. Use `fetch()` instead.
        """
        return IngestResult(
            source=self.name,
            observations=[],
            errors=["API adapters use fetch(operator_id, days), not ingest(path). Use the file adapter for file-based ingest."],
        )

    def fetch(self, operator_id: str, days: int = 30) -> IngestResult:
        """Fetch telemetry from the API (or stub) and return Observations.

        Args:
            operator_id: The operator to fetch telemetry for.
            days: Number of days of history to fetch.

        Returns:
            IngestResult with normalized Observation objects.
        """
        mode = "stub" if self._stub_mode else "live"
        try:
            raw_records = self._fetch_stub(operator_id, days) if self._stub_mode else self._fetch_live(operator_id, days)
        except Exception as e:
            return IngestResult(
                source=self.name,
                observations=[],
                errors=[f"API fetch failed ({mode}): {e}"],
            )

        observations: List[Observation] = []
        errors: List[str] = []
        warnings: List[str] = []

        if self._stub_mode:
            warnings.append(f"STUB MODE — no API key found. Set {self._env_key_name()} for live data.")

        for i, rec in enumerate(raw_records):
            try:
                obs = self._make_observation(
                    operator_id=str(operator_id),
                    timestamp_str=str(rec["timestamp"]),
                    I=int(rec.get("input_tokens", 0)),
                    O=int(rec.get("output_tokens", 0)),
                    R=int(rec.get("cache_read_tokens", 0)),
                    W=int(rec.get("cache_write_tokens", 0)),
                    synthetic=self._stub_mode,
                    platform=self.name,
                    model=rec.get("model"),
                    session_id=rec.get("session_id"),
                    provenance=f"api:{self.name}:{mode}",
                    obs_id=rec.get("observation_id"),
                )
                observations.append(obs)
            except Exception as e:
                errors.append(f"Record {i}: {e}")

        return IngestResult(
            source=self.name,
            observations=observations,
            errors=errors,
            warnings=warnings,
        )

    def fetch_and_persist(self, operator_id: str, repo, days: int = 30) -> IngestResult:
        """Fetch telemetry and persist observations to a repository.

        Works with SQLiteRepository. Falls back to returning the result
        without persisting if the repository doesn't support inserts.
        """
        result = self.fetch(operator_id, days)
        if result.ok and result.observations:
            if hasattr(repo, "insert_observations"):
                repo.insert_observations(result.observations)
        return result
