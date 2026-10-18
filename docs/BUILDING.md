# Building YouTube Downloader

## Development environment

The project uses [uv](https://docs.astral.sh/uv/). Use a uv-managed Python: a system Python
often has no `tkinter`.

```bash
git clone https://github.com/george7979/youtube-downloader.git
cd youtube-downloader
uv sync --managed-python --python 3.12
```

Run the window or the command line from the working tree:

```bash
uv run youtube-downloader                 # GUI
uv run youtube-downloader info <URL>      # CLI (get / info / tools)
uv run python launcher.py                 # same entry point as the packaged binary
```

Run the tests (no network is used):

```bash
uv run pytest -q
```

GUI tests need a display. On a headless Linux machine or in CI use a virtual one:

```bash
xvfb-run -a uv run pytest -q
```

Without any display the GUI tests skip themselves; the rest still run.

## Branch workflow

- `dev` — all development work happens here
- `main` — stable, only updated via PR from `dev`
- Never commit directly to `main`

```
work on dev -> push -> CI green -> PR to main -> merge -> tag
```

## Building installers

PyInstaller is in the `dev` dependency group (already installed by `uv sync`). yt-dlp is **not**
bundled; the app downloads it at first run.

### Linux (.deb)

```bash
uv run pyinstaller youtube-downloader.spec --clean
bash installer/linux/build-deb.sh            # version is read from version.py
```

Output: `youtube-downloader_VERSION_amd64.deb`. Requires `fakeroot` and `dpkg-dev`.

### Windows (.exe installer)

```bash
uv run pyinstaller youtube-downloader.spec --clean
makensis /DAPP_VERSION=VERSION installer\windows\installer.nsi
```

Output: `installer\windows\youtube-downloader-VERSION-setup.exe`. Requires NSIS 3.x.

## Releasing

GitHub Actions (`build.yml`) builds both packages on every push to `dev`/`main` and uploads them
as artifacts; a `v*` tag additionally creates a GitHub Release.

1. Bump the version on `dev` (it lives only in `version.py`; CI passes it to the installer):
   ```bash
   ./build-tools/version-manager.sh bump patch   # or minor / major
   ```
2. Push `dev`, wait for CI, merge to `main` via PR.
3. Tag only with the product owner's approval:
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

## Project structure

```
launcher.py              # entry point for PyInstaller and `python launcher.py`
version.py               # the version number (single source)
pyproject.toml           # dependencies, console script, pytest config
youtube-downloader.spec  # PyInstaller config (no yt-dlp inside)

ytdownloader/
  __main__.py            # routes: get/info/tools -> cli, otherwise the window
  cli.py                 # command line, JSON contract
  core/                  # no tkinter here
    paths.py             #   per-OS locations (config, data, logs, tools)
    settings.py          #   settings.json and the recent list
    logsetup.py          #   rotating log file
    urls.py              #   video id from a URL
    errors.py            #   friendly errors, yt-dlp stderr classification
    models.py            #   shared data types
    tools.py             #   yt-dlp / ffmpeg / Deno: download, verify, update
    engine.py            #   yt-dlp arguments, progress parsing, cancellable runner
    probe.py             #   video info and caption track choice
    subtitles.py         #   VTT -> paragraphs, SRT
    naming.py            #   file names, detecting existing downloads
    note.py              #   the Markdown note
    service.py           #   the one entry point for GUI and CLI
  gui/                   # CustomTkinter window
    app.py               #   main window
    first_run.py         #   tool download on the first start
    widgets.py           #   error panel, dialogs, window icon
    theme.py             #   colours and button styles
    placement.py         #   window size and position from the screen's work area
    worker.py            #   background work, results back on the Tk thread
    system.py            #   open a folder, show a file

icons/                   # app icon (.ico, PNG sizes)
pics/                    # screenshots for the README
docs/                    # PRD, PLAN, TECH (Polish), BUILDING; superpowers/ = design archive
installer/
  linux/build-deb.sh     # .deb packaging
  windows/installer.nsi  # NSIS installer

integrations/claude-skill/youtube-downloader/SKILL.md   # Claude Code skill
tests/                   # pytest; fixtures from real yt-dlp output in tests/fixtures/
.github/workflows/
  build.yml              # packages, .deb install test, release
  ci.yml                 # lint, tests (Ubuntu with xvfb, Windows), security scan
```
