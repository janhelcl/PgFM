from pgfm.data.acquisition.tracklogs.fingerprint import raw_sha256, trajectory_sha256
from pgfm.data.acquisition.tracklogs.igc import decode_igc

BODY = (
    b"HFDTE010924\n"
    b"B1200005000000N01400000EA0050000550\n"
    b"B1201005000060N01400120EA0051000560\n"
)


def test_header_changes_raw_hash_but_not_trajectory_hash() -> None:
    first = b"AXXX\nHFGTYGLIDERTYPE:Wing A\n" + BODY
    second = b"AYYY\nHFGTYGLIDERTYPE:Wing B\n" + BODY

    assert raw_sha256(first) != raw_sha256(second)
    assert trajectory_sha256(decode_igc(first).points) == trajectory_sha256(
        decode_igc(second).points
    )
