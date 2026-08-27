"""SystemVersion — a versioned release of a System.

Per `03_CONNECTION_INGESTION.md` §5.6 Object 3: A specific version/configuration
of a System. Tracks model versions, provider configurations, and deployment
versions. This enables model comparison as an operator×system-version analysis
(not a model leaderboard — frozen invariant).

Required fields: version_id, system_id, version_label, synthetic.
Optional fields: release_date, model_identifier, capabilities, deprecated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True, slots=True)
class SystemVersion:
    """A versioned release of a System.

    The `synthetic` flag must survive import/export.
    """
    version_id: str
    system_id: str
    version_label: str
    synthetic: bool = False
    release_date: Optional[str] = None  # ISO date
    model_identifier: Optional[str] = None
    capabilities: dict = field(default_factory=dict)
    deprecated: bool = False

    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "system_id": self.system_id,
            "version_label": self.version_label,
            "synthetic": self.synthetic,
            "release_date": self.release_date,
            "model_identifier": self.model_identifier,
            "capabilities": dict(self.capabilities),
            "deprecated": self.deprecated,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SystemVersion":
        return cls(
            version_id=d["version_id"],
            system_id=d["system_id"],
            version_label=d["version_label"],
            synthetic=bool(d["synthetic"]),
            release_date=d.get("release_date"),
            model_identifier=d.get("model_identifier"),
            capabilities=dict(d.get("capabilities", {})),
            deprecated=bool(d.get("deprecated", False)),
        )
