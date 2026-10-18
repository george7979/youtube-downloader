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


def _pick(cls, data: dict) -> dict:
    names = {f.name for f in fields(cls)}
    return {k: v for k, v in data.items() if k in names}


def load_settings(path: Path | None = None) -> Settings:
    path = path or _default_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return Settings()
        values = _pick(Settings, data)
        values["recent"] = [
            RecentItem(**_pick(RecentItem, r)) for r in values.get("recent", [])
        ]
        return Settings(**values)
    except (OSError, ValueError, TypeError):
        return Settings()


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
    if s.output_dir is None:
        return paths.downloads_dir(), None
    saved = Path(s.output_dir)
    if saved.is_dir():
        return saved, None
    return (
        paths.downloads_dir(),
        f"Saved folder {saved} is not available. Using Downloads instead.",
    )
