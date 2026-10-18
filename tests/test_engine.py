import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from ytdownloader.core.engine import (
    COMMON,
    FileDone,
    ProgressParser,
    Runner,
    base_args,
    download_args,
    probe_args,
)
from ytdownloader.core.models import DownloadRequest, Progress, Status, SubtitleTrack
from ytdownloader.core.naming import NamePlan
from ytdownloader.core.tools import ToolPaths

FIXTURES = Path(__file__).parent / "fixtures"
STDOUT_FIXTURE = FIXTURES / "progress_lines.txt"
STDERR_FIXTURE = FIXTURES / "progress_stderr_lines.txt"
FAKE = Path(__file__).parent / "fake_ytdlp.py"

TOOLS = ToolPaths(yt_dlp=Path("/t/yt-dlp"), ffmpeg_dir=Path("/t/ff"), deno=Path("/t/deno"))
URL = "https://www.youtube.com/watch?v=abcdefghijk"
NO_H264 = "No H.264 at this quality — downloading VP9/AV1 instead."


def _names(base: str = "T", ext: str = "mp4") -> NamePlan:
    folder = Path("/out")
    return NamePlan(
        base=base,
        media=folder / f"{base}.{ext}",
        note=folder / f"{base}.md",
        existing_media=None,
        existing_note=None,
    )


def _req(**kw) -> DownloadRequest:
    return DownloadRequest(url=URL, output_dir=Path("/out"), **kw)


def _base() -> list[str]:
    return [
        str(Path("/t/yt-dlp")),
        "--ignore-config",
        "--no-playlist",
        "--no-mtime",
        "--force-ipv4",
        "--encoding",
        "utf-8",
        "--js-runtimes",
        f"deno:{Path('/t/deno')}",
        "--ffmpeg-location",
        str(Path("/t/ff")),
    ]


def _common_dl(base: str = "T") -> list[str]:
    return [
        "-o",
        str(Path("/out") / base) + ".%(ext)s",
        "--progress",
        "--newline",
        "--progress-template",
        "download:YTDL %(progress)j",
        "--progress-template",
        "postprocess:YTPP %(progress)j",
        "--print",
        "before_dl:CODEC %(vcodec)s",
        "--print",
        "after_move:FILE %(filepath)s",
    ]


def _option_value(args: list[str], option: str) -> str:
    return args[args.index(option) + 1]


# --- arguments ------------------------------------------------------------------


def test_common_and_base_and_probe_args():
    assert COMMON == ["--ignore-config", "--no-playlist", "--no-mtime", "--force-ipv4"]
    assert base_args(TOOLS) == _base()
    assert probe_args(URL, TOOLS) == _base() + ["-J", "--", URL]


def test_download_args_mp4_manual_subs():
    track = SubtitleTrack(lang="pl", kind="manual", key="pl")
    args = download_args(_req(quality=1080), _names(), track, TOOLS)
    assert args == _base() + _common_dl() + [
        "-S",
        "res:1080,vcodec:h264,acodec:m4a",
        "--merge-output-format",
        "mp4",
        "--write-subs",
        "--sub-langs",
        "pl",
        "--sub-format",
        "vtt",
        "--",
        URL,
    ]
    assert _option_value(args, "-o") == str(Path("/out/T")) + ".%(ext)s"
    assert "--no-playlist" in args


def test_download_args_mp3_auto_subs():
    track = SubtitleTrack(lang="pl", kind="auto", key="pl-orig")
    args = download_args(_req(mode="mp3"), _names(ext="mp3"), track, TOOLS)
    assert args == _base() + _common_dl() + [
        "-f",
        "bestaudio",
        "-x",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "192K",
        "--write-auto-subs",
        "--sub-langs",
        "pl-orig",
        "--sub-format",
        "vtt",
        "--",
        URL,
    ]


def test_media_only_has_no_subs():
    track = SubtitleTrack(lang="pl", kind="manual", key="pl")
    args = download_args(_req(), _names(), track, TOOLS, media_only=True)
    for flag in ("--write-subs", "--write-auto-subs", "--sub-langs", "--sub-format"):
        assert flag not in args
    assert "--skip-download" not in args
    assert args[-1] == URL


