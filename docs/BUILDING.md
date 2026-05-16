# Building YouTube Downloader

## Development environment

```bash
git clone https://github.com/george7979/youtube-downloader.git
cd youtube-downloader
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run locally:

```bash
python3 launcher.py
```

Run tests:

```bash
python3 -m pytest tests/ -v
```

## Branch workflow

- `dev` — all development work happens here
- `main` — stable, only updated via PR from `dev`
- Never commit directly to `main`

Feature development:

```
work on dev → push → CI green → PR to main → merge
```

## Building installers

Requires PyInstaller:

```bash
pip install "pyinstaller>=6.0" pillow
```

### Linux (.deb)

```bash
pyinstaller youtube-downloader.spec --clean
bash installer/linux/build-deb.sh
```

Output: `youtube-downloader_VERSION_amd64.deb`

Requires: `fakeroot`, `dpkg-dev`

### Windows (.exe installer)

```bash
pyinstaller youtube-downloader.spec --clean
makensis /DAPP_VERSION=VERSION installer\windows\installer.nsi
```

Output: `installer\windows\youtube-downloader-VERSION-setup.exe`

Requires: NSIS 3.x

## Releasing

GitHub Actions builds both platforms automatically on every `v*` tag.

To release a new version:

1. Bump version (on `dev`):
   ```bash
   ./build-tools/version-manager.sh bump minor   # 1.2.0 → 1.3.0
   ./build-tools/version-manager.sh bump patch   # 1.3.0 → 1.3.1
   ```

2. Commit and push to `dev`, merge to `main` via PR

3. Create and push tag (ask before doing this):
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

CI will build `.deb` + `.exe` and create a GitHub Release automatically.

## Project structure

```
launcher.py          # entry point, auto-detects GUI/CLI
version.py           # version number
requirements.txt     # Python dependencies
youtube-downloader.spec  # PyInstaller config

core/
  downloader.py      # yt-dlp download engine
  utils.py           # utilities
  translations.py    # i18n

ui/
  gui.py             # CustomTkinter GUI
  cli.py             # CLI fallback

installer/
  linux/build-deb.sh     # .deb packaging script
  windows/installer.nsi  # NSIS installer script

tests/
  test_cancel.py     # cancel mechanism tests

.github/workflows/
  build.yml          # main build + release pipeline
  ci.yml             # lint, tests, security scan
```
