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

    assert "zapret-manager-v${{ steps.bump.outputs.version }}-windows-x64.exe" in release_workflow
    assert (
        '$artifactName = "zapret-manager-v${{ steps.bump.outputs.version }}-windows-x64.exe"'
        in release_workflow
    )
    assert "build\\dist\\ZapretManager.exe" in release_workflow
    assert "build/dist/ZapretManager.exe" in jenkinsfile
    assert "dist\\ZapretManager.exe" in build_script

    assert "..\\dist\\ZapretManager.exe" not in jenkinsfile
    assert "sha256sum dist/zapret-manager-windows-x64.exe" not in release_workflow
    assert "build/dist/zapret-manager-windows-x64.exe" not in release_workflow
    assert "working-directory: build\n        shell: bash" not in release_workflow
    assert "scripts/bump_version.py 2>&1" not in release_workflow
    assert "New-TemporaryFile" in release_workflow
    assert 'PYTHONIOENCODING = "utf-8"' in release_workflow
    assert "resources\\\\bin\\\\tls_clienthello_www_google_com.bin" in release_workflow


def test_config_frozen_paths_point_to_bundled_resources(tmp_path):
    local_app_data = tmp_path / "LocalAppData"
    script = f"""
import sys
import tempfile
from pathlib import Path

sys.frozen = True
sys._MEIPASS = r"{tmp_path}"

from utils.config import Config

base = Path(r"{tmp_path}")
local_app_data = Path(r"{local_app_data}")
assert Config.IS_FROZEN is True
assert Config.BASE_DIR == base
assert Config.APP_DATA_DIR == local_app_data / "ZapretManager"
assert Config.BUNDLED_RESOURCES_DIR == base / "resources"
assert Config.RESOURCES_DIR == local_app_data / "ZapretManager" / "resources"
assert Config.CONFIG_DIR == local_app_data / "ZapretManager" / "config"
assert Config.CONFIG_DIR != Path(tempfile.gettempdir()) / "ZapretManager" / "config"
assert Config.BIN_DIR == local_app_data / "ZapretManager" / "resources" / "bin"
assert Config.WINWS2_EXE == local_app_data / "ZapretManager" / "resources" / "bin" / "winws2.exe"
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    env["LOCALAPPDATA"] = str(local_app_data)

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_frozen_runtime_preparation_copies_resources_and_migrates_temp_config(tmp_path):
    bundle_root = tmp_path / "bundle"
    bundled_resources = bundle_root / "resources"
    local_app_data = tmp_path / "LocalAppData"
    temp_root = tmp_path / "Temp"

    for entry in ("bin", "presets", "lists", "lua", "windivert.filter"):
        (bundled_resources / entry).mkdir(parents=True)
        (bundled_resources / entry / "sentinel.txt").write_text(entry, encoding="utf-8")
    (bundled_resources / "bin" / "winws2.exe").write_text("exe", encoding="utf-8")

    legacy_config = temp_root / "ZapretManager" / "config"
    legacy_config.mkdir(parents=True)
    (legacy_config / "current_preset.txt").write_text("Default", encoding="utf-8")
    (legacy_config / "runtime-state.json").write_text("{}", encoding="utf-8")

    script = f"""
import sys
from pathlib import Path

sys.frozen = True
sys._MEIPASS = r"{bundle_root}"

from utils.config import Config

Config.prepare_runtime()

app_data = Path(r"{local_app_data}") / "ZapretManager"

def read_text(*parts):
    return app_data.joinpath(*parts).read_text(encoding="utf-8")

assert read_text("resources", "bin", "winws2.exe") == "exe"
assert read_text("resources", "presets", "sentinel.txt") == "presets"
assert read_text("resources", "lists", "sentinel.txt") == "lists"
assert read_text("resources", "lua", "sentinel.txt") == "lua"
assert read_text("resources", "windivert.filter", "sentinel.txt") == "windivert.filter"
assert read_text("config", "current_preset.txt") == "Default"
assert read_text("config", "runtime-state.json") == "{{}}"
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    env["LOCALAPPDATA"] = str(local_app_data)
    env["TEMP"] = str(temp_root)
    env["TMP"] = str(temp_root)

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_pyinstaller_bundle_includes_preset_payload_bins():
    spec_file = (REPO_ROOT / "build" / "zapret_manager.spec").read_text(encoding="utf-8")

    assert 'collect_tree(project_root / "bin", "resources/bin")' in spec_file
    assert 'project_root / "bin" / "tls_clienthello_www_google_com.bin"' in spec_file


def test_required_pyinstaller_resources_are_tracked():
    required_paths = [
        "src/resources/bin/winws2.exe",
        "src/resources/bin/WinDivert.dll",
        "src/resources/bin/WinDivert32.sys",
        "src/resources/bin/WinDivert64.sys",
    ]
    result = subprocess.run(
        ["git", "ls-files", *required_paths],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    tracked = set(result.stdout.splitlines())

    assert result.returncode == 0, result.stderr
    assert set(required_paths).issubset(tracked)
