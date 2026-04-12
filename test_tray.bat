@echo off
:: Быстрый тест Zapret Tray
cd /d "%~dp0"

echo.
echo ========================================
echo   Тест Zapret Tray Application
echo ========================================
echo.

:: Проверка Python
echo [1/5] Проверка Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python не найден
    goto :error
)
echo [+] Python найден

:: Проверка PyQt5
echo [2/5] Проверка PyQt5...
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] PyQt5 не установлен
    echo [*] Установка PyQt5...
    python -m pip install PyQt5
    if %errorlevel% neq 0 goto :error
)
echo [+] PyQt5 установлен

:: Проверка файлов
echo [3/5] Проверка файлов zapret...
if not exist "exe\winws2.exe" (
    echo [X] Не найден exe\winws2.exe
    goto :error
)
if not exist "utils\zapret2-run.bat" (
    echo [X] Не найден utils\zapret2-run.bat
    goto :error
)
echo [+] Файлы zapret на месте

:: Проверка синтаксиса Python
echo [4/5] Проверка синтаксиса zapret_tray.py...
python -m py_compile zapret_tray.py >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Ошибка синтаксиса в zapret_tray.py
    goto :error
)
echo [+] Синтаксис корректен

:: Проверка запущенных копий
echo [5/5] Проверка запущенных копий...
tasklist /FI "IMAGENAME eq pythonw.exe" 2>nul | find /I "pythonw.exe" >nul
if %errorlevel% equ 0 (
    echo [!] Обнаружена запущенная копия
    echo     Если приложение уже работает - это нормально
) else (
    echo [+] Нет запущенных копий
)

echo.
echo ========================================
echo [+] Все проверки пройдены успешно!
echo ========================================
echo.
echo Приложение готово к запуску.
echo.
echo Запустите: start_tray.bat
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo [X] Тест не пройден
echo ========================================
echo.
pause
exit /b 1
