"""System — an AI system, platform, or tool through which an operator interacts.

Per `03_CONNECTION_INGESTION.md` §5.6 Object 2: A system is the "system" in
operator×system analysis. A system is NOT a model — it is the platform/tool
(e.g. "Claude Code", "ChatGPT Enterprise", "GitHub Copilot"). Models are
tracked as System Versions.

Required fields: system_id, tenant_id, name, system_type, synthetic.
Optional fields: vendor, active.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SystemType(str, Enum):
    """System category per `03` §5.6 Object 2."""
    AI_PLATFORM = "ai_platform"
    AGENT_PLATFORM = "agent_platform"
    ENTERPRISE_SOFTWARE = "enterprise_software"
    IDENTITY = "identity"
    DATA_INPUT = "data_input"


@dataclass(frozen=True, slots=True)
class System:
    """An AI system/platform through which an operator interacts.

    The `synthetic` flag must survive import/export.
    """
    system_id: str
    tenant_id: str
    name: str
    system_type: SystemType
    synthetic: bool = False
    vendor: Optional[str] = None
    active: bool = True

    def to_dict(self) -> dict:
        return {
            "system_id": self.system_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "system_type": self.system_type.value,
            "synthetic": self.synthetic,
            "vendor": self.vendor,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "System":
        system_type = d["system_type"]
        if isinstance(system_type, str):
            system_type = SystemType(system_type)
        return cls(
            system_id=d["system_id"],
            tenant_id=d["tenant_id"],
            name=d["name"],
            system_type=system_type,
            synthetic=bool(d["synthetic"]),
            vendor=d.get("vendor"),
            active=d.get("active", True),
        )
