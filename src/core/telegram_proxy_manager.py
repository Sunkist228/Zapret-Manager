# -*- coding: utf-8 -*-
"""Management for an optional local Telegram proxy helper."""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

try:
    from utils.config import Config
    from utils.logger import logger
except ImportError:
    from src.utils.config import Config
    from src.utils.logger import logger


@dataclass(frozen=True)
class TelegramProxyStatus:
    installed: bool
    running: bool
    executable: Optional[Path]
    pid: Optional[int]
    log_file: Path
    socks_host: str = "127.0.0.1"
    socks_ports: tuple[int, ...] = (1080, 1443)


class TelegramProxyManager:
    """Start and stop an external local SOCKS5/WS helper for Telegram."""

    ENV_EXE = "ZAPRET_TELEGRAM_PROXY_EXE"
    ENV_ARGS = "ZAPRET_TELEGRAM_PROXY_ARGS"
    PROCESS_NAMES = (
        "tgwsproxy.exe",
        "tg-ws-proxy.exe",
        "tg_ws_proxy.exe",
        "telegram-ws-proxy.exe",
        "TelegramWsProxy.exe",
    )

    def __init__(self):
        self.config = Config
        self.log_file = Path(tempfile.gettempdir()) / "ZapretManager" / "telegram-proxy.log"

    def candidate_paths(self) -> list[Path]:
        paths: list[Path] = []

        env_path = os.environ.get(self.ENV_EXE)
        if env_path:
            paths.append(Path(env_path))

        base_dirs = [
            self.config.BASE_DIR / "tools" / "telegram-proxy",
            self.config.BASE_DIR / "tools",
            self.config.BASE_DIR / "bin",
            self.config.BASE_DIR / "exe",
            self.config.RESOURCES_DIR / "bin",
        ]

        for directory in base_dirs:
            for name in self.PROCESS_NAMES:
                paths.append(directory / name)

        deduped: list[Path] = []
        seen: set[str] = set()
        for path in paths:
            key = str(path).lower()
            if key not in seen:
                seen.add(key)
                deduped.append(path)
        return deduped

    def find_executable(self) -> Optional[Path]:
        for path in self.candidate_paths():
            if path.exists() and path.is_file():
                return path
        return None

    def _process_rows(self, process_names: Iterable[str]) -> list[list[str]]:
        rows: list[list[str]] = []
        for process_name in process_names:
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {process_name}", "/NH", "/FO", "CSV"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=self.config.PROCESS_CHECK_TIMEOUT,
                )
            except Exception as exc:
                logger.debug("Telegram proxy tasklist failed for %s: %s", process_name, exc)
                continue

            for line in result.stdout.splitlines():
                if process_name.lower() not in line.lower():
                    continue
                rows.append([part.strip().strip('"') for part in line.split(",")])
        return rows

    def is_running(self) -> bool:
        return self.get_pid() is not None

    def get_pid(self) -> Optional[int]:
        executable = self.find_executable()
        names = [executable.name] if executable else list(self.PROCESS_NAMES)

        for row in self._process_rows(names):
            if len(row) >= 2:
                try:
                    return int(row[1])
                except ValueError:
                    continue
        return None

    def get_status(self) -> TelegramProxyStatus:
        executable = self.find_executable()
        pid = self.get_pid()
        return TelegramProxyStatus(
            installed=executable is not None,
            running=pid is not None,
            executable=executable,
            pid=pid,
            log_file=self.log_file,
        )

    def start(self) -> bool:
        if self.is_running():
            logger.info("Telegram proxy is already running")
            return True

        executable = self.find_executable()
        if executable is None:
            logger.error("Telegram proxy executable was not found")
            return False

        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        args = os.environ.get(self.ENV_ARGS, "").split()

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0

        logger.info("Starting Telegram proxy: %s", executable)
        logger.info("Telegram proxy log: %s", self.log_file)

        try:
            with open(self.log_file, "w", encoding="utf-8") as log_f:
                process = subprocess.Popen(
                    [str(executable), *args],
                    cwd=str(executable.parent),
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                    startupinfo=startupinfo,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                )

            time.sleep(1)
            return_code = process.poll()
            if return_code is not None:
                logger.error("Telegram proxy exited with code %s", return_code)
                return False

            return self.is_running()
        except Exception as exc:
            logger.error("Failed to start Telegram proxy: %s", exc, exc_info=True)
            return False

    def stop(self) -> bool:
        status = self.get_status()
        if not status.running:
            return True

        names = [status.executable.name] if status.executable else list(self.PROCESS_NAMES)
        ok = True

        for process_name in names:
            try:
                result = subprocess.run(
                    ["taskkill", "/F", "/IM", process_name],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10,
                )
                if result.returncode not in (0, 128):
                    ok = False
                    logger.warning("taskkill %s returned %s", process_name, result.returncode)
            except Exception as exc:
                ok = False
                logger.error("Failed to stop Telegram proxy %s: %s", process_name, exc)

        time.sleep(1)
        return ok and not self.is_running()
