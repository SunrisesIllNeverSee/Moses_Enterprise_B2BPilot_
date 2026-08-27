"""Transformation — the delta between prior and resulting state.

Per `03_CONNECTION_INGESTION.md` §5.6 Object 12: The change produced by an
interaction — how the operator's input and the system's output transformed
the work state. This is the framework's central analytical unit: it captures
the BI (before-input) → AAI (AI-assisted action) → committed state → outcome
chain from §16 Graphic 5.

Required fields: transformation_id, session_id, task_id, operator_id,
transformation_type, synthetic.
Optional fields: prior_state_id, resulting_state_id, artifact_id, micro_eval.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TransformationType(str, Enum):
    """Transformation types per `03` §5.6 Object 12."""
    CREATION = "creation"
    MODIFICATION = "modification"
    REFINEMENT = "refinement"
    REDIRECTION = "redirection"
    EXTENSION = "extension"
    COMMIT = "commit"


@dataclass(frozen=True, slots=True)
class Transformation:
    """The delta between prior and resulting state.

    The `micro_eval` dict carries the transformation-level micro-evaluation
    scores: leverage, yield, token_snr, construction, upsilon.

    The `synthetic` flag must survive import/export.
    """
    transformation_id: str
    session_id: str
    task_id: str
    operator_id: str
    transformation_type: TransformationType
    synthetic: bool = False
    prior_state_id: Optional[str] = None
    resulting_state_id: Optional[str] = None
    artifact_id: Optional[str] = None
    micro_eval: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "transformation_id": self.transformation_id,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "operator_id": self.operator_id,
            "transformation_type": self.transformation_type.value,
            "synthetic": self.synthetic,
            "prior_state_id": self.prior_state_id,
            "resulting_state_id": self.resulting_state_id,
            "artifact_id": self.artifact_id,
            "micro_eval": dict(self.micro_eval),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Transformation":
        transformation_type = d["transformation_type"]
        if isinstance(transformation_type, str):
            transformation_type = TransformationType(transformation_type)
        return cls(
            transformation_id=d["transformation_id"],
            session_id=d["session_id"],
            task_id=d["task_id"],
            operator_id=d["operator_id"],
            transformation_type=transformation_type,
            synthetic=bool(d["synthetic"]),
            prior_state_id=d.get("prior_state_id"),
            resulting_state_id=d.get("resulting_state_id"),
            artifact_id=d.get("artifact_id"),
            micro_eval=dict(d.get("micro_eval", {})),
        )
