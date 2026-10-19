import pytest

from ytdownloader.core.urls import canonical_url, parse_video_id

VID = "VIw16SXObUQ"


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VID}",
        f"https://www.youtube.com/watch?v={VID}&list=PL123&t=42s",
        f"https://youtu.be/{VID}?si=abc",
        f"https://m.youtube.com/watch?v={VID}",
        f"https://www.youtube.com/shorts/{VID}",
        f"https://www.youtube.com/live/{VID}",
        f"https://www.youtube.com/embed/{VID}",
        f"youtube.com/watch?v={VID}",
    ],
)
def test_parse_video_id(url):
    assert parse_video_id(url) == VID


@pytest.mark.parametrize(
    "url",
    [
        "https://vimeo.com/123",
        "https://www.youtube.com/playlist?list=PL1",
        "https://www.youtube.com/watch?v=short",
        "",
        "hello",
    ],
)
def test_parse_video_id_invalid(url):
    assert parse_video_id(url) is None


def test_canonical_url():
    assert canonical_url(VID) == f"https://www.youtube.com/watch?v={VID}"
