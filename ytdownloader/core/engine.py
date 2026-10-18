"""yt-dlp engine: command lines, progress parsing and a cancellable subprocess runner."""

from __future__ import annotations

import json
import os
import queue
import signal
import subprocess
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .models import DownloadRequest, Progress, Status, SubtitleTrack
from .naming import NamePlan
from .tools import ToolPaths

COMMON: list[str] = ["--ignore-config", "--no-playlist", "--no-mtime"]

_POLL_SECONDS = 0.1
_TERM_GRACE_SECONDS = 3


# --- arguments ------------------------------------------------------------------


def base_args(tools: ToolPaths) -> list[str]:
    return [
        str(tools.yt_dlp),
        *COMMON,
        "--js-runtimes",
        f"deno:{tools.deno}",
        "--ffmpeg-location",
        str(tools.ffmpeg_dir),
    ]


def probe_args(url: str, tools: ToolPaths) -> list[str]:
    return base_args(tools) + ["-J", url]


def download_args(
    req: DownloadRequest,
    names: NamePlan,
    track: SubtitleTrack | None,
    tools: ToolPaths,
    media_only: bool = False,
    note_only: bool = False,
) -> list[str]:
    folder = names.media.parent
    # `%` starts a yt-dlp template field; escape it only in our literal part.
    output = str(folder / names.base).replace("%", "%%") + ".%(ext)s"
    args = base_args(tools) + [
        "-o",
        output,
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
    if req.force:
        args.append("--force-overwrites")
    if note_only:
        args.append("--skip-download")
    if req.mode == "mp3":
        args += ["-f", "bestaudio", "-x", "--audio-format", "mp3", "--audio-quality", "192K"]
    else:
        args += ["-S", f"res:{req.quality},vcodec:h264,acodec:m4a", "--merge-output-format", "mp4"]
    if track is not None and not media_only:
        args.append("--write-subs" if track.kind == "manual" else "--write-auto-subs")
        args += ["--sub-langs", track.key, "--sub-format", "vtt"]
    args.append(req.url)
    return args


# --- progress parsing -----------------------------------------------------------


@dataclass(frozen=True)
class FileDone:
    path: Path


Event = Status | Progress | FileDone

_NO_H264 = "No H.264 at this quality — downloading VP9/AV1 instead."
_POSTPROCESS_STATUS = {
    "Merger": "Merging into MP4…",
    "ExtractAudio": "Converting to MP3…",
}


def _format_eta(seconds: float) -> str:
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


class ProgressParser:
    """Turns yt-dlp output lines (our templates) into events."""

    def __init__(self, mode: str):
        self.mode = mode  # "mp4" | "mp3"
        self._first_file_done = False

    def feed(self, line: str) -> Event | None:
        line = line.rstrip("\r\n")
        tag, _, rest = line.partition(" ")
        if tag == "YTDL":
            data = self._json(rest)
            return self._download(data) if data is not None else None
        if tag == "YTPP":
            data = self._json(rest)
            if data is None or data.get("status") != "started":
                return None
            text = _POSTPROCESS_STATUS.get(data.get("postprocessor"))
            return Status(text) if text else None
        if tag == "FILE" and rest:
            return FileDone(Path(rest))
        if tag == "CODEC" and self.mode == "mp4":
            return None if rest.startswith("avc1") else Status(_NO_H264)
        return None

    @staticmethod
    def _json(text: str) -> dict | None:
        try:
            data = json.loads(text)
        except ValueError:
            return None
        return data if isinstance(data, dict) else None

    def _label(self, filename: str) -> str:
        if filename.endswith(".vtt"):
            return "Downloading subtitles"
        if self.mode == "mp3" or self._first_file_done:
            return "Downloading audio"
        return "Downloading video"

    def _download(self, data: dict) -> Progress:
        filename = str(data.get("filename") or "")
        label = self._label(filename)
        if data.get("status") == "finished":
            if not filename.endswith(".vtt"):
                self._first_file_done = True
            return Progress(1.0, f"{label} done")

        downloaded = data.get("downloaded_bytes")
        total = data.get("total_bytes") or data.get("total_bytes_estimate")
        fraction = None
        if downloaded is not None and total:
            fraction = min(downloaded / total, 1.0)

        head = f"{label} {int(fraction * 100)}%" if fraction is not None else label
        parts = [head]
        speed = data.get("speed")
        if speed is not None:
            parts.append(f"{speed / 1_000_000:.1f} MB/s")
        eta = data.get("eta")
        if eta is not None:
            parts.append(f"{_format_eta(eta)} left")
        return Progress(fraction, " · ".join(parts))


# --- runner ---------------------------------------------------------------------

_EOF = object()


def kill_tree(proc: subprocess.Popen) -> None:
    """Terminate the process and everything it started."""
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return
    # POSIX: the runner starts the process in its own session, so pgid == pid.
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        return
    try:
        proc.wait(timeout=_TERM_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        pass
    # Also catches children that outlived the leader or ignored SIGTERM.
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


class Runner:
    def run(
        self,
        args: list[str],
        on_line: Callable[[str], None],
        cancel: threading.Event,
    ) -> tuple[int, str]:
        """Run yt-dlp; every stdout and stderr line goes to `on_line` on this thread.

        Returns (returncode, stderr text); returncode is -1 when cancelled.
        """
        kwargs: dict = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        else:
            kwargs["start_new_session"] = True
        proc = subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            **kwargs,
        )

        lines: queue.Queue = queue.Queue()
        stderr_parts: list[str] = []

        def pump(stream, keep: list[str] | None) -> None:
            try:
                for raw in stream:
                    if keep is not None:
                        keep.append(raw)
                    lines.put(raw.rstrip("\r\n"))
            finally:
                lines.put(_EOF)

        readers = [
            threading.Thread(target=pump, args=(proc.stdout, None), daemon=True),
            threading.Thread(target=pump, args=(proc.stderr, stderr_parts), daemon=True),
        ]
        done = threading.Event()

        def watch() -> None:
            while not done.wait(_POLL_SECONDS):
                if cancel.is_set():
                    kill_tree(proc)
                    return

        watcher = threading.Thread(target=watch, daemon=True)
        for thread in readers:
            thread.start()
        watcher.start()

        try:
            open_streams = len(readers)
            while open_streams:
                item = lines.get()
                if item is _EOF:
                    open_streams -= 1
                else:
                    on_line(item)
        except BaseException:
            kill_tree(proc)
            raise
        finally:
            returncode = proc.wait()
            done.set()
            watcher.join()
            for thread in readers:
                thread.join()
            proc.stdout.close()
            proc.stderr.close()

        if cancel.is_set():
            returncode = -1
        return returncode, "".join(stderr_parts)
