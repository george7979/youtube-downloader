from __future__ import annotations

import sys

CLI_COMMANDS = {"get", "info", "tools"}
NO_CONSOLE = "The command line is available on Linux/WSL. On Windows use the app window."


def _show_message(text: str) -> None:
    """A message box for the windowed .exe, which has no console to print to."""
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        try:
            messagebox.showinfo("YouTube Downloader", text, parent=root)
        finally:
            root.destroy()
    except Exception:  # noqa: BLE001 - nowhere left to report; exit code 2 still tells
        pass


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and (args[0] in CLI_COMMANDS or args[0] in ("--help", "-h")):
        if sys.stdout is None:  # frozen windowed .exe (console=False)
            _show_message(NO_CONSOLE)
            return 2
        from . import cli

        return cli.main(args)

    from . import gui

    return gui.run() or 0


if __name__ == "__main__":
    raise SystemExit(main())
