"""Models that describe acquisition before any domain-specific decoding."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


def require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


class RightsStatus(StrEnum):
    """What we currently know about permitted downstream use."""

    UNKNOWN = "unknown"
    PUBLIC_TERMS = "public_terms"
    PERMISSION_GRANTED = "permission_granted"
    OWNER_EXPORT = "owner_export"
    RESTRICTED = "restricted"


class AcquisitionMethod(StrEnum):
    """How the source artifact was obtained."""

    API = "api"
    BULK_EXPORT = "bulk_export"
    DOWNLOAD = "download"
    SCRAPE = "scrape"
    USER_IMPORT = "user_import"
    LOCAL = "local"


@dataclass(frozen=True, slots=True)
class RightsStatement:
    """A point-in-time rights/provenance statement, not a legal conclusion."""

    status: RightsStatus
    captured_at: datetime
    terms_url: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        require_aware(self.captured_at, "captured_at")


@dataclass(frozen=True, slots=True)
class AcquisitionCandidate:
    """A source-specific object that may contain a tracklog."""

    source: str
    external_id: str
    locator: str
    discovered_at: datetime
    subject_key: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("source must not be empty")
        if not self.external_id:
            raise ValueError("external_id must not be empty")
        require_aware(self.discovered_at, "discovered_at")


@dataclass(frozen=True, slots=True)
class FetchedArtifact:
    """Bytes fetched from a source before parsing or normalization."""

    candidate: AcquisitionCandidate
    content: bytes
    media_type: str
    retrieved_at: datetime
    method: AcquisitionMethod
    source_modified_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("content must not be empty")
        require_aware(self.retrieved_at, "retrieved_at")
        if self.source_modified_at is not None:
            require_aware(self.source_modified_at, "source_modified_at")
