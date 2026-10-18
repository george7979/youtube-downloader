"""User-facing errors and classification of yt-dlp stderr."""

from __future__ import annotations


class FriendlyError(Exception):
    def __init__(self, code: str, message: str, hint: str = "", details: str = ""):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.details = details


# code -> (message, hint)
_TABLE: dict[str, tuple[str, str]] = {
    "write_failed": (
        "Can't save to the selected folder.",
        "Choose another folder or free up disk space.",
    ),
    "bot_check": (
        "YouTube is blocking this request.",
        "This often happens on VPNs or office networks. "
        "Try again in a few minutes, or update the engine.",
    ),
    "rate_limit": (
        "YouTube rate limit reached.",
        "Wait a few minutes and try again.",
    ),
    "forbidden": (
        "YouTube refused the video stream (HTTP 403).",
        "This is usually temporary — try again. If it keeps happening, update the engine.",
    ),
    "engine_outdated": (
        "The download engine needs an update.",
        "Update the engine and try again.",
    ),
    "unavailable": (
        "This video is not publicly available.",
        "Check the link, or try a different video.",
    ),
    "network": (
        "No connection to YouTube.",
        "Check your internet connection and try again.",
    ),
    "unknown": (
        "Something went wrong.",
        "See the details and include them in a bug report.",
    ),
    "invalid_url": (
        "This doesn't look like a YouTube video link.",
        "Paste a link like https://www.youtube.com/watch?v=…",
    ),
    "tools_missing": (
        "Download tools are missing.",
        "Restart the app while connected to the internet to download them.",
    ),
    "cancelled": ("Download cancelled.", ""),
}

# Checked top-down; lowercase substrings.
_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    (
        "write_failed",
        (
            "permission denied",
            "no space left on device",
            "[errno 28]",
            "[errno 13]",
            "read-only file system",
        ),
    ),
    ("bot_check", ("not a bot",)),
    ("rate_limit", ("this content isn't available, try again later", "http error 429")),
    ("forbidden", ("http error 403",)),
    (
        "engine_outdated",
        (
            "nsig extraction failed",
            "signature extraction failed",
            "unable to extract",
            "requested format is not available",
        ),
    ),
    (
        "unavailable",
        (
            "private video",
            "video unavailable",
            "this video has been removed",
            "not available in your country",
            "confirm your age",
            "members-only",
        ),
    ),
    (
        "network",
        (
            "unable to download webpage",
            "getaddrinfo failed",
            "temporary failure in name resolution",
            "connection refused",
            "timed out",
            "network is unreachable",
            "urlopen error",
        ),
    ),
]


def friendly(code: str, details: str = "") -> FriendlyError:
    message, hint = _TABLE[code]
    return FriendlyError(code, message, hint, details)


def classify(stderr_text: str) -> FriendlyError:
    details = "\n".join((stderr_text or "").splitlines()[-40:])
    haystack = (stderr_text or "").replace("’", "'").lower()
    for code, patterns in _PATTERNS:
        if any(p in haystack for p in patterns):
            return friendly(code, details)
    return friendly("unknown", details)
