"""Stable identities for raw artifacts and normalized trajectories."""

from __future__ import annotations

import hashlib

from pgfm.data.acquisition.tracklogs.models import TrackPoint


def raw_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def trajectory_sha256(points: tuple[TrackPoint, ...]) -> str:
    """Hash normalized fixes, excluding source headers and source metadata.

    IGC headers can differ when the same trajectory is copied between platforms. The
    trajectory hash deliberately keys identity only on the ordered physical fixes. This is
    exact normalized deduplication, not fuzzy/near-duplicate detection.
    """

    digest = hashlib.sha256()
    for point in points:
        pressure = "" if point.pressure_altitude_m is None else str(point.pressure_altitude_m)
        gps = "" if point.gps_altitude_m is None else str(point.gps_altitude_m)
        row = (
            f"{point.timestamp.isoformat(timespec='seconds')}|"
            f"{point.latitude_deg:.7f}|{point.longitude_deg:.7f}|"
            f"{pressure}|{gps}|{int(point.valid)}\n"
        )
        digest.update(row.encode("ascii"))
    return digest.hexdigest()


def tracklog_id(trajectory_digest: str) -> str:
    if len(trajectory_digest) != 64:
        raise ValueError("trajectory_digest must be a SHA-256 hex digest")
    return f"trk_sha256_{trajectory_digest}"
