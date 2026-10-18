"""Entry point for PyInstaller and `python launcher.py`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ytdownloader.__main__ import main  # noqa: E402

raise SystemExit(main())
