"""Initial window size and position that fit the screen's work area at any DPI scaling."""

from __future__ import annotations

import sys
import tkinter as tk
from dataclasses import dataclass

# Logical (unscaled) pixels — CustomTkinter multiplies width and height by the window scaling,
# so 780 becomes 1170 physical px at Windows' 150% and no longer fits a 1080 px screen.
PREFERRED = (540, 780)
MINIMUM = (480, 420)
# Title bar and frame drawn by the window manager outside the geometry we set.
FRAME = 40
# Panels the fallback work area cannot see (Linux: GNOME top bar, docks).
PANEL_RESERVE = 48


@dataclass(frozen=True)
class Placement:
    width: int  # logical
    height: int  # logical
    x: int  # physical
    y: int  # physical
    min_width: int  # logical
    min_height: int  # logical


def fit_window(work: tuple[int, int, int, int], scaling: float) -> Placement:
    """Fit PREFERRED into `work` (left, top, width, height in physical px), centred.

    The minimum shrinks with the window on very small screens, so the window can never be
    forced taller than the work area.
    """
    left, top, work_w, work_h = work
    room_w = int(work_w / scaling) - FRAME // 2
    room_h = int(work_h / scaling) - FRAME
    width = max(1, min(PREFERRED[0], room_w))
    height = max(1, min(PREFERRED[1], room_h))
    outer_w = round(width * scaling)
    outer_h = round((height + FRAME) * scaling)
    return Placement(
        width=width,
        height=height,
        x=left + max(0, (work_w - outer_w) // 2),
        y=top + max(0, (work_h - outer_h) // 2),
        min_width=min(MINIMUM[0], width),
        min_height=min(MINIMUM[1], height),
    )


def work_area(root: tk.Misc) -> tuple[int, int, int, int]:
    """The primary screen without the taskbar, in physical px (CustomTkinter makes the
    process DPI-aware on Windows, so Win32 and Tk both report physical pixels)."""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            rect = wintypes.RECT()
            spi_getworkarea = 0x0030
            if ctypes.windll.user32.SystemParametersInfoW(spi_getworkarea, 0, ctypes.byref(rect), 0):
                return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
        except Exception:  # noqa: BLE001 - fall back to the whole screen
            pass
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight() - PANEL_RESERVE
