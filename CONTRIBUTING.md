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

### Формат сообщения

```
type: short description

Optional longer description explaining what and why.
```

### Типы коммитов

- `feat` — новая функциональность
- `fix` — исправление бага
- `docs` — изменения в документации
- `refactor` — рефакторинг без изменения функциональности
- `test` — добавление или изменение тестов
- `chore` — рутинные задачи (обновление зависимостей, конфигурация)
- `ci` — изменения в CI/CD
- `build` — изменения в процессе сборки

### Примеры

```bash
feat: add auto-update functionality
fix: resolve tray icon crash on Windows 7
docs: update installation instructions
refactor: simplify preset loading logic
test: add tests for config manager
chore: update dependencies
ci: add GitHub Actions workflow for releases
```

### Плохие примеры

```bash
update
fix
WIP
changes
```

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

### Для мейнтейнеров

1. **Подготовка релиза**:
   ```bash
   # Bump версию
   python scripts/bump_version.py [major|minor|patch]
   
   # Обновите CHANGELOG.md
   # Добавьте release notes для новой версии
   ```

2. **Создание коммита и тега**:
   ```bash
   git add VERSION CHANGELOG.md
   git commit -m "chore: bump version to X.Y.Z"
   git tag vX.Y.Z
   ```

3. **Push**:
   ```bash
   git push origin master --tags
   ```

4. **Автоматическая публикация**:
   - GitHub Actions автоматически создаст release
   - Соберет Windows x64 EXE
   - Опубликует в GitHub Releases
   - Сгенерирует release notes

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
