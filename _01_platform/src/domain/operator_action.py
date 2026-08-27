"""OperatorAction — what the operator did to initiate or redirect an interaction.

Per `03_CONNECTION_INGESTION.md` §5.6 Object 9: The operator's contribution to
the interaction — the prompt formulation, the tool selection, the context
provision, the redirection.

Required fields: action_id, operator_id, session_id, task_id, action_type,
timestamp, synthetic.
Optional fields: action_summary, token_cost.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ActionType(str, Enum):
    """Operator action types per `03` §5.6 Object 9."""
    PROMPT = "prompt"
    REDIRECT = "redirect"
    REFINE = "refine"
    ACCEPT = "accept"
    REJECT = "reject"
    RETRY = "retry"
    ABORT = "abort"
    COMMIT = "commit"


@dataclass(frozen=True, slots=True)
class OperatorAction:
    """What the operator did during an interaction.

    The `synthetic` flag must survive import/export.
    """
    action_id: str
    operator_id: str
    session_id: str
    task_id: str
    action_type: ActionType
    timestamp: datetime
    synthetic: bool = False
    action_summary: Optional[str] = None
    token_cost: Optional[int] = None

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
            "operator_id": self.operator_id,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "action_type": self.action_type.value,
            "timestamp": self.timestamp.isoformat(),
            "synthetic": self.synthetic,
            "action_summary": self.action_summary,
            "token_cost": self.token_cost,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OperatorAction":
        ts = d["timestamp"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        action_type = d["action_type"]
        if isinstance(action_type, str):
            action_type = ActionType(action_type)
        return cls(
            action_id=d["action_id"],
            operator_id=d["operator_id"],
            session_id=d["session_id"],
            task_id=d["task_id"],
            action_type=action_type,
            timestamp=ts,
            synthetic=bool(d["synthetic"]),
            action_summary=d.get("action_summary"),
            token_cost=d.get("token_cost"),
        )
