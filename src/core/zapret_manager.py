# -*- coding: utf-8 -*-
"""
Управление процессом winws2.exe.
"""

from __future__ import annotations

import csv
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.runtime_state import RuntimeState
from utils.config import Config
from utils.logger import create_winws2_log_file, logger


class ZapretManager:
    """Управление процессом winws2.exe."""

    RESOURCE_OPTIONS = (
        "--blob=",
        "--lua-init=",
        "--wf-raw-part=",
        "--wf-raw-filter=",
        "--wf-raw=",
        "--ipset=",
        "--ipset-exclude=",
        "--hostlist=",
        "--hostlist-exclude=",
        "--hostlist-auto=",
    )

    def __init__(self):
        self.config = Config
        self.runtime_state = RuntimeState()
        self.process: Optional[subprocess.Popen] = None
        self.process_start_time: Optional[datetime] = None
        self.last_start_error: Optional[str] = None
        self._status_cache_checked_at = 0.0
        self._status_cache_running = False
        self._status_cache_pid: Optional[int] = None

    def _set_status_cache(self, running: bool, pid: Optional[int]) -> None:
        self._status_cache_checked_at = time.monotonic()
        self._status_cache_running = running
        self._status_cache_pid = pid if running else None

    def _query_process_status(self) -> Tuple[bool, Optional[int]]:
        """Query Windows process list once and parse PID if present."""
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq winws2.exe", "/NH", "/FO", "CSV"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=self.config.PROCESS_CHECK_TIMEOUT,
        )

        for row in csv.reader(result.stdout.splitlines()):
            if len(row) >= 2 and row[0].lower() == "winws2.exe":
                try:
                    return True, int(row[1])
                except ValueError:
                    return True, None

        return False, None

    def is_running(self) -> bool:
        """Проверка запущен ли winws2.exe."""
        if self.process and self.process.poll() is None:
            self._set_status_cache(True, self.process.pid)
            return True

        cache_age = time.monotonic() - self._status_cache_checked_at
        if cache_age < self.config.PROCESS_STATUS_CACHE_SECONDS:
            return self._status_cache_running

        try:
            running, pid = self._query_process_status()
            self._set_status_cache(running, pid)
            return running
        except Exception as exc:
            logger.warning("Не удалось проверить статус winws2.exe: %s", exc)
            return self._status_cache_running

    def get_pid(self) -> Optional[int]:
        """Получить PID процесса winws2.exe."""
        if self.process and self.process.poll() is None:
            self._set_status_cache(True, self.process.pid)
            return self.process.pid

        if self.is_running():
            return self._status_cache_pid
        return None

    def _cleanup_windivert(self):
        """Очистка WinDivert сервисов."""
        logger.info("Очистка WinDivert сервисов")

        for service in self.config.WINDIVERT_SERVICES:
            try:
                result = subprocess.run(
                    ["sc", "query", service],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5,
                )

                if result.returncode == 0:
                    subprocess.run(
                        ["net", "stop", service],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=5,
                    )
                    subprocess.run(
                        ["sc", "delete", service],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=5,
                    )
                    logger.info("Сервис %s очищен", service)
            except Exception as exc:
                logger.debug("Сервис %s: %s", service, exc)

    def _enable_tcp_timestamps(self):
        """Включение TCP timestamps."""
        try:
            logger.info("Включение TCP timestamps")
            subprocess.run(
                ["netsh", "interface", "tcp", "set", "global", "timestamps=enabled"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
            )
        except Exception as exc:
            logger.warning("Не удалось включить TCP timestamps: %s", exc)

    def get_current_preset_name(self) -> Optional[str]:
        """Return current preset name, tolerant to BOM."""
        try:
            if self.config.CURRENT_PRESET_NAME.exists():
                name = self.config.CURRENT_PRESET_NAME.read_text(
                    encoding="utf-8-sig"
                ).strip()
                return name or None
        except Exception as exc:
            logger.debug("Не удалось прочитать текущий пресет: %s", exc)
        return None

    def _resolve_resource_path(self, value: str) -> Optional[Path]:
        value = value.strip().strip("\"'")
        if not value or value.startswith(("0x", "$")):
            return None

        if "@" in value:
            value = value.rsplit("@", 1)[1].strip().strip("\"'")
        elif "\n" in value or " " in value:
            return None

        if not value or value.startswith(("0x", "$")):
            return None

        value = value.lstrip("/\\")
        path = Path(value)
        if not path.is_absolute():
            path = self.config.RESOURCES_DIR / path
        return path

    def validate_active_preset_resources(self) -> List[Path]:
        """Validate file references used by the active preset."""
        missing: List[Path] = []
        if not self.config.ACTIVE_PRESET.exists():
            return [self.config.ACTIVE_PRESET]

        try:
            lines = self.config.ACTIVE_PRESET.read_text(
                encoding="utf-8-sig", errors="ignore"
            ).splitlines()
        except OSError:
            return [self.config.ACTIVE_PRESET]

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            for option in self.RESOURCE_OPTIONS:
                if not line.startswith(option):
                    continue

                value = line[len(option) :]
                path = self._resolve_resource_path(value)
                if path and not path.exists():
                    missing.append(path)
                break

        return missing

    @staticmethod
    def explain_start_failure(output: str, return_code: Optional[int]) -> str:
        """Map common winws2 errors to user-readable diagnostics."""
        text = output.lower()

        if "ambiguous option" in text or "unknown option" in text:
            return (
                "Пресет несовместим с текущей версией winws2.exe: "
                "в нем есть неподдерживаемые параметры."
            )

        if (
            "could not read" in text
            or "cannot access file" in text
            or "no such file" in text
        ):
            return "В пресете указан отсутствующий файл ресурса."

        if "windivert" in text or return_code == 177:
            return (
                "WinDivert не смог открыть фильтр. Проверьте права администратора, "
                "драйвер WinDivert и возможный конфликт с VPN, античитом или антивирусом."
            )

        if return_code is not None:
            return f"winws2.exe завершился с кодом {return_code}."

        return "winws2.exe не подтвердил запуск."

    def _read_log_tail(self, log_file: Path, limit: int = 4000) -> str:
        try:
            if log_file.exists():
                return log_file.read_text(encoding="utf-8", errors="ignore")[-limit:]
        except OSError as exc:
            logger.error("Не удалось прочитать логи winws2.exe: %s", exc)
        return ""

    def _set_start_error(self, message: str) -> None:
        self.last_start_error = message
        self.runtime_state.mark_start_error(message)

    def start(self) -> bool:
        """Запуск winws2.exe с текущим пресетом."""
        try:
            logger.info("=== Запуск zapret ===")
            self.last_start_error = None

            if self.is_running():
                logger.warning("winws2.exe уже запущен")
                self.runtime_state.mark_zapret_active(self.get_current_preset_name())
                return True

            if not self.config.WINWS2_EXE.exists():
                message = f"winws2.exe не найден: {self.config.WINWS2_EXE}"
                logger.error(message)
                self._set_start_error(message)
                return False

            if not self.config.ACTIVE_PRESET.exists():
                message = f"Активный пресет не найден: {self.config.ACTIVE_PRESET}"
                logger.error(message)
                self._set_start_error(message)
                return False

            missing_resources = self.validate_active_preset_resources()
            if missing_resources:
                preview = "\n".join(str(path) for path in missing_resources[:10])
                extra = "" if len(missing_resources) <= 10 else "\n..."
                message = (
                    "В активном пресете отсутствуют ресурсы:\n"
                    f"{preview}{extra}"
                )
                logger.error(message)
                self._set_start_error(message)
                return False

            self._cleanup_windivert()
            time.sleep(1)
            self._enable_tcp_timestamps()

            cwd = self.config.RESOURCES_DIR if self.config.IS_FROZEN else self.config.BASE_DIR

            logger.info("Запуск winws2.exe с пресетом: %s", self.config.ACTIVE_PRESET)
            logger.info("Рабочая директория: %s", cwd)
            logger.info("Команда: %s @%s", self.config.WINWS2_EXE, self.config.ACTIVE_PRESET)

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

            log_file = create_winws2_log_file()
            with open(log_file, "w", encoding="utf-8") as log_f:
                self.process = subprocess.Popen(
                    [str(self.config.WINWS2_EXE), f"@{self.config.ACTIVE_PRESET}"],
                    cwd=str(cwd),
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                    startupinfo=startupinfo,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                )

            logger.info("winws2.exe запущен, PID: %s", self.process.pid)
            logger.info("Логи winws2.exe: %s", log_file)
            self.process_start_time = datetime.now()
            self._set_status_cache(True, self.process.pid)

            time.sleep(2)

            return_code = self.process.poll()
            if return_code is not None:
                log_content = self._read_log_tail(log_file)
                diagnostic = self.explain_start_failure(log_content, return_code)
                logger.error("winws2.exe завершился с кодом: %s", return_code)
                if log_content.strip():
                    logger.error("Вывод winws2.exe:\n%s", log_content)
                logger.error("Диагностика запуска: %s", diagnostic)
                self._set_status_cache(False, None)
                self._set_start_error(diagnostic)
                return False

            if not self.is_running():
                log_content = self._read_log_tail(log_file)
                diagnostic = self.explain_start_failure(log_content, None)
                if log_content.strip():
                    logger.error("Вывод winws2.exe:\n%s", log_content)
                logger.error("Диагностика запуска: %s", diagnostic)
                self._set_status_cache(False, None)
                self._set_start_error(diagnostic)
                return False

            self.runtime_state.mark_zapret_active(self.get_current_preset_name())
            return True

        except Exception as exc:
            message = f"Ошибка запуска winws2.exe: {exc}"
            logger.error(message, exc_info=True)
            self._set_status_cache(False, None)
            self._set_start_error(message)
            return False

    def stop(self) -> bool:
        """Остановка winws2.exe."""
        try:
            logger.info("=== Остановка zapret ===")

            if not self.is_running():
                logger.info("winws2.exe не запущен")
                self.process = None
                self.process_start_time = None
                self._set_status_cache(False, None)
                self.runtime_state.mark_zapret_inactive()
                return True

            result = subprocess.run(
                ["taskkill", "/F", "/IM", "winws2.exe"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )

            logger.info("Результат taskkill: %s", result.returncode)
            time.sleep(1)
            self._cleanup_windivert()

            self.process = None
            self.process_start_time = None
            self._status_cache_checked_at = 0.0

            if self.is_running():
                logger.warning("winws2.exe все еще запущен после остановки")
                return False

            self._set_status_cache(False, None)
            self.runtime_state.mark_zapret_inactive()
            logger.info("winws2.exe остановлен")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Таймаут при остановке winws2.exe")
            return False
        except Exception as exc:
            logger.error("Ошибка остановки winws2.exe: %s", exc, exc_info=True)
            return False

    def restart(self) -> bool:
        """Перезапуск winws2.exe."""
        logger.info("Перезапуск winws2.exe")

        if not self.stop():
            logger.error("Не удалось остановить winws2.exe")
            return False

        time.sleep(1)

        if not self.start():
            logger.error("Не удалось запустить winws2.exe")
            return False

        return True

    def get_status(self) -> Dict:
        """Получить статус процесса."""
        running = self.is_running()
        pid = self.get_pid() if running else None

        uptime = None
        if running and self.process_start_time:
            delta = datetime.now() - self.process_start_time
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            uptime = f"{hours}ч {minutes}м"

        preset_name = self.get_current_preset_name() or "не выбран"

        return {
            "running": running,
            "pid": pid,
            "uptime": uptime,
            "preset": preset_name,
            "last_start_error": self.last_start_error,
        }
