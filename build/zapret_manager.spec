# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


spec_root = Path(SPECPATH).parent
project_root = spec_root.parent if not (spec_root / "src").exists() else spec_root
src_dir = project_root / "src"
version_file = project_root / "VERSION"

block_cipher = None


def collect_tree(source: Path, target: str):
    return [
        (str(path), str(Path(target) / path.parent.relative_to(source)))
        for path in source.rglob("*")
        if path.is_file()
    ]


datas = []
datas += collect_tree(src_dir / "resources" / "presets", "resources/presets")
datas += collect_tree(src_dir / "resources" / "lists", "resources/lists")
datas += collect_tree(src_dir / "resources" / "lua", "resources/lua")
# Copy both bin/ (fake packets) and exe/ (winws2.exe, WinDivert) to resources/bin
datas += collect_tree(project_root / "bin", "resources/bin")
datas += collect_tree(project_root / "exe", "resources/bin")
# Copy windivert filter files
datas += collect_tree(project_root / "windivert.filter", "resources/windivert.filter")
datas.append((str(version_file), "."))

a = Analysis(
    [str(src_dir / "main.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "requests",
    ],
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
    name="ZapretManager",
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
