"""Observation — immutable measurement input event or aggregate.

Conforms to `schemas/observation.schema.json`. An observation is the rawest
content-free telemetry record: token counts (I/O/R/W), operator, timestamp,
and provenance. No derived values live here.

Provenance is structured per `12` §Provenance (source provider, collection
method, collector version, ingestion timestamp, original time window,
signature/checksum, synthetic marker). For backward compatibility, a bare
string is accepted and treated as `source_provider`; to_dict() always emits
the structured form.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Union

from .provenance import Provenance


@dataclass(frozen=True, slots=True)
class Observation:
    """A single canonical token-telemetry observation.

    Required fields (per observation.schema.json):
        observation_id, operator_id, timestamp,
        input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
        synthetic.

    Optional fields: platform, model, session_id, provenance,
    source_confidence, raw_source_reference.

    provenance accepts either a string (treated as source_provider for
    backward compatibility) or a Provenance object. It is normalized to a
    Provenance object in __post_init__.
    """

    observation_id: str
    operator_id: str
    timestamp: datetime
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    synthetic: bool
    platform: Optional[str] = None
    model: Optional[str] = None
    session_id: Optional[str] = None
    provenance: Optional[Union[str, Provenance]] = None
    source_confidence: Optional[str] = None
    raw_source_reference: Optional[str] = None

    def __post_init__(self) -> None:
        if self.input_tokens < 0 or self.output_tokens < 0:
            raise ValueError("token counts must be non-negative")
        if self.cache_read_tokens < 0 or self.cache_write_tokens < 0:
            raise ValueError("cache token counts must be non-negative")
        # Normalize naive datetimes to UTC for consistent serialization.
        if self.timestamp.tzinfo is None:
            object.__setattr__(self, "timestamp", self.timestamp.replace(tzinfo=timezone.utc))
        # Normalize provenance: bare string → Provenance(source_provider=...).
        # None stays None (no provenance). A Provenance object passes through.
        if self.provenance is not None and not isinstance(self.provenance, Provenance):
            object.__setattr__(
                self, "provenance",
                Provenance.from_dict(self.provenance),
            )

    @property
    def I(self) -> int:
        """Fresh input tokens (primitive symbol I)."""
        return self.input_tokens

    @property
    def O(self) -> int:
        """Generated output tokens (primitive symbol O)."""
        return self.output_tokens

    @property
    def R(self) -> int:
        """Cached/context tokens read (primitive symbol R)."""
        return self.cache_read_tokens

    @property
    def W(self) -> int:
        """Cached/context tokens written (primitive symbol W)."""
        return self.cache_write_tokens

    def to_dict(self) -> dict:
        prov = self.provenance.to_dict() if isinstance(self.provenance, Provenance) else self.provenance
        return {
            "observation_id": self.observation_id,
            "operator_id": self.operator_id,
            "timestamp": self.timestamp.isoformat(),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "synthetic": self.synthetic,
            "platform": self.platform,
            "model": self.model,
            "session_id": self.session_id,
            "provenance": prov,
            "source_confidence": self.source_confidence,
            "raw_source_reference": self.raw_source_reference,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Observation":
        ts = d["timestamp"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        prov = d.get("provenance")
        # Provenance.from_dict handles None, str, and dict forms.
        if prov is not None:
            prov = Provenance.from_dict(prov)
        return cls(
            observation_id=d["observation_id"],
            operator_id=d["operator_id"],
            timestamp=ts,
            input_tokens=int(d["input_tokens"]),
            output_tokens=int(d["output_tokens"]),
            cache_read_tokens=int(d["cache_read_tokens"]),
            cache_write_tokens=int(d["cache_write_tokens"]),
            synthetic=bool(d["synthetic"]),
            platform=d.get("platform"),
            model=d.get("model"),
            session_id=d.get("session_id"),
            provenance=prov,
            source_confidence=d.get("source_confidence"),
            raw_source_reference=d.get("raw_source_reference"),
        )
