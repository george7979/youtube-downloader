"""Desktop GUI (CustomTkinter)."""

from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path
from tkinter import messagebox

log = logging.getLogger(__name__)

CRASH_TITLE = "Something went wrong"
DOWNLOAD_STOP_TIMEOUT = 5.0  # seconds to wait at exit for a cancelled download to clean up


class CrashReporter:
    """Unhandled exceptions: log them and tell the user where the log is — never exit silently."""

    def __init__(self, log_file: Path | None, log_problem: str | None = None):
        self.log_file = log_file
        self.log_problem = log_problem
        self.root = None  # the window currently shown; dialogs are parented to it

    def message(self) -> str:
        if self.log_file is not None:
            return (
                "An unexpected error occurred.\n\n"
                f"The details were written to the log file:\n{self.log_file}"
            )
        return (
            "An unexpected error occurred.\n\n"
            f"The log file could not be created ({self.log_problem}), "
            "so the details were not saved."
        )

    def attach(self, root) -> None:
        self.root = root
        root.report_callback_exception = self.report

    def install(self) -> None:
        sys.excepthook = self.report
        threading.excepthook = self._thread_hook

    def report(self, exc_type, exc, tb) -> None:
        """Main thread: Tk callbacks (`report_callback_exception`) and `sys.excepthook`."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        log.critical("Unhandled exception", exc_info=(exc_type, exc, tb))
        self._show()

    def _thread_hook(self, args: threading.ExceptHookArgs) -> None:
        """Worker thread: log here, show the dialog on the UI thread."""
        if args.exc_type is SystemExit:
            return
        log.critical(
            "Unhandled exception in thread %s",
            getattr(args.thread, "name", "?"),
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )
        ui = getattr(self.root, "ui", None)
        if ui is not None:
            ui.post(self._show)

    def _show(self) -> None:
        parent = self.root
        try:
            if parent is not None and not parent.winfo_exists():
                parent = None
        except Exception:  # noqa: BLE001 - a destroyed root raises instead of answering
            parent = None
        try:
            if parent is not None:
                messagebox.showerror(CRASH_TITLE, self.message(), parent=parent)
            else:
                messagebox.showerror(CRASH_TITLE, self.message())
        except Exception:  # noqa: BLE001 - no display left; the log has the details
            log.exception("Could not show the error dialog")


def run() -> int:
    from ytdownloader.core.logsetup import setup_logging

    try:
        reporter = CrashReporter(setup_logging())
    except OSError as exc:  # unwritable profile: keep going without a log file, and say so
        reporter = CrashReporter(None, str(exc))
    reporter.install()
    try:
        return _run(reporter)
    except Exception:  # noqa: BLE001 - e.g. the main window failed to build
        reporter.report(*sys.exc_info())
        return 1


def _run(reporter: CrashReporter) -> int:
    from ytdownloader.core.service import Service
    from ytdownloader.core.settings import load_settings
    from ytdownloader.core.tools import ToolManager

    from .app import MainWindow
    from .first_run import FirstRunWindow

    tools = ToolManager()
    missing = tools.missing()
    if missing:
        # Its own Tk root, destroyed before the main window exists: two live CTk roots would
        # split Tk state (default root, variables, images) between them.
        first_run = FirstRunWindow(tools, missing)
        reporter.attach(first_run)
        first_run.mainloop()
        ok = first_run.ok
        reporter.root = None
        first_run.destroy()
        if not ok:
            return 0

    window = MainWindow(Service(tools), tools, load_settings())
    reporter.attach(window)
    window.start_engine_status()
    window.mainloop()
    # Closing the window cancelled a running download; give the engine time to kill the
    # yt-dlp/ffmpeg tree and the service time to delete partial files before the process ends.
    if not window.wait_for_download(DOWNLOAD_STOP_TIMEOUT):
        log.warning("Download still stopping after %s s; exiting anyway", DOWNLOAD_STOP_TIMEOUT)
    return 0