def test_option_like_url_is_after_separator():
    evil = "--exec=touch x"
    probe = probe_args(evil, TOOLS)
    assert probe[-2:] == ["--", evil]
    track = SubtitleTrack(lang="pl", kind="manual", key="pl")
    for kwargs in ({}, {"media_only": True}, {"note_only": True}):
        req = DownloadRequest(url=evil, output_dir=Path("/out"))
        args = download_args(req, _names(), track, TOOLS, **kwargs)
        assert args[-2:] == ["--", evil]
        assert args.count("--") == 1


def test_output_template_escapes_percent():
    args = download_args(_req(), _names(base="100% Pure"), None, TOOLS)
    assert _option_value(args, "-o").endswith("100%% Pure.%(ext)s")


def test_download_args_force_overwrites():
    assert "--force-overwrites" in download_args(_req(force=True), _names(), None, TOOLS)
    assert "--force-overwrites" not in download_args(_req(), _names(), None, TOOLS)


def test_note_only_skips_download():
    track = SubtitleTrack(lang="en", kind="manual", key="en")
    args = download_args(_req(), _names(), track, TOOLS, note_only=True)
    assert "--skip-download" in args
    i = args.index("--write-subs")
    assert args[i : i + 5] == ["--write-subs", "--sub-langs", "en", "--sub-format", "vtt"]
    assert args[-1] == URL


# --- progress parser ------------------------------------------------------------


def test_parser_codec_status():
    parser = ProgressParser("mp4")
    assert parser.feed("CODEC vp9") == Status(NO_H264)
    assert parser.feed("CODEC avc1.4D401F") is None
    assert ProgressParser("mp3").feed("CODEC none") is None


def test_parser_on_real_lines():
    out_lines = STDOUT_FIXTURE.read_text(encoding="utf-8").splitlines()
    err_lines = STDERR_FIXTURE.read_text(encoding="utf-8").splitlines()
    parser = ProgressParser("mp4")
    events = [parser.feed(line) for line in out_lines[:-1] + err_lines + out_lines[-1:]]
    events = [e for e in events if e is not None]

    assert isinstance(events[0], Progress)
    assert events[0].text.startswith("Downloading video 0%")
    assert any(isinstance(e, Progress) and e.text.startswith("Downloading audio") for e in events)
    assert Progress(1.0, "Downloading video done") in events
    assert Progress(1.0, "Downloading audio done") in events
    assert Status("Merging into MP4…") in events
    assert events.count(Status("Merging into MP4…")) == 1
    assert events[-1] == FileDone(Path("/OUT/zoo.mp4"))
    # MoveFiles and Merger "finished" produce nothing: Merging is the last Status.
    assert events[-2] == Status("Merging into MP4…")


def test_parser_movefiles_and_extract_audio():
    mp4 = ProgressParser("mp4")
    assert mp4.feed('YTPP {"status": "started", "postprocessor": "MoveFiles"}') is None
    mp3 = ProgressParser("mp3")
    assert mp3.feed('YTPP {"status": "started", "postprocessor": "ExtractAudio"}') == Status(
        "Converting to MP3…"
    )


def test_parser_uses_estimate_when_total_missing():
    line = "YTDL " + json.dumps(
        {
            "status": "downloading",
            "downloaded_bytes": 500,
            "total_bytes_estimate": 2000,
            "filename": "/OUT/x.f140.m4a",
            "speed": None,
            "eta": None,
        }
    )
    event = ProgressParser("mp3").feed(line)
    assert event == Progress(0.25, "Downloading audio 25%")


def test_parser_text_format_and_subtitles():
    line = "YTDL " + json.dumps(
        {
            "status": "downloading",
            "downloaded_bytes": 1,
            "total_bytes": 2,
            "filename": "/OUT/x.f137.mp4",
            "speed": 8_400_000,
            "eta": 3725,
        }
    )
    assert ProgressParser("mp4").feed(line).text == "Downloading video 50% · 8.4 MB/s · 1:02:05 left"
    vtt = "YTDL " + json.dumps(
        {"status": "downloading", "downloaded_bytes": 10, "filename": "/OUT/x.pl.vtt", "eta": 65}
    )
    event = ProgressParser("mp4").feed(vtt)
    assert event == Progress(None, "Downloading subtitles · 1:05 left")


