@echo off
:: Запуск Zapret Manager с правами администратора
::
:: Этот скрипт автоматически запрашивает права администратора
:: и запускает приложение

echo ========================================
echo Zapret Manager - Запуск с правами администратора
echo ========================================
echo.

:: Проверка наличия EXE файла
if exist "build\dist\ZapretManager.exe" (
    echo Запуск ZapretManager.exe...
    powershell -NoProfile -Command "Start-Process '%~dp0build\dist\ZapretManager.exe' -Verb RunAs"
) else if exist "src\main.py" (
    echo Запуск из исходников (Python)...
    powershell -NoProfile -Command "Start-Process 'python' -ArgumentList '%~dp0src\main.py' -Verb RunAs"
) else (
    echo ОШИБКА: Не найден ни ZapretManager.exe, ни src\main.py
    echo.
    echo Убедитесь что вы запускаете скрипт из корневой директории проекта.
    pause
    exit /b 1
)

echo.
echo Запрос прав администратора отправлен.
echo Подтвердите UAC запрос для продолжения.
echo.
timeout /t 3 >nul
