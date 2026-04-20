# -*- coding: utf-8 -*-
"""
Управление автозапуском через Task Scheduler
"""

import subprocess
import sys
import tempfile
import winreg
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional

from utils.config import Config
from utils.logger import logger


class AutostartManager:
    """Управление автозапуском через Task Scheduler."""

    def __init__(self):
        self.config = Config
        self.task_name = self.config.TASK_NAME

    def _get_expected_action(self) -> Dict[str, str]:
        """Получить ожидаемую команду автозапуска."""
        if getattr(sys, "frozen", False):
            command = str(Path(sys.executable))
            arguments = "--autostart"
            working_directory = str(Path(sys.executable).parent)
        else:
            current_python = Path(sys.executable)
            pythonw = current_python.with_name("pythonw.exe")
            if not pythonw.exists():
                pythonw = current_python
            script_path = (Path(__file__).parent.parent / "main.py").resolve()
            command = str(pythonw)
            arguments = f'"{script_path}" --autostart'
            working_directory = str(self.config.BASE_DIR)

        return {
            "command": command,
            "arguments": arguments,
            "working_directory": working_directory,
        }

    @staticmethod
    def _normalize_path(value: str) -> str:
        """Нормализовать путь для сравнения."""
        if not value:
            return ""

        normalized = value.strip().strip('"')
        try:
            return str(Path(normalized).resolve()).lower()
        except Exception:
            return str(Path(normalized)).lower()

    @staticmethod
    def _normalize_arguments(value: str) -> str:
        """Нормализовать аргументы командной строки."""
        return " ".join((value or "").replace('"', "").split()).lower()

    def _task_exists(self, task_name: str) -> bool:
        """Проверить существование задачи планировщика."""
        result = subprocess.run(
            ["schtasks", "/Query", "/TN", task_name],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=5,
        )
        return result.returncode == 0

    def _get_task_definition(self, task_name: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Прочитать описание задачи из XML Task Scheduler."""
        task_name = task_name or self.task_name

        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", task_name, "/XML"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
            )

            if result.returncode != 0 or not result.stdout.strip():
                return None

            root = ET.fromstring(result.stdout)
            namespace = {"ts": "http://schemas.microsoft.com/windows/2004/02/mit/task"}

            return {
                "command": root.findtext(".//ts:Exec/ts:Command", default="", namespaces=namespace)
                or "",
                "arguments": root.findtext(
                    ".//ts:Exec/ts:Arguments", default="", namespaces=namespace
                )
                or "",
                "working_directory": root.findtext(
                    ".//ts:Exec/ts:WorkingDirectory", default="", namespaces=namespace
                )
                or "",
            }

        except Exception as e:
            logger.error(f"Ошибка чтения XML задачи '{task_name}': {e}")
            return None

    def _is_expected_task_definition(self, definition: Optional[Dict[str, str]]) -> bool:
        """Проверить, что задача указывает на текущую установленную версию."""
        if not definition:
            return False

        expected = self._get_expected_action()
        return (
            self._normalize_path(definition.get("command", ""))
            == self._normalize_path(expected["command"])
            and self._normalize_arguments(definition.get("arguments", ""))
            == self._normalize_arguments(expected["arguments"])
            and self._normalize_path(definition.get("working_directory", ""))
            == self._normalize_path(expected["working_directory"])
        )

    def _delete_task(self, task_name: str):
        """Удалить задачу планировщика, если она существует."""
        if not self._task_exists(task_name):
            return

        result = subprocess.run(
            ["schtasks", "/Delete", "/TN", task_name, "/F"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
        )

        if result.returncode != 0:
            logger.warning(f"Не удалось удалить задачу '{task_name}': {result.stderr}")

    def _cleanup_legacy_registry_entries(self):
        """Удалить legacy-автозапуск из Run."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_READ,
            )
        except FileNotFoundError:
            return
        except Exception as e:
            logger.warning(f"Не удалось открыть раздел Run для очистки: {e}")
            return

        try:
            for value_name in self.config.LEGACY_RUN_VALUE_NAMES:
                try:
                    winreg.DeleteValue(key, value_name)
                    logger.info(f"Удалена legacy-запись автозапуска Run: {value_name}")
                except FileNotFoundError:
                    continue
        finally:
            winreg.CloseKey(key)

    def _cleanup_legacy_artifacts(self):
        """Удалить устаревшие механизмы автозапуска."""
        self._cleanup_legacy_registry_entries()

        for legacy_task_name in self.config.LEGACY_TASK_NAMES:
            self._delete_task(legacy_task_name)

    def _clear_existing_autostart(self):
        """Удалить текущую и legacy-конфигурацию автозапуска."""
        self._cleanup_legacy_artifacts()
        self._delete_task(self.task_name)

    def is_enabled(self) -> bool:
        """
        Проверка, установлен ли автозапуск.

        Returns:
            True если задача существует и соответствует текущей установке.
        """
        try:
            if not self._task_exists(self.task_name):
                return False

            definition = self._get_task_definition(self.task_name)
            if self._is_expected_task_definition(definition):
                return True

            logger.warning("Найдена устаревшая или некорректная задача автозапуска")
            return False

        except Exception as e:
            logger.error(f"Ошибка проверки автозапуска: {e}")
            return False

    def enable(self) -> bool:
        """
        Установить автозапуск.

        Returns:
            True если успешно.
        """
        try:
            logger.info("Установка автозапуска")
            self._clear_existing_autostart()

            action = self._get_expected_action()
            xml_content = self._generate_task_xml(
                action["command"], action["arguments"], action["working_directory"]
            )
            xml_path = Path(tempfile.gettempdir()) / "ZapretManager" / "zapret_manager_task.xml"
            xml_path.parent.mkdir(parents=True, exist_ok=True)
            xml_path.write_text(xml_content, encoding="utf-16")

            result = subprocess.run(
                ["schtasks", "/Create", "/TN", self.task_name, "/XML", str(xml_path), "/F"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )

            try:
                xml_path.unlink()
            except OSError:
                pass

            if result.returncode != 0:
                logger.error(f"Ошибка создания задачи: {result.stderr}")
                return False

            definition = self._get_task_definition(self.task_name)
            if not self._is_expected_task_definition(definition):
                logger.error("Созданная задача автозапуска не соответствует ожидаемой команде")
                self._delete_task(self.task_name)
                return False

            logger.info("Автозапуск установлен")
            return True

        except Exception as e:
            logger.error(f"Ошибка установки автозапуска: {e}", exc_info=True)
            return False

    def disable(self) -> bool:
        """
        Удалить автозапуск.

        Returns:
            True если успешно.
        """
        try:
            logger.info("Удаление автозапуска")
            had_current_task = self._task_exists(self.task_name)
            self._clear_existing_autostart()

            if had_current_task and self._task_exists(self.task_name):
                logger.error("Не удалось удалить текущую задачу автозапуска")
                return False

            logger.info("Автозапуск удален")
            return True

        except Exception as e:
            logger.error(f"Ошибка удаления автозапуска: {e}", exc_info=True)
            return False

    def get_task_info(self) -> Optional[Dict]:
        """
        Получить информацию о задаче.

        Returns:
            Словарь с информацией или None.
        """
        try:
            if not self._task_exists(self.task_name):
                return None

            result = subprocess.run(
                ["schtasks", "/Query", "/TN", self.task_name, "/V", "/FO", "LIST"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
            )

            if result.returncode != 0:
                return None

            info = {}
            for line in result.stdout.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    info[key.strip()] = value.strip()

            definition = self._get_task_definition(self.task_name)
            if definition:
                info["Command"] = definition["command"]
                info["Arguments"] = definition["arguments"]
                info["WorkingDirectory"] = definition["working_directory"]
                info["IsCurrentInstall"] = self._is_expected_task_definition(definition)

            return info

        except Exception as e:
            logger.error(f"Ошибка получения информации о задаче: {e}")
            return None

    def _generate_task_xml(self, command: str, arguments: str, working_directory: str) -> str:
        """
        Генерация XML для задачи Task Scheduler.

        Args:
            command: Команда запуска.
            arguments: Аргументы запуска.
            working_directory: Рабочая директория.

        Returns:
            XML содержимое.
        """
        xml = f"""<?xml version="1.0" encoding="UTF-16"?>
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
      <Command>{command}</Command>"""

        if arguments:
            xml += f"""
      <Arguments>{arguments}</Arguments>"""

        if working_directory:
            xml += f"""
      <WorkingDirectory>{working_directory}</WorkingDirectory>"""

        xml += """
    </Exec>
  </Actions>
</Task>"""

        return xml
