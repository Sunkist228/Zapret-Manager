# Release Process

Этот документ описывает автоматический процесс релиза для Zapret Manager.

## Обзор

Zapret Manager использует **автоматическое версионирование** на основе [Conventional Commits](https://www.conventionalcommits.org/) и [Semantic Versioning](https://semver.org/).

**Ключевые особенности:**
- ✅ Автоматический bump версии при push в master
- ✅ Автоматическая генерация CHANGELOG
- ✅ Автоматическое создание GitHub Release
- ✅ Continuous Delivery: каждый merge в master → новый release

## Как это работает

### 1. Разработка

Создайте feature branch и делайте коммиты следуя формату Conventional Commits:

```bash
git checkout -b feature/telegram-proxy
git commit -m "feat: добавлена поддержка Telegram proxy"
git commit -m "fix(ui): исправлено отображение статуса"
git push origin feature/telegram-proxy
```

### 2. Pull Request

Создайте PR в master:

```bash
gh pr create --base master --title "feat: Telegram proxy support" --body "..."
```

CI проверит:
- Lint (flake8, black)
- Tests (pytest)
- Build (PyInstaller)

### 3. Merge в Master

После merge в master автоматически запускается Release workflow:

```
1. Анализ коммитов с последнего тега
   - feat: → minor bump (0.1.0 → 0.2.0)
   - fix: → patch bump (0.1.0 → 0.1.1)
   - BREAKING CHANGE: → major bump (0.1.0 → 1.0.0)

2. Обновление VERSION файла
   - scripts/bump_version.py

3. Генерация CHANGELOG.md
   - scripts/generate_changelog.py
   - Группировка по типам: Features, Bug Fixes, Breaking Changes

4. Commit изменений
   - git commit -m "chore: bump version to X.Y.Z"

5. Создание git tag
   - git tag vX.Y.Z

6. Push commit и tag
   - git push origin master
   - git push origin vX.Y.Z

7. Сборка EXE
   - build/build.bat
   - PyInstaller

8. Генерация SHA256
   - zapret-manager-windows-x64.exe.sha256

9. Создание GitHub Release
   - Tag: vX.Y.Z
   - Assets: EXE + SHA256
   - Release notes из CHANGELOG

10. (Опционально) Публикация в Artifact Server
    - Если настроены credentials
```

### 4. Автоматическое обновление пользователей

Update Manager в приложении:
1. Проверяет GitHub Releases API (primary)
2. Fallback на Artifact Server (если GitHub недоступен)
3. Уведомляет пользователя о новой версии
4. Скачивает и устанавливает обновление

## Типы коммитов и версионирование

| Тип коммита | Bump | Пример | Результат |
|-------------|------|--------|-----------|
| `feat:` | minor | 0.1.0 | 0.2.0 |
| `fix:` | patch | 0.1.0 | 0.1.1 |
| `feat!:` или `BREAKING CHANGE:` | major | 0.1.0 | 1.0.0 |
| `chore:`, `docs:`, `style:`, etc. | none | 0.1.0 | 0.1.0 (no release) |

## Ручной релиз

Если нужно создать релиз вручную (например, для hotfix):

### Через GitHub UI

1. Перейдите в Actions → Release
2. Нажмите "Run workflow"
3. Выберите bump type:
   - `auto` - автоматически определить из коммитов
   - `major` - принудительный major bump
   - `minor` - принудительный minor bump
   - `patch` - принудительный patch bump

### Через CLI

```bash
# Автоматический bump
gh workflow run release.yml

# Принудительный patch bump
gh workflow run release.yml -f bump_type=patch
```

## Hotfix процесс

Для срочных исправлений:

```bash
# 1. Создать hotfix branch
git checkout -b hotfix/critical-bug

# 2. Исправить баг
git commit -m "fix: критическое исправление безопасности"

# 3. Создать PR
gh pr create --base master --title "fix: critical security fix"

# 4. После merge автоматически создастся patch release
# 0.1.5 → 0.1.6
```

## Откат релиза

Если релиз содержит критическую ошибку:

### Вариант 1: Быстрый hotfix (рекомендуется)

```bash
# Исправить баг и создать новый релиз
git commit -m "fix: исправлена критическая ошибка из v0.2.0"
git push origin master
# Автоматически создастся v0.2.1
```

### Вариант 2: Удалить релиз (не рекомендуется)

```bash
# Удалить GitHub Release
gh release delete v0.2.0 --yes

# Удалить tag
git tag -d v0.2.0
git push origin :refs/tags/v0.2.0

# Откатить VERSION
echo "0.1.9" > VERSION
git commit -am "chore: revert version to 0.1.9"
git push origin master
```

## Проверка релиза

После создания релиза проверьте:

- [ ] GitHub Release создан: https://github.com/Sunkist228/zapret2/releases
- [ ] EXE файл прикреплен к релизу
- [ ] SHA256 файл прикреплен к релизу
- [ ] Release notes корректны
- [ ] VERSION файл обновлен
- [ ] CHANGELOG.md обновлен
- [ ] Git tag создан

## Мониторинг

### GitHub Actions

Проверить статус workflow:
```bash
gh run list --workflow=release.yml --limit 5
```

Посмотреть логи последнего run:
```bash
gh run view --log
```

### Update Manager

Проверить что Update Manager находит новую версию:
1. Запустить приложение
2. Открыть меню → "Проверить обновления"
3. Проверить логи в `%TEMP%\ZapretManager\logs\`

## Troubleshooting

### Release не создается после push в master

**Причина:** Нет коммитов с feat/fix типом

**Решение:** Убедитесь что коммиты следуют Conventional Commits формату

```bash
# Проверить коммиты с последнего тега
git log $(git describe --tags --abbrev=0)..HEAD --oneline

# Должны быть коммиты вида:
# feat: ...
# fix: ...
```

### Версия bump неправильная

**Причина:** Неправильный формат коммита

**Решение:** Проверьте формат коммитов:
- `feat:` → minor bump
- `fix:` → patch bump
- `feat!:` или `BREAKING CHANGE:` → major bump

### Update Manager не находит обновление

**Причина:** GitHub API rate limit или release не опубликован

**Решение:**
1. Проверить rate limit: https://api.github.com/rate_limit
2. Проверить что release не draft: https://github.com/Sunkist228/zapret2/releases
3. Проверить логи Update Manager

### Build failed

**Причина:** Ошибка в коде или зависимостях

**Решение:**
1. Проверить логи GitHub Actions
2. Запустить build локально: `cd build && .\build.bat`
3. Исправить ошибки и создать новый коммит

## Best Practices

1. **Используйте Conventional Commits** - это критично для автоматизации
2. **Тестируйте перед merge** - CI должен пройти успешно
3. **Пишите понятные commit messages** - они попадут в CHANGELOG
4. **Группируйте связанные изменения** - один PR = одна фича
5. **Не коммитьте напрямую в master** - используйте PR workflow
6. **Проверяйте релизы** - убедитесь что все работает после публикации

## Ссылки

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
