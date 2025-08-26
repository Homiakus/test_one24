"""
Тестирование DI контейнера
"""
import sys
import os
import logging
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from core.di_container import DIContainer, register, resolve, get_container
from core.di_config_loader import DIConfigLoader
from core.interfaces import (
    ISerialManager, ICommandExecutor, ISequenceManager, 
    IConfigLoader, ISettingsManager, ILogger
)


def setup_logging():
    """Настройка логирования для тестов"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_basic_registration():
    """Тест базовой регистрации сервисов"""
    print("\n=== Тест базовой регистрации сервисов ===")
    
    # Создаем контейнер
    container = DIContainer()
    
    # Создаем простые классы для тестирования
    class MockSerialManager:
        def __init__(self):
            self.connected = False
        
        def connect(self, port: str, **kwargs):
            self.connected = True
            return True
        
        def disconnect(self):
            self.connected = False
        
        def send_command(self, command: str):
            return True
        
        def is_connected(self):
            return self.connected
        
        def get_available_ports(self):
            return ["COM1", "COM2", "COM3"]
        
        def get_port_info(self):
            return {"connected": self.connected, "port": "COM1"}
    
    class MockCommandExecutor:
        def __init__(self, serial_manager: MockSerialManager):
            self.serial_manager = serial_manager
        
        def execute(self, command: str, **kwargs):
            return self.serial_manager.send_command(command)
        
        def validate_command(self, command: str):
            return bool(command and command.strip())
    
    # Регистрируем сервисы
    container.register(ISerialManager, MockSerialManager)
    container.register(ICommandExecutor, MockCommandExecutor, dependencies={"serial_manager": ISerialManager})
    
    print("Сервисы зарегистрированы")
    
    # Разрешаем зависимости
    try:
        serial_manager = container.resolve(ISerialManager)
        command_executor = container.resolve(ICommandExecutor)
        
        print(f"SerialManager создан: {type(serial_manager).__name__}")
        print(f"CommandExecutor создан: {type(command_executor).__name__}")
        
        # Тестируем функциональность
        assert serial_manager.connect("COM1")
        assert serial_manager.is_connected()
        assert command_executor.execute("test command")
        
        print("✅ Базовые тесты прошли успешно")
        
    except Exception as e:
        print(f"❌ Ошибка в базовых тестах: {e}")
        return False
    
    return True


def test_singleton_behavior():
    """Тест поведения singleton"""
    print("\n=== Тест поведения singleton ===")
    
    container = DIContainer()
    
    class SingletonService:
        def __init__(self):
            self.id = id(self)
    
    class TransientService:
        def __init__(self):
            self.id = id(self)
    
    # Регистрируем singleton и transient сервисы
    container.register(ISerialManager, SingletonService, singleton=True)
    container.register(ILogger, TransientService, singleton=False)
    
    # Получаем экземпляры
    singleton1 = container.resolve(ISerialManager)
    singleton2 = container.resolve(ISerialManager)
    
    transient1 = container.resolve(ILogger)
    transient2 = container.resolve(ILogger)
    
    # Проверяем singleton
    if singleton1.id == singleton2.id:
        print("✅ Singleton работает корректно")
    else:
        print("❌ Singleton не работает")
        return False
    
    # Проверяем transient
    if transient1.id != transient2.id:
        print("✅ Transient работает корректно")
    else:
        print("❌ Transient не работает")
        return False
    
    return True


def test_circular_dependency_detection():
    """Тест обнаружения циклических зависимостей"""
    print("\n=== Тест обнаружения циклических зависимостей ===")
    
    container = DIContainer()
    
    class ServiceA:
        def __init__(self, service_b):
            self.service_b = service_b
    
    class ServiceB:
        def __init__(self, service_a):
            self.service_a = service_a
    
    # Регистрируем сервисы с циклической зависимостью
    container.register(ISerialManager, ServiceA, dependencies={"service_b": ICommandExecutor})
    container.register(ICommandExecutor, ServiceB, dependencies={"service_a": ISerialManager})
    
    try:
        # Попытка разрешения должна вызвать исключение
        container.resolve(ISerialManager)
        print("❌ Циклическая зависимость не обнаружена")
        return False
    except RuntimeError as e:
        if "циклическая зависимость" in str(e).lower():
            print("✅ Циклическая зависимость обнаружена корректно")
            return True
        else:
            print(f"❌ Неожиданная ошибка: {e}")
            return False


def test_config_loader():
    """Тест загрузчика конфигурации"""
    print("\n=== Тест загрузчика конфигурации ===")
    
    config_path = "resources/di_config.toml"
    
    if not os.path.exists(config_path):
        print(f"❌ Файл конфигурации не найден: {config_path}")
        return False
    
    # Создаем загрузчик
    config_loader = DIConfigLoader()
    
    # Валидируем конфигурацию
    errors = config_loader.validate_config(config_path)
    if errors:
        print(f"❌ Ошибки валидации конфигурации:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("✅ Конфигурация валидна")
    
    # Загружаем конфигурацию
    if config_loader.load_config(config_path):
        print("✅ Конфигурация загружена успешно")
        
        # Получаем контейнер
        container = config_loader.get_container()
        services = container.get_registered_services()
        print(f"Зарегистрированные сервисы: {services}")
        
        return True
    else:
        print("❌ Ошибка загрузки конфигурации")
        return False


def test_global_container():
    """Тест глобального контейнера"""
    print("\n=== Тест глобального контейнера ===")
    
    # Получаем глобальный контейнер
    container = get_container()
    
    # Регистрируем тестовый сервис
    class TestService:
        def __init__(self):
            self.name = "TestService"
    
    register(ILogger, TestService)
    
    # Разрешаем зависимость
    try:
        service = resolve(ILogger)
        print(f"✅ Глобальный контейнер работает: {service.name}")
        return True
    except Exception as e:
        print(f"❌ Ошибка глобального контейнера: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов DI контейнера")
    
    setup_logging()
    
    tests = [
        test_basic_registration,
        test_singleton_behavior,
        test_circular_dependency_detection,
        test_config_loader,
        test_global_container
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Тест {test.__name__} завершился с исключением: {e}")
    
    print(f"\n📊 Результаты тестирования: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно!")
        return True
    else:
        print("⚠️ Некоторые тесты не прошли")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
