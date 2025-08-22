#!/usr/bin/env python3
"""
Тесты для проверки улучшенного управления потоками в SerialManager
"""
import threading
import time
import logging
import sys
import os
import signal

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.serial_manager import SerialManager, SerialReader, InterruptibleThread, ThreadManager
import serial

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_interruptible_thread():
    """Тест InterruptibleThread с proper shutdown"""
    print("\n=== Тест InterruptibleThread ===")
    
    def long_running_task():
        for i in range(100):
            time.sleep(0.1)
            if threading.current_thread()._stop_event.is_set():
                print(f"Поток прерван на итерации {i}")
                break
        print("Долгая задача завершена")
    
    # Создаем поток с таймаутом
    thread = InterruptibleThread(
        target=long_running_task,
        name="test_thread",
        timeout=2.0
    )
    
    print("Запуск потока...")
    thread.start()
    
    # Ждем немного и останавливаем
    time.sleep(0.5)
    print("Остановка потока...")
    success = thread.stop(timeout=1.0)
    
    print(f"Поток остановлен: {success}")
    print(f"Время выполнения: {thread.get_runtime():.3f}s")
    print(f"Прерван: {thread.is_interrupted()}")
    
    return success

def test_thread_manager():
    """Тест ThreadManager"""
    print("\n=== Тест ThreadManager ===")
    
    manager = ThreadManager()
    
    def worker_task(worker_id):
        for i in range(20):
            time.sleep(0.1)
            if threading.current_thread()._stop_event.is_set():
                print(f"Работник {worker_id} прерван на итерации {i}")
                break
        print(f"Работник {worker_id} завершен")
    
    # Запускаем несколько потоков
    threads = []
    for i in range(3):
        thread = manager.start_thread(
            name=f"worker_{i}",
            target=worker_task,
            args=(i,),
            timeout=3.0
        )
        threads.append(thread)
    
    print("Потоки запущены")
    time.sleep(0.5)
    
    # Получаем информацию о потоках
    thread_info = manager.get_thread_info()
    print(f"Информация о потоках: {thread_info}")
    
    # Останавливаем все потоки
    print("Остановка всех потоков...")
    results = manager.stop_all_threads(timeout=5.0)
    print(f"Результаты остановки: {results}")
    
    # Очищаем завершенные потоки
    manager.cleanup()
    
    return all(results.values())

def test_proper_shutdown_vs_daemon():
    """Тест proper shutdown vs daemon threads"""
    print("\n=== Тест proper shutdown vs daemon threads ===")
    
    def daemon_task():
        time.sleep(2.0)
        print("Daemon задача завершена")
    
    def proper_task():
        for i in range(20):
            time.sleep(0.1)
            if threading.current_thread()._stop_event.is_set():
                print(f"Proper задача прервана на итерации {i}")
                break
        print("Proper задача завершена")
    
    # Daemon поток (неправильный подход)
    daemon_thread = threading.Thread(target=daemon_task)
    daemon_thread.daemon = True
    daemon_thread.start()
    
    # Proper поток (правильный подход)
    proper_thread = InterruptibleThread(target=proper_task, timeout=1.0)
    proper_thread.start()
    
    print("Потоки запущены")
    time.sleep(0.5)
    
    # Останавливаем proper поток
    print("Остановка proper потока...")
    proper_success = proper_thread.stop(timeout=1.0)
    
    print(f"Proper поток остановлен: {proper_success}")
    print("Daemon поток будет завершен при выходе из программы")
    
    return proper_success

def test_timeout_join_operations():
    """Тест timeout для join() операций"""
    print("\n=== Тест timeout для join() операций ===")
    
    def blocking_task():
        time.sleep(5.0)  # Блокирующая задача
        print("Блокирующая задача завершена")
    
    # Тест с таймаутом
    thread = InterruptibleThread(target=blocking_task, timeout=1.0)
    thread.start()
    
    print("Запуск блокирующей задачи...")
    start_time = time.time()
    
    # Пытаемся остановить с таймаутом
    success = thread.stop(timeout=1.0)
    end_time = time.time()
    
    print(f"Остановка за {end_time - start_time:.3f}s")
    print(f"Успешно остановлен: {success}")
    
    return not success  # Ожидаем неудачу из-за таймаута

def test_interrupt_mechanism():
    """Тест interrupt mechanism"""
    print("\n=== Тест interrupt mechanism ===")
    
    def interruptible_task():
        for i in range(50):
            time.sleep(0.1)
            if threading.current_thread()._stop_event.is_set():
                print(f"Задача прервана на итерации {i}")
                return
        print("Задача завершена полностью")
    
    thread = InterruptibleThread(target=interruptible_task, timeout=10.0)
    thread.start()
    
    print("Задача запущена")
    time.sleep(0.3)
    
    # Прерываем поток
    print("Прерывание потока...")
    thread.interrupt()
    
    # Проверяем состояние
    print(f"Прерван: {thread.is_interrupted()}")
    
    # Ждем завершения
    success = thread.stop(timeout=2.0)
    print(f"Поток остановлен: {success}")
    
    return success

