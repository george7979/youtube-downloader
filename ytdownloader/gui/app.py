"""Main window — layout A: one column, link → video card → options → folder → download → recent."""

from __future__ import annotations

import dataclasses
import io
import logging
import sys
import threading
import time
import tkinter as tk
import traceback
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image, ImageOps

from ytdownloader import __version__
from ytdownloader.core import paths
from ytdownloader.core.errors import FriendlyError, friendly
from ytdownloader.core.models import (
    SUBS_DEFAULT,
    SUBS_NONE,
    DownloadRequest,
    DownloadResult,
    Progress,
    Status,
    SubtitleTrack,
    VideoInfo,
)
from ytdownloader.core.note import format_ts
from ytdownloader.core.paths import resource_path
from ytdownloader.core.probe import pick_track
from ytdownloader.core.service import Service
from ytdownloader.core.settings import (
    RecentItem,
    Settings,
    add_recent,
    resolve_output_dir,
    save_settings,
)
from ytdownloader.core.tools import ToolManager, should_check_update

from . import system
from .first_run import size_text
from .widgets import ErrorPanel, ask_already_downloaded, show_about
from .worker import UiQueue, cancel_pending_after

log = logging.getLogger(__name__)

THUMB_SIZE = (160, 90)
THUMB_TIMEOUT_S = 10
THUMB_MAX_BYTES = 5 * 1024 * 1024
PLACEHOLDER_RGB = (75, 85, 99)
DIM_TEXT = ("gray40", "gray60")
NO_SUBS = "None"
MODES = {"MP4": "mp4", "MP3": "mp3"}
MENU_UPDATE = 0  # index of "Update engine" in the footer menu


def _traceback_text(exc: BaseException) -> str:
    return "".join(traceback.format_exception(exc))


def _as_friendly(exc: Exception, what: str) -> FriendlyError:
    """Known errors pass through; anything else is logged and becomes `unknown` + traceback."""
    if isinstance(exc, FriendlyError):
        log.warning("%s failed [%s]: %s", what, exc.code, exc.details)
        return exc
    log.error("%s failed", what, exc_info=exc)
    return friendly("unknown", details=_traceback_text(exc))


def fetch_thumbnail(url: str) -> Image.Image | None:
    """Download and decode a thumbnail, cropped to THUMB_SIZE. Runs off the UI thread."""
    if urllib.parse.urlsplit(url).scheme.lower() not in ("http", "https"):
        raise ValueError(f"not an http(s) thumbnail URL: {url!r}")
    with urllib.request.urlopen(url, timeout=THUMB_TIMEOUT_S) as resp:
        data = resp.read(THUMB_MAX_BYTES + 1)
    if len(data) > THUMB_MAX_BYTES:
        raise ValueError(f"thumbnail larger than {THUMB_MAX_BYTES} bytes")
    with Image.open(io.BytesIO(data)) as img:
        return ImageOps.fit(img.convert("RGB"), THUMB_SIZE)


def _placeholder() -> Image.Image:
    return Image.new("RGB", THUMB_SIZE, PLACEHOLDER_RGB)


