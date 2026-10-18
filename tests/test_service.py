import dataclasses
import json
import os
import threading
from datetime import date
from pathlib import Path

import pytest

from ytdownloader.core.errors import FriendlyError
from ytdownloader.core.models import DownloadRequest, Progress, Status
from ytdownloader.core.naming import safe_filename
from ytdownloader.core.probe import info_from_json
from ytdownloader.core import service as service_module
from ytdownloader.core.service import Service
from ytdownloader.core.tools import ToolPaths

FIXTURES = Path(__file__).parent / "fixtures"
TODAY = date(2026, 10, 18)


class FakeTools:
    def __init__(self, missing=()):
        self._missing = list(missing)

    def paths(self) -> ToolPaths:
        return ToolPaths(Path("yt-dlp"), Path("ffmpeg"), Path("deno"))

    def missing(self):
        return self._missing


class FakeRunner:
    """Creates `files` (name -> bytes) in the output dir, emits `lines`, returns (rc, stderr)."""

    def __init__(self, folder: Path, files=None, lines=(), rc=0, stderr=""):
        self.folder = folder
        self.files = files or {}
        self.lines = list(lines)
        self.rc = rc
        self.stderr = stderr
        self.calls: list[list[str]] = []

    def run(self, args, on_line, cancel):
        self.calls.append(args)
        for name, data in self.files.items():
            (self.folder / name).write_bytes(data)
        for line in self.lines:
            on_line(line)
        return self.rc, self.stderr


class NoRunner:
    def run(self, args, on_line, cancel):
        raise AssertionError("runner must not be called")


@pytest.fixture
def lecture():
    info = info_from_json(json.loads((FIXTURES / "info_lecture.json").read_text(encoding="utf-8")))
    return dataclasses.replace(info, title="T")


@pytest.fixture
def vtt() -> bytes:
    return (FIXTURES / "auto_pl.vtt").read_bytes()


def make_service(runner) -> Service:
    return Service(FakeTools(), runner_factory=lambda: runner, today=lambda: TODAY)


def request(folder: Path, **kw) -> DownloadRequest:
    return DownloadRequest(url="https://www.youtube.com/watch?v=VIw16SXObUQ", output_dir=folder, **kw)


def download(service, req, info):
    events: list = []
    result = service.download(req, info, events.append, threading.Event())
    return result, events


def full_runner(folder: Path, vtt: bytes) -> FakeRunner:
    return FakeRunner(
        folder,
        files={"T.mp4": b"video", "T.pl-orig.vtt": vtt},
        lines=["CODEC avc1.4d401f", f"FILE {folder / 'T.mp4'}"],
    )


def test_full_download_writes_media_note_and_removes_vtt(tmp_path, lecture, vtt):
    runner = full_runner(tmp_path, vtt)
    result, events = download(make_service(runner), request(tmp_path), lecture)

    assert result.media_path == tmp_path / "T.mp4"
    assert result.note_path == tmp_path / "T.md"
    assert result.srt_path is None
    assert result.transcript == "youtube-auto-pl"
    assert result.already_exists is False
    note = (tmp_path / "T.md").read_bytes().decode("utf-8")
    assert "\r\n" not in note
    assert "transcript: youtube-auto-pl" in note
    assert "downloaded: 2026-10-18" in note
    assert "## Transcript" in note
    assert "[0:00:08](https://youtu.be/VIw16SXObUQ?t=8)" in note
    assert "--write-auto-subs" in runner.calls[0]
    assert not list(tmp_path.glob("*.vtt"))
    assert Status("Writing note…") in events
    assert events[-1] == Status("Done.")


def test_srt_option_writes_srt(tmp_path, lecture, vtt):
    runner = full_runner(tmp_path, vtt)
    result, _ = download(make_service(runner), request(tmp_path, save_srt=True), lecture)

    srt = tmp_path / "T.pl.srt"
    assert result.srt_path == srt
    text = srt.read_bytes().decode("utf-8")
    assert text.startswith("1\n00:00:08,760 --> ")
    assert "\r\n" not in text
    assert not list(tmp_path.glob("*.vtt"))


def test_already_downloaded_returns_without_running(tmp_path, lecture):
    media = tmp_path / "T.mp4"
    media.write_bytes(b"video")
    note = tmp_path / "T.md"
    note.write_text("---\nurl: https://www.youtube.com/watch?v=VIw16SXObUQ\n---\n", encoding="utf-8")

    result, _ = download(make_service(NoRunner()), request(tmp_path), lecture)

    assert result.already_exists is True
    assert result.media_path == media
    assert result.note_path == note
    assert result.video_id == "VIw16SXObUQ"


