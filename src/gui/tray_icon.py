# -*- coding: utf-8 -*-
"""
System tray icon for Zapret Manager.
"""

import subprocess
import tempfile
import threading
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QMessageBox, QSystemTrayIcon

from core.autostart import AutostartManager
from core.preset_manager import PresetManager
from core.telegram_proxy_manager import TelegramProxyManager
from core.update_manager import UpdateError, UpdateManager
from core.zapret_manager import ZapretManager
from utils.config import Config
from utils.logger import logger


class ZapretTrayIcon(QSystemTrayIcon):
    """Tray icon controller."""

    update_check_finished = pyqtSignal(object, bool)
    update_check_failed = pyqtSignal(str, bool)
    update_download_finished = pyqtSignal(object)
    update_download_failed = pyqtSignal(str)

    def __init__(self, parent=None, auto_start: bool = False):
        super().__init__(parent)

        self.zapret_manager = ZapretManager()
        self.preset_manager = PresetManager()
        self.telegram_proxy_manager = TelegramProxyManager()
        self.autostart_manager = AutostartManager()
        self.update_manager = UpdateManager()

        self.main_window = None
        self.available_release = None
        self.downloaded_update = self.update_manager.get_downloaded_update()
        self.update_check_in_progress = False
        self.update_download_in_progress = False

        self.create_menu()
        self.set_icon_color("red")
        self.activated.connect(self.on_tray_activated)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(Config.STATUS_UPDATE_INTERVAL)

        self.update_check_finished.connect(self.on_update_check_finished)
        self.update_check_failed.connect(self.on_update_check_failed)
        self.update_download_finished.connect(self.on_update_download_finished)
        self.update_download_failed.connect(self.on_update_download_failed)

        self.update_status()
        self.check_autostart()
        self.refresh_update_actions()
        QTimer.singleShot(5000, self.schedule_background_update_check)
        if auto_start:
            QTimer.singleShot(1000, self.start_zapret)

    def show_notification(
        self,
        title: str,
        message: str,
        icon=QSystemTrayIcon.Information,
        duration: int = 2000,
        level: str = "success",
    ):
        """Show a tray notification only when enabled by config."""
        if not Config.should_show_notification(level):
            return

        self.showMessage(title, message, icon, duration)

    def create_menu(self):
        """Create tray context menu."""
        self.menu = QMenu()

        self.status_action = QAction("Статус: проверка...", self.menu)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)
        self.menu.addSeparator()

        self.toggle_action = QAction("▶ Включить", self.menu)
        self.toggle_action.triggered.connect(self.toggle_zapret)
        self.menu.addAction(self.toggle_action)

        self.restart_action = QAction("Перезапустить", self.menu)
        self.restart_action.triggered.connect(self.restart_zapret)
        self.restart_action.setEnabled(False)
        self.menu.addAction(self.restart_action)
        self.menu.addSeparator()

        self.presets_menu = QMenu("Пресеты", self.menu)
        self.menu.addMenu(self.presets_menu)
        self.update_presets_menu()
        self.menu.addSeparator()

        self.telegram_proxy_menu = QMenu("Telegram proxy", self.menu)
        self.menu.addMenu(self.telegram_proxy_menu)
        self.update_telegram_proxy_menu()
        self.menu.addSeparator()

        self.check_updates_action = QAction("Проверить обновления", self.menu)
        self.check_updates_action.triggered.connect(self.manual_update_check)
        self.menu.addAction(self.check_updates_action)

        self.install_update_action = QAction("Установить обновление", self.menu)
        self.install_update_action.setEnabled(False)
        self.install_update_action.triggered.connect(self.prepare_update_install)
        self.menu.addAction(self.install_update_action)
        self.menu.addSeparator()

        self.show_window_action = QAction("Открыть главное окно", self.menu)
        self.show_window_action.triggered.connect(self.show_main_window)
        self.menu.addAction(self.show_window_action)
        self.menu.addSeparator()

        show_logs_action = QAction("Показать логи", self.menu)
        show_logs_action.triggered.connect(self.show_logs)
        self.menu.addAction(show_logs_action)

        diagnostics_action = QAction("Диагностика", self.menu)
        diagnostics_action.triggered.connect(self.show_diagnostics)
        self.menu.addAction(diagnostics_action)
        self.menu.addSeparator()

        self.autostart_action = QAction("Автозапуск", self.menu)
        self.autostart_action.setCheckable(True)
        self.autostart_action.triggered.connect(self.toggle_autostart)
        self.menu.addAction(self.autostart_action)
        self.menu.addSeparator()

        about_action = QAction("О программе", self.menu)
        about_action.triggered.connect(self.show_about)
        self.menu.addAction(about_action)

        quit_action = QAction("Выход", self.menu)
        quit_action.triggered.connect(self.quit_app)
        self.menu.addAction(quit_action)

        self.setContextMenu(self.menu)

    def update_presets_menu(self):
        """Refresh presets submenu."""
        self.presets_menu.clear()

        presets = self.preset_manager.list_presets()
        active_preset = self.preset_manager.get_active_preset()
        popular_presets = [
            "Default (Discord, YouTube, Telegram)",
            "Telegram Direct",
            "default-main",
            "Discord YouTube Telegram - Safe",
            "Discord Voice Focus",
            "YouTube Telegram Minimal",
            "CrazyMaxs",
            "Default v5",
            "ALL TCP & UDP v1",
            "Ростелеком",
        ]

        for preset_name in popular_presets:
            preset = next((item for item in presets if item.name == preset_name), None)
            if not preset:
                continue

            action = QAction(preset.name, self.presets_menu)
            action.setCheckable(True)
            if active_preset and preset.name == active_preset.name:
                action.setChecked(True)
            action.triggered.connect(lambda checked, name=preset.name: self.set_preset(name))
            self.presets_menu.addAction(action)

        self.presets_menu.addSeparator()
        all_presets_menu = self.presets_menu.addMenu("Все пресеты")

        for preset in presets:
            if preset.name in popular_presets:
                continue

            action = QAction(preset.name, all_presets_menu)
            action.setCheckable(True)
            if active_preset and preset.name == active_preset.name:
                action.setChecked(True)
            action.triggered.connect(lambda checked, name=preset.name: self.set_preset(name))
            all_presets_menu.addAction(action)

    def on_tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_zapret()

    def update_status(self):
        """Refresh tray state."""
        try:
            status = self.zapret_manager.get_status()
            running = status["running"]

            if running:
                uptime_str = f" ({status['uptime']})" if status["uptime"] else ""
                self.status_action.setText(f"● Запущен{uptime_str}")
                self.toggle_action.setText("⏹ Выключить")
                self.restart_action.setEnabled(True)
                self.setToolTip(
                    f"{Config.APP_NAME} - Запущен\nПресет: {status['preset']}"
                )
                self.set_icon_color("green")
            else:
                self.status_action.setText("✗ Остановлен")
                self.toggle_action.setText("▶ Включить")
                self.restart_action.setEnabled(False)
                self.setToolTip(f"{Config.APP_NAME} - Остановлен")
                self.set_icon_color("red")

            self.update_telegram_proxy_menu()

        except Exception as exc:
            logger.error(f"Ошибка обновления статуса: {exc}")

    def update_telegram_proxy_menu(self):
        """Refresh Telegram proxy submenu."""
        if not hasattr(self, "telegram_proxy_menu"):
            return

        self.telegram_proxy_menu.clear()
        status = self.telegram_proxy_manager.get_status()

        if status.running:
            status_text = f"Запущен: PID {status.pid}"
        elif status.installed:
            status_text = "Найден, остановлен"
        else:
            status_text = "Не найден"

        status_action = QAction(status_text, self.telegram_proxy_menu)
        status_action.setEnabled(False)
        self.telegram_proxy_menu.addAction(status_action)

        start_action = QAction(
            "Запустить локальный прокси", self.telegram_proxy_menu
        )
        start_action.setEnabled(status.installed and not status.running)
        start_action.triggered.connect(self.start_telegram_proxy)
        self.telegram_proxy_menu.addAction(start_action)

        stop_action = QAction(
            "Остановить локальный прокси", self.telegram_proxy_menu
        )
        stop_action.setEnabled(status.running)
        stop_action.triggered.connect(self.stop_telegram_proxy)
        self.telegram_proxy_menu.addAction(stop_action)

        self.telegram_proxy_menu.addSeparator()

        settings_action = QAction("Как настроить Telegram", self.telegram_proxy_menu)
        settings_action.triggered.connect(self.show_telegram_proxy_help)
        self.telegram_proxy_menu.addAction(settings_action)

    def start_telegram_proxy(self):
        """Start optional local Telegram proxy helper."""
        if self.telegram_proxy_manager.start():
            self.show_notification(
                "Telegram proxy",
                "Локальный прокси запущен. В Telegram используйте "  # noqa: E501
                "SOCKS5 127.0.0.1:1080 или 127.0.0.1:1443.",
                QSystemTrayIcon.Information,
                4000,
            )
            self.update_telegram_proxy_menu()
            return

        status = self.telegram_proxy_manager.get_status()
        QMessageBox.warning(
            None,
            "Telegram proxy",
            "Не удалось запустить локальный Telegram-прокси.\n\n"
            "Положите tgwsproxy.exe в папку tools\\telegram-proxy рядом с приложением "  # noqa: E501
            "или задайте путь через переменную ZAPRET_TELEGRAM_PROXY_EXE.\n\n"  # noqa: E501
            f"Лог: {status.log_file}",
        )
        self.update_telegram_proxy_menu()

    def stop_telegram_proxy(self):
        """Stop optional local Telegram proxy helper."""
        if self.telegram_proxy_manager.stop():
            self.update_telegram_proxy_menu()
            return

        QMessageBox.warning(
            None,
            "Telegram proxy",
            "Не удалось остановить Telegram-прокси. Проверьте процесс в диспетчере задач.",  # noqa: E501
        )
        self.update_telegram_proxy_menu()

    def show_telegram_proxy_help(self):
        """Show Telegram proxy setup instructions."""
        status = self.telegram_proxy_manager.get_status()
        exe_text = str(status.executable) if status.executable else "не найден"
        QMessageBox.information(
            None,
            "Telegram proxy",
            "1. Положите tgwsproxy.exe в tools\\telegram-proxy рядом с приложением.\n"  # noqa: E501
            "   Также можно задать полный путь в ZAPRET_TELEGRAM_PROXY_EXE.\n\n"  # noqa: E501
            "2. Запустите прокси из этого меню.\n\n"
            "3. В Telegram Desktop откройте:\n"
            "   Настройки -> Продвинутые настройки -> Тип подключения -> SOCKS5.\n\n"  # noqa: E501
            "4. Укажите адрес 127.0.0.1 и порт 1080. Если не подключается, попробуйте 1443.\n\n"  # noqa: E501
            f"Текущий исполняемый файл: {exe_text}\n"
            f"Лог запуска: {status.log_file}",
        )

    def set_icon_color(self, color: str):
        """Update tray icon color."""
        try:
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            if color == "green":
                painter.setBrush(QColor(76, 175, 80))
            elif color == "yellow":
                painter.setBrush(QColor(255, 193, 7))
            else:
                painter.setBrush(QColor(244, 67, 54))

            painter.setPen(Qt.NoPen)
            painter.drawEllipse(4, 4, 56, 56)

            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 36, QFont.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "Z")
            painter.end()

            self.setIcon(QIcon(pixmap))

        except Exception as exc:
            logger.error(f"Ошибка установки иконки: {exc}")

    def schedule_background_update_check(self):
        """Schedule a silent background update check."""
        self.start_update_check(force=False, manual=False)

    def manual_update_check(self):
        """Run a manual update check."""
        self.start_update_check(force=True, manual=True)

    def start_update_check(self, force: bool, manual: bool):
        """Start background update check thread."""
        if self.update_check_in_progress:
            if manual:
                QMessageBox.information(
                    None,
                    "Обновления",
                    "Проверка уже выполняется.",
                )
            return

        self.update_check_in_progress = True
        self.check_updates_action.setEnabled(False)
        self.check_updates_action.setText("Проверка обновлений...")

        thread = threading.Thread(
            target=self._run_update_check,
            args=(force, manual),
            daemon=True,
        )
        thread.start()

    def _run_update_check(self, force: bool, manual: bool):
        try:
            result = self.update_manager.check_for_updates(force=force)
            self.update_check_finished.emit(result, manual)
        except Exception as exc:
            logger.error(
                "Ошибка проверки обновлений: %s", exc, exc_info=True
            )
            self.update_check_failed.emit(str(exc), manual)

    def on_update_check_finished(self, result, manual: bool):
        """Handle update check completion on UI thread."""
        self.update_check_in_progress = False
        self.check_updates_action.setEnabled(True)
        self.check_updates_action.setText("Проверить обновления")

        self.available_release = result.release
        self.downloaded_update = result.downloaded_update
        self.refresh_update_actions()

        if result.update_available and result.release:
            message = f"Доступна версия {result.release.product_version}"
            logger.info(message)
            self.show_notification(
                "Доступно обновление",
                message,
                QSystemTrayIcon.Information,
                4000,
                level="info",
            )
            if manual:
                QMessageBox.information(
                    None,
                    "Обновления",
                    self._build_update_message(
                        result.release,
                        downloaded=bool(result.downloaded_update),
                    ),
                )
            return

        if manual:
            QMessageBox.information(
                None,
                "Обновления",
                "Новых обновлений не найдено.",
            )

    def on_update_check_failed(self, error_message: str, manual: bool):
        """Handle update check failure on UI thread."""
        self.update_check_in_progress = False
        self.check_updates_action.setEnabled(True)
        self.check_updates_action.setText("Проверить обновления")
        self.refresh_update_actions()

        if manual:
            QMessageBox.warning(
                None,
                "Обновления",
                f"Не удалось проверить обновления:\n{error_message}",
            )

    def prepare_update_install(self):
        """Download update if needed and launch installer helper."""
        if self.update_download_in_progress:
            QMessageBox.information(
                None,
                "Обновления",
                "Загрузка обновления уже выполняется.",
            )
            return

        downloaded = self.downloaded_update
        if downloaded is None:
            if not self.available_release:
                QMessageBox.information(
                    None,
                    "Обновления",
                    "Сначала проверьте наличие обновлений.",
                )
                return

            reply = QMessageBox.question(
                None,
                "Обновления",
                self._build_update_message(self.available_release, downloaded=False)
                + "\n\nСкачать сейчас?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply != QMessageBox.Yes:
                return

            self.start_update_download(self.available_release)
            return

        self.install_downloaded_update(downloaded)

    def start_update_download(self, release):
        """Start background update download."""
        self.update_download_in_progress = True
        self.install_update_action.setEnabled(False)
        self.install_update_action.setText("Загрузка обновления...")

        thread = threading.Thread(
            target=self._run_update_download,
            args=(release,),
            daemon=True,
        )
        thread.start()

    def _run_update_download(self, release):
        try:
            downloaded = self.update_manager.download_update(release)
            self.update_download_finished.emit(downloaded)
        except Exception as exc:
            logger.error(
                "Ошибка загрузки обновления: %s", exc, exc_info=True
            )
            self.update_download_failed.emit(str(exc))

    def on_update_download_finished(self, downloaded):
        """Handle update download completion on UI thread."""
        self.update_download_in_progress = False
        self.downloaded_update = downloaded
        self.available_release = downloaded.release
        self.refresh_update_actions()

        reply = QMessageBox.question(
            None,
            "Обновление загружено",
            self._build_update_message(downloaded.release, downloaded=True)
            + "\n\nУстановить обновление сейчас?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            self.install_downloaded_update(downloaded)

    def on_update_download_failed(self, error_message: str):
        """Handle update download failure on UI thread."""
        self.update_download_in_progress = False
        self.refresh_update_actions()
        QMessageBox.warning(
            None,
            "Обновления",
            f"Не удалось загрузить обновление:\n{error_message}",
        )

    def install_downloaded_update(self, downloaded):
        """Validate state and launch helper installer."""
        if self.zapret_manager.is_running():
            QMessageBox.warning(
                None,
                "Обновления",
                "Сначала остановите zapret перед установкой обновления.",  # noqa: E501
            )
            return

        if not Config.IS_FROZEN:
            QMessageBox.information(
                None,
                "Обновления",
                "Автоустановка доступна только в собранной EXE-версии приложения.",  # noqa: E501
            )
            return

        reply = QMessageBox.question(
            None,
            "Установить обновление",
            "Приложение будет закрыто, обновлено и запущено заново.\n\nПродолжить?",  # noqa: E501
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self.update_manager.install_update(downloaded)
        except UpdateError as exc:
            QMessageBox.critical(None, "Обновления", str(exc))
            return
        except Exception as exc:
            logger.error(
                "Ошибка запуска установки обновления: %s",
                exc,
                exc_info=True,
            )
            QMessageBox.critical(
                None,
                "Обновления",
                f"Не удалось запустить установку:\n{exc}",
            )
            return

        logger.info(
            "Запущена установка обновления %s",
            downloaded.release.product_version,
        )
        self.hide()
        QApplication.quit()

    def refresh_update_actions(self):
        """Refresh tray menu state for update actions."""
        if self.update_check_in_progress:
            self.check_updates_action.setEnabled(False)
            self.check_updates_action.setText("Проверка обновлений...")
        else:
            self.check_updates_action.setEnabled(True)
            self.check_updates_action.setText("Проверить обновления")

        if self.update_download_in_progress:
            self.install_update_action.setEnabled(False)
            self.install_update_action.setText("Загрузка обновления...")
            return

        if self.downloaded_update:
            version = self.downloaded_update.release.product_version
            self.install_update_action.setEnabled(True)
            self.install_update_action.setText(
                f"Установить обновление {version}"
            )
            return

        if self.available_release:
            version = self.available_release.product_version
            self.install_update_action.setEnabled(True)
            self.install_update_action.setText(f"Скачать обновление {version}")
            return

        self.install_update_action.setEnabled(False)
        self.install_update_action.setText("Установить обновление")

    def _build_update_message(self, release, downloaded: bool) -> str:
        release_notes = (
            release.release_notes.strip()
            or "Описание обновления отсутствует."
        )
        prefix = (
            "Обновление уже загружено."
            if downloaded
            else "Доступно обновление."
        )
        return (
            f"{prefix}\n\n"
            f"Версия: {release.product_version}\n"
            f"Канал: {release.channel}\n"
            f"Источник: {release.source_endpoint}\n\n"
            f"{release_notes}"
        )

    def toggle_zapret(self):
        """Toggle zapret state."""
        try:
            if self.zapret_manager.is_running():
                self.stop_zapret()
            else:
                self.start_zapret()
        except Exception as exc:
            QMessageBox.critical(
                None,
                "Ошибка",
                f"Ошибка переключения:\n{exc}",
            )

    def start_zapret(self):
        """Start zapret."""
        try:
            logger.info("Запуск zapret через трей")

            if not Config.ACTIVE_PRESET.exists():
                QMessageBox.warning(
                    None,
                    "Пресет не выбран",
                    "Сначала выберите пресет из меню 'Пресеты'",
                )
                return

            if self.zapret_manager.start():
                QTimer.singleShot(2000, self.update_status)
                return

            log_file = Path(tempfile.gettempdir()) / "ZapretManager" / "winws2.log"
            error_msg = "Не удалось запустить zapret.\n\n"

            if log_file.exists():
                try:
                    log_content = log_file.read_text(encoding="utf-8", errors="ignore")
                    if log_content.strip():
                        error_msg += f"Вывод winws2.exe:\n{log_content[:500]}\n\n"
                except OSError:
                    pass

            error_msg += "Возможные причины:\n"
            error_msg += "• Отсутствуют права администратора\n"
            error_msg += "• Неверный пресет или отсутствуют файлы списков\n"  # noqa: E501
            error_msg += "• Конфликт с другими программами (VPN, антивирус)\n\n"  # noqa: E501
            error_msg += "Проверьте логи: Меню → Показать логи"

            QMessageBox.critical(None, "Ошибка запуска", error_msg)

        except Exception as exc:
            logger.error(f"Ошибка запуска: {exc}", exc_info=True)
            QMessageBox.critical(
                None,
                "Ошибка",
                f"Не удалось запустить:\n{exc}",
            )

    def stop_zapret(self):
        """Stop zapret."""
        try:
            logger.info("Остановка zapret через трей")

            if self.zapret_manager.stop():
                QTimer.singleShot(500, self.update_status)
            else:
                QMessageBox.warning(
                    None,
                    "Предупреждение",
                    "Не удалось остановить zapret.\n\nПопробуйте еще раз.",  # noqa: E501
                )

        except Exception as exc:
            logger.error(f"Ошибка остановки: {exc}", exc_info=True)
            QMessageBox.critical(
                None,
                "Ошибка",
                f"Не удалось остановить:\n{exc}",
            )

    def restart_zapret(self):
        """Restart zapret."""
        try:
            logger.info("Перезапуск zapret через трей")

            if self.zapret_manager.restart():
                QTimer.singleShot(2000, self.update_status)
            else:
                QMessageBox.critical(
                    None,
                    "Ошибка",
                    "Не удалось перезапустить zapret.",
                )

        except Exception as exc:
            logger.error(f"Ошибка перезапуска: {exc}", exc_info=True)
            QMessageBox.critical(
                None,
                "Ошибка",
                f"Не удалось перезапустить:\n{exc}",
            )

    def set_preset(self, preset_name: str):
        """Set active preset."""
        try:
            logger.info(f"Установка пресета: {preset_name}")

            if not self.preset_manager.set_active_preset(preset_name):
                QMessageBox.critical(
                    None,
                    "Ошибка",
                    f"Не удалось установить пресет '{preset_name}'",
                )
                return

            self.show_notification(
                "Пресет изменен",
                f"Установлен: {preset_name}",
                QSystemTrayIcon.Information,
                2000,
            )
            self.update_presets_menu()

            if self.zapret_manager.is_running():
                reply = QMessageBox.question(
                    None,
                    "Перезапустить?",
                    f"Пресет изменен на '{preset_name}'.\n\n"
                    "Перезапустить zapret с новым пресетом?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if reply == QMessageBox.Yes:
                    self.restart_zapret()

        except Exception as exc:
            logger.error(f"Ошибка установки пресета: {exc}", exc_info=True)
            QMessageBox.critical(
                None,
                "Ошибка",
                f"Не удалось установить пресет:\n{exc}",
            )

    def check_autostart(self):
        """Refresh autostart checkbox state."""
        try:
            self.autostart_action.setChecked(self.autostart_manager.is_enabled())
        except Exception as exc:
            logger.error(f"Ошибка проверки автозапуска: {exc}")

    def toggle_autostart(self):
        """Toggle autostart state."""
        try:
            if self.autostart_action.isChecked():
                if self.autostart_manager.enable():
                    self.show_notification(
                        "Автозапуск",
                        "Включен",
                        QSystemTrayIcon.Information,
                        2000,
                    )
                else:
                    QMessageBox.critical(
                        None,
                        "Ошибка",
                        "Не удалось включить автозапуск",
                    )
                    self.autostart_action.setChecked(False)
            else:
                if self.autostart_manager.disable():
                    self.show_notification(
                        "Автозапуск",
                        "Выключен",
                        QSystemTrayIcon.Information,
                        2000,
                    )
                else:
                    QMessageBox.critical(
                        None,
                        "Ошибка",
                        "Не удалось выключить автозапуск",
                    )
                    self.autostart_action.setChecked(True)

        except Exception as exc:
            logger.error(
                f"Ошибка переключения автозапуска: {exc}",
                exc_info=True,
            )
            QMessageBox.critical(
                None,
                "Ошибка",
                f"Не удалось изменить автозапуск:\n{exc}",
            )
            self.check_autostart()

    def show_main_window(self):
        """Placeholder for main window."""
        QMessageBox.information(
            None,
            "В разработке",
            "Главное окно будет доступно в следующей версии.\n\n"  # noqa: E501
            "Пока используйте меню системного трея для управления.",  # noqa: E501
        )

    def show_logs(self):
        """Open application logs."""
        try:
            log_file = Path(tempfile.gettempdir()) / "ZapretManager" / "app.log"

            if not log_file.exists():
                QMessageBox.warning(
                    None,
                    "Логи не найдены",
                    f"Файл логов не найден:\n{log_file}",
                )
                return

            subprocess.Popen(["notepad.exe", str(log_file)])

        except Exception as exc:
            logger.error(f"Ошибка открытия логов: {exc}", exc_info=True)
            QMessageBox.critical(
                None,
                "Ошибка",
                f"Не удалось открыть логи:\n{exc}",
            )

    def show_diagnostics(self):
        """Show current system diagnostics."""
        try:
            from core.privileges import PrivilegesManager

            info = []
            info.append("=== Диагностика Zapret Manager ===\n")

            is_admin = PrivilegesManager.is_admin()
            admin_status = "✓ Да" if is_admin else "✗ НЕТ (ТРЕБУЕТСЯ!)"
            info.append(f"Права администратора: {admin_status}")

            status = self.zapret_manager.get_status()
            zapret_status = (
                "✓ Запущен" if status["running"] else "✗ Остановлен"
            )
            info.append(f"Статус zapret: {zapret_status}")
            if status["running"]:
                info.append(f"  PID: {status['pid']}")
                info.append(f"  Uptime: {status['uptime']}")

            info.append(f"Активный пресет: {status['preset']}")
            info.append(f"\nБазовая директория: {Config.BASE_DIR}")
            mode = "EXE (frozen)" if Config.IS_FROZEN else "Python скрипт"
            info.append(f"Режим: {mode}")
            info.append(f"Версия продукта: {Config.PRODUCT_VERSION}")

            winws_exists = "✓" if Config.WINWS2_EXE.exists() else "✗ НЕ НАЙДЕН"
            info.append(f"winws2.exe: {winws_exists} {Config.WINWS2_EXE}")

            log_file = Path(tempfile.gettempdir()) / "ZapretManager" / "app.log"
            info.append(f"\nЛоги приложения: {log_file}")
            info.append(f"  Существует: {'✓' if log_file.exists() else '✗'}")

            winws2_log = Path(tempfile.gettempdir()) / "ZapretManager" / "winws2.log"
            info.append(f"Логи winws2.exe: {winws2_log}")
            info.append(f"  Существует: {'✓' if winws2_log.exists() else '✗'}")

            info.append(
                f"\nПуть состояния обновлений: {Config.UPDATE_STATE_FILE}"
            )
            info.append(
                f"Каталог загрузок обновлений: {Config.UPDATE_DOWNLOAD_DIR}"  # noqa: E501
            )

            info.append("\n=== Запущенные процессы ===")
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq winws2.exe", "/NH"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5,
                )
                if "winws2.exe" in result.stdout:
                    info.append("✓ winws2.exe запущен")
                else:
                    info.append("✗ winws2.exe не запущен")
            except Exception:
                info.append("? Не удалось проверить")

            QMessageBox.information(None, "Диагностика", "\n".join(info))

        except Exception as exc:
            logger.error(f"Ошибка диагностики: {exc}", exc_info=True)
            QMessageBox.critical(
                None,
                "Ошибка",
                f"Не удалось выполнить диагностику:\n{exc}",
            )

    def show_about(self):
        """Show About dialog."""
        QMessageBox.about(
            None,
            "О программе",
            f"<h3>{Config.APP_NAME}</h3>"
            f"<p>Версия {Config.VERSION}</p>"
            f"<p>Полноценное управление zapret2 через удобный GUI</p>"  # noqa: E501
            f"<p><b>Возможности:</b></p>"
            f"<ul>"
            f"<li>Управление через системный трей</li>"
            f"<li>70+ готовых пресетов</li>"
            f"<li>Автозапуск с Windows</li>"
            f"<li>Автообновление через artifact/update server</li>"
            f"<li>Диагностика и исправление проблем</li>"
            f"</ul>"
            f"<p><b>Благодарности:</b></p>"
            f"<p>zapret2, WinDivert, PyQt5</p>",
        )

    def quit_app(self):
        """Quit tray application."""
        reply = QMessageBox.question(
            None,
            "Выход",
            "Выйти из приложения?\n\nZapret продолжит работать в фоне.",  # noqa: E501
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            logger.info("Выход из приложения")
            self.hide()
            QApplication.quit()
