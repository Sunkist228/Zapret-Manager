# Сборка

Zapret Manager собирается в один EXE через PyInstaller. Текущий контракт сборки используется GitHub Actions, Jenkins и тестами, поэтому пути output-файлов нужно менять только вместе со всеми проверками.

## Требования

- Windows.
- Python 3.8+.
- Зависимости из `requirements-dev.txt`.
- Tracked-ресурсы в `src/resources/*`, `bin/`, `lists/`, `presets/`, `lua/` и `windivert.filter/`.

## Локальная сборка

```bat
pip install -r requirements-dev.txt
cd build
build.bat
```

Ожидаемый результат:

```text
build\dist\ZapretManager.exe
```

## Что попадает в EXE

`build/zapret_manager.spec` включает:

- Python-точку входа `src/main.py`.
- `src/resources/presets`, `src/resources/lists`, `src/resources/lua`, `src/resources/bin`.
- Payload-файлы из корневого `bin/`.
- Фильтры из `windivert.filter/`.
- Файл `VERSION`.

## Перед изменением сборки

Запустите:

```bat
python -m pytest tests\test_release_paths.py -q
```

Если меняется путь артефакта, синхронно обновите:

- `build/build.bat`
- `build/zapret_manager.spec`
- `.github/workflows/release.yml`
- `Jenkinsfile`
- `tests/test_release_paths.py`
