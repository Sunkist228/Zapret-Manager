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

        self.status_action = QAction("РЎС‚Р°С‚СѓСЃ: РїСЂРѕРІРµСЂРєР°...", self.menu)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)
        self.menu.addSeparator()

        self.toggle_action = QAction("в–¶ Р’РєР»СЋС‡РёС‚СЊ", self.menu)
        self.toggle_action.triggered.connect(self.toggle_zapret)
        self.menu.addAction(self.toggle_action)

        self.restart_action = QAction("РџРµСЂРµР·Р°РїСѓСЃС‚РёС‚СЊ", self.menu)
        self.restart_action.triggered.connect(self.restart_zapret)
        self.restart_action.setEnabled(False)
        self.menu.addAction(self.restart_action)
        self.menu.addSeparator()

        self.presets_menu = QMenu("РџСЂРµСЃРµС‚С‹", self.menu)
        self.menu.addMenu(self.presets_menu)
        self.update_presets_menu()
        self.menu.addSeparator()

        self.telegram_proxy_menu = QMenu("Telegram proxy", self.menu)
        self.menu.addMenu(self.telegram_proxy_menu)
        self.update_telegram_proxy_menu()
        self.menu.addSeparator()

        self.check_updates_action = QAction("РџСЂРѕРІРµСЂРёС‚СЊ РѕР±РЅРѕРІР»РµРЅРёСЏ", self.menu)
        self.check_updates_action.triggered.connect(self.manual_update_check)
        self.menu.addAction(self.check_updates_action)

        self.install_update_action = QAction("РЈСЃС‚Р°РЅРѕРІРёС‚СЊ РѕР±РЅРѕРІР»РµРЅРёРµ", self.menu)
        self.install_update_action.setEnabled(False)
        self.install_update_action.triggered.connect(self.prepare_update_install)
        self.menu.addAction(self.install_update_action)
        self.menu.addSeparator()

        self.show_window_action = QAction("РћС‚РєСЂС‹С‚СЊ РіР»Р°РІРЅРѕРµ РѕРєРЅРѕ", self.menu)
        self.show_window_action.triggered.connect(self.show_main_window)
        self.menu.addAction(self.show_window_action)
        self.menu.addSeparator()

        show_logs_action = QAction("РџРѕРєР°Р·Р°С‚СЊ Р»РѕРіРё", self.menu)
        show_logs_action.triggered.connect(self.show_logs)
        self.menu.addAction(show_logs_action)

        diagnostics_action = QAction("Р”РёР°РіРЅРѕСЃС‚РёРєР°", self.menu)
        diagnostics_action.triggered.connect(self.show_diagnostics)
        self.menu.addAction(diagnostics_action)
        self.menu.addSeparator()

        self.autostart_action = QAction("РђРІС‚РѕР·Р°РїСѓСЃРє", self.menu)
        self.autostart_action.setCheckable(True)
        self.autostart_action.triggered.connect(self.toggle_autostart)
        self.menu.addAction(self.autostart_action)
        self.menu.addSeparator()

        about_action = QAction("Рћ РїСЂРѕРіСЂР°РјРјРµ", self.menu)
        about_action.triggered.connect(self.show_about)
        self.menu.addAction(about_action)

        quit_action = QAction("Р’С‹С…РѕРґ", self.menu)
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
            "Р РѕСЃС‚РµР»РµРєРѕРј",
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
        all_presets_menu = self.presets_menu.addMenu("Р’СЃРµ РїСЂРµСЃРµС‚С‹")

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
                self.status_action.setText(f"в—Џ Р—Р°РїСѓС‰РµРЅ{uptime_str}")
                self.toggle_action.setText("вЏ№ Р’С‹РєР»СЋС‡РёС‚СЊ")
                self.restart_action.setEnabled(True)
                self.setToolTip(
                    f"{Config.APP_NAME} - Р—Р°РїСѓС‰РµРЅ\nРџСЂРµСЃРµС‚: {status['preset']}"
                )
                self.set_icon_color("green")
            else:
                self.status_action.setText("вњ— РћСЃС‚Р°РЅРѕРІР»РµРЅ")
                self.toggle_action.setText("в–¶ Р’РєР»СЋС‡РёС‚СЊ")
                self.restart_action.setEnabled(False)
                self.setToolTip(f"{Config.APP_NAME} - РћСЃС‚Р°РЅРѕРІР»РµРЅ")
                self.set_icon_color("red")

            self.update_telegram_proxy_menu()

        except Exception as exc:
            logger.error(f"РћС€РёР±РєР° РѕР±РЅРѕРІР»РµРЅРёСЏ СЃС‚Р°С‚СѓСЃР°: {exc}")

    def update_telegram_proxy_menu(self):
        """Refresh Telegram proxy submenu."""
        if not hasattr(self, "telegram_proxy_menu"):
            return

        self.telegram_proxy_menu.clear()
        status = self.telegram_proxy_manager.get_status()

        if status.running:
            status_text = f"Р—Р°РїСѓС‰РµРЅ: PID {status.pid}"
        elif status.installed:
            status_text = "РќР°Р№РґРµРЅ, РѕСЃС‚Р°РЅРѕРІР»РµРЅ"
        else:
            status_text = "РќРµ РЅР°Р№РґРµРЅ"

        status_action = QAction(status_text, self.telegram_proxy_menu)
        status_action.setEnabled(False)
        self.telegram_proxy_menu.addAction(status_action)

        start_action = QAction(
            "Р—Р°РїСѓСЃС‚РёС‚СЊ Р»РѕРєР°Р»СЊРЅС‹Р№ РїСЂРѕРєСЃРё", self.telegram_proxy_menu
        )
        start_action.setEnabled(status.installed and not status.running)
        start_action.triggered.connect(self.start_telegram_proxy)
        self.telegram_proxy_menu.addAction(start_action)

        stop_action = QAction(
            "РћСЃС‚Р°РЅРѕРІРёС‚СЊ Р»РѕРєР°Р»СЊРЅС‹Р№ РїСЂРѕРєСЃРё", self.telegram_proxy_menu
        )
        stop_action.setEnabled(status.running)
        stop_action.triggered.connect(self.stop_telegram_proxy)
        self.telegram_proxy_menu.addAction(stop_action)

        self.telegram_proxy_menu.addSeparator()

        settings_action = QAction("РљР°Рє РЅР°СЃС‚СЂРѕРёС‚СЊ Telegram", self.telegram_proxy_menu)
        settings_action.triggered.connect(self.show_telegram_proxy_help)
        self.telegram_proxy_menu.addAction(settings_action)

    def start_telegram_proxy(self):
        """Start optional local Telegram proxy helper."""
        if self.telegram_proxy_manager.start():
            self.show_notification(
                "Telegram proxy",
                "Р›РѕРєР°Р»СЊРЅС‹Р№ РїСЂРѕРєСЃРё Р·Р°РїСѓС‰РµРЅ. Р’ Telegram РёСЃРїРѕР»СЊР·СѓР№С‚Рµ "  # noqa: E501
                "SOCKS5 127.0.0.1:1080 РёР»Рё 127.0.0.1:1443.",
                QSystemTrayIcon.Information,
                4000,
            )
            self.update_telegram_proxy_menu()
            return

        status = self.telegram_proxy_manager.get_status()
        QMessageBox.warning(
            None,
            "Telegram proxy",
            "РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РїСѓСЃС‚РёС‚СЊ Р»РѕРєР°Р»СЊРЅС‹Р№ Telegram-РїСЂРѕРєСЃРё.\n\n"
            "РџРѕР»РѕР¶РёС‚Рµ tgwsproxy.exe РІ РїР°РїРєСѓ tools\\telegram-proxy СЂСЏРґРѕРј СЃ РїСЂРёР»РѕР¶РµРЅРёРµРј "  # noqa: E501
            "РёР»Рё Р·Р°РґР°Р№С‚Рµ РїСѓС‚СЊ С‡РµСЂРµР· РїРµСЂРµРјРµРЅРЅСѓСЋ ZAPRET_TELEGRAM_PROXY_EXE.\n\n"  # noqa: E501
            f"Р›РѕРі: {status.log_file}",
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
            "РќРµ СѓРґР°Р»РѕСЃСЊ РѕСЃС‚Р°РЅРѕРІРёС‚СЊ Telegram-РїСЂРѕРєСЃРё. РџСЂРѕРІРµСЂСЊС‚Рµ РїСЂРѕС†РµСЃСЃ РІ РґРёСЃРїРµС‚С‡РµСЂРµ Р·Р°РґР°С‡.",  # noqa: E501
        )
        self.update_telegram_proxy_menu()

    def show_telegram_proxy_help(self):
        """Show Telegram proxy setup instructions."""
        status = self.telegram_proxy_manager.get_status()
        exe_text = str(status.executable) if status.executable else "РЅРµ РЅР°Р№РґРµРЅ"
        QMessageBox.information(
            None,
            "Telegram proxy",
            "1. РџРѕР»РѕР¶РёС‚Рµ tgwsproxy.exe РІ tools\\telegram-proxy СЂСЏРґРѕРј СЃ РїСЂРёР»РѕР¶РµРЅРёРµРј.\n"  # noqa: E501
            "   РўР°РєР¶Рµ РјРѕР¶РЅРѕ Р·Р°РґР°С‚СЊ РїРѕР»РЅС‹Р№ РїСѓС‚СЊ РІ ZAPRET_TELEGRAM_PROXY_EXE.\n\n"  # noqa: E501
            "2. Р—Р°РїСѓСЃС‚РёС‚Рµ РїСЂРѕРєСЃРё РёР· СЌС‚РѕРіРѕ РјРµРЅСЋ.\n\n"
            "3. Р’ Telegram Desktop РѕС‚РєСЂРѕР№С‚Рµ:\n"
            "   РќР°СЃС‚СЂРѕР№РєРё -> РџСЂРѕРґРІРёРЅСѓС‚С‹Рµ РЅР°СЃС‚СЂРѕР№РєРё -> РўРёРї РїРѕРґРєР»СЋС‡РµРЅРёСЏ -> SOCKS5.\n\n"  # noqa: E501
            "4. РЈРєР°Р¶РёС‚Рµ Р°РґСЂРµСЃ 127.0.0.1 Рё РїРѕСЂС‚ 1080. Р•СЃР»Рё РЅРµ РїРѕРґРєР»СЋС‡Р°РµС‚СЃСЏ, РїРѕРїСЂРѕР±СѓР№С‚Рµ 1443.\n\n"  # noqa: E501
            f"РўРµРєСѓС‰РёР№ РёСЃРїРѕР»РЅСЏРµРјС‹Р№ С„Р°Р№Р»: {exe_text}\n"
            f"Р›РѕРі Р·Р°РїСѓСЃРєР°: {status.log_file}",
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
            logger.error(f"РћС€РёР±РєР° СѓСЃС‚Р°РЅРѕРІРєРё РёРєРѕРЅРєРё: {exc}")

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
                    "РћР±РЅРѕРІР»РµРЅРёСЏ",
                    "РџСЂРѕРІРµСЂРєР° СѓР¶Рµ РІС‹РїРѕР»РЅСЏРµС‚СЃСЏ.",
                )
            return

        self.update_check_in_progress = True
        self.check_updates_action.setEnabled(False)
        self.check_updates_action.setText("РџСЂРѕРІРµСЂРєР° РѕР±РЅРѕРІР»РµРЅРёР№...")

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
                "РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё РѕР±РЅРѕРІР»РµРЅРёР№: %s", exc, exc_info=True
            )
            self.update_check_failed.emit(str(exc), manual)

    def on_update_check_finished(self, result, manual: bool):
        """Handle update check completion on UI thread."""
        self.update_check_in_progress = False
        self.check_updates_action.setEnabled(True)
        self.check_updates_action.setText("РџСЂРѕРІРµСЂРёС‚СЊ РѕР±РЅРѕРІР»РµРЅРёСЏ")

        self.available_release = result.release
        self.downloaded_update = result.downloaded_update
        self.refresh_update_actions()

        if result.update_available and result.release:
            message = f"Р”РѕСЃС‚СѓРїРЅР° РІРµСЂСЃРёСЏ {result.release.product_version}"
            logger.info(message)
            self.show_notification(
                "Р”РѕСЃС‚СѓРїРЅРѕ РѕР±РЅРѕРІР»РµРЅРёРµ",
                message,
                QSystemTrayIcon.Information,
                4000,
                level="info",
            )
            if manual:
                QMessageBox.information(
                    None,
                    "РћР±РЅРѕРІР»РµРЅРёСЏ",
                    self._build_update_message(
                        result.release,
                        downloaded=bool(result.downloaded_update),
                    ),
                )
            return

        if manual:
            QMessageBox.information(
                None,
                "РћР±РЅРѕРІР»РµРЅРёСЏ",
                "РќРѕРІС‹С… РѕР±РЅРѕРІР»РµРЅРёР№ РЅРµ РЅР°Р№РґРµРЅРѕ.",
            )

    def on_update_check_failed(self, error_message: str, manual: bool):
        """Handle update check failure on UI thread."""
        self.update_check_in_progress = False
        self.check_updates_action.setEnabled(True)
        self.check_updates_action.setText("РџСЂРѕРІРµСЂРёС‚СЊ РѕР±РЅРѕРІР»РµРЅРёСЏ")
        self.refresh_update_actions()

        if manual:
            QMessageBox.warning(
                None,
                "РћР±РЅРѕРІР»РµРЅРёСЏ",
                f"РќРµ СѓРґР°Р»РѕСЃСЊ РїСЂРѕРІРµСЂРёС‚СЊ РѕР±РЅРѕРІР»РµРЅРёСЏ:\n{error_message}",
            )

    def prepare_update_install(self):
        """Download update if needed and launch installer helper."""
        if self.update_download_in_progress:
            QMessageBox.information(
                None,
                "РћР±РЅРѕРІР»РµРЅРёСЏ",
                "Р—Р°РіСЂСѓР·РєР° РѕР±РЅРѕРІР»РµРЅРёСЏ СѓР¶Рµ РІС‹РїРѕР»РЅСЏРµС‚СЃСЏ.",
            )
            return

        downloaded = self.downloaded_update
        if downloaded is None:
            if not self.available_release:
                QMessageBox.information(
                    None,
                    "РћР±РЅРѕРІР»РµРЅРёСЏ",
                    "РЎРЅР°С‡Р°Р»Р° РїСЂРѕРІРµСЂСЊС‚Рµ РЅР°Р»РёС‡РёРµ РѕР±РЅРѕРІР»РµРЅРёР№.",
                )
                return

            reply = QMessageBox.question(
                None,
                "РћР±РЅРѕРІР»РµРЅРёСЏ",
                self._build_update_message(self.available_release, downloaded=False)
                + "\n\nРЎРєР°С‡Р°С‚СЊ СЃРµР№С‡Р°СЃ?",
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
        self.install_update_action.setText("Р—Р°РіСЂСѓР·РєР° РѕР±РЅРѕРІР»РµРЅРёСЏ...")

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
                "РћС€РёР±РєР° Р·Р°РіСЂСѓР·РєРё РѕР±РЅРѕРІР»РµРЅРёСЏ: %s", exc, exc_info=True
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
            "РћР±РЅРѕРІР»РµРЅРёРµ Р·Р°РіСЂСѓР¶РµРЅРѕ",
            self._build_update_message(downloaded.release, downloaded=True)
            + "\n\nРЈСЃС‚Р°РЅРѕРІРёС‚СЊ РѕР±РЅРѕРІР»РµРЅРёРµ СЃРµР№С‡Р°СЃ?",
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
            "РћР±РЅРѕРІР»РµРЅРёСЏ",
            f"РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ РѕР±РЅРѕРІР»РµРЅРёРµ:\n{error_message}",
        )

    def install_downloaded_update(self, downloaded):
        """Validate state and launch helper installer."""
        if self.zapret_manager.is_running():
            QMessageBox.warning(
                None,
                "РћР±РЅРѕРІР»РµРЅРёСЏ",
                "РЎРЅР°С‡Р°Р»Р° РѕСЃС‚Р°РЅРѕРІРёС‚Рµ zapret РїРµСЂРµРґ СѓСЃС‚Р°РЅРѕРІРєРѕР№ РѕР±РЅРѕРІР»РµРЅРёСЏ.",  # noqa: E501
            )
            return

        if not Config.IS_FROZEN:
            QMessageBox.information(
                None,
                "РћР±РЅРѕРІР»РµРЅРёСЏ",
                "РђРІС‚РѕСѓСЃС‚Р°РЅРѕРІРєР° РґРѕСЃС‚СѓРїРЅР° С‚РѕР»СЊРєРѕ РІ СЃРѕР±СЂР°РЅРЅРѕР№ EXE-РІРµСЂСЃРёРё РїСЂРёР»РѕР¶РµРЅРёСЏ.",  # noqa: E501
            )
            return

        reply = QMessageBox.question(
            None,
            "РЈСЃС‚Р°РЅРѕРІРёС‚СЊ РѕР±РЅРѕРІР»РµРЅРёРµ",
            "РџСЂРёР»РѕР¶РµРЅРёРµ Р±СѓРґРµС‚ Р·Р°РєСЂС‹С‚Рѕ, РѕР±РЅРѕРІР»РµРЅРѕ Рё Р·Р°РїСѓС‰РµРЅРѕ Р·Р°РЅРѕРІРѕ.\n\nРџСЂРѕРґРѕР»Р¶РёС‚СЊ?",  # noqa: E501
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self.update_manager.install_update(downloaded)
        except UpdateError as exc:
            QMessageBox.critical(None, "РћР±РЅРѕРІР»РµРЅРёСЏ", str(exc))
            return
        except Exception as exc:
            logger.error(
                "РћС€РёР±РєР° Р·Р°РїСѓСЃРєР° СѓСЃС‚Р°РЅРѕРІРєРё РѕР±РЅРѕРІР»РµРЅРёСЏ: %s",
                exc,
                exc_info=True,
            )
            QMessageBox.critical(
                None,
                "РћР±РЅРѕРІР»РµРЅРёСЏ",
                f"РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РїСѓСЃС‚РёС‚СЊ СѓСЃС‚Р°РЅРѕРІРєСѓ:\n{exc}",
            )
            return

        logger.info(
            "Р—Р°РїСѓС‰РµРЅР° СѓСЃС‚Р°РЅРѕРІРєР° РѕР±РЅРѕРІР»РµРЅРёСЏ %s",
            downloaded.release.product_version,
        )
        self.hide()
        QApplication.quit()

    def refresh_update_actions(self):
        """Refresh tray menu state for update actions."""
        if self.update_check_in_progress:
            self.check_updates_action.setEnabled(False)
            self.check_updates_action.setText("РџСЂРѕРІРµСЂРєР° РѕР±РЅРѕРІР»РµРЅРёР№...")
        else:
            self.check_updates_action.setEnabled(True)
            self.check_updates_action.setText("РџСЂРѕРІРµСЂРёС‚СЊ РѕР±РЅРѕРІР»РµРЅРёСЏ")

        if self.update_download_in_progress:
            self.install_update_action.setEnabled(False)
            self.install_update_action.setText("Р—Р°РіСЂСѓР·РєР° РѕР±РЅРѕРІР»РµРЅРёСЏ...")
            return

        if self.downloaded_update:
            version = self.downloaded_update.release.product_version
            self.install_update_action.setEnabled(True)
            self.install_update_action.setText(
                f"РЈСЃС‚Р°РЅРѕРІРёС‚СЊ РѕР±РЅРѕРІР»РµРЅРёРµ {version}"
            )
            return

        if self.available_release:
            version = self.available_release.product_version
            self.install_update_action.setEnabled(True)
            self.install_update_action.setText(f"РЎРєР°С‡Р°С‚СЊ РѕР±РЅРѕРІР»РµРЅРёРµ {version}")
            return

        self.install_update_action.setEnabled(False)
        self.install_update_action.setText("РЈСЃС‚Р°РЅРѕРІРёС‚СЊ РѕР±РЅРѕРІР»РµРЅРёРµ")

    def _build_update_message(self, release, downloaded: bool) -> str:
        release_notes = (
            release.release_notes.strip()
            or "РћРїРёСЃР°РЅРёРµ РѕР±РЅРѕРІР»РµРЅРёСЏ РѕС‚СЃСѓС‚СЃС‚РІСѓРµС‚."
        )
        prefix = (
            "РћР±РЅРѕРІР»РµРЅРёРµ СѓР¶Рµ Р·Р°РіСЂСѓР¶РµРЅРѕ."
            if downloaded
            else "Р”РѕСЃС‚СѓРїРЅРѕ РѕР±РЅРѕРІР»РµРЅРёРµ."
        )
        return (
            f"{prefix}\n\n"
            f"Р’РµСЂСЃРёСЏ: {release.product_version}\n"
            f"РљР°РЅР°Р»: {release.channel}\n"
            f"РСЃС‚РѕС‡РЅРёРє: {release.source_endpoint}\n\n"
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
                "РћС€РёР±РєР°",
                f"РћС€РёР±РєР° РїРµСЂРµРєР»СЋС‡РµРЅРёСЏ:\n{exc}",
            )

    def start_zapret(self):
        """Start zapret."""
        try:
            logger.info("Р—Р°РїСѓСЃРє zapret С‡РµСЂРµР· С‚СЂРµР№")

            if not Config.ACTIVE_PRESET.exists():
                QMessageBox.warning(
                    None,
                    "РџСЂРµСЃРµС‚ РЅРµ РІС‹Р±СЂР°РЅ",
                    "РЎРЅР°С‡Р°Р»Р° РІС‹Р±РµСЂРёС‚Рµ РїСЂРµСЃРµС‚ РёР· РјРµРЅСЋ 'РџСЂРµСЃРµС‚С‹'",
                )
                return

            if self.zapret_manager.start():
                QTimer.singleShot(2000, self.update_status)
                return

            log_file = Path(tempfile.gettempdir()) / "ZapretManager" / "winws2.log"
            error_msg = "РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РїСѓСЃС‚РёС‚СЊ zapret.\n\n"

            if log_file.exists():
                try:
                    log_content = log_file.read_text(encoding="utf-8", errors="ignore")
                    if log_content.strip():
                        error_msg += f"Р’С‹РІРѕРґ winws2.exe:\n{log_content[:500]}\n\n"
                except OSError:
                    pass

            error_msg += "Р’РѕР·РјРѕР¶РЅС‹Рµ РїСЂРёС‡РёРЅС‹:\n"
            error_msg += "вЂў РћС‚СЃСѓС‚СЃС‚РІСѓСЋС‚ РїСЂР°РІР° Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂР°\n"
            error_msg += "вЂў РќРµРІРµСЂРЅС‹Р№ РїСЂРµСЃРµС‚ РёР»Рё РѕС‚СЃСѓС‚СЃС‚РІСѓСЋС‚ С„Р°Р№Р»С‹ СЃРїРёСЃРєРѕРІ\n"  # noqa: E501
            error_msg += "вЂў РљРѕРЅС„Р»РёРєС‚ СЃ РґСЂСѓРіРёРјРё РїСЂРѕРіСЂР°РјРјР°РјРё (VPN, Р°РЅС‚РёРІРёСЂСѓСЃ)\n\n"  # noqa: E501
            error_msg += "РџСЂРѕРІРµСЂСЊС‚Рµ Р»РѕРіРё: РњРµРЅСЋ в†’ РџРѕРєР°Р·Р°С‚СЊ Р»РѕРіРё"

            QMessageBox.critical(None, "РћС€РёР±РєР° Р·Р°РїСѓСЃРєР°", error_msg)

        except Exception as exc:
            logger.error(f"РћС€РёР±РєР° Р·Р°РїСѓСЃРєР°: {exc}", exc_info=True)
            QMessageBox.critical(
                None,
                "РћС€РёР±РєР°",
                f"РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РїСѓСЃС‚РёС‚СЊ:\n{exc}",
            )

    def stop_zapret(self):
        """Stop zapret."""
        try:
            logger.info("РћСЃС‚Р°РЅРѕРІРєР° zapret С‡РµСЂРµР· С‚СЂРµР№")

            if self.zapret_manager.stop():
                QTimer.singleShot(500, self.update_status)
            else:
                QMessageBox.warning(
                    None,
                    "РџСЂРµРґСѓРїСЂРµР¶РґРµРЅРёРµ",
                    "РќРµ СѓРґР°Р»РѕСЃСЊ РѕСЃС‚Р°РЅРѕРІРёС‚СЊ zapret.\n\nРџРѕРїСЂРѕР±СѓР№С‚Рµ РµС‰Рµ СЂР°Р·.",  # noqa: E501
                )

        except Exception as exc:
            logger.error(f"РћС€РёР±РєР° РѕСЃС‚Р°РЅРѕРІРєРё: {exc}", exc_info=True)
            QMessageBox.critical(
                None,
                "РћС€РёР±РєР°",
                f"РќРµ СѓРґР°Р»РѕСЃСЊ РѕСЃС‚Р°РЅРѕРІРёС‚СЊ:\n{exc}",
            )

    def restart_zapret(self):
        """Restart zapret."""
        try:
            logger.info("РџРµСЂРµР·Р°РїСѓСЃРє zapret С‡РµСЂРµР· С‚СЂРµР№")

            if self.zapret_manager.restart():
                QTimer.singleShot(2000, self.update_status)
            else:
                QMessageBox.critical(
                    None,
                    "РћС€РёР±РєР°",
                    "РќРµ СѓРґР°Р»РѕСЃСЊ РїРµСЂРµР·Р°РїСѓСЃС‚РёС‚СЊ zapret.",
                )

        except Exception as exc:
            logger.error(f"РћС€РёР±РєР° РїРµСЂРµР·Р°РїСѓСЃРєР°: {exc}", exc_info=True)
            QMessageBox.critical(
                None,
                "РћС€РёР±РєР°",
                f"РќРµ СѓРґР°Р»РѕСЃСЊ РїРµСЂРµР·Р°РїСѓСЃС‚РёС‚СЊ:\n{exc}",
            )

    def set_preset(self, preset_name: str):
        """Set active preset."""
        try:
            logger.info(f"РЈСЃС‚Р°РЅРѕРІРєР° РїСЂРµСЃРµС‚Р°: {preset_name}")

            if not self.preset_manager.set_active_preset(preset_name):
                QMessageBox.critical(
                    None,
                    "РћС€РёР±РєР°",
                    f"РќРµ СѓРґР°Р»РѕСЃСЊ СѓСЃС‚Р°РЅРѕРІРёС‚СЊ РїСЂРµСЃРµС‚ '{preset_name}'",
                )
                return

            self.show_notification(
                "РџСЂРµСЃРµС‚ РёР·РјРµРЅРµРЅ",
                f"РЈСЃС‚Р°РЅРѕРІР»РµРЅ: {preset_name}",
                QSystemTrayIcon.Information,
                2000,
            )
            self.update_presets_menu()

            if self.zapret_manager.is_running():
                reply = QMessageBox.question(
                    None,
                    "РџРµСЂРµР·Р°РїСѓСЃС‚РёС‚СЊ?",
                    f"РџСЂРµСЃРµС‚ РёР·РјРµРЅРµРЅ РЅР° '{preset_name}'.\n\n"
                    "РџРµСЂРµР·Р°РїСѓСЃС‚РёС‚СЊ zapret СЃ РЅРѕРІС‹Рј РїСЂРµСЃРµС‚РѕРј?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if reply == QMessageBox.Yes:
                    self.restart_zapret()

        except Exception as exc:
            logger.error(f"РћС€РёР±РєР° СѓСЃС‚Р°РЅРѕРІРєРё РїСЂРµСЃРµС‚Р°: {exc}", exc_info=True)
            QMessageBox.critical(
                None,
                "РћС€РёР±РєР°",
                f"РќРµ СѓРґР°Р»РѕСЃСЊ СѓСЃС‚Р°РЅРѕРІРёС‚СЊ РїСЂРµСЃРµС‚:\n{exc}",
            )

    def check_autostart(self):
        """Refresh autostart checkbox state."""
        try:
            self.autostart_action.setChecked(self.autostart_manager.is_enabled())
        except Exception as exc:
            logger.error(f"РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё Р°РІС‚РѕР·Р°РїСѓСЃРєР°: {exc}")

    def toggle_autostart(self):
        """Toggle autostart state."""
        try:
            if self.autostart_action.isChecked():
                if self.autostart_manager.enable():
                    self.show_notification(
                        "РђРІС‚РѕР·Р°РїСѓСЃРє",
                        "Р’РєР»СЋС‡РµРЅ",
                        QSystemTrayIcon.Information,
                        2000,
                    )
                else:
                    QMessageBox.critical(
                        None,
                        "РћС€РёР±РєР°",
                        "РќРµ СѓРґР°Р»РѕСЃСЊ РІРєР»СЋС‡РёС‚СЊ Р°РІС‚РѕР·Р°РїСѓСЃРє",
                    )
                    self.autostart_action.setChecked(False)
            else:
                if self.autostart_manager.disable():
                    self.show_notification(
                        "РђРІС‚РѕР·Р°РїСѓСЃРє",
                        "Р’С‹РєР»СЋС‡РµРЅ",
                        QSystemTrayIcon.Information,
                        2000,
                    )
                else:
                    QMessageBox.critical(
                        None,
                        "РћС€РёР±РєР°",
                        "РќРµ СѓРґР°Р»РѕСЃСЊ РІС‹РєР»СЋС‡РёС‚СЊ Р°РІС‚РѕР·Р°РїСѓСЃРє",
                    )
                    self.autostart_action.setChecked(True)

        except Exception as exc:
            logger.error(
                f"РћС€РёР±РєР° РїРµСЂРµРєР»СЋС‡РµРЅРёСЏ Р°РІС‚РѕР·Р°РїСѓСЃРєР°: {exc}",
                exc_info=True,
            )
            QMessageBox.critical(
                None,
                "РћС€РёР±РєР°",
                f"РќРµ СѓРґР°Р»РѕСЃСЊ РёР·РјРµРЅРёС‚СЊ Р°РІС‚РѕР·Р°РїСѓСЃРє:\n{exc}",
            )
            self.check_autostart()

    def show_main_window(self):
        """Placeholder for main window."""
        QMessageBox.information(
            None,
            "Р’ СЂР°Р·СЂР°Р±РѕС‚РєРµ",
            "Р“Р»Р°РІРЅРѕРµ РѕРєРЅРѕ Р±СѓРґРµС‚ РґРѕСЃС‚СѓРїРЅРѕ РІ СЃР»РµРґСѓСЋС‰РµР№ РІРµСЂСЃРёРё.\n\n"  # noqa: E501
            "РџРѕРєР° РёСЃРїРѕР»СЊР·СѓР№С‚Рµ РјРµРЅСЋ СЃРёСЃС‚РµРјРЅРѕРіРѕ С‚СЂРµСЏ РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ.",  # noqa: E501
        )

    def show_logs(self):
        """Open application logs."""
        try:
            log_file = Path(tempfile.gettempdir()) / "ZapretManager" / "app.log"

            if not log_file.exists():
                QMessageBox.warning(
                    None,
                    "Р›РѕРіРё РЅРµ РЅР°Р№РґРµРЅС‹",
                    f"Р¤Р°Р№Р» Р»РѕРіРѕРІ РЅРµ РЅР°Р№РґРµРЅ:\n{log_file}",
                )
                return

            subprocess.Popen(["notepad.exe", str(log_file)])

        except Exception as exc:
            logger.error(f"РћС€РёР±РєР° РѕС‚РєСЂС‹С‚РёСЏ Р»РѕРіРѕРІ: {exc}", exc_info=True)
            QMessageBox.critical(
                None,
                "РћС€РёР±РєР°",
                f"РќРµ СѓРґР°Р»РѕСЃСЊ РѕС‚РєСЂС‹С‚СЊ Р»РѕРіРё:\n{exc}",
            )

    def show_diagnostics(self):
        """Show current system diagnostics."""
        try:
            from core.privileges import PrivilegesManager

            info = []
            info.append("=== Р”РёР°РіРЅРѕСЃС‚РёРєР° Zapret Manager ===\n")

            is_admin = PrivilegesManager.is_admin()
            admin_status = "вњ“ Р”Р°" if is_admin else "вњ— РќР•Рў (РўР Р•Р‘РЈР•РўРЎРЇ!)"
            info.append(f"РџСЂР°РІР° Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂР°: {admin_status}")

            status = self.zapret_manager.get_status()
            zapret_status = (
                "вњ“ Р—Р°РїСѓС‰РµРЅ" if status["running"] else "вњ— РћСЃС‚Р°РЅРѕРІР»РµРЅ"
            )
            info.append(f"РЎС‚Р°С‚СѓСЃ zapret: {zapret_status}")
            if status["running"]:
                info.append(f"  PID: {status['pid']}")
                info.append(f"  Uptime: {status['uptime']}")

            info.append(f"РђРєС‚РёРІРЅС‹Р№ РїСЂРµСЃРµС‚: {status['preset']}")
            info.append(f"\nР‘Р°Р·РѕРІР°СЏ РґРёСЂРµРєС‚РѕСЂРёСЏ: {Config.BASE_DIR}")
            mode = "EXE (frozen)" if Config.IS_FROZEN else "Python СЃРєСЂРёРїС‚"
            info.append(f"Р РµР¶РёРј: {mode}")
            info.append(f"Р’РµСЂСЃРёСЏ РїСЂРѕРґСѓРєС‚Р°: {Config.PRODUCT_VERSION}")

            winws_exists = "вњ“" if Config.WINWS2_EXE.exists() else "вњ— РќР• РќРђР™Р”Р•Рќ"
            info.append(f"winws2.exe: {winws_exists} {Config.WINWS2_EXE}")

            log_file = Path(tempfile.gettempdir()) / "ZapretManager" / "app.log"
            info.append(f"\nР›РѕРіРё РїСЂРёР»РѕР¶РµРЅРёСЏ: {log_file}")
            info.append(f"  РЎСѓС‰РµСЃС‚РІСѓРµС‚: {'вњ“' if log_file.exists() else 'вњ—'}")

            winws2_log = Path(tempfile.gettempdir()) / "ZapretManager" / "winws2.log"
            info.append(f"Р›РѕРіРё winws2.exe: {winws2_log}")
            info.append(f"  РЎСѓС‰РµСЃС‚РІСѓРµС‚: {'вњ“' if winws2_log.exists() else 'вњ—'}")

            info.append(
                f"\nРџСѓС‚СЊ СЃРѕСЃС‚РѕСЏРЅРёСЏ РѕР±РЅРѕРІР»РµРЅРёР№: {Config.UPDATE_STATE_FILE}"
            )
            info.append(
                f"РљР°С‚Р°Р»РѕРі Р·Р°РіСЂСѓР·РѕРє РѕР±РЅРѕРІР»РµРЅРёР№: {Config.UPDATE_DOWNLOAD_DIR}"  # noqa: E501
            )

            info.append("\n=== Р—Р°РїСѓС‰РµРЅРЅС‹Рµ РїСЂРѕС†РµСЃСЃС‹ ===")
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq winws2.exe", "/NH"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5,
                )
                if "winws2.exe" in result.stdout:
                    info.append("вњ“ winws2.exe Р·Р°РїСѓС‰РµРЅ")
                else:
                    info.append("вњ— winws2.exe РЅРµ Р·Р°РїСѓС‰РµРЅ")
            except Exception:
                info.append("? РќРµ СѓРґР°Р»РѕСЃСЊ РїСЂРѕРІРµСЂРёС‚СЊ")

            QMessageBox.information(None, "Р”РёР°РіРЅРѕСЃС‚РёРєР°", "\n".join(info))

        except Exception as exc:
            logger.error(f"РћС€РёР±РєР° РґРёР°РіРЅРѕСЃС‚РёРєРё: {exc}", exc_info=True)
            QMessageBox.critical(
                None,
                "РћС€РёР±РєР°",
                f"РќРµ СѓРґР°Р»РѕСЃСЊ РІС‹РїРѕР»РЅРёС‚СЊ РґРёР°РіРЅРѕСЃС‚РёРєСѓ:\n{exc}",
            )

    def show_about(self):
        """Show About dialog."""
        QMessageBox.about(
            None,
            "Рћ РїСЂРѕРіСЂР°РјРјРµ",
            f"<h3>{Config.APP_NAME}</h3>"
            f"<p>Р’РµСЂСЃРёСЏ {Config.VERSION}</p>"
            f"<p>РџРѕР»РЅРѕС†РµРЅРЅРѕРµ СѓРїСЂР°РІР»РµРЅРёРµ zapret2 С‡РµСЂРµР· СѓРґРѕР±РЅС‹Р№ GUI</p>"  # noqa: E501
            f"<p><b>Р’РѕР·РјРѕР¶РЅРѕСЃС‚Рё:</b></p>"
            f"<ul>"
            f"<li>РЈРїСЂР°РІР»РµРЅРёРµ С‡РµСЂРµР· СЃРёСЃС‚РµРјРЅС‹Р№ С‚СЂРµР№</li>"
            f"<li>70+ РіРѕС‚РѕРІС‹С… РїСЂРµСЃРµС‚РѕРІ</li>"
            f"<li>РђРІС‚РѕР·Р°РїСѓСЃРє СЃ Windows</li>"
            f"<li>РђРІС‚РѕРѕР±РЅРѕРІР»РµРЅРёРµ С‡РµСЂРµР· artifact/update server</li>"
            f"<li>Р”РёР°РіРЅРѕСЃС‚РёРєР° Рё РёСЃРїСЂР°РІР»РµРЅРёРµ РїСЂРѕР±Р»РµРј</li>"
            f"</ul>"
            f"<p><b>Р‘Р»Р°РіРѕРґР°СЂРЅРѕСЃС‚Рё:</b></p>"
            f"<p>zapret2, WinDivert, PyQt5</p>",
        )

    def quit_app(self):
        """Quit tray application."""
        reply = QMessageBox.question(
            None,
            "Р’С‹С…РѕРґ",
            "Р’С‹Р№С‚Рё РёР· РїСЂРёР»РѕР¶РµРЅРёСЏ?\n\nZapret РїСЂРѕРґРѕР»Р¶РёС‚ СЂР°Р±РѕС‚Р°С‚СЊ РІ С„РѕРЅРµ.",  # noqa: E501
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            logger.info("Р’С‹С…РѕРґ РёР· РїСЂРёР»РѕР¶РµРЅРёСЏ")
            self.hide()
            QApplication.quit()
