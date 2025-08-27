---
title: "ISerialManager Examples - Примеры использования"
type: "api_reference"
audiences: ["backend_dev", "frontend_dev"]
tags: ["api", "examples", "serial", "communication"]
last_updated: "2024-12-19"
---

# 🔌 ISerialManager Examples

> [!info] Serial Manager
> Примеры использования интерфейса ISerialManager для работы с последовательными портами

## 📋 Содержание

- [Базовые операции](#базовые-операции)
- [Подключение и отключение](#подключение-и-отключение)
- [Отправка команд](#отправка-команд)
- [Получение информации](#получение-информации)
- [Обработка ошибок](#обработка-ошибок)
- [Интеграционные примеры](#интеграционные-примеры)
- [Тесты](#тесты)

## 🚀 Базовые операции

### Импорты и настройка

```python
import sys
import os
import time
import logging
from typing import Optional

# Добавляем путь к корню проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from core.interfaces import ISerialManager
from core.serial_manager import SerialManager
from core.di.container import DIContainer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Создание экземпляра

```python
def create_serial_manager() -> ISerialManager:
    """Создание экземпляра Serial Manager"""
    # Прямое создание
    serial_manager = SerialManager()
    
    # Или через DI контейнер
    container = DIContainer()
    container.register(ISerialManager, SerialManager)
    serial_manager = container.resolve(ISerialManager)
    
    return serial_manager
```

## 🔗 Подключение и отключение

### Базовое подключение

```python
def basic_connection_example():
    """Пример базового подключения к Serial порту"""
    serial_manager = create_serial_manager()
    
    try:
        # Получение списка доступных портов
        available_ports = serial_manager.get_available_ports()
        print(f"Доступные порты: {available_ports}")
        
        if not available_ports:
            print("Нет доступных портов")
            return
        
        # Подключение к первому доступному порту
        port = available_ports[0]
        success = serial_manager.connect(
            port=port,
            baudrate=115200,
            timeout=1.0
        )
        
        if success:
            print(f"Успешно подключились к {port}")
            
            # Проверка состояния подключения
            if serial_manager.is_connected():
                print("Подключение активно")
                
                # Получение информации о порте
                port_info = serial_manager.get_port_info()
                print(f"Информация о порте: {port_info}")
                
                # Отключение
                serial_manager.disconnect()
                print("Отключились от порта")
            else:
                print("Подключение неактивно")
        else:
            print(f"Не удалось подключиться к {port}")
            
    except Exception as e:
        logger.error(f"Ошибка при работе с Serial Manager: {e}")
    finally:
        # Гарантированное отключение
        if serial_manager.is_connected():
            serial_manager.disconnect()
```

### Подключение с параметрами

```python
def advanced_connection_example():
    """Пример подключения с дополнительными параметрами"""
    serial_manager = create_serial_manager()
    
    # Расширенные параметры подключения
    connection_params = {
        'port': 'COM4',
        'baudrate': 115200,
        'timeout': 2.0,
        'bytesize': 8,
        'parity': 'N',
        'stopbits': 1,
        'xonxoff': False,
        'rtscts': False,
        'dsrdtr': False
    }
    
    try:
        success = serial_manager.connect(**connection_params)
        
        if success:
            print("Подключение с расширенными параметрами успешно")
            
            # Проверка настроек
            port_info = serial_manager.get_port_info()
            print(f"Текущие настройки: {port_info}")
            
        else:
            print("Не удалось подключиться с расширенными параметрами")
            
    except Exception as e:
        logger.error(f"Ошибка подключения: {e}")
    finally:
        serial_manager.disconnect()
```

## 📤 Отправка команд

### Простая отправка команды

```python
def send_command_example():
    """Пример отправки команды"""
    serial_manager = create_serial_manager()
    
    try:
        # Подключение
        if not serial_manager.connect("COM4"):
            print("Не удалось подключиться")
            return
        
        # Отправка простой команды
        command = "test_command"
        success = serial_manager.send_command(command)
        
        if success:
            print(f"Команда '{command}' отправлена успешно")
        else:
            print(f"Ошибка отправки команды '{command}'")
            
    except Exception as e:
        logger.error(f"Ошибка отправки команды: {e}")
    finally:
        serial_manager.disconnect()
```

### Отправка множественных команд

```python
def send_multiple_commands_example():
    """Пример отправки множественных команд"""
    serial_manager = create_serial_manager()
    
    commands = [
        "command1",
        "command2", 
        "command3",
        "status",
        "reset"
    ]
    
    try:
        if not serial_manager.connect("COM4"):
            return
        
        for i, command in enumerate(commands, 1):
            print(f"Отправка команды {i}/{len(commands)}: {command}")
            
            success = serial_manager.send_command(command)
            
            if success:
                print(f"✓ Команда '{command}' отправлена")
            else:
                print(f"✗ Ошибка отправки '{command}'")
            
            # Небольшая пауза между командами
            time.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Ошибка отправки команд: {e}")
    finally:
        serial_manager.disconnect()
```

### Отправка с проверкой состояния

```python
def send_with_state_check_example():
    """Пример отправки команд с проверкой состояния подключения"""
    serial_manager = create_serial_manager()
    
    def send_command_safe(command: str) -> bool:
        """Безопасная отправка команды с проверкой состояния"""
        if not serial_manager.is_connected():
            print("Нет активного подключения")
            return False
        
        try:
            return serial_manager.send_command(command)
        except Exception as e:
            logger.error(f"Ошибка отправки '{command}': {e}")
            return False
    
    try:
        if not serial_manager.connect("COM4"):
            return
        
        # Проверка состояния перед отправкой
        if serial_manager.is_connected():
            print("Подключение активно, отправляем команды")
            
            commands = ["ping", "status", "version"]
            for command in commands:
                if send_command_safe(command):
                    print(f"Команда '{command}' выполнена")
                else:
                    print(f"Ошибка выполнения '{command}'")
        else:
            print("Подключение неактивно")
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        serial_manager.disconnect()
```

## 📊 Получение информации

### Информация о портах

```python
def port_info_example():
    """Пример получения информации о портах"""
    serial_manager = create_serial_manager()
    
    try:
        # Получение списка доступных портов
        available_ports = serial_manager.get_available_ports()
        print(f"Доступные порты: {available_ports}")
        
        # Подробная информация о каждом порте
        for port in available_ports:
            print(f"\nПорт: {port}")
            
            # Попытка подключения для получения информации
            if serial_manager.connect(port):
                port_info = serial_manager.get_port_info()
                print(f"  Информация: {port_info}")
                serial_manager.disconnect()
            else:
                print(f"  Не удалось подключиться для получения информации")
                
    except Exception as e:
        logger.error(f"Ошибка получения информации о портах: {e}")
```

### Мониторинг состояния

```python
def state_monitoring_example():
    """Пример мониторинга состояния подключения"""
    serial_manager = create_serial_manager()
    
    def monitor_connection():
        """Мониторинг состояния подключения"""
        while True:
            try:
                is_connected = serial_manager.is_connected()
                status = "подключено" if is_connected else "отключено"
                print(f"Статус подключения: {status}")
                
                if is_connected:
                    port_info = serial_manager.get_port_info()
                    print(f"  Порт: {port_info.get('port', 'N/A')}")
                    print(f"  Скорость: {port_info.get('baudrate', 'N/A')}")
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\nМониторинг остановлен")
                break
            except Exception as e:
                logger.error(f"Ошибка мониторинга: {e}")
                break
    
    try:
        if serial_manager.connect("COM4"):
            print("Начинаем мониторинг (Ctrl+C для остановки)")
            monitor_connection()
        else:
            print("Не удалось подключиться для мониторинга")
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        serial_manager.disconnect()
```

## ⚠️ Обработка ошибок

### Обработка ошибок подключения

```python
def error_handling_example():
    """Пример обработки ошибок подключения"""
    serial_manager = create_serial_manager()
    
    def safe_connect(port: str, **kwargs) -> bool:
        """Безопасное подключение с обработкой ошибок"""
        try:
            return serial_manager.connect(port, **kwargs)
        except FileNotFoundError:
            print(f"Порт {port} не найден")
            return False
        except PermissionError:
            print(f"Нет прав доступа к порту {port}")
            return False
        except Exception as e:
            print(f"Неизвестная ошибка подключения: {e}")
            return False
    
    def safe_send_command(command: str) -> bool:
        """Безопасная отправка команды"""
        try:
            if not serial_manager.is_connected():
                print("Нет активного подключения")
                return False
            
            return serial_manager.send_command(command)
            
        except Exception as e:
            print(f"Ошибка отправки команды: {e}")
            return False
    
    # Тестирование различных сценариев ошибок
    test_cases = [
        ("COM999", "Несуществующий порт"),
        ("COM4", "Нормальный порт"),
        ("/dev/ttyUSB999", "Несуществующий Linux порт")
    ]
    
    for port, description in test_cases:
        print(f"\nТест: {description}")
        print(f"Порт: {port}")
        
        success = safe_connect(port)
        if success:
            print("✓ Подключение успешно")
            
            # Тест отправки команды
            if safe_send_command("test"):
                print("✓ Команда отправлена")
            else:
                print("✗ Ошибка отправки команды")
            
            serial_manager.disconnect()
        else:
            print("✗ Подключение не удалось")
```

### Восстановление подключения

```python
def connection_recovery_example():
    """Пример восстановления подключения"""
    serial_manager = create_serial_manager()
    
    def reconnect_with_retry(port: str, max_attempts: int = 3) -> bool:
        """Повторные попытки подключения"""
        for attempt in range(max_attempts):
            print(f"Попытка подключения {attempt + 1}/{max_attempts}")
            
            try:
                if serial_manager.connect(port):
                    print(f"✓ Подключение восстановлено на попытке {attempt + 1}")
                    return True
                else:
                    print(f"✗ Попытка {attempt + 1} не удалась")
                    
            except Exception as e:
                print(f"✗ Ошибка на попытке {attempt + 1}: {e}")
            
            # Пауза перед следующей попыткой
            if attempt < max_attempts - 1:
                time.sleep(2)
        
        print("✗ Все попытки подключения исчерпаны")
        return False
    
    try:
        # Первоначальное подключение
        if serial_manager.connect("COM4"):
            print("Первоначальное подключение успешно")
            
            # Симуляция разрыва соединения
            serial_manager.disconnect()
            print("Соединение разорвано")
            
            # Попытка восстановления
            if reconnect_with_retry("COM4"):
                print("Подключение восстановлено")
                
                # Проверка работоспособности
                if serial_manager.send_command("test"):
                    print("✓ Система работает после восстановления")
                else:
                    print("✗ Проблемы после восстановления")
            else:
                print("Не удалось восстановить подключение")
                
    except Exception as e:
        logger.error(f"Ошибка восстановления: {e}")
    finally:
        serial_manager.disconnect()
```

## 🔗 Интеграционные примеры

### Интеграция с Command Executor

```python
def integration_with_command_executor():
    """Пример интеграции с Command Executor"""
    from core.interfaces import ICommandExecutor
    from core.command_executor import BasicCommandExecutor
    
    # Создание сервисов
    serial_manager = create_serial_manager()
    command_executor = BasicCommandExecutor(serial_manager)
    
    try:
        if serial_manager.connect("COM4"):
            print("Интеграция с Command Executor")
            
            # Выполнение команд через Command Executor
            commands = ["status", "version", "reset"]
            
            for command in commands:
                print(f"Выполнение: {command}")
                
                # Валидация команды
                if command_executor.validate_command(command):
                    # Выполнение команды
                    success = command_executor.execute(command)
                    print(f"  Результат: {'✓' if success else '✗'}")
                else:
                    print(f"  Команда невалидна: {command}")
                    
    except Exception as e:
        logger.error(f"Ошибка интеграции: {e}")
    finally:
        serial_manager.disconnect()
```

### Интеграция с Event Bus

```python
def integration_with_event_bus():
    """Пример интеграции с Event Bus"""
    from core.interfaces import IEventBus
    from core.communication.manager import EventBus
    
    # Создание сервисов
    serial_manager = create_serial_manager()
    event_bus = EventBus()
    
    # Обработчики событий
    def on_connected(data):
        print(f"✓ Событие: подключение установлено - {data}")
    
    def on_disconnected(data):
        print(f"✗ Событие: подключение разорвано - {data}")
    
    def on_command_sent(data):
        print(f"📤 Событие: команда отправлена - {data}")
    
    # Подписка на события
    event_bus.subscribe('serial_connected', on_connected)
    event_bus.subscribe('serial_disconnected', on_disconnected)
    event_bus.subscribe('command_sent', on_command_sent)
    
    try:
        # Подключение с публикацией событий
        if serial_manager.connect("COM4"):
            event_bus.publish('serial_connected', {'port': 'COM4'})
            
            # Отправка команды
            if serial_manager.send_command("test"):
                event_bus.publish('command_sent', {'command': 'test'})
            
            # Отключение
            serial_manager.disconnect()
            event_bus.publish('serial_disconnected', {'port': 'COM4'})
            
    except Exception as e:
        logger.error(f"Ошибка интеграции с Event Bus: {e}")
```

## 🧪 Тесты

### Базовые тесты

```python
def test_serial_manager_basic():
    """Базовые тесты Serial Manager"""
    serial_manager = create_serial_manager()
    
    # Тест получения портов
    ports = serial_manager.get_available_ports()
    assert isinstance(ports, list), "get_available_ports должен возвращать список"
    
    # Тест состояния подключения
    assert not serial_manager.is_connected(), "Изначально не должно быть подключения"
    
    # Тест информации о порте без подключения
    port_info = serial_manager.get_port_info()
    assert isinstance(port_info, dict), "get_port_info должен возвращать словарь"
    
    print("✓ Базовые тесты пройдены")

def test_serial_manager_connection():
    """Тесты подключения"""
    serial_manager = create_serial_manager()
    
    # Тест подключения к несуществующему порту
    success = serial_manager.connect("COM999")
    assert not success, "Подключение к несуществующему порту должно быть неуспешным"
    
    # Тест состояния после неуспешного подключения
    assert not serial_manager.is_connected(), "Не должно быть активного подключения"
    
    print("✓ Тесты подключения пройдены")

def test_serial_manager_commands():
    """Тесты отправки команд"""
    serial_manager = create_serial_manager()
    
    # Тест отправки команды без подключения
    success = serial_manager.send_command("test")
    assert not success, "Отправка команды без подключения должна быть неуспешной"
    
    print("✓ Тесты команд пройдены")
```

### Запуск всех тестов

```python
def run_all_tests():
    """Запуск всех тестов"""
    print("🧪 Запуск тестов Serial Manager")
    
    try:
        test_serial_manager_basic()
        test_serial_manager_connection()
        test_serial_manager_commands()
        
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
    basic_connection_example()
    send_command_example()
    error_handling_example()
```

## 🔗 Связанные документы

- [[docs/api/index|API Reference]] - Полная документация API
- [[docs/api/examples/index|Все примеры API]] - Другие примеры использования
- [[docs/architecture/index|Архитектура]] - Понимание архитектуры системы
- [[core/interfaces.py|ISerialManager Interface]] - Исходный код интерфейса
- [[core/serial_manager.py|SerialManager Implementation]] - Реализация

## 📝 Примечания

1. **Порты**: В Windows используйте `COM1`, `COM2`, etc. В Linux - `/dev/ttyUSB0`, `/dev/ttyACM0`
2. **Права доступа**: На Linux может потребоваться права на доступ к портам
3. **Таймауты**: Увеличьте timeout для медленных устройств
4. **Обработка ошибок**: Всегда используйте try-catch для обработки исключений
5. **Ресурсы**: Не забывайте вызывать `disconnect()` для освобождения ресурсов
