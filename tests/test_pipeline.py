import json
from datetime import UTC, datetime
from pathlib import Path

from pgfm.data.acquisition.models import RightsStatement, RightsStatus
from pgfm.data.acquisition.tracklogs.connectors.local import LocalIgcConnector
from pgfm.data.acquisition.tracklogs.pipeline import TracklogIngestionPipeline
from pgfm.data.acquisition.tracklogs.storage import (
    LocalCanonicalTracklogStore,
    LocalRawArtifactStore,
)


IGC = b"""AXXX\nHFDTE010924\nB1200005000000N01400000EA0050000550\nB1201005000060N01400120EA0051000560\n"""


def test_local_pipeline_persists_raw_manifest_and_canonical_track(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "flight.igc").write_bytes(IGC)
    data_root = tmp_path / "data"

    connector = LocalIgcConnector(inbox)
    rights = RightsStatement(RightsStatus.OWNER_EXPORT, datetime.now(UTC), note="test import")
    pipeline = TracklogIngestionPipeline(
        connector,
        LocalRawArtifactStore(data_root),
        LocalCanonicalTracklogStore(data_root),
        rights,
    )

    tracks = pipeline.run()

    assert len(tracks) == 1
    assert list((data_root / "raw" / "sha256").rglob("*.igc"))
    manifests = list((data_root / "raw" / "manifests").rglob("*.json"))
    canonical = list((data_root / "canonical" / "tracklogs").rglob("*.json"))
    assert len(manifests) == 1
    assert len(canonical) == 1
    assert json.loads(canonical[0].read_text())["tracklog_id"] == tracks[0].tracklog_id
