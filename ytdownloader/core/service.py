"""Download service: probe, engine, transcript and note — the one entry point for every UI."""

from __future__ import annotations

import dataclasses
import fnmatch
import logging
import os
import threading
import time
from collections.abc import Callable
from datetime import date
from pathlib import Path

from .engine import FileDone, ProgressParser, Runner, download_args
from .errors import classify, friendly
from .models import DownloadRequest, DownloadResult, EventSink, Status, SubtitleTrack, VideoInfo
from .naming import NamePlan, note_fields, plan_names
from .note import render_note
from .probe import pick_track, probe
from .subtitles import clean_auto, parse_vtt, to_paragraphs, to_srt
from .tools import ToolManager

log = logging.getLogger(__name__)

# Extra engine runs after an HTTP 403 (stream URL refused); the second run usually succeeds.
FORBIDDEN_RETRIES = 1
# A gap this long without any engine output is logged, with the line before it.
STALL_LOG_S = 15.0

_PARTIAL_PATTERNS = ("*.part", "*.ytdl", "*.f[0-9]*.*", "*.vtt", "*.temp.*")

_KEPT_NOTE = "Kept your existing note."
_NO_SUBS = "No subtitles were downloaded."


def _write_text(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _transcript_lang(note: Path) -> tuple[bool, str | None]:
    """Language of a note's transcript from its `transcript:` field: (True, "<lang>") for
    `youtube-<kind>-<lang>`, (True, None) for `none`, (False, None) when missing or unreadable."""
    value = note_fields(note).get("transcript")
    if value == "none":
        return True, None
    parts = value.split("-", 2) if value else []
    if len(parts) == 3 and parts[0] == "youtube" and parts[2]:
        return True, parts[2]
    return False, None


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


class _EngineLog:
    """What a slow or failed download needs afterwards in app.log: yt-dlp's own messages
    (warnings, errors, codec and file lines — `--print` silences the rest), every gap without
    output of STALL_LOG_S or more with the line before it, and the total time."""

    def __init__(self, clock: Callable[[], float]):
        self.clock = clock
        self.start = self.last = clock()
        self.last_line = "(start)"

    def _check_gap(self) -> float:
        now = self.clock()
        gap = now - self.last
        if gap >= STALL_LOG_S:
            log.info("yt-dlp: no output for %.0f s after: %s", gap, self.last_line[:300])
        self.last = now
        return now

    def line(self, line: str) -> None:
        self._check_gap()
        self.last_line = line.rstrip()
        if not line.startswith(("YTDL ", "YTPP ")):
            log.info("yt-dlp: %s", self.last_line[:500])

    def done(self, rc: int) -> None:
        now = self._check_gap()
        log.info("yt-dlp: exit code %s after %.0f s", rc, now - self.start)


class Service:
    def __init__(
        self,
        tools: ToolManager,
        runner_factory: Callable[[], Runner] = Runner,
        today: Callable[[], date] = date.today,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.tools = tools
        self.runner_factory = runner_factory
        self.today = today
        self.clock = clock

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
        warnings: list[str] = []
        track: SubtitleTrack | None = None
        # The note this run writes and, for a language note, the main note it links to.
        note_target: Path | None = None
        main_note: str | None = None
        if names.existing_media and names.existing_note and not req.force:
            track = pick_track(info, req.subs, remembered_lang)[0]
            known, note_lang = _transcript_lang(names.existing_note)
            addable_lang: str | None = None
            if (
                req.save_note
                and track is not None
                and known
                and track.lang != note_lang
                and not names.language_note(track.lang).exists()
            ):
                addable_lang = track.lang
            if track is None or addable_lang is None or not req.add_transcript:
                return DownloadResult(
                    video_id=info.id,
                    title=info.title,
                    media_path=names.existing_media,
                    note_path=names.existing_note,
                    srt_path=None,
                    transcript="none",
                    already_exists=True,
                    addable_lang=addable_lang,
                    note_lang=note_lang,
                )
            # Only the subtitles are fetched; the video and every existing note stay as they are.
            media_only, note_only = False, True
            note_target, main_note = names.language_note(track.lang), names.base
            sink(Status(f"Video and note already here — adding the {track.lang} transcript."))
        else:
            media_only = names.existing_note is not None
            note_only = (
                names.existing_media is not None and names.existing_note is None and not req.force
            )
            if media_only:
                warnings.append(_KEPT_NOTE)
            else:
                track, warning = pick_track(info, req.subs, remembered_lang)
                if warning:
                    warnings.append(warning)
            if req.save_note and names.existing_note is None:
                note_target = names.note
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
        if note_only and main_note is None:
            sink(Status("Video already here — writing the note only."))

        # The canonical watch URL, not whatever the user pasted (tracking, playlist parameters).
        engine_req = dataclasses.replace(req, url=info.url)
        media_path = self._run_engine(
            engine_req, names, track, sink, cancel, media_only, note_only
        )

        try:
            transcript, srt_path, written = self._write_outputs(
                req, info, names, track, media_path, sink, warnings, note_target, main_note
            )
        except OSError as exc:
            _cleanup(names)
            raise friendly("write_failed", details=str(exc)) from exc

        note_path = written if written or main_note is not None else names.existing_note
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
        note_target: Path | None,
        main_note: str | None = None,
    ) -> tuple[str, Path | None, Path | None]:
        """Transcript, .srt and the note `note_target` (if any) after a successful engine run;
        returns the note written, or None. A language note (`main_note` set) needs subtitles.
        May raise OSError."""
        folder = names.media.parent
        transcript = "none"
        srt_path: Path | None = None
        paragraphs = None
        have_vtt = False
        if track is not None:
            vtt = folder / f"{names.base}.{track.key}.vtt"
            if vtt.is_file():
                have_vtt = True
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

        if note_target is None or (main_note is not None and not have_vtt):
            return transcript, srt_path, None
        sink(Status("Writing note…"))
        note_text = render_note(
            info, media_path.name, transcript, paragraphs, self.today(), main_note=main_note
        )
        try:
            _write_text(note_target, note_text)
        except OSError:
            # A half-written note would later count as "existing" and never be rewritten.
            try:
                note_target.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        return transcript, srt_path, note_target

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
        captured: list[Path] = []
        for attempt in range(FORBIDDEN_RETRIES + 1):
            parser = ProgressParser(req.mode)
            engine_log = _EngineLog(self.clock)
            captured.clear()
            log.info(
                "Download %s (%s, %sp, attempt %d)", req.url, req.mode, req.quality, attempt + 1
            )

            def on_line(
                line: str, parser: ProgressParser = parser, engine_log: _EngineLog = engine_log
            ) -> None:
                engine_log.line(line)
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
            engine_log.done(rc)
            if rc == -1:
                _cleanup(names)
                raise friendly("cancelled")
            if rc == 0:
                break
            _cleanup(names)
            error = classify(stderr)
            # YouTube now and then refuses a stream URL with 403; a fresh run gets new URLs.
            if error.code != "forbidden" or attempt == FORBIDDEN_RETRIES or cancel.is_set():
                raise error
            log.warning("HTTP 403 from YouTube, retrying the download")
            sink(Status("YouTube refused the stream — retrying…"))

        if note_only and names.existing_media is not None:
            return names.existing_media
        if captured:
            return captured[-1]
        if names.media.is_file():
            return names.media
        _cleanup(names)
        raise friendly("unknown", details=stderr)
