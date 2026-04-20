@echo off
setlocal

for %%P in (
    tgwsproxy.exe
    tg-ws-proxy.exe
    tg_ws_proxy.exe
    telegram-ws-proxy.exe
    TelegramWsProxy.exe
) do (
    taskkill /F /IM %%P >nul 2>nul
)

echo Telegram proxy stop command sent.
