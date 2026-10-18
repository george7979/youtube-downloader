"""Main window — layout A: one column, link → video card → options → folder → download → recent."""

from __future__ import annotations

import io
import logging
import sys
import tkinter as tk
import urllib.request
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image, ImageOps

from ytdownloader import __version__
from ytdownloader.core.errors import FriendlyError, friendly
from ytdownloader.core.models import (
    SUBS_DEFAULT,
    SUBS_NONE,
    DownloadRequest,
    SubtitleTrack,
    VideoInfo,
)
from ytdownloader.core.note import format_ts
from ytdownloader.core.paths import resource_path
from ytdownloader.core.probe import pick_track
from ytdownloader.core.service import Service
from ytdownloader.core.settings import Settings, resolve_output_dir, save_settings
from ytdownloader.core.tools import ToolManager

from . import system
from .worker import UiQueue

log = logging.getLogger(__name__)

THUMB_SIZE = (160, 90)
THUMB_TIMEOUT_S = 10
PLACEHOLDER_RGB = (75, 85, 99)
DIM_TEXT = ("gray40", "gray60")
NO_SUBS = "None"
MODES = {"MP4": "mp4", "MP3": "mp3"}


def fetch_thumbnail(url: str) -> Image.Image | None:
    """Download and decode a thumbnail, cropped to THUMB_SIZE. Runs off the UI thread."""
    with urllib.request.urlopen(url, timeout=THUMB_TIMEOUT_S) as resp:
        data = resp.read()
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
        self._details_shown = False
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
                self.iconbitmap(str(ico))

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

        self._on_mode_change(mode)

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
        # Task 13 wires the command (download flow).
        self.download_button = ctk.CTkButton(
            self.download_box, text="Download", height=36, state="disabled"
        )
        self.download_button.pack(fill="x", padx=10, pady=(10, 6))
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
        # Task 13 fills the engine label (yt-dlp version and update state).
        self.engine_label = ctk.CTkLabel(
            self.footer, text="", font=self._font_small, text_color=DIM_TEXT
        )
        self.engine_label.pack(side="left")
        self.version_label = ctk.CTkLabel(
            self.footer, text=f"v{__version__}", font=self._font_small, text_color=DIM_TEXT
        )
        self.version_label.pack(side="right")

    # --- status --------------------------------------------------------------

    def set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def show_error(self, error: FriendlyError) -> None:
        self.set_status(error.message)

    # --- check flow ----------------------------------------------------------

    def check(self) -> None:
        url = self.url_entry.get().strip()
        self._check_seq += 1
        seq = self._check_seq
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
        self.set_status("Ready.")

    def _on_check_err(self, seq: int, exc: Exception) -> None:
        if seq != self._check_seq:
            return
        if not isinstance(exc, FriendlyError):
            log.error("Check failed", exc_info=exc)
            exc = friendly("unknown", details=repr(exc))
        self.show_error(exc)

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

        if not self._details_shown:
            self.card.pack(fill="x", pady=(0, 8), after=self.url_row)
            self.options.pack(fill="x", pady=(0, 8), after=self.card)
            self._details_shown = True
        self.download_button.configure(state="normal")

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

    def destroy(self) -> None:
        self.ui.close()
        # CustomTkinter keeps its own `after` loops (DPI scaling, redraws); cancel them so they
        # do not fire into a destroyed window ("invalid command name …" on stderr).
        for after_id in self.tk.splitlist(self.tk.call("after", "info")):
            self.after_cancel(after_id)
        super().destroy()
