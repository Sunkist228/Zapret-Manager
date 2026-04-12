@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo   Rebuild Zapret Manager
echo ========================================
echo.

:: Clean everything
echo Cleaning old build files...
if exist dist rmdir /s /q dist 2>nul
if exist build rmdir /s /q build 2>nul

:: Rebuild
echo Building EXE...
pyinstaller --clean zapret_manager.spec

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

:: Check result
if not exist "dist\ZapretManager.exe" (
    echo.
    echo [ERROR] EXE file not created!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS! File: dist\ZapretManager.exe
echo ========================================
echo.

:: Show size
for %%A in ("dist\ZapretManager.exe") do (
    set size=%%~zA
    set /a sizeMB=!size! / 1048576
    echo Size: !sizeMB! MB
)

echo.
echo Ready to test!
pause
