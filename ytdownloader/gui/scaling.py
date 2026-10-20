"""Display scaling on Linux, where CustomTkinter detects none (it does on Windows and macOS).

CustomTkinter's `get_window_dpi_scaling` returns 1 on Linux, so on a high-density screen the
window came out at half size (issue #10). We read the scale the desktop announces to other
applications and hand it to CustomTkinter; the Size menu overrides it.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import os
import re
import sys
import tkinter as tk
from collections.abc import Callable, Mapping

import customtkinter as ctk
from customtkinter.windows.widgets.scaling import ScalingTracker

# Choices of the Size menu: (factor, label). An explicit size replaces detection.
SIZES = ((1.0, "100%"), (1.25, "125%"), (1.5, "150%"), (1.75, "175%"), (2.0, "200%"))
MIN_SCALE = 1.0  # auto never shrinks the window below CustomTkinter's own size
MAX_SCALE = 3.0
BASE_DPI = 96
_XFT_DPI = re.compile(r"^Xft\.dpi:\s*([0-9.]+)\s*$", re.MULTILINE)


def _quarter(value: float) -> float:
    return min(MAX_SCALE, max(MIN_SCALE, round(value * 4) / 4))


def linux_factor(env: Mapping[str, str], xresources: str | None) -> float:
    """`GDK_SCALE` if set, else `Xft.dpi` / 96 (GNOME, KDE, Xfce publish it on HiDPI), else 1."""
    try:
        gdk = float(env.get("GDK_SCALE") or "")
    except ValueError:
        gdk = 0.0
    if gdk > 0:
        return _quarter(gdk)
    match = _XFT_DPI.search(xresources or "")
    if match:
        try:
            return _quarter(float(match.group(1)) / BASE_DPI)
        except ValueError:
            pass
    return 1.0


def _load_x11():
    # Tk has already loaded libX11 by its soname; find_library shells out to ldconfig and can
    # come back empty inside a PyInstaller bundle.
    try:
        return ctypes.CDLL("libX11.so.6")
    except OSError:
        name = ctypes.util.find_library("X11")
        return ctypes.CDLL(name) if name else None


def read_xresources() -> str | None:
    """The X resource database (what `xrdb -query` prints), or None — never raises."""
    try:
        x11 = _load_x11()
        if x11 is None:
            return None
        x11.XOpenDisplay.restype = ctypes.c_void_p
        x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x11.XResourceManagerString.restype = ctypes.c_char_p
        x11.XResourceManagerString.argtypes = [ctypes.c_void_p]
        x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        display = x11.XOpenDisplay(None)
        if not display:
            return None
        try:
            raw = x11.XResourceManagerString(display)
        finally:
            x11.XCloseDisplay(display)
        return raw.decode("utf-8", errors="replace") if raw else None
    except Exception:  # noqa: BLE001 - no X, odd libX11: fall back to 100%
        return None


def is_linux(platform: str | None = None) -> bool:
    return (platform or sys.platform).startswith("linux")


def ui_factor(
    override: float | None,
    platform: str | None = None,
    env: Mapping[str, str] | None = None,
    read: Callable[[], str | None] | None = None,
) -> float:
    """The factor to hand CustomTkinter: 1 off Linux, else the saved size or detection."""
    if not is_linux(platform):
        return 1.0
    if override is not None:
        return override
    return linux_factor(os.environ if env is None else env, (read or read_xresources)())


def apply(factor: float) -> None:
    """Scale every CustomTkinter widget and window; call before the first window exists."""
    ctk.set_widget_scaling(factor)
    ctk.set_window_scaling(factor)


def sync_tk(root: tk.Misc) -> None:
    """Native Tk parts (menus, message boxes) size their point fonts by `tk scaling`, which X
    derives from the screen's reported millimetres — match it to CustomTkinter instead."""
    if is_linux() and root.tk.call("tk", "windowingsystem") == "x11":
        factor = ScalingTracker.get_widget_scaling(root)  # a CTk root keeps only window scaling
        root.tk.call("tk", "scaling", factor * BASE_DPI / 72)
