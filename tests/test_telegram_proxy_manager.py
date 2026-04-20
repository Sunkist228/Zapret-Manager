from __future__ import annotations

from core.telegram_proxy_manager import TelegramProxyManager
from utils import config as config_module


def test_telegram_proxy_manager_finds_helper_in_tools_dir(monkeypatch, tmp_path):
    base_dir = tmp_path
    helper_dir = base_dir / "tools" / "telegram-proxy"
    helper_dir.mkdir(parents=True)
    helper = helper_dir / "tgwsproxy.exe"
    helper.write_bytes(b"")

    monkeypatch.setattr(config_module.Config, "BASE_DIR", base_dir)
    monkeypatch.setattr(config_module.Config, "RESOURCES_DIR", base_dir / "src" / "resources")
    monkeypatch.delenv(TelegramProxyManager.ENV_EXE, raising=False)

    manager = TelegramProxyManager()

    assert manager.find_executable() == helper


def test_telegram_proxy_manager_prefers_env_executable(monkeypatch, tmp_path):
    base_dir = tmp_path / "app"
    env_helper = tmp_path / "custom" / "TelegramWsProxy.exe"
    env_helper.parent.mkdir(parents=True)
    env_helper.write_bytes(b"")

    monkeypatch.setattr(config_module.Config, "BASE_DIR", base_dir)
    monkeypatch.setattr(config_module.Config, "RESOURCES_DIR", base_dir / "src" / "resources")
    monkeypatch.setenv(TelegramProxyManager.ENV_EXE, str(env_helper))

    manager = TelegramProxyManager()

    assert manager.find_executable() == env_helper
