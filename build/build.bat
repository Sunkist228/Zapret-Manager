@echo off
chcp 65001 >nul
echo ========================================
echo   Сборка Zapret Manager
echo ========================================
echo.

:: Проверка Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден!
    echo Установите Python 3.8+ и добавьте в PATH
    pause
    exit /b 1
)

:: Проверка PyInstaller
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] PyInstaller не установлен!
    echo Установите: pip install pyinstaller
    pause
    exit /b 1
)

:: Очистка старых файлов
echo [1/4] Очистка старых файлов...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

:: Сборка
echo [2/4] Сборка EXE...
pyinstaller zapret_manager.spec

if %errorlevel% neq 0 (
    echo.
    echo [ОШИБКА] Сборка не удалась!
    pause
    exit /b 1
)

:: Проверка результата
if not exist "..\dist\ZapretManager.exe" (
    echo.
    echo [ОШИБКА] EXE файл не создан!
    pause
    exit /b 1
)

:: Информация о файле
echo [3/4] Проверка файла...
for %%A in ("..\dist\ZapretManager.exe") do (
    set size=%%~zA
    set /a sizeMB=!size! / 1048576
    echo Размер: !sizeMB! MB
)

echo [4/4] Готово!
echo.
echo ========================================
echo   Файл создан: dist\ZapretManager.exe
echo ========================================
echo.
echo Для запуска: dist\ZapretManager.exe
echo (требуются права администратора)
echo.
pause
