"""Reusable GUI pieces: the error panel and the small dialogs."""

from __future__ import annotations

import logging
import sys
import tkinter as tk
import webbrowser
from collections.abc import Callable

import customtkinter as ctk
from PIL import Image, ImageDraw

from ytdownloader.core.errors import FriendlyError
from ytdownloader.core.paths import resource_path

from .theme import DIM_TEXT, ERROR_BG, ERROR_BORDER, ERROR_TEXT, OUTLINE_BUTTON, TEXT_BUTTON

log = logging.getLogger(__name__)


def set_window_icon(root: tk.Tk) -> None:
    """The app icon on a root window. On Windows CustomTkinter puts its own icon on every CTk
    root shortly after creation unless iconbitmap() was called, so the .ico is set there too."""
    png = resource_path("icons/youtube-downloader-32.png")
    if png.is_file():
        try:
            root._app_icon = tk.PhotoImage(master=root, file=str(png))  # keep a reference
            root.iconphoto(True, root._app_icon)
        except tk.TclError:
            log.warning("Could not load window icon %s", png, exc_info=True)
    if sys.platform == "win32":
        ico = resource_path("icons/youtube-downloader.ico")
        if ico.is_file():
            try:
                root.iconbitmap(str(ico))
            except tk.TclError:
                log.warning("Could not load window icon %s", ico, exc_info=True)

REPO_URL = "https://github.com/george7979/youtube-downloader"
LINK_TEXT = ("#1d4ed8", "#93c5fd")
WRAP = 420
ENGINE_FIXABLE = frozenset({"bot_check", "engine_outdated", "forbidden"})  # errors an engine update may fix


def _error_icon() -> ctk.CTkImage:
    """A circled exclamation mark in the error colour, drawn at 2x for sharp HiDPI rendering."""

    def draw(colour: str) -> Image.Image:
        img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        pen = ImageDraw.Draw(img)
        pen.ellipse((2, 2, 29, 29), outline=colour, width=3)
        pen.line((16, 8, 16, 19), fill=colour, width=3)
        pen.ellipse((14, 22, 18, 26), fill=colour)
        return img

    return ctk.CTkImage(light_image=draw(ERROR_TEXT[0]), dark_image=draw(ERROR_TEXT[1]), size=(16, 16))


class ErrorPanel(ctk.CTkFrame):
    """What happened, what to do, and technical details folded under "Show details".

    The panel shows itself on `show()` (packed with `pack_opts`) and hides on `clear()`.
    With `on_update_engine`, errors an engine update may fix also offer an "Update engine" button.
    """

    def __init__(
        self,
        master,
        pack_opts: dict | None = None,
        on_update_engine: Callable[[], None] | None = None,
        on_layout: Callable[[], None] | None = None,
        **kwargs,
    ):
        kwargs.setdefault("fg_color", ERROR_BG)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", ERROR_BORDER)
        super().__init__(master, **kwargs)
        self._pack_opts = pack_opts or {"fill": "x"}
        self._on_layout = on_layout  # called after the panel grows (shown, details expanded)
        self._details = ""
        self._on_update_engine = on_update_engine

        self.message_row = ctk.CTkFrame(self, fg_color="transparent")
        self.message_row.pack(fill="x", padx=10, pady=(8, 0))
        ctk.CTkLabel(self.message_row, text="", image=_error_icon(), width=16).pack(
            side="left", padx=(0, 8)
        )
        self.message_label = ctk.CTkLabel(
            self.message_row,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ERROR_TEXT,
            wraplength=WRAP - 24,
            justify="left",
            anchor="w",
        )
        self.message_label.pack(side="left", fill="x", expand=True)
        self.hint_label = ctk.CTkLabel(self, text="", wraplength=WRAP, justify="left", anchor="w")
        self.hint_label.pack(fill="x", padx=10)
        self.update_button = ctk.CTkButton(
            self,
            text="Update engine",
            width=120,
            height=26,
            command=self._update_engine,
            **OUTLINE_BUTTON,
        )
        self.details_button = ctk.CTkButton(
            self, text="Show details", width=96, height=24, command=self.toggle_details, **TEXT_BUTTON
        )
        self.details_button.pack(anchor="w", padx=10, pady=(4, 8))

        self.details_box = ctk.CTkFrame(self, fg_color="transparent")
        self.details_text = ctk.CTkTextbox(self.details_box, height=120, wrap="word")
        self.details_text.pack(fill="x")
        self.copy_button = ctk.CTkButton(
            self.details_box, text="Copy", width=56, height=24, command=self.copy_details, **TEXT_BUTTON
        )
        self.copy_button.pack(anchor="e", pady=(4, 0))

    def show(self, err: FriendlyError) -> None:
        self._details = err.details or ""
        self.message_label.configure(text=err.message)
        self.hint_label.configure(text=err.hint)
        if err.hint:
            self.hint_label.pack(fill="x", padx=10, after=self.message_row)
        else:
            self.hint_label.pack_forget()
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", "end")
        self.details_text.insert("1.0", self._details)
        self.details_text.configure(state="disabled")
        self._collapse()
        self.update_button.pack_forget()
        self.details_button.pack_forget()
        if self._on_update_engine is not None and err.code in ENGINE_FIXABLE:
            self.update_button.pack(anchor="w", padx=10, pady=(4, 0 if self._details else 8))
        if self._details:
            self.details_button.pack(anchor="w", padx=10, pady=(4, 8))
        self.pack(**self._pack_opts)
        self._layout_changed()

    def _layout_changed(self) -> None:
        if self._on_layout is not None:
            self._on_layout()

    def _update_engine(self) -> None:
        if self._on_update_engine is not None:
            self._on_update_engine()

    def clear(self) -> None:
        self.pack_forget()
        self._collapse()

    def toggle_details(self) -> None:
        if self.details_box.winfo_manager():
            self._collapse()
        else:
            self.details_box.pack(fill="x", padx=10, pady=(0, 10))
            self.details_button.configure(text="Hide details")
            self._layout_changed()

    def copy_details(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self._details)

    def _collapse(self) -> None:
        self.details_box.pack_forget()
        self.details_button.configure(text="Show details")


