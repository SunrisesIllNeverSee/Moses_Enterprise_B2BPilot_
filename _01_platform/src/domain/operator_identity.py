"""OperatorIdentity — cross-system identity mapping for operators.

Per Jaimie's product review (Gap 5): "Cross-system identity is only partial.
Need a robust way to map operators across platforms."

A single logical operator may appear under different system-specific
identities across platforms (e.g. operator "alice" might be
"alice@company.com" in ChatGPT, "alice_chen" in Claude, "achen" in
Copilot). The OperatorIdentity registry maps these system-specific IDs
back to a single canonical operator ID so that telemetry from multiple
platforms can be attributed correctly.

Governance guardrails (per `12`):
- Identity mapping is for telemetry attribution, NOT for personnel
  surveillance. The canonical operator ID is the pseudonymous handle
  already used throughout the platform.
- Conflict detection prevents silent mis-attribution: if the same
  system-specific ID is mapped to two different canonical operators,
  an IdentityConflictError is raised rather than silently overwriting.
- No real names are stored; system-specific IDs are opaque handles.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


class IdentityConflictError(ValueError):
    """Raised when a system-specific ID maps to two different canonical operators.

    Per Gap 5: "Handles conflicts (same system-specific ID mapped to
    different canonical operators)." Rather than silently overwriting,
    the registry raises so the caller can resolve the conflict
    explicitly (e.g. by correcting a stale mapping or splitting the ID).
    """

    def __init__(
        self,
        system: str,
        system_id: str,
        existing_canonical: str,
        new_canonical: str,
    ) -> None:
        super().__init__(
            f"Identity conflict for {system}:{system_id!r} — "
            f"already mapped to canonical operator {existing_canonical!r}, "
            f"cannot remap to {new_canonical!r}. Resolve the conflict "
            f"explicitly before adding this mapping."
        )
        self.system = system
        self.system_id = system_id
        self.existing_canonical = existing_canonical
        self.new_canonical = new_canonical


@dataclass
class OperatorIdentity:
    """Cross-system identity registry for a cohort.

    Maps a single canonical operator ID to one or more system-specific
    identities, and supports reverse resolution: given a (system,
    system_id) pair, resolve back to the canonical operator.

    This is a mutable registry (not a frozen value object) because
    identity mappings are added incrementally as telemetry from new
    platforms is ingested.

    Attributes:
        canonical_to_systems: canonical_id → {system → system_id}.
        system_to_canonical: (system, system_id) → canonical_id
            (reverse index for fast resolution).
    """
    canonical_to_systems: Dict[str, Dict[str, str]] = field(default_factory=dict)
    system_to_canonical: Dict[Tuple[str, str], str] = field(default_factory=dict)

    def add_mapping(
        self,
        canonical_operator_id: str,
        system: str,
        system_id: str,
    ) -> None:
        """Add a system-specific identity mapping for a canonical operator.

        Args:
            canonical_operator_id: The canonical operator ID (pseudonym).
            system: The platform/system name (e.g. "chatgpt", "claude").
            system_id: The system-specific identity handle.

        Raises:
            IdentityConflictError: If (system, system_id) is already
                mapped to a *different* canonical operator. Re-mapping
                to the same canonical operator is idempotent (no error).
        """
        key = (system, system_id)
        existing = self.system_to_canonical.get(key)
        if existing is not None and existing != canonical_operator_id:
            raise IdentityConflictError(
                system=system,
                system_id=system_id,
                existing_canonical=existing,
                new_canonical=canonical_operator_id,
            )
        self.system_to_canonical[key] = canonical_operator_id
        self.canonical_to_systems.setdefault(canonical_operator_id, {})[system] = system_id

    def resolve(
        self,
        system: str,
        system_id: str,
    ) -> Optional[str]:
        """Resolve a (system, system_id) pair to the canonical operator ID.

        Returns None if no mapping exists for this pair.
        """
        return self.system_to_canonical.get((system, system_id))

    def systems_for(self, canonical_operator_id: str) -> Dict[str, str]:
        """Return all system-specific identities for a canonical operator.

        Returns a dict of {system → system_id}. Empty dict if the
        canonical operator has no registered mappings.
        """
        return dict(self.canonical_to_systems.get(canonical_operator_id, {}))

    def canonical_ids(self) -> list:
        """Return all canonical operator IDs known to this registry."""
        return list(self.canonical_to_systems.keys())

    def has_conflict(self, canonical_operator_id: str, system: str, system_id: str) -> bool:
        """Check whether adding a mapping would cause a conflict.

        Returns True if (system, system_id) is already mapped to a
        different canonical operator.
        """
        key = (system, system_id)
        existing = self.system_to_canonical.get(key)
        return existing is not None and existing != canonical_operator_id

    def to_dict(self) -> dict:
        """Serialize the registry for persistence/export."""
        return {
            "canonical_to_systems": {
                cid: dict(sys_map)
                for cid, sys_map in self.canonical_to_systems.items()
            },
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OperatorIdentity":
        """Rebuild the registry from a serialized dict (rebuilds the reverse index)."""
        reg = cls()
        for cid, sys_map in d.get("canonical_to_systems", {}).items():
            for system, system_id in sys_map.items():
                reg.add_mapping(cid, system, system_id)
        return reg
