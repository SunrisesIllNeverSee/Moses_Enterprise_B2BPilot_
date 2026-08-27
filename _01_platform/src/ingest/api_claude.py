"""Claude API adapter — fetches usage telemetry from the Anthropic API.

Stub mode: generates deterministic synthetic daily telemetry.
Live mode: calls the Anthropic Messages API usage endpoint.

Requires ANTHROPIC_API_KEY environment variable for live mode.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import List

from .api_base import ApiAdapter


class ClaudeApiAdapter(ApiAdapter):
    """Fetches Claude usage telemetry from the Anthropic API."""

    @property
    def name(self) -> str:
        return "claude"

    def _env_key_name(self) -> str:
        return "ANTHROPIC_API_KEY"

    def _default_collector_version(self) -> str:
        return "claude_api_v1"

    def _fetch_stub(self, operator_id: str, days: int) -> List[dict]:
        """Generate deterministic synthetic daily telemetry.

        Uses a hash of operator_id to seed per-operator variation so
        each operator gets consistent but different token counts.
        """
        seed = int(hashlib.md5(operator_id.encode()).hexdigest()[:8], 16)
        records: List[dict] = []
        now = datetime.now(timezone.utc)
        for d in range(days):
            day = now - timedelta(days=days - d)
            # Deterministic pseudo-random based on seed + day offset
            r = (seed + d * 7919) % 10000
            I = 8000 + (r % 12000)       # 8k–20k input
            O = 2000 + (r * 3 % 8000)    # 2k–10k output
            R = 5000 + (r * 7 % 15000)   # 5k–20k cache read
            W = 500 + (r % 2000)         # 0.5k–2.5k cache write
            records.append({
                "timestamp": day.strftime("%Y-%m-%d"),
                "input_tokens": I,
                "output_tokens": O,
                "cache_read_tokens": R,
                "cache_write_tokens": W,
                "model": "claude-sonnet-4-20250514",
                "session_id": f"session_{operator_id}_{day.strftime('%Y%m%d')}",
            })
        return records

    def _fetch_live(self, operator_id: str, days: int) -> List[dict]:
        """Fetch live usage from the Anthropic API.

        Calls the /v1/messages/usage endpoint (if available) or falls
        back to aggregating from the messages API. The Anthropic API
        returns token usage per request; this adapter aggregates to
        daily totals.
        """
        import urllib.request
        import json

        api_key = self._api_key
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")

        # Anthropic usage API endpoint (aggregated daily usage)
        # This is a placeholder for the real endpoint structure.
        # The actual Anthropic API may not expose a direct usage endpoint;
        # in practice, usage is tracked via response headers on each call.
        # This adapter assumes a usage reporting endpoint exists.
        url = "https://api.anthropic.com/v1/usage"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        body = json.dumps({"operator_id": operator_id, "start_date": start}).encode()

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        # Normalize API response to our record format
        records: List[dict] = []
        for entry in data.get("usage_records", []):
            records.append({
                "timestamp": entry.get("date") or entry.get("timestamp"),
                "input_tokens": int(entry.get("input_tokens", 0)),
                "output_tokens": int(entry.get("output_tokens", 0)),
                "cache_read_tokens": int(entry.get("cache_read_tokens", 0)),
                "cache_write_tokens": int(entry.get("cache_write_tokens", 0)),
                "model": entry.get("model", "claude-sonnet-4"),
                "session_id": entry.get("session_id"),
            })
        return records
