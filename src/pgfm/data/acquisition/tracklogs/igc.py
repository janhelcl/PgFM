"""Shared IGC decoder.

Source adapters fetch bytes; this module owns the file-format semantics once for all sources.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from pgfm.data.acquisition.tracklogs.models import TrackPoint

_DATE_RE = re.compile(r"^H(?:F|P)DTE(?:DATE:)?(?P<day>\d{2})(?P<month>\d{2})(?P<year>\d{2})")


class IgcDecodeError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ParsedIgc:
    points: tuple[TrackPoint, ...]


def _parse_date(lines: list[str]) -> date:
    for line in lines:
        match = _DATE_RE.match(line)
        if match:
            year = int(match.group("year"))
            year += 2000 if year < 70 else 1900
            return date(year, int(match.group("month")), int(match.group("day")))
    raise IgcDecodeError("IGC file has no supported HFDTE date header")


def _coordinate(degrees: str, minutes_thousandths: str, hemisphere: str) -> float:
    deg = int(degrees)
    minutes = int(minutes_thousandths[:2]) + int(minutes_thousandths[2:]) / 1000
    value = deg + minutes / 60
    if hemisphere in {"S", "W"}:
        value = -value
    return value


def decode_igc(content: bytes) -> ParsedIgc:
    try:
        text = content.decode("ascii")
    except UnicodeDecodeError as exc:
        raise IgcDecodeError("IGC content must be ASCII") from exc

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    flight_date = _parse_date(lines)
    points: list[TrackPoint] = []
    current_date = flight_date
    previous_seconds: int | None = None

    for line in lines:
        if not line.startswith("B"):
            continue
        if len(line) < 35:
            raise IgcDecodeError(f"short B record: {line!r}")

        try:
            hour = int(line[1:3])
            minute = int(line[3:5])
            second = int(line[5:7])
            seconds = hour * 3600 + minute * 60 + second
            if previous_seconds is not None and seconds < previous_seconds:
                current_date += timedelta(days=1)
            previous_seconds = seconds

            latitude = _coordinate(line[7:9], line[9:14], line[14])
            longitude = _coordinate(line[15:18], line[18:23], line[23])
            validity = line[24]
            pressure_altitude = int(line[25:30])
            gps_altitude = int(line[30:35])
        except (ValueError, IndexError) as exc:
            raise IgcDecodeError(f"invalid B record: {line!r}") from exc

        if validity not in {"A", "V"}:
            raise IgcDecodeError(f"invalid fix validity {validity!r}")

        timestamp = datetime.combine(
            current_date,
            datetime.min.time(),
            tzinfo=UTC,
        ) + timedelta(seconds=seconds)
        points.append(
            TrackPoint(
                timestamp=timestamp,
                latitude_deg=latitude,
                longitude_deg=longitude,
                pressure_altitude_m=pressure_altitude,
                gps_altitude_m=gps_altitude,
                valid=validity == "A",
            )
        )

    if len(points) < 2:
        raise IgcDecodeError("IGC file contains fewer than two B records")
    return ParsedIgc(points=tuple(points))
