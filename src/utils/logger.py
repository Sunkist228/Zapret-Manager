# -*- coding: utf-8 -*-
"""
Утилиты для логирования
"""

import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
import tempfile
from datetime import datetime


LOG_RETENTION_DAYS = 14
LOG_DIR = Path(tempfile.gettempdir()) / "ZapretManager"


def cleanup_old_logs(log_dir: Path = LOG_DIR, retention_days: int = LOG_RETENTION_DAYS) -> None:
    """Remove application logs older than the configured retention window."""
    if retention_days <= 0 or not log_dir.exists():
        return

    cutoff = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
    for pattern in ("app.log.*", "winws2-*.log", "winws2.log.*"):
        for path in log_dir.glob(pattern):
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
            except OSError:
                pass


def create_winws2_log_file(log_dir: Path = LOG_DIR) -> Path:
    """Return a unique per-run log path for winws2 output."""
    log_dir.mkdir(parents=True, exist_ok=True)
    cleanup_old_logs(log_dir)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = log_dir / f"winws2-{timestamp}.log"
    if not log_file.exists():
        return log_file

    index = 1
    while True:
        candidate = log_dir / f"winws2-{timestamp}-{index}.log"
        if not candidate.exists():
            return candidate
        index += 1


def setup_logger(name: str = "ZapretManager", level: int = logging.INFO) -> logging.Logger:
    """
    Настройка логгера с ротацией файлов

    Args:
        name: Имя логгера
        level: Уровень логирования

    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Избегаем дублирования хэндлеров
    if logger.handlers:
        return logger

    # Создаем директорию для логов
    LOG_DIR.mkdir(exist_ok=True)
    cleanup_old_logs(LOG_DIR)
    log_file = LOG_DIR / "app.log"

    # Формат логов
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Файловый хэндлер с ротацией (макс 10 MB)
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=LOG_RETENTION_DAYS,
        encoding="utf-8",
        utc=False,
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Консольный хэндлер (только для разработки)
    if sys.stdout is not None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


# Глобальный логгер
logger = setup_logger()
