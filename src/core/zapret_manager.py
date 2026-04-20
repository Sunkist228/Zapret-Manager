# -*- coding: utf-8 -*-
"""
Управление процессом winws2.exe
"""

import subprocess
import time
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from utils.config import Config
from utils.logger import logger


class ZapretManager:
    """Управление процессом winws2.exe"""

    def __init__(self):
        self.config = Config
        self.process_start_time: Optional[datetime] = None

    def is_running(self) -> bool:
        """
        Проверка запущен ли winws2.exe

        Returns:
            True если процесс запущен
        """
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq winws2.exe", "/NH"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=self.config.PROCESS_CHECK_TIMEOUT,
            )
            return "winws2.exe" in result.stdout
        except Exception as e:
            logger.error(f"Ошибка проверки статуса winws2.exe: {e}")
            return False

    def get_pid(self) -> Optional[int]:
        """
        Получить PID процесса winws2.exe

        Returns:
            PID или None если процесс не запущен
        """
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq winws2.exe", "/NH", "/FO", "CSV"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=self.config.PROCESS_CHECK_TIMEOUT,
            )

            if "winws2.exe" in result.stdout:
                # Парсим CSV: "winws2.exe","12345",...
                parts = result.stdout.split(",")
                if len(parts) >= 2:
                    pid_str = parts[1].strip('"')
                    return int(pid_str)

        except Exception as e:
            logger.error(f"Ошибка получения PID: {e}")

        return None

    def _cleanup_windivert(self):
        """Очистка WinDivert сервисов"""
        logger.info("Очистка WinDivert сервисов")

        for service in self.config.WINDIVERT_SERVICES:
            try:
                # Проверяем существование сервиса
                result = subprocess.run(
                    ["sc", "query", service],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5,
                )

                if result.returncode == 0:
                    # Останавливаем
                    subprocess.run(
                        ["net", "stop", service],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=5,
                    )

                    # Удаляем
                    subprocess.run(
                        ["sc", "delete", service],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=5,
                    )

                    logger.info(f"Сервис {service} очищен")

            except Exception as e:
                logger.debug(f"Сервис {service}: {e}")

    def _enable_tcp_timestamps(self):
        """Включение TCP timestamps"""
        try:
            logger.info("Включение TCP timestamps")
            subprocess.run(
                ["netsh", "interface", "tcp", "set", "global", "timestamps=enabled"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
            )
        except Exception as e:
            logger.warning(f"Не удалось включить TCP timestamps: {e}")

    def start(self) -> bool:
        """
        Запуск winws2.exe с текущим пресетом

        Returns:
            True если запуск успешен
        """
        try:
            logger.info("=== Запуск zapret ===")

            # Проверка что уже не запущен
            if self.is_running():
                logger.warning("winws2.exe уже запущен")
                return True

            # Проверка наличия winws2.exe
            if not self.config.WINWS2_EXE.exists():
                logger.error(f"winws2.exe не найден: {self.config.WINWS2_EXE}")
                return False

            # Проверка наличия активного пресета
            if not self.config.ACTIVE_PRESET.exists():
                logger.error(
                    f"Активный пресет не найден: {self.config.ACTIVE_PRESET}"
                )
                return False

            # Очистка WinDivert
            self._cleanup_windivert()
            time.sleep(1)

            # Включение TCP timestamps
            self._enable_tcp_timestamps()

            # Определяем рабочую директорию
            # In frozen mode winws2.exe must run from resources/ so relative paths work.
            if self.config.IS_FROZEN:
                cwd = self.config.RESOURCES_DIR
            else:
                cwd = self.config.BASE_DIR

            # Запуск winws2.exe в фоне
            logger.info(f"Запуск winws2.exe с пресетом: {self.config.ACTIVE_PRESET}")
            logger.info(f"Рабочая директория: {cwd}")
            logger.info(f"Команда: {self.config.WINWS2_EXE} @{self.config.ACTIVE_PRESET}")

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE

            # Создаем временный файл для логов winws2.exe
            import tempfile

            log_file = Path(tempfile.gettempdir()) / "ZapretManager" / "winws2.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Запускаем с захватом вывода
            with open(log_file, "w", encoding="utf-8") as log_f:
                process = subprocess.Popen(
                    [str(self.config.WINWS2_EXE), f"@{self.config.ACTIVE_PRESET}"],
                    cwd=str(cwd),
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                    startupinfo=startupinfo,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                )

            logger.info(f"winws2.exe запущен, PID: {process.pid}")
            logger.info(f"Логи winws2.exe: {log_file}")
            self.process_start_time = datetime.now()

            # Verify that the process actually started.
            time.sleep(2)

            # Проверяем код возврата
            return_code = process.poll()
            if return_code is not None:
                logger.error(f"winws2.exe завершился с кодом: {return_code}")
                # Читаем логи для диагностики
                try:
                    if log_file.exists():
                        log_content = log_file.read_text(encoding="utf-8", errors="ignore")
                        logger.error(f"Вывод winws2.exe:\n{log_content}")
                except Exception as e:
                    logger.error(f"Не удалось прочитать логи: {e}")
                return False

            if not self.is_running():
                logger.error("winws2.exe не удалось запустить")
                # Читаем логи для диагностики
                try:
                    if log_file.exists():
                        log_content = log_file.read_text(encoding="utf-8", errors="ignore")
                        logger.error(f"Вывод winws2.exe:\n{log_content}")
                except Exception as e:
                    logger.error(f"Не удалось прочитать логи: {e}")
                return False

            return True

        except Exception as e:
            logger.error(f"Ошибка запуска winws2.exe: {e}", exc_info=True)
            return False

    def stop(self) -> bool:
        """
        Остановка winws2.exe

        Returns:
            True если остановка успешна
        """
        try:
            logger.info("=== Остановка zapret ===")

            if not self.is_running():
                logger.info("winws2.exe не запущен")
                return True

            # Останавливаем процесс
            result = subprocess.run(
                ["taskkill", "/F", "/IM", "winws2.exe"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )

            logger.info(f"Результат taskkill: {result.returncode}")

            # Ждем завершения
            time.sleep(1)

            # Очистка WinDivert
            self._cleanup_windivert()

            self.process_start_time = None

            # Verify that the process actually stopped.
            if self.is_running():
                logger.warning(
                    "winws2.exe все еще запущен после остановки"
                )
                return False

            logger.info("winws2.exe остановлен")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Таймаут при остановке winws2.exe")
            return False
        except Exception as e:
            logger.error(f"Ошибка остановки winws2.exe: {e}", exc_info=True)
            return False

    def restart(self) -> bool:
        """
        Перезапуск winws2.exe

        Returns:
            True если перезапуск успешен
        """
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
        """
        Получить статус процесса

        Returns:
            Словарь со статусом: running, pid, uptime, preset
        """
        running = self.is_running()
        pid = self.get_pid() if running else None

        # Uptime
        uptime = None
        if running and self.process_start_time:
            delta = datetime.now() - self.process_start_time
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            uptime = f"{hours}ч {minutes}м"

        # Текущий пресет
        preset_name = "не выбран"
        if self.config.CURRENT_PRESET_NAME.exists():
            try:
                preset_name = self.config.CURRENT_PRESET_NAME.read_text(encoding="utf-8").strip()
            except Exception:
                pass

        return {"running": running, "pid": pid, "uptime": uptime, "preset": preset_name}
