"""GitHub Copilot adapter — parses Copilot usage data into Observations.

GitHub Copilot usage exports typically contain per-repo or per-user daily
usage statistics. This adapter normalizes them into canonical Observation
objects and, in full-ingest mode, emits the full canonical object set.

Expected input format (GitHub Copilot usage export):
    CSV or JSON with per-user-day records containing some of:
    - date (or timestamp)
    - user_id (→ operator_id)
    - suggestions_shown
    - suggestions_accepted
    - lines_accepted
    - lines_rejected
    - language
    - repo (or repository)
    - input_tokens / output_tokens (may be absent — estimated from lines)

Token estimation: when token fields are absent, output tokens are estimated
as ~100 tokens per line accepted, and input tokens as ~50 tokens per
suggestion shown.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .base import IngestAdapter, IngestResult

# Column name aliases — first match wins.
COL_ALIASES = {
    "operator_id": ["operator_id", "user_id", "user", "developer"],
    "timestamp": ["timestamp", "date", "day", "created_at"],
    "suggestions_shown": ["suggestions_shown", "suggestions"],
    "suggestions_accepted": ["suggestions_accepted", "acceptances"],
    "lines_accepted": ["lines_accepted", "lines_acceptance"],
    "lines_rejected": ["lines_rejected", "lines_rejection"],
    "language": ["language", "lang"],
    "repo": ["repo", "repository"],
    "input_tokens": ["input_tokens", "prompt_tokens"],
    "output_tokens": ["output_tokens", "completion_tokens"],
    "session_id": ["session_id", "session"],
    "model": ["model", "engine"],
}

# Token estimation constants.
TOKENS_PER_LINE_ACCEPTED = 100
TOKENS_PER_SUGGESTION_SHOWN = 50


def _resolve_column(row: dict, field: str) -> str:
    """Find the actual column name in `row` for a logical field."""
    for alias in COL_ALIASES.get(field, [field]):
        if alias in row:
            return alias
    return field


class GitHubAdapter(IngestAdapter):
    """Parses GitHub Copilot usage CSV/JSON into Observation objects."""

    @property
    def name(self) -> str:
        return "github-copilot"

    def _default_collection_method(self) -> str:
        return "github_copilot_usage_export"

    def _default_collector_version(self) -> str:
        return "github_adapter_v1"

    # ── File loading ────────────────────────────────────────────────────

    def _load_records(self, path: str):
        """Load records from a CSV or JSON file.

        Returns (records, errors) where records is a list of dicts.
        """
        p = Path(path)
        if not p.exists():
            return [], [f"File not found: {p}"]

        suffix = p.suffix.lower()
        if suffix == ".json":
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
        else:
            # Default: treat as CSV.
            rows: List[dict] = []
            with open(p, newline="") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    return [], ["Empty CSV or no header"]
                for row in reader:
                    rows.append(row)
            return rows, []

    # ── Timestamp parsing ───────────────────────────────────────────────

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

    # ── Standard ingest (observations only) ─────────────────────────────

    def ingest(self, path: str) -> IngestResult:
        records, load_errors = self._load_records(path)
        if load_errors:
            return IngestResult(source=self.name, observations=[], errors=load_errors)

        observations: List = []
        errors: List[str] = []
        warnings: List[str] = []
        estimated_count = 0

        for i, rec in enumerate(records):
            try:
                operator_id = rec.get("operator_id") or rec.get("user_id") or rec.get("user") or rec.get("developer")
                if not operator_id:
                    errors.append(f"Record {i}: missing operator_id/user_id")
                    continue

                timestamp = rec.get("timestamp") or rec.get("date") or rec.get("day") or rec.get("created_at")
                if not timestamp:
                    errors.append(f"Record {i}: missing timestamp/date")
                    continue

                # Token counts — may be directly provided or estimated.
                I = rec.get("input_tokens") or rec.get("prompt_tokens")
                O = rec.get("output_tokens") or rec.get("completion_tokens")

                lines_accepted = int(rec.get("lines_accepted") or rec.get("lines_acceptance") or 0)
                suggestions_shown = int(rec.get("suggestions_shown") or rec.get("suggestions") or 0)

                if I is None or O is None:
                    estimated_count += 1
                    if O is None:
                        O = lines_accepted * TOKENS_PER_LINE_ACCEPTED
                    if I is None:
                        I = suggestions_shown * TOKENS_PER_SUGGESTION_SHOWN

                I = int(I or 0)
                O = int(O or 0)

                session_id = rec.get("session_id") or rec.get("session")
                model = rec.get("model")

                obs = self._make_observation(
                    operator_id=str(operator_id),
                    timestamp_str=str(timestamp),
                    I=I, O=O, R=0, W=0,
                    synthetic=False,
                    platform="copilot",
                    model=model,
                    session_id=session_id,
                    provenance="ingest:github-copilot",
                    source_confidence=rec.get("source_confidence"),
                    raw_source_reference=rec.get("raw_source_reference"),
                )
                observations.append(obs)
            except Exception as e:
                errors.append(f"Record {i}: {e}")

        if estimated_count > 0:
            warnings.append(
                f"{estimated_count} records had no token fields (estimated from lines/suggestions)"
            )

        return IngestResult(
            source=self.name,
            observations=observations,
            errors=errors,
            warnings=warnings,
        )

    # ── Full ingest: canonical objects ──────────────────────────────────

    _TENANT_ID = "default"
    _SYSTEM_ID = "copilot"

    def ingest_full(self, path: str) -> IngestResult:
        """Full ingest: emit Observations + all canonical objects.

        Produces System, SystemVersion, Session, and Artifact objects
        in addition to the Observations from the standard ingest path.
        """
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
            name="GitHub Copilot",
            system_type="ai_platform",
            vendor="GitHub",
        )

        # ── SystemVersion ───────────────────────────────────────────────
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

        # Default version if no model fields present.
        default_label = "copilot-business"
        if not system_versions:
            version_id = f"{self._SYSTEM_ID}:{default_label}"
            seen_models[default_label] = version_id
            system_versions.append(self._make_system_version(
                version_id=version_id,
                system_id=self._SYSTEM_ID,
                version_label=default_label,
            ))

        # ── Sessions per user-day ───────────────────────────────────────
        sessions: List = []
        session_meta: dict = {}  # session_key -> {operator_id, start_time, model}

        for rec in records:
            operator_id = rec.get("operator_id") or rec.get("user_id") or rec.get("user") or rec.get("developer")
            if not operator_id:
                continue
            timestamp = rec.get("timestamp") or rec.get("date") or rec.get("day") or rec.get("created_at")
            if not timestamp:
                continue
            try:
                dt = self._parse_ts(str(timestamp))
            except Exception:
                continue

            # Use explicit session_id if present, otherwise derive user-day key.
            explicit_sid = rec.get("session_id") or rec.get("session")
            if explicit_sid:
                sid = explicit_sid
            else:
                day_str = dt.strftime("%Y%m%d")
                sid = f"copilot:{operator_id}:{day_str}"

            model = rec.get("model")
            if sid not in session_meta or dt < session_meta[sid]["start_time"]:
                session_meta[sid] = {
                    "operator_id": str(operator_id),
                    "start_time": dt,
                    "model": model,
                }

        for sid, meta in session_meta.items():
            version_id = seen_models.get(meta["model"]) if meta["model"] else seen_models.get(default_label)
            sessions.append(self._make_session(
                session_id=sid,
                operator_id=meta["operator_id"],
                system_id=self._SYSTEM_ID,
                start_time=meta["start_time"],
                system_version_id=version_id,
            ))

        # ── Artifacts from accepted suggestions ─────────────────────────
        artifacts: List = []
        for i, rec in enumerate(records):
            operator_id = rec.get("operator_id") or rec.get("user_id") or rec.get("user") or rec.get("developer")
            if not operator_id:
                continue
            lines_accepted = int(rec.get("lines_accepted") or rec.get("lines_acceptance") or 0)
            if lines_accepted <= 0:
                continue
            timestamp = rec.get("timestamp") or rec.get("date") or rec.get("day") or rec.get("created_at")
            created_dt = None
            if timestamp:
                try:
                    created_dt = self._parse_ts(str(timestamp))
                except Exception:
                    created_dt = None

            repo = rec.get("repo") or rec.get("repository")
            language = rec.get("language") or rec.get("lang")
            file_path = None
            if repo and language:
                file_path = f"{repo}/*.{language}"
            elif repo:
                file_path = f"{repo}/*"

            artifact_id = f"copilot_art_{operator_id}_{i}"
            artifacts.append(self._make_artifact(
                artifact_id=artifact_id,
                operator_id=str(operator_id),
                artifact_type="code_file",
                file_path=file_path,
                lines_added=lines_accepted,
                created_at=created_dt,
            ))

        return IngestResult(
            source=self.name,
            observations=base_result.observations,
            errors=base_result.errors,
            warnings=warnings,
            systems=[system],
            system_versions=system_versions,
            sessions=sessions,
            artifacts=artifacts,
        )
