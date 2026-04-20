# Zapret Manager: документация

Эта страница служит оглавлением и кратким техническим описанием проекта. Практические инструкции вынесены в `docs/`, чтобы корень репозитория оставался компактным.

## Что делает приложение

Zapret Manager запускает `winws2.exe`, передает ему выбранный пресет, следит за состоянием процесса и предоставляет управление через системный трей PyQt5.

Основные подсистемы:

- `src/main.py` - точка входа и проверка прав администратора.
- `src/gui/tray_icon.py` - меню трея, уведомления и пользовательские действия.
- `src/core/zapret_manager.py` - запуск, остановка и перезапуск `winws2.exe`.
- `src/core/preset_manager.py` - поиск и выбор пресетов.
- `src/core/update_manager.py` - проверка и загрузка обновлений.
- `src/core/autostart.py` - настройка автозапуска через Windows Task Scheduler.
- `src/utils/config.py` - пути, версия, update-настройки и runtime-константы.

## Ресурсы

В репозитории есть несколько деревьев ресурсов:

- `src/resources/*` - ресурсы, которые приложение использует при запуске из исходников и которые упаковываются в EXE.
- `bin/`, `lists/`, `presets/`, `lua/` - runtime/payload-деревья для zapret и bat-сценариев.
- `windivert.filter/` - фильтры WinDivert.

Эти директории нельзя считать случайными дублями. Текущий PyInstaller spec и тесты проверяют, что нужные файлы остаются на местах.

## Основные сценарии

- Запуск из исходников: см. [README.md](README.md).
- Сборка EXE: см. [docs/build.md](docs/build.md).
- Тестирование: см. [docs/testing.md](docs/testing.md).
- Диагностика проблем: см. [docs/troubleshooting.md](docs/troubleshooting.md).
- CI/CD и Jenkins: см. [docs/ci-cd.md](docs/ci-cd.md).
- Релизы: см. [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md).
- Пресеты: см. [docs/presets.md](docs/presets.md).

## Минимальные правила изменений

- Не менять build-output контракт без обновления `.github/workflows/release.yml`, `Jenkinsfile`, `build/build.bat` и `tests/test_release_paths.py`.
- Не удалять resource-деревья только потому, что их содержимое похоже.
- Пользовательские строки и документация должны храниться в UTF-8 без mojibake.
- Runtime-конфиг, состояние обновлений и активный пресет должны оставаться в mutable-директориях, а не в tracked-ресурсах.
