#!/usr/bin/env python3
"""
Исполняемые примеры использования ISerialManager

Этот файл содержит рабочие примеры использования интерфейса ISerialManager
для работы с последовательными портами.

Запуск:
    python serial_manager_example.py
"""

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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_serial_manager() -> ISerialManager:
    """Создание экземпляра Serial Manager"""
    try:
        # Прямое создание
        serial_manager = SerialManager()
        return serial_manager
    except Exception as e:
        logger.error(f"Ошибка создания Serial Manager: {e}")
        raise


def basic_connection_example():
    """Пример базового подключения к Serial порту"""
    print("\n=== Базовое подключение ===")
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
        print(f"Попытка подключения к {port}")
        
        success = serial_manager.connect(
            port=port,
            baudrate=115200,
            timeout=1.0
        )
        
        if success:
            print(f"✓ Успешно подключились к {port}")
            
            # Проверка состояния подключения
            if serial_manager.is_connected():
                print("✓ Подключение активно")
                
                # Получение информации о порте
                port_info = serial_manager.get_port_info()
                print(f"Информация о порте: {port_info}")
                
                # Отключение
                serial_manager.disconnect()
                print("✓ Отключились от порта")
            else:
                print("✗ Подключение неактивно")
        else:
            print(f"✗ Не удалось подключиться к {port}")
            
    except Exception as e:
        logger.error(f"Ошибка при работе с Serial Manager: {e}")
    finally:
        # Гарантированное отключение
        if serial_manager.is_connected():
            serial_manager.disconnect()


def send_command_example():
    """Пример отправки команды"""
    print("\n=== Отправка команды ===")
    serial_manager = create_serial_manager()
    
    try:
        # Получение доступных портов
        available_ports = serial_manager.get_available_ports()
        if not available_ports:
            print("Нет доступных портов для тестирования")
            return
        
        # Подключение
        port = available_ports[0]
        if not serial_manager.connect(port):
            print(f"Не удалось подключиться к {port}")
            return
        
        print(f"✓ Подключились к {port}")
        
        # Отправка простой команды
        command = "test_command"
        print(f"Отправка команды: {command}")
        
        success = serial_manager.send_command(command)
        
        if success:
            print(f"✓ Команда '{command}' отправлена успешно")
        else:
            print(f"✗ Ошибка отправки команды '{command}'")
            
    except Exception as e:
        logger.error(f"Ошибка отправки команды: {e}")
    finally:
        serial_manager.disconnect()


def multiple_commands_example():
    """Пример отправки множественных команд"""
    print("\n=== Множественные команды ===")
    serial_manager = create_serial_manager()
    
    commands = [
        "status",
        "version", 
        "ping",
        "reset"
    ]
    
    try:
        # Получение доступных портов
        available_ports = serial_manager.get_available_ports()
        if not available_ports:
            print("Нет доступных портов для тестирования")
            return
        
        port = available_ports[0]
        if not serial_manager.connect(port):
            print(f"Не удалось подключиться к {port}")
            return
        
        print(f"✓ Подключились к {port}")
        
        for i, command in enumerate(commands, 1):
            print(f"Отправка команды {i}/{len(commands)}: {command}")
            
            success = serial_manager.send_command(command)
            
            if success:
                print(f"  ✓ Команда '{command}' отправлена")
            else:
                print(f"  ✗ Ошибка отправки '{command}'")
            
            # Небольшая пауза между командами
            time.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Ошибка отправки команд: {e}")
    finally:
        serial_manager.disconnect()


def port_info_example():
    """Пример получения информации о портах"""
    print("\n=== Информация о портах ===")
    serial_manager = create_serial_manager()
    
    try:
        # Получение списка доступных портов
        available_ports = serial_manager.get_available_ports()
        print(f"Доступные порты: {available_ports}")
        
        if not available_ports:
            print("Нет доступных портов")
            return
        
        # Подробная информация о каждом порте
        for port in available_ports:
            print(f"\nПорт: {port}")
            
            # Попытка подключения для получения информации
            if serial_manager.connect(port):
                port_info = serial_manager.get_port_info()
                print(f"  ✓ Информация: {port_info}")
                serial_manager.disconnect()
            else:
                print(f"  ✗ Не удалось подключиться для получения информации")
                
    except Exception as e:
        logger.error(f"Ошибка получения информации о портах: {e}")


