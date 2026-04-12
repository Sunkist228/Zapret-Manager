# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Определяем базовую директорию
spec_root = Path(SPECPATH).parent
src_dir = spec_root / 'src'

block_cipher = None

a = Analysis(
    [str(src_dir / 'main.py')],
    pathex=[str(src_dir)],
    binaries=[],
    datas=[
        (str(src_dir / 'resources' / 'presets'), 'resources/presets'),
        (str(src_dir / 'resources' / 'lists'), 'resources/lists'),
        (str(src_dir / 'resources' / 'lua'), 'resources/lua'),
        (str(src_dir / 'resources' / 'bin'), 'resources/bin'),
    ],
    hiddenimports=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
    name='ZapretManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    uac_uiaccess=False,
)
