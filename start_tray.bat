@echo off
:: Запуск Zapret Tray приложения
cd /d "%~dp0"

:: Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [!] Python не найден
    echo.
    echo Установите Python 3.8 или новее:
    echo https://www.python.org/downloads/
    echo.
    echo При установке обязательно отметьте "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

:: Проверка зависимостей
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [*] Установка зависимостей PyQt5...
    echo.
    python -m pip install --upgrade pip
    python -m pip install PyQt5
    if %errorlevel% neq 0 (
        echo.
        echo [!] Ошибка установки зависимостей
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [+] Зависимости установлены успешно
    echo.
)

:: Запуск приложения (pythonw = без консоли)
echo [*] Запуск Zapret Tray...
start "" pythonw zapret_tray.py

:: Ждем 2 секунды и проверяем запуск
timeout /t 2 /nobreak >nul

tasklist /FI "IMAGENAME eq pythonw.exe" 2>nul | find /I "pythonw.exe" >nul
if %errorlevel% equ 0 (
    echo [+] Приложение запущено в системном трее
) else (
    echo [!] Возможно, произошла ошибка при запуске
    echo     Проверьте системный трей
)

echo.
echo Нажмите любую клавишу для выхода...
pause >nul
