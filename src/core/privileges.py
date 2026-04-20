# -*- coding: utf-8 -*-
"""
Проверка и запрос прав администратора
"""

import ctypes
import sys
import subprocess
import logging

logger = logging.getLogger("ZapretManager")


class PrivilegesManager:
    """Управление правами администратора"""

    @staticmethod
    def is_admin() -> bool:
        """
        Проверка наличия прав администратора

        Returns:
            True если запущено с правами администратора
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            logger.error(f"Ошибка проверки прав администратора: {e}")
            return False

    @staticmethod
    def request_admin_rights() -> bool:
        """
        Запрос прав администратора (перезапуск с UAC)

        Returns:
            True если перезапуск инициирован
        """
        try:
            if PrivilegesManager.is_admin():
                return True

            logger.info("Запрос прав администратора")

            # Получаем путь к исполняемому файлу
            if getattr(sys, "frozen", False):
                # Если запущен как EXE
                exe_path = sys.executable
            else:
                # Если запущен как скрипт
                exe_path = sys.executable
                script_path = sys.argv[0]

            # Перезапускаем с правами администратора через PowerShell
            ps_command = f'Start-Process "{exe_path}"'

            if not getattr(sys, "frozen", False):
                # Для скрипта добавляем путь к скрипту
                ps_command = f'Start-Process "{exe_path}" -ArgumentList "{script_path}"'

            ps_command += " -Verb RunAs"

            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps_command],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            logger.info("Перезапуск с правами администратора инициирован")
            return True

        except Exception as e:
            logger.error(f"Ошибка запроса прав администратора: {e}", exc_info=True)
            return False

    @staticmethod
    def check_and_request() -> bool:
        """
        Проверить права и запросить если нужно

        Returns:
            True если права есть или запрос инициирован
        """
        if PrivilegesManager.is_admin():
            return True

        logger.warning("Требуются права администратора")
        return PrivilegesManager.request_admin_rights()
