# Telegram proxy mode

`zapret` may not restore Telegram when an ISP blocks or throttles Telegram IP ranges directly.
For this case Zapret Manager can launch an optional local Telegram proxy helper, such as TG WS Proxy.

## Install helper

Place the proxy executable in one of these locations:

- `tools/telegram-proxy/tgwsproxy.exe`
- `tools/tgwsproxy.exe`
- `bin/tgwsproxy.exe`
- `exe/tgwsproxy.exe`

The manager also accepts a custom executable path through:

```powershell
$env:ZAPRET_TELEGRAM_PROXY_EXE = "C:\path\to\tgwsproxy.exe"
```

If the helper needs command-line arguments, set:

```powershell
$env:ZAPRET_TELEGRAM_PROXY_ARGS = "--your --args"
```

## Start

Open the tray menu:

`Telegram proxy -> Start local proxy`

The proxy log is written to:

`%TEMP%\ZapretManager\telegram-proxy.log`

## Configure Telegram Desktop

Open:

`Settings -> Advanced -> Connection type -> SOCKS5`

Use:

- Host: `127.0.0.1`
- Port: `1080`

If port `1080` does not work, try:

- Host: `127.0.0.1`
- Port: `1443`

## Notes

This mode is independent from `winws2.exe` presets. You can keep using zapret for YouTube/Discord
and route Telegram through the local proxy at the same time.
