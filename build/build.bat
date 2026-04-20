@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo ========================================
echo   Build Zapret Manager
echo ========================================
echo.

set "DIST_EXE=%CD%\dist\ZapretManager.exe"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

:: Check PyInstaller
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller not installed!
    echo Install: pip install pyinstaller
    pause
    exit /b 1
)

:: Guard against rebuilding over a running EXE
tasklist /FI "IMAGENAME eq ZapretManager.exe" 2>nul | find /I "ZapretManager.exe" >nul
if %errorlevel% equ 0 (
    echo [ERROR] ZapretManager.exe is currently running.
    echo Close the application from the tray or end all ZapretManager processes before building.
    echo.
    echo Hint:
    echo   taskkill /F /IM ZapretManager.exe
    echo.
    pause
    exit /b 1
)

:: Clean old files
echo [1/4] Cleaning old files...
if exist dist rmdir /s /q dist 2>nul
if exist build rmdir /s /q build 2>nul

if exist "%DIST_EXE%" (
    echo [ERROR] Failed to clean previous build output:
    echo   %DIST_EXE%
    echo The file is locked or access is denied.
    echo Close any running ZapretManager processes and try again.
    echo.
    pause
    exit /b 1
)

:: Build
echo [2/4] Building EXE...
pyinstaller zapret_manager.spec

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

:: File info
echo [3/4] Checking file...
for %%A in ("dist\ZapretManager.exe") do (
    set size=%%~zA
    set /a sizeMB=!size! / 1048576
    echo Size: !sizeMB! MB
)

echo [4/4] Done!
echo.
echo ========================================
echo   File created: dist\ZapretManager.exe
echo ========================================
echo.
echo To run: dist\ZapretManager.exe
echo (requires administrator rights)
echo.
pause
