"""Source catalogue census helpers."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass

from pgfm.data.acquisition.tracklogs.connectors.skylines import SkyLinesConnector


@dataclass(frozen=True, slots=True)
class SkyLinesCensus:
    listed_flights: int
    downloadable_igc: int
    by_aircraft_type: dict[str, int]
    by_year: dict[str, int]
    by_takeoff_country: dict[str, int]


def build_skylines_census(
    connector: SkyLinesConnector,
    *,
    cursor: str | None = None,
    max_pages: int | None = None,
) -> SkyLinesCensus:
    aircraft: Counter[str] = Counter()
    years: Counter[str] = Counter()
    countries: Counter[str] = Counter()
    listed = 0
    downloadable = 0

    for flight in connector.iter_catalog(cursor, max_pages=max_pages):
        listed += 1
        downloadable += flight.igc_filename is not None
        aircraft[flight.aircraft_type or "unknown"] += 1
        year = (
            flight.score_date[:4]
            if flight.score_date and len(flight.score_date) >= 4
            else "unknown"
        )
        years[year] += 1
        countries[flight.takeoff_country or "unknown"] += 1

    return SkyLinesCensus(
        listed_flights=listed,
        downloadable_igc=downloadable,
        by_aircraft_type=dict(sorted(aircraft.items())),
        by_year=dict(sorted(years.items())),
        by_takeoff_country=dict(sorted(countries.items())),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Census the public SkyLines flight catalogue")
    parser.add_argument("--base-url", default="https://www.skylines.aero")
    parser.add_argument("--delay-seconds", type=float, default=1.0)
    parser.add_argument("--cursor", help="1-based page to resume from")
    parser.add_argument("--max-pages", type=int, help="limit pages for a smoke run")
    args = parser.parse_args()

    connector = SkyLinesConnector(
        base_url=args.base_url,
        request_delay_seconds=args.delay_seconds,
    )
    census = build_skylines_census(
        connector,
        cursor=args.cursor,
        max_pages=args.max_pages,
    )
    print(json.dumps(asdict(census), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
