"""Colours and button styles shared by every window: one filled accent button per screen.

Colours are (light, dark) pairs because the app follows the system appearance mode.
"""

from __future__ import annotations

import customtkinter as ctk

ACCENT = ("#C62828", "#C62828")
ACCENT_HOVER = ("#A51F1F", "#A51F1F")
# A disabled CTkButton keeps its fg_color; the primary button swaps to this so it stops shouting.
ACCENT_MUTED = ("#E8B4B4", "#5A2A2A")

DIM_TEXT = ("gray40", "gray60")
ERROR_TEXT = ("#b91c1c", "#f87171")
ERROR_BG = ("#FDECEC", "#3A2324")
ERROR_BORDER = ("#F1B8B8", "#6E2F31")

_NEUTRAL = ("#E3E5E8", "#343638")
_NEUTRAL_RAISED = ("#D5D8DC", "#3D4043")
_NEUTRAL_HOVER = ("#C6CACE", "#4A4F54")
_TEXT = ("gray10", "#DCE4EE")
_HOVER = ("#E6E8EA", "#33363A")

OUTLINE_BUTTON = {
    "fg_color": "transparent",
    "border_width": 1,
    "border_color": ("#9AA0A6", "#6B7075"),
    "text_color": _TEXT,
    "hover_color": _HOVER,
}
TEXT_BUTTON = {
    "fg_color": "transparent",
    "border_width": 0,
    "text_color": ("gray35", "#A3A9AE"),
    "hover_color": _HOVER,
}


def apply_theme() -> None:
    """Replace CustomTkinter's default blue before any widget exists (idempotent)."""
    theme = ctk.ThemeManager.theme
    theme["CTkButton"].update(fg_color=list(ACCENT), hover_color=list(ACCENT_HOVER))
    theme["CTkCheckBox"].update(fg_color=list(ACCENT), hover_color=list(ACCENT_HOVER))
    theme["CTkProgressBar"].update(progress_color=list(ACCENT))
    theme["CTkOptionMenu"].update(
        fg_color=list(_NEUTRAL),
        button_color=list(_NEUTRAL_RAISED),
        button_hover_color=list(_NEUTRAL_HOVER),
        text_color=list(_TEXT),
    )
    theme["CTkSegmentedButton"].update(
        fg_color=list(_NEUTRAL),
        unselected_color=list(_NEUTRAL),
        unselected_hover_color=list(_NEUTRAL_RAISED),
        selected_color=list(("#B4BAC0", "#4A4F54")),
        selected_hover_color=list(("#A9AFB5", "#55595E")),
        text_color=list(_TEXT),
    )


def set_primary_enabled(button: ctk.CTkButton, enabled: bool) -> None:
    """Enable or disable the screen's filled button, muting its colour while disabled."""
    button.configure(
        state="normal" if enabled else "disabled",
        fg_color=ACCENT if enabled else ACCENT_MUTED,
    )
