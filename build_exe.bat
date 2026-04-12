@echo off
:: Создание EXE файла для Zapret Tray
cd /d "%~dp0"

echo.
echo ========================================
echo   Создание EXE файла Zapret Tray
echo ========================================
echo.

:: Проверка Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python не найден
    pause
    exit /b 1
)

:: Установка PyInstaller
echo [*] Проверка PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Установка PyInstaller...
    python -m pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [!] Ошибка установки PyInstaller
        pause
        exit /b 1
    )
)

:: Создание EXE
echo.
echo [*] Создание EXE файла...
echo     Это может занять несколько минут...
echo.

python -m PyInstaller --onefile --windowed --name=ZapretTray --clean zapret_tray.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo [+] EXE файл создан успешно!
    echo ========================================
    echo.
    echo Файл находится в: dist\ZapretTray.exe
    echo.
    echo Вы можете:
    echo 1. Скопировать ZapretTray.exe в любую папку
    echo 2. Запустить его двойным кликом
    echo 3. Добавить в автозагрузку через меню приложения
    echo.

    :: Открываем папку с EXE
    if exist "dist\ZapretTray.exe" (
        explorer /select,"dist\ZapretTray.exe"
    )
) else (
    echo.
    echo [!] Ошибка при создании EXE
    echo.
)

pause
