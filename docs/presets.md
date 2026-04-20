# Документация по пресетам Zapret Manager

Эта документация описывает, как устроены пресеты в этом проекте, как выбирать стратегию для новых сервисов и какие ограничения соблюдать, чтобы не затрагивать лишний трафик, особенно игровые UDP-порты.

## Где лежат пресеты

- `src/resources/presets/*.txt` - основные пресеты GUI/EXE-сборки.
- `presets/*.txt` - пресеты для старых bat-сценариев (`service.bat`, `zapret-console.bat`).
- `src/resources/config/current_preset.txt` - имя активного пресета GUI в dev-режиме, создается при первом запуске.
- `src/resources/config/preset-active.txt` - копия активного пресета GUI в dev-режиме, создается при первом запуске.
- `%TEMP%/ZapretManager/config/current_preset.txt` и `%TEMP%/ZapretManager/config/preset-active.txt` - активное состояние EXE-сборки.
- `utils/current_preset.txt` и `utils/preset-active.txt` - активное состояние старых bat-сценариев.

Приложение хранит именно имя последнего активного пресета и копирует его файл в `preset-active.txt`. При автозапуске используется эта копия, поэтому Task Scheduler не должен указывать конкретный пресет в аргументах.

## Автозапуск

Task Scheduler запускает Zapret Manager с аргументом `--autostart`.

Логика:

1. Приложение стартует.
2. `PresetManager` проверяет `current_preset.txt`.
3. Если активный пресет существует в каталоге пресетов, он синхронизируется в `preset-active.txt`.
4. В режиме `--autostart` tray автоматически вызывает запуск `winws2.exe`.
5. `winws2.exe` получает только `@preset-active.txt`, то есть всегда стартует последний активный пресет.

## Формат пресета

Пресет - обычный `.txt` файл с аргументами `winws2.exe`.

Рекомендуемый заголовок:

```txt
# Preset: Human readable name
# ActivePreset: Human readable name
# BuiltinVersion: 2.12
# Description: What this preset targets and what it deliberately avoids.
```

Минимальный каркас:

```txt
--lua-init=@lua/zapret-lib.lua
--lua-init=@lua/zapret-antidpi.lua
--lua-init=@lua/zapret-auto.lua
--lua-init=@lua/custom_funcs.lua
--lua-init=@lua/custom_diag.lua
--lua-init=@lua/zapret-multishake.lua

--ctrack-disable=0
--ipcache-lifetime=8400
--ipcache-hostname=1

--wf-tcp-out=80,443
--wf-udp-out=443

--filter-tcp=80,443
--hostlist=lists/example.txt
--out-range=-d8
--lua-desync=multisplit:pos=2,midsld-2:seqovl=1:seqovl_pattern=tls7
```

## Ключевые блоки

`--lua-init` подключает Lua-модули. Для новых пресетов обычно оставлять стандартный набор из основного пресета.

`--wf-tcp-out` и `--wf-udp-out` задают первичный WinDivert-захват. Это самый важный слой для безопасности. Не указывать широкие диапазоны вроде `--wf-udp-out=443-65535`, если цель - не трогать игры.

`--wf-raw-part` добавляет точный WinDivert-фильтр из файла. Использовать только если этот файл гарантированно входит в EXE-сборку и доступен из рабочей директории `winws2.exe`. Для переносимых пресетов лучше обходиться без внешних `windivert.filter`-файлов.

`--filter-tcp` / `--filter-udp` задают фильтр внутри `winws2.exe` для отдельного блока.

`--hostlist` ограничивает блок доменными списками. Это предпочтительный способ для HTTPS-сервисов.

`--ipset` ограничивает блок IP-сетями. Использовать только когда доменного списка недостаточно, например для QUIC/UDP или CDN.

`--hostlist-domains` подходит для коротких точечных правил без отдельного файла списка.

`--new` разделяет независимые блоки обработки. Каждый сервис или протокол лучше держать отдельным блоком, чтобы настройку можно было отключить или заменить без побочных эффектов.

## Правила создания безопасных пресетов

1. Начинать с минимального набора портов: TCP `80,443`, UDP `443`.
2. Добавлять нестандартные TCP-порты только для конкретного сервиса: например Discord через Cloudflare может использовать `2053,2083,2087,2096,8443`, Telegram Desktop может использовать `5222`.
3. Не использовать общий UDP `*`, `444-65535`, `443-65535`, `50000-65535`, если пользователь просит не трогать игры.
4. Для Discord voice не делать общий захват `50000-65535`; допустим узкий диапазон `50000-50099` вместе с `--filter-l7=stun,discord`.
5. Для YouTube QUIC использовать только UDP `443` и `lists/ipset-youtube.txt`.
6. Для Telegram начинать с TCP `80,443,5222`; UDP добавлять только точечно и после проверки.
7. Не добавлять catch-all блоки с `ipset-all`, `ipset-base`, `ipset-cloudflare`, если пресет должен затрагивать только Discord/YouTube/Telegram.
8. В каждом блоке должен быть ограничитель: `--hostlist`, `--hostlist-domains`, `--ipset` или точный `--filter-l7`.
9. Любой новый blob из `@bin/...` должен существовать и быть доступен и в dev, и в EXE-сборке.
10. После изменения пресета проверять, что он валиден, что все файлы списков существуют, и что игровые диапазоны UDP не попали в широкий захват.

## Основной пресет

`Default (Discord, YouTube, Telegram)` - основной пресет проекта.

Цели:

- Discord: вход, обновления, CDN/media, UDP 443, узкий voice discovery диапазон `50000-50099`.
- YouTube: HTTPS, `googlevideo.com`, QUIC UDP 443.
- Telegram: домены Telegram и IP-сети Telegram по TCP `80,443,5222`.

Ограничения:

- Нет общего UDP `443-65535`.
- Нет общего `ipset-all`.
- Нет общего захвата игровых UDP-портов.
- Discord voice обрабатывается через L7 payload на узком диапазоне `50000-50099`, а не через весь диапазон `50000-65535`.

## Дополнительные пресеты

`Discord Voice Focus` - только Discord. Использовать, когда нужно проверить Discord отдельно от YouTube/Telegram.

`YouTube Telegram Minimal` - только YouTube и Telegram. Использовать, если Discord voice не нужен или нужно снизить риск влияния на игры до минимума.

## Чеклист проверки пресета

Перед тем как считать пресет готовым:

1. Файл лежит в `src/resources/presets` и, если нужны bat-сценарии, продублирован в `presets`.
2. В заголовке есть `# Description:`.
3. `Validators.validate_preset_file()` возвращает `True`.
4. Все пути из `@lua/...`, `@bin/...`, `lists/...`, `windivert.filter/...` существуют.
5. Нет широких UDP-захватов, если пресет заявлен как не затрагивающий игры.
6. Нет catch-all блоков без hostlist/ipset/L7-ограничения.
7. Если пресет должен стать активным, обновлены `current_preset.txt` и `preset-active.txt` для нужного режима.
