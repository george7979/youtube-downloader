# youtube-downloader.spec
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

ctk_datas = collect_data_files('customtkinter')

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('icons', 'icons'),
        *ctk_datas,
    ],
    hiddenimports=[
        'customtkinter',
        'core.downloader',
        'core.utils',
        'core.translations',
        'ui.gui',
        'ui.cli',
        'yt_dlp',
        'yt_dlp.extractor',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'PIL',
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
    icon='icons/youtube-downloader-32.png' if os.path.exists('icons/youtube-downloader-32.png') else None,
)
