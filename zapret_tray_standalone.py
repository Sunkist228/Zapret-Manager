#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zapret System Tray Application - Standalone Version
Все файлы упакованы внутри EXE
"""

import sys
import os
import subprocess
import winreg
import traceback
import tempfile
import shutil
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
        pass

try:
    from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
    from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
    from PyQt5.QtCore import QTimer, Qt
except ImportError:
    print("Ошибка: PyQt5 не установлен")
    sys.exit(1)

class ZapretTray:
    def __init__(self):
        import logging
        try:
            logging.info("Инициализация QApplication")
            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)

            # Определяем базовую директорию
            if getattr(sys, 'frozen', False):
                # Если запущен как EXE
                self.base_dir = Path(sys._MEIPASS)
                self.is_frozen = True
                logging.info(f"Режим: EXE, базовая директория: {self.base_dir}")
            else:
                # Если запущен как скрипт
                self.base_dir = Path(__file__).parent.absolute()
                self.is_frozen = False
                logging.info(f"Режим: Python скрипт, базовая директория: {self.base_dir}")

            # Пути к файлам
            self.exe_dir = self.base_dir / "exe"
            self.utils_dir = self.base_dir / "utils"
            self.winws2_exe = self.exe_dir / "winws2.exe"
            self.preset_file = self.utils_dir / "preset-active.txt"

            logging.info(f"Проверка winws2.exe: {self.winws2_exe}")
            logging.info(f"Существует: {self.winws2_exe.exists()}")

            # Проверка файлов
            if not self.winws2_exe.exists():
                error_msg = f"Не найден winws2.exe:\n{self.winws2_exe}\n\nБазовая директория: {self.base_dir}"
                logging.error(error_msg)

                # Показываем содержимое директории для диагностики
                try:
                    files = list(self.base_dir.rglob("*"))
                    logging.error(f"Файлы в базовой директории: {files[:20]}")
                except:
                    pass

                QMessageBox.critical(None, "Ошибка", error_msg)
                sys.exit(1)

            if not self.preset_file.exists():
                error_msg = f"Не найден preset-active.txt:\n{self.preset_file}"
                logging.error(error_msg)
                QMessageBox.critical(None, "Ошибка", error_msg)
                sys.exit(1)

            logging.info("Все файлы найдены успешно")

            # Создание иконки трея
            logging.info("Создание иконки трея")
            self.tray_icon = QSystemTrayIcon(self.app)
            self.tray_icon.setToolTip("Zapret")

            # Создание меню
            logging.info("Создание меню")
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
            self.tray_icon.activated.connect(self.on_tray_activated)

            # Таймер для обновления статуса
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_status)
            self.timer.start(3000)

            # Первоначальное обновление
            self.update_status()
            self.check_autostart()

            # Показать иконку
            self.tray_icon.show()

            # Уведомление о запуске
            self.tray_icon.showMessage(
                "Zapret Tray",
                "Приложение запущено",
                QSystemTrayIcon.Information,
                2000
            )

        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось запустить:\n{e}\n\n{traceback.format_exc()}")
            sys.exit(1)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_zapret()

    def is_running(self):
        import logging
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq winws2.exe', '/NH'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5
            )
            running = 'winws2.exe' in result.stdout
            logging.debug(f"Проверка статуса winws2.exe: {running}")
            return running
        except Exception as e:
            logging.error(f"Ошибка проверки статуса: {e}")
            return False

    def update_status(self):
        import logging
        try:
            running = self.is_running()
            logging.debug(f"Обновление статуса: running={running}")

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
            logging.error(f"Ошибка обновления статуса: {e}")
            print(f"Ошибка обновления статуса: {e}")

    def set_icon_color(self, color):
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

            painter.setPen(QColor(255, 255, 255))
            font = QFont("Arial", 36, QFont.Bold)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "Z")

            painter.end()

            self.tray_icon.setIcon(QIcon(pixmap))
        except Exception as e:
            print(f"Ошибка установки иконки: {e}")

    def toggle_zapret(self):
        try:
            if self.is_running():
                self.stop_zapret()
            else:
                self.start_zapret()
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка переключения:\n{e}")

    def start_zapret(self):
        import logging
        try:
            logging.info("=== Запуск zapret ===")
            logging.info(f"winws2.exe: {self.winws2_exe}")
            logging.info(f"preset: {self.preset_file}")

            # Проверка прав администратора
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            logging.info(f"Права администратора: {is_admin}")

            if not is_admin:
                QMessageBox.warning(
                    None,
                    "Требуются права администратора",
                    "Для запуска zapret требуются права администратора.\n\n"
                    "Перезапустите приложение от имени администратора."
                )
                return

            # Очистка WinDivert
            logging.info("Очистка WinDivert сервисов")
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
                    logging.info(f"Сервис {service} очищен")
                except Exception as e:
                    logging.debug(f"Сервис {service}: {e}")

            # TCP timestamps
            logging.info("Включение TCP timestamps")
            try:
                subprocess.run(
                    ['netsh', 'interface', 'tcp', 'set', 'global', 'timestamps=enabled'],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5
                )
            except Exception as e:
                logging.warning(f"TCP timestamps: {e}")

            # Запуск winws2.exe в фоне
            logging.info("Запуск winws2.exe")
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

            process = subprocess.Popen(
                [str(self.winws2_exe), f'@{self.preset_file}'],
                cwd=str(self.base_dir),
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )

            logging.info(f"winws2.exe запущен, PID: {process.pid}")

            self.tray_icon.showMessage("Zapret", "Запуск...", QSystemTrayIcon.Information, 1000)
            QTimer.singleShot(2000, self.update_status)

        except Exception as e:
            error_msg = f"Не удалось запустить:\n{e}\n\n{traceback.format_exc()}"
            logging.error(error_msg)
            QMessageBox.critical(None, "Ошибка", error_msg)

    def stop_zapret(self):
        import logging
        try:
            logging.info("=== Остановка zapret ===")
            result = subprocess.run(
                ['taskkill', '/F', '/IM', 'winws2.exe'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10
            )
            logging.info(f"Результат taskkill: {result.returncode}")
            logging.info(f"Вывод: {result.stdout}")

            self.tray_icon.showMessage("Zapret", "Остановлен", QSystemTrayIcon.Information, 1000)
            QTimer.singleShot(500, self.update_status)

        except subprocess.TimeoutExpired:
            logging.error("Таймаут при остановке winws2.exe")
            QMessageBox.warning(None, "Предупреждение", "Таймаут при остановке процесса")
        except Exception as e:
            error_msg = f"Не удалось остановить:\n{e}"
            logging.error(error_msg)
            QMessageBox.critical(None, "Ошибка", error_msg)

    def check_autostart(self):
        import logging
        try:
            logging.info("Проверка автозапуска")
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            try:
                value, _ = winreg.QueryValueEx(key, "ZapretTray")
                logging.info(f"Найден ключ автозапуска: {value}")

                # Проверяем, что путь совпадает с текущим EXE
                if getattr(sys, 'frozen', False):
                    current_exe = f'"{sys.executable}"'
                    # Сравниваем пути (игнорируя регистр)
                    if value.lower().strip('"') == sys.executable.lower():
                        logging.info("Автозапуск включен для текущего EXE")
                        self.autostart_action.setChecked(True)
                    else:
                        logging.info(f"Автозапуск включен для другого пути: {value}")
                        self.autostart_action.setChecked(False)
                else:
                    # Для Python скрипта
                    self.autostart_action.setChecked(True)

            except FileNotFoundError:
                logging.info("Ключ автозапуска не найден")
                self.autostart_action.setChecked(False)
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            logging.error(f"Ошибка проверки автозапуска: {e}")
            self.autostart_action.setChecked(False)

    def toggle_autostart(self):
        import logging
        try:
            logging.info(f"Переключение автозапуска: {self.autostart_action.isChecked()}")

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_READ
            )

            if self.autostart_action.isChecked():
                # Включаем автозапуск
                if getattr(sys, 'frozen', False):
                    exe_path = sys.executable
                    startup_cmd = f'"{exe_path}"'
                    logging.info(f"Добавление в автозапуск: {startup_cmd}")
                else:
                    pythonw = sys.executable.replace('python.exe', 'pythonw.exe')
                    script_path = str(Path(__file__).absolute())
                    startup_cmd = f'"{pythonw}" "{script_path}"'
                    logging.info(f"Добавление в автозапуск (Python): {startup_cmd}")

                winreg.SetValueEx(key, "ZapretTray", 0, winreg.REG_SZ, startup_cmd)
                logging.info("Автозапуск успешно включен")
                self.tray_icon.showMessage("Автозапуск", "Включен", QSystemTrayIcon.Information, 2000)
            else:
                # Выключаем автозапуск
                try:
                    logging.info("Удаление из автозапуска")
                    winreg.DeleteValue(key, "ZapretTray")
                    logging.info("Автозапуск успешно выключен")
                    self.tray_icon.showMessage("Автозапуск", "Выключен", QSystemTrayIcon.Information, 2000)
                except FileNotFoundError:
                    logging.info("Ключ автозапуска не найден (уже удален)")
                    pass

            winreg.CloseKey(key)

        except Exception as e:
            error_msg = f"Не удалось изменить автозапуск:\n{e}"
            logging.error(error_msg)
            QMessageBox.critical(None, "Ошибка", error_msg)
            self.check_autostart()  # Восстанавливаем правильное состояние

    def show_about(self):
        QMessageBox.about(
            None,
            "О программе",
            "<h3>Zapret System Tray</h3>"
            "<p>Версия 1.0 (Standalone)</p>"
            "<p>Управление zapret через системный трей</p>"
            "<p><b>Все файлы упакованы внутри EXE</b></p>"
            "<p><b>Возможности:</b></p>"
            "<ul>"
            "<li>Включение/выключение одним кликом</li>"
            "<li>Автозапуск при старте Windows</li>"
            "<li>Полностью фоновая работа</li>"
            "</ul>"
        )

    def quit_app(self):
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
        return self.app.exec_()

def main():
    # Настройка логирования для диагностики
    log_file = None
    try:
        import logging
        log_dir = Path(tempfile.gettempdir()) / "ZapretTray"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "zapret_tray.log"

        logging.basicConfig(
            filename=str(log_file),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.info("=== Запуск ZapretTray ===")
    except:
        pass

    try:
        # Защита от двойного запуска через именованный Mutex
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

        # ВАЖНО: используем глобальный mutex с уникальным именем
        mutex_name = "Global\\ZapretTray_SingleInstance_Mutex_48621"

        # Создаем mutex
        mutex = kernel32.CreateMutexW(None, True, mutex_name)
        last_error = kernel32.GetLastError()

        if log_file:
            logging.info(f"CreateMutex вызван, last_error: {last_error}")

        # ERROR_ALREADY_EXISTS = 183
        if last_error == 183:
            # Приложение уже запущено - тихо выходим БЕЗ ОКНА
            if log_file:
                logging.info("Приложение уже запущено (mutex существует), тихий выход")

            # Освобождаем mutex и выходим
            if mutex:
                kernel32.CloseHandle(mutex)

            sys.exit(0)

        if log_file:
            logging.info("Mutex создан успешно, продолжаем запуск")

        # Создаем приложение
        tray = ZapretTray()
        if log_file:
            logging.info("ZapretTray инициализирован")

        # Запускаем event loop
        result = tray.run()

        # Освобождаем mutex при выходе
        if mutex:
            kernel32.ReleaseMutex(mutex)
            kernel32.CloseHandle(mutex)
            if log_file:
                logging.info("Mutex освобожден")

        if log_file:
            logging.info("Выход из приложения")
        sys.exit(result)

    except Exception as e:
        error_msg = f"Критическая ошибка: {e}\n\n{traceback.format_exc()}"
        if log_file:
            logging.error(error_msg)

        # Показываем окно с ошибкой только если это реальная ошибка
        try:
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Ошибка запуска ZapretTray",
                f"Не удалось запустить приложение.\n\n{e}\n\nЛог: {log_file}"
            )
        except:
            pass

        sys.exit(1)

if __name__ == "__main__":
    main()
