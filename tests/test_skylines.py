from collections.abc import Mapping
from typing import Any

from pgfm.data.acquisition.tracklogs.census import build_skylines_census
from pgfm.data.acquisition.tracklogs.connectors.skylines import SkyLinesConnector


class FakeHttpClient:
    def __init__(self, pages: dict[str, Mapping[str, Any]], files: dict[str, bytes]) -> None:
        self.pages = pages
        self.files = files
        self.json_urls: list[str] = []
        self.byte_urls: list[str] = []

    def get_json(self, url: str) -> Mapping[str, Any]:
        self.json_urls.append(url)
        return self.pages[url]

    def get_bytes(self, url: str) -> bytes:
        self.byte_urls.append(url)
        return self.files[url]


def _flight(
    flight_id: int,
    *,
    filename: str | None,
    aircraft_type: str,
    model: str,
    date: str,
    country: str,
) -> dict[str, object]:
    return {
        "id": flight_id,
        "pilot": {"id": 999, "name": "Must Not Leak"},
        "igcFile": None if filename is None else {"filename": filename},
        "scoreDate": date,
        "model": {"type": aircraft_type, "name": model},
        "takeoffAirport": {"countryCode": country},
    }


def _connector() -> tuple[SkyLinesConnector, FakeHttpClient]:
    base = "https://example.test"
    page1 = {
        "count": 3,
        "flights": [
            _flight(
                10,
                filename="10.igc",
                aircraft_type="glider",
                model="ASG 29",
                date="2025-05-01",
                country="DE",
            ),
            _flight(
                11,
                filename="11.igc",
                aircraft_type="paraglider",
                model="Mentor 4",
                date="2025-05-02",
                country="AT",
            ),
        ],
    }
    page2 = {
        "count": 3,
        "flights": [
            _flight(
                12,
                filename=None,
                aircraft_type="glider",
                model="LS8",
                date="2024-07-01",
                country="DE",
            )
        ],
    }
    client = FakeHttpClient(
        pages={
            f"{base}/api/flights/all?page=1": page1,
            f"{base}/api/flights/all?page=2": page2,
        },
        files={f"{base}/files/10.igc": b"IGC"},
    )
    connector = SkyLinesConnector(
        base_url=base,
        client=client,
        request_delay_seconds=0,
        page_size=2,
    )
    return connector, client


def test_skylines_catalog_paginates_and_census_counts_source_classes() -> None:
    connector, _ = _connector()

    census = build_skylines_census(connector)

    assert census.listed_flights == 3
    assert census.downloadable_igc == 2
    assert census.by_aircraft_type == {"glider": 2, "paraglider": 1}
    assert census.by_year == {"2024": 1, "2025": 2}
    assert census.by_takeoff_country == {"AT": 1, "DE": 2}


def test_discovery_excludes_pilot_identity_and_skips_missing_igc() -> None:
    connector, _ = _connector()

    candidates = list(connector.discover())

    assert [candidate.external_id for candidate in candidates] == ["10", "11"]
    assert candidates[0].metadata == {
        "score_date": "2025-05-01",
        "aircraft_type": "glider",
        "aircraft_model": "ASG 29",
        "takeoff_country": "DE",
    }
    assert "pilot" not in candidates[0].metadata
    assert candidates[0].subject_key is None


def test_fetch_only_accepts_skylines_file_locator() -> None:
    connector, client = _connector()
    candidate = next(connector.discover())

    fetched = connector.fetch(candidate)

    assert fetched.content == b"IGC"
    assert fetched.media_type == "application/vnd.fai.igc"
    assert client.byte_urls == ["https://example.test/files/10.igc"]
