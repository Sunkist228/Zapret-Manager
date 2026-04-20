# Jenkins Setup Instructions

## Репозиторий настроен

✅ GitHub репозиторий: https://github.com/Sunkist228/zapret2
✅ Код запушен в master
✅ GitHub webhook настроен: https://jenkins.devflux.ru/github-webhook/

## Настройка Jenkins Job

### 1. Создать Multibranch Pipeline

В Jenkins UI (https://jenkins.devflux.ru):

1. **New Item** → введите имя `zapret2` → выберите **Multibranch Pipeline** → OK

2. **Branch Sources** → Add source → **GitHub**:
   - Credentials: выберите существующий GitHub credential или создайте новый
   - Repository HTTPS URL: `https://github.com/Sunkist228/zapret2`
   - Behaviors: 
     - Discover branches (All branches)
     - Discover pull requests from origin (Merging the pull request with the current target branch revision)

3. **Build Configuration**:
   - Mode: by Jenkinsfile
   - Script Path: `Jenkinsfile`

4. **Scan Multibranch Pipeline Triggers**:
   - ✅ Periodically if not otherwise run
   - Interval: 1 hour

5. **Orphaned Item Strategy**:
   - Discard old items
   - Days to keep old items: 7
   - Max # of old items to keep: 10

### 2. Добавить Credentials

В Jenkins → Manage Jenkins → Credentials → (global):

#### GitHub Credential (если еще нет)
- Kind: Username with password
- Username: Sunkist228
- Password: [GitHub Personal Access Token]
- ID: `GitHub`
- Description: GitHub Access Token

#### Artifact Server Credentials

**Dev Environment:**
- Kind: Secret text
- Secret: [API Key для dev]
- ID: `ARTIFACT_SERVER_API_KEY_DEV`
- Description: Artifact Server API Key (Dev)

**Prod Environment:**
- Kind: Secret text
- Secret: [API Key для prod]
- ID: `ARTIFACT_SERVER_API_KEY_PROD`
- Description: Artifact Server API Key (Prod)

**Artifact Server URL:**
- Kind: Secret text
- Secret: https://artifacts.devflux.ru (или ваш URL)
- ID: `ARTIFACT_SERVER_URL`
- Description: Artifact Server URL

### 3. Настроить Windows Agent

Убедитесь, что Windows agent с label `windows` доступен и имеет:
- Python 3.12+
- PyInstaller
- Git
- Доступ к интернету для pip install

### 4. Первый запуск

После создания job:
1. Jenkins автоматически просканирует репозиторий
2. Найдет ветку `master` с Jenkinsfile
3. Запустит первый build

Или запустите вручную: **Scan Multibranch Pipeline Now**

## Проверка работы

### GitHub Actions
Проверьте: https://github.com/Sunkist228/zapret2/actions

Должны быть workflows:
- CI (запускается на PR и push)
- PR Governance (запускается на открытие PR)
- Release (запускается на push тега v*)

### Jenkins
После первого build проверьте:
- Build прошел успешно
- Артефакты заархивированы (dist/ZapretManager.exe)
- JUnit тесты опубликованы

### Webhook
Проверьте webhook: https://github.com/Sunkist228/zapret2/settings/hooks

Должен быть webhook на `https://jenkins.devflux.ru/github-webhook/`
- Events: push, pull_request
- Active: ✅

## Тестирование

### 1. Тест PR workflow
```bash
git checkout -b feature/test-ci-cd
echo "# Test" >> README.md
git add README.md
git commit -m "test: verify CI/CD pipeline"
git push origin feature/test-ci-cd
gh pr create --base master --title "test: verify CI/CD" --body "Testing CI/CD pipeline"
```

Проверьте:
- GitHub Actions запустились
- Jenkins НЕ запустился (feature ветки не деплоятся)
- PR можно смержить после прохождения CI

### 2. Тест master build
После merge PR в master:
- Jenkins должен автоматически запуститься
- Собрать EXE
- Опубликовать в Artifact Server (stable channel)

### 3. Тест release
```bash
python scripts/bump_version.py patch
git add VERSION CHANGELOG.md
git commit -m "chore: bump version to 1.0.1"
git tag v1.0.1
git push origin master --tags
```

Проверьте:
- GitHub Actions создал release
- EXE опубликован в GitHub Releases
- Release notes сгенерированы

## Troubleshooting

### Jenkins не запускается
- Проверьте webhook в GitHub: Settings → Webhooks → Recent Deliveries
- Проверьте Jenkins logs
- Убедитесь, что GitHub credential настроен правильно

### Build падает на Windows agent
- Проверьте Python версию: `python --version` (должна быть 3.12+)
- Проверьте PyInstaller: `pip show pyinstaller`
- Проверьте логи Jenkins build

### Artifact Server недоступен
- Проверьте credentials в Jenkins
- Проверьте URL artifact server
- Build продолжится, но публикация будет пропущена (WARNING)

## Полезные команды

```bash
# Проверить статус GitHub Actions
gh run list --limit 5

# Проверить webhook deliveries
gh api repos/Sunkist228/zapret2/hooks --jq '.[].config.url'

# Создать тестовый PR
gh pr create --base master --title "test: ..." --body "..."

# Создать release
git tag v1.0.1 && git push origin --tags
```

## Документация

- GitHub Actions workflows: `.github/workflows/`
- Jenkins pipeline: `Jenkinsfile`
- AI rules: `.claude/rules/`
- Contributing: `CONTRIBUTING.md`
- Changelog: `CHANGELOG.md`
