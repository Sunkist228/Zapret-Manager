# -*- coding: utf-8 -*-
"""
Управление пресетами
"""

import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

from utils.config import Config
from utils.logger import logger
from utils.validators import Validators


@dataclass
class Preset:
    """Информация о пресете"""

    name: str
    path: Path
    description: str = ""
    is_active: bool = False


class PresetManager:
    """Управление пресетами"""

    def __init__(self):
        self.config = Config
        self.config.ensure_config_dir()

        # Установить дефолтный пресет при первом запуске
        if not self.config.ACTIVE_PRESET.exists():
            self._set_default_preset()
        else:
            # Синхронизация активного пресета с файлом в директории пресетов (при обновлении)
            try:
                active_name = self.get_active_preset_name()
                if active_name:
                    source_preset = self.config.PRESETS_DIR / f"{active_name}.txt"
                    if source_preset.exists():
                        shutil.copy2(source_preset, self.config.ACTIVE_PRESET)
                        logger.info(f"Активный пресет '{active_name}' синхронизирован с источником")
                    else:
                        logger.warning(f"Источник для активного пресета '{active_name}' не найден")
            except Exception as e:
                logger.error(f"Ошибка синхронизации активного пресета: {e}")

    def _set_default_preset(self):
        """Установить дефолтный пресет при первом запуске"""
        try:
            logger.info("Установка дефолтного пресета")
            default_preset = self.config.PRESETS_DIR / f"{self.config.DEFAULT_PRESET_NAME}.txt"

            if default_preset.exists():
                shutil.copy2(default_preset, self.config.ACTIVE_PRESET)
                self.config.CURRENT_PRESET_NAME.write_text(
                    self.config.DEFAULT_PRESET_NAME, encoding="utf-8"
                )
                logger.info("Дефолтный пресет установлен")
            else:
                logger.warning(f"Дефолтный пресет не найден: {default_preset}")
        except Exception as e:
            logger.error(f"Ошибка установки дефолтного пресета: {e}")

    def list_presets(self) -> List[Preset]:
        """
        Получить список всех пресетов

        Returns:
            Список объектов Preset
        """
        presets = []

        if not self.config.PRESETS_DIR.exists():
            logger.error(f"Директория пресетов не найдена: {self.config.PRESETS_DIR}")
            return presets

        # Получаем активный пресет
        active_preset_name = self.get_active_preset_name()

        # Сканируем директорию
        for preset_file in sorted(self.config.PRESETS_DIR.glob("*.txt")):
            # Пропускаем файлы начинающиеся с _
            if preset_file.name.startswith("_"):
                continue

            name = preset_file.stem
            description = self._extract_description(preset_file)
            is_active = name == active_preset_name

            presets.append(
                Preset(name=name, path=preset_file, description=description, is_active=is_active)
            )

        return presets

    def _extract_description(self, preset_path: Path) -> str:
        """
        Извлечь описание из пресета (из комментариев)

        Args:
            preset_path: Путь к файлу пресета

        Returns:
            Описание или пустая строка
        """
        try:
            content = preset_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Ищем строку # Description:
            for line in lines:
                if line.strip().startswith("# Description:"):
                    return line.split(":", 1)[1].strip()

            return ""

        except Exception as e:
            logger.debug(f"Не удалось извлечь описание из {preset_path.name}: {e}")
            return ""

    def get_active_preset_name(self) -> Optional[str]:
        """
        Получить имя активного пресета

        Returns:
            Имя пресета или None
        """
        if not self.config.CURRENT_PRESET_NAME.exists():
            return None

        try:
            name = self.config.CURRENT_PRESET_NAME.read_text(encoding="utf-8").strip()
            return name if name else None
        except Exception as e:
            logger.error(f"Ошибка чтения имени активного пресета: {e}")
            return None

    def get_active_preset(self) -> Optional[Preset]:
        """
        Получить активный пресет

        Returns:
            Объект Preset или None
        """
        name = self.get_active_preset_name()
        if not name:
            return None

        # Ищем пресет в списке
        for preset in self.list_presets():
            if preset.name == name:
                return preset

        return None

    def set_active_preset(self, preset_name: str) -> bool:
        """
        Установить активный пресет

        Args:
            preset_name: Имя пресета

        Returns:
            True если успешно
        """
        try:
            logger.info(f"Установка активного пресета: {preset_name}")

            # Ищем пресет
            preset_path = self.config.PRESETS_DIR / f"{preset_name}.txt"

            if not preset_path.exists():
                logger.error(f"Пресет не найден: {preset_path}")
                return False

            # Валидация пресета
            if not Validators.validate_preset_file(preset_path):
                logger.error(f"Пресет невалиден: {preset_path}")
                return False

            # Копируем в активный пресет
            shutil.copy2(preset_path, self.config.ACTIVE_PRESET)

            # Сохраняем имя
            self.config.CURRENT_PRESET_NAME.write_text(preset_name, encoding="utf-8")

            logger.info(f"Пресет '{preset_name}' установлен как активный")
            return True

        except Exception as e:
            logger.error(f"Ошибка установки пресета: {e}", exc_info=True)
            return False

    def import_preset(self, file_path: Path, name: Optional[str] = None) -> bool:
        """
        Импорт пользовательского пресета

        Args:
            file_path: Путь к файлу пресета
            name: Имя для сохранения (если None, используется имя файла)

        Returns:
            True если успешно
        """
        try:
            if not file_path.exists():
                logger.error(f"Файл не найден: {file_path}")
                return False

            # Валидация
            if not Validators.validate_preset_file(file_path):
                logger.error(f"Файл не является валидным пресетом: {file_path}")
                return False

            # Определяем имя
            if name is None:
                name = file_path.stem

            # Путь назначения
            dest_path = self.config.PRESETS_DIR / f"{name}.txt"

            # Проверяем что не перезаписываем существующий
            if dest_path.exists():
                logger.warning(f"Пресет с именем '{name}' уже существует")
                # Добавляем суффикс
                counter = 1
                while dest_path.exists():
                    dest_path = self.config.PRESETS_DIR / f"{name}_{counter}.txt"
                    counter += 1

            # Копируем
            shutil.copy2(file_path, dest_path)

            logger.info(f"Пресет импортирован: {dest_path.name}")
            return True

        except Exception as e:
            logger.error(f"Ошибка импорта пресета: {e}", exc_info=True)
            return False

    def export_preset(self, preset_name: str, dest_path: Path) -> bool:
        """
        Экспорт пресета

        Args:
            preset_name: Имя пресета
            dest_path: Путь для сохранения

        Returns:
            True если успешно
        """
        try:
            preset_path = self.config.PRESETS_DIR / f"{preset_name}.txt"

            if not preset_path.exists():
                logger.error(f"Пресет не найден: {preset_name}")
                return False

            # Копируем
            shutil.copy2(preset_path, dest_path)

            logger.info(f"Пресет экспортирован: {dest_path}")
            return True

        except Exception as e:
            logger.error(f"Ошибка экспорта пресета: {e}", exc_info=True)
            return False

    def search_presets(self, query: str) -> List[Preset]:
        """
        Поиск пресетов по имени или описанию

        Args:
            query: Поисковый запрос

        Returns:
            Список найденных пресетов
        """
        query_lower = query.lower()
        all_presets = self.list_presets()

        return [
            preset
            for preset in all_presets
            if query_lower in preset.name.lower() or query_lower in preset.description.lower()
        ]
