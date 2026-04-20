# -*- coding: utf-8 -*-
"""
Утилиты для логирования
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import tempfile


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
    log_dir = Path(tempfile.gettempdir()) / "ZapretManager"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"

    # Формат логов
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Файловый хэндлер с ротацией (макс 10 MB)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"  # 10 MB
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
