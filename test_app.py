#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматическое тестирование Zapret Manager
"""

import sys
import time
import subprocess
import tempfile
from pathlib import Path

# Фикс кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_process(name):
    """Проверить запущен ли процесс"""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', f'IMAGENAME eq {name}', '/NH'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=5
        )
        return name in result.stdout
    except:
        return False

def read_logs(lines=20):
    """Прочитать последние строки логов"""
    log_file = Path(tempfile.gettempdir()) / "ZapretManager" / "app.log"
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            return f.readlines()[-lines:]
    return []

def test_app():
    """Автоматическое тестирование"""
    print("=== Автоматическое тестирование Zapret Manager ===\n")

    # Тест 1: Проверка наличия EXE
    print("[1/5] Проверка наличия EXE файла...")
    exe_path = Path("build/dist/ZapretManager.exe")
    if exe_path.exists():
        print(f"  [OK] EXE найден: {exe_path} ({exe_path.stat().st_size / 1024 / 1024:.1f} MB)")
    else:
        print(f"  [FAIL] EXE не найден: {exe_path}")
        return False

    # Тест 2: Проверка запущенного приложения
    print("\n[2/5] Проверка запущенного приложения...")
    if check_process("ZapretManager.exe"):
        print("  [OK] ZapretManager.exe запущен")
    else:
        print("  [FAIL] ZapretManager.exe не запущен")
        print("  -> Запустите приложение от имени администратора")
        return False

    # Тест 3: Проверка winws2.exe
    print("\n[3/5] Проверка winws2.exe...")
    if check_process("winws2.exe"):
        print("  [OK] winws2.exe запущен (zapret работает)")
    else:
        print("  [WARN] winws2.exe не запущен")
        print("  -> Запустите zapret через двойной клик по иконке в трее")

    # Тест 4: Проверка логов
    print("\n[4/5] Проверка логов...")
    logs = read_logs(10)
    if logs:
        print("  [OK] Логи найдены")

        # Проверяем на ошибки
        errors = [line for line in logs if 'ERROR' in line]
        if errors:
            print(f"  [WARN] Найдено ошибок: {len(errors)}")
            for err in errors[-3:]:
                print(f"    {err.strip()}")
        else:
            print("  [OK] Критических ошибок не найдено")

        # Проверяем успешный запуск winws2
        success = any('winws2.exe запущен' in line and 'ERROR' not in logs[i+1] if i+1 < len(logs) else False
                     for i, line in enumerate(logs))
        if success:
            print("  [OK] winws2.exe успешно запущен")
    else:
        print("  [FAIL] Логи не найдены")

    # Тест 5: Проверка конфигурации
    print("\n[5/5] Проверка конфигурации...")
    config_dir = Path(tempfile.gettempdir()) / "ZapretManager" / "config"
    if config_dir.exists():
        print(f"  [OK] Конфигурация найдена: {config_dir}")

        preset = config_dir / "preset-active.txt"
        if preset.exists():
            print(f"  [OK] Активный пресет: {preset}")
        else:
            print("  [WARN] Активный пресет не найден")
    else:
        print("  [FAIL] Конфигурация не найдена")

    # Итог
    print("\n" + "="*50)
    if check_process("winws2.exe"):
        print("[SUCCESS] ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Zapret работает!")
        print("\nПроверьте Discord/YouTube - должны работать без блокировок.")
        return True
    else:
        print("[WARN] Приложение запущено, но zapret не активен")
        print("\nЗапустите zapret: двойной клик по иконке 'Z' в трее")
        return False

if __name__ == "__main__":
    try:
        success = test_app()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
