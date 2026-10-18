"""Initial window placement: fits the work area at any Windows display scaling."""

from __future__ import annotations

import pytest

from ytdownloader.gui.placement import FRAME, MINIMUM, PREFERRED, fit_window


def outer_bottom(p, scaling):
    return p.y + round((p.height + FRAME) * scaling)


@pytest.mark.parametrize(
    "work, scaling",
    [
        ((0, 0, 1920, 1032), 1.5),  # Full HD laptop, 150%, taskbar 48 px
        ((0, 0, 1920, 1040), 1.25),
        ((0, 0, 1366, 728), 1.0),
        ((0, 0, 1280, 680), 1.5),  # tiny: room below the minimum
        ((0, 72, 1920, 1008), 1.5),  # taskbar on top
    ],
)
def test_window_fits_work_area(work, scaling):
    p = fit_window(work, scaling)
    left, top, width, height = work
    assert p.y >= top
    assert outer_bottom(p, scaling) <= top + height
    assert p.x >= left and p.x + round(p.width * scaling) <= left + width
    assert p.min_height <= p.height and p.min_width <= p.width


def test_full_hd_at_150_percent_keeps_preferred_size():
    p = fit_window((0, 0, 1920, 1032), 1.5)  # the PO's laptop: 688 logical px of room
    assert (p.width, p.height) == PREFERRED


def test_small_screen_at_125_percent_shrinks_height():
    p = fit_window((0, 0, 1366, 728), 1.25)
    assert p.width == PREFERRED[0]
    assert p.height == int(728 / 1.25) - FRAME  # 542 logical
    assert p.min_height == MINIMUM[1]


def test_large_screen_keeps_preferred_size_centred():
    p = fit_window((0, 0, 1920, 1040), 1.0)
    assert (p.width, p.height) == PREFERRED
    assert p.x == (1920 - 540) // 2
    assert p.y == (1040 - (PREFERRED[1] + FRAME)) // 2
