"""Base classes for ingest adapters.

Every adapter inherits from IngestAdapter and implements `ingest(path)`.
The adapter normalizes provider-specific telemetry into canonical
Observation objects. Adapters do NOT compute metrics — that's the engine's job.
"""
from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.observation import Observation


@dataclass(frozen=True, slots=True)
class IngestResult:
    """Result of an ingest operation."""
    source: str               # adapter name (e.g. "fixture", "claude", "codex")
    observations: List[Observation]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    # Canonical objects emitted by full-ingest mode (ingest_full).
    systems: List = field(default_factory=list)         # List[System]
    system_versions: List = field(default_factory=list) # List[SystemVersion]
    sessions: List = field(default_factory=list)        # List[Session]
    tasks: List = field(default_factory=list)           # List[Task]
    artifacts: List = field(default_factory=list)       # List[Artifact]
    lineages: List = field(default_factory=list)        # List[Lineage]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    @property
    def count(self) -> int:
        return len(self.observations)

    def canonical_object_count(self) -> int:
        """Total number of canonical objects (excluding observations)."""
        return (
            len(self.systems)
            + len(self.system_versions)
            + len(self.sessions)
            + len(self.tasks)
            + len(self.artifacts)
            + len(self.lineages)
        )

    def total_object_count(self) -> int:
        """Total number of all objects including observations."""
        return len(self.observations) + self.canonical_object_count()


class IngestAdapter(ABC):
    """Base class for all ingest adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter name (e.g. 'claude', 'codex', 'fixture')."""
        ...

    @abstractmethod
    def ingest(self, path: str) -> IngestResult:
        """Read provider data from `path` and return normalized Observations."""
        ...

    def ingest_full(self, path: str) -> IngestResult:
        """Full ingest: emit all canonical objects, not just observations.

        Default implementation calls ingest() and returns the result.
        Override in subclasses that support full canonical object emission.
        """
        return self.ingest(path)

    # ── Canonical object builders ───────────────────────────────────────

    def _make_system(self, system_id, tenant_id, name, system_type, synthetic=False, vendor=None, active=True):
        """Build a System canonical object."""
        from domain import System, SystemType
        if isinstance(system_type, str):
            system_type = SystemType(system_type)
        return System(
            system_id=system_id,
            tenant_id=tenant_id,
            name=name,
            system_type=system_type,
            synthetic=synthetic,
            vendor=vendor,
            active=active,
        )

    def _make_system_version(self, version_id, system_id, version_label, synthetic=False, **kwargs):
        """Build a SystemVersion canonical object."""
        from domain import SystemVersion
        return SystemVersion(
            version_id=version_id,
            system_id=system_id,
            version_label=version_label,
            synthetic=synthetic,
            **kwargs,
        )

    def _make_session(self, session_id, operator_id, system_id, start_time, synthetic=False, **kwargs):
        """Build a Session canonical object."""
        from domain import Session
        return Session(
            session_id=session_id,
            operator_id=operator_id,
            system_id=system_id,
            start_time=start_time,
            synthetic=synthetic,
            **kwargs,
        )

    def _make_task(self, task_id, operator_id, intent_label, task_type, created_at, synthetic=False, **kwargs):
        """Build a Task canonical object."""
        from domain import Task, TaskType
        if isinstance(task_type, str):
            task_type = TaskType(task_type)
        return Task(
            task_id=task_id,
            operator_id=operator_id,
            intent_label=intent_label,
            task_type=task_type,
            created_at=created_at,
            synthetic=synthetic,
            **kwargs,
        )

    def _make_artifact(self, artifact_id, operator_id, artifact_type, synthetic=False, **kwargs):
        """Build an Artifact canonical object."""
        from domain import Artifact, ArtifactType
        if isinstance(artifact_type, str):
            artifact_type = ArtifactType(artifact_type)
        return Artifact(
            artifact_id=artifact_id,
            operator_id=operator_id,
            artifact_type=artifact_type,
            synthetic=synthetic,
            **kwargs,
        )

    def _make_observation(
        self,
        operator_id: str,
        timestamp_str: str,
        I: int, O: int, R: int, W: int,
        synthetic: bool = False,
        platform: Optional[str] = None,
        model: Optional[str] = None,
        session_id: Optional[str] = None,
        provenance: Optional[str] = None,
        obs_id: Optional[str] = None,
        source_confidence: Optional[str] = None,
        raw_source_reference: Optional[str] = None,
        collection_method: Optional[str] = None,
        collector_version: Optional[str] = None,
        original_time_window: Optional[tuple] = None,
        signature_checksum: Optional[str] = None,
    ) -> Observation:
        """Helper to build an Observation with a generated ID if not provided.

        Populates structured provenance per `12` §Provenance. The
        `source_provider` defaults to `ingest:{name}`; `collection_method`
        and `collector_version` are set when provided. The ingestion
        timestamp is always set to now (UTC ISO 8601).
        """
        from datetime import datetime, timezone
        from domain.provenance import Provenance
        # Parse timestamp — accept ISO 8601 or date-only.
        ts = timestamp_str
        if isinstance(ts, str):
            if "T" in ts:
                ts = ts.replace("Z", "+00:00")
                ts = datetime.fromisoformat(ts)
            else:
                ts = datetime.fromisoformat(ts + "T12:00:00+00:00")
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        if obs_id is None:
            obs_id = f"{operator_id}_{ts.strftime('%Y%m%d%H%M%S')}"

        # Build structured provenance. A bare string provenance is treated as
        # source_provider; otherwise default to ingest:{name}.
        if provenance is None:
            source_provider = f"ingest:{self.name}"
        elif isinstance(provenance, str):
            source_provider = provenance
        else:
            source_provider = str(provenance)

        prov = Provenance(
            source_provider=source_provider,
            collection_method=collection_method or self._default_collection_method(),
            collector_version=collector_version or self._default_collector_version(),
            ingestion_timestamp=datetime.now(timezone.utc).isoformat(),
            original_time_window=original_time_window,
            signature_checksum=signature_checksum,
            synthetic=synthetic,
        )

        return Observation(
            observation_id=obs_id,
            operator_id=operator_id,
            timestamp=ts,
            input_tokens=max(0, I),
            output_tokens=max(0, O),
            cache_read_tokens=max(0, R),
            cache_write_tokens=max(0, W),
            synthetic=synthetic,
            platform=platform,
            model=model,
            session_id=session_id,
            provenance=prov,
            source_confidence=source_confidence,
            raw_source_reference=raw_source_reference,
        )

    def _default_collection_method(self) -> str:
        """Default collection method for this adapter (override in subclasses)."""
        return "file_export"

    def _default_collector_version(self) -> str:
        """Default collector version for this adapter (override in subclasses)."""
        return "ingest_v1"
