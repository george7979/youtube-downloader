"""Download service: probe, engine, transcript and note — the one entry point for every UI."""

from __future__ import annotations

import dataclasses
import fnmatch
import os
import threading
from collections.abc import Callable
from datetime import date
from pathlib import Path

from .engine import FileDone, ProgressParser, Runner, download_args
from .errors import classify, friendly
from .models import DownloadRequest, DownloadResult, EventSink, Status, SubtitleTrack, VideoInfo
from .naming import NamePlan, plan_names
from .note import render_note
from .probe import pick_track, probe
from .subtitles import clean_auto, parse_vtt, to_paragraphs, to_srt
from .tools import ToolManager

_PARTIAL_PATTERNS = ("*.part", "*.ytdl", "*.f[0-9]*.*", "*.vtt", "*.temp.*")

_KEPT_NOTE = "Kept your existing note."
_NO_SUBS = "No subtitles were downloaded."


def _write_text(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _cleanup(names: NamePlan) -> None:
    """Delete partial files of this download; never the note or pre-existing media."""
    folder = names.media.parent
    keep = {names.existing_media, names.existing_note}
    prefix = f"{names.base}."
    try:
        entries = list(folder.iterdir())
    except OSError:
        return
    for path in entries:
        if path in keep or not path.name.startswith(prefix) or not path.is_file():
            continue
        if any(fnmatch.fnmatchcase(path.name, p) for p in _PARTIAL_PATTERNS):
            try:
                path.unlink()
            except OSError:
                pass


class Service:
    def __init__(
        self,
        tools: ToolManager,
        runner_factory: Callable[[], Runner] = Runner,
        today: Callable[[], date] = date.today,
    ):
        self.tools = tools
        self.runner_factory = runner_factory
        self.today = today

    def probe(self, url: str) -> VideoInfo:
        return probe(url, self.tools.paths(), self.runner_factory())

    def download(
        self,
        req: DownloadRequest,
        info: VideoInfo | None,
        sink: EventSink,
        cancel: threading.Event,
        remembered_lang: str | None = None,
    ) -> DownloadResult:
        if self.tools.missing():
            raise friendly("tools_missing")
        if info is None:
            sink(Status("Fetching video info…"))
            info = self.probe(req.url)

        folder = Path(req.output_dir)
        if not folder.is_dir() or not os.access(folder, os.W_OK):
            raise friendly("write_failed", details=str(folder))

        names = plan_names(folder, info.title, info.id, "mp3" if req.mode == "mp3" else "mp4")
        if names.existing_media and names.existing_note and not req.force:
            return DownloadResult(
                video_id=info.id,
                title=info.title,
                media_path=names.existing_media,
                note_path=names.existing_note,
                srt_path=None,
                transcript="none",
                already_exists=True,
            )

        warnings: list[str] = []
        media_only = names.existing_note is not None
        note_only = (
            names.existing_media is not None and names.existing_note is None and not req.force
        )
        track: SubtitleTrack | None = None
        if media_only:
            warnings.append(_KEPT_NOTE)
        else:
            track, warning = pick_track(info, req.subs, remembered_lang)
            if warning:
                warnings.append(warning)
        if note_only and not req.save_note and not (req.save_srt and track is not None):
            # The media is here and neither a note nor an .srt is wanted: nothing to do.
            return DownloadResult(
                video_id=info.id,
                title=info.title,
                media_path=names.existing_media,
                note_path=None,
                srt_path=None,
                transcript="none",
                already_exists=True,
            )
        if note_only:
            sink(Status("Video already here — writing the note only."))

        # The canonical watch URL, not whatever the user pasted (tracking, playlist parameters).
        engine_req = dataclasses.replace(req, url=info.url)
        media_path = self._run_engine(
            engine_req, names, track, sink, cancel, media_only, note_only
        )

        try:
            transcript, srt_path, note_path = self._write_outputs(
                req, info, names, track, media_path, sink, warnings
            )
        except OSError as exc:
            _cleanup(names)
            raise friendly("write_failed", details=str(exc)) from exc

        sink(Status("Done."))
        return DownloadResult(
            video_id=info.id,
            title=info.title,
            media_path=media_path,
            note_path=note_path,
            srt_path=srt_path,
            transcript=transcript,
            warnings=warnings,
        )

    def _write_outputs(
        self,
        req: DownloadRequest,
        info: VideoInfo,
        names: NamePlan,
        track: SubtitleTrack | None,
        media_path: Path,
        sink: EventSink,
        warnings: list[str],
    ) -> tuple[str, Path | None, Path | None]:
        """Transcript, .srt and note after a successful engine run; may raise OSError."""
        folder = names.media.parent
        transcript = "none"
        srt_path: Path | None = None
        paragraphs = None
        if track is not None:
            vtt = folder / f"{names.base}.{track.key}.vtt"
            if vtt.is_file():
                cues = parse_vtt(vtt.read_text(encoding="utf-8", errors="replace"))
                if track.kind == "auto":
                    cues = clean_auto(cues)
                paragraphs = to_paragraphs(cues, info.chapters)
                if paragraphs:
                    transcript = f"youtube-{track.kind}-{track.lang}"
                if req.save_srt:
                    srt_path = folder / f"{names.base}.{track.lang}.srt"
                    _write_text(srt_path, to_srt(cues))
                vtt.unlink()
            else:
                warnings.append(_NO_SUBS)

        note_path = names.existing_note
        if req.save_note and names.existing_note is None:
            sink(Status("Writing note…"))
            note_text = render_note(info, media_path.name, transcript, paragraphs, self.today())
            try:
                _write_text(names.note, note_text)
            except OSError:
                # A half-written note would later count as "existing" and never be rewritten.
                try:
                    names.note.unlink(missing_ok=True)
                except OSError:
                    pass
                raise
            note_path = names.note
        return transcript, srt_path, note_path

    def _run_engine(
        self,
        req: DownloadRequest,
        names: NamePlan,
        track: SubtitleTrack | None,
        sink: EventSink,
        cancel: threading.Event,
        media_only: bool,
        note_only: bool,
    ) -> Path:
        args = download_args(req, names, track, self.tools.paths(), media_only, note_only)
        parser = ProgressParser(req.mode)
        captured: list[Path] = []

        def on_line(line: str) -> None:
            event = parser.feed(line)
            if event is None:
                return
            if isinstance(event, FileDone):
                if not note_only:
                    captured.append(event.path)
                return
            if note_only and line.startswith("CODEC "):
                return
            sink(event)

        rc, stderr = self.runner_factory().run(args, on_line, cancel)
        if rc == -1:
            _cleanup(names)
            raise friendly("cancelled")
        if rc != 0:
            _cleanup(names)
            raise classify(stderr)

        if note_only and names.existing_media is not None:
            return names.existing_media
        if captured:
            return captured[-1]
        if names.media.is_file():
            return names.media
        _cleanup(names)
        raise friendly("unknown", details=stderr)
