---
title: "ICommandExecutor Examples - Примеры использования"
type: "api_reference"
audiences: ["backend_dev", "frontend_dev"]
tags: ["api", "examples", "commands", "execution"]
last_updated: "2024-12-19"
---

# ⚡ ICommandExecutor Examples

> [!info] Command Executor
> Примеры использования интерфейса ICommandExecutor для выполнения команд на устройстве

## 📋 Содержание

- [Базовые операции](#базовые-операции)
- [Выполнение команд](#выполнение-команд)
- [Валидация команд](#валидация-команд)
- [Обработка результатов](#обработка-результатов)
- [Интеграция с другими сервисами](#интеграция-с-другими-сервисами)
- [Обработка ошибок](#обработка-ошибок)
- [Тесты](#тесты)

## 🚀 Базовые операции

### Импорты и настройка

```python
import sys
import os
import time
import logging
from typing import Optional, Dict, Any

# Добавляем путь к корню проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from core.interfaces import ICommandExecutor, ISerialManager
from core.command_executor import BasicCommandExecutor, InteractiveCommandExecutor
from core.serial_manager import SerialManager
from core.di.container import DIContainer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Создание экземпляра

```python
def create_command_executor() -> ICommandExecutor:
    """Создание экземпляра Command Executor"""
    # Создание зависимостей
    serial_manager = SerialManager()
    
    # Создание Command Executor
    command_executor = BasicCommandExecutor(
        serial_manager=serial_manager,
        tag_manager=None,
        tag_dialog_manager=None
    )
    
    return command_executor

def create_interactive_executor() -> ICommandExecutor:
    """Создание интерактивного Command Executor"""
    serial_manager = SerialManager()
    
    interactive_executor = InteractiveCommandExecutor(
        serial_manager=serial_manager,
        tag_manager=None,
        tag_dialog_manager=None
    )
    
    return interactive_executor
```

## ⚡ Выполнение команд

### Простое выполнение команды

```python
def basic_execution_example():
    """Пример базового выполнения команды"""
    command_executor = create_command_executor()
    
    try:
        # Подключение к устройству
        if not command_executor.serial_manager.connect("COM4"):
            print("Не удалось подключиться к устройству")
            return
        
        # Выполнение простой команды
        command = "status"
        print(f"Выполнение команды: {command}")
        
        success = command_executor.execute(command)
        
        if success:
            print(f"✓ Команда '{command}' выполнена успешно")
        else:
            print(f"✗ Ошибка выполнения команды '{command}'")
            
    except Exception as e:
        logger.error(f"Ошибка выполнения команды: {e}")
    finally:
        command_executor.serial_manager.disconnect()
```

### Выполнение с параметрами

```python
def execution_with_params_example():
    """Пример выполнения команды с дополнительными параметрами"""
    command_executor = create_command_executor()
    
    try:
        if not command_executor.serial_manager.connect("COM4"):
            return
        
        # Выполнение команды с параметрами
        command = "set_parameter"
        params = {
            'timeout': 5.0,
            'retry_count': 3,
            'async_execution': True
        }
        
        print(f"Выполнение команды '{command}' с параметрами: {params}")
        
        success = command_executor.execute(command, **params)
        
        if success:
            print("✓ Команда выполнена с параметрами")
        else:
            print("✗ Ошибка выполнения команды с параметрами")
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        command_executor.serial_manager.disconnect()
```

### Пакетное выполнение команд

```python
def batch_execution_example():
    """Пример пакетного выполнения команд"""
    command_executor = create_command_executor()
    
    commands = [
        "initialize",
        "status",
        "get_config",
        "test_connection",
        "cleanup"
    ]
    
    try:
        if not command_executor.serial_manager.connect("COM4"):
            return
        
        print("Пакетное выполнение команд:")
        
        results = []
        for i, command in enumerate(commands, 1):
            print(f"  {i}/{len(commands)}: {command}")
            
            success = command_executor.execute(command)
            results.append((command, success))
            
            if success:
                print(f"    ✓ Успешно")
            else:
                print(f"    ✗ Ошибка")
            
            # Пауза между командами
            time.sleep(0.2)
        
        # Статистика выполнения
        successful = sum(1 for _, success in results if success)
        print(f"\nСтатистика: {successful}/{len(commands)} команд выполнено успешно")
        
    except Exception as e:
        logger.error(f"Ошибка пакетного выполнения: {e}")
    finally:
        command_executor.serial_manager.disconnect()
```

## ✅ Валидация команд

### Валидация перед выполнением

```python
def validation_example():
    """Пример валидации команд перед выполнением"""
    command_executor = create_command_executor()
    
    # Тестовые команды
    test_commands = [
        "valid_command",
        "invalid_command_with_special_chars!@#",
        "command_with_spaces",
        "",
        "very_long_command_" + "x" * 1000,
        "normal_command"
    ]
    
    print("Валидация команд:")
    
    for command in test_commands:
        print(f"\nКоманда: '{command}'")
        
        # Валидация
        is_valid = command_executor.validate_command(command)
        
        if is_valid:
            print("  ✓ Команда валидна")
            
            # Попытка выполнения
            if command_executor.serial_manager.connect("COM4"):
                success = command_executor.execute(command)
                print(f"  Результат выполнения: {'✓' if success else '✗'}")
                command_executor.serial_manager.disconnect()
            else:
                print("  ✗ Не удалось подключиться для выполнения")
        else:
            print("  ✗ Команда невалидна")
```

### Валидация с пользовательскими правилами

```python
def custom_validation_example():
    """Пример валидации с пользовательскими правилами"""
    command_executor = create_command_executor()
    
    def custom_validate_command(command: str) -> bool:
        """Пользовательская валидация команды"""
        if not command:
            return False
        
        # Проверка длины
        if len(command) > 100:
            return False
        
        # Проверка на запрещенные символы
        forbidden_chars = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')']
        if any(char in command for char in forbidden_chars):
            return False
        
        # Проверка на разрешенные команды
        allowed_commands = ['status', 'version', 'reset', 'ping', 'config']
        if command not in allowed_commands:
            return False
        
        return True
    
    # Тестирование пользовательской валидации
    test_commands = [
        "status",
        "invalid!",
        "very_long_command_" + "x" * 200,
        "unknown_command",
        "reset"
    ]
    
    print("Пользовательская валидация:")
    
    for command in test_commands:
        print(f"\nКоманда: '{command}'")
        
        # Стандартная валидация
        standard_valid = command_executor.validate_command(command)
        print(f"  Стандартная валидация: {'✓' if standard_valid else '✗'}")
        
        # Пользовательская валидация
        custom_valid = custom_validate_command(command)
        print(f"  Пользовательская валидация: {'✓' if custom_valid else '✗'}")
        
        # Выполнение только если обе валидации пройдены
        if standard_valid and custom_valid:
            print("  ✓ Команда готова к выполнению")
        else:
            print("  ✗ Команда отклонена")
```

## 📊 Обработка результатов

### Получение детальных результатов

```python
def detailed_results_example():
    """Пример получения детальных результатов выполнения"""
    command_executor = create_command_executor()
    
    def execute_with_details(command: str) -> Dict[str, Any]:
        """Выполнение команды с детальной информацией"""
        result = {
            'command': command,
            'timestamp': time.time(),
            'success': False,
            'error': None,
            'execution_time': 0,
            'response': None
        }
        
        try:
            start_time = time.time()
            
            # Валидация
            if not command_executor.validate_command(command):
                result['error'] = "Команда невалидна"
                return result
            
            # Выполнение
            success = command_executor.execute(command)
            
            end_time = time.time()
            result['execution_time'] = end_time - start_time
            result['success'] = success
            
            if not success:
                result['error'] = "Ошибка выполнения"
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    try:
        if not command_executor.serial_manager.connect("COM4"):
            return
        
        commands = ["status", "version", "invalid_command"]
        
        print("Детальные результаты выполнения:")
        
        for command in commands:
            print(f"\nКоманда: {command}")
            
            result = execute_with_details(command)
            
            print(f"  Успех: {'✓' if result['success'] else '✗'}")
            print(f"  Время выполнения: {result['execution_time']:.3f}с")
            
            if result['error']:
                print(f"  Ошибка: {result['error']}")
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        command_executor.serial_manager.disconnect()
```

### Асинхронное выполнение

```python
import threading
import queue

def async_execution_example():
    """Пример асинхронного выполнения команд"""
    command_executor = create_command_executor()
    
    def async_execute_command(command: str, result_queue: queue.Queue):
        """Асинхронное выполнение команды"""
        try:
            success = command_executor.execute(command)
            result_queue.put((command, success, None))
        except Exception as e:
            result_queue.put((command, False, str(e)))
    
    try:
        if not command_executor.serial_manager.connect("COM4"):
            return
        
        commands = ["status", "version", "ping", "config"]
        result_queue = queue.Queue()
        threads = []
        
        print("Асинхронное выполнение команд:")
        
        # Запуск команд в отдельных потоках
        for command in commands:
            thread = threading.Thread(
                target=async_execute_command,
                args=(command, result_queue)
            )
            threads.append(thread)
            thread.start()
        
        # Ожидание завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Сбор результатов
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
        
        # Вывод результатов
        for command, success, error in results:
            print(f"  {command}: {'✓' if success else '✗'}")
            if error:
                print(f"    Ошибка: {error}")
        
    except Exception as e:
        logger.error(f"Ошибка асинхронного выполнения: {e}")
    finally:
        command_executor.serial_manager.disconnect()
```

## 🔗 Интеграция с другими сервисами

### Интеграция с Tag Manager

```python
def tag_manager_integration_example():
    """Пример интеграции с Tag Manager"""
    from core.tag_manager import TagManager
    
    # Создание сервисов
    serial_manager = SerialManager()
    tag_manager = TagManager()
    
    # Создание Command Executor с Tag Manager
    command_executor = BasicCommandExecutor(
        serial_manager=serial_manager,
        tag_manager=tag_manager,
        tag_dialog_manager=None
    )
    
    try:
        if not serial_manager.connect("COM4"):
            return
        
        # Команды с тегами
        commands_with_tags = [
            "set_value {tag:temperature}",
            "get_status {tag:device_id}",
            "configure {tag:settings}",
            "normal_command"
        ]
        
        print("Выполнение команд с тегами:")
        
        for command in commands_with_tags:
            print(f"\nКоманда: {command}")
            
            # Парсинг тегов
            parsed_command = tag_manager.parse_command(command)
            print(f"  Парсинг: {parsed_command}")
            
            # Валидация
            if command_executor.validate_command(command):
                # Выполнение
                success = command_executor.execute(command)
                print(f"  Результат: {'✓' if success else '✗'}")
            else:
                print("  ✗ Команда невалидна")
        
    except Exception as e:
        logger.error(f"Ошибка интеграции с Tag Manager: {e}")
    finally:
        serial_manager.disconnect()
```

### Интеграция с Event Bus

```python
def event_bus_integration_example():
    """Пример интеграции с Event Bus"""
    from core.communication.manager import EventBus
    
    # Создание сервисов
    serial_manager = SerialManager()
    event_bus = EventBus()
    command_executor = BasicCommandExecutor(serial_manager)
    
    # Обработчики событий
    def on_command_started(data):
        print(f"🚀 Событие: команда начата - {data}")
    
    def on_command_completed(data):
        print(f"✅ Событие: команда завершена - {data}")
    
    def on_command_failed(data):
        print(f"❌ Событие: команда провалена - {data}")
    
    # Подписка на события
    event_bus.subscribe('command_started', on_command_started)
    event_bus.subscribe('command_completed', on_command_completed)
    event_bus.subscribe('command_failed', on_command_failed)
    
    try:
        if not serial_manager.connect("COM4"):
            return
        
        commands = ["status", "version", "test"]
        
        for command in commands:
            print(f"\nВыполнение: {command}")
            
            # Публикация события начала
            event_bus.publish('command_started', {'command': command})
            
            # Выполнение команды
            success = command_executor.execute(command)
            
            # Публикация события завершения
            if success:
                event_bus.publish('command_completed', {
                    'command': command,
                    'result': 'success'
                })
            else:
                event_bus.publish('command_failed', {
                    'command': command,
                    'error': 'execution_failed'
                })
        
    except Exception as e:
        logger.error(f"Ошибка интеграции с Event Bus: {e}")
    finally:
        serial_manager.disconnect()
```

## ⚠️ Обработка ошибок

### Обработка различных типов ошибок

```python
def error_handling_example():
    """Пример обработки различных типов ошибок"""
    command_executor = create_command_executor()
    
    def safe_execute_command(command: str) -> Dict[str, Any]:
        """Безопасное выполнение команды с обработкой ошибок"""
        result = {
            'command': command,
            'success': False,
            'error_type': None,
            'error_message': None
        }
        
        try:
            # Проверка подключения
            if not command_executor.serial_manager.is_connected():
                result['error_type'] = 'connection_error'
                result['error_message'] = 'Нет активного подключения'
                return result
            
            # Валидация команды
            if not command_executor.validate_command(command):
                result['error_type'] = 'validation_error'
                result['error_message'] = 'Команда невалидна'
                return result
            
            # Выполнение команды
            success = command_executor.execute(command)
            result['success'] = success
            
            if not success:
                result['error_type'] = 'execution_error'
                result['error_message'] = 'Ошибка выполнения команды'
            
        except ConnectionError as e:
            result['error_type'] = 'connection_error'
            result['error_message'] = str(e)
        except ValueError as e:
            result['error_type'] = 'value_error'
            result['error_message'] = str(e)
        except TimeoutError as e:
            result['error_type'] = 'timeout_error'
            result['error_message'] = str(e)
        except Exception as e:
            result['error_type'] = 'unknown_error'
            result['error_message'] = str(e)
        
        return result
    
    # Тестовые сценарии
    test_scenarios = [
        ("valid_command", "Нормальная команда"),
        ("", "Пустая команда"),
        ("very_long_command_" + "x" * 1000, "Очень длинная команда"),
        ("invalid!@#", "Команда с запрещенными символами")
    ]
    
    print("Обработка ошибок:")
    
    for command, description in test_scenarios:
        print(f"\nСценарий: {description}")
        print(f"Команда: '{command}'")
        
        result = safe_execute_command(command)
        
        if result['success']:
            print("  ✓ Успешно выполнено")
        else:
            print(f"  ✗ Ошибка: {result['error_type']}")
            print(f"    Сообщение: {result['error_message']}")
```

### Восстановление после ошибок

```python
def error_recovery_example():
    """Пример восстановления после ошибок"""
    command_executor = create_command_executor()
    
    def execute_with_retry(command: str, max_retries: int = 3) -> bool:
        """Выполнение команды с повторными попытками"""
        for attempt in range(max_retries):
            try:
                print(f"  Попытка {attempt + 1}/{max_retries}")
                
                success = command_executor.execute(command)
                
                if success:
                    print(f"    ✓ Успешно на попытке {attempt + 1}")
                    return True
                else:
                    print(f"    ✗ Ошибка на попытке {attempt + 1}")
                    
            except Exception as e:
                print(f"    ✗ Исключение на попытке {attempt + 1}: {e}")
            
            # Пауза перед следующей попыткой
            if attempt < max_retries - 1:
                time.sleep(1)
        
        print(f"  ✗ Все попытки исчерпаны")
        return False
    
    try:
        if not command_executor.serial_manager.connect("COM4"):
            return
        
        commands = ["status", "version", "test_command"]
        
        print("Выполнение с восстановлением после ошибок:")
        
        for command in commands:
            print(f"\nКоманда: {command}")
            
            success = execute_with_retry(command)
            
            if success:
                print(f"  ✓ Команда '{command}' выполнена")
            else:
                print(f"  ✗ Команда '{command}' провалена")
        
    except Exception as e:
        logger.error(f"Ошибка восстановления: {e}")
    finally:
        command_executor.serial_manager.disconnect()
```

## 🧪 Тесты

### Базовые тесты

```python
def test_command_executor_basic():
    """Базовые тесты Command Executor"""
    command_executor = create_command_executor()
    
    # Тест валидации
    assert command_executor.validate_command("test"), "Валидная команда должна пройти проверку"
    assert not command_executor.validate_command(""), "Пустая команда должна быть отклонена"
    
    # Тест выполнения без подключения
    success = command_executor.execute("test")
    assert not success, "Выполнение без подключения должно быть неуспешным"
    
    print("✓ Базовые тесты пройдены")

def test_command_executor_validation():
    """Тесты валидации команд"""
    command_executor = create_command_executor()
    
    # Тест различных типов команд
    test_cases = [
        ("valid_command", True),
        ("", False),
        ("command_with_spaces", True),
        ("very_long_command_" + "x" * 1000, False)
    ]
    
    for command, expected in test_cases:
        result = command_executor.validate_command(command)
        assert result == expected, f"Валидация '{command}' должна быть {expected}"
    
    print("✓ Тесты валидации пройдены")

def test_command_executor_integration():
    """Тесты интеграции"""
    command_executor = create_command_executor()
    
    # Тест с подключением
    if command_executor.serial_manager.connect("COM4"):
        # Тест выполнения
        success = command_executor.execute("status")
        assert isinstance(success, bool), "Результат выполнения должен быть булевым"
        
        command_executor.serial_manager.disconnect()
    
    print("✓ Тесты интеграции пройдены")
```

### Запуск всех тестов

```python
def run_all_tests():
    """Запуск всех тестов"""
    print("🧪 Запуск тестов Command Executor")
    
    try:
        test_command_executor_basic()
        test_command_executor_validation()
        test_command_executor_integration()
        
        print("🎉 Все тесты пройдены успешно!")
        
    except AssertionError as e:
        print(f"❌ Тест не пройден: {e}")
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")

if __name__ == "__main__":
    # Запуск тестов
    run_all_tests()
    
    # Запуск примеров
    print("\n🚀 Запуск примеров:")
    basic_execution_example()
    validation_example()
    error_handling_example()
```

## 🔗 Связанные документы

- [[docs/api/index|API Reference]] - Полная документация API
- [[docs/api/examples/index|Все примеры API]] - Другие примеры использования
- [[docs/api/examples/serial_manager|ISerialManager Examples]] - Примеры Serial Manager
- [[docs/architecture/index|Архитектура]] - Понимание архитектуры системы
- [[core/interfaces.py|ICommandExecutor Interface]] - Исходный код интерфейса
- [[core/command_executor.py|CommandExecutor Implementation]] - Реализация

## 📝 Примечания

1. **Валидация**: Всегда валидируйте команды перед выполнением
2. **Обработка ошибок**: Используйте try-catch для обработки исключений
3. **Подключение**: Убедитесь в активном подключении перед выполнением команд
4. **Параметры**: Используйте **kwargs для передачи дополнительных параметров
5. **Асинхронность**: Для длительных операций используйте асинхронное выполнение
6. **Интеграция**: Command Executor интегрируется с Tag Manager и Event Bus
