"""Tool registration gate (HRN-008 governance).

The governance layer gates tool *invocation* via the existing enforcement
module. This module gates tool *registration* — the act of adding a new
tool to the pilot's allowed catalog. Without this, a new tool added to
the ecosystem is automatically trusted; governance must gate registration,
not just invocation (HRN-008: "gate tool registration, not just tool
invocation").

Every tool used by the pilot must be registered with:
    - tool_id: unique identifier
    - description: what the tool does
    - data_classes: what data classes it touches (telemetry, identity, etc.)
    - blast_radius: read_only | write_local | write_external | destructive
    - approved_by: who authorized this tool's use in the pilot
    - approved_at: when

Unregistered tools are denied by default (deny-by-default, HRN-008).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set

from .enforcement import GovernanceAuditLog, GovernanceAuditEntry


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ToolBlastRadius(str, Enum):
    """The blast radius of a tool — how much damage it can do if compromised."""
    READ_ONLY = "read_only"
    WRITE_LOCAL = "write_local"
    WRITE_EXTERNAL = "write_external"
    DESTRUCTIVE = "destructive"


@dataclass(frozen=True, slots=True)
class RegisteredTool:
    """A tool that has been registered and approved for use in a pilot."""
    tool_id: str
    description: str
    data_classes: List[str]  # e.g. ["telemetry", "identity", "outcomes"]
    blast_radius: ToolBlastRadius
    approved_by: str
    approved_at: datetime = field(default_factory=_now)
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "description": self.description,
            "data_classes": list(self.data_classes),
            "blast_radius": self.blast_radius.value,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat(),
            "revoked": self.revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revoked_by": self.revoked_by,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RegisteredTool":
        approved = d.get("approved_at")
        if isinstance(approved, str):
            approved = datetime.fromisoformat(approved.replace("Z", "+00:00"))
        revoked = d.get("revoked_at")
        if isinstance(revoked, str):
            revoked = datetime.fromisoformat(revoked.replace("Z", "+00:00"))
        return cls(
            tool_id=d["tool_id"],
            description=d["description"],
            data_classes=list(d.get("data_classes", [])),
            blast_radius=ToolBlastRadius(d.get("blast_radius", "read_only")),
            approved_by=d["approved_by"],
            approved_at=approved or _now(),
            revoked=d.get("revoked", False),
            revoked_at=revoked,
            revoked_by=d.get("revoked_by"),
        )


class UnregisteredToolError(Exception):
    """Raised when an unregistered tool is invoked (deny-by-default, HRN-008)."""
    pass


class ToolRegistry:
    """Registry of approved tools for a pilot (HRN-008 tool registration gate).

    Every tool used by the pilot must be registered before it can be
    invoked. Unregistered tools are denied by default. Registration
    requires explicit approval — a tool cannot be silently added.

    All registration and revocation actions are logged to the governance
    audit log.
    """

    def __init__(self, audit_log: Optional[GovernanceAuditLog] = None) -> None:
        self._tools: Dict[str, RegisteredTool] = {}
        self._audit_log = audit_log

    def register(
        self,
        tool_id: str,
        description: str,
        data_classes: List[str],
        blast_radius: ToolBlastRadius,
        approved_by: str,
    ) -> RegisteredTool:
        """Register a new tool for use in the pilot.

        Raises ValueError if the tool_id is already registered and active.
        Logs the registration to the audit log.
        """
        existing = self._tools.get(tool_id)
        if existing and not existing.revoked:
            raise ValueError(
                f"Tool '{tool_id}' is already registered and active. "
                f"Revoke it first if you need to re-register with different properties."
            )
        tool = RegisteredTool(
            tool_id=tool_id,
            description=description,
            data_classes=list(data_classes),
            blast_radius=blast_radius,
            approved_by=approved_by,
        )
        self._tools[tool_id] = tool
        if self._audit_log:
            self._audit_log.log(
                action="tool_registered",
                actor=approved_by,
                target=tool_id,
                details=f"blast_radius={blast_radius.value}, data_classes={data_classes}",
            )
        return tool

    def revoke(self, tool_id: str, revoked_by: str) -> None:
        """Revoke a registered tool. Subsequent invocations will be denied.

        Raises KeyError if the tool is not registered.
        """
        existing = self._tools.get(tool_id)
        if not existing:
            raise KeyError(f"Tool '{tool_id}' is not registered.")
        self._tools[tool_id] = RegisteredTool(
            tool_id=existing.tool_id,
            description=existing.description,
            data_classes=existing.data_classes,
            blast_radius=existing.blast_radius,
            approved_by=existing.approved_by,
            approved_at=existing.approved_at,
            revoked=True,
            revoked_at=_now(),
            revoked_by=revoked_by,
        )
        if self._audit_log:
            self._audit_log.log(
                action="tool_revoked",
                actor=revoked_by,
                target=tool_id,
                details=f"previously approved by {existing.approved_by}",
            )

    def is_registered(self, tool_id: str) -> bool:
        """Check whether a tool is registered and active (not revoked)."""
        tool = self._tools.get(tool_id)
        return tool is not None and not tool.revoked

    def check_invocation(self, tool_id: str) -> RegisteredTool:
        """Check whether a tool invocation is permitted.

        Returns the RegisteredTool if permitted.
        Raises UnregisteredToolError if the tool is not registered or revoked.
        """
        tool = self._tools.get(tool_id)
        if not tool:
            raise UnregisteredToolError(
                f"Tool '{tool_id}' is not registered. "
                f"Deny-by-default (HRN-008): register the tool before invocation."
            )
        if tool.revoked:
            raise UnregisteredToolError(
                f"Tool '{tool_id}' was revoked by {tool.revoked_by} "
                f"at {tool.revoked_at.isoformat()}. Invocation denied."
            )
        return tool

    def list_tools(self, include_revoked: bool = False) -> List[RegisteredTool]:
        """List all registered tools, optionally including revoked ones."""
        if include_revoked:
            return list(self._tools.values())
        return [t for t in self._tools.values() if not t.revoked]

    def to_dict(self) -> dict:
        return {
            "tools": [t.to_dict() for t in self._tools.values()],
        }

    @classmethod
    def from_dict(cls, d: dict, audit_log: Optional[GovernanceAuditLog] = None) -> "ToolRegistry":
        reg = cls(audit_log=audit_log)
        for t in d.get("tools", []):
            reg._tools[t["tool_id"]] = RegisteredTool.from_dict(t)
        return reg
