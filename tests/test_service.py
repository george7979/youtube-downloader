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
from ytdownloader.core.note import render_note
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


class SequenceRunner:
    """Returns (rc, stderr) from `results` one call at a time; the last result repeats."""

    def __init__(self, folder: Path, results, files=None):
        self.folder = folder
        self.results = list(results)
        self.files = files or {}
        self.calls = 0

    def run(self, args, on_line, cancel):
        rc, stderr = self.results[min(self.calls, len(self.results) - 1)]
        self.calls += 1
        if rc == 0:
            for name, data in self.files.items():
                (self.folder / name).write_bytes(data)
        else:
            (self.folder / "T.f137.mp4.part").write_bytes(b"partial")
        return rc, stderr


FORBIDDEN = "ERROR: unable to download video data: HTTP Error 403: Forbidden\n"


def test_forbidden_is_retried_once_and_succeeds(tmp_path, lecture):
    runner = SequenceRunner(tmp_path, [(1, FORBIDDEN), (0, "")], files={"T.mp4": b"video"})
    events = []
    result = make_service(runner).download(
        request(tmp_path), lecture, events.append, threading.Event()
    )

    assert runner.calls == 2
    assert result.media_path == tmp_path / "T.mp4"
    assert any(getattr(e, "text", "") == "YouTube refused the stream — retrying…" for e in events)
    assert not (tmp_path / "T.f137.mp4.part").exists()


def test_forbidden_twice_raises_forbidden(tmp_path, lecture):
    runner = SequenceRunner(tmp_path, [(1, FORBIDDEN)])

    with pytest.raises(FriendlyError) as exc:
        download(make_service(runner), request(tmp_path), lecture)

    assert runner.calls == 2
    assert exc.value.code == "forbidden"
    assert not (tmp_path / "T.f137.mp4.part").exists()


def test_other_errors_are_not_retried(tmp_path, lecture):
    runner = SequenceRunner(tmp_path, [(1, "ERROR: HTTP Error 429: Too Many Requests\n")])

    with pytest.raises(FriendlyError):
        download(make_service(runner), request(tmp_path), lecture)

    assert runner.calls == 1


def test_engine_output_and_stalls_are_logged(tmp_path, lecture, caplog):
    now = [100.0]

    class SlowRunner(FakeRunner):
        def run(self, args, on_line, cancel):
            (self.folder / "T.mp4").write_bytes(b"video")
            on_line('YTDL {"status": "downloading", "downloaded_bytes": 1, "total_bytes": 10}')
            now[0] += 40  # YouTube stopped sending for 40 s
            on_line("WARNING: [youtube] something odd")
            on_line("FILE " + str(self.folder / "T.mp4"))
            now[0] += 2
            return 0, ""

    runner = SlowRunner(tmp_path)
    service = Service(FakeTools(), runner_factory=lambda: runner, today=lambda: TODAY,
                      clock=lambda: now[0])
    with caplog.at_level("INFO", logger="ytdownloader.core.service"):
        download(service, request(tmp_path), lecture)

    text = caplog.text
    assert 'no output for 40 s after: YTDL {"status": "downloading"' in text
    assert "yt-dlp: WARNING: [youtube] something odd" in text
    assert "yt-dlp: exit code 0 after 42 s" in text
    assert "downloaded_bytes" not in text.split("no output")[0]  # progress lines are not logged


# --- another transcript language as Title.<lang>.md ---------------------------------------


def write_main(folder: Path, info, transcript: str, media: str = "T.mp4") -> Path:
    note = folder / "T.md"
    note.write_text(render_note(info, media, transcript, None, TODAY), encoding="utf-8")
    return note


def write_media(folder: Path, name: str = "T.mp4") -> Path:
    media = folder / name
    media.write_bytes(b"video")
    return media


def test_other_language_is_offered_not_downloaded(tmp_path, lecture):
    media = write_media(tmp_path)
    note = write_main(tmp_path, lecture, "youtube-auto-en")

    result, _ = download(make_service(NoRunner()), request(tmp_path, subs="pl"), lecture)

    assert result.already_exists is True
    assert result.media_path == media
    assert result.note_path == note
    assert result.addable_lang == "pl"
    assert result.note_lang == "en"
    assert not (tmp_path / "T.pl.md").exists()


