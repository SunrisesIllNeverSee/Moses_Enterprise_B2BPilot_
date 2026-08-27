"""Codex adapter — parses Codex/OpenAI usage CSV into Observations.

Codex usage exports are typically CSV with per-session or per-day token counts.
This adapter normalizes them into canonical Observation objects.

Expected input format (Codex usage CSV):
    A CSV file with columns that may include:
    - operator_id (or user_id)
    - timestamp (or date)
    - input_tokens (or prompt_tokens)
    - output_tokens (or completion_tokens)
    - cache_read_tokens (or cached_tokens) — may be absent → 0
    - cache_write_tokens — may be absent → 0
    - model (e.g. "gpt-4", "codex")
    - session_id

Optional columns (used by ingest_full for canonical objects):
    - session_id → Session objects
    - model (or engine) → SystemVersion
    - task_id / intent_label → Task objects
    - artifacts (JSON array string) → Artifact objects

Column name aliases are handled (prompt_tokens→input_tokens, etc.).
"""
from __future__ import annotations

import csv
import json as _json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .base import IngestAdapter, IngestResult


# Column name aliases — first match wins.
COL_ALIASES = {
    "operator_id": ["operator_id", "user_id", "operator"],
    "timestamp": ["timestamp", "date", "created_at", "day"],
    "input_tokens": ["input_tokens", "prompt_tokens", "input"],
    "output_tokens": ["output_tokens", "completion_tokens", "output"],
    "cache_read_tokens": ["cache_read_tokens", "cached_tokens", "cache_read"],
    "cache_write_tokens": ["cache_write_tokens", "cache_write"],
    "model": ["model", "engine"],
    "session_id": ["session_id", "session"],
    "source_confidence": ["source_confidence", "source_conf"],
    "raw_source_reference": ["raw_source_reference", "raw_ref"],
    "task_id": ["task_id", "task"],
    "intent_label": ["intent_label", "intent"],
    "task_type": ["task_type", "intent_type"],
    "artifacts": ["artifacts", "artifact_json"],
}


def _resolve_column(row: dict, field: str) -> str:
    """Find the actual column name in `row` for a logical field."""
    for alias in COL_ALIASES.get(field, [field]):
        if alias in row:
            return alias
    return field


