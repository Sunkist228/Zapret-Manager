# -*- coding: utf-8 -*-
"""
Управление списками доменов и IP-адресов
"""

from pathlib import Path
from typing import List, Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import Config
from utils.logger import logger
from utils.validators import Validators


class ListManager:
    """Управление списками доменов/IP"""

    def __init__(self):
        self.config = Config

    def list_files(self) -> List[str]:
        """
        Получить список всех файлов списков

        Returns:
            Список имен файлов
        """
        if not self.config.LISTS_DIR.exists():
            logger.error(f"Директория списков не найдена: {self.config.LISTS_DIR}")
            return []

        files = []
        for list_file in sorted(self.config.LISTS_DIR.glob("*.txt")):
            files.append(list_file.name)

        return files

    def read_list(self, list_name: str) -> List[str]:
        """
        Прочитать список

        Args:
            list_name: Имя файла списка

        Returns:
            Список записей (домены/IP)
        """
        list_path = self.config.LISTS_DIR / list_name

        if not list_path.exists():
            logger.error(f"Список не найден: {list_name}")
            return []

        try:
            content = list_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Фильтруем пустые строки
            entries = [line.strip() for line in lines if line.strip()]

            return entries

        except Exception as e:
            logger.error(f"Ошибка чтения списка {list_name}: {e}")
            return []

    def write_list(self, list_name: str, entries: List[str]) -> bool:
        """
        Записать список

        Args:
            list_name: Имя файла списка
            entries: Список записей

        Returns:
            True если успешно
        """
        list_path = self.config.LISTS_DIR / list_name

        try:
            # Валидация записей
            valid_entries = []
            for entry in entries:
                entry = entry.strip()
                if not entry:
                    continue

                # Пропускаем комментарии
                if entry.startswith('#'):
                    valid_entries.append(entry)
                    continue

                # Валидируем
                is_valid, entry_type = Validators.validate_list_entry(entry)
                if is_valid:
                    valid_entries.append(entry)
                else:
                    logger.warning(f"Невалидная запись пропущена: {entry}")

            # Записываем
            content = '\n'.join(valid_entries)
            list_path.write_text(content, encoding='utf-8')

            logger.info(f"Список {list_name} сохранен ({len(valid_entries)} записей)")
            return True

        except Exception as e:
            logger.error(f"Ошибка записи списка {list_name}: {e}", exc_info=True)
            return False

    def add_entry(self, list_name: str, entry: str) -> bool:
        """
        Добавить запись в список

        Args:
            list_name: Имя файла списка
            entry: Запись (домен или IP)

        Returns:
            True если успешно
        """
        entry = entry.strip()

        # Валидация
        is_valid, entry_type = Validators.validate_list_entry(entry)
        if not is_valid:
            logger.error(f"Невалидная запись: {entry}")
            return False

        # Читаем текущий список
        entries = self.read_list(list_name)

        # Проверяем дубликаты
        if entry in entries:
            logger.warning(f"Запись уже существует: {entry}")
            return False

        # Добавляем
        entries.append(entry)

        # Сохраняем
        return self.write_list(list_name, entries)

    def remove_entry(self, list_name: str, entry: str) -> bool:
        """
        Удалить запись из списка

        Args:
            list_name: Имя файла списка
            entry: Запись для удаления

        Returns:
            True если успешно
        """
        entry = entry.strip()

        # Читаем текущий список
        entries = self.read_list(list_name)

        # Удаляем
        if entry in entries:
            entries.remove(entry)
            return self.write_list(list_name, entries)
        else:
            logger.warning(f"Запись не найдена: {entry}")
            return False

    def create_list(self, list_name: str) -> bool:
        """
        Создать новый список

        Args:
            list_name: Имя файла списка

        Returns:
            True если успешно
        """
        list_path = self.config.LISTS_DIR / list_name

        if list_path.exists():
            logger.error(f"Список уже существует: {list_name}")
            return False

        try:
            list_path.write_text("", encoding='utf-8')
            logger.info(f"Создан новый список: {list_name}")
            return True

        except Exception as e:
            logger.error(f"Ошибка создания списка: {e}")
            return False

    def delete_list(self, list_name: str) -> bool:
        """
        Удалить список

        Args:
            list_name: Имя файла списка

        Returns:
            True если успешно
        """
        list_path = self.config.LISTS_DIR / list_name

        if not list_path.exists():
            logger.error(f"Список не найден: {list_name}")
            return False

        try:
            list_path.unlink()
            logger.info(f"Список удален: {list_name}")
            return True

        except Exception as e:
            logger.error(f"Ошибка удаления списка: {e}")
            return False

    def import_list(self, file_path: Path, list_name: Optional[str] = None) -> bool:
        """
        Импорт списка из файла

        Args:
            file_path: Путь к файлу
            list_name: Имя для сохранения (если None, используется имя файла)

        Returns:
            True если успешно
        """
        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            return False

        try:
            # Читаем файл
            content = file_path.read_text(encoding='utf-8')
            entries = [line.strip() for line in content.split('\n') if line.strip()]

            # Определяем имя
            if list_name is None:
                list_name = file_path.name

            # Сохраняем
            return self.write_list(list_name, entries)

        except Exception as e:
            logger.error(f"Ошибка импорта списка: {e}")
            return False

    def export_list(self, list_name: str, dest_path: Path) -> bool:
        """
        Экспорт списка в файл

        Args:
            list_name: Имя списка
            dest_path: Путь для сохранения

        Returns:
            True если успешно
        """
        list_path = self.config.LISTS_DIR / list_name

        if not list_path.exists():
            logger.error(f"Список не найден: {list_name}")
            return False

        try:
            import shutil
            shutil.copy2(list_path, dest_path)
            logger.info(f"Список экспортирован: {dest_path}")
            return True

        except Exception as e:
            logger.error(f"Ошибка экспорта списка: {e}")
            return False
