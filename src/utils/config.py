# -*- coding: utf-8 -*-
"""
Конфигурация приложения
"""

from pathlib import Path
import sys


class Config:
    """Конфигурация приложения"""

    # Версия
    VERSION = "1.0.0"
    APP_NAME = "Zapret Manager"

    # Определяем базовую директорию
    if getattr(sys, 'frozen', False):
        # Если запущен как EXE (PyInstaller)
        BASE_DIR = Path(sys._MEIPASS)
        IS_FROZEN = True
    else:
        # Если запущен как скрипт
        BASE_DIR = Path(__file__).parent.parent.parent.absolute()
        IS_FROZEN = False

    # Пути к ресурсам
    RESOURCES_DIR = BASE_DIR / "src" / "resources" if not IS_FROZEN else BASE_DIR / "resources"
    BIN_DIR = RESOURCES_DIR / "bin"
    PRESETS_DIR = RESOURCES_DIR / "presets"
    LISTS_DIR = RESOURCES_DIR / "lists"
    LUA_DIR = RESOURCES_DIR / "lua"
    CONFIG_DIR = RESOURCES_DIR / "config"

    # Исполняемые файлы
    WINWS2_EXE = BIN_DIR / "winws2.exe"

    # Конфигурационные файлы
    ACTIVE_PRESET = CONFIG_DIR / "preset-active.txt"
    CURRENT_PRESET_NAME = CONFIG_DIR / "current_preset.txt"

    # Task Scheduler
    TASK_NAME = "ZapretManager"

    # Таймауты
    PROCESS_CHECK_TIMEOUT = 5  # секунд
    STATUS_UPDATE_INTERVAL = 3000  # миллисекунд

    # WinDivert сервисы для очистки
    WINDIVERT_SERVICES = ["WinDivert", "WinDivert14", "Monkey", "Monkey14"]

    # Конфликтующие сервисы
    CONFLICTING_SERVICES = ["GoodbyeDPI", "zapret", "discordfix_zapret", "winws1"]

    @classmethod
    def ensure_config_dir(cls):
        """Создать директорию для конфигов если не существует"""
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_resources(cls) -> bool:
        """
        Проверка наличия необходимых ресурсов

        Returns:
            True если все ресурсы на месте
        """
        required_paths = [
            cls.WINWS2_EXE,
            cls.PRESETS_DIR,
            cls.LISTS_DIR,
            cls.LUA_DIR,
        ]

        for path in required_paths:
            if not path.exists():
                return False

        return True
