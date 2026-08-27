"""Groq API adapter — fetches usage telemetry from the Groq API.

Groq is OpenAI-compatible and offers a free tier, making it ideal for
testing the API ingest pipeline without paid API credentials.

Stub mode: generates deterministic synthetic daily telemetry.
Live mode: calls the Groq usage API endpoint.

Requires GROQ_API_KEY environment variable for live mode.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import List

from .api_base import ApiAdapter


class GroqApiAdapter(ApiAdapter):
    """Fetches Groq usage telemetry from the Groq API.

    Groq is OpenAI-compatible and offers a free tier. Use this adapter
    for testing the API ingest pipeline without paid credentials.
    """

    @property
    def name(self) -> str:
        return "groq"

    def _env_key_name(self) -> str:
        return "GROQ_API_KEY"

    def _default_collector_version(self) -> str:
        return "groq_api_v1"

    def _fetch_stub(self, operator_id: str, days: int) -> List[dict]:
        """Generate deterministic synthetic daily telemetry."""
        seed = int(hashlib.md5(operator_id.encode()).hexdigest()[:8], 16)
        records: List[dict] = []
        now = datetime.now(timezone.utc)
        for d in range(days):
            day = now - timedelta(days=days - d)
            r = (seed + d * 5471) % 10000
            I = 3000 + (r % 8000)        # 3k–11k input
            O = 1000 + (r * 9 % 5000)    # 1k–6k output
            R = 0                        # Groq doesn't report cache tokens
            W = 0
            records.append({
                "timestamp": day.strftime("%Y-%m-%d"),
                "input_tokens": I,
                "output_tokens": O,
                "cache_read_tokens": R,
                "cache_write_tokens": W,
                "model": "llama-3.3-70b-versatile",
                "session_id": f"groq_{operator_id}_{day.strftime('%Y%m%d')}",
            })
        return records

    def _fetch_live(self, operator_id: str, days: int) -> List[dict]:
        """Fetch live usage from the Groq API.

        Groq provides usage data via the OpenAI-compatible API. Token
        counts are returned in each completion response. This adapter
        assumes a usage reporting endpoint or aggregates from session logs.
        """
        import urllib.request
        import json

        api_key = self._api_key
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set")

        # Groq usage endpoint (OpenAI-compatible usage API)
        start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        url = f"https://api.groq.com/openai/v1/usage?start_date={start}&end_date={end}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        }

        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        records: List[dict] = []
        for entry in data.get("data", []):
            records.append({
                "timestamp": entry.get("date") or entry.get("aggregation_timestamp"),
                "input_tokens": int(entry.get("prompt_tokens", 0)),
                "output_tokens": int(entry.get("completion_tokens", 0)),
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
                "model": entry.get("model", "llama-3.3-70b-versatile"),
                "session_id": None,
            })
        return records
