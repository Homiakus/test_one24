"""
Пример использования DI контейнера
"""
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.di_container import DIContainer, register, resolve, get_container
from core.di_config_loader import DIConfigLoader
from core.interfaces import (
    ISerialManager, ICommandExecutor, ISequenceManager, 
    IConfigLoader, ISettingsManager, ILogger
)


def example_basic_usage():
    """Пример базового использования DI контейнера"""
    print("=== Пример базового использования DI контейнера ===")
    
    # Создаем контейнер
    container = DIContainer()
    
    # Определяем простые реализации
    class SimpleLogger:
        def __init__(self):
            self.messages = []
        
        def info(self, message: str):
            self.messages.append(f"INFO: {message}")
            print(f"INFO: {message}")
        
        def error(self, message: str):
            self.messages.append(f"ERROR: {message}")
            print(f"ERROR: {message}")
    
    class SimpleSerialManager:
        def __init__(self, logger: SimpleLogger):
            self.logger = logger
            self.connected = False
        
        def connect(self, port: str, **kwargs):
            self.logger.info(f"Подключение к порту {port}")
            self.connected = True
            return True
        
        def disconnect(self):
            self.logger.info("Отключение от порта")
            self.connected = False
        
        def send_command(self, command: str):
            self.logger.info(f"Отправка команды: {command}")
            return True
        
        def is_connected(self):
            return self.connected
    
    class SimpleCommandExecutor:
        def __init__(self, serial_manager: SimpleSerialManager, logger: SimpleLogger):
            self.serial_manager = serial_manager
            self.logger = logger
        
        def execute(self, command: str, **kwargs):
            self.logger.info(f"Выполнение команды: {command}")
            return self.serial_manager.send_command(command)
        
        def validate_command(self, command: str):
            return bool(command and command.strip())
    
    # Регистрируем сервисы
    container.register(ILogger, SimpleLogger)
    container.register(ISerialManager, SimpleSerialManager)
    container.register(ICommandExecutor, SimpleCommandExecutor)
    
    print("Сервисы зарегистрированы")
    
    # Разрешаем зависимости
    logger = container.resolve(ILogger)
    serial_manager = container.resolve(ISerialManager)
    command_executor = container.resolve(ICommandExecutor)
    
    print(f"Logger: {type(logger).__name__}")
    print(f"SerialManager: {type(serial_manager).__name__}")
    print(f"CommandExecutor: {type(command_executor).__name__}")
    
    # Тестируем функциональность
    serial_manager.connect("COM1")
    command_executor.execute("test command")
    
    print(f"Количество сообщений в логгере: {len(logger.messages)}")
    print()


def example_singleton_vs_transient():
    """Пример различий между singleton и transient"""
    print("=== Пример Singleton vs Transient ===")
    
    container = DIContainer()
    
    class Counter:
        def __init__(self):
            self.count = 0
        
        def increment(self):
            self.count += 1
            return self.count
    
    # Регистрируем как singleton
    container.register(ISerialManager, Counter, singleton=True)
    
    # Регистрируем как transient
    container.register(ILogger, Counter, singleton=False)
    
    # Получаем экземпляры
    singleton1 = container.resolve(ISerialManager)
    singleton2 = container.resolve(ISerialManager)
    
    transient1 = container.resolve(ILogger)
    transient2 = container.resolve(ILogger)
    
    # Тестируем singleton
    singleton1.increment()  # count = 1
    singleton2.increment()  # count = 2 (тот же экземпляр)
    
    # Тестируем transient
    transient1.increment()  # count = 1
    transient2.increment()  # count = 1 (новый экземпляр)
    
    print(f"Singleton: {singleton1.count} (должно быть 2)")
    print(f"Transient1: {transient1.count} (должно быть 1)")
    print(f"Transient2: {transient2.count} (должно быть 1)")
    print()


def example_config_loader():
    """Пример использования загрузчика конфигурации"""
    print("=== Пример загрузчика конфигурации ===")
    
    config_path = "resources/di_config.toml"
    
    if not os.path.exists(config_path):
        print(f"Файл конфигурации не найден: {config_path}")
        return
    
    # Создаем загрузчик
    config_loader = DIConfigLoader()
    
    # Валидируем конфигурацию
    errors = config_loader.validate_config(config_path)
    if errors:
        print("Ошибки валидации:")
        for error in errors:
            print(f"  - {error}")
        return
    
    print("Конфигурация валидна")
    
    # Загружаем конфигурацию
    if config_loader.load_config(config_path):
        container = config_loader.get_container()
        services = container.get_registered_services()
        print(f"Зарегистрированные сервисы: {services}")
    else:
        print("Ошибка загрузки конфигурации")
    print()


def example_global_container():
    """Пример использования глобального контейнера"""
    print("=== Пример глобального контейнера ===")
    
    # Получаем глобальный контейнер
    container = get_container()
    
    # Регистрируем сервис
    class GlobalService:
        def __init__(self):
            self.name = "GlobalService"
            print(f"Создан {self.name}")
    
    register(ILogger, GlobalService)
    
    # Разрешаем зависимость
    service = resolve(ILogger)
    print(f"Получен сервис: {service.name}")
    
    # Повторное разрешение должно вернуть тот же экземпляр (singleton)
    service2 = resolve(ILogger)
    print(f"Повторное разрешение: {service2.name}")
    print(f"Тот же экземпляр: {service is service2}")
    print()


def example_error_handling():
    """Пример обработки ошибок"""
    print("=== Пример обработки ошибок ===")
    
    container = DIContainer()
    
    # Попытка разрешить незарегистрированный сервис
    try:
        service = container.resolve(ISerialManager)
        print("Сервис разрешен (неожиданно)")
    except ValueError as e:
        print(f"Ожидаемая ошибка: {e}")
    
    # Попытка создать циклическую зависимость
    class ServiceA:
        def __init__(self, service_b):
            self.service_b = service_b
    
    class ServiceB:
        def __init__(self, service_a):
            self.service_a = service_a
    
    container.register(ISerialManager, ServiceA, dependencies={"service_b": ICommandExecutor})
    container.register(ICommandExecutor, ServiceB, dependencies={"service_a": ISerialManager})
    
    try:
        container.resolve(ISerialManager)
        print("Циклическая зависимость не обнаружена (неожиданно)")
    except RuntimeError as e:
        print(f"Ожидаемая ошибка циклической зависимости: {e}")
    print()


def main():
    """Основная функция с примерами"""
    print("🚀 Примеры использования DI контейнера\n")
    
    examples = [
        example_basic_usage,
        example_singleton_vs_transient,
        example_config_loader,
        example_global_container,
        example_error_handling
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"❌ Ошибка в примере {example.__name__}: {e}")
            print()
    
    print("✅ Все примеры выполнены")


if __name__ == "__main__":
    main()
