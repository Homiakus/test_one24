---
title: "Troubleshooting Runbook - Руководство по решению проблем"
type: "runbook"
audiences: ["support", "devops", "backend_dev"]
tags: ["troubleshooting", "diagnostics", "support", "runbook"]
last_updated: "2024-12-19"
---

# 🔧 Troubleshooting Runbook

> [!warning] Важно
> Это руководство содержит пошаговые инструкции по диагностике и решению типичных проблем приложения

## 📋 Содержание

- [Быстрая диагностика](#быстрая-диагностика)
- [Проблемы подключения](#проблемы-подключения)
- [Проблемы выполнения команд](#проблемы-выполнения-команд)
- [Проблемы последовательностей](#проблемы-последовательностей)
- [Проблемы UI](#проблемы-ui)
- [Проблемы производительности](#проблемы-производительности)
- [Проблемы конфигурации](#проблемы-конфигурации)
- [Логи и диагностика](#логи-и-диагностика)
- [Экстренные процедуры](#экстренные-процедуры)

## 🚨 Быстрая диагностика

### Чек-лист быстрой диагностики

```bash
# 1. Проверка состояния приложения
python -c "import sys; print('Python:', sys.version)"
python -c "import PyQt6; print('PyQt6:', PyQt6.QtCore.QT_VERSION_STR)"

# 2. Проверка доступных портов
python -c "
import serial.tools.list_ports
ports = serial.tools.list_ports.comports()
print('Доступные порты:', [p.device for p in ports])
"

# 3. Проверка логов
tail -n 50 logs/app.log

# 4. Проверка конфигурации
python -c "
import tomli
with open('resources/config.toml', 'rb') as f:
    config = tomli.load(f)
print('Конфигурация загружена:', bool(config))
"
```

### Статус системы

```python
def quick_system_check():
    """Быстрая проверка состояния системы"""
    import sys
    import os
    import importlib
    
    checks = {
        'python_version': sys.version,
        'working_directory': os.getcwd(),
        'config_exists': os.path.exists('resources/config.toml'),
        'logs_exist': os.path.exists('logs/'),
        'serial_available': importlib.util.find_spec('serial') is not None,
        'pyqt6_available': importlib.util.find_spec('PyQt6') is not None
    }
    
    print("=== Быстрая диагностика системы ===")
    for check, result in checks.items():
        status = "✓" if result else "✗"
        print(f"{status} {check}: {result}")
    
    return all(checks.values())
```

## 🔌 Проблемы подключения

### Проблема: Не удается подключиться к Serial порту

**Симптомы:**
- Ошибка "Port not found" или "Access denied"
- Приложение не может обнаружить устройство
- Подключение прерывается сразу после установки

**Диагностика:**

```python
def diagnose_connection_issues():
    """Диагностика проблем подключения"""
    import serial.tools.list_ports
    import os
    
    print("=== Диагностика проблем подключения ===")
    
    # 1. Проверка доступных портов
    ports = list(serial.tools.list_ports.comports())
    print(f"Найдено портов: {len(ports)}")
    
    for port in ports:
        print(f"  {port.device}: {port.description}")
    
    # 2. Проверка прав доступа (Linux)
    if os.name == 'posix':
        for port in ports:
            if os.access(port.device, os.R_OK | os.W_OK):
                print(f"  ✓ Права доступа к {port.device}: OK")
            else:
                print(f"  ✗ Нет прав доступа к {port.device}")
    
    # 3. Проверка занятости портов
    import psutil
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.info['connections']:
                if hasattr(conn, 'laddr') and conn.laddr:
                    print(f"  Порт {conn.laddr.port} используется процессом {proc.info['name']} (PID: {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
```

**Решения:**

1. **Порт не найден:**
   ```bash
   # Windows: Проверка Device Manager
   # Linux: Проверка /dev/tty*
   ls -la /dev/tty*
   
   # Добавление пользователя в группу dialout (Linux)
   sudo usermod -a -G dialout $USER
   sudo chmod 666 /dev/ttyUSB0
   ```

2. **Доступ запрещен:**
   ```bash
   # Windows: Запуск от имени администратора
   # Linux: Настройка прав доступа
   sudo chmod 666 /dev/ttyUSB0
   sudo chown $USER:dialout /dev/ttyUSB0
   ```

3. **Порт занят:**
   ```bash
   # Поиск процесса, использующего порт
   lsof | grep /dev/ttyUSB0
   
   # Завершение процесса
   sudo kill -9 <PID>
   ```

### Проблема: Нестабильное подключение

**Симптомы:**
- Подключение прерывается во время работы
- Команды не доходят до устройства
- Таймауты при выполнении операций

**Диагностика:**

```python
def diagnose_connection_stability():
    """Диагностика стабильности подключения"""
    import time
    from core.serial_manager import SerialManager
    
    serial_manager = SerialManager()
    
    print("=== Тест стабильности подключения ===")
    
    # Получение доступных портов
    ports = serial_manager.get_available_ports()
    if not ports:
        print("Нет доступных портов")
        return
    
    port = ports[0]
    
    # Тест подключения
    if not serial_manager.connect(port):
        print(f"Не удалось подключиться к {port}")
        return
    
    print(f"Подключились к {port}")
    
    # Тест стабильности
    test_commands = ["ping", "status", "version"]
    success_count = 0
    
    for i in range(10):
        for command in test_commands:
            try:
                success = serial_manager.send_command(command)
                if success:
                    success_count += 1
                time.sleep(0.1)
            except Exception as e:
                print(f"Ошибка на итерации {i}: {e}")
    
    print(f"Успешных команд: {success_count}/30")
    
    serial_manager.disconnect()
```

**Решения:**

1. **Проверка кабеля и физического подключения**
2. **Увеличение таймаутов:**
   ```python
   serial_manager.connect(port, timeout=5.0, write_timeout=5.0)
   ```
3. **Настройка буферизации:**
   ```python
   serial_manager.connect(port, xonxoff=True, rtscts=True)
   ```

## ⚡ Проблемы выполнения команд

### Проблема: Команды не выполняются

**Симптомы:**
- Команды отправляются, но устройство не отвечает
- Ошибки валидации команд
- Таймауты при выполнении

**Диагностика:**

```python
def diagnose_command_execution():
    """Диагностика выполнения команд"""
    from core.command_executor import BasicCommandExecutor
    from core.serial_manager import SerialManager
    
    print("=== Диагностика выполнения команд ===")
    
    # Создание сервисов
    serial_manager = SerialManager()
    command_executor = BasicCommandExecutor(serial_manager)
    
    # Получение портов
    ports = serial_manager.get_available_ports()
    if not ports:
        print("Нет доступных портов")
        return
    
    port = ports[0]
    
    # Подключение
    if not serial_manager.connect(port):
        print(f"Не удалось подключиться к {port}")
        return
    
    print(f"Подключились к {port}")
    
    # Тест команд
    test_commands = [
        ("status", "Простая команда"),
        ("", "Пустая команда"),
        ("very_long_command_" + "x" * 1000, "Очень длинная команда"),
        ("invalid!@#", "Команда с запрещенными символами")
    ]
    
    for command, description in test_commands:
        print(f"\nТест: {description}")
        print(f"Команда: '{command}'")
        
        # Валидация
        is_valid = command_executor.validate_command(command)
        print(f"Валидация: {'✓' if is_valid else '✗'}")
        
        if is_valid:
            # Выполнение
            success = command_executor.execute(command)
            print(f"Выполнение: {'✓' if success else '✗'}")
    
    serial_manager.disconnect()
```

**Решения:**

1. **Проверка формата команд:**
   ```python
   # Проверка синтаксиса команды
   def validate_command_syntax(command):
       if not command or len(command) > 100:
           return False
       forbidden_chars = ['!', '@', '#', '$', '%', '^', '&', '*']
       return not any(char in command for char in forbidden_chars)
   ```

2. **Настройка таймаутов:**
   ```python
   # Увеличение таймаутов для медленных устройств
   command_executor.execute(command, timeout=10.0)
   ```

3. **Проверка протокола связи:**
   ```python
   # Тест базовой связи
   def test_basic_communication():
       serial_manager.send_command("ping")
       time.sleep(1)
       # Проверка ответа
       response = serial_manager.read_response()
       return "pong" in response.lower()
   ```

### Проблема: Команды выполняются с ошибками

**Симптомы:**
- Частичное выполнение команд
- Неожиданные ответы от устройства
- Ошибки парсинга ответов

**Диагностика:**

```python
def diagnose_command_errors():
    """Диагностика ошибок выполнения команд"""
    import time
    from core.command_executor import BasicCommandExecutor
    from core.serial_manager import SerialManager
    
    print("=== Диагностика ошибок команд ===")
    
    serial_manager = SerialManager()
    command_executor = BasicCommandExecutor(serial_manager)
    
    # Подключение
    ports = serial_manager.get_available_ports()
    if not ports or not serial_manager.connect(ports[0]):
        print("Не удалось подключиться")
        return
    
    # Тест с детальным логированием
    commands = ["status", "version", "config", "reset"]
    
    for command in commands:
        print(f"\nВыполнение: {command}")
        
        start_time = time.time()
        
        try:
            success = command_executor.execute(command)
            execution_time = time.time() - start_time
            
            print(f"  Результат: {'✓' if success else '✗'}")
            print(f"  Время выполнения: {execution_time:.3f}с")
            
            if not success:
                print(f"  Возможные причины:")
                print(f"    - Устройство не поддерживает команду")
                print(f"    - Неправильный формат команды")
                print(f"    - Проблемы связи")
                
        except Exception as e:
            print(f"  Исключение: {e}")
    
    serial_manager.disconnect()
```

## 🔄 Проблемы последовательностей

### Проблема: Последовательности не выполняются

**Симптомы:**
- Ошибки при разворачивании последовательностей
- Бесконечные циклы в последовательностях
- Неправильный порядок выполнения команд

**Диагностика:**

```python
def diagnose_sequence_issues():
    """Диагностика проблем с последовательностями"""
    from core.sequence_manager import SequenceManager
    from core.flag_manager import FlagManager
    
    print("=== Диагностика последовательностей ===")
    
    # Создание менеджеров
    flag_manager = FlagManager()
    sequence_manager = SequenceManager(flag_manager)
    
    # Тестовые последовательности
    test_sequences = {
        "simple": ["command1", "command2", "command3"],
        "with_conditionals": ["if flag1", "command1", "else", "command2", "endif"],
        "with_nesting": ["sequence1", "sequence2"],
        "invalid": ["if flag1", "command1"]  # Незакрытый if
    }
    
    for name, sequence in test_sequences.items():
        print(f"\nТест последовательности: {name}")
        print(f"Команды: {sequence}")
        
        # Валидация
        is_valid, errors = sequence_manager.validate_sequence(sequence)
        print(f"Валидность: {'✓' if is_valid else '✗'}")
        
        if not is_valid:
            print(f"Ошибки: {errors}")
        
        # Разворачивание
        try:
            expanded = sequence_manager.expand_sequence(sequence)
            print(f"Развернуто команд: {len(expanded)}")
        except Exception as e:
            print(f"Ошибка разворачивания: {e}")
```

**Решения:**

1. **Проверка синтаксиса последовательностей:**
   ```python
   def validate_sequence_syntax(sequence):
       """Проверка синтаксиса последовательности"""
       if_count = sequence.count("if")
       endif_count = sequence.count("endif")
       
       if if_count != endif_count:
           return False, "Несоответствие if/endif"
       
       return True, None
   ```

2. **Обнаружение циклов:**
   ```python
   def detect_cycles(sequence, visited=None):
       """Обнаружение циклов в последовательности"""
       if visited is None:
           visited = set()
       
       for command in sequence:
           if command.startswith("sequence_"):
               if command in visited:
                   return True  # Обнаружен цикл
               visited.add(command)
       
       return False
   ```

## 🖥️ Проблемы UI

### Проблема: Интерфейс не отвечает

**Симптомы:**
- UI зависает при выполнении операций
- Не обновляются элементы интерфейса
- Ошибки в консоли браузера

**Диагностика:**

```python
def diagnose_ui_issues():
    """Диагностика проблем UI"""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    
    print("=== Диагностика проблем UI ===")
    
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    
    # Проверка событийного цикла
    def check_event_loop():
        print("Проверка событийного цикла...")
        # Создание таймера для проверки
        timer = QTimer()
        timer.singleShot(1000, lambda: print("Событийный цикл работает"))
        timer.start()
    
    check_event_loop()
    
    # Проверка памяти
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"Использование памяти: {memory_info.rss / 1024 / 1024:.1f} MB")
    
    # Проверка потоков
    threads = process.threads()
    print(f"Количество потоков: {len(threads)}")
    
    for thread in threads:
        print(f"  Поток {thread.id}: {thread.user_time:.2f}s")
```

**Решения:**

1. **Перемещение тяжелых операций в отдельные потоки:**
   ```python
   from PyQt6.QtCore import QThread, pyqtSignal
   
   class WorkerThread(QThread):
       finished = pyqtSignal()
       
       def run(self):
           # Тяжелая операция
           time.sleep(5)
           self.finished.emit()
   ```

2. **Обновление UI через сигналы:**
   ```python
   from PyQt6.QtCore import pyqtSignal
   
   class MainWindow(QMainWindow):
       update_signal = pyqtSignal(str)
       
       def __init__(self):
           super().__init__()
           self.update_signal.connect(self.update_ui)
       
       def update_ui(self, data):
           # Обновление UI элементов
           pass
   ```

### Проблема: Ошибки отображения

**Симптомы:**
- Элементы интерфейса не отображаются
- Неправильное позиционирование
- Проблемы с темами

**Диагностика:**

```python
def diagnose_display_issues():
    """Диагностика проблем отображения"""
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
    from PyQt6.QtCore import Qt
    
    print("=== Диагностика проблем отображения ===")
    
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    
    # Создание тестового окна
    window = QWidget()
    window.setWindowTitle("Тест отображения")
    window.resize(400, 300)
    
    layout = QVBoxLayout()
    
    # Тестовые элементы
    label1 = QLabel("Тест 1: Обычный текст")
    label2 = QLabel("Тест 2: Специальные символы: áéíóú")
    label3 = QLabel("Тест 3: Русский текст: привет мир")
    
    layout.addWidget(label1)
    layout.addWidget(label2)
    layout.addWidget(label3)
    
    window.setLayout(layout)
    window.show()
    
    # Проверка шрифтов
    font = window.font()
    print(f"Шрифт: {font.family()}")
    print(f"Размер: {font.pointSize()}")
    
    # Проверка разрешения экрана
    screen = app.primaryScreen()
    geometry = screen.geometry()
    print(f"Разрешение экрана: {geometry.width()}x{geometry.height()}")
    
    return window
```

## ⚡ Проблемы производительности

### Проблема: Медленная работа приложения

**Симптомы:**
- Долгое время отклика интерфейса
- Высокое потребление CPU/памяти
- Зависания при выполнении операций

**Диагностика:**

```python
def diagnose_performance_issues():
    """Диагностика проблем производительности"""
    import psutil
    import time
    from PyQt6.QtCore import QTimer
    
    print("=== Диагностика производительности ===")
    
    process = psutil.Process()
    
    # Мониторинг ресурсов
    def monitor_resources():
        cpu_percent = process.cpu_percent()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        print(f"CPU: {cpu_percent:.1f}%")
        print(f"Память: {memory_info.rss / 1024 / 1024:.1f} MB ({memory_percent:.1f}%)")
        
        # Проверка на утечки памяти
        if memory_percent > 80:
            print("⚠️ Высокое потребление памяти")
        
        if cpu_percent > 90:
            print("⚠️ Высокая нагрузка на CPU")
    
    # Запуск мониторинга
    timer = QTimer()
    timer.timeout.connect(monitor_resources)
    timer.start(1000)  # Каждую секунду
    
    # Тест производительности
    def performance_test():
        start_time = time.time()
        
        # Имитация тяжелой операции
        for i in range(1000):
            _ = i * i
        
        execution_time = time.time() - start_time
        print(f"Время выполнения теста: {execution_time:.3f}с")
        
        if execution_time > 1.0:
            print("⚠️ Медленное выполнение")
    
    performance_test()
    
    return timer
```

**Решения:**

1. **Оптимизация алгоритмов:**
   ```python
   # Использование кеширования
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def expensive_operation(data):
       # Тяжелая операция
       return result
   ```

2. **Асинхронная обработка:**
   ```python
   import asyncio
   
   async def async_operation():
       # Асинхронная операция
       await asyncio.sleep(1)
       return result
   ```

3. **Оптимизация UI:**
   ```python
   # Отключение обновлений во время операций
   def batch_update():
       widget.setUpdatesEnabled(False)
       try:
           # Массовые обновления
           for item in items:
               update_item(item)
       finally:
           widget.setUpdatesEnabled(True)
   ```

## ⚙️ Проблемы конфигурации

### Проблема: Неправильная конфигурация

**Симптомы:**
- Приложение не запускается
- Неправильное поведение функций
- Ошибки при загрузке настроек

**Диагностика:**

```python
def diagnose_configuration_issues():
    """Диагностика проблем конфигурации"""
    import tomli
    import os
    
    print("=== Диагностика конфигурации ===")
    
    config_files = [
        'resources/config.toml',
        'resources/di_config.toml',
        'serial_settings.json',
        'update_settings.json'
    ]
    
    for config_file in config_files:
        print(f"\nПроверка файла: {config_file}")
        
        if not os.path.exists(config_file):
            print(f"  ✗ Файл не найден")
            continue
        
        try:
            with open(config_file, 'rb') as f:
                if config_file.endswith('.toml'):
                    config = tomli.load(f)
                else:
                    import json
                    config = json.load(f)
            
            print(f"  ✓ Файл загружен успешно")
            print(f"  Размер: {os.path.getsize(config_file)} байт")
            
            # Проверка структуры
            if isinstance(config, dict):
                print(f"  Ключи: {list(config.keys())}")
            
        except Exception as e:
            print(f"  ✗ Ошибка загрузки: {e}")
    
    # Проверка переменных окружения
    env_vars = ['PYTHONPATH', 'QT_LOGGING_RULES', 'QT_DEBUG_PLUGINS']
    print(f"\nПроверка переменных окружения:")
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"  {var}: {value}")
        else:
            print(f"  {var}: не установлена")
```

**Решения:**

1. **Восстановление конфигурации по умолчанию:**
   ```python
   def restore_default_config():
       """Восстановление конфигурации по умолчанию"""
       default_config = {
           'serial': {
               'default_port': 'COM4',
               'baudrate': 115200,
               'timeout': 1.0
           },
           'ui': {
               'theme': 'light',
               'language': 'ru'
           }
       }
       
       import json
       with open('resources/config.toml', 'w') as f:
           json.dump(default_config, f, indent=2)
   ```

2. **Валидация конфигурации:**
   ```python
   def validate_config(config):
       """Валидация конфигурации"""
       required_keys = ['serial', 'ui']
       
       for key in required_keys:
           if key not in config:
               raise ValueError(f"Отсутствует обязательный ключ: {key}")
       
       # Проверка значений
       if config['serial']['baudrate'] not in [9600, 19200, 38400, 57600, 115200]:
           raise ValueError("Неподдерживаемая скорость передачи")
   ```

## 📊 Логи и диагностика

### Сбор диагностической информации

```python
def collect_diagnostic_info():
    """Сбор диагностической информации"""
    import platform
    import sys
    import os
    import psutil
    from datetime import datetime
    
    print("=== Сбор диагностической информации ===")
    
    diagnostic_info = {
        'timestamp': datetime.now().isoformat(),
        'system': {
            'platform': platform.platform(),
            'python_version': sys.version,
            'architecture': platform.architecture(),
            'processor': platform.processor()
        },
        'application': {
            'working_directory': os.getcwd(),
            'python_path': sys.executable,
            'modules': list(sys.modules.keys())
        },
        'resources': {
            'memory_usage': psutil.virtual_memory()._asdict(),
            'disk_usage': psutil.disk_usage('.')._asdict(),
            'cpu_count': psutil.cpu_count()
        },
        'files': {
            'config_exists': os.path.exists('resources/config.toml'),
            'logs_exist': os.path.exists('logs/'),
            'backup_exists': os.path.exists('backups/')
        }
    }
    
    # Сохранение диагностической информации
    import json
    with open('diagnostic_info.json', 'w', encoding='utf-8') as f:
        json.dump(diagnostic_info, f, indent=2, ensure_ascii=False)
    
    print("Диагностическая информация сохранена в diagnostic_info.json")
    return diagnostic_info
```

### Анализ логов

```python
def analyze_logs():
    """Анализ логов приложения"""
    import re
    from datetime import datetime, timedelta
    
    print("=== Анализ логов ===")
    
    log_file = 'logs/app.log'
    if not os.path.exists(log_file):
        print("Файл логов не найден")
        return
    
    # Чтение последних 1000 строк
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()[-1000:]
    
    # Анализ ошибок
    error_pattern = r'ERROR|CRITICAL|Exception|Traceback'
    errors = [line for line in lines if re.search(error_pattern, line, re.IGNORECASE)]
    
    print(f"Найдено ошибок: {len(errors)}")
    
    if errors:
        print("\nПоследние ошибки:")
        for error in errors[-5:]:
            print(f"  {error.strip()}")
    
    # Анализ по времени
    time_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
    timestamps = []
    
    for line in lines:
        match = re.search(time_pattern, line)
        if match:
            try:
                timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                timestamps.append(timestamp)
            except ValueError:
                pass
    
    if timestamps:
        print(f"\nВременной диапазон логов:")
        print(f"  Начало: {min(timestamps)}")
        print(f"  Конец: {max(timestamps)}")
        print(f"  Продолжительность: {max(timestamps) - min(timestamps)}")
```

## 🚨 Экстренные процедуры

### Экстренная остановка приложения

```python
def emergency_shutdown():
    """Экстренная остановка приложения"""
    print("=== ЭКСТРЕННАЯ ОСТАНОВКА ===")
    
    # Остановка всех потоков
    import threading
    active_threads = threading.enumerate()
    print(f"Активных потоков: {len(active_threads)}")
    
    for thread in active_threads:
        if thread != threading.main_thread():
            print(f"Остановка потока: {thread.name}")
            # thread.join(timeout=1.0)
    
    # Закрытие всех соединений
    try:
        from core.serial_manager import SerialManager
        serial_manager = SerialManager()
        if serial_manager.is_connected():
            serial_manager.disconnect()
            print("Serial соединение закрыто")
    except Exception as e:
        print(f"Ошибка закрытия соединения: {e}")
    
    # Сохранение состояния
    try:
        import json
        state = {
            'timestamp': datetime.now().isoformat(),
            'emergency_shutdown': True
        }
        with open('emergency_state.json', 'w') as f:
            json.dump(state, f)
        print("Состояние сохранено")
    except Exception as e:
        print(f"Ошибка сохранения состояния: {e}")
    
    print("Экстренная остановка завершена")
```

### Восстановление после сбоя

```python
def recovery_after_crash():
    """Восстановление после сбоя"""
    print("=== ВОССТАНОВЛЕНИЕ ПОСЛЕ СБОЯ ===")
    
    # Проверка файла состояния
    if os.path.exists('emergency_state.json'):
        print("Обнаружен файл экстренного состояния")
        
        try:
            import json
            with open('emergency_state.json', 'r') as f:
                state = json.load(f)
            
            print(f"Время сбоя: {state.get('timestamp', 'неизвестно')}")
            
            # Очистка файла состояния
            os.remove('emergency_state.json')
            print("Файл состояния очищен")
            
        except Exception as e:
            print(f"Ошибка чтения состояния: {e}")
    
    # Проверка и восстановление конфигурации
    if not os.path.exists('resources/config.toml'):
        print("Конфигурация отсутствует, восстановление...")
        restore_default_config()
    
    # Очистка временных файлов
    temp_files = [f for f in os.listdir('.') if f.endswith('.tmp')]
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
            print(f"Удален временный файл: {temp_file}")
        except Exception as e:
            print(f"Ошибка удаления {temp_file}: {e}")
    
    print("Восстановление завершено")
```

## 📞 Контакты поддержки

### Информация для обращения в поддержку

При обращении в поддержку предоставьте:

1. **Диагностическую информацию:**
   ```bash
   python -c "from docs.runbooks.troubleshooting import collect_diagnostic_info; collect_diagnostic_info()"
   ```

2. **Логи приложения:**
   ```bash
   tail -n 100 logs/app.log > support_logs.txt
   ```

3. **Описание проблемы:**
   - Что происходило перед возникновением проблемы
   - Точные шаги для воспроизведения
   - Ожидаемое и фактическое поведение

4. **Системная информация:**
   - Версия операционной системы
   - Версия Python
   - Версия PyQt6
   - Список установленных пакетов

### Полезные команды

```bash
# Создание полного отчета о системе
python -c "
import sys
import platform
import psutil
print('Python:', sys.version)
print('Platform:', platform.platform())
print('CPU:', psutil.cpu_count())
print('Memory:', psutil.virtual_memory().total // 1024 // 1024, 'MB')
"

# Проверка зависимостей
pip list | grep -E "(PyQt6|pyserial|qt-material)"

# Проверка прав доступа к портам (Linux)
ls -la /dev/tty*

# Мониторинг ресурсов в реальном времени
top -p $(pgrep -f "python.*main.py")
```

## 🔗 Связанные документы

- [[docs/api/examples/index|API Examples]] - Примеры использования API
- [[docs/guides/development|Руководство разработчика]] - Лучшие практики
- [[docs/architecture/index|Архитектура]] - Понимание архитектуры
- [[docs/operations/index|Операции]] - Руководство по эксплуатации
- [[docs/security/index|Безопасность]] - Рекомендации по безопасности
