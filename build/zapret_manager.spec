# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


# SPECPATH is the directory containing the .spec file
spec_dir = Path(SPECPATH).absolute()

# When PyInstaller runs, it creates build/ subdirectory
# So we might be in: zapret2/build/ or zapret2/build/build/
# We need to find the project root (zapret2/)
current = spec_dir
while current.name in ['build', 'dist'] and current.parent != current:
    current = current.parent

project_root = current
src_dir = project_root / "src"
version_file = project_root / "VERSION"

print(f"[SPEC] SPECPATH: {spec_dir}")
print(f"[SPEC] Project root: {project_root}")
print(f"[SPEC] Checking bin: {(project_root / 'bin').exists()}")
print(f"[SPEC] Checking exe: {(project_root / 'exe').exists()}")
print(f"[SPEC] Checking src: {src_dir.exists()}")

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
# Copy bin/ (fake packets) as data
datas += collect_tree(project_root / "bin", "resources/bin")
# Copy windivert filter files
datas += collect_tree(project_root / "windivert.filter", "resources/windivert.filter")
datas.append((str(version_file), "."))

# Mark executables and DLLs as binaries for proper extraction
binaries = []
exe_dir = project_root / "exe"
if exe_dir.exists():
    for exe_file in exe_dir.rglob("*"):
        if exe_file.is_file() and exe_file.suffix.lower() in ['.exe', '.dll', '.sys']:
            binaries.append((str(exe_file), "resources/bin"))

a = Analysis(
    [str(src_dir / "main.py")],
    pathex=[str(src_dir)],
    binaries=binaries,
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
    runtime_hooks=['runtime_hook.py'],
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
