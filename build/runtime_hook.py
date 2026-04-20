# -*- coding: utf-8 -*-
"""
PyInstaller runtime hook для диагностики извлечения файлов.
"""

import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    meipass = Path(sys._MEIPASS)
    print(f"[HOOK] _MEIPASS: {meipass}")
    print(f"[HOOK] _MEIPASS exists: {meipass.exists()}")

    if meipass.exists():
        try:
            root_files = list(meipass.iterdir())
            print(f"[HOOK] Files in _MEIPASS root: {len(root_files)}")
            for f in root_files[:10]:
                print(f"[HOOK]   - {f.name} ({'dir' if f.is_dir() else 'file'})")
        except Exception as e:
            print(f"[HOOK] Error listing _MEIPASS: {e}")

    resources_dir = meipass / "resources"
    print(f"[HOOK] resources/ exists: {resources_dir.exists()}")

    if resources_dir.exists():
        try:
            res_files = list(resources_dir.iterdir())
            print(f"[HOOK] Files in resources/: {len(res_files)}")
            for f in res_files[:10]:
                print(f"[HOOK]   - {f.name} ({'dir' if f.is_dir() else 'file'})")
        except Exception as e:
            print(f"[HOOK] Error listing resources/: {e}")

    resources_bin = meipass / "resources" / "bin"
    print(f"[HOOK] resources/bin/ exists: {resources_bin.exists()}")

    if resources_bin.exists():
        try:
            bin_files = list(resources_bin.iterdir())
            print(f"[HOOK] Files in resources/bin/: {len(bin_files)}")
            for f in bin_files[:15]:
                print(f"[HOOK]   - {f.name} ({f.stat().st_size} bytes)")
        except Exception as e:
            print(f"[HOOK] Error listing resources/bin/: {e}")

    winws2_path = resources_bin / "winws2.exe"
    print(f"[HOOK] winws2.exe exists: {winws2_path.exists()}")
    if winws2_path.exists():
        print(f"[HOOK] winws2.exe size: {winws2_path.stat().st_size} bytes")