def error_handling_example():
    """Пример обработки ошибок подключения"""
    print("\n=== Обработка ошибок ===")
    serial_manager = create_serial_manager()
    
    def safe_connect(port: str, **kwargs) -> bool:
        """Безопасное подключение с обработкой ошибок"""
        try:
            return serial_manager.connect(port, **kwargs)
        except FileNotFoundError:
            print(f"  ✗ Порт {port} не найден")
            return False
        except PermissionError:
            print(f"  ✗ Нет прав доступа к порту {port}")
            return False
        except Exception as e:
            print(f"  ✗ Неизвестная ошибка подключения: {e}")
            return False
    
    def safe_send_command(command: str) -> bool:
        """Безопасная отправка команды"""
        try:
            if not serial_manager.is_connected():
                print("  ✗ Нет активного подключения")
                return False
            
            return serial_manager.send_command(command)
            
        except Exception as e:
            print(f"  ✗ Ошибка отправки команды: {e}")
            return False
    
    # Тестирование различных сценариев ошибок
    test_cases = [
        ("COM999", "Несуществующий порт"),
        ("/dev/ttyUSB999", "Несуществующий Linux порт")
    ]
    
    # Добавляем реальный порт, если есть
    available_ports = serial_manager.get_available_ports()
    if available_ports:
        test_cases.append((available_ports[0], "Нормальный порт"))
    
    for port, description in test_cases:
        print(f"\nТест: {description}")
        print(f"Порт: {port}")
        
        success = safe_connect(port)
        if success:
            print("  ✓ Подключение успешно")
            
            # Тест отправки команды
            if safe_send_command("test"):
                print("  ✓ Команда отправлена")
            else:
                print("  ✗ Ошибка отправки команды")
            
            serial_manager.disconnect()
        else:
            print("  ✗ Подключение не удалось")


def di_container_example():
    """Пример использования через DI контейнер"""
    print("\n=== DI Container пример ===")
    
    try:
        # Создание DI контейнера
        container = DIContainer()
        
        # Регистрация сервиса
        container.register(ISerialManager, SerialManager)
        
        # Получение сервиса
        serial_manager = container.resolve(ISerialManager)
        
        print("✓ Serial Manager получен через DI контейнер")
        
        # Получение доступных портов
        available_ports = serial_manager.get_available_ports()
        print(f"Доступные порты: {available_ports}")
        
        if available_ports:
            # Тест подключения
            if serial_manager.connect(available_ports[0]):
                print("✓ Подключение через DI успешно")
                serial_manager.disconnect()
            else:
                print("✗ Ошибка подключения через DI")
        
    except Exception as e:
        logger.error(f"Ошибка DI контейнера: {e}")


def run_all_examples():
    """Запуск всех примеров"""
    print("🚀 Запуск примеров ISerialManager")
    print("=" * 50)
    
    try:
        # Базовые примеры
        basic_connection_example()
        port_info_example()
        send_command_example()
        multiple_commands_example()
        
        # Примеры обработки ошибок
        error_handling_example()
        
        # DI контейнер
        di_container_example()
        
        print("\n" + "=" * 50)
        print("✅ Все примеры выполнены")
        
    except Exception as e:
        logger.error(f"Критическая ошибка при выполнении примеров: {e}")
        print(f"❌ Ошибка: {e}")


def run_tests():
    """Запуск тестов"""
    print("\n🧪 Запуск тестов ISerialManager")
    print("=" * 50)
    
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
    run_tests()
    
    # Запуск примеров
    run_all_examples()