def _shorten_end(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _shorten_start(text: str, limit: int) -> str:
    return text if len(text) <= limit else "…" + text[-(limit - 1) :]


def meta_line(info: VideoInfo) -> str:
    duration = None
    if info.duration is not None:
        duration = format_ts(info.duration, info.duration >= 3600)
    published = info.published.isoformat() if info.published else None
    return " · ".join(part for part in (info.channel, duration, published) if part)


def subtitles_line(info: VideoInfo) -> str:
    if not info.subtitles:
        return "Subtitles: none"
    return "Subtitles: " + ", ".join(t.label() for t in info.subtitles)


def _default_height(heights: list[int], wanted: int) -> int:
    fitting = [h for h in heights if h <= wanted]
    return fitting[0] if fitting else heights[-1]


class MainWindow(ctk.CTk):
    def __init__(self, service: Service, tools: ToolManager, settings: Settings):
        ctk.set_appearance_mode("system")
        super().__init__()
        self.service = service
        self.tools = tools
        self.settings = settings
        self.ui = UiQueue(self)

        self._info: VideoInfo | None = None
        self._tracks_by_label: dict[str, SubtitleTrack] = {}
        self._check_seq = 0
        # A download "runs" from the click until its result is handled — also while it waits
        # for an engine update (`_pending`) and while the already-downloaded dialog is open.
        self.downloading = False
        self._cancel: threading.Event | None = None
        self._pending: tuple[DownloadRequest, VideoInfo] | None = None
        self._download_idle = threading.Event()  # clear while service.download() runs
        self._download_idle.set()
        self._indeterminate = False
        self._engine_busy = False  # startup update or "Update engine" in progress
        self._ytdlp_version: str | None = None
        self._thumb_image: ctk.CTkImage | None = None
        self.recent_labels: list[ctk.CTkLabel] = []

        self.title(f"YouTube Downloader {__version__}")
        self.geometry("540x780")
        self.minsize(480, 640)
        self._set_icon()

        self._font_title = ctk.CTkFont(size=14, weight="bold")
        self._font_small = ctk.CTkFont(size=12)
        self._font_heading = ctk.CTkFont(size=11, weight="bold")

        self._build_footer()
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=6, pady=(6, 0))
        self._build_url_row()
        self._build_card()
        self._build_options()
        self._build_folder_row()
        self._build_download()
        self._build_recent()

        self._output_dir, warning = resolve_output_dir(settings)
        self._show_output_dir()
        if warning:
            self.set_status(warning)
        self.refresh_recent()

    # --- building ------------------------------------------------------------

    def _set_icon(self) -> None:
        png = resource_path("icons/youtube-downloader-32.png")
        if png.is_file():
            try:
                self._icon = tk.PhotoImage(master=self, file=str(png))
                self.iconphoto(True, self._icon)
            except tk.TclError:
                log.warning("Could not load window icon %s", png, exc_info=True)
        if sys.platform == "win32":
            ico = resource_path("icons/youtube-downloader.ico")
            if ico.is_file():
                try:
                    self.iconbitmap(str(ico))
                except tk.TclError:
                    log.warning("Could not load window icon %s", ico, exc_info=True)

    def _section(self) -> ctk.CTkFrame:
        return ctk.CTkFrame(self.body)

    def _build_url_row(self) -> None:
        self.url_row = ctk.CTkFrame(self.body, fg_color="transparent")
        self.url_row.pack(fill="x", pady=(0, 8))
        self.url_entry = ctk.CTkEntry(self.url_row, placeholder_text="Paste a YouTube link")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.url_entry.bind("<Return>", lambda _e: self.check())
        self.check_button = ctk.CTkButton(self.url_row, text="Check", width=80, command=self.check)
        self.check_button.pack(side="left")

    def _build_card(self) -> None:
        self.card = self._section()
        self.card.grid_columnconfigure(1, weight=1)
        self.thumb_label = ctk.CTkLabel(self.card, text="")
        self.thumb_label.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="n")
        self.title_label = ctk.CTkLabel(
            self.card, text="", font=self._font_title, wraplength=330, justify="left", anchor="w"
        )
        self.title_label.grid(row=0, column=1, padx=(0, 10), pady=(10, 2), sticky="w")
        self.meta_label = ctk.CTkLabel(
            self.card, text="", font=self._font_small, text_color=DIM_TEXT, anchor="w"
        )
        self.meta_label.grid(row=1, column=1, padx=(0, 10), sticky="w")
        self.subs_line_label = ctk.CTkLabel(
            self.card, text="", font=self._font_small, text_color=DIM_TEXT, anchor="w"
        )
        self.subs_line_label.grid(row=2, column=1, padx=(0, 10), pady=(0, 10), sticky="nw")

    def _build_options(self) -> None:
        self.options = self._section()
        self.options.grid_columnconfigure(1, weight=1)

        mode = "MP3" if self.settings.mode == "mp3" else "MP4"
        self.mode_switch = ctk.CTkSegmentedButton(
            self.options, values=list(MODES), command=self._on_mode_change
        )
        self.mode_switch.set(mode)
        self.mode_switch.grid(row=0, column=0, padx=10, pady=(10, 6), sticky="w")

        quality_row = ctk.CTkFrame(self.options, fg_color="transparent")
        quality_row.grid(row=0, column=1, padx=10, pady=(10, 6), sticky="e")
        ctk.CTkLabel(quality_row, text="Quality").pack(side="left", padx=(0, 6))
        self.quality_menu = ctk.CTkOptionMenu(quality_row, values=[""], width=100)
        self.quality_menu.pack(side="left")

        subs_row = ctk.CTkFrame(self.options, fg_color="transparent")
        subs_row.grid(row=1, column=0, columnspan=2, padx=10, pady=6, sticky="w")
        ctk.CTkLabel(subs_row, text="Subtitles").pack(side="left", padx=(0, 6))
        self.subs_menu = ctk.CTkOptionMenu(subs_row, values=[NO_SUBS], width=140)
        self.subs_menu.pack(side="left")

        checks = ctk.CTkFrame(self.options, fg_color="transparent")
        checks.grid(row=2, column=0, columnspan=2, padx=10, pady=(6, 10), sticky="w")
        self.note_var = tk.BooleanVar(master=self, value=self.settings.save_note)
        self.srt_var = tk.BooleanVar(master=self, value=self.settings.save_srt)
        self.note_check = ctk.CTkCheckBox(checks, text="Save note (.md)", variable=self.note_var)
        self.note_check.pack(side="left", padx=(0, 16))
        self.srt_check = ctk.CTkCheckBox(checks, text="Also save .srt", variable=self.srt_var)
        self.srt_check.pack(side="left")

        self._reset_options()
        self._on_mode_change(mode)
        self.options.pack(fill="x", pady=(0, 8))

    def _build_folder_row(self) -> None:
        self.folder_row = self._section()
        self.folder_row.pack(fill="x", pady=(0, 8))
        self.folder_label = ctk.CTkLabel(self.folder_row, text="", anchor="w")
        self.folder_label.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.open_folder_button = ctk.CTkButton(
            self.folder_row, text="Open folder", width=96, command=self.open_folder
        )
        self.open_folder_button.pack(side="right", padx=(0, 10))
        self.change_button = ctk.CTkButton(
            self.folder_row, text="Change", width=72, command=self.change_folder
        )
        self.change_button.pack(side="right", padx=(0, 6))

    def _build_download(self) -> None:
        self.download_box = self._section()
        self.download_box.pack(fill="x", pady=(0, 8))
        buttons = ctk.CTkFrame(self.download_box, fg_color="transparent")
        buttons.pack(fill="x", padx=10, pady=(10, 6))
        self.download_button = ctk.CTkButton(
            buttons, text="Download", height=36, state="disabled", command=self.download
        )
        self.download_button.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.cancel_button = ctk.CTkButton(
            buttons, text="Cancel", width=90, height=36, state="disabled", command=self.cancel
        )
        self.cancel_button.pack(side="right")
        self.progress_bar = ctk.CTkProgressBar(self.download_box)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 4))
        self.status_label = ctk.CTkLabel(
            self.download_box,
            text="",
            font=self._font_small,
            anchor="w",
            justify="left",
            wraplength=440,
        )
        self.status_label.pack(fill="x", padx=10, pady=(0, 8))
        self.error_panel = ErrorPanel(
            self.download_box,
            pack_opts={"fill": "x", "padx": 10, "pady": (0, 10)},
            on_update_engine=self.update_engine,
        )

    def _build_recent(self) -> None:
        self.recent_box = self._section()
        self.recent_box.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            self.recent_box, text="RECENT DOWNLOADS", font=self._font_heading, text_color=DIM_TEXT
        ).pack(anchor="w", padx=10, pady=(8, 2))
        self.recent_rows = ctk.CTkFrame(self.recent_box, fg_color="transparent")
        self.recent_rows.pack(fill="x", padx=10, pady=(0, 8))

    def _build_footer(self) -> None:
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(side="bottom", fill="x", padx=16, pady=(4, 8))
        self.engine_label = ctk.CTkLabel(
            self.footer, text="yt-dlp", font=self._font_small, text_color=DIM_TEXT
        )
        self.engine_label.pack(side="left")
        self.menu_button = ctk.CTkButton(
            self.footer, text="⋯", width=32, height=24, command=self._open_menu
        )
        self.menu_button.pack(side="right", padx=(8, 0))
        self.version_label = ctk.CTkLabel(
            self.footer, text=f"v{__version__}", font=self._font_small, text_color=DIM_TEXT
        )
        self.version_label.pack(side="right")
        self.engine_menu = tk.Menu(self, tearoff=False)
        self.engine_menu.add_command(label="Update engine", command=self.update_engine)
        self.engine_menu.add_command(label="Open log folder", command=self.open_log_folder)
        self.engine_menu.add_command(label="About", command=self.about)

    def _open_menu(self) -> None:
        x = self.menu_button.winfo_rootx()
        y = self.menu_button.winfo_rooty() - self.engine_menu.winfo_reqheight()
        try:
            self.engine_menu.tk_popup(x, y)
        finally:
            self.engine_menu.grab_release()

    # --- status --------------------------------------------------------------

    def set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def show_error(self, error: FriendlyError) -> None:
        if not self.downloading:  # a running download keeps its own status line
            self.set_status("")
        self.error_panel.show(error)

    # --- check flow ----------------------------------------------------------

    def update_download_button(self) -> None:
        """Download is enabled iff a video is checked and no download is running."""
        ready = self._info is not None and not self.downloading
        self.download_button.configure(state="normal" if ready else "disabled")

    def check(self) -> None:
        url = self.url_entry.get().strip()
        self._check_seq += 1
        seq = self._check_seq
        self._clear_info()
        self.error_panel.clear()
        # During a download the status line belongs to it (e.g. "Merging into MP4…" has no
        # further events); the card and options still show the Check's result.
        if not self.downloading:
            self.set_status("Fetching video info…")
        self.ui.run_bg(
            lambda: self.service.probe(url),
            lambda info: self._on_check_ok(seq, info),
            lambda exc: self._on_check_err(seq, exc),
        )

    def _on_check_ok(self, seq: int, info: VideoInfo) -> None:
        if seq != self._check_seq:
            return
        self.apply_info(info)
        if not self.downloading:
            self.set_status("Ready.")

    def _on_check_err(self, seq: int, exc: Exception) -> None:
        if seq != self._check_seq:
            return
        self.show_error(_as_friendly(exc, "Check"))

    def apply_info(self, info: VideoInfo) -> None:
        self._info = info
        self.title_label.configure(text=info.title)
        self.meta_label.configure(text=meta_line(info))
        self.subs_line_label.configure(text=subtitles_line(info))
        self._set_thumbnail(_placeholder())
        if info.thumbnail:
            self._load_thumbnail(info)

        if info.heights:
            values = [f"{h}p" for h in info.heights]
            default = f"{_default_height(info.heights, self.settings.quality)}p"
        else:
            default = f"{self.settings.quality}p"
            values = [default]
        self.quality_menu.configure(values=values)
        self.quality_menu.set(default)

        self._tracks_by_label = {t.label(): t for t in info.subtitles}
        track, _warning = pick_track(info, SUBS_DEFAULT, self.settings.subs_lang)
        self.subs_menu.configure(values=[NO_SUBS, *self._tracks_by_label])
        self.subs_menu.set(track.label() if track else NO_SUBS)

        if not self.card.winfo_manager():
            self.card.pack(fill="x", pady=(0, 8), after=self.url_row)
        self.update_download_button()

    def _clear_info(self) -> None:
        """Forget the checked video so nothing can target it: hide the card, reset options."""
        self._info = None
        self.card.pack_forget()
        self._reset_options()
        self.update_download_button()

    def _reset_options(self) -> None:
        default = f"{self.settings.quality}p"
        self.quality_menu.configure(values=[default])
        self.quality_menu.set(default)
        self._tracks_by_label = {}
        self.subs_menu.configure(values=[NO_SUBS])
        self.subs_menu.set(NO_SUBS)

    def _set_thumbnail(self, img: Image.Image) -> None:
        self._thumb_image = ctk.CTkImage(light_image=img, dark_image=img, size=THUMB_SIZE)
        self.thumb_label.configure(image=self._thumb_image)

    def _load_thumbnail(self, info: VideoInfo) -> None:
        def on_ok(img: Image.Image | None) -> None:
            if img is not None and self._info is info:
                self._set_thumbnail(img)

        def on_err(exc: Exception) -> None:
            log.info("Thumbnail not loaded for %s: %s", info.id, exc)

        self.ui.run_bg(lambda: fetch_thumbnail(info.thumbnail), on_ok, on_err)

    def _on_mode_change(self, value: str) -> None:
        self.quality_menu.configure(state="disabled" if value == "MP3" else "normal")

    def selected_request(self) -> DownloadRequest:
        url = self._info.url if self._info else self.url_entry.get().strip()
        try:
            quality = int(self.quality_menu.get().removesuffix("p"))
        except ValueError:
            quality = self.settings.quality
        label = self.subs_menu.get()
        if label == NO_SUBS:
            subs = SUBS_NONE
        elif label in self._tracks_by_label:
            subs = self._tracks_by_label[label].lang
        else:
            subs = SUBS_DEFAULT
        return DownloadRequest(
            url=url,
            output_dir=self._output_dir,
            mode=MODES[self.mode_switch.get()],
            quality=quality,
            subs=subs,
            save_note=self.note_var.get(),
            save_srt=self.srt_var.get(),
        )

    # --- download flow -------------------------------------------------------

    def download(self) -> None:
        if self._info is None or self.downloading:
            return
        # Captured now: a Check during the download replaces `_info` and the options.
        req, info = self.selected_request(), self._info
        self.error_panel.clear()
        self.downloading = True
        self._cancel = threading.Event()
        self._sync_controls()
        self._reset_progress()
        if self._engine_busy:
            self._pending = (req, info)
            self.set_status("Waiting for engine update to finish…")
            return
        self._run_download(req, info)

    def cancel(self) -> None:
        if not self.downloading or self._cancel is None:
            return
        self._cancel.set()
        self.cancel_button.configure(state="disabled")
        if self._pending is not None:  # still waiting for the engine: nothing to stop
            self._finish_download()
            self.set_status("Cancelled.")
            return
        self.set_status("Cancelling…")

    def _run_download(self, req: DownloadRequest, info: VideoInfo) -> None:
        cancel = self._cancel
        remembered = self.settings.subs_lang
        self.set_status("Starting download…")

        idle = self._download_idle
        idle.clear()

        def sink(event: Status | Progress) -> None:  # worker thread
            self.ui.post(lambda: self._on_event(event, cancel))

        def work() -> DownloadResult:  # worker thread
            try:
                return self.service.download(req, info, sink, cancel, remembered)
            finally:
                idle.set()  # set from the worker: the UI queue may no longer run at exit

        self.ui.run_bg(
            work,
            lambda result: self._on_download_ok(req, info, result),
            self._on_download_err,
        )

    def _on_event(self, event: Status | Progress, cancel: threading.Event) -> None:
        if cancel.is_set():  # keep "Cancelling…" until the run ends
            return
        self.set_status(event.text)
        if isinstance(event, Progress):
            if event.fraction is None:
                if not self._indeterminate:
                    self._indeterminate = True
                    self.progress_bar.configure(mode="indeterminate")
                    self.progress_bar.start()
            else:
                self._stop_indeterminate()
                self.progress_bar.set(event.fraction)

    def _on_download_ok(
        self, req: DownloadRequest, info: VideoInfo, result: DownloadResult
    ) -> None:
        self._stop_indeterminate()
        if result.already_exists:
            self.progress_bar.set(0)
            self.cancel_button.configure(state="disabled")
            # Out of the UI-queue drain: the modal dialog runs a nested event loop.
            self.after(0, lambda: self._ask_already(req, info, result))
            return
        self._finish_download()
        self.progress_bar.set(1.0)
        name = result.media_path.name if result.media_path else result.title
        parts = [f"Done. Saved {name}", *result.warnings]
        if not self._remember(req, info, result):
            parts.append("Settings could not be saved.")
        self.set_status(" · ".join(parts))
        self.refresh_recent()

    def _ask_already(self, req: DownloadRequest, info: VideoInfo, result: DownloadResult) -> None:
        choice = ask_already_downloaded(self, result.title, has_note=result.note_path is not None)
        if choice == "again":
            self._cancel = threading.Event()
            self.cancel_button.configure(state="normal")
            self._run_download(dataclasses.replace(req, force=True), info)
            return
        self._finish_download()
        self.set_status("Already downloaded.")
        if choice == "show" and result.media_path is not None:
            system.show_file(result.media_path)

    def _on_download_err(self, exc: Exception) -> None:
        self._finish_download()
        self._reset_progress()
        if isinstance(exc, FriendlyError) and exc.code == "cancelled":
            self.set_status("Cancelled.")
            return
        error = _as_friendly(exc, "Download")
        self.set_status("Download failed.")
        self.error_panel.show(error)

    def _remember(self, req: DownloadRequest, info: VideoInfo, result: DownloadResult) -> bool:
        """Persist the options of a successful download and add it to Recent downloads."""
        s = self.settings
        s.mode = req.mode
        # The stored quality is a ceiling: a 720p-max video must not lower it for later videos.
        default = _default_height(info.heights, s.quality) if info.heights else s.quality
        if req.quality != default:
            s.quality = req.quality
        if req.subs not in (SUBS_NONE, SUBS_DEFAULT):
            s.subs_lang = req.subs
        s.save_note = req.save_note
        s.save_srt = req.save_srt
        if result.media_path is not None:
            add_recent(
                s,
                RecentItem(
                    video_id=result.video_id,
                    title=result.title,
                    media_path=str(result.media_path),
                    downloaded=date.today().isoformat(),
                ),
            )
        return self._save_settings()

    def _save_settings(self) -> bool:
        try:
            save_settings(self.settings)
        except OSError:
            log.warning("Could not save settings", exc_info=True)
            return False
        return True

    def _finish_download(self) -> None:
        self.downloading = False
        self._cancel = None
        self._pending = None
        self._sync_controls()

    def _sync_controls(self) -> None:
        self.update_download_button()
        self.cancel_button.configure(state="normal" if self.downloading else "disabled")
        can_update = not (self.downloading or self._engine_busy)
        self.engine_menu.entryconfigure(MENU_UPDATE, state="normal" if can_update else "disabled")

    def _reset_progress(self) -> None:
        self._stop_indeterminate()
        self.progress_bar.set(0)

    def _stop_indeterminate(self) -> None:
        if self._indeterminate:
            self._indeterminate = False
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")

    # --- engine status -------------------------------------------------------

    def start_engine_status(self, now: float | None = None) -> None:
        """Show the yt-dlp version; once a day also update yt-dlp in the background."""
        now = time.time() if now is None else now
        check = should_check_update(self.settings.last_update_check, now)
        if check:
            self._set_engine_busy(True)
        self.ui.run_bg(
            self.tools.ytdlp_version,
            lambda version: self._on_version(version, check, now),
            lambda exc: self._on_version(None, check, now, exc),
        )

    def _on_version(
        self, version: str | None, check: bool, now: float, exc: Exception | None = None
    ) -> None:
        if exc is not None:
            log.warning("Could not read the yt-dlp version", exc_info=exc)
        self._ytdlp_version = version
        if not check:
            self._show_engine()
            return
        self._show_engine("checking for updates…")
        self.ui.run_bg(
            self.tools.update_ytdlp,
            lambda versions: self._on_startup_update(versions, now),
            lambda err: self._on_startup_update(None, now, err),
        )

    def _on_startup_update(
        self,
        versions: tuple[str | None, str | None] | None,
        now: float,
        exc: Exception | None = None,
    ) -> None:
        old, new = versions if versions is not None else (self._ytdlp_version, None)
        if exc is not None:
            log.warning("yt-dlp update failed", exc_info=exc)
        if new is None:
            if exc is None:
                log.warning("yt-dlp update failed (offline, or yt-dlp -U exited with an error)")
            # Not stored: the next start tries again instead of waiting a day.
            self._show_engine("update failed")
        else:
            self._ytdlp_version = new
            self._show_engine("updated" if new != old else "up to date")
            self.settings.last_update_check = now
            self._save_settings()
        self._set_engine_busy(False)

    def update_engine(self) -> None:
        if self.downloading:
            self.set_status("Can't update the engine while a download is running.")
            return
        if self._engine_busy:
            return
        self._set_engine_busy(True)
        self.engine_label.configure(text="Updating engine…")
        self.ui.run_bg(
            lambda: self.tools.update_all(self._engine_bytes_for),
            self._on_engine_updated,
            self._on_engine_update_failed,
        )

    def _engine_bytes_for(self, name: str):
        last = [""]

        def on_bytes(done: int, total: int | None) -> None:  # worker thread
            text = f"Updating engine… {name} {size_text(done, total)}"
            if text != last[0]:
                last[0] = text
                self.ui.post(lambda: self.engine_label.configure(text=text))

        return on_bytes

    def _on_engine_updated(self, versions: tuple[str | None, str | None]) -> None:
        _old, new = versions
        if new is None:
            log.warning("Engine update failed: yt-dlp -U failed or yt-dlp does not run")
            self._show_engine("update failed")
        else:
            self._ytdlp_version = new
            self._show_engine()
            self.settings.last_update_check = time.time()
            self._save_settings()
        self._set_engine_busy(False)

    def _on_engine_update_failed(self, exc: Exception) -> None:
        details = exc.details if isinstance(exc, FriendlyError) else _traceback_text(exc)
        log.warning("Engine update failed: %s", details)
        self._show_engine("update failed")
        self.error_panel.show(
            FriendlyError(
                "update_failed",
                "Engine update failed.",
                "Check your internet connection and try again.",
                details,
            )
        )
        self._set_engine_busy(False)

    def _show_engine(self, state: str | None = None) -> None:
        text = f"yt-dlp {self._ytdlp_version or '(version unknown)'}"
        self.engine_label.configure(text=f"{text} · {state}" if state else text)

    def _set_engine_busy(self, busy: bool) -> None:
        self._engine_busy = busy
        self._sync_controls()
        if not busy and self._pending is not None:
            req, info = self._pending
            self._pending = None
            self._run_download(req, info)

    def open_log_folder(self) -> None:
        try:
            folder = paths.log_dir()
        except OSError as exc:
            log.warning("Log folder not available", exc_info=True)
            self.set_status(f"Can't open the log folder: {exc}")
            return
        system.open_folder(folder)

    def about(self) -> None:
        show_about(self, __version__, self._ytdlp_version)

    # --- folder --------------------------------------------------------------

    def _show_output_dir(self) -> None:
        self.folder_label.configure(text=_shorten_start(str(self._output_dir), 42))

    def change_folder(self) -> None:
        chosen = filedialog.askdirectory(
            parent=self, initialdir=str(self._output_dir), title="Choose download folder"
        )
        if not chosen:
            return
        self._output_dir = Path(chosen)
        self.settings.output_dir = str(self._output_dir)
        self._show_output_dir()
        try:
            save_settings(self.settings)
        except OSError:
            log.warning("Could not save settings", exc_info=True)

    def open_folder(self) -> None:
        system.open_folder(self._output_dir)

    # --- recent downloads ----------------------------------------------------

    def refresh_recent(self) -> None:
        for child in self.recent_rows.winfo_children():
            child.destroy()
        self.recent_labels = []
        for item in self.settings.recent:
            path = Path(item.media_path)
            present = path.is_file()
            row = ctk.CTkFrame(self.recent_rows, fg_color="transparent")
            row.pack(fill="x", pady=1)
            text = _shorten_end(item.title, 46)
            if not present:
                text += "  (file missing)"
            label = ctk.CTkLabel(row, text=text, font=self._font_small, anchor="w")
            if not present:
                label.configure(text_color=DIM_TEXT)
            label.pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row,
                text="Show file",
                width=80,
                height=24,
                font=self._font_small,
                state="normal" if present else "disabled",
                command=lambda p=path: system.show_file(p),
            ).pack(side="right")
            self.recent_labels.append(label)

    # --- lifecycle -----------------------------------------------------------

    def wait_for_download(self, timeout: float) -> bool:
        """Block until no service.download() is running (thread-safe); False on timeout."""
        return self._download_idle.wait(timeout)

    def destroy(self) -> None:
        # Closing mid-download cancels it: the engine kills the yt-dlp/ffmpeg tree and the
        # service deletes partial files. run() waits for that via wait_for_download().
        if self._cancel is not None:
            self._cancel.set()
        self.ui.close()
        cancel_pending_after(self)
        super().destroy()
