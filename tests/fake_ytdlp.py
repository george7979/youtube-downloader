"""Stand-in for yt-dlp in runner tests. Must not import project code.

Usage:
  fake_ytdlp.py <stdout-fixture>
      print the fixture's lines to stdout, with a small sleep between them
  fake_ytdlp.py <stdout-fixture> stderr <stderr-fixture>
      like above, but print the stderr fixture's lines to stderr just before the
      last stdout line (as yt-dlp does with postprocess progress)
  fake_ytdlp.py <stdout-fixture> spawn-child <pid-file>
      start a long-sleeping child, write its PID to <pid-file>, print the fixture,
      then sleep 60 s (to be cancelled)
"""

import os
import subprocess
import sys
import time
from pathlib import Path

DELAY = 0.005


def _emit(stream, lines: list[str]) -> None:
    for line in lines:
        stream.write(line + "\n")
        stream.flush()
        time.sleep(DELAY)


def main() -> None:
    # No reconfigure of stdout/stderr: like a frozen yt-dlp.exe, the output encoding
    # must come from the environment the runner sets (PYTHONIOENCODING / PYTHONUTF8).
    lines = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
    mode = sys.argv[2] if len(sys.argv) > 2 else ""

    if mode == "spawn-child":
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        pid_file = Path(sys.argv[3])
        tmp = pid_file.with_name(pid_file.name + ".tmp")
        tmp.write_text(str(child.pid), encoding="utf-8")
        os.replace(tmp, pid_file)
        _emit(sys.stdout, lines)
        time.sleep(60)
    elif mode == "stderr":
        err_lines = Path(sys.argv[3]).read_text(encoding="utf-8").splitlines()
        _emit(sys.stdout, lines[:-1])
        _emit(sys.stderr, err_lines)
        _emit(sys.stdout, lines[-1:])
    else:
        _emit(sys.stdout, lines)


if __name__ == "__main__":
    main()
