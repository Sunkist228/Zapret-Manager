@echo off
:: Cleanup скрипт для Zapret Manager
::
:: Останавливает все процессы, очищает WinDivert сервисы и временные файлы

echo ========================================
echo Zapret Manager - Полная очистка
echo ========================================
echo.
echo Этот скрипт выполнит:
echo - Остановку всех процессов ZapretManager.exe и winws2.exe
echo - Очистку WinDivert сервисов
echo - Очистку временных файлов
echo.
pause

:: Проверка прав администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ОШИБКА: Требуются права администратора!
    echo Запустите этот скрипт правой кнопкой мыши -^> "Запуск от имени администратора"
    echo.
    pause
    exit /b 1
)

echo.
echo [1/4] Остановка процессов ZapretManager.exe...
taskkill /F /IM ZapretManager.exe >nul 2>&1
if %errorLevel% equ 0 (
    echo   ✓ ZapretManager.exe остановлен
) else (
    echo   - ZapretManager.exe не запущен
)

echo.
echo [2/4] Остановка процессов winws2.exe...
taskkill /F /IM winws2.exe >nul 2>&1
if %errorLevel% equ 0 (
    echo   ✓ winws2.exe остановлен
) else (
    echo   - winws2.exe не запущен
)

echo.
echo [3/4] Очистка WinDivert сервисов...

:: Останавливаем и удаляем WinDivert сервисы
for %%s in (WinDivert WinDivert14 Monkey Monkey14) do (
    sc query %%s >nul 2>&1
    if %errorLevel% equ 0 (
        echo   Остановка %%s...
        net stop %%s >nul 2>&1
        sc delete %%s >nul 2>&1
        echo   ✓ %%s удален
    )
)

echo   ✓ WinDivert сервисы очищены

echo.
echo [4/4] Очистка временных файлов...

:: Очистка QSharedMemory
if exist "%TEMP%\qipc_sharedmemory_ZapretManagerSingleInstance" (
    del /F /Q "%TEMP%\qipc_sharedmemory_ZapretManagerSingleInstance" >nul 2>&1
    echo   ✓ QSharedMemory очищен
)

:: Очистка логов (опционально)
set /p clear_logs="Очистить логи? (y/n): "
if /i "%clear_logs%"=="y" (
    if exist "%TEMP%\ZapretManager\app.log" (
        del /F /Q "%TEMP%\ZapretManager\app.log" >nul 2>&1
        echo   ✓ app.log удален
    )
    if exist "%TEMP%\ZapretManager\winws2.log" (
        del /F /Q "%TEMP%\ZapretManager\winws2.log" >nul 2>&1
        echo   ✓ winws2.log удален
    )
)

echo.
echo ========================================
echo ✓ Очистка завершена!
echo ========================================
echo.
echo Теперь вы можете запустить приложение заново.
echo.
pause
