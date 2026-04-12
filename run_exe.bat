@echo off
:: Быстрый запуск ZapretTray.exe
cd /d "%~dp0"

if exist "dist\ZapretTray.exe" (
    echo [*] Запуск ZapretTray...
    start "" "dist\ZapretTray.exe"

    timeout /t 2 /nobreak >nul

    tasklist /FI "IMAGENAME eq ZapretTray.exe" 2>nul | find /I "ZapretTray.exe" >nul
    if %errorlevel% equ 0 (
        echo [+] Приложение запущено в системном трее
    ) else (
        echo [!] Проверьте системный трей
    )
) else (
    echo [!] Файл не найден: dist\ZapretTray.exe
    echo.
    echo Создайте EXE файл: build_exe.bat
    pause
    exit /b 1
)
