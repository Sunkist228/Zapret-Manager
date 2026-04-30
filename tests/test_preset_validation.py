from __future__ import annotations

from pathlib import Path

from core.zapret_manager import ZapretManager
from utils import config as config_module

REPO_ROOT = Path(__file__).resolve().parents[1]


def _configure_paths(monkeypatch, tmp_path):
    resources = tmp_path / "resources"
    config_dir = tmp_path / "config"
    resources.mkdir()
    config_dir.mkdir()
    monkeypatch.setattr(config_module.Config, "RESOURCES_DIR", resources)
    monkeypatch.setattr(config_module.Config, "BIN_DIR", resources / "bin")
    monkeypatch.setattr(config_module.Config, "BASE_DIR", tmp_path)
    monkeypatch.setattr(config_module.Config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config_module.Config, "ACTIVE_PRESET", config_dir / "preset-active.txt")
    monkeypatch.setattr(
        config_module.Config,
        "CURRENT_PRESET_NAME",
        config_dir / "current_preset.txt",
    )
    monkeypatch.setattr(config_module.Config, "IS_FROZEN", True)
    return resources, config_dir


def test_validate_active_preset_reports_missing_relative_resources(monkeypatch, tmp_path):
    resources, config_dir = _configure_paths(monkeypatch, tmp_path)
    (resources / "lists").mkdir()
    (resources / "lists" / "present.txt").write_text("example.com\n", encoding="utf-8")
    (resources / "lists" / "rooted.txt").write_text("example.com\n", encoding="utf-8")

    active_preset = config_dir / "preset-active.txt"
    active_preset.write_text(
        "\n".join(
            [
                "--hostlist=lists/present.txt",
                "--hostlist=/lists/rooted.txt",
                "--ipset=lists/missing-ipset.txt",
                "--blob=tls:@bin/missing.bin",
                "--blob=fake_default_udp:0x00000000000000000000000000000000",
                "--blob=fake_default_udp",
                "--lua-desync=fake:blob=fake_default_udp",
            ]
        ),
        encoding="utf-8",
    )

    missing = ZapretManager().validate_active_preset_resources()

    assert resources / "lists" / "missing-ipset.txt" in missing
    assert resources / "bin" / "missing.bin" in missing
    assert resources / "fake_default_udp:0x00000000000000000000000000000000" not in missing
    assert resources / "fake_default_udp" not in missing
    assert resources / "lists" / "present.txt" not in missing
    assert resources / "lists" / "rooted.txt" not in missing


def test_default_preset_resource_validation_accepts_inline_blobs(monkeypatch, tmp_path):
    resources = tmp_path / "resources"
    config_dir = tmp_path / "config"
    (resources / "bin").mkdir(parents=True)
    (resources / "lists").mkdir()
    (resources / "lua").mkdir()
    config_dir.mkdir()
    active_preset = config_dir / "preset-active.txt"
    default_preset = (
        REPO_ROOT / "src" / "resources" / "presets" / "Default (Discord, YouTube, Telegram).txt"
    )
    active_preset.write_text(
        default_preset.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    for name in (
        "tls_clienthello_www_google_com.bin",
        "tls_clienthello_5.bin",
        "tls_clienthello_7.bin",
        "quic_initial_www_google_com.bin",
        "quic_2.bin",
    ):
        (resources / "bin" / name).write_bytes(b"payload")

    for name in (
        "youtube.txt",
        "ipset-youtube.txt",
        "discord.txt",
        "ipset-discord.txt",
        "telegram.txt",
        "ipset-telegram.txt",
    ):
        (resources / "lists" / name).write_text("example.com\n", encoding="utf-8")

    for name in (
        "zapret-lib.lua",
        "zapret-antidpi.lua",
        "zapret-auto.lua",
        "custom_funcs.lua",
        "custom_diag.lua",
        "zapret-multishake.lua",
    ):
        (resources / "lua" / name).write_text("-- test\n", encoding="utf-8")

    monkeypatch.setattr(config_module.Config, "RESOURCES_DIR", resources)
    monkeypatch.setattr(config_module.Config, "BASE_DIR", REPO_ROOT)
    monkeypatch.setattr(config_module.Config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config_module.Config, "ACTIVE_PRESET", active_preset)
    monkeypatch.setattr(
        config_module.Config,
        "CURRENT_PRESET_NAME",
        config_dir / "current_preset.txt",
    )
    monkeypatch.setattr(config_module.Config, "IS_FROZEN", True)

    assert ZapretManager().validate_active_preset_resources() == []


def test_current_preset_name_ignores_utf8_bom(monkeypatch, tmp_path):
    _, config_dir = _configure_paths(monkeypatch, tmp_path)
    (config_dir / "current_preset.txt").write_text(
        "\ufeffDefault (Discord, YouTube, Telegram)",
        encoding="utf-8",
    )

    assert ZapretManager().get_current_preset_name() == "Default (Discord, YouTube, Telegram)"


def test_start_prerequisites_report_missing_windivert(monkeypatch, tmp_path):
    resources, _ = _configure_paths(monkeypatch, tmp_path)
    (resources / "bin").mkdir()
    monkeypatch.setattr("core.zapret_manager.PrivilegesManager.is_admin", lambda: True)

    message = ZapretManager()._check_start_prerequisites()

    assert message is not None
    assert "WinDivert" in message
    assert "BFE" not in message


def test_start_prerequisites_report_unavailable_bfe(monkeypatch, tmp_path):
    resources, _ = _configure_paths(monkeypatch, tmp_path)
    (resources / "bin").mkdir()
    for name in ZapretManager.REQUIRED_WINDIVERT_FILES:
        (resources / "bin" / name).write_bytes(b"driver")

    monkeypatch.setattr("core.zapret_manager.PrivilegesManager.is_admin", lambda: True)
    monkeypatch.setattr(ZapretManager, "_ensure_bfe_running", lambda self: False)

    message = ZapretManager()._check_start_prerequisites()

    assert message is not None
    assert "BFE" in message


def test_start_failure_diagnostics_are_actionable():
    assert "несовместим" in ZapretManager.explain_start_failure("unknown option --dpi", 1)
    assert "отсутствующий файл" in ZapretManager.explain_start_failure("cannot access file 'x'", 1)
    assert "WinDivert" in ZapretManager.explain_start_failure(
        "windivert: error opening filter", 177
    )