def ask_already_downloaded(
    parent,
    title: str,
    has_note: bool = True,
    add_lang: str | None = None,
    note_lang: str | None = None,
    srt_lang: str | None = None,
) -> str:
    """Modal: the video (and its note) are already in the folder.

    Returns add | srt | show | again | cancel; "add" only when `add_lang` offers a transcript
    note, "srt" only when `srt_lang` offers subtitles and no transcript can be added.
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title("Already downloaded")
    dialog.resizable(False, False)
    dialog.transient(parent)
    choice = {"value": "cancel"}

    def pick(value: str) -> None:
        choice["value"] = value
        dialog.destroy()

    ctk.CTkLabel(
        dialog, text="Already downloaded", font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
    ).pack(fill="x", padx=16, pady=(14, 2))
    ctk.CTkLabel(dialog, text=title, wraplength=360, justify="left", anchor="w").pack(
        fill="x", padx=16
    )
    ctk.CTkLabel(
        dialog,
        text=(
            f"The video and its note (transcript: {note_lang}) are already in this folder."
            if has_note and note_lang
            else "The video and its note are already in this folder."
            if has_note
            else "The video is already in this folder."
        ),
        text_color=DIM_TEXT,
        anchor="w",
    ).pack(fill="x", padx=16, pady=(2, 10))

    row = ctk.CTkFrame(dialog, fg_color="transparent")
    row.pack(fill="x", padx=16, pady=(0, 14))
    dialog.buttons = {}
    if add_lang:  # the only filled button: the obvious next step
        dialog.buttons["add"] = ctk.CTkButton(
            row,
            text=f"Add transcript ({add_lang})",
            width=150,
            command=lambda: pick("add"),
        )
    elif srt_lang:  # at most one filled button: subtitles only when no transcript can be added
        dialog.buttons["srt"] = ctk.CTkButton(
            row,
            text=f"Add subtitles ({srt_lang})",
            width=150,
            command=lambda: pick("srt"),
        )
    # Without an addable language no button is filled: neither choice is the obvious one.
    dialog.buttons |= {
        "show": ctk.CTkButton(
            row, text="Show file", width=96, command=lambda: pick("show"), **OUTLINE_BUTTON
        ),
        "again": ctk.CTkButton(
            row, text="Download again", width=120, command=lambda: pick("again"), **OUTLINE_BUTTON
        ),
        "cancel": ctk.CTkButton(
            row, text="Cancel", width=72, command=lambda: pick("cancel"), **TEXT_BUTTON
        ),
    }
    for button in dialog.buttons.values():
        button.pack(side="left", padx=(0, 8))

    dialog.protocol("WM_DELETE_WINDOW", lambda: pick("cancel"))
    dialog.bind("<Escape>", lambda _e: pick("cancel"))
    try:
        dialog.grab_set()
    except tk.TclError:  # not viewable yet on some window managers; stays non-modal
        log.info("Could not grab the already-downloaded dialog", exc_info=True)
    parent.wait_window(dialog)
    return choice["value"]


def show_about(parent, app_version: str, ytdlp_version: str | None) -> None:
    dialog = ctk.CTkToplevel(parent)
    dialog.title("About")
    dialog.resizable(False, False)
    dialog.transient(parent)
    ctk.CTkLabel(
        dialog,
        text=f"YouTube Downloader {app_version}",
        font=ctk.CTkFont(size=14, weight="bold"),
        anchor="w",
    ).pack(fill="x", padx=16, pady=(14, 2))
    ctk.CTkLabel(
        dialog, text=f"Engine: yt-dlp {ytdlp_version or '(version unknown)'}", anchor="w"
    ).pack(fill="x", padx=16)
    link = ctk.CTkLabel(dialog, text=REPO_URL, text_color=LINK_TEXT, cursor="hand2", anchor="w")
    link.pack(fill="x", padx=16, pady=(2, 10))
    link.bind("<Button-1>", lambda _e: webbrowser.open(REPO_URL))
    ctk.CTkButton(dialog, text="Close", width=80, command=dialog.destroy, **OUTLINE_BUTTON).pack(
        anchor="e", padx=16, pady=(0, 14)
    )
