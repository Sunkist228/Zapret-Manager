# Тестирование

## Базовый запуск

```bat
python -m pytest tests -q
```

Если локальный Python/pytest падает при завершении capture, повторите без capture:

```bat
python -m pytest tests -q -s
```

## Важные группы тестов

- `tests/test_release_paths.py` - контракт сборки, CI и PyInstaller resources.
- `tests/test_encoding.py` - защита от mojibake в коде и документации.
- `tests/test_update_manager.py` - update flow, fallback endpoints и checksum.
- `tests/test_telegram_support.py` - наличие Telegram lists/presets в runtime-деревьях.

## Когда добавлять тесты

Добавляйте или обновляйте тесты, если изменение затрагивает:

- Пути ресурсов.
- Сборку EXE.
- Пресеты или списки.
- Автообновление.
- Пользовательские строки.
- Поведение запуска, остановки или автозапуска.
