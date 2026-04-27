from __future__ import annotations

from core.zapret_manager import ZapretManager
from utils import config as config_module


def _configure_paths(monkeypatch, tmp_path):
    resources = tmp_path / "resources"
    config_dir = tmp_path / "config"
    resources.mkdir()
    config_dir.mkdir()
    monkeypatch.setattr(config_module.Config, "RESOURCES_DIR", resources)
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
            ]
        ),
        encoding="utf-8",
    )

    missing = ZapretManager().validate_active_preset_resources()

    assert resources / "lists" / "missing-ipset.txt" in missing
    assert resources / "bin" / "missing.bin" in missing
    assert resources / "lists" / "present.txt" not in missing
    assert resources / "lists" / "rooted.txt" not in missing


def test_current_preset_name_ignores_utf8_bom(monkeypatch, tmp_path):
    _, config_dir = _configure_paths(monkeypatch, tmp_path)
    (config_dir / "current_preset.txt").write_text(
        "\ufeffDefault (Discord, YouTube, Telegram)",
        encoding="utf-8",
    )

    assert ZapretManager().get_current_preset_name() == "Default (Discord, YouTube, Telegram)"


def test_start_failure_diagnostics_are_actionable():
    assert "несовместим" in ZapretManager.explain_start_failure("unknown option --dpi", 1)
    assert "отсутствующий файл" in ZapretManager.explain_start_failure("cannot access file 'x'", 1)
    assert "WinDivert" in ZapretManager.explain_start_failure("windivert: error opening filter", 177)
