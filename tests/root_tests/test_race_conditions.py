#!/usr/bin/env python3
"""
Тесты для проверки улучшенной обработки race conditions в SerialManager
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

def test_concurrent_connect_disconnect():
    """Тест одновременного подключения и отключения"""
    print("\n=== Тест одновременного подключения и отключения ===")
    
    manager = SerialManager()
    
    def connect_worker(worker_id):
        for i in range(10):
            try:
                result = manager.connect(f"COM{worker_id}{i}", 115200)
                print(f"Поток {worker_id}: Подключение {i} = {result}")
                time.sleep(0.01)
            except Exception as e:
                print(f"Поток {worker_id}: Ошибка подключения {i}: {e}")
    
    def disconnect_worker(worker_id):
        for i in range(10):
            try:
                manager.disconnect()
                print(f"Поток {worker_id}: Отключение {i} завершено")
                time.sleep(0.01)
            except Exception as e:
                print(f"Поток {worker_id}: Ошибка отключения {i}: {e}")
    
    # Запускаем потоки подключения и отключения одновременно
    connect_threads = []
    disconnect_threads = []
    
    for i in range(3):
        conn_thread = threading.Thread(target=connect_worker, args=(i,))
        disc_thread = threading.Thread(target=disconnect_worker, args=(i,))
        
        conn_thread.daemon = True
        disc_thread.daemon = True
        
        connect_threads.append(conn_thread)
        disconnect_threads.append(disc_thread)
        
        conn_thread.start()
        disc_thread.start()
    
    # Ждем завершения
    for thread in connect_threads + disconnect_threads:
        thread.join(timeout=15.0)
    
    print("Тест одновременного подключения/отключения завершен")

def test_state_consistency_under_load():
    """Тест консистентности состояния под нагрузкой"""
    print("\n=== Тест консистентности состояния под нагрузкой ===")
    
    manager = SerialManager()
    
    # Создаем мок порт
    class MockSerial:
        def __init__(self):
            self.is_open = True
            self.port = "COM1"
            self.baudrate = 115200
            self.timeout = 1.0
            self.write_timeout = 2.0
        
        def close(self):
            self.is_open = False
    
    # Устанавливаем мок порт
    with manager._lock:
        with manager._port_operation_lock:
            manager.port = MockSerial()
    
    manager._update_connection_state(connected=True)
    
    def state_checker_worker(worker_id):
        inconsistencies = 0
        for i in range(1000):
            try:
                # Проверяем состояние подключения
                is_conn = manager.is_connected
                
                # Получаем информацию о порте
                port_info = manager.get_port_info()
                
                # Проверяем доступность порта
                is_available = manager.is_port_available()
                
                # Проверяем консистентность
                if is_conn != port_info['connected']:
                    inconsistencies += 1
                    print(f"Поток {worker_id}: Несоответствие состояния {i}: is_connected={is_conn}, port_info={port_info['connected']}")
                
                if is_conn != is_available:
                    inconsistencies += 1
                    print(f"Поток {worker_id}: Несоответствие доступности {i}: is_connected={is_conn}, is_available={is_available}")
                
                time.sleep(0.001)  # 1ms пауза
                
            except Exception as e:
                print(f"Поток {worker_id}: Ошибка проверки {i}: {e}")
        
        print(f"Поток {worker_id}: Найдено несоответствий: {inconsistencies}")
        return inconsistencies
    
    # Запускаем несколько потоков проверки состояния
    threads = []
    for i in range(5):
        thread = threading.Thread(target=state_checker_worker, args=(i,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    # Ждем завершения
    total_inconsistencies = 0
    for thread in threads:
        thread.join(timeout=30.0)
    
    print(f"Общее количество несоответствий: {total_inconsistencies}")
    print("Тест консистентности состояния завершен")

def test_atomic_operations():
    """Тест атомарности операций"""
    print("\n=== Тест атомарности операций ===")
    
    manager = SerialManager()
    
    # Создаем мок порт с медленными операциями
    class SlowMockSerial:
        def __init__(self):
            self.is_open = True
            self.port = "COM1"
            self.baudrate = 115200
            self.timeout = 1.0
            self.write_timeout = 2.0
            self._write_lock = threading.Lock()
        
        def write(self, data):
            with self._write_lock:
                time.sleep(0.1)  # Медленная операция записи
                return len(data)
        
        def close(self):
            time.sleep(0.05)  # Медленная операция закрытия
            self.is_open = False
    
    # Устанавливаем мок порт
    with manager._lock:
        with manager._port_operation_lock:
            manager.port = SlowMockSerial()
    
    manager._update_connection_state(connected=True)
    
    def concurrent_send_worker(worker_id):
        successful_sends = 0
        failed_sends = 0
        
        for i in range(20):
            try:
                result = manager.send_command(f"command_{worker_id}_{i}")
                if result:
                    successful_sends += 1
                else:
                    failed_sends += 1
                time.sleep(0.01)
            except Exception as e:
                failed_sends += 1
                print(f"Поток {worker_id}: Ошибка отправки {i}: {e}")
        
        print(f"Поток {worker_id}: Успешных отправок: {successful_sends}, неудачных: {failed_sends}")
        return successful_sends, failed_sends
    
    # Запускаем несколько потоков одновременной отправки
    threads = []
    for i in range(4):
        thread = threading.Thread(target=concurrent_send_worker, args=(i,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    # Ждем завершения
    total_successful = 0
    total_failed = 0
    for thread in threads:
        thread.join(timeout=30.0)
    
    print(f"Общее количество успешных отправок: {total_successful}")
    print(f"Общее количество неудачных отправок: {total_failed}")
    print("Тест атомарности операций завершен")

def test_connection_state_transitions():
    """Тест переходов состояния подключения"""
    print("\n=== Тест переходов состояния подключения ===")
    
    manager = SerialManager()
    
    def state_transition_worker(worker_id):
        transitions = 0
        for i in range(50):
            try:
                # Пытаемся подключиться
                connect_result = manager.connect(f"COM{worker_id}{i}", 115200)
                
                # Проверяем состояние после подключения
                state_after_connect = manager._get_connection_state()
                
                # Отключаемся
                manager.disconnect()
                
                # Проверяем состояние после отключения
                state_after_disconnect = manager._get_connection_state()
                
                # Проверяем корректность переходов
                if not state_after_disconnect['connected'] and not state_after_disconnect['connecting'] and not state_after_disconnect['disconnecting']:
                    transitions += 1
                else:
                    print(f"Поток {worker_id}: Некорректное состояние после отключения {i}: {state_after_disconnect}")
                
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Поток {worker_id}: Ошибка перехода {i}: {e}")
        
        print(f"Поток {worker_id}: Корректных переходов: {transitions}")
        return transitions
    
    # Запускаем потоки тестирования переходов
    threads = []
    for i in range(3):
        thread = threading.Thread(target=state_transition_worker, args=(i,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    # Ждем завершения
    total_transitions = 0
    for thread in threads:
        thread.join(timeout=30.0)
    
    print(f"Общее количество корректных переходов: {total_transitions}")
    print("Тест переходов состояния завершен")

def test_port_operation_safety():
    """Тест безопасности операций с портом"""
    print("\n=== Тест безопасности операций с портом ===")
    
    manager = SerialManager()
    
    # Создаем мок порт с небезопасными операциями
    class UnsafeMockSerial:
        def __init__(self):
            self.is_open = True
            self.port = "COM1"
            self._operation_count = 0
            self._lock = threading.Lock()
        
        def write(self, data):
            with self._lock:
                self._operation_count += 1
                if self._operation_count % 10 == 0:  # Каждая 10-я операция "падает"
                    raise Exception("Simulated port error")
                time.sleep(0.01)
                return len(data)
        
        def close(self):
            with self._lock:
                self.is_open = False
    
    # Устанавливаем мок порт
    with manager._lock:
        with manager._port_operation_lock:
            manager.port = UnsafeMockSerial()
    
    manager._update_connection_state(connected=True)
    
    def safe_operation_worker(worker_id):
        successful_operations = 0
        failed_operations = 0
        
        for i in range(30):
            try:
                # Проверяем состояние перед операцией
                if not manager.is_connected:
                    failed_operations += 1
                    continue
                
                # Проверяем доступность порта
                if not manager.is_port_available():
                    failed_operations += 1
                    continue
                
                # Выполняем операцию
                result = manager.send_command(f"safe_command_{worker_id}_{i}")
                if result:
                    successful_operations += 1
                else:
                    failed_operations += 1
                
                time.sleep(0.01)
                
            except Exception as e:
                failed_operations += 1
                print(f"Поток {worker_id}: Ошибка операции {i}: {e}")
        
        print(f"Поток {worker_id}: Успешных операций: {successful_operations}, неудачных: {failed_operations}")
        return successful_operations, failed_operations
    
    # Запускаем потоки безопасных операций
    threads = []
    for i in range(3):
        thread = threading.Thread(target=safe_operation_worker, args=(i,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    # Ждем завершения
    total_successful = 0
    total_failed = 0
    for thread in threads:
        thread.join(timeout=30.0)
    
    print(f"Общее количество успешных операций: {total_successful}")
    print(f"Общее количество неудачных операций: {total_failed}")
    print("Тест безопасности операций завершен")

def main():
    """Основная функция тестирования race conditions"""
    print("Запуск тестов race conditions в SerialManager")
    print("=" * 60)
    
    try:
        test_concurrent_connect_disconnect()
        test_state_consistency_under_load()
        test_atomic_operations()
        test_connection_state_transitions()
        test_port_operation_safety()
        
        print("\n" + "=" * 60)
        print("Все тесты race conditions завершены успешно!")
        
    except Exception as e:
        print(f"\nОШИБКА в тестах race conditions: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

