@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo ========================================
echo   Rebuild Zapret Manager
echo ========================================
echo.

set "SPEC_FILE=zapret_manager.spec"
set "WORK_DIR=build"
set "DIST_DIR=dist"
set "DIST_EXE=%CD%\%DIST_DIR%\ZapretManager.exe"

:: Clean everything
echo Cleaning old build files...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%" 2>nul
if exist "%WORK_DIR%" rmdir /s /q "%WORK_DIR%" 2>nul

:: Rebuild
echo Building EXE...
pyinstaller --clean --workpath "%WORK_DIR%" --distpath "%DIST_DIR%" "%SPEC_FILE%"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

:: Check result
if not exist "%DIST_EXE%" (
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
for %%A in ("%DIST_EXE%") do (
    set size=%%~zA
    set /a sizeMB=!size! / 1048576
    echo Size: !sizeMB! MB
)

echo.
echo Ready to test!
pause
