# Contributing

Спасибо за интерес к проекту. Этот документ фиксирует короткий рабочий процесс для разработки Zapret Manager.

## Рабочий процесс

1. Создайте ветку от `master`.
2. Внесите минимально необходимые изменения.
3. Запустите релевантные тесты.
4. Откройте Pull Request в `master`.

```bash
git checkout master
git pull origin master
git checkout -b feature/short-name
```

## Коммиты

Используйте Conventional Commits:

```text
feat: add update check action
fix: keep bundled resources in frozen mode
docs: simplify repository docs
test: cover preset resource paths
chore: clean ignored artifacts
```

Типы:

- `feat` - новая возможность.
- `fix` - исправление ошибки.
- `docs` - документация.
- `test` - тесты.
- `build` - сборка, CI, release automation.
- `refactor` - изменение структуры без изменения поведения.
- `chore` - обслуживание репозитория.

## Тесты

Базовая проверка:

```bash
python -m pytest tests -q
```

Если pytest на локальном Python 3.14 падает при завершении capture, повторите без capture:

```bash
python -m pytest tests -q -s
```

Перед изменениями сборки обязательно проверьте:

```bash
python -m pytest tests/test_release_paths.py -q
```

Подробности: [docs/testing.md](docs/testing.md).

## Сборка

```bash
pip install -r requirements-dev.txt
cd build
build.bat
```

Ожидаемый результат: `build/dist/ZapretManager.exe`.

Подробности: [docs/build.md](docs/build.md).

## Pull Request checklist

- [ ] Тесты пройдены или причина пропуска описана.
- [ ] Для изменений сборки проверен `tests/test_release_paths.py`.
- [ ] Пользовательские строки и документы не содержат mojibake.
- [ ] Новые runtime-файлы не попали в git случайно.
- [ ] Риски и способ отката описаны в PR.

## Релизы

Процесс релиза описан в [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md). CI/CD и Jenkins описаны в [docs/ci-cd.md](docs/ci-cd.md).
