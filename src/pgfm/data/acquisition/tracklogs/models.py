"""Canonical, source-independent tracklog model."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from pgfm.data.acquisition.models import AcquisitionMethod, RightsStatement, require_aware


class AircraftClass(StrEnum):
    PARAGLIDER = "paraglider"
    HANG_GLIDER = "hang_glider"
    RIGID_WING = "rigid_wing"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SourceReference:
    """One source record that contributed this trajectory."""

    source: str
    external_id: str
    locator: str
    retrieved_at: datetime
    raw_sha256: str
    acquisition_method: AcquisitionMethod
    rights: RightsStatement
    subject_key: str | None = None

    def __post_init__(self) -> None:
        require_aware(self.retrieved_at, "retrieved_at")
        if len(self.raw_sha256) != 64:
            raise ValueError("raw_sha256 must be a SHA-256 hex digest")


@dataclass(frozen=True, slots=True)
class TrackPoint:
    """One normalized trajectory fix.

    Altitudes remain separate because pressure and GNSS altitude are physically different
    measurements and should never be silently substituted for one another.
    """

    timestamp: datetime
    latitude_deg: float
    longitude_deg: float
    pressure_altitude_m: int | None = None
    gps_altitude_m: int | None = None
    valid: bool = True
    extras: Mapping[str, float | int | str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_aware(self.timestamp, "timestamp")
        if not -90 <= self.latitude_deg <= 90:
            raise ValueError("latitude_deg outside [-90, 90]")
        if not -180 <= self.longitude_deg <= 180:
            raise ValueError("longitude_deg outside [-180, 180]")


@dataclass(frozen=True, slots=True)
class TracklogMetadata:
    """Canonical metadata only; source-specific metadata belongs in raw manifests."""

    aircraft_class: AircraftClass = AircraftClass.UNKNOWN


@dataclass(frozen=True, slots=True)
class Tracklog:
    """A canonical trajectory that may be referenced by multiple source records."""

    schema_version: str
    tracklog_id: str
    trajectory_sha256: str
    points: tuple[TrackPoint, ...]
    source_refs: tuple[SourceReference, ...]
    metadata: TracklogMetadata = TracklogMetadata()

    def __post_init__(self) -> None:
        if len(self.points) < 2:
            raise ValueError("a tracklog requires at least two points")
        if not self.source_refs:
            raise ValueError("a tracklog requires at least one source reference")
        if len(self.trajectory_sha256) != 64:
            raise ValueError("trajectory_sha256 must be a SHA-256 hex digest")
        if any(
            a.timestamp > b.timestamp
            for a, b in zip(self.points, self.points[1:], strict=False)
        ):
            raise ValueError("track points must be ordered by timestamp")

    @property
    def start_time(self) -> datetime:
        return self.points[0].timestamp

    @property
    def end_time(self) -> datetime:
        return self.points[-1].timestamp
