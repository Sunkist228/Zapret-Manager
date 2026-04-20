@echo off
setlocal
cd /d "%~dp0"

echo.
echo ========================================
echo   Build Zapret Manager EXE
echo ========================================
echo.
echo [i] Legacy ZapretTray build is deprecated.
echo [i] Building the current application from src\main.py via build\zapret_manager.spec
echo.

call "%~dp0build\build.bat"
exit /b %errorlevel%
