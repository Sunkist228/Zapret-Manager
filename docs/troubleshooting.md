# Диагностика проблем

## Нужны права администратора

Zapret Manager работает с WinDivert и сетевым стеком Windows, поэтому требует запуск от администратора.

Решение:

```bat
run_as_admin.bat
```

Или запустите PowerShell/CMD от имени администратора и выполните:

```bat
python src\main.py
```

## Приложение уже запущено

Приложение использует single-instance lock. Если процесс завис, завершите `ZapretManager.exe` или `python.exe` через Task Manager и запустите снова.

## Не найден winws2.exe

Проверьте наличие файла:

```text
src\resources\bin\winws2.exe
```

Для EXE-сборки файл должен быть упакован в `resources\bin\winws2.exe`. Это проверяется тестом `tests/test_release_paths.py`.

## Zapret не стартует

Проверьте:

- Приложение запущено от администратора.
- Выбранный пресет существует.
- `WinDivert.dll`, `WinDivert32.sys`, `WinDivert64.sys` есть в `src/resources/bin`.
- Нет конфликтующих сервисов или других DPI bypass tools.

## Обновления не скачиваются

Проверьте доступ к:

- GitHub Releases.
- `https://artifact.devflux.ru`
- `https://update.devflux.ru`

Состояние обновлений хранится во временной директории пользователя, а не в tracked-ресурсах репозитория.
