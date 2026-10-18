"""Logging setup: rotating file under paths.log_dir(), stderr when available."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import paths

_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_MARK = "_ytdownloader_handler"


def setup_logging(level: int = logging.INFO) -> Path:
    log_file = paths.log_dir() / "app.log"
    root = logging.getLogger()
    root.setLevel(level)

    for handler in root.handlers:
        if getattr(handler, _MARK, False):
            return log_file

    formatter = logging.Formatter(_FORMAT)
    handlers: list[logging.Handler] = [
        RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    ]
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())
    for handler in handlers:
        handler.setFormatter(formatter)
        setattr(handler, _MARK, True)
        root.addHandler(handler)
    return log_file
