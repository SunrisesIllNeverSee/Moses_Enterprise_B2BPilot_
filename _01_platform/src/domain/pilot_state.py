"""PilotState — the canonical state machine for an Upsilon Enterprise Pilot.

Per `pilot/governance/PILOT_STATE_MACHINE.md`: every pilot transitions
through these states. No state may be skipped. Transitions are gated by
the decision gates defined in `pilot/governance/DECISION_GATES.md`.

The state machine is distinct from operator-level routing gates
(`production_gate.py`). Pilot-level gates govern the pilot lifecycle;
operator-level gates route individual operators to coaching/review.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Tuple


class PilotState(str, Enum):
    """The canonical lifecycle states for an enterprise pilot."""
    DEFINED = "DEFINED"
    INSTRUMENTED = "INSTRUMENTED"
    BASELINED = "BASELINED"
    DIAGNOSED = "DIAGNOSED"
    INTERVENING = "INTERVENING"
    VERIFYING = "VERIFYING"
    READOUT = "READOUT"
    DECIDING = "DECIDING"
    TERMINATED = "TERMINATED"


# Canonical forward transitions: (from_state, to_state, gate_label)
# Gate labels indicate which pilot-level decision gate (if any) authorizes
# the transition. "—" means no gate required (automatic on artifact completion).
_VALID_TRANSITIONS: List[Tuple[PilotState, PilotState, str]] = [
    (PilotState.DEFINED, PilotState.INSTRUMENTED, "—"),
    (PilotState.INSTRUMENTED, PilotState.BASELINED, "—"),
    (PilotState.BASELINED, PilotState.DIAGNOSED, "—"),
    (PilotState.DIAGNOSED, PilotState.INTERVENING, "Gate 2: CONTINUE"),
    (PilotState.INTERVENING, PilotState.VERIFYING, "Gate 2: CONTINUE"),
    (PilotState.VERIFYING, PilotState.READOUT, "—"),
    (PilotState.READOUT, PilotState.DECIDING, "—"),
    (PilotState.DECIDING, PilotState.TERMINATED, "Gate 3: STOP/DEPLOY"),
    # Gate 3: EXTEND returns to INSTRUMENTED with a new window
    (PilotState.DECIDING, PilotState.INSTRUMENTED, "Gate 3: EXTEND"),
    # Gate 2: ADJUST returns to INTERVENING with adjusted protocol
    (PilotState.INTERVENING, PilotState.INTERVENING, "Gate 2: ADJUST"),
    # Gate 2: TERMINATE jumps to DECIDING (premature closure)
    (PilotState.INTERVENING, PilotState.DECIDING, "Gate 2: TERMINATE"),
]

# The canonical ordered sequence (for lifecycle display).
_STAGE_ORDER: List[PilotState] = [
    PilotState.DEFINED,
    PilotState.INSTRUMENTED,
    PilotState.BASELINED,
    PilotState.DIAGNOSED,
    PilotState.INTERVENING,
    PilotState.VERIFYING,
    PilotState.READOUT,
    PilotState.DECIDING,
    PilotState.TERMINATED,
]


@dataclass(frozen=True, slots=True)
class StageTransition:
    """A recorded state transition in the pilot lifecycle."""
    from_state: PilotState
    to_state: PilotState
    timestamp: str
    gate_label: str
    rationale: str

    def to_dict(self) -> dict:
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "timestamp": self.timestamp,
            "gate_label": self.gate_label,
            "rationale": self.rationale,
        }


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


@dataclass
class PilotStateMachine:
    """Tracks the current state of a pilot and enforces valid transitions.

    This is a mutable object — the state changes over the pilot lifecycle.
    The transition history is append-only and provides an audit trail.
    """
    pilot_id: str
    current_state: PilotState = PilotState.DEFINED
    _history: List[StageTransition] = field(default_factory=list)

    def can_transition_to(self, target: PilotState) -> bool:
        """Check whether a transition to the target state is valid."""
        return any(
            frm == self.current_state and to == target
            for frm, to, _ in _VALID_TRANSITIONS
        )

    def transition_to(
        self,
        target: PilotState,
        gate_label: str = "",
        rationale: str = "",
    ) -> StageTransition:
        """Transition to the target state.

        Raises InvalidTransitionError if the transition is not valid.
        Records the transition in the history.
        """
        valid = self.can_transition_to(target)
        if not valid:
            raise InvalidTransitionError(
                f"Cannot transition from {self.current_state.value} to {target.value}. "
                f"Valid transitions from {self.current_state.value}: "
                f"{[t.value for f, t, _ in _VALID_TRANSITIONS if f == self.current_state]}"
            )
        # Find the canonical gate label for this transition
        canonical_gate = gate_label
        if not canonical_gate:
            for frm, to, g in _VALID_TRANSITIONS:
                if frm == self.current_state and to == target:
                    canonical_gate = g
                    break
        ts = datetime.now(timezone.utc).isoformat()
        record = StageTransition(
            from_state=self.current_state,
            to_state=target,
            timestamp=ts,
            gate_label=canonical_gate,
            rationale=rationale,
        )
        self._history.append(record)
        self.current_state = target
        return record

    @property
    def history(self) -> List[StageTransition]:
        """The append-only transition history."""
        return list(self._history)

    def lifecycle_display(self) -> List[dict]:
        """Return the lifecycle display: ✓/→/○ for each stage."""
        current_idx = _STAGE_ORDER.index(self.current_state)
        result = []
        for i, stage in enumerate(_STAGE_ORDER):
            if i < current_idx:
                marker = "✓"
                status = "complete"
            elif i == current_idx:
                marker = "→"
                status = "current"
            else:
                marker = "○"
                status = "pending"
            result.append({
                "stage": stage.value,
                "marker": marker,
                "status": status,
            })
        return result

    def to_dict(self) -> dict:
        return {
            "pilot_id": self.pilot_id,
            "current_state": self.current_state.value,
            "history": [t.to_dict() for t in self._history],
            "lifecycle_display": self.lifecycle_display(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PilotStateMachine":
        sm = cls(
            pilot_id=d["pilot_id"],
            current_state=PilotState(d.get("current_state", "DEFINED")),
        )
        for t in d.get("history", []):
            sm._history.append(StageTransition(
                from_state=PilotState(t["from_state"]),
                to_state=PilotState(t["to_state"]),
                timestamp=t["timestamp"],
                gate_label=t.get("gate_label", ""),
                rationale=t.get("rationale", ""),
            ))
        return sm


def stage_order() -> List[PilotState]:
    """Return the canonical ordered list of pilot stages."""
    return list(_STAGE_ORDER)


def valid_transitions() -> List[Tuple[PilotState, PilotState, str]]:
    """Return the canonical transition table."""
    return list(_VALID_TRANSITIONS)
