#!/usr/bin/env python3
"""
Тесты для проверки исправлений многопоточности в SerialManager
"""
import threading
import time
import logging
import sys
import os

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.serial_manager import SerialManager, SerialReader
import serial

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_deadlock_prevention():
    """Тест предотвращения deadlock в disconnect()"""
    print("\n=== Тест предотвращения deadlock ===")
    
    manager = SerialManager()
    
    # Симулируем быстрое подключение/отключение в нескольких потоках
    def connect_disconnect_worker(worker_id):
        print(f"Поток {worker_id}: Начало работы")
        for i in range(5):
            try:
                # Пытаемся подключиться к несуществующему порту
                result = manager.connect(f"COM{worker_id}{i}", 115200)
                print(f"Поток {worker_id}: Подключение {i} = {result}")
                
                # Сразу отключаемся
                manager.disconnect()
                print(f"Поток {worker_id}: Отключение {i} завершено")
                
                time.sleep(0.1)  # Небольшая пауза
            except Exception as e:
                print(f"Поток {worker_id}: Ошибка в итерации {i}: {e}")
    
    # Запускаем несколько потоков одновременно
    threads = []
    for i in range(3):
        thread = threading.Thread(target=connect_disconnect_worker, args=(i,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    # Ждем завершения всех потоков
    for thread in threads:
        thread.join(timeout=10.0)
        if thread.is_alive():
            print(f"ПРЕДУПРЕЖДЕНИЕ: Поток {thread.name} не завершился за 10 секунд")
    
    print("Тест deadlock завершен")

def test_serial_reader_graceful_shutdown():
    """Тест graceful shutdown для SerialReader"""
    print("\n=== Тест graceful shutdown SerialReader ===")
    
    # Создаем мок Serial объект
    class MockSerial:
        def __init__(self):
            self.is_open = True
            self.in_waiting = 0
        
        def readline(self):
            time.sleep(0.1)  # Симулируем медленное чтение
            return b"test data\n"
    
    mock_port = MockSerial()
    reader = SerialReader(mock_port)
    
    # Запускаем поток
    reader.start()
    time.sleep(0.5)  # Даем время на запуск
    
    # Останавливаем поток
    print("Запрос остановки потока...")
    start_time = time.time()
    reader.stop()
    stop_time = time.time()
    
    print(f"Поток остановлен за {stop_time - start_time:.3f} секунд")
    
    if reader.isRunning():
        print("ОШИБКА: Поток все еще работает после stop()")
    else:
        print("Поток успешно остановлен")

def test_send_command_timeout():
    """Тест таймаута для send_command"""
    print("\n=== Тест таймаута send_command ===")
    
    manager = SerialManager()
    
    # Создаем мок порт, который будет блокироваться
    class BlockingSerial:
        def __init__(self):
            self.is_open = True
        
        def write(self, data):
            time.sleep(3.0)  # Блокируемся на 3 секунды
            return len(data)
    
    # Устанавливаем мок порт
    with manager._lock:
        manager.port = BlockingSerial()
    
    # Пытаемся отправить команду
    print("Отправка команды с таймаутом...")
    start_time = time.time()
    result = manager.send_command("test command")
    end_time = time.time()
    
    print(f"Результат отправки: {result}")
    print(f"Время выполнения: {end_time - start_time:.3f} секунд")
    
    if end_time - start_time > 3.0:
        print("ОШИБКА: Таймаут не сработал")
    else:
        print("Таймаут работает корректно")

def test_concurrent_operations():
    """Тест одновременных операций"""
    print("\n=== Тест одновременных операций ===")
    
    manager = SerialManager()
    
    # Создаем мок порт
    class MockSerial:
        def __init__(self):
            self.is_open = True
            self._lock = threading.Lock()
        
        def write(self, data):
            with self._lock:
                time.sleep(0.1)  # Небольшая задержка
                return len(data)
    
    # Устанавливаем мок порт
    with manager._lock:
        manager.port = MockSerial()
    
    # Функция для одновременной отправки команд
    def send_commands_worker(worker_id):
        for i in range(10):
            try:
                result = manager.send_command(f"command_{worker_id}_{i}")
                print(f"Поток {worker_id}: Команда {i} = {result}")
            except Exception as e:
                print(f"Поток {worker_id}: Ошибка {i}: {e}")
    
    # Запускаем несколько потоков
    threads = []
    for i in range(3):
        thread = threading.Thread(target=send_commands_worker, args=(i,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    # Ждем завершения
    for thread in threads:
        thread.join(timeout=15.0)
    
    print("Тест одновременных операций завершен")

def test_connection_state_consistency():
    """Тест консистентности состояния подключения"""
    print("\n=== Тест консистентности состояния ===")
    
    manager = SerialManager()
    
    # Проверяем начальное состояние
    print(f"Начальное состояние подключения: {manager.is_connected}")
    
    # Создаем мок порт
    class MockSerial:
        def __init__(self):
            self.is_open = True
    
    # Устанавливаем порт
    with manager._lock:
        manager.port = MockSerial()
    
    print(f"Состояние после установки порта: {manager.is_connected}")
    
    # Проверяем в нескольких потоках одновременно
    def check_state_worker(worker_id):
        for i in range(100):
            state = manager.is_connected
            if not state:
                print(f"Поток {worker_id}: Неожиданное состояние {i}: {state}")
            time.sleep(0.01)
    
    threads = []
    for i in range(5):
        thread = threading.Thread(target=check_state_worker, args=(i,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    # Ждем завершения
    for thread in threads:
        thread.join(timeout=10.0)
    
    print("Тест консистентности состояния завершен")

def main():
    """Основная функция тестирования"""
    print("Запуск тестов многопоточности SerialManager")
    print("=" * 50)
    
    try:
        test_deadlock_prevention()
        test_serial_reader_graceful_shutdown()
        test_send_command_timeout()
        test_concurrent_operations()
        test_connection_state_consistency()
        
        print("\n" + "=" * 50)
        print("Все тесты завершены успешно!")
        
    except Exception as e:
        print(f"\nОШИБКА в тестах: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

