# youtube-downloader.spec — one-file build of the GUI + CLI.
# yt-dlp is NOT bundled: the app downloads the official yt-dlp binary on first run.
import glob
import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Release builds on Linux use a system-style Python (Tk with Xft, see docs/BUILDING.md); there
# the glob finds nothing and PyInstaller resolves libtk8.6 itself. A local build on uv-managed
# (python-build-standalone) Python keeps libtcl/libtk next to libpython and _tkinter has no
# RPATH, so PyInstaller cannot resolve them on its own — that build runs, but without Xft.
tcltk_binaries = []
if sys.platform.startswith('linux'):
    libdir = os.path.join(sys.base_prefix, 'lib')
    tcltk_binaries = [
        (path, '.')
        for pattern in ('libtcl*.so*', 'libtk*.so*')
        for path in glob.glob(os.path.join(libdir, pattern))
    ]

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=tcltk_binaries,
    datas=[
        ('icons', 'icons'),
        *collect_data_files('customtkinter'),
    ],
    hiddenimports=[
        *collect_submodules('ytdownloader'),
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='youtube-downloader',
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    target_arch=None,
    icon='icons/youtube-downloader.ico' if sys.platform == 'win32' else None,
)
