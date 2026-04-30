#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zapret Manager entry point.
"""

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    application_path = Path(sys._MEIPASS)
    sys.path.insert(0, str(application_path))
else:
    application_path = Path(__file__).parent
    sys.path.insert(0, str(application_path))

if sys.platform == "win32" and sys.stdout is not None:
    try:
        import codecs

        if hasattr(sys.stdout, "buffer"):
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        if hasattr(sys.stderr, "buffer"):
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")
    except Exception:
        pass

from PyQt5.QtCore import QSharedMemory
from PyQt5.QtWidgets import QApplication, QMessageBox

from core.privileges import PrivilegesManager
from core.runtime_state import RuntimeState
from gui.tray_icon import ZapretTrayIcon
from utils.config import Config
from utils.logger import logger


def should_restore_zapret_on_start(runtime_state: RuntimeState | None = None) -> bool:
    """Return whether zapret should be restored on application startup."""
    state = runtime_state or RuntimeState()
    return state.should_restore_zapret()


def main():
    """Main application bootstrap."""
    try:
        logger.info("=== Запуск Zapret Manager ===")
        logger.info(f"Версия: {Config.VERSION}")
        logger.info(f"Режим: {'EXE' if Config.IS_FROZEN else 'Python скрипт'}")
        logger.info(f"Базовая директория: {Config.BASE_DIR}")

        Config.prepare_runtime()

        if Config.IS_FROZEN:
            logger.info(f"sys._MEIPASS: {sys._MEIPASS}")
            logger.info(f"BUNDLED_RESOURCES_DIR: {Config.BUNDLED_RESOURCES_DIR}")
            logger.info(f"APP_DATA_DIR: {Config.APP_DATA_DIR}")
            logger.info(f"RESOURCES_DIR: {Config.RESOURCES_DIR}")
            logger.info(f"BIN_DIR: {Config.BIN_DIR}")
            logger.info(f"WINWS2_EXE: {Config.WINWS2_EXE}")

            logger.info(f"RESOURCES_DIR exists: {Config.RESOURCES_DIR.exists()}")
            logger.info(f"BIN_DIR exists: {Config.BIN_DIR.exists()}")

            if Config.BIN_DIR.exists():
                bin_files = list(Config.BIN_DIR.iterdir())
                logger.info(f"Files in BIN_DIR ({len(bin_files)}):")
                for f in bin_files[:20]:
                    logger.info(f"  - {f.name} ({f.stat().st_size} bytes)")

            logger.info(f"WINWS2_EXE exists: {Config.WINWS2_EXE.exists()}")
            if Config.WINWS2_EXE.exists():
                logger.info(f"WINWS2_EXE size: {Config.WINWS2_EXE.stat().st_size} bytes")

        app = QApplication(sys.argv)

        shared_memory = QSharedMemory("ZapretManagerSingleInstance")
        if not shared_memory.create(1):
            logger.warning("Приложение уже запущено")
            return 0

        if not PrivilegesManager.is_admin():
            logger.warning("Требуются права администратора")

            reply = QMessageBox.critical(
                None,
                "Требуются права администратора",
                "Для работы с сетевым стеком Windows требуются права администратора.\n\n"
                "Zapret Manager не может работать без прав администратора.\n\n"
                "Перезапустить приложение с правами администратора?",
                QMessageBox.Yes | QMessageBox.Cancel,
                QMessageBox.Yes,
            )

            if reply == QMessageBox.Yes:
                logger.info("Перезапуск с правами администратора")
                PrivilegesManager.request_admin_rights()
                return 0

            logger.info("Пользователь отменил запрос прав администратора")
            QMessageBox.information(
                None,
                "Приложение не может запуститься",
                "Zapret Manager требует права администратора для работы.\n\n"
                "Запустите приложение правой кнопкой мыши → 'Запуск от имени администратора'",
            )
            return 1

        if not Config.validate_resources():
            logger.error("Не все ресурсы найдены")
            QMessageBox.critical(
                None,
                "Ошибка",
                f"Не найдены необходимые файлы.\n\n"
                f"Проверьте что winws2.exe находится в:\n{Config.WINWS2_EXE}\n\n"
                f"Базовая директория: {Config.BASE_DIR}",
            )
            return 1

        app.setQuitOnLastWindowClosed(False)
        app.setApplicationName(Config.APP_NAME)
        app.setApplicationVersion(Config.VERSION)

        autostart_mode = "--autostart" in sys.argv[1:]
        auto_start = should_restore_zapret_on_start()
        if autostart_mode:
            logger.info(
                "Autostart mode detected: restore saved zapret state = %s",
                auto_start,
            )
        elif auto_start:
            logger.info("Saved state requests zapret restore on startup")

        tray = ZapretTrayIcon(auto_start=auto_start)
        tray.show()

        logger.info("Приложение запущено успешно")
        return app.exec_()

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)

        try:
            QMessageBox.critical(
                None, "Критическая ошибка", f"Не удалось запустить приложение:\n\n{e}"
            )
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    sys.exit(main())
