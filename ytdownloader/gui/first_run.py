"""First run: download the missing tools, one progress bar per tool, Retry on failure."""

from __future__ import annotations

import logging
import math
import traceback

import customtkinter as ctk

from ytdownloader import __version__
from ytdownloader.core.errors import FriendlyError, friendly
from ytdownloader.core.tools import OnBytes, ToolManager, ToolSpec

from . import scaling
from .placement import fit_window, max_height, work_area
from .theme import ACCENT, DIM_TEXT, OUTLINE_BUTTON, apply_theme
from .widgets import ErrorPanel, set_window_icon
from .worker import UiQueue, cancel_pending_after

log = logging.getLogger(__name__)

MB = 1_000_000


def size_text(done: int, total: int | None) -> str:
    if total:
        return f"{done / MB:.1f} / {total / MB:.1f} MB"
    return f"{done / MB:.1f} MB"


class FirstRunWindow(ctk.CTk):
    """Its own Tk root, run before the main window; `run()` destroys it before building that one.

    Installs start right away; `ok` turns True once every tool is installed and the window
    leaves its main loop. Quit (or closing the window) leaves the loop with `ok` False.
    """

    def __init__(self, tools: ToolManager, specs: list[ToolSpec]):
        ctk.set_appearance_mode("system")
        apply_theme()
        super().__init__()
        scaling.sync_tk(self)
        self.tools = tools
        self.specs = list(specs)
        self.ok = False
        self.ui = UiQueue(self)
        self._installed: set[str] = set()

        self.title(f"YouTube Downloader {__version__}")
        set_window_icon(self)
        place = fit_window(
            work_area(self), self._get_window_scaling(), preferred=(480, 360), minimum=(420, 300)
        )
        self._width = place.width
        self.minsize(place.min_width, place.min_height)
        self.geometry(f"{place.width}x{place.height}+{place.x}+{place.y}")
        self.protocol("WM_DELETE_WINDOW", self.quit)

        total_mb = sum(spec.approx_mb for spec in self.specs)
        self.header_label = ctk.CTkLabel(
            self, text="Setting up", font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        )
        self.header_label.pack(fill="x", padx=18, pady=(18, 0))
        self.detail_label = ctk.CTkLabel(
            self,
            text=(
                f"Downloading yt-dlp, ffmpeg and Deno, about {total_mb} MB. This happens once; "
                "later the app keeps them up to date on its own."
            ),
            text_color=DIM_TEXT,
            wraplength=430,
            justify="left",
            anchor="w",
        )
        self.detail_label.pack(fill="x", padx=18, pady=(2, 12))

        self.bars: dict[str, ctk.CTkProgressBar] = {}
        self.size_labels: dict[str, ctk.CTkLabel] = {}
        for spec in self.specs:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=spec.name, width=60, anchor="w").grid(row=0, column=0)
            bar = ctk.CTkProgressBar(row, height=6)
            bar.set(0)
            bar.grid(row=0, column=1, sticky="ew", padx=8)
            size = ctk.CTkLabel(row, text="Waiting…", width=130, anchor="e")
            size.grid(row=0, column=2)
            self.bars[spec.name] = bar
            self.size_labels[spec.name] = size

        self.buttons = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons.pack(side="bottom", fill="x", padx=16, pady=(8, 16))
        self.quit_button = ctk.CTkButton(
            self.buttons, text="Quit", width=80, command=self.quit, **OUTLINE_BUTTON
        )
        self.quit_button.pack(side="right")
        self.retry_button = ctk.CTkButton(
            self.buttons, text="Retry", width=80, command=self.start
        )
        self.error_panel = ErrorPanel(
            self, pack_opts={"fill": "x", "padx": 16, "pady": (8, 0)}, on_layout=self._fit_content
        )

        self.start()

    def start(self) -> None:
        """Install every tool not installed yet, in order, on a background thread."""
        self.error_panel.clear()
        self.retry_button.pack_forget()
        pending = [spec for spec in self.specs if spec.name not in self._installed]
        for spec in pending:
            self._set_waiting(spec.name, True)
            self.size_labels[spec.name].configure(text="Waiting…")
        self.ui.run_bg(
            lambda: self._install_all(pending), lambda _result: self._on_done(), self._on_error
        )

    def _install_all(self, pending: list[ToolSpec]) -> None:  # worker thread
        for spec in pending:
            self.tools.install(spec, self._on_bytes_for(spec.name))
            self.ui.post(lambda name=spec.name: self._mark_installed(name))

    def _on_bytes_for(self, name: str) -> OnBytes:
        last = [""]

        def on_bytes(done: int, total: int | None) -> None:  # worker thread
            text = size_text(done, total)
            if text != last[0]:
                last[0] = text
                self.ui.post(lambda: self._show_bytes(name, done, total, text))

        return on_bytes

    def _set_waiting(self, name: str, waiting: bool) -> None:
        """A waiting tool's bar shows no fill at all: at 0 CTk still draws a round accent nub."""
        bar = self.bars[name]
        if waiting:
            bar.set(0)
        bar.configure(progress_color=bar.cget("fg_color") if waiting else ACCENT)

    def _show_bytes(self, name: str, done: int, total: int | None, text: str) -> None:
        self._set_waiting(name, False)
        if total:
            self.bars[name].set(min(done / total, 1.0))
            if done >= total:
                text += " · installing…"
        self.size_labels[name].configure(text=text)

    def _mark_installed(self, name: str) -> None:
        self._installed.add(name)
        self._set_waiting(name, False)
        self.bars[name].set(1.0)
        self.size_labels[name].configure(text="Done")

    def _on_done(self) -> None:
        self.ok = True
        self.quit()

    def _on_error(self, exc: Exception) -> None:
        if isinstance(exc, FriendlyError):
            log.warning("Tool install failed [%s]: %s", exc.code, exc.details)
        else:
            log.error("Tool install failed", exc_info=exc)
            exc = friendly("unknown", details="".join(traceback.format_exception(exc)))
        self.error_panel.show(exc)
        self.retry_button.pack(side="right", padx=(0, 8))

    def _fit_content(self) -> None:
        """Grow (never shrink) so the error panel and its details are not cut off."""
        self.update_idletasks()
        scaling = self._get_window_scaling()
        need = min(
            math.ceil(self.winfo_reqheight() / scaling), max_height(work_area(self), scaling)
        )
        if need > round(self.winfo_height() / scaling):
            self.geometry(f"{self._width}x{need}")

    def destroy(self) -> None:
        self.ui.close()
        cancel_pending_after(self)
        super().destroy()