def test_serial_reader_interrupt():
    """Тест interrupt mechanism в SerialReader"""
    print("\n=== Тест interrupt mechanism в SerialReader ===")
    
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
    time.sleep(0.5)
    
    print("Поток чтения запущен")
    
    # Прерываем поток
    print("Прерывание потока чтения...")
    reader.interrupt()
    
    # Останавливаем поток
    start_time = time.time()
    reader.stop()
    end_time = time.time()
    
    print(f"Поток чтения остановлен за {end_time - start_time:.3f}s")
    
    return not reader.isRunning()

def test_graceful_shutdown():
    """Тест graceful shutdown"""
    print("\n=== Тест graceful shutdown ===")
    
    manager = SerialManager()
    
    def background_task():
        for i in range(30):
            time.sleep(0.1)
            if threading.current_thread()._stop_event.is_set():
                print(f"Фоновая задача прервана на итерации {i}")
                break
        print("Фоновая задача завершена")
    
    # Запускаем несколько фоновых потоков
    for i in range(3):
        manager._thread_manager.start_thread(
            name=f"background_{i}",
            target=background_task,
            timeout=2.0
        )
    
    print("Фоновые потоки запущены")
    time.sleep(0.5)
    
    # Выполняем graceful shutdown
    print("Выполнение graceful shutdown...")
    start_time = time.time()
    manager.graceful_shutdown(timeout=5.0)
    end_time = time.time()
    
    print(f"Graceful shutdown завершен за {end_time - start_time:.3f}s")
    
    # Проверяем, что все потоки остановлены
    thread_info = manager.get_thread_info()
    print(f"Информация о потоках после shutdown: {thread_info}")
    
    return len(thread_info) == 0

def test_signal_handlers():
    """Тест обработчиков сигналов"""
    print("\n=== Тест обработчиков сигналов ===")
    
    manager = SerialManager()
    
    def signal_task():
        for i in range(20):
            time.sleep(0.1)
            if threading.current_thread()._stop_event.is_set():
                print(f"Сигнальная задача прервана на итерации {i}")
                break
        print("Сигнальная задача завершена")
    
    # Запускаем поток
    manager._thread_manager.start_thread(
        name="signal_test",
        target=signal_task,
        timeout=3.0
    )
    
    print("Поток запущен")
    time.sleep(0.3)
    
    # Симулируем получение сигнала (только для тестирования)
    print("Симуляция получения сигнала...")
    try:
        # В реальности это будет вызвано системой
        manager.graceful_shutdown(timeout=3.0)
        print("Graceful shutdown выполнен")
    except Exception as e:
        print(f"Ошибка при graceful shutdown: {e}")
        return False
    
    return True

def test_thread_lifecycle():
    """Тест жизненного цикла потоков"""
    print("\n=== Тест жизненного цикла потоков ===")
    
    manager = ThreadManager()
    
    def lifecycle_task():
        print("Задача началась")
        time.sleep(1.0)
        print("Задача завершилась")
    
    # Запуск
    thread = manager.start_thread("lifecycle", lifecycle_task, timeout=5.0)
    print(f"Поток запущен: {thread.is_alive()}")
    
    # Проверка информации
    info = manager.get_thread_info()
    print(f"Информация о потоке: {info}")
    
    # Ожидание завершения
    time.sleep(1.5)
    
    # Очистка
    manager.cleanup()
    info_after = manager.get_thread_info()
    print(f"Информация после очистки: {info_after}")
    
    return len(info_after) == 0

def main():
    """Основная функция тестирования управления потоками"""
    print("Запуск тестов управления потоками в SerialManager")
    print("=" * 70)
    
    tests = [
        ("InterruptibleThread", test_interruptible_thread),
        ("ThreadManager", test_thread_manager),
        ("Proper shutdown vs daemon", test_proper_shutdown_vs_daemon),
        ("Timeout join operations", test_timeout_join_operations),
        ("Interrupt mechanism", test_interrupt_mechanism),
        ("SerialReader interrupt", test_serial_reader_interrupt),
        ("Graceful shutdown", test_graceful_shutdown),
        ("Signal handlers", test_signal_handlers),
        ("Thread lifecycle", test_thread_lifecycle),
    ]
    
    results = {}
    
    try:
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_func()
                results[test_name] = result
                status = "✅ ПРОЙДЕН" if result else "❌ НЕ ПРОЙДЕН"
                print(f"{status}: {test_name}")
            except Exception as e:
                results[test_name] = False
                print(f"❌ ОШИБКА: {test_name} - {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 70)
        print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅" if result else "❌"
            print(f"{status} {test_name}")
        
        print(f"\nПройдено: {passed}/{total} тестов")
        
        if passed == total:
            print("🎉 Все тесты управления потоками прошли успешно!")
        else:
            print("⚠️  Некоторые тесты не прошли")
            
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

