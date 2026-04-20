# CI/CD и Jenkins

Проект использует GitHub Actions и Jenkins для проверки, сборки и публикации релизных артефактов.

## GitHub Actions

Основные workflow:

- `.github/workflows/ci.yml` - тесты и базовые проверки.
- `.github/workflows/release.yml` - сборка и публикация релиза.
- `.github/workflows/codeql.yml` - анализ безопасности.
- `.github/workflows/pr-governance.yml` - проверки Pull Request.

## Jenkins

Jenkins Pipeline описан в `Jenkinsfile`.

Ожидаемый build-output:

```text
build/dist/ZapretManager.exe
```

Не меняйте этот путь без синхронного обновления Jenkins, GitHub Actions и `tests/test_release_paths.py`.

## Версионирование

Версия продукта хранится в `VERSION`. Скрипты в `scripts/` используются для bump/changelog/publish задач:

- `scripts/bump_version.py`
- `scripts/generate_changelog.py`
- `scripts/publish_artifact.py`

## Перед релизными изменениями

Запустите:

```bat
python -m pytest tests\test_release_paths.py -q
python -m pytest tests -q
```

Если меняете release automation, проверьте также [docs/RELEASE_PROCESS.md](RELEASE_PROCESS.md).
