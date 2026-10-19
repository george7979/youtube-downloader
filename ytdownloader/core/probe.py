"""Video metadata probe (`yt-dlp -J`) and subtitle track selection."""

from __future__ import annotations

import json
import threading
from datetime import date, datetime

from .engine import Runner, probe_args
from .errors import classify, friendly
from .models import (
    SUBS_DEFAULT,
    SUBS_NONE,
    Chapter,
    SubtitleTrack,
    VideoInfo,
)
from .tools import ToolPaths
from .urls import canonical_url, parse_video_id


def _tracks(d: dict) -> list[SubtitleTrack]:
    tracks = [
        SubtitleTrack(key, "manual", key)
        for key in (d.get("subtitles") or {})
        if key != "live_chat"
    ]
    auto = d.get("automatic_captions") or {}
    orig = [k for k in auto if k.endswith("-orig")]
    if orig:
        tracks += [SubtitleTrack(k[: -len("-orig")], "auto", k) for k in orig]
    elif d.get("language") and d["language"] in auto:
        tracks.append(SubtitleTrack(d["language"], "auto", d["language"]))
    return tracks


def _published(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError:
        return None


def info_from_json(d: dict) -> VideoInfo:
    heights = {
        f["height"]
        for f in d.get("formats") or []
        if f.get("vcodec") not in (None, "none") and f.get("height")
    }
    duration = d.get("duration")
    return VideoInfo(
        id=d["id"],
        title=d.get("title") or d["id"],
        channel=d.get("channel") or d.get("uploader") or "",
        url=canonical_url(d["id"]),
        duration=int(duration) if duration is not None else None,
        published=_published(d.get("upload_date")),
        language=d.get("language"),
        thumbnail=d.get("thumbnail"),
        description=d.get("description") or "",
        chapters=[
            Chapter(float(c.get("start_time") or 0), c.get("title") or "")
            for c in d.get("chapters") or []
        ],
        heights=sorted((int(h) for h in heights), reverse=True),
        subtitles=_tracks(d),
    )


def _json_object(line: str) -> dict | None:
    if not line.startswith("{"):
        return None
    try:
        data = json.loads(line)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def probe(url: str, tools: ToolPaths, runner: Runner | None = None) -> VideoInfo:
    video_id = parse_video_id(url)
    if video_id is None:
        raise friendly("invalid_url")
    runner = runner or Runner()
    found: list[dict] = []

    def on_line(line: str) -> None:
        data = _json_object(line)
        if data is not None:
            found.append(data)

    rc, stderr = runner.run(probe_args(canonical_url(video_id), tools), on_line, threading.Event())
    if rc != 0:
        raise classify(stderr)
    if not found:
        raise friendly("unknown", details=stderr)
    return info_from_json(found[-1])


def _find(info: VideoInfo, lang: str, kind: str | None = None) -> SubtitleTrack | None:
    for track in info.subtitles:
        if track.lang == lang and (kind is None or track.kind == kind):
            return track
    return None


def _by_lang(info: VideoInfo, lang: str) -> SubtitleTrack | None:
    return _find(info, lang, "manual") or _find(info, lang, "auto")


def pick_track(
    info: VideoInfo, subs: str, remembered: str | None = None
) -> tuple[SubtitleTrack | None, str | None]:
    if subs == SUBS_NONE:
        return None, None
    if subs != SUBS_DEFAULT:
        track = _by_lang(info, subs)
        if track:
            return track, None
        return None, f"No {subs} subtitles for this video."
    if remembered:
        track = _by_lang(info, remembered)
        if track:
            return track, None
    if info.language:
        track = _find(info, info.language, "manual")
        if track:
            return track, None
    for kind in ("manual", "auto"):
        for track in info.subtitles:
            if track.kind == kind:
                return track, None
    return None, None
