# -*- coding: utf-8 -*-
"""
Диагностика системы (портирование из service.bat)
"""

import subprocess
from typing import Dict, List
from dataclasses import dataclass

from ..utils.config import Config
from ..utils.logger import logger


@dataclass
class DiagnosticResult:
    """Результат диагностической проверки"""
    name: str
    status: str  # 'ok', 'warning', 'error'
    message: str
    fixable: bool = False


class DiagnosticsManager:
    """Диагностика системы"""

    def __init__(self):
        self.config = Config

    def check_bfe_service(self) -> DiagnosticResult:
        """Проверка Base Filtering Engine"""
        try:
            result = subprocess.run(
                ['sc', 'query', 'BFE'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5
            )

            if 'RUNNING' in result.stdout:
                return DiagnosticResult(
                    name="Base Filtering Engine",
                    status="ok",
                    message="Запущен"
                )
            else:
                return DiagnosticResult(
                    name="Base Filtering Engine",
                    status="error",
                    message="Не запущен",
                    fixable=True
                )

        except Exception as e:
            logger.error(f"Ошибка проверки BFE: {e}")
            return DiagnosticResult(
                name="Base Filtering Engine",
                status="error",
                message=f"Ошибка проверки: {e}"
            )

    def check_tcp_timestamps(self) -> DiagnosticResult:
        """Проверка TCP timestamps"""
        try:
            result = subprocess.run(
                ['netsh', 'interface', 'tcp', 'show', 'global'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5
            )

            if 'timestamps' in result.stdout.lower() and 'enabled' in result.stdout.lower():
                return DiagnosticResult(
                    name="TCP timestamps",
                    status="ok",
                    message="Включены"
                )
            else:
                return DiagnosticResult(
                    name="TCP timestamps",
                    status="warning",
                    message="Отключены (рекомендуется включить)",
                    fixable=True
                )

        except Exception as e:
            logger.error(f"Ошибка проверки TCP timestamps: {e}")
            return DiagnosticResult(
                name="TCP timestamps",
                status="error",
                message=f"Ошибка проверки: {e}"
            )

    def check_windivert_driver(self) -> DiagnosticResult:
        """Проверка WinDivert драйвера"""
        windivert_files = [
            self.config.BIN_DIR / "WinDivert.dll",
            self.config.BIN_DIR / "WinDivert32.sys",
            self.config.BIN_DIR / "WinDivert64.sys"
        ]

        missing = [f.name for f in windivert_files if not f.exists()]

        if not missing:
            return DiagnosticResult(
                name="WinDivert драйвер",
                status="ok",
                message="Найден"
            )
        else:
            return DiagnosticResult(
                name="WinDivert драйвер",
                status="error",
                message=f"Отсутствуют файлы: {', '.join(missing)}"
            )

    def check_conflicting_services(self) -> DiagnosticResult:
        """Проверка конфликтующих сервисов"""
        conflicts = []

        for service in self.config.CONFLICTING_SERVICES:
            try:
                result = subprocess.run(
                    ['sc', 'query', service],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5
                )

                if result.returncode == 0:
                    conflicts.append(service)

            except Exception:
                pass

        if not conflicts:
            return DiagnosticResult(
                name="Конфликтующие сервисы",
                status="ok",
                message="Не обнаружены"
            )
        else:
            return DiagnosticResult(
                name="Конфликтующие сервисы",
                status="error",
                message=f"Обнаружены: {', '.join(conflicts)}",
                fixable=True
            )

    def check_vpn_services(self) -> DiagnosticResult:
        """Проверка VPN сервисов"""
        try:
            result = subprocess.run(
                ['sc', 'query'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5
            )

            vpn_keywords = ['VPN', 'OpenVPN', 'WireGuard', 'NordVPN', 'ExpressVPN']
            vpn_services = []

            for line in result.stdout.split('\n'):
                if 'SERVICE_NAME:' in line:
                    service_name = line.split(':', 1)[1].strip()
                    if any(keyword.lower() in service_name.lower() for keyword in vpn_keywords):
                        vpn_services.append(service_name)

            if not vpn_services:
                return DiagnosticResult(
                    name="VPN сервисы",
                    status="ok",
                    message="Не обнаружены"
                )
            else:
                return DiagnosticResult(
                    name="VPN сервисы",
                    status="warning",
                    message=f"Обнаружены: {', '.join(vpn_services[:3])} (могут конфликтовать)"
                )

        except Exception as e:
            logger.error(f"Ошибка проверки VPN: {e}")
            return DiagnosticResult(
                name="VPN сервисы",
                status="error",
                message=f"Ошибка проверки: {e}"
            )

    def check_killer_network(self) -> DiagnosticResult:
        """Проверка Killer Network"""
        try:
            result = subprocess.run(
                ['sc', 'query'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5
            )

            if 'Killer' in result.stdout:
                return DiagnosticResult(
                    name="Killer Network",
                    status="error",
                    message="Обнаружен (конфликтует с zapret)"
                )
            else:
                return DiagnosticResult(
                    name="Killer Network",
                    status="ok",
                    message="Не обнаружен"
                )

        except Exception as e:
            logger.error(f"Ошибка проверки Killer Network: {e}")
            return DiagnosticResult(
                name="Killer Network",
                status="error",
                message=f"Ошибка проверки: {e}"
            )

    def check_adguard(self) -> DiagnosticResult:
        """Проверка Adguard"""
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq AdguardSvc.exe'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5
            )

            if 'AdguardSvc.exe' in result.stdout:
                return DiagnosticResult(
                    name="Adguard",
                    status="warning",
                    message="Запущен (может мешать Discord)"
                )
            else:
                return DiagnosticResult(
                    name="Adguard",
                    status="ok",
                    message="Не обнаружен"
                )

        except Exception as e:
            logger.error(f"Ошибка проверки Adguard: {e}")
            return DiagnosticResult(
                name="Adguard",
                status="error",
                message=f"Ошибка проверки: {e}"
            )

    def run_full_diagnostics(self) -> List[DiagnosticResult]:
        """
        Полная диагностика системы

        Returns:
            Список результатов проверок
        """
        logger.info("Запуск полной диагностики")

        results = [
            self.check_bfe_service(),
            self.check_tcp_timestamps(),
            self.check_windivert_driver(),
            self.check_conflicting_services(),
            self.check_vpn_services(),
            self.check_killer_network(),
            self.check_adguard(),
        ]

        # Логируем результаты
        for result in results:
            if result.status == 'error':
                logger.error(f"{result.name}: {result.message}")
            elif result.status == 'warning':
                logger.warning(f"{result.name}: {result.message}")
            else:
                logger.info(f"{result.name}: {result.message}")

        return results

    def fix_problems(self) -> Dict[str, bool]:
        """
        Попытка исправить обнаруженные проблемы

        Returns:
            Словарь {проблема: успешно_исправлена}
        """
        logger.info("Исправление проблем")
        results = {}

        # Включаем TCP timestamps
        try:
            subprocess.run(
                ['netsh', 'interface', 'tcp', 'set', 'global', 'timestamps=enabled'],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5
            )
            results['tcp_timestamps'] = True
            logger.info("TCP timestamps включены")
        except Exception as e:
            results['tcp_timestamps'] = False
            logger.error(f"Не удалось включить TCP timestamps: {e}")

        # Удаляем конфликтующие сервисы
        for service in self.config.CONFLICTING_SERVICES:
            try:
                # Проверяем существование
                result = subprocess.run(
                    ['sc', 'query', service],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5
                )

                if result.returncode == 0:
                    # Останавливаем
                    subprocess.run(
                        ['net', 'stop', service],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=5
                    )

                    # Удаляем
                    subprocess.run(
                        ['sc', 'delete', service],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=5
                    )

                    results[f'service_{service}'] = True
                    logger.info(f"Сервис {service} удален")

            except Exception as e:
                results[f'service_{service}'] = False
                logger.error(f"Не удалось удалить сервис {service}: {e}")

        # Очищаем WinDivert
        for service in self.config.WINDIVERT_SERVICES:
            try:
                subprocess.run(
                    ['sc', 'query', service],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5
                )

                subprocess.run(
                    ['net', 'stop', service],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5
                )

                subprocess.run(
                    ['sc', 'delete', service],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5
                )

            except Exception:
                pass

        return results
