#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zapret Manager - главная точка входа
"""

import sys
import os
from pathlib import Path

# Добавляем текущую директорию в путь для импортов
if getattr(sys, 'frozen', False):
    # Если запущен как EXE
    application_path = Path(sys._MEIPASS)
    sys.path.insert(0, str(application_path))
else:
    # Если запущен как скрипт
    application_path = Path(__file__).parent
    sys.path.insert(0, str(application_path))

# Исправление кодировки для Windows
if sys.platform == 'win32' and sys.stdout is not None:
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

from utils.config import Config
from utils.logger import logger
from core.privileges import PrivilegesManager
from gui.tray_icon import ZapretTrayIcon


def main():
    """Главная функция"""
    try:
        logger.info("=== Запуск Zapret Manager ===")
        logger.info(f"Версия: {Config.VERSION}")
        logger.info(f"Режим: {'EXE' if Config.IS_FROZEN else 'Python скрипт'}")
        logger.info(f"Базовая директория: {Config.BASE_DIR}")

        # Проверка прав администратора
        if not PrivilegesManager.is_admin():
            logger.warning("Требуются права администратора")

            # Показываем предупреждение
            app = QApplication(sys.argv)
            reply = QMessageBox.question(
                None,
                "Требуются права администратора",
                "Для работы с сетевым стеком Windows требуются права администратора.\n\n"
                "Перезапустить приложение с правами администратора?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                PrivilegesManager.request_admin_rights()
                sys.exit(0)
            else:
                logger.info("Пользователь отказался от прав администратора")
                sys.exit(1)

        # Проверка ресурсов
        if not Config.validate_resources():
            logger.error("Не все ресурсы найдены")
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Ошибка",
                f"Не найдены необходимые файлы.\n\n"
                f"Проверьте что winws2.exe находится в:\n{Config.WINWS2_EXE}\n\n"
                f"Базовая директория: {Config.BASE_DIR}"
            )
            sys.exit(1)

        # Создаем приложение
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setApplicationName(Config.APP_NAME)
        app.setApplicationVersion(Config.VERSION)

        # Создаем системный трей
        tray = ZapretTrayIcon()
        tray.show()

        logger.info("Приложение запущено успешно")

        # Запускаем event loop
        return app.exec_()

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)

        try:
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Критическая ошибка",
                f"Не удалось запустить приложение:\n\n{e}"
            )
        except:
            pass

        return 1


if __name__ == "__main__":
    sys.exit(main())
