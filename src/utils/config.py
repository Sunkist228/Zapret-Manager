# -*- coding: utf-8 -*-
"""
Configuration for Zapret Manager.
"""

from pathlib import Path
import os
import shutil
import sys
import tempfile

try:
    from utils.versioning import normalize_product_version, read_version_file
    from utils.logger import logger
except ImportError:
    from .versioning import normalize_product_version, read_version_file
    from .logger import logger


class Config:
    """Application configuration."""

    APP_NAME = "Zapret Manager"
    NOTIFICATION_LEVEL = "errors_only"

    if getattr(sys, "frozen", False):
        BASE_DIR = Path(sys._MEIPASS)
        IS_FROZEN = True
    else:
        BASE_DIR = Path(__file__).parent.parent.parent.absolute()
        IS_FROZEN = False

    if IS_FROZEN:
        _LOCAL_APPDATA = os.environ.get("LOCALAPPDATA")
        APP_DATA_DIR = (
            Path(_LOCAL_APPDATA) / "ZapretManager"
            if _LOCAL_APPDATA
            else Path.home() / "AppData" / "Local" / "ZapretManager"
        )
    else:
        APP_DATA_DIR = BASE_DIR

    VERSION_FILE = BASE_DIR / "VERSION"
    VERSION = read_version_file(VERSION_FILE, default="0.0.0")
    PRODUCT_VERSION = normalize_product_version(VERSION)

    BUNDLED_RESOURCES_DIR = BASE_DIR / "resources" if IS_FROZEN else BASE_DIR / "src" / "resources"
    RESOURCES_DIR = APP_DATA_DIR / "resources" if IS_FROZEN else BUNDLED_RESOURCES_DIR
    BIN_DIR = RESOURCES_DIR / "bin"
    PRESETS_DIR = RESOURCES_DIR / "presets"
    LISTS_DIR = RESOURCES_DIR / "lists"
    LUA_DIR = RESOURCES_DIR / "lua"

    if IS_FROZEN:
        LEGACY_CONFIG_DIR = Path(tempfile.gettempdir()) / "ZapretManager" / "config"
        CONFIG_DIR = APP_DATA_DIR / "config"
    else:
        LEGACY_CONFIG_DIR = RESOURCES_DIR / "config"
        CONFIG_DIR = RESOURCES_DIR / "config"

    UPDATE_DOWNLOAD_DIR = (
        APP_DATA_DIR / "updates"
        if IS_FROZEN
        else Path(tempfile.gettempdir()) / "ZapretManager" / "updates"
    )
    UPDATE_STATE_FILE = CONFIG_DIR / "update-state.json"

    WINWS2_EXE = BIN_DIR / "winws2.exe"

    ACTIVE_PRESET = CONFIG_DIR / "preset-active.txt"
    CURRENT_PRESET_NAME = CONFIG_DIR / "current_preset.txt"
    RUNTIME_STATE_FILE = CONFIG_DIR / "runtime-state.json"

    DEFAULT_PRESET_NAME = "Default (Discord, YouTube, Telegram)"

    TASK_NAME = "ZapretManager"
    LEGACY_TASK_NAMES = ["Zapret2", "ZapretTray"]
    LEGACY_RUN_VALUE_NAMES = ["ZapretTray"]

    PROCESS_CHECK_TIMEOUT = 5
    PROCESS_STATUS_CACHE_SECONDS = 10
    STATUS_UPDATE_INTERVAL = 3000
    LOG_RETENTION_DAYS = 14

    WINDIVERT_SERVICES = ["WinDivert", "WinDivert14", "Monkey", "Monkey14"]
    CONFLICTING_SERVICES = ["GoodbyeDPI", "zapret", "discordfix_zapret", "winws1"]
    GAMEGUARD_PROCESS_NAMES = [
        "GameMon.des",
        "GameGuard.des",
        "GameGuard.exe",
        "GameGuard64.exe",
    ]

    UPDATE_ENABLED = True
    UPDATE_CHANNEL = "stable"
    UPDATE_CHECK_INTERVAL_HOURS = 24

    # GitHub Releases (primary update source)
    GITHUB_REPO_OWNER = "Sunkist228"
    GITHUB_REPO_NAME = "Zapret-Manager"
    GITHUB_API_BASE = "https://api.github.com"

    # Artifact servers (fallback update sources)
    UPDATE_ENDPOINTS = [
        {"type": "github", "url": "https://api.github.com"},
        {"type": "artifact_server", "url": "https://artifact.devflux.ru"},
        {"type": "artifact_server", "url": "https://update.devflux.ru"},
    ]
    UPDATE_CHECK_PATH = "/api/v1/update/check"
    UPDATE_ARTIFACT_SLUG = "zapret-manager"
    UPDATE_PLATFORM = "windows"
    UPDATE_ARCH = "x64"

    RUNTIME_RESOURCE_ENTRIES = ("bin", "presets", "lists", "lua", "windivert.filter")
    MIGRATABLE_CONFIG_FILES = (
        "preset-active.txt",
        "current_preset.txt",
        "runtime-state.json",
        "update-state.json",
    )

    @classmethod
    def should_show_notification(cls, level: str = "success") -> bool:
        """Return whether a tray notification should be shown."""
        if level == "error":
            return True

        if cls.NOTIFICATION_LEVEL == "errors_only":
            return False

        return True

    @classmethod
    def ensure_config_dir(cls):
        """Ensure mutable application directories exist."""
        cls.migrate_legacy_config()
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cls.UPDATE_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def prepare_runtime(cls):
        """Prepare mutable config and frozen-mode runtime resources."""
        cls.ensure_config_dir()
        cls.sync_bundled_resources()

    @classmethod
    def migrate_legacy_config(cls):
        """Copy old temp-based config into the stable app data directory once."""
        if not cls.IS_FROZEN or cls.LEGACY_CONFIG_DIR == cls.CONFIG_DIR:
            return

        if not cls.LEGACY_CONFIG_DIR.exists():
            return

        has_new_state = cls.CONFIG_DIR.exists() and any(
            (cls.CONFIG_DIR / name).exists() for name in cls.MIGRATABLE_CONFIG_FILES
        )
        if has_new_state:
            return

        try:
            cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            migrated = []
            for name in cls.MIGRATABLE_CONFIG_FILES:
                source = cls.LEGACY_CONFIG_DIR / name
                target = cls.CONFIG_DIR / name
                if source.exists() and not target.exists():
                    shutil.copy2(source, target)
                    migrated.append(name)

            if migrated:
                logger.info(
                    "Migrated legacy temp config files to stable app data: %s",
                    ", ".join(migrated),
                )
        except Exception as exc:
            logger.warning("Failed to migrate legacy temp config: %s", exc)

    @classmethod
    def sync_bundled_resources(cls):
        """Copy PyInstaller resources out of the volatile _MEI directory."""
        if not cls.IS_FROZEN:
            return

        if not cls.BUNDLED_RESOURCES_DIR.exists():
            logger.warning("Bundled resources directory not found: %s", cls.BUNDLED_RESOURCES_DIR)
            return

        try:
            cls.RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
            for entry in cls.RUNTIME_RESOURCE_ENTRIES:
                source = cls.BUNDLED_RESOURCES_DIR / entry
                target = cls.RESOURCES_DIR / entry
                if not source.exists():
                    logger.warning("Bundled resource entry not found: %s", source)
                    continue

                if source.is_dir():
                    shutil.copytree(source, target, dirs_exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)

            logger.info(
                "Synchronized bundled resources from %s to %s",
                cls.BUNDLED_RESOURCES_DIR,
                cls.RESOURCES_DIR,
            )
        except Exception as exc:
            logger.error("Failed to synchronize bundled resources: %s", exc, exc_info=True)
            raise

    @classmethod
    def validate_resources(cls) -> bool:
        """Validate required bundled resources."""
        required_paths = [
            (cls.WINWS2_EXE, "winws2.exe"),
            (cls.PRESETS_DIR, "presets directory"),
            (cls.LISTS_DIR, "lists directory"),
            (cls.LUA_DIR, "lua directory"),
        ]

        missing = []
        for path, name in required_paths:
            if not path.exists():
                missing.append(f"{name}: {path}")
                logger.error(f"Missing resource: {name} at {path}")

        if missing:
            logger.error(f"Missing {len(missing)} required resources")

            # Вывести содержимое родительских директорий для диагностики
            if cls.IS_FROZEN:
                try:
                    logger.error(f"BASE_DIR contents: {list(cls.BASE_DIR.iterdir())}")
                except Exception as e:
                    logger.error(f"Cannot list BASE_DIR: {e}")

                if cls.RESOURCES_DIR.exists():
                    try:
                        logger.error(f"RESOURCES_DIR contents: {list(cls.RESOURCES_DIR.iterdir())}")
                    except Exception as e:
                        logger.error(f"Cannot list RESOURCES_DIR: {e}")

                if cls.BIN_DIR.exists():
                    try:
                        bin_contents = list(cls.BIN_DIR.iterdir())[:20]
                        logger.error(f"BIN_DIR contents (first 20): {bin_contents}")
                    except Exception as e:
                        logger.error(f"Cannot list BIN_DIR: {e}")

            return False

        return True
