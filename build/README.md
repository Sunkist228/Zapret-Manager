# Zapret Manager - Build Instructions

## Требования

- Python 3.8+
- PyQt5
- PyInstaller

## Установка зависимостей

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Сборка EXE

### Windows

```bash
cd build
build.bat
```

Готовый файл: `dist/ZapretManager.exe`

### Ручная сборка

```bash
cd build
pyinstaller zapret_manager.spec
```

## Тестирование

После сборки:

1. Запустите `dist/ZapretManager.exe` от имени администратора
2. Проверьте что иконка появилась в системном трее
3. Выберите пресет из меню
4. Нажмите "Включить"
5. Проверьте работу Discord/YouTube

## Размер файла

Ожидаемый размер: ~50-100 MB (включает все ресурсы)

## Проблемы

### "Не найден winws2.exe"

Убедитесь что файлы скопированы в `src/resources/bin/`:
- winws2.exe
- WinDivert.dll
- WinDivert32.sys
- WinDivert64.sys
- cygwin1.dll

### "Антивирус блокирует"

Добавьте в исключения или подпишите EXE сертификатом.

### "Медленный запуск"

PyInstaller распаковывает файлы во временную папку при каждом запуске (~3-5 сек).
Это нормально.
