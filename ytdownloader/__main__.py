from __future__ import annotations

import sys

CLI_COMMANDS = {"get", "info", "tools"}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and (args[0] in CLI_COMMANDS or args[0] in ("--help", "-h")):
        from . import cli

        return cli.main(args)

    from . import gui

    return gui.run() or 0


if __name__ == "__main__":
    raise SystemExit(main())
