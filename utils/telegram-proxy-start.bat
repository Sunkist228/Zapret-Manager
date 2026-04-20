@echo off
setlocal

set "BASE_DIR=%~dp0.."
set "PROXY_EXE="

if defined ZAPRET_TELEGRAM_PROXY_EXE (
    if exist "%ZAPRET_TELEGRAM_PROXY_EXE%" set "PROXY_EXE=%ZAPRET_TELEGRAM_PROXY_EXE%"
)

if not defined PROXY_EXE if exist "%BASE_DIR%\tools\telegram-proxy\tgwsproxy.exe" set "PROXY_EXE=%BASE_DIR%\tools\telegram-proxy\tgwsproxy.exe"
if not defined PROXY_EXE if exist "%BASE_DIR%\tools\tgwsproxy.exe" set "PROXY_EXE=%BASE_DIR%\tools\tgwsproxy.exe"
if not defined PROXY_EXE if exist "%BASE_DIR%\bin\tgwsproxy.exe" set "PROXY_EXE=%BASE_DIR%\bin\tgwsproxy.exe"
if not defined PROXY_EXE if exist "%BASE_DIR%\exe\tgwsproxy.exe" set "PROXY_EXE=%BASE_DIR%\exe\tgwsproxy.exe"

if not defined PROXY_EXE (
    echo Telegram proxy executable not found.
    echo Put tgwsproxy.exe into tools\telegram-proxy or set ZAPRET_TELEGRAM_PROXY_EXE.
    exit /b 1
)

echo Starting Telegram proxy:
echo %PROXY_EXE%
start "Telegram proxy" /D "%~dp0.." "%PROXY_EXE%" %ZAPRET_TELEGRAM_PROXY_ARGS%
echo.
echo Configure Telegram Desktop as SOCKS5:
echo Host: 127.0.0.1
echo Port: 1080 or 1443
