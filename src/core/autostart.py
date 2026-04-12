# -*- coding: utf-8 -*-
"""
Управление автозапуском через Task Scheduler
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict

from ..utils.config import Config
from ..utils.logger import logger


class AutostartManager:
    """Управление автозапуском через Task Scheduler"""

    def __init__(self):
        self.config = Config
        self.task_name = self.config.TASK_NAME

    def is_enabled(self) -> bool:
        """
        Проверка установлен ли автозапуск

        Returns:
            True если задача существует
        """
        try:
            result = subprocess.run(
                ['schtasks', '/Query', '/TN', self.task_name],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5
            )
            return result.returncode == 0

        except Exception as e:
            logger.error(f"Ошибка проверки автозапуска: {e}")
            return False

    def enable(self) -> bool:
        """
        Установить автозапуск

        Returns:
            True если успешно
        """
        try:
            logger.info("Установка автозапуска")

            # Удаляем старую задачу если есть
            if self.is_enabled():
                logger.info("Удаление старой задачи")
                subprocess.run(
                    ['schtasks', '/Delete', '/TN', self.task_name, '/F'],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5
                )

            # Получаем путь к EXE
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                # Для разработки используем pythonw
                pythonw = sys.executable.replace('python.exe', 'pythonw.exe')
                script_path = Path(__file__).parent.parent / 'main.py'
                exe_path = f'"{pythonw}" "{script_path}"'

            # Создаем XML для задачи
            xml_content = self._generate_task_xml(exe_path)
            xml_path = Path(self.config.BASE_DIR) / "zapret_manager_task.xml"

            # Сохраняем XML
            xml_path.write_text(xml_content, encoding='utf-16')

            # Создаем задачу через XML
            result = subprocess.run(
                ['schtasks', '/Create', '/TN', self.task_name, '/XML', str(xml_path), '/F'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10
            )

            # Удаляем временный XML
            try:
                xml_path.unlink()
            except:
                pass

            if result.returncode != 0:
                logger.error(f"Ошибка создания задачи: {result.stderr}")
                return False

            logger.info("Автозапуск установлен")
            return True

        except Exception as e:
            logger.error(f"Ошибка установки автозапуска: {e}", exc_info=True)
            return False

    def disable(self) -> bool:
        """
        Удалить автозапуск

        Returns:
            True если успешно
        """
        try:
            logger.info("Удаление автозапуска")

            if not self.is_enabled():
                logger.info("Задача не найдена")
                return True

            result = subprocess.run(
                ['schtasks', '/Delete', '/TN', self.task_name, '/F'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10
            )

            if result.returncode != 0:
                logger.error(f"Ошибка удаления задачи: {result.stderr}")
                return False

            logger.info("Автозапуск удален")
            return True

        except Exception as e:
            logger.error(f"Ошибка удаления автозапуска: {e}", exc_info=True)
            return False

    def get_task_info(self) -> Optional[Dict]:
        """
        Получить информацию о задаче

        Returns:
            Словарь с информацией или None
        """
        try:
            if not self.is_enabled():
                return None

            result = subprocess.run(
                ['schtasks', '/Query', '/TN', self.task_name, '/V', '/FO', 'LIST'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5
            )

            if result.returncode != 0:
                return None

            # Парсим вывод
            info = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()

            return info

        except Exception as e:
            logger.error(f"Ошибка получения информации о задаче: {e}")
            return None

    def _generate_task_xml(self, exe_path: str) -> str:
        """
        Генерация XML для задачи Task Scheduler

        Args:
            exe_path: Путь к исполняемому файлу

        Returns:
            XML содержимое
        """
        # Для EXE используем прямой запуск
        # Для скрипта используем pythonw
        if getattr(sys, 'frozen', False):
            command = exe_path
            arguments = ""
        else:
            parts = exe_path.split('" "')
            command = parts[0].strip('"')
            arguments = parts[1].strip('"') if len(parts) > 1 else ""

        xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT5S</Delay>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <AllowHardTerminate>true</AllowHardTerminate>
    <Hidden>true</Hidden>
  </Settings>
  <Actions>
    <Exec>
      <Command>{command}</Command>'''

        if arguments:
            xml += f'''
      <Arguments>{arguments}</Arguments>'''

        xml += '''
    </Exec>
  </Actions>
</Task>'''

        return xml