def test_add_transcript_writes_language_note_without_video(tmp_path, lecture, vtt):
    media = write_media(tmp_path)
    note = write_main(tmp_path, lecture, "youtube-auto-en")
    main_before = note.read_bytes()
    runner = FakeRunner(tmp_path, files={"T.pl-orig.vtt": vtt}, lines=["CODEC vp9"])

    result, events = download(
        make_service(runner), request(tmp_path, subs="pl", add_transcript=True), lecture
    )

    assert "--skip-download" in runner.calls[0]
    assert "--write-auto-subs" in runner.calls[0]
    language_note = tmp_path / "T.pl.md"
    text = language_note.read_text(encoding="utf-8")
    assert 'main_note: "[[T]]"' in text
    assert "transcript: youtube-auto-pl" in text
    assert "![[T.mp4]]" in text
    assert "## Transcript" in text
    assert note.read_bytes() == main_before
    assert media.read_bytes() == b"video"
    assert result.already_exists is False
    assert result.media_path == media
    assert result.note_path == language_note
    assert result.transcript == "youtube-auto-pl"
    assert "Kept your existing note." not in result.warnings
    assert Status("Writing note…") in events
    assert not any(isinstance(e, Status) and "H.264" in e.text for e in events)
    assert not list(tmp_path.glob("*.vtt"))


def test_add_transcript_writes_srt_when_wanted(tmp_path, lecture, vtt):
    write_media(tmp_path)
    write_main(tmp_path, lecture, "youtube-auto-en")
    runner = FakeRunner(tmp_path, files={"T.pl-orig.vtt": vtt})

    result, _ = download(
        make_service(runner),
        request(tmp_path, subs="pl", add_transcript=True, save_srt=True),
        lecture,
    )

    assert result.srt_path == tmp_path / "T.pl.srt"
    assert result.srt_path.is_file()


def test_same_language_is_not_offered(tmp_path, lecture):
    write_media(tmp_path)
    write_main(tmp_path, lecture, "youtube-manual-pl")

    result, _ = download(make_service(NoRunner()), request(tmp_path, subs="pl"), lecture)

    assert result.already_exists is True
    assert result.addable_lang is None
    assert result.note_lang == "pl"


def test_existing_language_note_is_not_offered(tmp_path, lecture):
    write_media(tmp_path)
    write_main(tmp_path, lecture, "youtube-auto-en")
    language_note = tmp_path / "T.pl.md"
    language_note.write_text("MY OWN PL NOTES\n", encoding="utf-8")

    result, _ = download(make_service(NoRunner()), request(tmp_path, subs="pl"), lecture)
    assert result.already_exists is True
    assert result.addable_lang is None

    result, _ = download(
        make_service(NoRunner()), request(tmp_path, subs="pl", add_transcript=True), lecture
    )
    assert result.already_exists is True
    assert result.addable_lang is None
    assert language_note.read_text(encoding="utf-8") == "MY OWN PL NOTES\n"


def test_note_off_is_not_offered(tmp_path, lecture):
    write_media(tmp_path)
    write_main(tmp_path, lecture, "youtube-auto-en")

    result, _ = download(
        make_service(NoRunner()),
        request(tmp_path, subs="pl", save_note=False, save_srt=True, add_transcript=True),
        lecture,
    )

    assert result.already_exists is True
    assert result.addable_lang is None
    assert not (tmp_path / "T.pl.srt").exists()


def test_main_note_without_transcript_field_is_not_offered(tmp_path, lecture):
    write_media(tmp_path)
    note = tmp_path / "T.md"
    note.write_text("---\nurl: https://www.youtube.com/watch?v=VIw16SXObUQ\n---\n", encoding="utf-8")

    result, _ = download(make_service(NoRunner()), request(tmp_path, subs="pl"), lecture)

    assert result.already_exists is True
    assert result.addable_lang is None
    assert result.note_lang is None


def test_main_note_without_transcript_offers_any_language(tmp_path, lecture):
    write_media(tmp_path)
    write_main(tmp_path, lecture, "none")

    result, _ = download(make_service(NoRunner()), request(tmp_path, subs="pl"), lecture)

    assert result.already_exists is True
    assert result.addable_lang == "pl"
    assert result.note_lang is None


