"""Non-interactive command line: `get`, `info`, `tools` — JSON output for Claude Code (spec §8)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .core import settings as settings_module
from .core.errors import FriendlyError, friendly
from .core.logsetup import setup_logging
from .core.models import SUBS_DEFAULT, SUBS_NONE, DownloadRequest, Progress, Status
from .core.service import Service
from .core.tools import ToolManager

log = logging.getLogger(__name__)

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_CANCELLED = 130


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="youtube-downloader",
        description="Download a YouTube video with a Markdown note and transcript.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    get = sub.add_parser("get", help="download a video and write its note")
    get.add_argument("url")
    get.add_argument("--out", required=True, help="output folder (created if missing)")
    get.add_argument("--quality", type=int, default=1080, help="max video height (default 1080)")
    get.add_argument("--audio", action="store_true", help="download MP3 audio only")
    get.add_argument("--subs", metavar="LANG|none", help="subtitle language, or 'none'")
    get.add_argument("--srt", action="store_true", help="also save an .srt file")
    get.add_argument("--no-note", action="store_true", help="do not write the Markdown note")
    get.add_argument("--force", action="store_true", help="download again even if files exist")
    get.add_argument("--json", action="store_true", help="print one JSON object on stdout")

    info = sub.add_parser("info", help="show video metadata without downloading")
    info.add_argument("url")
    info.add_argument("--json", action="store_true", help="print one JSON object on stdout")

    tools = sub.add_parser("tools", help="show (and optionally update) the download tools")
    tools.add_argument("--update", action="store_true", help="update yt-dlp, ffmpeg and deno")
    tools.add_argument("--json", action="store_true", help="print one JSON object on stdout")
    return parser


# --- output ----------------------------------------------------------------


def _emit_json(obj: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _err(text: str) -> None:
    print(text, file=sys.stderr, flush=True)


def _error_json(exc: FriendlyError) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": exc.code,
            "message": exc.message,
            "hint": exc.hint,
            "details": exc.details,
        },
    }


def _report_error(exc: FriendlyError, as_json: bool) -> int:
    if as_json:
        _emit_json(_error_json(exc))
    else:
        _err(f"Error: {exc.message}" + (f"\n{exc.hint}" if exc.hint else ""))
    return EXIT_CANCELLED if exc.code == "cancelled" else EXIT_ERROR


def _utf8_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass


def _path_or_none(path: Path | None) -> str | None:
    return None if path is None else str(path)


# --- progress --------------------------------------------------------------


class _Sink:
    """Progress events to stderr: every status, and a progress line per 10% step."""

    def __init__(self) -> None:
        self._step = -1

    def __call__(self, event: Status | Progress) -> None:
        if isinstance(event, Status):
            self._step = -1
            _err(event.text)
            return
        if event.fraction is None:
            _err(event.text)
            return
        step = int(event.fraction * 10)
        if step != self._step or event.fraction >= 1.0:
            self._step = step
            _err(event.text)


def _install_missing(tools: ToolManager) -> None:
    for spec in tools.missing():
        last = [-1]

        def on_bytes(done: int, total: int | None, name: str = spec.name) -> None:
            if total:
                pct = done * 100 // total
                if pct != last[0] and (pct % 10 == 0 or pct == 100):
                    last[0] = pct
                    _err(f"Installing {name}… {pct}%")
            elif last[0] < 0:
                last[0] = 0
                _err(f"Installing {name}…")

        _err(f"Installing {spec.name}…")
        tools.install(spec, on_bytes)


# --- commands --------------------------------------------------------------


def _subs_value(raw: str | None) -> str:
    if raw is None:
        return SUBS_DEFAULT
    if raw.strip().lower() == SUBS_NONE:
        return SUBS_NONE
    return raw.strip()


def _run_get(service: Service, args: argparse.Namespace, cancel: threading.Event) -> dict[str, Any]:
    out = Path(args.out).resolve()
    try:
        out.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise friendly("write_failed", details=str(exc)) from exc
    _install_missing(service.tools)
    req = DownloadRequest(
        url=args.url,
        output_dir=out,
        mode="mp3" if args.audio else "mp4",
        quality=args.quality,
        subs=_subs_value(args.subs),
        save_note=not args.no_note,
        save_srt=args.srt,
        force=args.force,
    )
    result = service.download(req, None, _Sink(), cancel)
    return {
        "ok": True,
        "video_id": result.video_id,
        "title": result.title,
        "media": _path_or_none(result.media_path),
        "note": _path_or_none(result.note_path),
        "srt": _path_or_none(result.srt_path),
        "transcript": result.transcript,
        "already_exists": result.already_exists,
        "warnings": list(result.warnings),
    }


def _run_info(service: Service, args: argparse.Namespace) -> dict[str, Any]:
    _install_missing(service.tools)
    info = service.probe(args.url)
    return {
        "ok": True,
        "video_id": info.id,
        "title": info.title,
        "channel": info.channel,
        "url": info.url,
        "duration": info.duration,
        "published": info.published.isoformat() if info.published else None,
        "heights": list(info.heights),
        "subtitles": [{"lang": t.lang, "kind": t.kind} for t in info.subtitles],
    }


def _run_tools(service: Service, args: argparse.Namespace) -> dict[str, Any]:
    tools = service.tools
    _install_missing(tools)
    updated = None
    if args.update:

        def on_bytes_for(name: str) -> Callable[[int, int | None], None]:
            last = [-1]

            def on_bytes(done: int, total: int | None) -> None:
                if total:
                    pct = done * 100 // total
                    if pct != last[0] and (pct % 10 == 0 or pct == 100):
                        last[0] = pct
                        _err(f"Updating {name}… {pct}%")

            return on_bytes

        old, new = tools.update_all(on_bytes_for)
        updated = {"from": old, "to": new}
        try:
            current = settings_module.load_settings()
            current.last_update_check = time.time()
            settings_module.save_settings(current)
        except OSError:
            log.warning("Could not store the update check time", exc_info=True)
    p = tools.paths()
    return {
        "ok": True,
        "tools": {
            "yt-dlp": {"path": str(p.yt_dlp), "version": tools.ytdlp_version()},
            "ffmpeg": {"path": str(p.ffmpeg_dir)},
            "deno": {"path": str(p.deno)},
        },
        "updated": updated,
    }


def _human_output(payload: dict[str, Any], command: str) -> None:
    if command == "get":
        if payload["already_exists"]:
            print("Already downloaded.")
        if payload["media"]:
            print(f"Saved: {payload['media']}")
        if payload["note"]:
            print(f"Note: {payload['note']}")
        if payload["srt"]:
            print(f"Subtitles: {payload['srt']}")
        if payload["transcript"] != "none":
            print(f"Transcript: {payload['transcript']}")
        for warning in payload["warnings"]:
            print(f"Warning: {warning}")
    elif command == "info":
        print(f"Title: {payload['title']}")
        print(f"Channel: {payload['channel']}")
        print(f"URL: {payload['url']}")
        print(f"Duration: {payload['duration']}")
        print(f"Published: {payload['published']}")
        print(f"Heights: {', '.join(str(h) for h in payload['heights'])}")
        subs = ", ".join(f"{s['lang']} ({s['kind']})" for s in payload["subtitles"]) or "none"
        print(f"Subtitles: {subs}")
    else:
        for name, entry in payload["tools"].items():
            version = f" {entry['version']}" if entry.get("version") else ""
            print(f"{name}:{version} {entry['path']}")
        if payload["updated"]:
            print(f"yt-dlp updated: {payload['updated']['from']} -> {payload['updated']['to']}")


def _run_interruptible(work: Callable[[threading.Event], dict[str, Any]]) -> dict[str, Any]:
    """Run `work` in a thread; Ctrl+C sets the cancel event and waits for the clean-up."""
    cancel = threading.Event()
    box: dict[str, Any] = {}

    def target() -> None:
        try:
            box["result"] = work(cancel)
        except BaseException as exc:  # re-raised in the main thread
            box["error"] = exc

    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    interrupted = False
    while worker.is_alive():
        try:
            worker.join(0.2)
        except KeyboardInterrupt:
            interrupted = True
            cancel.set()
    if "error" in box:
        raise box["error"]
    if interrupted and "result" not in box:
        raise friendly("cancelled")
    return box["result"]


def main(argv: list[str], service_factory: Callable[[], Service] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)  # argparse exits with 2 on usage errors
    _utf8_stdout()
    try:
        setup_logging()
    except OSError as exc:  # unwritable profile: log to stderr only, still emit our output
        logging.basicConfig(level=logging.INFO, stream=sys.stderr)
        log.warning("File logging disabled: %s", exc)
    as_json = bool(getattr(args, "json", False))
    try:
        service = service_factory() if service_factory else Service(ToolManager())
        if args.command == "get":
            payload = _run_interruptible(lambda cancel: _run_get(service, args, cancel))
        elif args.command == "info":
            payload = _run_info(service, args)
        else:
            payload = _run_tools(service, args)
    except FriendlyError as exc:
        return _report_error(exc, as_json)
    except KeyboardInterrupt:
        return _report_error(friendly("cancelled"), as_json)
    except Exception as exc:
        log.exception("Unexpected CLI failure")
        return _report_error(friendly("unknown", details=f"{type(exc).__name__}: {exc}"), as_json)

    if as_json:
        _emit_json(payload)
    else:
        _human_output(payload, args.command)
    return EXIT_OK
