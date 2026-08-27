"""OpenAI/Codex API adapter — fetches usage telemetry from the OpenAI API.

Stub mode: generates deterministic synthetic daily telemetry.
Live mode: calls the OpenAI usage API endpoint.

Requires OPENAI_API_KEY environment variable for live mode.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import List

from .api_base import ApiAdapter


class CodexApiAdapter(ApiAdapter):
    """Fetches OpenAI/Codex usage telemetry from the OpenAI API."""

    @property
    def name(self) -> str:
        return "codex"

    def _env_key_name(self) -> str:
        return "OPENAI_API_KEY"

    def _default_collector_version(self) -> str:
        return "codex_api_v1"

    def _fetch_stub(self, operator_id: str, days: int) -> List[dict]:
        """Generate deterministic synthetic daily telemetry."""
        seed = int(hashlib.md5(operator_id.encode()).hexdigest()[:8], 16)
        records: List[dict] = []
        now = datetime.now(timezone.utc)
        for d in range(days):
            day = now - timedelta(days=days - d)
            r = (seed + d * 3571) % 10000
            I = 6000 + (r % 10000)       # 6k–16k input
            O = 1500 + (r * 5 % 6000)    # 1.5k–7.5k output
            R = 2000 + (r * 11 % 8000)   # 2k–10k cache read
            W = 200 + (r % 1000)         # 0.2k–1.2k cache write
            records.append({
                "timestamp": day.strftime("%Y-%m-%d"),
                "input_tokens": I,
                "output_tokens": O,
                "cache_read_tokens": R,
                "cache_write_tokens": W,
                "model": "gpt-4o",
                "session_id": f"session_{operator_id}_{day.strftime('%Y%m%d')}",
            })
        return records

    def _fetch_live(self, operator_id: str, days: int) -> List[dict]:
        """Fetch live usage from the OpenAI API.

        Calls the /v1/usage endpoint (completions usage breakdown).
        The OpenAI API provides daily usage data via the usage endpoint.
        """
        import urllib.request
        import json

        api_key = self._api_key
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        url = f"https://api.openai.com/v1/usage?start_date={start}&end_date={end}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        }

        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        # Normalize OpenAI usage response to our record format
        # OpenAI returns daily usage by model
        records: List[dict] = []
        for entry in data.get("data", []):
            records.append({
                "timestamp": entry.get("date") or entry.get("aggregation_timestamp"),
                "input_tokens": int(entry.get("n_context_tokens_total", 0) or entry.get("prompt_tokens", 0)),
                "output_tokens": int(entry.get("n_generated_tokens_total", 0) or entry.get("completion_tokens", 0)),
                "cache_read_tokens": 0,  # OpenAI doesn't report cache separately in usage API
                "cache_write_tokens": 0,
                "model": entry.get("model", "gpt-4o"),
                "session_id": None,
            })
        return records