def test_add_transcript_without_subtitles_writes_nothing(tmp_path, lecture):
    write_media(tmp_path)
    write_main(tmp_path, lecture, "youtube-auto-en")
    runner = FakeRunner(tmp_path)

    result, _ = download(
        make_service(runner), request(tmp_path, subs="pl", add_transcript=True), lecture
    )

    assert "--skip-download" in runner.calls[0]
    assert not (tmp_path / "T.pl.md").exists()
    assert result.already_exists is False
    assert result.note_path is None
    assert result.transcript == "none"
    assert "No subtitles were downloaded." in result.warnings


def test_cancel_while_adding_leaves_everything(tmp_path, lecture, vtt):
    media = write_media(tmp_path)
    note = write_main(tmp_path, lecture, "youtube-auto-en")
    main_before = note.read_bytes()
    runner = FakeRunner(tmp_path, files={"T.pl-orig.vtt": vtt}, rc=-1)

    with pytest.raises(FriendlyError) as exc:
        download(make_service(runner), request(tmp_path, subs="pl", add_transcript=True), lecture)

    assert exc.value.code == "cancelled"
    assert note.read_bytes() == main_before
    assert media.read_bytes() == b"video"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["T.md", "T.mp4"]


def test_language_note_for_mp3_embeds_the_mp3(tmp_path, lecture, vtt):
    write_media(tmp_path, "T.mp3")
    write_main(tmp_path, lecture, "youtube-auto-en", media="T.mp3")
    runner = FakeRunner(tmp_path, files={"T.pl-orig.vtt": vtt})

    result, _ = download(
        make_service(runner),
        request(tmp_path, mode="mp3", subs="pl", add_transcript=True),
        lecture,
    )

    assert result.media_path == tmp_path / "T.mp3"
    assert "![[T.mp3]]" in (tmp_path / "T.pl.md").read_text(encoding="utf-8")


def test_deleted_main_note_is_rebuilt_from_language_note(tmp_path, lecture, vtt):
    media = write_media(tmp_path)
    language_note = tmp_path / "T.pl.md"
    language_note.write_text(
        render_note(lecture, "T.mp4", "youtube-auto-pl", None, TODAY, main_note="T"),
        encoding="utf-8",
    )
    before = language_note.read_bytes()
    runner = FakeRunner(tmp_path, files={"T.pl-orig.vtt": vtt})

    result, _ = download(make_service(runner), request(tmp_path, subs="pl"), lecture)

    assert "--skip-download" in runner.calls[0]
    assert "T [VIw16SXObUQ].mp4" not in " ".join(runner.calls[0])
    assert result.media_path == media
    assert result.note_path == tmp_path / "T.md"
    assert "main_note" not in (tmp_path / "T.md").read_text(encoding="utf-8")
    assert language_note.read_bytes() == before
    assert not (tmp_path / "T [VIw16SXObUQ].mp4").exists()


def test_forced_download_ignores_the_offer(tmp_path, lecture):
    write_media(tmp_path)
    note = write_main(tmp_path, lecture, "youtube-auto-en")
    before = note.read_bytes()
    runner = FakeRunner(tmp_path, files={"T.mp4": b"new"}, lines=[f"FILE {tmp_path / 'T.mp4'}"])

    result, _ = download(
        make_service(runner),
        request(tmp_path, subs="pl", add_transcript=True, force=True),
        lecture,
    )

    assert "--skip-download" not in runner.calls[0]
    assert "--force-overwrites" in runner.calls[0]
    assert result.note_path == note
    assert note.read_bytes() == before
    assert not (tmp_path / "T.pl.md").exists()


def test_language_note_write_error_keeps_main_note(tmp_path, lecture, vtt, monkeypatch):
    real_write = service_module._write_text

    def failing_write(path, text):
        if path.name == "T.pl.md":
            path.write_text("---\nurl: half", encoding="utf-8")
            raise PermissionError(13, "Permission denied", str(path))
        real_write(path, text)

    monkeypatch.setattr(service_module, "_write_text", failing_write)
    media = write_media(tmp_path)
    note = write_main(tmp_path, lecture, "youtube-auto-en")
    before = note.read_bytes()
    runner = FakeRunner(tmp_path, files={"T.pl-orig.vtt": vtt})

    with pytest.raises(FriendlyError) as exc:
        download(make_service(runner), request(tmp_path, subs="pl", add_transcript=True), lecture)

    assert exc.value.code == "write_failed"
    assert note.read_bytes() == before
    assert media.read_bytes() == b"video"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["T.md", "T.mp4"]


