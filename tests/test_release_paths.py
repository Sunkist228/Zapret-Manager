from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_release_and_ci_use_single_build_dist_contract():
    release_workflow = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    jenkinsfile = (REPO_ROOT / "Jenkinsfile").read_text(encoding="utf-8")
    build_script = (REPO_ROOT / "build" / "build.bat").read_text(encoding="utf-8")

    assert "build/dist/zapret-manager-windows-x64.exe" in release_workflow
    assert "build\\dist\\ZapretManager.exe" in release_workflow
    assert "build/dist/ZapretManager.exe" in jenkinsfile
    assert "dist\\ZapretManager.exe" in build_script

    assert "..\\dist\\ZapretManager.exe" not in jenkinsfile
    assert "sha256sum dist/zapret-manager-windows-x64.exe" not in release_workflow
    assert "working-directory: build\n        shell: bash" not in release_workflow
    assert "scripts/bump_version.py 2>&1" not in release_workflow
    assert "New-TemporaryFile" in release_workflow


def test_config_frozen_paths_point_to_bundled_resources(tmp_path):
    script = f"""
import sys
from pathlib import Path

sys.frozen = True
sys._MEIPASS = r"{tmp_path}"

from utils.config import Config

base = Path(r"{tmp_path}")
assert Config.IS_FROZEN is True
assert Config.BASE_DIR == base
assert Config.RESOURCES_DIR == base / "resources"
assert Config.BIN_DIR == base / "resources" / "bin"
assert Config.WINWS2_EXE == base / "resources" / "bin" / "winws2.exe"
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )

    assert result.returncode == 0, result.stdout + result.stderr