def test_media_exists_note_missing_writes_note_only(tmp_path, lecture, vtt):
    # Without a note, media is recognised as this video's only by the " [ID]" suffix (spec §6.7).
    media = tmp_path / "T [VIw16SXObUQ].mp4"
    media.write_bytes(b"video")
    os.utime(media, (1_000_000_000, 1_000_000_000))
    mtime = media.stat().st_mtime_ns
    runner = FakeRunner(
        tmp_path,
        files={"T.pl-orig.vtt": vtt},
        lines=["CODEC vp9", f"FILE {tmp_path / 'T.webm'}"],
    )

    result, events = download(make_service(runner), request(tmp_path), lecture)

    assert "--skip-download" in runner.calls[0]
    assert result.media_path == media
    assert result.note_path == tmp_path / "T.md"
    note = (tmp_path / "T.md").read_text(encoding="utf-8")
    assert "## Transcript" in note
    assert "![[T [VIw16SXObUQ].mp4]]" in note
    assert media.stat().st_mtime_ns == mtime
    assert Status("Video already here — writing the note only.") in events
    assert not any(isinstance(e, Status) and "H.264" in e.text for e in events)
    assert not list(tmp_path.glob("*.vtt"))


@pytest.mark.parametrize("extra", [{}, {"save_srt": True, "subs": "none"}])
def test_media_exists_and_nothing_to_write_returns_without_running(tmp_path, lecture, extra):
    # No note wanted and no .srt possible: running yt-dlp would produce nothing.
    media = tmp_path / "T [VIw16SXObUQ].mp4"
    media.write_bytes(b"video")

    result, _ = download(make_service(NoRunner()), request(tmp_path, save_note=False, **extra), lecture)

    assert result.already_exists is True
    assert result.media_path == media
    assert result.note_path is None
    assert result.srt_path is None
    assert result.transcript == "none"
    assert not (tmp_path / "T.md").exists()


def test_media_exists_srt_wanted_still_runs(tmp_path, lecture, vtt):
    media = tmp_path / "T [VIw16SXObUQ].mp4"
    media.write_bytes(b"video")
    runner = FakeRunner(tmp_path, files={"T.pl-orig.vtt": vtt})

    result, _ = download(
        make_service(runner), request(tmp_path, save_note=False, save_srt=True), lecture
    )

    assert "--skip-download" in runner.calls[0]
    assert result.already_exists is False
    assert result.srt_path == tmp_path / "T.pl.srt"
    assert result.note_path is None


def test_engine_gets_the_canonical_url(tmp_path, lecture):
    runner = FakeRunner(tmp_path, files={"T.mp4": b"video"}, lines=[f"FILE {tmp_path / 'T.mp4'}"])
    req = DownloadRequest(
        url="https://youtu.be/VIw16SXObUQ?si=tracking&t=42", output_dir=tmp_path, subs="none"
    )
    download(make_service(runner), req, lecture)
    assert runner.calls[0][-2:] == ["--", "https://www.youtube.com/watch?v=VIw16SXObUQ"]


def test_note_kept_media_redownloaded(tmp_path, lecture):
    note = tmp_path / "T.md"
    original = "---\nurl: https://www.youtube.com/watch?v=VIw16SXObUQ\n---\n\nMY NOTES\n"
    note.write_text(original, encoding="utf-8")
    runner = FakeRunner(tmp_path, files={"T.mp4": b"video"}, lines=[f"FILE {tmp_path / 'T.mp4'}"])

    result, _ = download(make_service(runner), request(tmp_path), lecture)

    assert "--write-auto-subs" not in runner.calls[0]
    assert "--write-subs" not in runner.calls[0]
    assert note.read_text(encoding="utf-8") == original
    assert result.media_path == tmp_path / "T.mp4"
    assert result.note_path == note
    assert "Kept your existing note." in result.warnings


def test_cancel_cleans_partials(tmp_path, lecture, vtt):
    runner = FakeRunner(
        tmp_path,
        files={"T.f136.mp4.part": b"x", "T.pl-orig.vtt": vtt},
        lines=['YTDL {"status": "downloading", "filename": "T.f136.mp4"}'],
        rc=-1,
    )

    with pytest.raises(FriendlyError) as exc:
        download(make_service(runner), request(tmp_path), lecture)

    assert exc.value.code == "cancelled"
    assert not [p for p in tmp_path.iterdir() if p.name.startswith("T.")]


def test_cancelled_forced_redownload_keeps_note_and_media(tmp_path, lecture):
    media = tmp_path / "T.mp4"
    media.write_bytes(b"video")
    note = tmp_path / "T.md"
    note.write_text("---\nurl: https://www.youtube.com/watch?v=VIw16SXObUQ\n---\n", encoding="utf-8")
    (tmp_path / "Other.mp4.part").write_bytes(b"x")
    runner = FakeRunner(
        tmp_path,
        files={"T.f140.m4a": b"x", "T.temp.mp4": b"x", "T.mp4.ytdl": b"x", "T.mp4.part": b"x"},
        rc=-1,
    )

    with pytest.raises(FriendlyError) as exc:
        download(make_service(runner), request(tmp_path, force=True), lecture)

    assert exc.value.code == "cancelled"
    assert "--force-overwrites" in runner.calls[0]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["Other.mp4.part", "T.md", "T.mp4"]


