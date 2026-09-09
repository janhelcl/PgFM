from datetime import UTC, datetime

from pgfm.data.acquisition.tracklogs.igc import decode_igc

IGC = (
    b"AXXX\n"
    b"HFDTE010924\n"
    b"B1200005000000N01400000EA0050000550\n"
    b"B1201005000060N01400120EA0051000560\n"
)


def test_decode_igc_preserves_both_altitudes() -> None:
    parsed = decode_igc(IGC)

    assert len(parsed.points) == 2
    assert parsed.points[0].timestamp == datetime(2024, 9, 1, 12, 0, tzinfo=UTC)
    assert parsed.points[0].latitude_deg == 50.0
    assert parsed.points[0].longitude_deg == 14.0
    assert parsed.points[0].pressure_altitude_m == 500
    assert parsed.points[0].gps_altitude_m == 550
    assert parsed.points[0].valid is True


def test_decode_igc_handles_midnight_rollover() -> None:
    content = (
        b"AXXX\n"
        b"HFDTE010924\n"
        b"B2359505000000N01400000EA0050000550\n"
        b"B0000105000060N01400120EA0051000560\n"
    )
    parsed = decode_igc(content)

    assert parsed.points[1].timestamp == datetime(2024, 9, 2, 0, 0, 10, tzinfo=UTC)
