# -*- coding: utf-8 -*-
"""
Системный трей для Zapret Manager
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (QSystemTrayIcon, QMenu, QAction, QMessageBox)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import QTimer, Qt

from core.zapret_manager import ZapretManager
from core.preset_manager import PresetManager
from core.autostart import AutostartManager
from utils.config import Config
from utils.logger import logger


class ZapretTrayIcon(QSystemTrayIcon):
    """Иконка в системном трее"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Менеджеры
        self.zapret_manager = ZapretManager()
        self.preset_manager = PresetManager()
        self.autostart_manager = AutostartManager()

        # Главное окно (будет создано позже)
        self.main_window = None

        # Создание меню
        self.create_menu()

        # Установка иконки
        self.set_icon_color("red")

        # Обработка кликов
        self.activated.connect(self.on_tray_activated)

        # Таймер обновления статуса
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(Config.STATUS_UPDATE_INTERVAL)

        # Первоначальное обновление
        self.update_status()
        self.check_autostart()

        # Уведомление о запуске
        self.showMessage(
            Config.APP_NAME,
            "Приложение запущено",
            QSystemTrayIcon.Information,
            2000
        )

    def create_menu(self):
        """Создание контекстного меню"""
        self.menu = QMenu()

        # Статус
        self.status_action = QAction("Статус: проверка...", self.menu)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)

        self.menu.addSeparator()

        # Включить/Выключить
        self.toggle_action = QAction("▶ Включить", self.menu)
        self.toggle_action.triggered.connect(self.toggle_zapret)
        self.menu.addAction(self.toggle_action)

        # Перезапустить
        self.restart_action = QAction("🔄 Перезапустить", self.menu)
        self.restart_action.triggered.connect(self.restart_zapret)
        self.restart_action.setEnabled(False)
        self.menu.addAction(self.restart_action)

        self.menu.addSeparator()

        # Пресеты (подменю)
        self.presets_menu = QMenu("📋 Пресеты", self.menu)
        self.menu.addMenu(self.presets_menu)
        self.update_presets_menu()

        self.menu.addSeparator()

        # Открыть главное окно
        self.show_window_action = QAction("⚙️ Открыть главное окно", self.menu)
        self.show_window_action.triggered.connect(self.show_main_window)
        self.menu.addAction(self.show_window_action)

        self.menu.addSeparator()

        # Показать логи
        show_logs_action = QAction("📋 Показать логи", self.menu)
        show_logs_action.triggered.connect(self.show_logs)
        self.menu.addAction(show_logs_action)

        # Диагностика
        diagnostics_action = QAction("🔍 Диагностика", self.menu)
        diagnostics_action.triggered.connect(self.show_diagnostics)
        self.menu.addAction(diagnostics_action)

        self.menu.addSeparator()

        # Автозапуск
        self.autostart_action = QAction("Автозапуск", self.menu)
        self.autostart_action.setCheckable(True)
        self.autostart_action.triggered.connect(self.toggle_autostart)
        self.menu.addAction(self.autostart_action)

        self.menu.addSeparator()

        # О программе
        about_action = QAction("ℹ️ О программе", self.menu)
        about_action.triggered.connect(self.show_about)
        self.menu.addAction(about_action)

        # Выход
        quit_action = QAction("❌ Выход", self.menu)
        quit_action.triggered.connect(self.quit_app)
        self.menu.addAction(quit_action)

        self.setContextMenu(self.menu)

    def update_presets_menu(self):
        """Обновление меню пресетов"""
        self.presets_menu.clear()

        presets = self.preset_manager.list_presets()
        active_preset = self.preset_manager.get_active_preset()

        # Популярные пресеты (топ-5)
        popular_presets = [
            "default-main",
            "CrazyMaxs",
            "Default v5",
            "ALL TCP & UDP v1",
            "Ростелеком"
        ]

        # Добавляем популярные пресеты
        for preset_name in popular_presets:
            preset = next((p for p in presets if p.name == preset_name), None)
            if preset:
                action = QAction(preset.name, self.presets_menu)
                action.setCheckable(True)

                if active_preset and preset.name == active_preset.name:
                    action.setChecked(True)

                action.triggered.connect(lambda checked, p=preset.name: self.set_preset(p))
                self.presets_menu.addAction(action)

        # Разделитель
        self.presets_menu.addSeparator()

        # Все остальные пресеты в подменю
        all_presets_menu = self.presets_menu.addMenu("📋 Все пресеты")

        for preset in presets:
            if preset.name not in popular_presets:
                action = QAction(preset.name, all_presets_menu)
                action.setCheckable(True)

                if active_preset and preset.name == active_preset.name:
                    action.setChecked(True)

                action.triggered.connect(lambda checked, p=preset.name: self.set_preset(p))
                all_presets_menu.addAction(action)

    def on_tray_activated(self, reason):
        """Обработка кликов по иконке"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_zapret()

    def update_status(self):
        """Обновление статуса"""
        try:
            status = self.zapret_manager.get_status()
            running = status['running']

            if running:
                uptime_str = f" ({status['uptime']})" if status['uptime'] else ""
                self.status_action.setText(f"● Запущен{uptime_str}")
                self.toggle_action.setText("⏹ Выключить")
                self.restart_action.setEnabled(True)
                self.setToolTip(f"{Config.APP_NAME} - Запущен\nПресет: {status['preset']}")
                self.set_icon_color("green")
            else:
                self.status_action.setText("✗ Остановлен")
                self.toggle_action.setText("▶ Включить")
                self.restart_action.setEnabled(False)
                self.setToolTip(f"{Config.APP_NAME} - Остановлен")
                self.set_icon_color("red")

        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {e}")

    def set_icon_color(self, color: str):
        """Установка цвета иконки"""
        try:
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # Цвет фона
            if color == "green":
                painter.setBrush(QColor(76, 175, 80))
            elif color == "yellow":
                painter.setBrush(QColor(255, 193, 7))
            else:  # red
                painter.setBrush(QColor(244, 67, 54))

            painter.setPen(Qt.NoPen)
            painter.drawEllipse(4, 4, 56, 56)

            # Буква Z
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Arial", 36, QFont.Bold)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "Z")

            painter.end()

            self.setIcon(QIcon(pixmap))

        except Exception as e:
            logger.error(f"Ошибка установки иконки: {e}")

    def toggle_zapret(self):
        """Переключение состояния zapret"""
        try:
            if self.zapret_manager.is_running():
                self.stop_zapret()
            else:
                self.start_zapret()
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка переключения:\n{e}")

    def start_zapret(self):
        """Запуск zapret"""
        try:
            logger.info("Запуск zapret через трей")

            # Проверяем что пресет выбран
            if not Config.ACTIVE_PRESET.exists():
                QMessageBox.warning(
                    None,
                    "Пресет не выбран",
                    "Сначала выберите пресет из меню 'Пресеты'"
                )
                return

            self.showMessage(Config.APP_NAME, "Запуск...", QSystemTrayIcon.Information, 1000)

            if self.zapret_manager.start():
                self.showMessage(Config.APP_NAME, "Запущен", QSystemTrayIcon.Information, 2000)
                QTimer.singleShot(2000, self.update_status)
            else:
                # Показываем детальную ошибку
                import tempfile
                log_file = Path(tempfile.gettempdir()) / "ZapretManager" / "winws2.log"
                error_msg = "Не удалось запустить zapret.\n\n"

                # Пытаемся прочитать логи winws2.exe
                if log_file.exists():
                    try:
                        log_content = log_file.read_text(encoding='utf-8', errors='ignore')
                        if log_content.strip():
                            error_msg += f"Вывод winws2.exe:\n{log_content[:500]}\n\n"
                    except:
                        pass

                error_msg += "Возможные причины:\n"
                error_msg += "• Отсутствуют права администратора\n"
                error_msg += "• Неверный пресет или отсутствуют файлы списков\n"
                error_msg += "• Конфликт с другими программами (VPN, антивирус)\n\n"
                error_msg += "Проверьте логи: Меню → Показать логи"

                QMessageBox.critical(
                    None,
                    "Ошибка запуска",
                    error_msg
                )

        except Exception as e:
            logger.error(f"Ошибка запуска: {e}", exc_info=True)
            QMessageBox.critical(None, "Ошибка", f"Не удалось запустить:\n{e}")

    def stop_zapret(self):
        """Остановка zapret"""
        try:
            logger.info("Остановка zapret через трей")

            self.showMessage(Config.APP_NAME, "Остановка...", QSystemTrayIcon.Information, 1000)

            if self.zapret_manager.stop():
                self.showMessage(Config.APP_NAME, "Остановлен", QSystemTrayIcon.Information, 2000)
                QTimer.singleShot(500, self.update_status)
            else:
                QMessageBox.warning(
                    None,
                    "Предупреждение",
                    "Не удалось остановить zapret.\n\nПопробуйте еще раз."
                )

        except Exception as e:
            logger.error(f"Ошибка остановки: {e}", exc_info=True)
            QMessageBox.critical(None, "Ошибка", f"Не удалось остановить:\n{e}")

    def restart_zapret(self):
        """Перезапуск zapret"""
        try:
            logger.info("Перезапуск zapret через трей")

            self.showMessage(Config.APP_NAME, "Перезапуск...", QSystemTrayIcon.Information, 1000)

            if self.zapret_manager.restart():
                self.showMessage(Config.APP_NAME, "Перезапущен", QSystemTrayIcon.Information, 2000)
                QTimer.singleShot(2000, self.update_status)
            else:
                QMessageBox.critical(
                    None,
                    "Ошибка",
                    "Не удалось перезапустить zapret."
                )

        except Exception as e:
            logger.error(f"Ошибка перезапуска: {e}", exc_info=True)
            QMessageBox.critical(None, "Ошибка", f"Не удалось перезапустить:\n{e}")

    def set_preset(self, preset_name: str):
        """Установка пресета"""
        try:
            logger.info(f"Установка пресета: {preset_name}")

            if self.preset_manager.set_active_preset(preset_name):
                self.showMessage(
                    "Пресет изменен",
                    f"Установлен: {preset_name}",
                    QSystemTrayIcon.Information,
                    2000
                )

                # Обновляем меню
                self.update_presets_menu()

                # Если zapret запущен, предлагаем перезапустить
                if self.zapret_manager.is_running():
                    reply = QMessageBox.question(
                        None,
                        "Перезапустить?",
                        f"Пресет изменен на '{preset_name}'.\n\nПерезапустить zapret с новым пресетом?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )

                    if reply == QMessageBox.Yes:
                        self.restart_zapret()

            else:
                QMessageBox.critical(
                    None,
                    "Ошибка",
                    f"Не удалось установить пресет '{preset_name}'"
                )

        except Exception as e:
            logger.error(f"Ошибка установки пресета: {e}", exc_info=True)
            QMessageBox.critical(None, "Ошибка", f"Не удалось установить пресет:\n{e}")

    def check_autostart(self):
        """Проверка автозапуска"""
        try:
            enabled = self.autostart_manager.is_enabled()
            self.autostart_action.setChecked(enabled)
        except Exception as e:
            logger.error(f"Ошибка проверки автозапуска: {e}")

    def toggle_autostart(self):
        """Переключение автозапуска"""
        try:
            if self.autostart_action.isChecked():
                if self.autostart_manager.enable():
                    self.showMessage("Автозапуск", "Включен", QSystemTrayIcon.Information, 2000)
                else:
                    QMessageBox.critical(None, "Ошибка", "Не удалось включить автозапуск")
                    self.autostart_action.setChecked(False)
            else:
                if self.autostart_manager.disable():
                    self.showMessage("Автозапуск", "Выключен", QSystemTrayIcon.Information, 2000)
                else:
                    QMessageBox.critical(None, "Ошибка", "Не удалось выключить автозапуск")
                    self.autostart_action.setChecked(True)

        except Exception as e:
            logger.error(f"Ошибка переключения автозапуска: {e}", exc_info=True)
            QMessageBox.critical(None, "Ошибка", f"Не удалось изменить автозапуск:\n{e}")
            self.check_autostart()

    def show_main_window(self):
        """Показать главное окно"""
        # TODO: Реализовать после создания главного окна
        QMessageBox.information(
            None,
            "В разработке",
            "Главное окно будет доступно в следующей версии.\n\n"
            "Пока используйте меню системного трея для управления."
        )

    def show_logs(self):
        """Показать логи приложения"""
        try:
            import tempfile
            import subprocess

            log_file = Path(tempfile.gettempdir()) / "ZapretManager" / "app.log"

            if not log_file.exists():
                QMessageBox.warning(
                    None,
                    "Логи не найдены",
                    f"Файл логов не найден:\n{log_file}"
                )
                return

            # Открываем в блокноте
            subprocess.Popen(['notepad.exe', str(log_file)])

        except Exception as e:
            logger.error(f"Ошибка открытия логов: {e}", exc_info=True)
            QMessageBox.critical(None, "Ошибка", f"Не удалось открыть логи:\n{e}")

    def show_diagnostics(self):
        """Показать диагностику системы"""
        try:
            from core.privileges import PrivilegesManager
            import tempfile

            # Собираем информацию
            info = []
            info.append("=== Диагностика Zapret Manager ===\n")

            # Права администратора
            is_admin = PrivilegesManager.is_admin()
            info.append(f"Права администратора: {'✓ Да' if is_admin else '✗ НЕТ (ТРЕБУЕТСЯ!)'}")

            # Статус zapret
            status = self.zapret_manager.get_status()
            info.append(f"Статус zapret: {'✓ Запущен' if status['running'] else '✗ Остановлен'}")
            if status['running']:
                info.append(f"  PID: {status['pid']}")
                info.append(f"  Uptime: {status['uptime']}")

            # Активный пресет
            info.append(f"Активный пресет: {status['preset']}")

            # Пути
            info.append(f"\nБазовая директория: {Config.BASE_DIR}")
            info.append(f"Режим: {'EXE (frozen)' if Config.IS_FROZEN else 'Python скрипт'}")
            info.append(f"winws2.exe: {'✓' if Config.WINWS2_EXE.exists() else '✗ НЕ НАЙДЕН'} {Config.WINWS2_EXE}")

            # Логи
            log_file = Path(tempfile.gettempdir()) / "ZapretManager" / "app.log"
            info.append(f"\nЛоги приложения: {log_file}")
            info.append(f"  Существует: {'✓' if log_file.exists() else '✗'}")

            winws2_log = Path(tempfile.gettempdir()) / "ZapretManager" / "winws2.log"
            info.append(f"Логи winws2.exe: {winws2_log}")
            info.append(f"  Существует: {'✓' if winws2_log.exists() else '✗'}")

            # Процессы
            info.append("\n=== Запущенные процессы ===")
            try:
                result = subprocess.run(
                    ['tasklist', '/FI', 'IMAGENAME eq winws2.exe', '/NH'],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5
                )
                if 'winws2.exe' in result.stdout:
                    info.append("✓ winws2.exe запущен")
                else:
                    info.append("✗ winws2.exe не запущен")
            except:
                info.append("? Не удалось проверить")

            # Показываем результат
            QMessageBox.information(
                None,
                "Диагностика",
                "\n".join(info)
            )

        except Exception as e:
            logger.error(f"Ошибка диагностики: {e}", exc_info=True)
            QMessageBox.critical(None, "Ошибка", f"Не удалось выполнить диагностику:\n{e}")

    def show_about(self):
        """Показать окно 'О программе'"""
        QMessageBox.about(
            None,
            "О программе",
            f"<h3>{Config.APP_NAME}</h3>"
            f"<p>Версия {Config.VERSION}</p>"
            f"<p>Полноценное управление zapret2 через удобный GUI</p>"
            f"<p><b>Возможности:</b></p>"
            f"<ul>"
            f"<li>Управление через системный трей</li>"
            f"<li>70+ готовых пресетов</li>"
            f"<li>Автозапуск с Windows</li>"
            f"<li>Диагностика и исправление проблем</li>"
            f"</ul>"
            f"<p><b>Благодарности:</b></p>"
            f"<p>zapret2, WinDivert, PyQt5</p>"
        )

    def quit_app(self):
        """Выход из приложения"""
        reply = QMessageBox.question(
            None,
            "Выход",
            "Выйти из приложения?\n\nZapret продолжит работать в фоне.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            logger.info("Выход из приложения")
            self.hide()
            from PyQt5.QtWidgets import QApplication
            QApplication.quit()
