"""Platform-specific locations. Every path in the app comes from here."""

from __future__ import annotations

import sys
from pathlib import Path

import platformdirs

APP_NAME = "YouTube Downloader"
APP_SLUG = "youtube-downloader"

_WINDOWS = sys.platform == "win32"


def _app_kwargs() -> dict:
    if _WINDOWS:
        return {"appname": APP_NAME, "appauthor": False}
    return {"appname": APP_SLUG}


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    kwargs = _app_kwargs()
    if _WINDOWS:
        kwargs["roaming"] = True
    return _ensure(Path(platformdirs.user_config_dir(**kwargs)))


def data_dir() -> Path:
    return _ensure(Path(platformdirs.user_data_dir(**_app_kwargs())))


def log_dir() -> Path:
    return _ensure(Path(platformdirs.user_log_dir(**_app_kwargs())))


def tools_dir() -> Path:
    return _ensure(data_dir() / "tools")


def downloads_dir() -> Path:
    """User's Downloads folder; never created."""
    candidate = Path(platformdirs.user_downloads_dir())
    if candidate.is_dir():
        return candidate
    return Path.home() / "Downloads"


def resource_path(rel: str) -> Path:
    """Bundled resource: under sys._MEIPASS when frozen, else the repo root."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / rel
    return Path(__file__).resolve().parents[2] / rel
