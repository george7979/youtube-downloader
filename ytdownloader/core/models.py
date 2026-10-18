"""Plain data types shared by core, GUI and CLI."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

SUBS_DEFAULT = "default"
SUBS_NONE = "none"


@dataclass(frozen=True)
class SubtitleTrack:
    lang: str  # "pl"
    kind: str  # "manual" | "auto"
    key: str  # yt-dlp key: "pl" or "pl-orig"

    def label(self) -> str:
        return f"{self.lang} ({self.kind})"


@dataclass(frozen=True)
class Chapter:
    start: float
    title: str


@dataclass
class VideoInfo:
    id: str
    title: str
    channel: str
    url: str  # https://www.youtube.com/watch?v=<id>
    duration: int | None
    published: date | None
    language: str | None
    thumbnail: str | None
    description: str
    chapters: list[Chapter]
    heights: list[int]  # descending, unique
    subtitles: list[SubtitleTrack]


@dataclass
class DownloadRequest:
    url: str
    output_dir: Path
    mode: str = "mp4"
    quality: int = 1080
    subs: str = SUBS_DEFAULT  # SUBS_DEFAULT | SUBS_NONE | language code
    save_note: bool = True
    save_srt: bool = False
    force: bool = False


@dataclass
class DownloadResult:
    video_id: str
    title: str
    media_path: Path | None
    note_path: Path | None
    srt_path: Path | None
    transcript: str  # "youtube-manual-pl" | "youtube-auto-pl" | "none"
    already_exists: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Status:
    text: str


@dataclass(frozen=True)
class Progress:
    fraction: float | None
    text: str


EventSink = Callable[[Status | Progress], None]
