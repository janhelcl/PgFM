"""SkyLines public flight database connector.

SkyLines exposes a public JSON flight catalogue and public IGC files. This
module deliberately keeps source/API semantics here; IGC decoding remains in
the shared decoder.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import quote
from urllib.request import Request, urlopen

from pgfm.data.acquisition.models import (
    AcquisitionCandidate,
    AcquisitionMethod,
    FetchedArtifact,
    RightsStatement,
    RightsStatus,
)

SKYLINES_BASE_URL = "https://www.skylines.aero"
SKYLINES_LICENSE_URL = "https://opendatacommons.org/licenses/by/1-0/"


class SkyLinesProtocolError(RuntimeError):
    """Raised when the public SkyLines response no longer matches our contract."""


class HttpClient(Protocol):
    def get_json(self, url: str) -> Mapping[str, Any]: ...

    def get_bytes(self, url: str) -> bytes: ...


class UrllibHttpClient:
    """Small dependency-free HTTP client with an identifiable user agent."""

    def __init__(self, *, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.user_agent = "PgFM/0.1 (+https://github.com/janhelcl/PgFM)"

    def _get(self, url: str) -> bytes:
        request = Request(url, headers={"User-Agent": self.user_agent})
        with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
            return response.read()

    def get_json(self, url: str) -> Mapping[str, Any]:
        payload = json.loads(self._get(url))
        if not isinstance(payload, dict):
            raise SkyLinesProtocolError("expected JSON object from SkyLines")
        return payload

    def get_bytes(self, url: str) -> bytes:
        return self._get(url)


@dataclass(frozen=True, slots=True)
class SkyLinesFlight:
    """Minimal non-PII catalogue record needed for acquisition and census."""

    flight_id: int
    igc_filename: str | None
    score_date: str | None
    aircraft_type: str | None
    aircraft_model: str | None
    takeoff_country: str | None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> SkyLinesFlight:
        try:
            flight_id = int(payload["id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SkyLinesProtocolError("flight record has no valid id") from exc

        igc = payload.get("igcFile")
        model = payload.get("model")
        takeoff = payload.get("takeoffAirport")
        return cls(
            flight_id=flight_id,
            igc_filename=_nested_string(igc, "filename"),
            score_date=_optional_string(payload.get("scoreDate")),
            aircraft_type=_nested_string(model, "type"),
            aircraft_model=_nested_string(model, "name"),
            takeoff_country=_nested_string(takeoff, "countryCode"),
        )


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _nested_string(value: object, key: str) -> str | None:
    if not isinstance(value, Mapping):
        return None
    return _optional_string(value.get(key))


def skylines_rights(captured_at: datetime | None = None) -> RightsStatement:
    """Point-in-time statement reflecting SkyLines' published database licence."""

    return RightsStatement(
        status=RightsStatus.PUBLIC_TERMS,
        captured_at=captured_at or datetime.now(UTC),
        terms_url=SKYLINES_LICENSE_URL,
        note="SkyLines states that its flight database is available under ODC-By.",
    )


class SkyLinesConnector:
    """Discover public SkyLines flights and fetch their original IGC files."""

    source_id = "skylines"

    def __init__(
        self,
        *,
        base_url: str = SKYLINES_BASE_URL,
        client: HttpClient | None = None,
        request_delay_seconds: float = 1.0,
        page_size: int = 50,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if request_delay_seconds < 0:
            raise ValueError("request_delay_seconds must be non-negative")
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        self.base_url = base_url.rstrip("/")
        self.client = client or UrllibHttpClient()
        self.request_delay_seconds = request_delay_seconds
        self.page_size = page_size
        self._sleep = sleep
        self._monotonic = monotonic
        self._next_request_at = 0.0

    def _wait(self) -> None:
        remaining = self._next_request_at - self._monotonic()
        if remaining > 0:
            self._sleep(remaining)
        self._next_request_at = self._monotonic() + self.request_delay_seconds

    def _get_json(self, url: str) -> Mapping[str, Any]:
        self._wait()
        return self.client.get_json(url)

    def _get_bytes(self, url: str) -> bytes:
        self._wait()
        return self.client.get_bytes(url)

    def iter_catalog(
        self,
        cursor: str | None = None,
        *,
        max_pages: int | None = None,
    ) -> Iterator[SkyLinesFlight]:
        """Iterate listable public flights; cursor is a 1-based page number."""

        try:
            page = int(cursor or "1")
        except ValueError as exc:
            raise ValueError("SkyLines cursor must be a page number") from exc
        if page < 1:
            raise ValueError("SkyLines cursor must be >= 1")
        if max_pages is not None and max_pages < 1:
            raise ValueError("max_pages must be >= 1")

        pages_read = 0
        while True:
            payload = self._get_json(f"{self.base_url}/api/flights/all?page={page}")
            rows = payload.get("flights")
            if not isinstance(rows, list):
                raise SkyLinesProtocolError("flight catalogue has no flights list")
            try:
                total_count = int(payload["count"])
            except (KeyError, TypeError, ValueError) as exc:
                raise SkyLinesProtocolError("flight catalogue has no valid count") from exc

            for row in rows:
                if not isinstance(row, Mapping):
                    raise SkyLinesProtocolError("flight entry is not an object")
                yield SkyLinesFlight.from_payload(row)

            pages_read += 1
            if not rows or page * self.page_size >= total_count:
                return
            if max_pages is not None and pages_read >= max_pages:
                return
            page += 1

    def discover(self, cursor: str | None = None) -> Iterator[AcquisitionCandidate]:
        discovered_at = datetime.now(UTC)
        for flight in self.iter_catalog(cursor):
            if flight.igc_filename is None:
                continue
            metadata = {
                key: value
                for key, value in {
                    "score_date": flight.score_date,
                    "aircraft_type": flight.aircraft_type,
                    "aircraft_model": flight.aircraft_model,
                    "takeoff_country": flight.takeoff_country,
                }.items()
                if value is not None
            }
            filename = quote(flight.igc_filename, safe="")
            yield AcquisitionCandidate(
                source=self.source_id,
                external_id=str(flight.flight_id),
                locator=f"{self.base_url}/files/{filename}",
                discovered_at=discovered_at,
                metadata=metadata,
            )

    def fetch(self, candidate: AcquisitionCandidate) -> FetchedArtifact:
        if candidate.source != self.source_id:
            raise ValueError("candidate does not belong to SkyLines connector")
        expected_prefix = f"{self.base_url}/files/"
        if not candidate.locator.startswith(expected_prefix):
            raise ValueError("refusing to fetch non-SkyLines locator")
        return FetchedArtifact(
            candidate=candidate,
            content=self._get_bytes(candidate.locator),
            media_type="application/vnd.fai.igc",
            retrieved_at=datetime.now(UTC),
            method=AcquisitionMethod.DOWNLOAD,
        )
