"""Artifact — a concrete output of AI-assisted work.

Per `03_CONNECTION_INGESTION.md` §5.6 Object 13: A tangible output produced by
a transformation — a code file, a document, a config, a test file. Artifacts
are the traceable products of operator-system interaction. Content is NOT
stored — only metadata about the artifact's existence, type, and relationship
to the transformation that produced it.

Required fields: artifact_id, operator_id, artifact_type, synthetic.
Optional fields: observation_id, file_path, lines_added, lines_removed,
commit_sha, created_at.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ArtifactType(str, Enum):
    """Artifact types per `03` §5.6 Object 13."""
    CODE_FILE = "code_file"
    DOCUMENT = "document"
    CONFIG = "config"
    TEST_FILE = "test_file"
    DESIGN_DOC = "design_doc"
    DATA_FILE = "data_file"
    SCRIPT = "script"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Artifact:
    """A concrete output of AI-assisted work.

    The `observation_id` field links back to the interaction (observation)
    that produced this artifact.

    The `synthetic` flag must survive import/export.
    """
    artifact_id: str
    operator_id: str
    artifact_type: ArtifactType
    synthetic: bool = False
    observation_id: Optional[str] = None
    file_path: Optional[str] = None
    lines_added: Optional[int] = None
    lines_removed: Optional[int] = None
    commit_sha: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        # Normalize naive datetimes to UTC for consistent serialization.
        if self.created_at is not None and self.created_at.tzinfo is None:
            object.__setattr__(
                self, "created_at",
                self.created_at.replace(tzinfo=timezone.utc),
            )

    def to_dict(self) -> dict:
        return {
            "artifact_id": self.artifact_id,
            "operator_id": self.operator_id,
            "artifact_type": self.artifact_type.value,
            "synthetic": self.synthetic,
            "observation_id": self.observation_id,
            "file_path": self.file_path,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "commit_sha": self.commit_sha,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Artifact":
        created = d.get("created_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created.replace("Z", "+00:00"))
        artifact_type = d["artifact_type"]
        if isinstance(artifact_type, str):
            artifact_type = ArtifactType(artifact_type)
        return cls(
            artifact_id=d["artifact_id"],
            operator_id=d["operator_id"],
            artifact_type=artifact_type,
            synthetic=bool(d["synthetic"]),
            observation_id=d.get("observation_id"),
            file_path=d.get("file_path"),
            lines_added=d.get("lines_added"),
            lines_removed=d.get("lines_removed"),
            commit_sha=d.get("commit_sha"),
            created_at=created,
        )
