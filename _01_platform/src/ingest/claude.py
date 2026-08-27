"""Claude adapter — parses Claude usage export JSON into Observations.

Claude usage exports typically contain per-session or per-day token counts.
This adapter normalizes them into canonical Observation objects.

Expected input format (Claude usage export):
    A JSON file with an array of records, each containing:
    - operator_id (or user_id, mapped to operator_id)
    - timestamp (or date)
    - input_tokens, output_tokens
    - cache_read_tokens, cache_write_tokens (may be absent → 0)
    - platform: "claude"
    - model (e.g. "claude-code", "claude-sonnet-4")

Optional fields (used by ingest_full for canonical objects):
    - session_id → Session objects
    - model → SystemVersion
    - task_id / intent_label → Task objects
    - artifacts (array) → Artifact objects (each with file_path, lines_added,
      lines_removed, commit_sha)

If cache fields are absent, they default to 0 (the adapter warns).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .base import IngestAdapter, IngestResult


class ClaudeAdapter(IngestAdapter):
    """Parses Claude usage export JSON into Observation objects."""

    @property
    def name(self) -> str:
        return "claude"

    def _default_collection_method(self) -> str:
        return "claude_usage_export_json"

    def _default_collector_version(self) -> str:
        return "claude_adapter_v1"

    def ingest(self, path: str) -> IngestResult:
        p = Path(path)
        if not p.exists():
            return IngestResult(source=self.name, observations=[], errors=[f"File not found: {p}"])

        try:
            with open(p) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return IngestResult(source=self.name, observations=[], errors=[f"JSON parse error: {e}"])

        # Accept either a bare array or {"records": [...]} / {"data": [...]}
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            records = data.get("records") or data.get("data") or data.get("usage") or []
        else:
            return IngestResult(source=self.name, observations=[], errors=["Unexpected JSON structure"])

        observations: List = []
        errors: List[str] = []
        warnings: List[str] = []
        missing_cache_count = 0

        for i, rec in enumerate(records):
            try:
                operator_id = rec.get("operator_id") or rec.get("user_id") or rec.get("operator")
                if not operator_id:
                    errors.append(f"Record {i}: missing operator_id/user_id")
                    continue

                timestamp = rec.get("timestamp") or rec.get("date") or rec.get("created_at")
                if not timestamp:
                    errors.append(f"Record {i}: missing timestamp/date")
                    continue

                I = int(rec.get("input_tokens", 0))
                O = int(rec.get("output_tokens", 0))
                R = int(rec.get("cache_read_tokens", 0))
                W = int(rec.get("cache_write_tokens", 0))

                if "cache_read_tokens" not in rec and "cache_write_tokens" not in rec:
                    missing_cache_count += 1

                model = rec.get("model")
                session_id = rec.get("session_id")

                obs = self._make_observation(
                    operator_id=str(operator_id),
                    timestamp_str=str(timestamp),
                    I=I, O=O, R=R, W=W,
                    synthetic=rec.get("synthetic", False),
                    platform="claude",
                    model=model,
                    session_id=session_id,
                    provenance=rec.get("provenance", "ingest:claude"),
                    obs_id=rec.get("observation_id"),
                    source_confidence=rec.get("source_confidence"),
                    raw_source_reference=rec.get("raw_source_reference"),
                )
                observations.append(obs)
            except Exception as e:
                errors.append(f"Record {i}: {e}")

        if missing_cache_count > 0:
            warnings.append(f"{missing_cache_count} records had no cache token fields (defaulted to 0)")

        return IngestResult(source=self.name, observations=observations, errors=errors, warnings=warnings)

    # ── Full ingest: canonical objects ──────────────────────────────────

    _TENANT_ID = "default"
    _SYSTEM_ID = "claude"

    def _load_records(self, path: str):
        """Load and return (records, errors) from a Claude export file."""
        p = Path(path)
        if not p.exists():
            return [], [f"File not found: {p}"]
        try:
            with open(p) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return [], [f"JSON parse error: {e}"]
        if isinstance(data, list):
            return data, []
        if isinstance(data, dict):
            return data.get("records") or data.get("data") or data.get("usage") or [], []
        return [], ["Unexpected JSON structure"]

    @staticmethod
    def _parse_ts(ts_str: str) -> datetime:
        """Parse a timestamp string into a UTC datetime."""
        ts = ts_str
        if isinstance(ts, str):
            if "T" in ts:
                ts = ts.replace("Z", "+00:00")
                ts = datetime.fromisoformat(ts)
            else:
                ts = datetime.fromisoformat(ts + "T12:00:00+00:00")
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts

    def ingest_full(self, path: str) -> IngestResult:
        """Full ingest: emit Observations + all canonical objects.

        Produces System, SystemVersion, Session, Task, and Artifact objects
        in addition to the Observations from the standard ingest path.
        """
        # Reuse the observation-level ingest first.
        base_result = self.ingest(path)
        if not base_result.ok:
            return base_result

        records, load_errors = self._load_records(path)
        if load_errors:
            return IngestResult(
                source=self.name,
                observations=base_result.observations,
                errors=base_result.errors + load_errors,
                warnings=base_result.warnings,
            )

        warnings: List[str] = list(base_result.warnings)

        # ── System ──────────────────────────────────────────────────────
        system = self._make_system(
            system_id=self._SYSTEM_ID,
            tenant_id=self._TENANT_ID,
            name="Claude",
            system_type="ai_platform",
            vendor="Anthropic",
        )

        # ── SystemVersion(s) from distinct models ───────────────────────
        system_versions: List = []
        seen_models: dict = {}  # model_label -> version_id
        for rec in records:
            model = rec.get("model")
            if not model:
                continue
            if model not in seen_models:
                version_id = f"{self._SYSTEM_ID}:{model}"
                seen_models[model] = version_id
                system_versions.append(self._make_system_version(
                    version_id=version_id,
                    system_id=self._SYSTEM_ID,
                    version_label=model,
                    model_identifier=model,
                ))

        # Fallback: if no model fields were present, emit a default version.
        if not system_versions:
            default_label = "claude-default"
            version_id = f"{self._SYSTEM_ID}:{default_label}"
            seen_models[default_label] = version_id
            system_versions.append(self._make_system_version(
                version_id=version_id,
                system_id=self._SYSTEM_ID,
                version_label=default_label,
            ))

        # ── Sessions from session_id groups ─────────────────────────────
        sessions: List = []
        session_meta: dict = {}  # session_id -> {operator_id, start_time, model}
        for rec in records:
            sid = rec.get("session_id")
            if not sid:
                continue
            operator_id = str(rec.get("operator_id") or rec.get("user_id") or rec.get("operator") or "unknown")
            ts = rec.get("timestamp") or rec.get("date") or rec.get("created_at")
            if not ts:
                continue
            try:
                dt = self._parse_ts(str(ts))
            except Exception:
                continue
            model = rec.get("model")
            if sid not in session_meta or dt < session_meta[sid]["start_time"]:
                session_meta[sid] = {
                    "operator_id": operator_id,
                    "start_time": dt,
                    "model": model,
                }

        for sid, meta in session_meta.items():
            version_id = seen_models.get(meta["model"]) if meta["model"] else seen_models.get("claude-default")
            sessions.append(self._make_session(
                session_id=sid,
                operator_id=meta["operator_id"],
                system_id=self._SYSTEM_ID,
                start_time=meta["start_time"],
                system_version_id=version_id,
            ))

        # ── Tasks from task_id / intent_label ───────────────────────────
        tasks: List = []
        seen_tasks: set = set()
        for rec in records:
            task_id = rec.get("task_id")
            if not task_id or task_id in seen_tasks:
                continue
            operator_id = str(rec.get("operator_id") or rec.get("user_id") or rec.get("operator") or "unknown")
            intent_label = rec.get("intent_label") or "unspecified"
            task_type = rec.get("task_type") or "code_generation"
            ts = rec.get("timestamp") or rec.get("date") or rec.get("created_at")
            if not ts:
                continue
            try:
                dt = self._parse_ts(str(ts))
            except Exception:
                continue
            seen_tasks.add(task_id)
            tasks.append(self._make_task(
                task_id=task_id,
                operator_id=operator_id,
                intent_label=intent_label,
                task_type=task_type,
                created_at=dt,
            ))

        # ── Artifacts from artifacts arrays ─────────────────────────────
        artifacts: List = []
        for rec in records:
            rec_artifacts = rec.get("artifacts")
            if not rec_artifacts or not isinstance(rec_artifacts, list):
                continue
            operator_id = str(rec.get("operator_id") or rec.get("user_id") or rec.get("operator") or "unknown")
            ts = rec.get("timestamp") or rec.get("date") or rec.get("created_at")
            created_dt = None
            if ts:
                try:
                    created_dt = self._parse_ts(str(ts))
                except Exception:
                    created_dt = None
            for art in rec_artifacts:
                if not isinstance(art, dict):
                    continue
                artifact_id = art.get("artifact_id") or f"art_{operator_id}_{len(artifacts)}"
                artifacts.append(self._make_artifact(
                    artifact_id=artifact_id,
                    operator_id=operator_id,
                    artifact_type=art.get("artifact_type") or "code_file",
                    file_path=art.get("file_path"),
                    lines_added=art.get("lines_added"),
                    lines_removed=art.get("lines_removed"),
                    commit_sha=art.get("commit_sha"),
                    created_at=created_dt,
                ))

        if not sessions:
            warnings.append("No session_id fields found — 0 Session objects emitted")

        return IngestResult(
            source=self.name,
            observations=base_result.observations,
            errors=base_result.errors,
            warnings=warnings,
            systems=[system],
            system_versions=system_versions,
            sessions=sessions,
            tasks=tasks,
            artifacts=artifacts,
        )
