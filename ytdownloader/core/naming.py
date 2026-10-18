"""Windows-safe file naming and detection of existing downloads."""

from __future__ import annotations

import codecs
import re
from dataclasses import dataclass
from pathlib import Path

from .urls import parse_video_id

_MEDIA_EXTS = ("mp4", "mp3")
_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {
    f"LPT{i}" for i in range(1, 10)
}
_REPLACEMENTS = {
    ":": " -",
    "?": "",
    '"': "'",
    "/": "-",
    "\\": "-",
    "|": "-",
    "<": "_",
    ">": "_",
    "*": "_",
}
_WS_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"^url:\s*(\S+)\s*$")
_HEAD_BYTES = 4096
_MAX_BYTES = 200


def _strip(text: str) -> str:
    return text.strip().rstrip(" .")


def _cap(text: str, max_len: int) -> str:
    text = text[:max_len]
    text = text.encode("utf-8", "ignore")[:_MAX_BYTES].decode("utf-8", "ignore")
    return _strip(text)


def safe_filename(title: str, max_len: int = 150) -> str:
    text = _WS_RE.sub(" ", title)
    text = "".join(_REPLACEMENTS.get(ch, ch) for ch in text)
    text = "".join("_" if ord(ch) < 0x20 or ord(ch) == 0x7F else ch for ch in text)
    text = _strip(_WS_RE.sub(" ", text))
    text = _cap(text, max_len)
    if not text:
        return "video"
    if text.split(".", 1)[0].strip().upper() in _RESERVED:
        text = _cap("_" + text, max_len)
    return text


@dataclass
class NamePlan:
    base: str
    media: Path
    note: Path
    existing_media: Path | None
    existing_note: Path | None


def note_video_id(note: Path) -> str | None:
    """Video id from the `url:` line of the note's YAML frontmatter, if any."""
    try:
        with open(note, "rb") as fh:
            raw = fh.read(_HEAD_BYTES)
        # Incremental decode tolerates a multibyte character cut at the boundary.
        text = codecs.getincrementaldecoder("utf-8")("strict").decode(raw, final=False)
    except (OSError, UnicodeDecodeError):
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            return None
        match = _URL_RE.match(line.strip())
        if match:
            return parse_video_id(match.group(1))
    return None


def _find_media(folder: Path, stem: str, ext: str) -> Path | None:
    exts = [ext.lower()] + [e for e in _MEDIA_EXTS if e != ext.lower()]
    for e in exts:
        candidate = folder / f"{stem}.{e}"
        if candidate.is_file():
            return candidate
    return None


def plan_names(folder: Path, title: str, video_id: str, media_ext: str) -> NamePlan:
    entries = sorted(folder.iterdir()) if folder.is_dir() else []

    existing_note = next(
        (p for p in entries if p.suffix == ".md" and p.is_file() and note_video_id(p) == video_id),
        None,
    )
    existing_media: Path | None = None
    if existing_note is not None:
        existing_media = _find_media(folder, existing_note.stem, media_ext)
    if existing_media is None:
        suffixes = tuple(f" [{video_id}].{e}" for e in _MEDIA_EXTS)
        existing_media = next((p for p in entries if p.is_file() and p.name.endswith(suffixes)), None)

    if existing_note is not None:
        base = existing_note.stem
    else:
        base = safe_filename(title)
        if (folder / f"{base}.{media_ext}").exists() or (folder / f"{base}.md").exists():
            base = f"{base} [{video_id}]"

    media = folder / f"{base}.{media_ext}"
    note = folder / f"{base}.md"
    # Never leave an existing target unreported (e.g. an unrecognised note).
    if existing_note is None and note.is_file():
        existing_note = note
    if media.is_file():
        existing_media = media

    return NamePlan(
        base=base,
        media=media,
        note=note,
        existing_media=existing_media,
        existing_note=existing_note,
    )
