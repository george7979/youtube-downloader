"""WebVTT parsing, auto-caption cleanup, paragraph building and SRT output."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

from .models import Chapter

_TIMING = re.compile(
    r"^\s*(?:(\d+):)?(\d{1,2}):(\d{2})\.(\d{1,3})\s*-->\s*(?:(\d+):)?(\d{1,2}):(\d{2})\.(\d{1,3})"
)
_TAG = re.compile(r"<[^>]*>")
_SENTENCE_END = (".", "?", "!", "…")
_SKIP_BLOCKS = ("WEBVTT", "NOTE", "STYLE", "REGION")


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str
    # Original text lines of the cue (needed by clean_auto); not part of equality.
    lines: tuple[str, ...] = field(default=(), compare=False, repr=False)


@dataclass(frozen=True)
class Paragraph:
    start: float
    text: str


def _seconds(h: str | None, m: str, s: str, ms: str) -> float:
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000


def _clean_line(line: str) -> str:
    line = html.unescape(_TAG.sub("", line)).replace("\xa0", " ")
    return " ".join(line.split())


def parse_vtt(text: str) -> list[Cue]:
    cues: list[Cue] = []
    for block in re.split(r"\n\n+",text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")):
        lines = block.strip("\n").split("\n")
        if not lines or lines[0].startswith(_SKIP_BLOCKS):
            continue
        for i, line in enumerate(lines):
            match = _TIMING.match(line)
            if match:
                g = match.groups()
                start = _seconds(g[0], g[1], g[2], g[3])
                end = _seconds(g[4], g[5], g[6], g[7])
                cleaned = tuple(c for c in (_clean_line(x) for x in lines[i + 1 :]) if c)
                if cleaned:
                    cues.append(Cue(start, end, " ".join(cleaned), cleaned))
                break
    return cues


def clean_auto(cues: list[Cue]) -> list[Cue]:
    result: list[Cue] = []
    last_line = ""
    for cue in cues:
        lines = [x for x in (cue.lines or tuple(cue.text.split("\n"))) if x.strip()]
        remaining = [x for x in lines if x != last_line]
        if remaining:
            result.append(Cue(cue.start, cue.end, " ".join(remaining), tuple(remaining)))
        if lines:
            last_line = lines[-1]
    return result


def to_paragraphs(
    cues: list[Cue], chapters: list[Chapter], target: float = 45.0, hard: float = 90.0
) -> list[Paragraph]:
    starts = sorted(c.start for c in chapters)
    next_chapter = 0
    paragraphs: list[Paragraph] = []
    para_start = 0.0
    parts: list[str] = []

    def flush() -> None:
        if parts:
            paragraphs.append(Paragraph(para_start, " ".join(parts).strip()))
            parts.clear()

    for cue in cues:
        text = " ".join(cue.text.split())
        if not text:
            continue
        chapter_break = False
        while next_chapter < len(starts) and starts[next_chapter] <= cue.start:
            chapter_break = True
            next_chapter += 1
        if parts:
            elapsed = cue.start - para_start
            current = " ".join(parts)
            if (
                chapter_break
                or elapsed >= hard
                or (elapsed >= target and current.endswith(_SENTENCE_END))
            ):
                flush()
        if not parts:
            para_start = cue.start
        parts.append(text)
    flush()
    return paragraphs


def _srt_time(t: float) -> str:
    total_ms = round(t * 1000)
    h, rem = divmod(total_ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_srt(cues: list[Cue]) -> str:
    return "".join(
        f"{i}\n{_srt_time(c.start)} --> {_srt_time(c.end)}\n{c.text}\n\n"
        for i, c in enumerate(cues, 1)
    )
