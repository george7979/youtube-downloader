import json
from datetime import date
from pathlib import Path

import pytest

from ytdownloader.core.errors import FriendlyError
from ytdownloader.core.models import SUBS_DEFAULT, SUBS_NONE, SubtitleTrack
from ytdownloader.core.probe import info_from_json, pick_track, probe
from ytdownloader.core.tools import ToolPaths

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str):
    return info_from_json(json.loads((FIXTURES / name).read_text(encoding="utf-8")))


@pytest.fixture
def zoo():
    return load("info_zoo.json")


@pytest.fixture
def lecture():
    return load("info_lecture.json")


def test_info_from_zoo(zoo):
    assert zoo.heights == [240, 144]
    assert zoo.subtitles == [
        SubtitleTrack("en", "manual", "en"),
        SubtitleTrack("de", "manual", "de"),
    ]
    assert len(zoo.chapters) == 3
    assert zoo.published == date(2005, 4, 24)
    assert isinstance(zoo.description, str)
    assert zoo.url == f"https://www.youtube.com/watch?v={zoo.id}"


def test_info_from_lecture(lecture):
    assert lecture.heights == [720, 360, 144]
    assert lecture.subtitles == [SubtitleTrack("pl", "auto", "pl-orig")]


def test_info_defaults_for_missing_fields():
    info = info_from_json({"id": "abcdefghijk", "duration": 12.7, "description": None})
    assert info.title == "abcdefghijk"
    assert info.channel == ""
    assert info.description == ""
    assert info.duration == 12
    assert info.published is None
    assert info.heights == []


def test_pick_default_prefers_manual_in_video_language(zoo):
    zoo.language = "de"
    track, warning = pick_track(zoo, SUBS_DEFAULT)
    assert track == SubtitleTrack("de", "manual", "de")
    assert warning is None


def test_pick_default_falls_back_to_auto(lecture):
    track, warning = pick_track(lecture, SUBS_DEFAULT)
    assert track == SubtitleTrack("pl", "auto", "pl-orig")
    assert warning is None


def test_pick_remembered_language(zoo):
    track, _ = pick_track(zoo, SUBS_DEFAULT, remembered="de")
    assert track.lang == "de"


def test_pick_explicit_missing_lang_warns(lecture):
    assert pick_track(lecture, "de") == (None, "No de subtitles for this video.")


def test_pick_explicit_lang(zoo, lecture):
    assert pick_track(zoo, "de")[0].key == "de"
    assert pick_track(lecture, "pl")[0].kind == "auto"


def test_pick_none(zoo):
    assert pick_track(zoo, SUBS_NONE) == (None, None)


class StubRunner:
    def __init__(self, rc=0, stderr="", lines=()):
        self.rc, self.stderr, self.lines, self.calls = rc, stderr, lines, 0

    def run(self, args, on_line, cancel):
        self.calls += 1
        for line in self.lines:
            on_line(line)
        return self.rc, self.stderr


def tools():
    return ToolPaths(Path("yt-dlp"), Path("ffmpeg"), Path("deno"))


def test_probe_invalid_url_does_not_run():
    runner = StubRunner()
    with pytest.raises(FriendlyError) as exc:
        probe("https://example.com/x", tools(), runner)
    assert exc.value.code == "invalid_url"
    assert runner.calls == 0


def test_probe_maps_errors():
    runner = StubRunner(rc=1, stderr="ERROR: [youtube] x: Video unavailable")
    with pytest.raises(FriendlyError) as exc:
        probe("https://www.youtube.com/watch?v=dQw4w9WgXcQ", tools(), runner)
    assert exc.value.code == "unavailable"


def test_probe_ignores_non_json_lines():
    payload = json.dumps({"id": "dQw4w9WgXcQ", "title": "T"})
    runner = StubRunner(lines=["WARNING: something", "{not json", payload])
    info = probe("https://www.youtube.com/watch?v=dQw4w9WgXcQ", tools(), runner)
    assert info.title == "T"


def test_probe_without_json_is_unknown_error():
    runner = StubRunner(lines=["WARNING: x"], stderr="WARNING: x")
    with pytest.raises(FriendlyError) as exc:
        probe("https://www.youtube.com/watch?v=dQw4w9WgXcQ", tools(), runner)
    assert exc.value.code == "unknown"
