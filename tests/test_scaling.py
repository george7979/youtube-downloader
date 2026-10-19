from __future__ import annotations

import ctypes.util

import pytest

from ytdownloader.gui import scaling


@pytest.mark.parametrize(
    ("env", "xresources", "expected"),
    [
        ({}, None, 1.0),
        ({}, "Xft.antialias:\t1\nXft.dpi:\t192\nXft.hinting:\t1\n", 2.0),
        ({}, "Xft.dpi:\t144\n", 1.5),
        ({}, "Xft.dpi: 120\n", 1.25),
        ({}, "Xft.dpi:\t96\n", 1.0),
        ({}, "Xft.dpi:\t110\n", 1.25),  # rounded to the nearest quarter
        ({}, "Xft.dpi:\t72\n", 1.0),  # auto never shrinks below 100%
        ({}, "Xft.dpi:\t480\n", 3.0),  # capped
        ({}, "Xft.dpi:\tlarge\n", 1.0),
        ({}, "Xcursor.size:\t48\n", 1.0),
        ({"GDK_SCALE": "2"}, None, 2.0),
        ({"GDK_SCALE": "2"}, "Xft.dpi:\t96\n", 2.0),  # explicit toolkit scale wins
        ({"GDK_SCALE": "x"}, "Xft.dpi:\t144\n", 1.5),
        ({"GDK_SCALE": ""}, "Xft.dpi:\t144\n", 1.5),
    ],
)
def test_linux_factor(env, xresources, expected):
    assert scaling.linux_factor(env, xresources) == expected


def test_ui_factor_override_replaces_detection():
    assert scaling.ui_factor(1.5, platform="linux", env={"GDK_SCALE": "2"}, read=lambda: None) == 1.5


def test_ui_factor_auto_on_linux():
    assert scaling.ui_factor(None, platform="linux", env={}, read=lambda: "Xft.dpi:\t192\n") == 2.0


def test_ui_factor_leaves_windows_and_macos_alone():
    # CustomTkinter scales those itself; the override is a Linux setting.
    for platform in ("win32", "darwin"):
        assert scaling.ui_factor(None, platform=platform, env={"GDK_SCALE": "2"}) == 1.0
        assert scaling.ui_factor(2.0, platform=platform) == 1.0


def test_read_xresources_without_libx11(monkeypatch):
    monkeypatch.setattr(ctypes.util, "find_library", lambda name: None)
    assert scaling.read_xresources() is None


def test_read_xresources_never_raises(monkeypatch):
    def broken(name):
        raise OSError("no X")

    monkeypatch.setattr(ctypes, "CDLL", broken)
    monkeypatch.setattr(ctypes.util, "find_library", lambda name: "libX11.so.6")
    assert scaling.read_xresources() is None


def test_size_steps_are_valid_settings():
    assert [s for s, _ in scaling.SIZES] == [1.0, 1.25, 1.5, 1.75, 2.0]


def test_apply_sets_customtkinter_scaling():
    import customtkinter as ctk
    from customtkinter.windows.widgets.scaling import ScalingTracker

    try:
        scaling.apply(1.75)
        assert ScalingTracker.widget_scaling == 1.75
        assert ScalingTracker.window_scaling == 1.75
    finally:
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