def test_add_transcript_with_empty_subtitles_writes_nothing(tmp_path, lecture):
    write_media(tmp_path)
    note = write_main(tmp_path, lecture, "youtube-auto-en")
    before = note.read_bytes()
    runner = FakeRunner(tmp_path, files={"T.pl-orig.vtt": b"WEBVTT\n\n"})

    result, _ = download(
        make_service(runner), request(tmp_path, subs="pl", add_transcript=True), lecture
    )

    assert not (tmp_path / "T.pl.md").exists()
    assert result.already_exists is False
    assert result.note_path is None
    assert result.transcript == "none"
    assert result.warnings.count("No subtitles were downloaded.") == 1
    assert note.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["T.md", "T.mp4"]


def test_lone_language_note_never_reuses_another_videos_files(tmp_path, lecture, vtt):
    # Video A (lecture) was saved as T.mp4 + T.md + T.pl.md; the user deleted T.mp4 and T.md.
    language_note = tmp_path / "T.pl.md"
    language_note.write_text(
        render_note(lecture, "T.mp4", "youtube-auto-pl", None, TODAY, main_note="T"),
        encoding="utf-8",
    )
    # Another video B with the same title then took T.mp4 + T.md.
    other = dataclasses.replace(lecture, id="dQw4w9WgXcQ", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    b_media = write_media(tmp_path)
    b_note = write_main(tmp_path, other, "youtube-auto-en")
    b_before = (b_media.read_bytes(), b_note.read_bytes())
    base = "T [VIw16SXObUQ]"
    runner = FakeRunner(
        tmp_path,
        files={f"{base}.mp4": b"A", f"{base}.pl-orig.vtt": vtt},
        lines=[f"FILE {tmp_path / (base + '.mp4')}"],
    )

    result, _ = download(make_service(runner), request(tmp_path), lecture)

    assert result.already_exists is False
    assert "--force-overwrites" not in runner.calls[0]
    assert "--skip-download" not in runner.calls[0]
    assert result.media_path == tmp_path / f"{base}.mp4"
    assert result.note_path == tmp_path / f"{base}.md"
    assert (b_media.read_bytes(), b_note.read_bytes()) == b_before


def test_download_again_after_lone_language_note_keeps_other_video(tmp_path, lecture):
    language_note = tmp_path / "T.pl.md"
    language_note.write_text(
        render_note(lecture, "T.mp4", "youtube-auto-pl", None, TODAY, main_note="T"),
        encoding="utf-8",
    )
    other = dataclasses.replace(lecture, id="dQw4w9WgXcQ", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    b_media = write_media(tmp_path)
    b_note = write_main(tmp_path, other, "youtube-auto-en")
    b_before = (b_media.read_bytes(), b_note.read_bytes())
    base = "T [VIw16SXObUQ]"
    runner = FakeRunner(
        tmp_path, files={f"{base}.mp4": b"A"}, lines=[f"FILE {tmp_path / (base + '.mp4')}"]
    )

    result, _ = download(make_service(runner), request(tmp_path, force=True), lecture)

    args = runner.calls[0]
    assert args[args.index("-o") + 1] == str(tmp_path / base) + ".%(ext)s"
    assert result.media_path == tmp_path / f"{base}.mp4"
    assert (b_media.read_bytes(), b_note.read_bytes()) == b_before


def test_missing_language_warns_on_already_downloaded(tmp_path, lecture):
    write_media(tmp_path)
    write_main(tmp_path, lecture, "youtube-auto-en")

    result, _ = download(make_service(NoRunner()), request(tmp_path, subs="xx"), lecture)

    assert result.already_exists is True
    assert result.addable_lang is None
    assert result.warnings == ["No xx subtitles for this video."]


def test_already_downloaded_without_subs_choice_has_no_warning(tmp_path, lecture):
    write_media(tmp_path)
    write_main(tmp_path, lecture, "youtube-auto-en")

    for subs in ("default", "none"):
        result, _ = download(make_service(NoRunner()), request(tmp_path, subs=subs), lecture)
        assert result.already_exists is True
        assert result.warnings == []