def test_note_write_error_is_write_failed(tmp_path, lecture, vtt, monkeypatch):
    real_write = service_module._write_text

    def failing_write(path, text):
        if path.suffix == ".md":
            path.write_text("---\nurl: https://www.youtube.com/watch?v=VIw16SXObUQ\n", encoding="utf-8")
            raise PermissionError(13, "Permission denied", str(path))
        real_write(path, text)

    monkeypatch.setattr(service_module, "_write_text", failing_write)
    runner = full_runner(tmp_path, vtt)

    with pytest.raises(FriendlyError) as exc:
        download(make_service(runner), request(tmp_path, save_srt=True), lecture)

    assert exc.value.code == "write_failed"
    assert "Permission denied" in exc.value.details
    assert not list(tmp_path.glob("*.vtt"))
    assert not (tmp_path / "T.md").exists()  # the half-written note is removed
    assert (tmp_path / "T.mp4").exists()


def test_vtt_read_error_is_write_failed(tmp_path, lecture, vtt, monkeypatch):
    real_read = Path.read_text

    def failing_read(self, *args, **kwargs):
        if self.suffix == ".vtt":
            raise OSError(5, "Input/output error", str(self))
        return real_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", failing_read)
    runner = full_runner(tmp_path, vtt)

    with pytest.raises(FriendlyError) as exc:
        download(make_service(runner), request(tmp_path), lecture)

    assert exc.value.code == "write_failed"
    assert not list(tmp_path.glob("*.vtt"))
    assert not (tmp_path / "T.md").exists()


def test_write_error_keeps_existing_note(tmp_path, lecture, monkeypatch):
    note = tmp_path / "T.md"
    original = "---\nurl: https://www.youtube.com/watch?v=VIw16SXObUQ\n---\n\nMY NOTES\n"
    note.write_text(original, encoding="utf-8")
    runner = FakeRunner(tmp_path, files={"T.mp4": b"video"}, lines=[f"FILE {tmp_path / 'T.mp4'}"])

    def boom(self, *args, **kwargs):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(service_module.Service, "_write_outputs", boom)

    with pytest.raises(FriendlyError) as exc:
        download(make_service(runner), request(tmp_path), lecture)

    assert exc.value.code == "write_failed"
    assert note.read_text(encoding="utf-8") == original


def test_unwritable_folder(tmp_path, lecture):
    missing = tmp_path / "nope"

    with pytest.raises(FriendlyError) as exc:
        download(make_service(NoRunner()), request(missing), lecture)

    assert exc.value.code == "write_failed"
    assert not missing.exists()


def test_failed_download_maps_error(tmp_path, lecture):
    runner = FakeRunner(tmp_path, rc=1, stderr="ERROR: HTTP Error 429: Too Many Requests\n")

    with pytest.raises(FriendlyError) as exc:
        download(make_service(runner), request(tmp_path), lecture)

    assert exc.value.code == "rate_limit"


def test_tools_missing(tmp_path, lecture):
    service = Service(FakeTools(missing=["yt-dlp"]), runner_factory=NoRunner, today=lambda: TODAY)

    with pytest.raises(FriendlyError) as exc:
        download(service, request(tmp_path), lecture)

    assert exc.value.code == "tools_missing"


def test_missing_vtt_is_a_warning_not_a_failure(tmp_path, lecture):
    runner = FakeRunner(tmp_path, files={"T.mp4": b"video"}, lines=[f"FILE {tmp_path / 'T.mp4'}"])

    result, _ = download(make_service(runner), request(tmp_path), lecture)

    assert result.transcript == "none"
    assert "No subtitles were downloaded." in result.warnings
    assert "transcript: none" in (tmp_path / "T.md").read_text(encoding="utf-8")


def test_no_media_after_success_is_unknown_error(tmp_path, lecture):
    runner = FakeRunner(tmp_path, files={"T.f136.mp4.part": b"x"}, stderr="odd")

    with pytest.raises(FriendlyError) as exc:
        download(make_service(runner), request(tmp_path), lecture)

    assert exc.value.code == "unknown"
    assert not [p for p in tmp_path.iterdir() if p.name.startswith("T.")]


def test_probe_when_info_missing(tmp_path):
    info_json = (FIXTURES / "info_lecture.json").read_text(encoding="utf-8")
    probe_line = json.dumps(json.loads(info_json))
    calls: list[list[str]] = []
    base = safe_filename(json.loads(info_json)["title"])

    class TwoStep:
        def run(self, args, on_line, cancel):
            calls.append(args)
            if "-J" in args:
                on_line(probe_line)
            else:
                path = tmp_path / f"{base}.mp4"
                path.write_bytes(b"video")
                on_line(f"FILE {path}")
            return 0, ""

    events: list = []
    service = Service(FakeTools(), runner_factory=TwoStep, today=lambda: TODAY)
    result = service.download(
        request(tmp_path, subs="none"), None, events.append, threading.Event()
    )

    assert events[0] == Status("Fetching video info…")
    assert len(calls) == 2
    assert result.title.startswith("Wykład")
    assert result.media_path is not None and result.media_path.is_file()
    assert all(isinstance(e, (Status, Progress)) for e in events)
