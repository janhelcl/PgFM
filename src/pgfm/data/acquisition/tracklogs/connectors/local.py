"""Local IGC connector used for imports, tests and connector development."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from pgfm.data.acquisition.models import (
    AcquisitionCandidate,
    AcquisitionMethod,
    FetchedArtifact,
)


class LocalIgcConnector:
    source_id = "local"

    def __init__(self, root: Path) -> None:
        self.root = root

    def discover(self, cursor: str | None = None) -> Iterable[AcquisitionCandidate]:
        del cursor
        discovered_at = datetime.now(UTC)
        for path in sorted(self.root.rglob("*.igc")):
            relative = path.relative_to(self.root).as_posix()
            yield AcquisitionCandidate(
                source=self.source_id,
                external_id=relative,
                locator=str(path),
                discovered_at=discovered_at,
            )

    def fetch(self, candidate: AcquisitionCandidate) -> FetchedArtifact:
        if candidate.source != self.source_id:
            raise ValueError("candidate does not belong to local connector")
        path = Path(candidate.locator)
        return FetchedArtifact(
            candidate=candidate,
            content=path.read_bytes(),
            media_type="application/vnd.fai.igc",
            retrieved_at=datetime.now(UTC),
            method=AcquisitionMethod.LOCAL,
        )
