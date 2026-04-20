# История изменений














## [1.0.12] - 2026-04-20

### Исправления

- match pyinstaller archive paths (d3847f2)


## [1.0.11] - 2026-04-20

### Исправления

- make release archive check unicode safe (fc602aa)


## [1.0.10] - 2026-04-20

### Исправления

- release bundled preset payloads (6675dbc)


## [1.0.9] - 2026-04-20

### Исправления

- restore tray menu encoding (00eb23f)


## [1.0.8] - 2026-04-20

### Исправления

- include winws2 build resource (7c719b3)


## [1.0.7] - 2026-04-20

### Исправления

- parse release bump version from stdout (ee2aaad)
- align release artifact paths (489fb19)


## [1.0.6] - 2026-04-20

### Исправления

- stabilize CI lint checks (9b38107)


## [1.0.5] - 2026-04-20

### Исправления

- add logger import to config.py (2394c13)


## [1.0.4] - 2026-04-20

### Исправления

- **build:** use DATA instead of BINARY for exe files in onefile mode (e919d0c)


## [1.0.3] - 2026-04-20

### Исправления

- **build:** add detailed logging and runtime hook for path diagnostics (a9bc637)


## [1.0.2] - 2026-04-20

### Исправления

- **build:** mark executables as BINARY in PyInstaller spec for proper extraction (f57406f)


## [1.0.1] - 2026-04-20

### Исправления

- improve path resolution in PyInstaller spec (7037372)


## [1.0.0] - 2026-04-20

### ⚠ КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ

- версия изменена с 1.0.0 на 0.1.1 для корректного semantic versioning (860e893)

### Новые функции

- initial release of zapret manager (a09c5b8)
- **ci:** switch language to russian and reset version to 0.1.0 (5a6c9c2)
- add PyInstaller build configuration and scripts (2a9b9f6)
- implement system tray with preset management and autostart (640ade5)
- implement core modules (zapret_manager, preset_manager, list_manager, autostart, privileges, diagnostics) (1ea39a5)

### Исправления

- correct PyInstaller paths for winws2.exe and reset version (2b9ee79)
- revert version to 0.1.0 and clean up changelog (ab4c5e6)
- **ci:** fix publish artifact step and avoid secret in if condition (99fa24d)
- **ci:** fix string interpolation for version in release.yml bash steps (1e3c604)
- **ci:** fix bash script string wrappers in release.yml (68bfe21)
- **ci:** fix build step and check dist directory (1785713)
- **ci:** fix check if exe exists in release.yml (134bdc4)
- **ci:** convert release.yml to run in bash (531a35d)
- **ci:** fix yaml pwsh variable interpolation in release.yml part 2 (b6565ef)
- **ci:** wrap string variables in release.yml (4e128ae)
- **ci:** fix yaml pwsh variable interpolation in release.yml (0abda44)
- **ci:** fix yaml string interpolation in release.yml (a962df6)
- **ci:** apply pwsh to all steps in release.yml (eeefe60)
- **ci:** fix pwsh yaml syntax in release.yml (160bd25)
- **ci:** fix yaml syntax in release.yml part 2 (e446ab7)
- **ci:** fix yaml syntax in release.yml (f5c2060)
- **scripts:** fix bump_version.py and set version to 0.1.0 (a0ac6cf)
- **scripts:** handle unicode in git log for Windows (e808e25)
- **ci:** correct build paths in workflows (f1eadbe)
- добавлен импорт Path и исправлен порядок определения cwd (d0575eb)
- исправлена работоспособность программы (v1.0.2) (053c1c5)
- correct imports for PyInstaller EXE execution (a270457)
- correct build.bat paths and finalize v1.0 (4769c94)
- correct imports for standalone execution (a7aadeb)


Все заметные изменения в этом проекте будут отражаться в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/),
и проект придерживается [Семантического версионирования](https://semver.org/lang/ru/).