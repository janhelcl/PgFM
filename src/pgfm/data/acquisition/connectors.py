"""Connector contract.

Connectors understand remote systems. They do not parse IGC or decide the canonical
tracklog schema.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from pgfm.data.acquisition.models import AcquisitionCandidate, FetchedArtifact


class Connector(Protocol):
    """Minimal contract implemented once per source."""

    @property
    def source_id(self) -> str: ...

    def discover(self, cursor: str | None = None) -> Iterable[AcquisitionCandidate]: ...

    def fetch(self, candidate: AcquisitionCandidate) -> FetchedArtifact: ...
