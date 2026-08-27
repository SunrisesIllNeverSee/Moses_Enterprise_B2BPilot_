"""Task — a unit of intent declared or inferred by an operator.

Per `03_CONNECTION_INGESTION.md` §5.6 Object 5: The operator's declared or
inferred goal for a session or interaction. Represents what the operator was
trying to accomplish.

Required fields: task_id, operator_id, intent_label, task_type, created_at,
synthetic.
Optional fields: workflow_id, workflow_stage_id, description.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class TaskType(str, Enum):
    """Categorized intent per `03` §5.6 Object 5."""
    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    REVIEW = "review"
    RESEARCH = "research"
    PLANNING = "planning"


@dataclass(frozen=True, slots=True)
class Task:
    """A unit of operator intent.

    The `synthetic` flag must survive import/export.
    """
    task_id: str
    operator_id: str
    intent_label: str
    task_type: TaskType
    created_at: datetime
    synthetic: bool = False
    workflow_id: Optional[str] = None
    workflow_stage_id: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self) -> None:
        # Normalize naive datetimes to UTC for consistent serialization.
        if self.created_at.tzinfo is None:
            object.__setattr__(
                self, "created_at",
                self.created_at.replace(tzinfo=timezone.utc),
            )

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "operator_id": self.operator_id,
            "intent_label": self.intent_label,
            "task_type": self.task_type.value,
            "created_at": self.created_at.isoformat(),
            "synthetic": self.synthetic,
            "workflow_id": self.workflow_id,
            "workflow_stage_id": self.workflow_stage_id,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        created = d["created_at"]
        if isinstance(created, str):
            created = datetime.fromisoformat(created.replace("Z", "+00:00"))
        task_type = d["task_type"]
        if isinstance(task_type, str):
            task_type = TaskType(task_type)
        return cls(
            task_id=d["task_id"],
            operator_id=d["operator_id"],
            intent_label=d["intent_label"],
            task_type=task_type,
            created_at=created,
            synthetic=bool(d["synthetic"]),
            workflow_id=d.get("workflow_id"),
            workflow_stage_id=d.get("workflow_stage_id"),
            description=d.get("description"),
        )
