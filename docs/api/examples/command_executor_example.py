#!/usr/bin/env python3
"""
Исполняемые примеры использования ICommandExecutor

Этот файл содержит рабочие примеры использования интерфейса ICommandExecutor
для выполнения команд на устройстве.

Запуск:
    python command_executor_example.py
"""

import sys
import os
import time
import logging
import threading
import queue
from typing import Optional, Dict, Any

# Добавляем путь к корню проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from core.interfaces import ICommandExecutor, ISerialManager
from core.command_executor import BasicCommandExecutor, InteractiveCommandExecutor
from core.serial_manager import SerialManager
from core.di.container import DIContainer

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_command_executor() -> ICommandExecutor:
    """Создание экземпляра Command Executor"""
    try:
        # Создание зависимостей
        serial_manager = SerialManager()
        
        # Создание Command Executor
        command_executor = BasicCommandExecutor(
            serial_manager=serial_manager,
            tag_manager=None,
            tag_dialog_manager=None
        )
        
        return command_executor
    except Exception as e:
        logger.error(f"Ошибка создания Command Executor: {e}")
        raise


def create_interactive_executor() -> ICommandExecutor:
    """Создание интерактивного Command Executor"""
    try:
        serial_manager = SerialManager()
        
        interactive_executor = InteractiveCommandExecutor(
            serial_manager=serial_manager,
            tag_manager=None,
            tag_dialog_manager=None
        )
        
        return interactive_executor
    except Exception as e:
        logger.error(f"Ошибка создания Interactive Command Executor: {e}")
        raise


def basic_execution_example():
    """Пример базового выполнения команды"""
    print("\n=== Базовое выполнение команды ===")
    command_executor = create_command_executor()
    
    try:
        # Получение доступных портов
        available_ports = command_executor.serial_manager.get_available_ports()
        if not available_ports:
            print("Нет доступных портов для тестирования")
            return
        
        # Подключение к устройству
        port = available_ports[0]
        if not command_executor.serial_manager.connect(port):
            print(f"Не удалось подключиться к {port}")
            return
        
        print(f"✓ Подключились к {port}")
        
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


def execution_with_params_example():
    """Пример выполнения команды с дополнительными параметрами"""
    print("\n=== Выполнение с параметрами ===")
    command_executor = create_command_executor()
    
    try:
        # Получение доступных портов
        available_ports = command_executor.serial_manager.get_available_ports()
        if not available_ports:
            print("Нет доступных портов для тестирования")
            return
        
        port = available_ports[0]
        if not command_executor.serial_manager.connect(port):
            print(f"Не удалось подключиться к {port}")
            return
        
        print(f"✓ Подключились к {port}")
        
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


def batch_execution_example():
    """Пример пакетного выполнения команд"""
    print("\n=== Пакетное выполнение команд ===")
    command_executor = create_command_executor()
    
    commands = [
        "status",
        "version",
        "ping",
        "config"
    ]
    
    try:
        # Получение доступных портов
        available_ports = command_executor.serial_manager.get_available_ports()
        if not available_ports:
            print("Нет доступных портов для тестирования")
            return
        
        port = available_ports[0]
        if not command_executor.serial_manager.connect(port):
            print(f"Не удалось подключиться к {port}")
            return
        
        print(f"✓ Подключились к {port}")
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


def validation_example():
    """Пример валидации команд перед выполнением"""
    print("\n=== Валидация команд ===")
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
            
            # Попытка выполнения (если есть подключение)
            available_ports = command_executor.serial_manager.get_available_ports()
            if available_ports and command_executor.serial_manager.connect(available_ports[0]):
                success = command_executor.execute(command)
                print(f"  Результат выполнения: {'✓' if success else '✗'}")
                command_executor.serial_manager.disconnect()
            else:
                print("  ✗ Не удалось подключиться для выполнения")
        else:
            print("  ✗ Команда невалидна")


def custom_validation_example():
    """Пример валидации с пользовательскими правилами"""
    print("\n=== Пользовательская валидация ===")
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


