# Zapret Manager

[![CI](https://github.com/Sunkist228/zapret2/actions/workflows/ci.yml/badge.svg)](https://github.com/Sunkist228/zapret2/actions/workflows/ci.yml)
[![Release](https://github.com/Sunkist228/zapret2/actions/workflows/release.yml/badge.svg)](https://github.com/Sunkist228/zapret2/actions/workflows/release.yml)
[![Version](https://img.shields.io/github/v/release/Sunkist228/zapret2)](https://github.com/Sunkist228/zapret2/releases/latest)

Zapret Manager - Windows-приложение для управления `winws2.exe` из zapret2 через системный трей. Оно помогает запускать и останавливать zapret, переключать пресеты, вести логи, настраивать автозапуск и проверять обновления.

## Возможности

- Управление zapret из системного трея.
- Выбор готовых пресетов для Discord, YouTube, Telegram и игровых сценариев.
- Работа со списками доменов и IP-адресов.
- Автозапуск через планировщик Windows.
- Проверка обновлений через GitHub Releases и fallback-серверы.
- Сборка автономного `ZapretManager.exe` через PyInstaller.

## Быстрый старт

Требования:

- Windows 7 / 8 / 10 / 11.
- Права администратора.
- Python 3.8+ для запуска из исходников.

Запуск из исходников:

```bat
pip install -r requirements.txt
run_as_admin.bat
```

Ручной запуск из консоли администратора:

```bat
python src\main.py
```

Готовую сборку можно скачать на странице [Releases](../../releases/latest).

## Сборка EXE

```bat
pip install -r requirements-dev.txt
cd build
build.bat
```

Результат сборки: `build\dist\ZapretManager.exe`.

Подробности: [docs/build.md](docs/build.md).

## Использование

После запуска приложение появляется в системном трее.

- Двойной клик по иконке включает или выключает zapret.
- Правый клик открывает меню управления.
- В меню `Пресеты` можно выбрать активную конфигурацию.
- В меню автозапуска можно включить старт вместе с Windows.

Если приложение сообщает о нехватке прав, перезапустите его через `run_as_admin.bat` или из консоли администратора.

## Структура репозитория

```text
src/                  исходный код приложения
src/resources/        ресурсы, которые попадают в EXE
bin/                  payload-файлы zapret для сборки
lists/                списки для bat/runtime-дерева
presets/              пресеты для bat/runtime-дерева
lua/                  Lua-скрипты zapret
build/                PyInstaller spec и bat-скрипты сборки
docs/                 подробная документация
tests/                pytest-тесты
```

Важно: корневые `bin/`, `lists/`, `presets/`, `lua/` и `src/resources/*` выглядят похожими, но сейчас участвуют в разных сценариях запуска и сборки. Не удаляйте их без обновления тестов и build-контракта.

## Документация

- [Полная документация](DOCUMENTATION.md)
- [Сборка](docs/build.md)
- [Тестирование](docs/testing.md)
- [Диагностика проблем](docs/troubleshooting.md)
- [CI/CD и Jenkins](docs/ci-cd.md)
- [Процесс релиза](docs/RELEASE_PROCESS.md)
- [Пресеты](docs/presets.md)
- [Telegram proxy](docs/telegram-proxy.md)
- [Update server](docs/update-server.md)
- [Contributing](CONTRIBUTING.md)

## Разработка

```bat
pip install -r requirements-dev.txt
python -m pytest tests -q
```

Перед изменениями в сборке проверьте:

```bat
python -m pytest tests\test_release_paths.py -q
```

## Лицензия

Проект распространяется на условиях лицензии репозитория.
