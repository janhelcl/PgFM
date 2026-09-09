"""Storage contracts and local reference implementations."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from pgfm.data.acquisition.models import FetchedArtifact, RightsStatement
from pgfm.data.acquisition.tracklogs.models import SourceReference, Tracklog


@dataclass(frozen=True, slots=True)
class StoredRawArtifact:
    sha256: str
    content_path: Path
    manifest_path: Path


class RawArtifactStore(Protocol):
    def put(self, artifact: FetchedArtifact, rights: RightsStatement) -> StoredRawArtifact: ...


class CanonicalTracklogStore(Protocol):
    def put(self, tracklog: Tracklog) -> None: ...


def _json_default(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return getattr(value, "value")
    raise TypeError(f"cannot JSON encode {type(value).__name__}")


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


class LocalRawArtifactStore:
    """Content-addressed raw store suitable for local acquisition and tests."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def put(self, artifact: FetchedArtifact, rights: RightsStatement) -> StoredRawArtifact:
        digest = hashlib.sha256(artifact.content).hexdigest()
        extension = ".igc" if "igc" in artifact.media_type.lower() else ".bin"
        content_path = self.root / "raw" / "sha256" / digest[:2] / f"{digest}{extension}"
        if content_path.exists():
            if content_path.read_bytes() != artifact.content:
                raise RuntimeError("SHA-256 collision or corrupted raw object")
        else:
            _atomic_write(content_path, artifact.content)

        external_key = hashlib.sha256(artifact.candidate.external_id.encode()).hexdigest()[:24]
        manifest_path = (
            self.root
            / "raw"
            / "manifests"
            / artifact.candidate.source
            / external_key
            / f"{digest}.json"
        )
        manifest = {
            "source": artifact.candidate.source,
            "external_id": artifact.candidate.external_id,
            "locator": artifact.candidate.locator,
            "subject_key": artifact.candidate.subject_key,
            "source_metadata": dict(artifact.candidate.metadata),
            "discovered_at": artifact.candidate.discovered_at,
            "retrieved_at": artifact.retrieved_at,
            "source_modified_at": artifact.source_modified_at,
            "acquisition_method": artifact.method,
            "media_type": artifact.media_type,
            "byte_length": len(artifact.content),
            "raw_sha256": digest,
            "rights": asdict(rights),
        }
        encoded = json.dumps(manifest, default=_json_default, sort_keys=True, indent=2).encode()
        if manifest_path.exists():
            if manifest_path.read_bytes() != encoded:
                raise RuntimeError("immutable acquisition manifest changed")
        else:
            _atomic_write(manifest_path, encoded)
        return StoredRawArtifact(digest, content_path, manifest_path)


class LocalCanonicalTracklogStore:
    """Simple canonical reference store.

    This deliberately implements the logical repository contract without declaring the eventual
    large-scale physical table format. Duplicate trajectories merge source provenance.
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    def put(self, tracklog: Tracklog) -> None:
        path = (
            self.root
            / "canonical"
            / "tracklogs"
            / tracklog.trajectory_sha256[:2]
            / f"{tracklog.tracklog_id}.json"
        )
        incoming = _tracklog_dict(tracklog)
        if path.exists():
            existing = json.loads(path.read_text())
            if _without_refs(existing) != _without_refs(incoming):
                raise RuntimeError(f"canonical identity collision for {tracklog.tracklog_id}")
            refs = {_source_ref_key(ref): ref for ref in existing["source_refs"]}
            for ref in incoming["source_refs"]:
                refs[_source_ref_key(ref)] = ref
            incoming["source_refs"] = [refs[key] for key in sorted(refs)]
        encoded = json.dumps(incoming, sort_keys=True, indent=2).encode()
        _atomic_write(path, encoded)


def _source_ref_key(ref: dict[str, object]) -> tuple[str, str, str]:
    return (str(ref["source"]), str(ref["external_id"]), str(ref["raw_sha256"]))


def _without_refs(tracklog: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in tracklog.items() if key != "source_refs"}


def _source_ref_dict(ref: SourceReference) -> dict[str, object]:
    return {
        "source": ref.source,
        "external_id": ref.external_id,
        "locator": ref.locator,
        "retrieved_at": ref.retrieved_at.isoformat(),
        "raw_sha256": ref.raw_sha256,
        "acquisition_method": ref.acquisition_method.value,
        "subject_key": ref.subject_key,
        "rights": {
            "status": ref.rights.status.value,
            "captured_at": ref.rights.captured_at.isoformat(),
            "terms_url": ref.rights.terms_url,
            "note": ref.rights.note,
        },
    }


def _tracklog_dict(tracklog: Tracklog) -> dict[str, object]:
    return {
        "schema_version": tracklog.schema_version,
        "tracklog_id": tracklog.tracklog_id,
        "trajectory_sha256": tracklog.trajectory_sha256,
        "metadata": {"aircraft_class": tracklog.metadata.aircraft_class.value},
        "source_refs": [_source_ref_dict(ref) for ref in tracklog.source_refs],
        "points": [
            {
                "timestamp": point.timestamp.isoformat(),
                "latitude_deg": point.latitude_deg,
                "longitude_deg": point.longitude_deg,
                "pressure_altitude_m": point.pressure_altitude_m,
                "gps_altitude_m": point.gps_altitude_m,
                "valid": point.valid,
                "extras": dict(point.extras),
            }
            for point in tracklog.points
        ],
    }
