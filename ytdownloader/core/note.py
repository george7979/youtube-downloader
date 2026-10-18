"""Render the Obsidian note (markdown with YAML frontmatter) for a video."""

from __future__ import annotations

import json
import re
from datetime import date

from .models import VideoInfo
from .subtitles import Paragraph

_HASH = re.compile(r"(?:(?<=^)|(?<=\s))#", re.MULTILINE)


def format_ts(seconds: float, long: bool) -> str:
    total = int(seconds)
    h, rest = divmod(total, 3600)
    m, s = divmod(rest, 60)
    if long:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{h * 60 + m:02d}:{s:02d}"


def ts_link(video_id: str, seconds: float, long: bool) -> str:
    return f"[{format_ts(seconds, long)}](https://youtu.be/{video_id}?t={int(seconds)})"


def neutralize_markdown(text: str) -> str:
    text = _HASH.sub(r"\\#", text)
    return text.replace("[[", r"\[\[")


def _q(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_note(
    info: VideoInfo,
    media_filename: str,
    transcript_kind: str,
    paragraphs: list[Paragraph] | None,
    downloaded: date,
) -> str:
    long = (info.duration or 0) >= 3600
    front = ["---", f"title: {_q(info.title)}", f"channel: {_q(info.channel)}", f"url: {info.url}"]
    if info.published is not None:
        front.append(f"published: {info.published.isoformat()}")
    front.append(f"downloaded: {downloaded.isoformat()}")
    front.append(f"duration: {_q(format_ts(info.duration or 0, long))}")
    front.append(f"video: {_q(f'[[{media_filename}]]')}")
    front.append(f"transcript: {transcript_kind}")
    front.append("tags: [video, youtube]")
    front.append("---")

    parts = [
        "\n".join(front),
        f"# {info.title}",
        f"![[{media_filename}]]",
        "## Description\n\n" + neutralize_markdown(info.description.strip()),
    ]
    if info.chapters:
        lines = [f"- {ts_link(info.id, c.start, long)} {c.title}" for c in info.chapters]
        parts.append("## Chapters\n\n" + "\n".join(lines))
    if paragraphs:
        body = "\n\n".join(f"{ts_link(info.id, p.start, long)} {p.text}" for p in paragraphs)
        parts.append("## Transcript\n\n" + body)
    return "\n\n".join(parts).rstrip("\n") + "\n"
