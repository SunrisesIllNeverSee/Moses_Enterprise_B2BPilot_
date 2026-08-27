"""SystemAction — what the AI system did in response to the operator's action.

Per `03_CONNECTION_INGESTION.md` §5.6 Object 10: The system's contribution —
the model response, the tool execution, the agent step.

Required fields: action_id, system_id, session_id, task_id, response_type,
timestamp, synthetic.
Optional fields: system_version_id, response_summary, token_output.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ResponseType(str, Enum):
    """System response types per `03` §5.6 Object 10."""
    GENERATE = "generate"
    COMPLETE = "complete"
    REFUSE = "refuse"
    ERROR = "error"
    PARTIAL = "partial"


@dataclass(frozen=True, slots=True)
class SystemAction:
    """What the AI system did in response to an operator action.

    The `synthetic` flag must survive import/export.
    """
    action_id: str
    system_id: str
    session_id: str
    task_id: str
    response_type: ResponseType
    timestamp: datetime
    synthetic: bool = False
    system_version_id: Optional[str] = None
    response_summary: Optional[str] = None
    token_output: Optional[int] = None

    def __post_init__(self) -> None:
        # Normalize naive datetimes to UTC for consistent serialization.
        if self.timestamp.tzinfo is None:
            object.__setattr__(
                self, "timestamp",
                self.timestamp.replace(tzinfo=timezone.utc),
            )

    def to_dict(self) -> dict:
        return {
            "action_id": self.action_id,
            "system_id": self.system_id,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "response_type": self.response_type.value,
            "timestamp": self.timestamp.isoformat(),
            "synthetic": self.synthetic,
            "system_version_id": self.system_version_id,
            "response_summary": self.response_summary,
            "token_output": self.token_output,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SystemAction":
        ts = d["timestamp"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        response_type = d["response_type"]
        if isinstance(response_type, str):
            response_type = ResponseType(response_type)
        return cls(
            action_id=d["action_id"],
            system_id=d["system_id"],
            session_id=d["session_id"],
            task_id=d["task_id"],
            response_type=response_type,
            timestamp=ts,
            synthetic=bool(d["synthetic"]),
            system_version_id=d.get("system_version_id"),
            response_summary=d.get("response_summary"),
            token_output=d.get("token_output"),
        )
