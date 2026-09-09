"""Tracklog ingestion orchestration."""

from __future__ import annotations

from pgfm.data.acquisition.connectors import Connector
from pgfm.data.acquisition.models import AcquisitionCandidate, RightsStatement
from pgfm.data.acquisition.tracklogs.fingerprint import tracklog_id, trajectory_sha256
from pgfm.data.acquisition.tracklogs.igc import decode_igc
from pgfm.data.acquisition.tracklogs.models import SourceReference, Tracklog
from pgfm.data.acquisition.tracklogs.storage import CanonicalTracklogStore, RawArtifactStore


class TracklogIngestionPipeline:
    """Persist raw first, then decode and canonicalize."""

    def __init__(
        self,
        connector: Connector,
        raw_store: RawArtifactStore,
        canonical_store: CanonicalTracklogStore,
        rights: RightsStatement,
    ) -> None:
        self.connector = connector
        self.raw_store = raw_store
        self.canonical_store = canonical_store
        self.rights = rights

    def ingest(self, candidate: AcquisitionCandidate) -> Tracklog:
        if candidate.source != self.connector.source_id:
            raise ValueError("candidate source does not match connector")
        fetched = self.connector.fetch(candidate)
        stored_raw = self.raw_store.put(fetched, self.rights)

        parsed = decode_igc(fetched.content)
        digest = trajectory_sha256(parsed.points)
        source_ref = SourceReference(
            source=candidate.source,
            external_id=candidate.external_id,
            locator=candidate.locator,
            retrieved_at=fetched.retrieved_at,
            raw_sha256=stored_raw.sha256,
            acquisition_method=fetched.method,
            rights=self.rights,
            subject_key=candidate.subject_key,
        )
        tracklog = Tracklog(
            schema_version="1.0",
            tracklog_id=tracklog_id(digest),
            trajectory_sha256=digest,
            points=parsed.points,
            source_refs=(source_ref,),
        )
        self.canonical_store.put(tracklog)
        return tracklog

    def run(self, cursor: str | None = None) -> list[Tracklog]:
        return [self.ingest(candidate) for candidate in self.connector.discover(cursor)]