def detailed_results_example():
    """Пример получения детальных результатов выполнения"""
    print("\n=== Детальные результаты ===")
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
        # Получение доступных портов
        available_ports = command_executor.serial_manager.get_available_ports()
        if not available_ports:
            print("Нет доступных портов для тестирования")
            return
        
        port = available_ports[0]
        if not command_executor.serial_manager.connect(port):
            print(f"Не удалось подключиться к {port}")
            return
        
        print(f"✓ Подключились к {port}")
        
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


def async_execution_example():
    """Пример асинхронного выполнения команд"""
    print("\n=== Асинхронное выполнение ===")
    command_executor = create_command_executor()
    
    def async_execute_command(command: str, result_queue: queue.Queue):
        """Асинхронное выполнение команды"""
        try:
            success = command_executor.execute(command)
            result_queue.put((command, success, None))
        except Exception as e:
            result_queue.put((command, False, str(e)))
    
    try:
        # Получение доступных портов
        available_ports = command_executor.serial_manager.get_available_ports()
        if not available_ports:
            print("Нет доступных портов для тестирования")
            return
        
        port = available_ports[0]
        if not command_executor.serial_manager.connect(port):
            print(f"Не удалось подключиться к {port}")
            return
        
        print(f"✓ Подключились к {port}")
        
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


def error_handling_example():
    """Пример обработки различных типов ошибок"""
    print("\n=== Обработка ошибок ===")
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


def error_recovery_example():
    """Пример восстановления после ошибок"""
    print("\n=== Восстановление после ошибок ===")
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
        # Получение доступных портов
        available_ports = command_executor.serial_manager.get_available_ports()
        if not available_ports:
            print("Нет доступных портов для тестирования")
            return
        
        port = available_ports[0]
        if not command_executor.serial_manager.connect(port):
            print(f"Не удалось подключиться к {port}")
            return
        
        print(f"✓ Подключились к {port}")
        
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


def di_container_example():
    """Пример использования через DI контейнер"""
    print("\n=== DI Container пример ===")
    
    try:
        # Создание DI контейнера
        container = DIContainer()
        
        # Регистрация сервисов
        container.register(ISerialManager, SerialManager)
        container.register(ICommandExecutor, BasicCommandExecutor)
        
        # Получение сервиса
        command_executor = container.resolve(ICommandExecutor)
        
        print("✓ Command Executor получен через DI контейнер")
        
        # Получение доступных портов
        available_ports = command_executor.serial_manager.get_available_ports()
        print(f"Доступные порты: {available_ports}")
        
        if available_ports:
            # Тест подключения
            if command_executor.serial_manager.connect(available_ports[0]):
                print("✓ Подключение через DI успешно")
                
                # Тест выполнения команды
                success = command_executor.execute("status")
                print(f"Результат выполнения: {'✓' if success else '✗'}")
                
                command_executor.serial_manager.disconnect()
            else:
                print("✗ Ошибка подключения через DI")
        
    except Exception as e:
        logger.error(f"Ошибка DI контейнера: {e}")


def run_all_examples():
    """Запуск всех примеров"""
    print("🚀 Запуск примеров ICommandExecutor")
    print("=" * 50)
    
    try:
        # Базовые примеры
        basic_execution_example()
        execution_with_params_example()
        batch_execution_example()
        
        # Валидация
        validation_example()
        custom_validation_example()
        
        # Результаты и асинхронность
        detailed_results_example()
        async_execution_example()
        
        # Обработка ошибок
        error_handling_example()
        error_recovery_example()
        
        # DI контейнер
        di_container_example()
        
        print("\n" + "=" * 50)
        print("✅ Все примеры выполнены")
        
    except Exception as e:
        logger.error(f"Критическая ошибка при выполнении примеров: {e}")
        print(f"❌ Ошибка: {e}")


def run_tests():
    """Запуск тестов"""
    print("\n🧪 Запуск тестов ICommandExecutor")
    print("=" * 50)
    
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
        available_ports = command_executor.serial_manager.get_available_ports()
        if available_ports and command_executor.serial_manager.connect(available_ports[0]):
            # Тест выполнения
            success = command_executor.execute("status")
            assert isinstance(success, bool), "Результат выполнения должен быть булевым"
            
            command_executor.serial_manager.disconnect()
        
        print("✓ Тесты интеграции пройдены")

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
    run_tests()
    
    # Запуск примеров
    run_all_examples()
