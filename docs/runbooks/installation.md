---
title: "Установка и настройка"
type: "runbook"
audiences: ["devops", "backend_dev", "support"]
tags: ["doc", "lab-equipment-system", "runbook", "installation"]
status: "approved"
last_updated: "2024-12-19"
sources:
  - path: "README.md"
    lines: "L100-L200"
    permalink: "https://github.com/lab-equipment-system/blob/main/README.md#L100-L200"
  - path: "requirements.txt"
    lines: "L1-L34"
    permalink: "https://github.com/lab-equipment-system/blob/main/requirements.txt#L1-L34"
related: ["docs/runbooks/quick-start", "docs/operations/deployment"]
---

> [!info] Навигация
> Родитель: [[docs/runbooks]] • Раздел: [[_moc/Overview]] • См. также: [[docs/runbooks/quick-start]]

# Установка и настройка

## Обзор

Этот runbook описывает процесс установки и настройки системы управления лабораторным оборудованием.

## Предварительные требования

### Системные требования

- **Операционная система**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.9 или выше
- **Память**: Минимум 4GB RAM
- **Дисковое пространство**: 1GB свободного места
- **Последовательные порты**: Доступ к COM портам (Windows) или /dev/tty* (Linux/macOS)

### Проверка системы

```bash
# Проверка версии Python
python --version

# Проверка доступных портов (Windows)
mode

# Проверка доступных портов (Linux/macOS)
ls /dev/tty*

# Проверка свободного места
df -h
```

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/lab-equipment-system.git
cd lab-equipment-system
```

### 2. Создание виртуального окружения

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Проверка установки

```bash
# Проверка импорта основных модулей
python -c "import core; import ui; print('Установка успешна')"

# Запуск тестов
pytest tests/ -v
```

## Настройка

### 1. Конфигурация последовательных портов

Создайте файл `config/serial_config.json`:

```json
{
  "port": "COM3",
  "baudrate": 9600,
  "timeout": 5.0,
  "parity": "N",
  "stopbits": 1,
  "bytesize": 8,
  "retry_attempts": 3,
  "retry_delay": 1.0
}
```

### 2. Настройка логирования

Создайте файл `config/logging_config.json`:

```json
{
  "level": "INFO",
  "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
  "file": "logs/app.log",
  "max_size": "10MB",
  "backup_count": 5
}
```

### 3. Настройка мониторинга

Создайте файл `config/monitoring_config.json`:

```json
{
  "enabled": true,
  "interval": 30,
  "health_check_timeout": 10,
  "performance_metrics": true,
  "error_reporting": true
}
```

## Проверка работоспособности

### 1. Тест подключения

```python
from core.serial_manager import SerialManager
from core.di_container import DIContainer

# Создание контейнера
container = DIContainer()

# Регистрация сервисов
container.register(ISerialManager, SerialManager)

# Тест подключения
serial_manager = container.resolve(ISerialManager)
success = serial_manager.connect("COM3", 9600)

if success:
    print("Подключение успешно")
else:
    print("Ошибка подключения")
```

### 2. Тест команд

```python
# Отправка тестовой команды
response = serial_manager.send_command("STATUS")
print(f"Ответ: {response}")

# Отключение
serial_manager.disconnect()
```

### 3. Запуск приложения

```bash
# Запуск главного приложения
python main.py

# Или с конфигурацией
python main.py --config config/app_config.json
```

## Устранение неполадок

### Проблема: Python не найден

**Симптомы**: `python: command not found`

**Решение**:
```bash
# Windows - установить Python с python.org
# Linux
sudo apt-get install python3 python3-pip

# macOS
brew install python3
```

### Проблема: Ошибка импорта модулей

**Симптомы**: `ModuleNotFoundError: No module named 'core'`

**Решение**:
```bash
# Проверить виртуальное окружение
which python

# Переустановить зависимости
pip install -r requirements.txt --force-reinstall
```

### Проблема: Ошибка доступа к порту

**Симптомы**: `PermissionError: [Errno 13] Permission denied`

**Решение**:
```bash
# Windows - запустить от имени администратора
# Linux
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB0

# macOS
sudo chmod 666 /dev/tty.usbserial-*
```

### Проблема: Порт не найден

**Симптомы**: `SerialException: could not open port COM3`

**Решение**:
1. Проверить подключение оборудования
2. Проверить драйверы
3. Найти правильный порт:
   ```bash
   # Windows
   mode
   
   # Linux
   ls /dev/tty*
   
   # macOS
   ls /dev/tty.*
   ```

## Автоматизация установки

### Скрипт установки (Windows)

Создайте `install.bat`:

```batch
@echo off
echo Установка системы управления лабораторным оборудованием...

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python не найден. Установите Python 3.9+
    pause
    exit /b 1
)

REM Создание виртуального окружения
python -m venv venv
call venv\Scripts\activate

REM Установка зависимостей
pip install -r requirements.txt

REM Создание конфигурации
if not exist config mkdir config
copy config.toml config\app_config.toml

echo Установка завершена!
pause
```

### Скрипт установки (Linux/macOS)

Создайте `install.sh`:

```bash
#!/bin/bash

echo "Установка системы управления лабораторным оборудованием..."

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 не найден. Установите Python 3.9+"
    exit 1
fi

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Создание конфигурации
mkdir -p config
cp config.toml config/app_config.toml

echo "Установка завершена!"
```

## Следующие шаги

После успешной установки:

1. [[docs/runbooks/quick-start|Быстрый старт]]
2. [[docs/runbooks/troubleshooting|Диагностика проблем]]
3. [[docs/operations/deployment|Развертывание в продакшене]]