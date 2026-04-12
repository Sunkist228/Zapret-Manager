# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CI/CD pipeline with GitHub Actions and Jenkins
- Automated releases via GitHub Releases
- Comprehensive AI rules for development (.claude/rules/)
- Version management script (scripts/bump_version.py)
- Artifact publishing script (scripts/publish_artifact.py)
- Contributing guidelines (CONTRIBUTING.md)
- Git workflow with feature branches
- Commit standards enforcement

### Changed
- Adopted Semantic Versioning with VERSION file
- Improved build process documentation
- Enhanced .gitignore with CI/CD patterns

### Infrastructure
- GitHub Actions workflows: CI, PR governance, releases
- Jenkins multibranch pipeline for delivery
- Integration with Playerok Artifact Server

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
