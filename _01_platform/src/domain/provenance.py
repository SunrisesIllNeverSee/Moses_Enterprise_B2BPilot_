"""Provenance — structured provenance for an Observation.

Per `12` §Provenance: every observation should identify:
    - source provider
    - collection method
    - collector version
    - ingestion timestamp
    - original time window
    - signature/checksum when available
    - synthetic/production marker

This module provides the structured Provenance object. Observation.provenance
accepts either a string (treated as source_provider, for backward
compatibility) or a Provenance object. to_dict() always emits the structured
form; from_dict() accepts either a string or a dict.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Tuple


@dataclass(frozen=True, slots=True)
class Provenance:
    """Structured provenance per `12` §Provenance.

    All fields except `source_provider` are optional — adapters populate
    what they know. The `synthetic` marker is mirrored from the observation
    so provenance is self-describing.
    """
    source_provider: str
    collection_method: Optional[str] = None
    collector_version: Optional[str] = None
    ingestion_timestamp: Optional[str] = None  # ISO 8601
    original_time_window: Optional[Tuple[str, str]] = None  # (start, end) ISO
    signature_checksum: Optional[str] = None
    synthetic: Optional[bool] = None

    def __bool__(self) -> bool:
        """Truthiness — True if source_provider is set."""
        return bool(self.source_provider)

    def __str__(self) -> str:
        """String form — returns source_provider for backward compatibility."""
        return self.source_provider

    def to_dict(self) -> dict:
        d = {
            "source_provider": self.source_provider,
            "collection_method": self.collection_method,
            "collector_version": self.collector_version,
            "ingestion_timestamp": self.ingestion_timestamp,
            "original_time_window": (
                list(self.original_time_window) if self.original_time_window else None
            ),
            "signature_checksum": self.signature_checksum,
            "synthetic": self.synthetic,
        }
        return d

    @classmethod
    def from_dict(cls, d) -> Optional["Provenance"]:
        """Build a Provenance from a dict or a bare string.

        A bare string is treated as source_provider (backward compatibility).
        Returns None when d is None — there is no provenance to describe.
        This keeps a single "no provenance" state: None everywhere, not
        None in some places and an empty Provenance in others.
        """
        if d is None:
            return None
        if isinstance(d, str):
            return cls(source_provider=d)
        if isinstance(d, dict):
            otw = d.get("original_time_window")
            if isinstance(otw, list):
                otw = tuple(otw)
            return cls(
                source_provider=d.get("source_provider", ""),
                collection_method=d.get("collection_method"),
                collector_version=d.get("collector_version"),
                ingestion_timestamp=d.get("ingestion_timestamp"),
                original_time_window=otw,
                signature_checksum=d.get("signature_checksum"),
                synthetic=d.get("synthetic"),
            )
        # Fallback — coerce to string.
        return cls(source_provider=str(d))

    @classmethod
    def from_string(cls, s: str) -> "Provenance":
        """Build a Provenance from a bare source-provider string."""
        return cls(source_provider=s)