def test_parser_ignores_other_lines():
    parser = ProgressParser("mp4")
    assert parser.feed("[youtube] abcdefghijk: Downloading webpage") is None
    assert parser.feed("YTDL not-json") is None


# --- runner ---------------------------------------------------------------------


def test_runner_returns_output():
    lines: list[str] = []
    rc, err = Runner().run(
        [sys.executable, str(FAKE), str(STDOUT_FIXTURE)], lines.append, threading.Event()
    )
    assert rc == 0
    assert err == ""
    assert lines == STDOUT_FIXTURE.read_text(encoding="utf-8").splitlines()


def test_runner_feeds_stderr_lines_and_returns_stderr_text():
    lines: list[str] = []
    rc, err = Runner().run(
        [sys.executable, str(FAKE), str(STDOUT_FIXTURE), "stderr", str(STDERR_FIXTURE)],
        lines.append,
        threading.Event(),
    )
    out_lines = STDOUT_FIXTURE.read_text(encoding="utf-8").splitlines()
    err_lines = STDERR_FIXTURE.read_text(encoding="utf-8").splitlines()
    assert rc == 0
    assert err.splitlines() == err_lines
    assert [line for line in lines if line.startswith("YTPP")] == err_lines
    assert [line for line in lines if not line.startswith("YTPP")] == out_lines


def test_runner_passes_non_ascii_lines_intact(tmp_path):
    fixture = tmp_path / "lines.txt"
    fixture.write_text("YTDL {}\nFILE /OUT/Zażółć gęślą.mp4\n", encoding="utf-8")
    lines: list[str] = []
    rc, _ = Runner().run([sys.executable, str(FAKE), str(fixture)], lines.append, threading.Event())
    assert rc == 0
    assert lines == ["YTDL {}", "FILE /OUT/Zażółć gęślą.mp4"]


def test_runner_forces_utf8_in_child_environment():
    lines: list[str] = []
    code = "import os; print(os.environ['PYTHONUTF8'], os.environ['PYTHONIOENCODING'])"
    rc, _ = Runner().run([sys.executable, "-c", code], lines.append, threading.Event())
    assert rc == 0
    assert lines == ["1 utf-8"]


def _alive(pid: int) -> bool:
    if sys.platform == "win32":
        # os.kill on Windows terminates the process, so ask tasklist instead.
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        ).stdout
        return str(pid) in out.split()
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def test_cancel_kills_process_tree(tmp_path):
    pid_file = tmp_path / "child.pid"
    cancel = threading.Event()

    def cancel_when_child_started():
        deadline = time.monotonic() + 10
        while not pid_file.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        cancel.set()

    threading.Thread(target=cancel_when_child_started, daemon=True).start()
    start = time.monotonic()
    rc, _ = Runner().run(
        [sys.executable, str(FAKE), str(STDOUT_FIXTURE), "spawn-child", str(pid_file)],
        lambda line: None,
        cancel,
    )
    assert rc == -1
    assert time.monotonic() - start < 5

    child_pid = int(pid_file.read_text(encoding="utf-8"))
    # The orphaned child may linger briefly as a zombie until init reaps it.
    deadline = time.monotonic() + 3
    while _alive(child_pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not _alive(child_pid)


def test_runner_cancel_before_any_output_still_returns_minus_one():
    cancel = threading.Event()
    cancel.set()
    rc, _ = Runner().run(
        [sys.executable, "-c", "import time; time.sleep(60)"], lambda line: None, cancel
    )
    assert rc == -1


def test_cancel_after_process_exited_keeps_success():
    # The process prints its last line and exits 0; Cancel arrives only after that, while the
    # runner is still handling the output. Nothing was killed, so the run is a success.
    cancel = threading.Event()

    def on_line(line: str) -> None:
        time.sleep(0.5)  # the process exits meanwhile
        cancel.set()
        time.sleep(0.3)  # the watcher wakes up and sees Cancel

    rc, _ = Runner().run([sys.executable, "-c", "print('LAST', flush=True)"], on_line, cancel)
    assert rc == 0
