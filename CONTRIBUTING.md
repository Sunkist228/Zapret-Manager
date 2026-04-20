# Contributing to zapret2

Спасибо за интерес к проекту! Это руководство поможет вам начать разработку.

## Оглавление

- [Git Workflow](#git-workflow)
- [Commit Standards](#commit-standards)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Building](#building)
- [Release Process](#release-process)

## Git Workflow

### 1. Создание ветки

Всегда создавайте отдельную ветку для своей работы:

```bash
git checkout master
git pull origin master
git checkout -b feature/your-feature-name
```

Типы веток:
- `feature/` — новая функциональность
- `fix/` — исправление багов
- `refactor/` — рефакторинг кода
- `docs/` — изменения в документации

### 2. Разработка

- Следуйте [Commit Standards](#commit-standards)
- Пишите тесты для нового кода
- Проверяйте сборку локально перед push

### 3. Pull Request

1. Push вашей ветки: `git push origin feature/your-feature-name`
2. Создайте PR в `master`
3. Дождитесь прохождения CI (GitHub Actions)
4. Запросите review (если применимо)
5. После одобрения PR будет смержен

**Не работайте напрямую в ветке `master`!**

## Commit Standards

Проект использует **[Conventional Commits](https://www.conventionalcommits.org/)** для автоматического версионирования и генерации CHANGELOG.

### Формат сообщения

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Типы коммитов и версионирование

| Тип | Bump | Описание | Пример |
|-----|------|----------|--------|
| `feat` | minor | Новая функциональность | `feat: add Telegram proxy support` |
| `fix` | patch | Исправление бага | `fix: resolve tray icon crash` |
| `feat!` или `BREAKING CHANGE:` | major | Breaking changes | `feat!: redesign config API` |
| `docs` | none | Изменения в документации | `docs: update README` |
| `refactor` | none | Рефакторинг без изменения API | `refactor: simplify preset loading` |
| `test` | none | Добавление тестов | `test: add config manager tests` |
| `chore` | none | Рутинные задачи | `chore: update dependencies` |
| `ci` | none | Изменения в CI/CD | `ci: add release workflow` |
| `build` | none | Изменения в сборке | `build: update PyInstaller config` |

### Примеры

**Хорошие примеры:**
```bash
feat: добавлена поддержка Telegram proxy
feat(ui): добавлено контекстное меню в трее
fix: исправлена ошибка в preset manager
fix(update): корректная проверка SHA256
docs: обновлен README с инструкциями
chore: обновлены зависимости до последних версий
```

**Breaking changes:**
```bash
feat!: переработан API конфигурации

BREAKING CHANGE: изменен формат конфигурационных файлов.
Старые конфигурации несовместимы с новой версией.
```

**Плохие примеры:**
```bash
update           # Нет типа и описания
fix              # Нет описания
WIP              # Не информативно
changes          # Слишком общее
```

### Scope (опционально)

Область изменения: `ui`, `core`, `presets`, `update`, `build`, etc.

```bash
feat(ui): добавлено контекстное меню
fix(core): исправлена утечка памяти
docs(api): обновлена документация API
```

### Проверка формата

Перед коммитом проверьте формат:
```bash
# Проверить последний коммит
git log -1 --pretty=%B

# Проверить все коммиты с последнего тега
git log $(git describe --tags --abbrev=0)..HEAD --oneline
```

**Важно:** Формат коммитов критичен для автоматического релиза!

## Pull Request Process

### Перед созданием PR

- [ ] Все тесты проходят локально
- [ ] Код собирается без ошибок
- [ ] EXE собирается успешно (для Windows builds)
- [ ] Нет конфликтов с `master`
- [ ] Commit messages следуют стандартам

### Шаблон PR

При создании PR используйте шаблон:

```markdown
## Кратко
- Что изменилось?
- Зачем нужно это изменение?

## Проверка
- [ ] Тесты прошли
- [ ] Сборка EXE успешна
- [ ] Ручная проверка выполнена

## Риск / Откат
- Уровень риска: низкий/средний/высокий
- План отката: как откатить изменения при проблемах
```

### CI/CD Checks

GitHub Actions автоматически проверит:
- Линтинг (flake8, black, mypy)
- Тесты (pytest с coverage)
- Тестовую сборку EXE

Все проверки должны пройти перед merge.

## Testing

### Установка зависимостей

```bash
# Основные зависимости
pip install -r requirements.txt

# Зависимости для разработки
pip install -r requirements-dev.txt
```

### Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# С coverage
pytest tests/ --cov=src --cov-report=html

# Конкретный тест
pytest tests/test_preset_manager.py -v
```

### Линтинг

```bash
# Проверка стиля
flake8 src/ tests/

# Форматирование
black src/ tests/

# Проверка типов
mypy src/
```

## Building

### Локальная сборка EXE

```bash
cd build
build.bat
```

Результат: `dist/ZapretManager.exe`

### Требования

- Python 3.12+
- PyInstaller
- Все зависимости из `requirements.txt`

### Проверка сборки

```bash
# Запуск собранного EXE (требует admin права)
dist\ZapretManager.exe
```

## Release Process

### Автоматический релиз (рекомендуется)

Проект использует **автоматическое версионирование** на основе Conventional Commits.

**Как это работает:**
1. Вы создаете PR с коммитами в формате Conventional Commits
2. После merge в `master` автоматически:
   - Анализируются коммиты с последнего тега
   - Определяется тип bump (major/minor/patch)
   - Обновляется VERSION файл
   - Генерируется CHANGELOG.md
   - Создается commit и git tag
   - Собирается EXE
   - Публикуется GitHub Release

**Примеры:**
```bash
# После merge PR с feat: коммитом
# 0.1.0 → 0.2.0 (minor bump)

# После merge PR с fix: коммитом
# 0.1.0 → 0.1.1 (patch bump)

# После merge PR с BREAKING CHANGE:
# 0.1.0 → 1.0.0 (major bump)
```

### Ручной релиз

Если нужно создать релиз вручную:

**Через GitHub UI:**
1. Перейдите в Actions → Release
2. Нажмите "Run workflow"
3. Выберите bump type (auto/major/minor/patch)

**Через CLI:**
```bash
# Автоматический bump
gh workflow run release.yml

# Принудительный patch bump
gh workflow run release.yml -f bump_type=patch
```

### Для мейнтейнеров (legacy)

Если автоматический релиз не работает, можно создать релиз вручную:

```bash
# 1. Bump версию
python scripts/bump_version.py --type patch

# 2. Генерация CHANGELOG
python scripts/generate_changelog.py

# 3. Commit и tag
git add VERSION CHANGELOG.md
git commit -m "chore: bump version to X.Y.Z"
git tag vX.Y.Z

# 4. Push
git push origin master --tags
```

### Подробности

См. [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md) для полной документации процесса релиза.

### Versioning

Проект использует [Semantic Versioning](https://semver.org/):

- **Major** (X.0.0) — breaking changes, крупные изменения
- **Minor** (x.Y.0) — новая функциональность, обратно совместимая
- **Patch** (x.y.Z) — исправления багов, мелкие улучшения

## Code Style

- Следуйте PEP 8
- Используйте type hints где возможно
- Документируйте публичные функции и классы
- Максимальная длина строки: 100 символов

## Questions?

- Создайте [Issue](../../issues) с вопросом
- Проверьте [документацию](docs/)
- Изучите [AI правила](.claude/rules/) для понимания workflow

## License

Проект распространяется под лицензией MIT. См. [LICENSE](LICENSE).
