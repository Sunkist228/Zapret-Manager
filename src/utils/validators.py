# -*- coding: utf-8 -*-
"""
Валидаторы для конфигурационных файлов
"""

import re
import ipaddress
from pathlib import Path
from typing import Optional


class Validators:
    """Валидаторы данных"""

    # Regex для доменов
    DOMAIN_REGEX = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$"
    )

    @staticmethod
    def validate_domain(domain: str) -> bool:
        """
        Валидация домена

        Args:
            domain: Доменное имя

        Returns:
            True если домен валиден
        """
        if not domain or len(domain) > 253:
            return False

        # Удаляем пробелы
        domain = domain.strip()

        # Проверяем regex
        return bool(Validators.DOMAIN_REGEX.match(domain))

    @staticmethod
    def validate_ip(ip: str) -> bool:
        """
        Валидация IP-адреса (IPv4 или IPv6)

        Args:
            ip: IP-адрес

        Returns:
            True если IP валиден
        """
        try:
            ipaddress.ip_address(ip.strip())
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_ip_network(network: str) -> bool:
        """
        Валидация IP-сети (CIDR)

        Args:
            network: IP-сеть в формате CIDR (например, 192.168.1.0/24)

        Returns:
            True если сеть валидна
        """
        try:
            ipaddress.ip_network(network.strip(), strict=False)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_preset_file(preset_path: Path) -> bool:
        """
        Валидация файла пресета

        Args:
            preset_path: Путь к файлу пресета

        Returns:
            True если пресет валиден
        """
        if not preset_path.exists() or not preset_path.is_file():
            return False

        try:
            content = preset_path.read_text(encoding="utf-8")

            # Базовая проверка: файл не пустой и содержит хотя бы одну опцию
            if not content.strip():
                return False

            # Проверяем что есть хотя бы одна строка с --
            has_option = any(line.strip().startswith("--") for line in content.split("\n"))

            return has_option

        except Exception:
            return False

    @staticmethod
    def sanitize_path(path: str) -> Optional[Path]:
        """
        Безопасная обработка пути (защита от directory traversal)

        Args:
            path: Путь для проверки

        Returns:
            Path объект или None если путь небезопасен
        """
        try:
            p = Path(path).resolve()

            # Проверяем что путь не содержит .. и другие опасные элементы
            if ".." in p.parts:
                return None

            return p

        except Exception:
            return None

    @staticmethod
    def validate_list_entry(entry: str) -> tuple[bool, str]:
        """
        Валидация записи в списке (домен или IP)

        Args:
            entry: Запись для проверки

        Returns:
            (валидна, тип: 'domain', 'ip', 'network' или 'invalid')
        """
        entry = entry.strip()

        if not entry or entry.startswith("#"):
            return False, "comment"

        # Проверяем IP
        if Validators.validate_ip(entry):
            return True, "ip"

        # Проверяем сеть
        if "/" in entry and Validators.validate_ip_network(entry):
            return True, "network"

        # Проверяем домен
        if Validators.validate_domain(entry):
            return True, "domain"

        return False, "invalid"
