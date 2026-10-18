"""User settings and the list of recent downloads, stored as JSON in the config dir."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from ytdownloader.core import paths

MAX_RECENT = 5


@dataclass
class RecentItem:
    video_id: str
    title: str
    media_path: str
    downloaded: str  # ISO date "2026-10-18"


@dataclass
class Settings:
    output_dir: str | None = None
    mode: str = "mp4"  # "mp4" | "mp3"
    quality: int = 1080
    subs_lang: str | None = None  # last chosen subtitle language, None = rule §6.4
    save_note: bool = True
    save_srt: bool = False
    last_update_check: float = 0.0
    recent: list[RecentItem] = field(default_factory=list)


def _default_path() -> Path:
    return paths.config_dir() / "settings.json"


def _is_str_or_none(v) -> bool:
    return v is None or isinstance(v, str)


def _is_pos_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


_VALIDATORS = {
    "output_dir": _is_str_or_none,
    "mode": lambda v: v in ("mp4", "mp3"),
    "quality": _is_pos_int,
    "subs_lang": _is_str_or_none,
    "save_note": lambda v: isinstance(v, bool),
    "save_srt": lambda v: isinstance(v, bool),
    "last_update_check": _is_number,
}


def _parse_recent(raw) -> list[RecentItem]:
    if not isinstance(raw, list):
        return []
    items = []
    for r in raw:
        if not isinstance(r, dict):
            continue
        vals = {f.name: r.get(f.name) for f in fields(RecentItem)}
        if all(isinstance(v, str) for v in vals.values()):
            items.append(RecentItem(**vals))
    return items[:MAX_RECENT]


def load_settings(path: Path | None = None) -> Settings:
    path = path or _default_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Settings()
    if not isinstance(data, dict):
        return Settings()
    values = {k: data[k] for k, ok in _VALIDATORS.items() if k in data and ok(data[k])}
    values["last_update_check"] = float(values.get("last_update_check", 0.0))
    return Settings(**values, recent=_parse_recent(data.get("recent")))


def save_settings(s: Settings, path: Path | None = None) -> None:
    path = path or _default_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(asdict(s), ensure_ascii=False, indent=2)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def add_recent(s: Settings, item: RecentItem) -> None:
    s.recent = [r for r in s.recent if r.video_id != item.video_id]
    s.recent.insert(0, item)
    del s.recent[MAX_RECENT:]


def resolve_output_dir(s: Settings) -> tuple[Path, str | None]:
    if not s.output_dir:  # None or "" = not chosen yet
        return paths.downloads_dir(), None
    saved = Path(s.output_dir)
    if saved.is_dir():
        return saved, None
    return (
        paths.downloads_dir(),
        f"Saved folder {saved} is not available. Using Downloads instead.",
    )
