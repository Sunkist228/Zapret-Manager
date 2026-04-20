# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-04-20

### Added
- **CI/CD**: Автоматическое версионирование на основе conventional commits
- **CI/CD**: Автоматическая генерация CHANGELOG из git commits
- **CI/CD**: Автоматический релиз при push в master через GitHub Actions
- **Update**: Поддержка GitHub Releases API как primary источника обновлений
- **Update**: Fallback на artifact server при недоступности GitHub
- **Docs**: docs/RELEASE_PROCESS.md с полным описанием процесса релиза
- **Docs**: .claude/rules/conventional-commits.md с правилами для коммитов
- **Scripts**: scripts/bump_version.py для автоматического определения версии
- **Scripts**: scripts/generate_changelog.py для генерации changelog

### Changed
- Переработан .github/workflows/release.yml для автоматического релиза
- Обновлен src/utils/config.py с константами для GitHub API
- Обновлен src/core/update_manager.py с поддержкой GitHub Releases
- Обновлен CONTRIBUTING.md с информацией о conventional commits
- Обновлен README.md с секцией про автоматические обновления
- Версия изменена с 1.0.0 на 0.1.1 для корректного semantic versioning

### Infrastructure
- GitHub Releases как primary источник обновлений
- Artifact Server как fallback источник
- Continuous Delivery: каждый merge в master создает новый release

## [1.0.0] - 2026-04-12

Initial release with CI/CD infrastructure.

### Features
- Windows desktop application for bypassing network blocks
- System tray GUI with preset management
- 70+ ready-to-use presets for Discord, YouTube, etc.
- Domain and IP list editor
- Automatic diagnostics and problem fixing
- Real-time logs viewer
- Auto-start with Windows (with admin rights)
- Standalone EXE with all dependencies bundled

### Technical
- Python 3.12+ with PyQt6
- PyInstaller for EXE compilation
- WinDivert for packet manipulation
- Requires administrator privileges

[Unreleased]: https://github.com/Sunkist228/zapret2/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Sunkist228/zapret2/releases/tag/v1.0.0
