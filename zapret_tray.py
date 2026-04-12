#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zapret System Tray Application
"""

import sys
import os
import subprocess
import winreg
import traceback
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32' and sys.stdout is not None:
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass  # Ignore encoding errors in GUI mode

try:
    from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
    from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
    from PyQt5.QtCore import QTimer, Qt
except ImportError:
    print("Ошибка: PyQt5 не установлен")
    print("Установите: pip install PyQt5")
    sys.exit(1)

class ZapretTray:
    def __init__(self):
        try:
            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)

            # Пути
            self.base_dir = Path(__file__).parent.absolute()
            self.run_bat = self.base_dir / "utils" / "zapret2-run.bat"
            self.service_bat = self.base_dir / "service.bat"
            self.winws2_exe = self.base_dir / "exe" / "winws2.exe"

            # Проверка существования файлов
            if not self.winws2_exe.exists():
                QMessageBox.critical(
                    None,
                    "Ошибка",
                    f"Не найден winws2.exe:\n{self.winws2_exe}\n\nУбедитесь, что приложение запущено из папки zapret2"
                )
                sys.exit(1)

            # Создание иконки трея
            self.tray_icon = QSystemTrayIcon(self.app)
            self.tray_icon.setToolTip("Zapret")

            # Создание меню
            self.menu = QMenu()

            # Статус
            self.status_action = QAction("Статус: проверка...", self.menu)
            self.status_action.setEnabled(False)
            self.menu.addAction(self.status_action)

            self.menu.addSeparator()

            # Включить/Выключить
            self.toggle_action = QAction("Включить", self.menu)
            self.toggle_action.triggered.connect(self.toggle_zapret)
            self.menu.addAction(self.toggle_action)

            self.menu.addSeparator()

            # Автозапуск
            self.autostart_action = QAction("Автозапуск", self.menu)
            self.autostart_action.setCheckable(True)
            self.autostart_action.triggered.connect(self.toggle_autostart)
            self.menu.addAction(self.autostart_action)

            self.menu.addSeparator()

            # О программе
            about_action = QAction("О программе", self.menu)
            about_action.triggered.connect(self.show_about)
            self.menu.addAction(about_action)

            self.menu.addSeparator()

            # Выход
            quit_action = QAction("Выход", self.menu)
            quit_action.triggered.connect(self.quit_app)
            self.menu.addAction(quit_action)

            self.tray_icon.setContextMenu(self.menu)

            # Обработка двойного клика
            self.tray_icon.activated.connect(self.on_tray_activated)

            # Таймер для обновления статуса
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_status)
            self.timer.start(3000)  # Обновление каждые 3 секунды

            # Первоначальное обновление
            self.update_status()
            self.check_autostart()

            # Показать иконку
            self.tray_icon.show()

            # Показать уведомление о запуске
            self.tray_icon.showMessage(
                "Zapret Tray",
                "Приложение запущено в системном трее",
                QSystemTrayIcon.Information,
                2000
            )

        except Exception as e:
            QMessageBox.critical(None, "Ошибка инициализации", f"Не удалось запустить приложение:\n{e}\n\n{traceback.format_exc()}")
            sys.exit(1)

    def on_tray_activated(self, reason):
        """Обработка клика по иконке трея"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_zapret()

    def is_running(self):
        """Проверка, запущен ли winws2.exe"""
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq winws2.exe', '/NH'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5
            )
            return 'winws2.exe' in result.stdout
        except Exception as e:
            print(f"Ошибка проверки статуса: {e}")
            return False

    def update_status(self):
        """Обновление статуса в меню"""
        try:
            running = self.is_running()

            if running:
                self.status_action.setText("Статус: ✓ Запущен")
                self.toggle_action.setText("⏹ Выключить")
                self.tray_icon.setToolTip("Zapret - Запущен")
                self.set_icon_color("green")
            else:
                self.status_action.setText("Статус: ✗ Остановлен")
                self.toggle_action.setText("▶ Включить")
                self.tray_icon.setToolTip("Zapret - Остановлен")
                self.set_icon_color("red")
        except Exception as e:
            print(f"Ошибка обновления статуса: {e}")

    def set_icon_color(self, color):
        """Установка цвета иконки"""
        try:
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            if color == "green":
                painter.setBrush(QColor(76, 175, 80))
            else:
                painter.setBrush(QColor(244, 67, 54))

            painter.setPen(Qt.NoPen)
            painter.drawEllipse(4, 4, 56, 56)

            # Добавляем букву Z
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Arial", 36, QFont.Bold)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "Z")

            painter.end()

            self.tray_icon.setIcon(QIcon(pixmap))
        except Exception as e:
            print(f"Ошибка установки иконки: {e}")

    def toggle_zapret(self):
        """Включение/выключение zapret"""
        try:
            if self.is_running():
                self.stop_zapret()
            else:
                self.start_zapret()
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка переключения:\n{e}")

    def start_zapret(self):
        """Запуск zapret"""
        try:
            # Проверяем наличие winws2.exe
            if not self.winws2_exe.exists():
                QMessageBox.warning(
                    None,
                    "Ошибка",
                    f"Не найден winws2.exe:\n{self.winws2_exe}"
                )
                return

            # Путь к файлу с пресетом
            preset_file = self.base_dir / "utils" / "preset-active.txt"
            if not preset_file.exists():
                QMessageBox.warning(
                    None,
                    "Ошибка",
                    f"Не найден файл пресета:\n{preset_file}"
                )
                return

            # Очистка WinDivert перед запуском
            for service in ["WinDivert", "WinDivert14", "Monkey", "Monkey14"]:
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
                except:
                    pass

            # Включаем TCP timestamps
            try:
                subprocess.run(
                    ['netsh', 'interface', 'tcp', 'set', 'global', 'timestamps=enabled'],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5
                )
            except:
                pass

            # Запускаем winws2.exe напрямую в фоне (БЕЗ ОКНА!)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE

            subprocess.Popen(
                [str(self.winws2_exe), f'@{preset_file}'],
                cwd=str(self.base_dir),
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )

            # Показываем уведомление
            self.tray_icon.showMessage(
                "Zapret",
                "Запуск...",
                QSystemTrayIcon.Information,
                1000
            )

            # Обновляем статус через 2 секунды
            QTimer.singleShot(2000, self.update_status)

        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось запустить zapret:\n{e}\n\n{traceback.format_exc()}")

    def stop_zapret(self):
        """Остановка zapret"""
        try:
            # Останавливаем процесс
            result = subprocess.run(
                ['taskkill', '/F', '/IM', 'winws2.exe'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10
            )

            # Показываем уведомление
            self.tray_icon.showMessage(
                "Zapret",
                "Остановлен",
                QSystemTrayIcon.Information,
                1000
            )

            # Обновляем статус через полсекунды
            QTimer.singleShot(500, self.update_status)

        except subprocess.TimeoutExpired:
            QMessageBox.warning(None, "Предупреждение", "Таймаут при остановке процесса")
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось остановить zapret:\n{e}")

    def check_autostart(self):
        """Проверка статуса автозапуска"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, "ZapretTray")
                self.autostart_action.setChecked(True)
            except FileNotFoundError:
                self.autostart_action.setChecked(False)
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            print(f"Ошибка проверки автозапуска: {e}")
            self.autostart_action.setChecked(False)

    def toggle_autostart(self):
        """Включение/выключение автозапуска"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_READ
            )

            if self.autostart_action.isChecked():
                # Добавляем в автозапуск
                if getattr(sys, 'frozen', False):
                    # Если это exe файл
                    exe_path = sys.executable
                    startup_cmd = f'"{exe_path}"'
                else:
                    # Если это Python скрипт
                    pythonw = sys.executable.replace('python.exe', 'pythonw.exe')
                    script_path = str(Path(__file__).absolute())
                    startup_cmd = f'"{pythonw}" "{script_path}"'

                winreg.SetValueEx(key, "ZapretTray", 0, winreg.REG_SZ, startup_cmd)

                self.tray_icon.showMessage(
                    "Автозапуск",
                    "Автозапуск включен",
                    QSystemTrayIcon.Information,
                    2000
                )
            else:
                # Удаляем из автозапуска
                try:
                    winreg.DeleteValue(key, "ZapretTray")
                    self.tray_icon.showMessage(
                        "Автозапуск",
                        "Автозапуск выключен",
                        QSystemTrayIcon.Information,
                        2000
                    )
                except FileNotFoundError:
                    pass

            winreg.CloseKey(key)

        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось изменить автозапуск:\n{e}")
            self.check_autostart()  # Восстанавливаем правильное состояние

    def show_about(self):
        """Показать информацию о программе"""
        QMessageBox.about(
            None,
            "О программе",
            "<h3>Zapret System Tray</h3>"
            "<p>Версия 1.0</p>"
            "<p>Управление zapret через системный трей</p>"
            "<p><b>Возможности:</b></p>"
            "<ul>"
            "<li>Включение/выключение одним кликом</li>"
            "<li>Автозапуск при старте Windows</li>"
            "<li>Автоматический мониторинг статуса</li>"
            "</ul>"
            "<p><b>Горячие клавиши:</b></p>"
            "<ul>"
            "<li>Двойной клик - включить/выключить</li>"
            "<li>Правый клик - меню</li>"
            "</ul>"
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
            self.tray_icon.hide()
            self.app.quit()

    def run(self):
        """Запуск приложения"""
        return self.app.exec_()

def main():
    """Главная функция"""
    try:
        # Проверка, что приложение не запущено дважды (Windows Mutex)
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

        # Создаем уникальный mutex
        mutex_name = "Global\\ZapretTrayMutex_UniqueID_48621"
        mutex = kernel32.CreateMutexW(None, True, mutex_name)

        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            # Приложение уже запущено
            app = QApplication(sys.argv)
            QMessageBox.warning(
                None,
                "Zapret Tray",
                "Приложение уже запущено!\n\nПроверьте системный трей."
            )
            sys.exit(0)

        tray = ZapretTray()
        result = tray.run()

        # Освобождаем mutex при выходе
        if mutex:
            kernel32.ReleaseMutex(mutex)
            kernel32.CloseHandle(mutex)

        sys.exit(result)

    except Exception as e:
        QMessageBox.critical(
            None,
            "Критическая ошибка",
            f"Не удалось запустить приложение:\n{e}\n\n{traceback.format_exc()}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
