"""YouTube URL parsing."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

_ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")
_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}
_PATH_PREFIXES = ("shorts", "live", "embed")


def _valid(candidate: str | None) -> str | None:
    if candidate and _ID_RE.fullmatch(candidate):
        return candidate
    return None


def parse_video_id(url: str) -> str | None:
    text = (url or "").strip()
    if not text:
        return None
    if "://" not in text:
        text = "https://" + text
    try:
        parsed = urlparse(text)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    parts = [p for p in parsed.path.split("/") if p]
    if host == "youtu.be":
        return _valid(parts[0]) if parts else None
    if host in _HOSTS:
        if parsed.path.rstrip("/") == "/watch":
            return _valid((parse_qs(parsed.query).get("v") or [None])[0])
        if len(parts) >= 2 and parts[0] in _PATH_PREFIXES:
            return _valid(parts[1])
    return None


def canonical_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"
