"""Open folders and reveal files in the system file manager."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

log = logging.getLogger(__name__)


def _spawn(args: list[str] | str) -> None:
    kwargs = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    subprocess.Popen(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )


def open_folder(path: Path) -> None:
    try:
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            _spawn(["xdg-open", str(path)])
    except Exception:  # noqa: BLE001 - never raise into the UI
        log.exception("Could not open folder %s", path)


def show_file(path: Path) -> None:
    if sys.platform != "win32":
        open_folder(path.parent)
        return
    try:
        # A command string, not a list: explorer needs /select,"<path>" with the quotes
        # around the path only, which list2cmdline would not produce.
        _spawn(f'explorer /select,"{path}"')
    except Exception:  # noqa: BLE001 - never raise into the UI
        log.exception("Could not show file %s", path)
