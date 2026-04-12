# Zapret Manager - Полная документация

## Содержание

1. [Обзор проекта](#обзор-проекта)
2. [Архитектура](#архитектура)
3. [Установка и запуск](#установка-и-запуск)
4. [Компоненты системы](#компоненты-системы)
5. [Работа с пресетами](#работа-с-пресетами)
6. [API и интеграция](#api-и-интеграция)
7. [Сборка и развертывание](#сборка-и-развертывание)
8. [Решение проблем](#решение-проблем)
9. [Разработка](#разработка)

---

## Обзор проекта

### Что это?

Zapret Manager - это полноценное GUI-приложение для управления [zapret2](https://github.com/bol-van/zapret2) - системой обхода блокировок Discord, YouTube и других сервисов в России.

### Ключевые особенности

- **Системный трей** - управление через иконку в трее
- **70+ пресетов** - готовые конфигурации для разных провайдеров
- **Автозапуск** - запуск вместе с Windows с правами администратора
- **Диагностика** - автоматическая проверка и исправление проблем
- **Логирование** - детальные логи для отладки
- **Автономность** - все файлы упакованы в один EXE

### Технологии

- **Python 3.8+** - основной язык
- **PyQt5** - GUI фреймворк
- **PyInstaller** - сборка в EXE
- **winws2.exe** - движок обхода блокировок (zapret2)
- **WinDivert** - драйвер перехвата пакетов

---

## Архитектура

### Структура проекта

```
zapret2/
├── src/                          # Исходный код
│   ├── main.py                   # Точка входа приложения
│   ├── core/                     # Бизнес-логика
│   │   ├── zapret_manager.py     # Управление процессом winws2.exe
│   │   ├── preset_manager.py     # Управление пресетами
│   │   ├── list_manager.py       # Управление списками доменов/IP
│   │   ├── autostart.py          # Автозапуск с Windows
│   │   ├── diagnostics.py        # Диагностика системы
│   │   └── privileges.py         # Проверка прав администратора
│   ├── gui/                      # Графический интерфейс
│   │   ├── tray_icon.py          # Системный трей
│   │   └── main_window.py        # Главное окно (в разработке)
│   ├── utils/                    # Утилиты
│   │   ├── config.py             # Конфигурация приложения
│   │   ├── logger.py             # Логирование
│   │   └── validators.py         # Валидация данных
│   └── resources/                # Ресурсы
│       ├── bin/                  # Исполняемые файлы
│       │   ├── winws2.exe        # Движок zapret2
│       │   └── WinDivert*.dll    # Драйвер WinDivert
│       ├── presets/              # Конфигурационные пресеты
│       ├── lists/                # Списки доменов и IP
│       └── lua/                  # Lua-скрипты для winws2
├── build/                        # Сборка EXE
│   ├── build.bat                 # Скрипт сборки
│   └── ZapretManager.spec        # Конфигурация PyInstaller
├── tests/                        # Тесты
├── requirements.txt              # Зависимости для runtime
├── requirements-dev.txt          # Зависимости для разработки
└── README.md                     # Основная документация

```

### Диаграмма компонентов

```
┌─────────────────────────────────────────────────────────┐
│                    Zapret Manager                        │
│                                                          │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────┐     │
│  │ Tray Icon  │  │ Main Window  │  │   Logger    │     │
│  │  (PyQt5)   │  │   (PyQt5)    │  │             │     │
│  └─────┬──────┘  └──────┬───────┘  └──────┬──────┘     │
│        │                │                  │            │
│        └────────────────┴──────────────────┘            │
│                         │                               │
│        ┌────────────────┴────────────────┐              │
│        │                                 │              │
│  ┌─────▼──────┐  ┌──────────────┐  ┌───▼──────┐       │
│  │  Zapret    │  │   Preset     │  │ Autostart│       │
│  │  Manager   │  │   Manager    │  │ Manager  │       │
│  └─────┬──────┘  └──────┬───────┘  └──────────┘       │
│        │                │                               │
│        └────────────────┘                               │
│                 │                                       │
└─────────────────┼───────────────────────────────────────┘
                  │
         ┌────────▼────────┐
         │   winws2.exe    │
         │   (zapret2)     │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │   WinDivert     │
         │   (driver)      │
         └─────────────────┘
                  │
         ┌────────▼────────┐
         │  Network Stack  │
         │   (Windows)     │
         └─────────────────┘
```

### Поток данных

1. **Пользователь** → Клик по иконке в трее
2. **Tray Icon** → Вызов метода `ZapretManager.start()`
3. **ZapretManager** → Запуск `winws2.exe` с активным пресетом
4. **winws2.exe** → Загрузка Lua-скриптов и списков доменов
5. **WinDivert** → Перехват сетевых пакетов
6. **winws2.exe** → Модификация пакетов согласно пресету
7. **Network Stack** → Отправка модифицированных пакетов

---

## Установка и запуск

### Системные требования

- **ОС**: Windows 7 / 8 / 10 / 11 (32-bit или 64-bit)
- **Права**: Администратор (обязательно!)
- **Место**: 100 MB свободного места
- **Python**: 3.8+ (только для запуска из исходников)

### Вариант 1: Готовый EXE (рекомендуется)

```bash
# 1. Скачайте ZapretManager.exe из Releases
# 2. Запустите с правами администратора
run_as_admin.bat
```

### Вариант 2: Из исходников

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/yourusername/zapret2.git
cd zapret2

# 2. Установите зависимости
pip install -r requirements.txt

# 3. Запустите с правами администратора
run_as_admin.bat
# ИЛИ
python src/main.py  # (правой кнопкой → "Запуск от имени администратора")
```

### Вариант 3: Сборка EXE

```bash
# 1. Установите зависимости для разработки
pip install -r requirements-dev.txt

# 2. Соберите EXE
cd build
build.bat

# 3. Запустите
cd ..
run_as_admin.bat
```

---

## Компоненты системы

### 1. ZapretManager (`core/zapret_manager.py`)

Управление процессом winws2.exe.

**Основные методы:**

```python
class ZapretManager:
    def is_running(self) -> bool:
        """Проверка запущен ли winws2.exe"""
        
    def start(self) -> bool:
        """Запуск winws2.exe с текущим пресетом"""
        
    def stop(self) -> bool:
        """Остановка winws2.exe"""
        
    def restart(self) -> bool:
        """Перезапуск winws2.exe"""
        
    def get_status(self) -> Dict:
        """Получить статус: running, pid, uptime, preset"""
```

**Алгоритм запуска:**

1. Проверка что winws2.exe не запущен
2. Проверка наличия winws2.exe и активного пресета
3. Очистка WinDivert сервисов
4. Включение TCP timestamps
5. Запуск winws2.exe в фоновом режиме
6. Проверка успешного запуска (через 2 секунды)

**Особенности:**

- Запуск в `DETACHED_PROCESS` режиме (не зависит от родительского процесса)
- Логи winws2.exe сохраняются в `%TEMP%\ZapretManager\winws2.log`
- Рабочая директория: `resources/` (для корректной работы относительных путей)

### 2. PresetManager (`core/preset_manager.py`)

Управление пресетами конфигурации.

**Основные методы:**

```python
class PresetManager:
    def list_presets(self) -> List[Preset]:
        """Получить список всех пресетов"""
        
    def get_active_preset(self) -> Optional[Preset]:
        """Получить активный пресет"""
        
    def set_active_preset(self, preset_name: str) -> bool:
        """Установить активный пресет"""
        
    def import_preset(self, file_path: Path, name: str) -> bool:
        """Импорт пользовательского пресета"""
        
    def export_preset(self, preset_name: str, dest_path: Path) -> bool:
        """Экспорт пресета"""
```

**Структура пресета:**

```python
@dataclass
class Preset:
    name: str              # Имя пресета
    path: Path             # Путь к файлу
    description: str       # Описание (из комментариев)
    is_active: bool        # Активен ли сейчас
```

**Формат файла пресета:**

```bash
# Description: Описание пресета
# Минимальный рабочий пресет с LUA конфигурацией

--lua-init=@lua/zapret-lib.lua
--lua-init=@lua/zapret-antidpi.lua
--lua-init=@lua/zapret-auto.lua

--ctrack-disable=0
--ipcache-lifetime=7200
--ipcache-hostname=1

--wf-tcp-out=80,443
--wf-udp-out=443,50000-65535

--hostlist=lists/discord.txt
--hostlist=lists/youtube.txt
```

### 3. TrayIcon (`gui/tray_icon.py`)

Системный трей для управления приложением.

**Основные функции:**

- Отображение статуса (зеленая/красная иконка)
- Контекстное меню с действиями
- Уведомления о событиях
- Автообновление статуса каждые 2 секунды

**Меню трея:**

```
● Статус: Запущен (2ч 15м)
─────────────────────────
⏹ Выключить
🔄 Перезапустить
─────────────────────────
📋 Пресеты >
    ✓ default-main
      CrazyMaxs
      Default v5
      ...
─────────────────────────
⚙️ Открыть главное окно
─────────────────────────
📋 Показать логи
🔍 Диагностика
─────────────────────────
✓ Автозапуск
─────────────────────────
ℹ️ О программе
❌ Выход
```

### 4. Config (`utils/config.py`)

Централизованная конфигурация приложения.

**Основные параметры:**

```python
class Config:
    # Информация о приложении
    APP_NAME = "Zapret Manager"
    VERSION = "1.0.0"
    
    # Режим работы
    IS_FROZEN = getattr(sys, 'frozen', False)
    
    # Пути
    BASE_DIR: Path              # Базовая директория
    RESOURCES_DIR: Path         # Директория ресурсов
    WINWS2_EXE: Path           # Путь к winws2.exe
    PRESETS_DIR: Path          # Директория пресетов
    LISTS_DIR: Path            # Директория списков
    
    # Конфигурация
    CONFIG_DIR: Path           # %TEMP%\ZapretManager\config
    ACTIVE_PRESET: Path        # Активный пресет
    CURRENT_PRESET_NAME: Path  # Имя активного пресета
    
    # Таймауты
    PROCESS_CHECK_TIMEOUT = 5
    STATUS_UPDATE_INTERVAL = 2000  # мс
```

**Определение путей:**

```python
if IS_FROZEN:
    # Режим EXE
    BASE_DIR = Path(sys._MEIPASS)
    RESOURCES_DIR = BASE_DIR / "resources"
else:
    # Режим Python скрипта
    BASE_DIR = Path(__file__).parent.parent.parent
    RESOURCES_DIR = BASE_DIR / "src" / "resources"
```

### 5. Logger (`utils/logger.py`)

Система логирования.

**Конфигурация:**

```python
# Логи сохраняются в %TEMP%\ZapretManager\app.log
# Формат: 2026-04-12 22:14:45 - ZapretManager - INFO - Сообщение
# Уровни: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Использование:**

```python
from utils.logger import logger

logger.info("Запуск приложения")
logger.warning("Предупреждение")
logger.error("Ошибка", exc_info=True)  # С трейсбеком
```

---

## Работа с пресетами

### Типы пресетов

1. **LUA-based** (современный, рекомендуется)
   - Использует Lua-скрипты для гибкой настройки
   - Пример: `default-main.txt`

2. **Legacy** (устаревший)
   - Использует старые параметры командной строки
   - Может не работать с новыми версиями winws2.exe

### Создание пресета

1. Создайте файл `my-preset.txt` в `src/resources/presets/`
2. Добавьте описание в комментарии:

```bash
# Description: Мой пресет для провайдера X
# Оптимизирован для Discord и YouTube

--lua-init=@lua/zapret-lib.lua
--lua-init=@lua/zapret-antidpi.lua
--lua-init=@lua/zapret-auto.lua

--ctrack-disable=0
--ipcache-lifetime=7200

--wf-tcp-out=80,443
--wf-udp-out=443,50000-65535

--hostlist=lists/discord.txt
--hostlist=lists/youtube.txt
```

3. Перезапустите приложение или пересоберите EXE

### Популярные пресеты

- **default-main** - универсальный пресет с LUA
- **CrazyMaxs** - для Discord и YouTube
- **Default v5** - базовый пресет v5
- **ALL TCP & UDP v1** - для всех TCP/UDP портов
- **Ростелеком** - оптимизирован для Ростелеком

### Отладка пресета

1. Запустите пресет через трей
2. Проверьте логи winws2.exe:
   ```bash
   notepad %TEMP%\ZapretManager\winws2.log
   ```
3. Ищите ошибки:
   - `unknown option` - неизвестная опция (устаревший синтаксис)
   - `could not read` - файл не найден
   - `ambiguous option` - неоднозначная опция

---

## API и интеграция

### Программный запуск

```python
from core.zapret_manager import ZapretManager
from core.preset_manager import PresetManager

# Создание менеджеров
zapret = ZapretManager()
presets = PresetManager()

# Установка пресета
presets.set_active_preset("default-main")

# Запуск
if zapret.start():
    print("Zapret запущен")
    
# Проверка статуса
status = zapret.get_status()
print(f"Running: {status['running']}")
print(f"PID: {status['pid']}")
print(f"Uptime: {status['uptime']}")

# Остановка
zapret.stop()
```

### Интеграция с другими приложениями

**Через командную строку:**

```bash
# Запуск приложения
ZapretManager.exe

# Проверка статуса через tasklist
tasklist /FI "IMAGENAME eq winws2.exe"

# Остановка через taskkill
taskkill /F /IM winws2.exe
```

**Через файлы конфигурации:**

```python
# Чтение активного пресета
preset_name = Path("%TEMP%/ZapretManager/config/preset-name.txt").read_text()

# Установка пресета
shutil.copy("my-preset.txt", "%TEMP%/ZapretManager/config/preset-active.txt")
```

---

## Сборка и развертывание

### Сборка EXE

```bash
cd build
build.bat
```

**Что происходит:**

1. PyInstaller собирает все зависимости
2. Копируются ресурсы (winws2.exe, пресеты, списки, lua)
3. Создается `dist/ZapretManager.exe` (~50 MB)

**Конфигурация PyInstaller** (`ZapretManager.spec`):

```python
a = Analysis(
    ['../src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../src/resources', 'resources'),  # Все ресурсы
    ],
    hiddenimports=['PyQt5'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
```

### Создание релиза

1. Обновите версию в `src/utils/config.py`:
   ```python
   VERSION = "1.0.1"
   ```

2. Соберите EXE:
   ```bash
   cd build
   build.bat
   ```

3. Протестируйте:
   ```bash
   dist/ZapretManager.exe
   ```

4. Создайте архив:
   ```bash
   7z a ZapretManager-v1.0.1.zip dist/ZapretManager.exe README.md
   ```

5. Опубликуйте на GitHub Releases

### Автоматическая сборка (CI/CD)

**GitHub Actions** (`.github/workflows/build.yml`):

```yaml
name: Build EXE

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
        
      - name: Build EXE
        run: |
          cd build
          build.bat
          
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: ZapretManager
          path: build/dist/ZapretManager.exe
```

---

## Решение проблем

### Проблема: "Приложение уже запущено"

**Причина:** Процесс ZapretManager.exe уже запущен, но иконка в трее не видна.

**Решение:**

```bash
# Вариант 1: Используйте cleanup.bat
cleanup.bat

# Вариант 2: Вручную через Диспетчер задач
# Ctrl+Shift+Esc → Найти ZapretManager.exe → Снять задачу
```

### Проблема: "winws2.exe не удалось запустить"

**Причина 1:** Нет прав администратора

**Решение:**
```bash
# Запустите с правами администратора
run_as_admin.bat
```

**Причина 2:** Устаревший пресет

**Решение:**
```bash
# Переключитесь на default-main
# Правый клик по иконке → Пресеты → default-main
```

**Причина 3:** Отсутствуют файлы списков

**Решение:**
```bash
# Проверьте логи winws2.exe
notepad %TEMP%\ZapretManager\winws2.log

# Ищите строки "could not read"
# Убедитесь что файлы существуют в resources/lists/
```

### Проблема: "winws2.exe завершился с кодом 1"

**Диагностика:**

1. Откройте логи winws2.exe:
   ```bash
   notepad %TEMP%\ZapretManager\winws2.log
   ```

2. Ищите ошибки:
   - `unknown option --dpi-desync` → Устаревший пресет, используйте LUA-based
   - `ambiguous option --wf-tcp` → Неполная опция, проверьте синтаксис
   - `could not read 'lists/discord.txt'` → Файл не найден

3. Переключитесь на рабочий пресет:
   ```
   Правый клик → Пресеты → default-main
   ```

### Проблема: Discord/YouTube не работают

**Решение:**

1. Проверьте что zapret запущен:
   ```bash
   tasklist | findstr winws2.exe
   ```

2. Попробуйте другой пресет:
   ```
   Правый клик → Пресеты → CrazyMaxs
   ```

3. Проверьте конфликты с VPN/антивирусом:
   ```
   Правый клик → Диагностика
   ```

4. Перезапустите zapret:
   ```
   Правый клик → Перезапустить
   ```

---

## Разработка

### Настройка окружения

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/yourusername/zapret2.git
cd zapret2

# 2. Создайте виртуальное окружение
python -m venv venv
venv\Scripts\activate

# 3. Установите зависимости
pip install -r requirements-dev.txt

# 4. Запустите из исходников
python src/main.py
```

### Структура кода

**Соглашения:**

- Используйте type hints
- Документируйте функции docstrings
- Логируйте важные события
- Обрабатывайте исключения

**Пример:**

```python
def start(self) -> bool:
    """
    Запуск winws2.exe с текущим пресетом
    
    Returns:
        True если запуск успешен
        
    Raises:
        FileNotFoundError: Если winws2.exe не найден
    """
    try:
        logger.info("Запуск winws2.exe")
        # ...
        return True
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}", exc_info=True)
        return False
```

### Тестирование

```bash
# Запуск всех тестов
pytest tests/ -v

# Запуск конкретного теста
pytest tests/test_zapret_manager.py -v

# С покрытием кода
pytest tests/ --cov=src --cov-report=html
```

### Отладка

**Включение DEBUG логов:**

```python
# В src/utils/logger.py
logger.setLevel(logging.DEBUG)
```

**Просмотр логов в реальном времени:**

```bash
# PowerShell
Get-Content $env:TEMP\ZapretManager\app.log -Wait

# CMD
tail -f %TEMP%\ZapretManager\app.log
```

### Добавление нового функционала

**Пример: Добавление нового менеджера**

1. Создайте файл `src/core/my_manager.py`:

```python
from utils.config import Config
from utils.logger import logger

class MyManager:
    """Описание менеджера"""
    
    def __init__(self):
        self.config = Config
        
    def do_something(self) -> bool:
        """Делает что-то полезное"""
        try:
            logger.info("Выполнение действия")
            # ...
            return True
        except Exception as e:
            logger.error(f"Ошибка: {e}", exc_info=True)
            return False
```

2. Интегрируйте в TrayIcon:

```python
from core.my_manager import MyManager

class ZapretTrayIcon(QSystemTrayIcon):
    def __init__(self):
        # ...
        self.my_manager = MyManager()
        
    def create_menu(self):
        # Добавьте пункт меню
        action = QAction("Моя функция", self.menu)
        action.triggered.connect(self.my_action)
        self.menu.addAction(action)
        
    def my_action(self):
        if self.my_manager.do_something():
            self.showMessage("Успех", "Действие выполнено")
```

3. Добавьте тесты:

```python
# tests/test_my_manager.py
import pytest
from core.my_manager import MyManager

def test_do_something():
    manager = MyManager()
    assert manager.do_something() == True
```

### Контрибьюция

1. Форкните репозиторий
2. Создайте ветку: `git checkout -b feature/my-feature`
3. Внесите изменения
4. Добавьте тесты
5. Закоммитьте: `git commit -m "Add my feature"`
6. Запушьте: `git push origin feature/my-feature`
7. Создайте Pull Request

---

## Лицензия

MIT License - см. [LICENSE](LICENSE)

## Поддержка

- **GitHub Issues**: [github.com/yourusername/zapret2/issues](https://github.com/yourusername/zapret2/issues)
- **Telegram**: [@zapretvpns_bot](https://t.me/zapretvpns_bot)
- **Email**: support@example.com

## Благодарности

- [zapret2](https://github.com/bol-van/zapret2) - bol-van
- [WinDivert](https://github.com/basil00/Divert) - basil00
- Сообщество: [@vpndiscordyooutube](https://t.me/vpndiscordyooutube), [@bypassblock](https://t.me/bypassblock)

---

**Версия документации:** 1.0.0  
**Дата обновления:** 2026-04-12
