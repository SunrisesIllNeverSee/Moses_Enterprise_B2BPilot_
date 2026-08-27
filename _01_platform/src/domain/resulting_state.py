"""ResultingState — the state of the operator's work context after an interaction.

Per `03_CONNECTION_INGESTION.md` §5.6 Object 11: Captures what changed as a
result of the interaction — new context written, artifacts produced, state
transitions.

Required fields: state_id, session_id, task_id, operator_id, synthetic.
Optional fields: state_hash, context_summary, artifact_ids, timestamp.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass(frozen=True, slots=True)
class ResultingState:
    """The state after an operator action and system response.

    The `synthetic` flag must survive import/export.
    """
    state_id: str
    session_id: str
    task_id: str
    operator_id: str
    synthetic: bool = False
    state_hash: Optional[str] = None
    context_summary: Optional[str] = None
    artifact_ids: List[str] = field(default_factory=list)
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        # Normalize naive datetimes to UTC for consistent serialization.
        if self.timestamp is not None and self.timestamp.tzinfo is None:
            object.__setattr__(
                self, "timestamp",
                self.timestamp.replace(tzinfo=timezone.utc),
            )

    def to_dict(self) -> dict:
        return {
            "state_id": self.state_id,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "operator_id": self.operator_id,
            "synthetic": self.synthetic,
            "state_hash": self.state_hash,
            "context_summary": self.context_summary,
            "artifact_ids": list(self.artifact_ids),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ResultingState":
        ts = d.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return cls(
            state_id=d["state_id"],
            session_id=d["session_id"],
            task_id=d["task_id"],
            operator_id=d["operator_id"],
            synthetic=bool(d["synthetic"]),
            state_hash=d.get("state_hash"),
            context_summary=d.get("context_summary"),
            artifact_ids=list(d.get("artifact_ids", [])),
            timestamp=ts,
        )
