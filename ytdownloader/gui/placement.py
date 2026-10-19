"""Initial window size and position that fit the screen's work area at any DPI scaling."""

from __future__ import annotations

import sys
import tkinter as tk
from dataclasses import dataclass

# Logical (unscaled) pixels — CustomTkinter multiplies width and height by the window scaling,
# so a fixed 780 became 1170 physical px at Windows' 150% and no longer fit a 1080 px screen.
PREFERRED = (540, 600)  # fits the full layout while downloading (card, progress, three recent)
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


def max_height(work: tuple[int, int, int, int], scaling: float) -> int:
    """Tallest logical window height whose frame still fits the work area."""
    return max(1, int(work[3] / scaling) - FRAME)


def fit_window(
    work: tuple[int, int, int, int],
    scaling: float,
    preferred: tuple[int, int] = PREFERRED,
    minimum: tuple[int, int] = MINIMUM,
) -> Placement:
    """Fit `preferred` into `work` (left, top, width, height in physical px), centred.

    The minimum shrinks with the window on very small screens, so the window can never be
    forced taller than the work area.
    """
    left, top, work_w, work_h = work
    room_w = int(work_w / scaling) - FRAME // 2
    width = max(1, min(preferred[0], room_w))
    height = min(preferred[1], max_height(work, scaling))
    outer_w = round(width * scaling)
    outer_h = round((height + FRAME) * scaling)
    return Placement(
        width=width,
        height=height,
        x=left + max(0, (work_w - outer_w) // 2),
        y=top + max(0, (work_h - outer_h) // 2),
        min_width=min(minimum[0], width),
        min_height=min(minimum[1], height),
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
