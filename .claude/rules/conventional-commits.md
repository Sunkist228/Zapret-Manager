# Conventional Commits для Zapret Manager

## Обязательное правило для всех коммитов

Все коммиты в этом проекте ДОЛЖНЫ следовать формату Conventional Commits.
Это критично для автоматического версионирования и генерации CHANGELOG.

## Формат коммита

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Type (обязательно)

- **feat**: Новая функциональность (minor bump: 0.1.0 → 0.2.0)
- **fix**: Исправление бага (patch bump: 0.1.0 → 0.1.1)
- **docs**: Изменения в документации (no bump)
- **style**: Форматирование кода, без изменения логики (no bump)
- **refactor**: Рефакторинг без изменения функциональности (no bump)
- **perf**: Улучшение производительности (patch bump)
- **test**: Добавление или изменение тестов (no bump)
- **chore**: Обновление зависимостей, конфигурации (no bump)
- **build**: Изменения в системе сборки (no bump)
- **ci**: Изменения в CI/CD (no bump)

### Scope (опционально)

Область изменения: `ui`, `core`, `presets`, `update`, `build`, etc.

### Breaking Changes (major bump)

Для breaking changes используйте один из способов:

1. Восклицательный знак после type/scope:
```
feat!: переработан API конфигурации
```

2. Footer с BREAKING CHANGE:
```
feat: переработан API конфигурации

BREAKING CHANGE: изменен формат конфигурационных файлов
```

## Примеры

### Patch bump (0.1.0 → 0.1.1)
```
fix: исправлена ошибка в preset manager
fix(ui): исправлено отображение иконки в трее
fix(update): корректная проверка SHA256 при обновлении
```

### Minor bump (0.1.0 → 0.2.0)
```
feat: добавлена поддержка Telegram proxy
feat(presets): новый пресет для Discord Voice
feat(ui): добавлено контекстное меню в трее
```

### Major bump (0.1.0 → 1.0.0)
```
feat!: переработан API конфигурации

BREAKING CHANGE: изменен формат конфигурационных файлов.
Старые конфигурации несовместимы с новой версией.
```

### Без bump (версия не меняется)
```
chore: обновлены зависимости
docs: обновлен README
style: форматирование кода
refactor: рефакторинг без изменения API
test: добавлены тесты для update manager
ci: обновлен GitHub Actions workflow
```

## Автоматический релиз

При push в master:
1. Анализируются все коммиты с последнего тега
2. Определяется тип bump (major/minor/patch)
3. Обновляется VERSION файл
4. Генерируется CHANGELOG.md
5. Создается commit и tag
6. Собирается EXE
7. Публикуется GitHub Release

## Проверка перед коммитом

Перед коммитом убедитесь:
- [ ] Коммит следует формату conventional commits
- [ ] Type выбран правильно (feat/fix/chore/etc.)
- [ ] Description понятно описывает изменение
- [ ] Если breaking change - добавлен BREAKING CHANGE footer

## Инструменты

Для проверки формата коммитов можно использовать:
```bash
# Проверить последний коммит
git log -1 --pretty=%B

# Проверить все коммиты с последнего тега
git log $(git describe --tags --abbrev=0)..HEAD --oneline
```

## Ссылки

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
