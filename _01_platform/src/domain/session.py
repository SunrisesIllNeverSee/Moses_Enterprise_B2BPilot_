"""Session — a contiguous period of operator interaction with a system.

Per `03_CONNECTION_INGESTION.md` §5.6 Object 4: Sessions group interactions
into meaningful units (e.g. a coding session, a chat conversation, an agent
run).

Required fields: session_id, operator_id, system_id, start_time, synthetic.
Optional fields: end_time, duration_seconds, system_version_id, task_id,
workflow_id, workflow_stage_id.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True, slots=True)
class Session:
    """A contiguous operator interaction period.

    The `synthetic` flag must survive import/export.
    """
    session_id: str
    operator_id: str
    system_id: str
    start_time: datetime
    synthetic: bool = False
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    system_version_id: Optional[str] = None
    task_id: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow_stage_id: Optional[str] = None

    def __post_init__(self) -> None:
        # Normalize naive datetimes to UTC for consistent serialization.
        if self.start_time.tzinfo is None:
            object.__setattr__(
                self, "start_time",
                self.start_time.replace(tzinfo=timezone.utc),
            )
        if self.end_time is not None and self.end_time.tzinfo is None:
            object.__setattr__(
                self, "end_time",
                self.end_time.replace(tzinfo=timezone.utc),
            )

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "operator_id": self.operator_id,
            "system_id": self.system_id,
            "start_time": self.start_time.isoformat(),
            "synthetic": self.synthetic,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "system_version_id": self.system_version_id,
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "workflow_stage_id": self.workflow_stage_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Session":
        start = d["start_time"]
        if isinstance(start, str):
            start = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end = d.get("end_time")
        if isinstance(end, str):
            end = datetime.fromisoformat(end.replace("Z", "+00:00"))
        return cls(
            session_id=d["session_id"],
            operator_id=d["operator_id"],
            system_id=d["system_id"],
            start_time=start,
            synthetic=bool(d["synthetic"]),
            end_time=end,
            duration_seconds=d.get("duration_seconds"),
            system_version_id=d.get("system_version_id"),
            task_id=d.get("task_id"),
            workflow_id=d.get("workflow_id"),
            workflow_stage_id=d.get("workflow_stage_id"),
        )
