#!/usr/bin/env python3
"""
Инструмент диагностики и решения проблем

Этот файл содержит исполняемые функции для диагностики и решения
типичных проблем приложения.

Запуск:
    python troubleshooting_tool.py
"""

import sys
import os
import time
import logging
import platform
import psutil
import json
from datetime import datetime
from typing import Dict, Any, List

# Добавляем путь к корню проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def quick_system_check() -> bool:
    """Быстрая проверка состояния системы"""
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
    all_passed = True
    
    for check, result in checks.items():
        if isinstance(result, bool):
            status = "✓" if result else "✗"
            print(f"{status} {check}: {result}")
            if not result:
                all_passed = False
        else:
            print(f"ℹ {check}: {result}")
    
    return all_passed


def diagnose_connection_issues():
    """Диагностика проблем подключения"""
    try:
        import serial.tools.list_ports
    except ImportError:
        print("✗ Модуль pyserial не установлен")
        return
    
    print("=== Диагностика проблем подключения ===")
    
    # 1. Проверка доступных портов
    ports = list(serial.tools.list_ports.comports())
    print(f"Найдено портов: {len(ports)}")
    
    for port in ports:
        print(f"  {port.device}: {port.description}")
    
    # 2. Проверка прав доступа (Linux)
    if os.name == 'posix':
        print("\nПроверка прав доступа:")
        for port in ports:
            if os.access(port.device, os.R_OK | os.W_OK):
                print(f"  ✓ Права доступа к {port.device}: OK")
            else:
                print(f"  ✗ Нет прав доступа к {port.device}")
    
    # 3. Проверка занятости портов
    print("\nПроверка занятости портов:")
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.info['connections']:
                if hasattr(conn, 'laddr') and conn.laddr:
                    print(f"  Порт {conn.laddr.port} используется процессом {proc.info['name']} (PID: {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def diagnose_command_execution():
    """Диагностика выполнения команд"""
    try:
        from core.command_executor import BasicCommandExecutor
        from core.serial_manager import SerialManager
    except ImportError as e:
        print(f"✗ Не удалось импортировать модули: {e}")
        return
    
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


def diagnose_ui_issues():
    """Диагностика проблем UI"""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
    except ImportError as e:
        print(f"✗ Не удалось импортировать PyQt6: {e}")
        return
    
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
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"Использование памяти: {memory_info.rss / 1024 / 1024:.1f} MB")
    
    # Проверка потоков
    threads = process.threads()
    print(f"Количество потоков: {len(threads)}")
    
    for thread in threads:
        print(f"  Поток {thread.id}: {thread.user_time:.2f}s")


def diagnose_performance_issues():
    """Диагностика проблем производительности"""
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
    
    monitor_resources()
    
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


def diagnose_configuration_issues():
    """Диагностика проблем конфигурации"""
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
                    import tomli
                    config = tomli.load(f)
                else:
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


def collect_diagnostic_info() -> Dict[str, Any]:
    """Сбор диагностической информации"""
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
    with open('diagnostic_info.json', 'w', encoding='utf-8') as f:
        json.dump(diagnostic_info, f, indent=2, ensure_ascii=False)
    
    print("Диагностическая информация сохранена в diagnostic_info.json")
    return diagnostic_info


def analyze_logs():
    """Анализ логов приложения"""
    print("=== Анализ логов ===")
    
    log_file = 'logs/app.log'
    if not os.path.exists(log_file):
        print("Файл логов не найден")
        return
    
    # Чтение последних 1000 строк
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()[-1000:]
    
    # Анализ ошибок
    import re
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


def recovery_after_crash():
    """Восстановление после сбоя"""
    print("=== ВОССТАНОВЛЕНИЕ ПОСЛЕ СБОЯ ===")
    
    # Проверка файла состояния
    if os.path.exists('emergency_state.json'):
        print("Обнаружен файл экстренного состояния")
        
        try:
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


def restore_default_config():
    """Восстановление конфигурации по умолчанию"""
    print("Восстановление конфигурации по умолчанию...")
    
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
    
    try:
        with open('resources/config.toml', 'w') as f:
            json.dump(default_config, f, indent=2)
        print("✓ Конфигурация восстановлена")
    except Exception as e:
        print(f"✗ Ошибка восстановления конфигурации: {e}")


def run_full_diagnostic():
    """Запуск полной диагностики"""
    print("🔧 ЗАПУСК ПОЛНОЙ ДИАГНОСТИКИ")
    print("=" * 50)
    
    try:
        # Быстрая проверка системы
        system_ok = quick_system_check()
        
        if not system_ok:
            print("\n⚠️ Обнаружены проблемы в системе")
        
        # Диагностика подключения
        diagnose_connection_issues()
        
        # Диагностика команд
        diagnose_command_execution()
        
        # Диагностика UI
        diagnose_ui_issues()
        
        # Диагностика производительности
        diagnose_performance_issues()
        
        # Диагностика конфигурации
        diagnose_configuration_issues()
        
        # Анализ логов
        analyze_logs()
        
        # Сбор диагностической информации
        diagnostic_info = collect_diagnostic_info()
        
        print("\n" + "=" * 50)
        print("✅ Полная диагностика завершена")
        print(f"📊 Результаты сохранены в diagnostic_info.json")
        
    except Exception as e:
        logger.error(f"Критическая ошибка при диагностике: {e}")
        print(f"❌ Ошибка: {e}")


def show_help():
    """Показать справку"""
    print("""
🔧 Инструмент диагностики и решения проблем

Использование:
    python troubleshooting_tool.py [команда]

Доступные команды:
    full          - Полная диагностика системы
    system        - Быстрая проверка системы
    connection    - Диагностика проблем подключения
    commands      - Диагностика выполнения команд
    ui            - Диагностика проблем UI
    performance   - Диагностика производительности
    config        - Диагностика конфигурации
    logs          - Анализ логов
    emergency     - Экстренная остановка
    recovery      - Восстановление после сбоя
    help          - Показать эту справку

Примеры:
    python troubleshooting_tool.py full
    python troubleshooting_tool.py connection
    python troubleshooting_tool.py emergency
""")


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        'full': run_full_diagnostic,
        'system': quick_system_check,
        'connection': diagnose_connection_issues,
        'commands': diagnose_command_execution,
        'ui': diagnose_ui_issues,
        'performance': diagnose_performance_issues,
        'config': diagnose_configuration_issues,
        'logs': analyze_logs,
        'emergency': emergency_shutdown,
        'recovery': recovery_after_crash,
        'help': show_help
    }
    
    if command in commands:
        commands[command]()
    else:
        print(f"❌ Неизвестная команда: {command}")
        show_help()


if __name__ == "__main__":
    main()