class CodexAdapter(IngestAdapter):
    """Parses Codex/OpenAI usage CSV into Observation objects."""

    @property
    def name(self) -> str:
        return "codex"

    def _default_collection_method(self) -> str:
        return "codex_usage_export_csv"

    def _default_collector_version(self) -> str:
        return "codex_adapter_v1"

    def ingest(self, path: str) -> IngestResult:
        p = Path(path)
        if not p.exists():
            return IngestResult(source=self.name, observations=[], errors=[f"File not found: {p}"])

        observations: List = []
        errors: List[str] = []
        warnings: List[str] = []
        missing_cache_count = 0

        with open(p, newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return IngestResult(source=self.name, observations=[], errors=["Empty CSV or no header"])

            for i, row in enumerate(reader):
                try:
                    op_col = _resolve_column(row, "operator_id")
                    operator_id = row.get(op_col)
                    if not operator_id:
                        errors.append(f"Row {i}: missing operator_id")
                        continue

                    ts_col = _resolve_column(row, "timestamp")
                    timestamp = row.get(ts_col)
                    if not timestamp:
                        errors.append(f"Row {i}: missing timestamp")
                        continue

                    I = int(row.get(_resolve_column(row, "input_tokens"), 0) or 0)
                    O = int(row.get(_resolve_column(row, "output_tokens"), 0) or 0)
                    R_col = _resolve_column(row, "cache_read_tokens")
                    W_col = _resolve_column(row, "cache_write_tokens")
                    R = int(row.get(R_col, 0) or 0)
                    W = int(row.get(W_col, 0) or 0)

                    if R_col not in row and W_col not in row:
                        missing_cache_count += 1

                    model = row.get(_resolve_column(row, "model"))
                    session_id = row.get(_resolve_column(row, "session_id"))
                    source_confidence = row.get(_resolve_column(row, "source_confidence"))
                    raw_source_reference = row.get(_resolve_column(row, "raw_source_reference"))

                    obs = self._make_observation(
                        operator_id=str(operator_id),
                        timestamp_str=str(timestamp),
                        I=I, O=O, R=R, W=W,
                        synthetic=False,
                        platform="codex",
                        model=model,
                        session_id=session_id,
                        provenance="ingest:codex",
                        source_confidence=source_confidence,
                        raw_source_reference=raw_source_reference,
                    )
                    observations.append(obs)
                except Exception as e:
                    errors.append(f"Row {i}: {e}")

        if missing_cache_count > 0:
            warnings.append(f"{missing_cache_count} rows had no cache token columns (defaulted to 0)")

        return IngestResult(source=self.name, observations=observations, errors=errors, warnings=warnings)

    # ── Full ingest: canonical objects ──────────────────────────────────

    _TENANT_ID = "default"
    _SYSTEM_ID = "codex"

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

    def _load_rows(self, path: str):
        """Load and return (rows, errors) from a Codex CSV file."""
        p = Path(path)
        if not p.exists():
            return [], [f"File not found: {p}"]
        rows: List[dict] = []
        with open(p, newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return [], ["Empty CSV or no header"]
            for row in reader:
                rows.append(row)
        return rows, []

    def ingest_full(self, path: str) -> IngestResult:
        """Full ingest: emit Observations + all canonical objects.

        Produces System, SystemVersion, Session, Task, and Artifact objects
        in addition to the Observations from the standard ingest path.
        """
        # Reuse the observation-level ingest first.
        base_result = self.ingest(path)
        if not base_result.ok:
            return base_result

        rows, load_errors = self._load_rows(path)
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
            name="Codex",
            system_type="ai_platform",
            vendor="OpenAI",
        )

        # ── SystemVersion(s) from distinct models ───────────────────────
        system_versions: List = []
        seen_models: dict = {}  # model_label -> version_id
        for row in rows:
            model = row.get(_resolve_column(row, "model"))
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

        # Fallback: if no model columns were present, emit a default version.
        if not system_versions:
            default_label = "codex-default"
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
        for row in rows:
            sid = row.get(_resolve_column(row, "session_id"))
            if not sid:
                continue
            operator_id = str(row.get(_resolve_column(row, "operator_id")) or "unknown")
            ts = row.get(_resolve_column(row, "timestamp"))
            if not ts:
                continue
            try:
                dt = self._parse_ts(str(ts))
            except Exception:
                continue
            model = row.get(_resolve_column(row, "model"))
            if sid not in session_meta or dt < session_meta[sid]["start_time"]:
                session_meta[sid] = {
                    "operator_id": operator_id,
                    "start_time": dt,
                    "model": model,
                }

        for sid, meta in session_meta.items():
            version_id = seen_models.get(meta["model"]) if meta["model"] else seen_models.get("codex-default")
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
        for row in rows:
            task_id = row.get(_resolve_column(row, "task_id"))
            if not task_id or task_id in seen_tasks:
                continue
            operator_id = str(row.get(_resolve_column(row, "operator_id")) or "unknown")
            intent_label = row.get(_resolve_column(row, "intent_label")) or "unspecified"
            task_type = row.get(_resolve_column(row, "task_type")) or "code_generation"
            ts = row.get(_resolve_column(row, "timestamp"))
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

        # ── Artifacts from artifacts column (JSON array string) ─────────
        artifacts: List = []
        for row in rows:
            art_col = _resolve_column(row, "artifacts")
            art_raw = row.get(art_col)
            if not art_raw:
                continue
            try:
                rec_artifacts = _json.loads(art_raw)
            except (_json.JSONDecodeError, TypeError):
                continue
            if not isinstance(rec_artifacts, list):
                continue
            operator_id = str(row.get(_resolve_column(row, "operator_id")) or "unknown")
            ts = row.get(_resolve_column(row, "timestamp"))
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
            warnings.append("No session_id columns found — 0 Session objects emitted")

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
