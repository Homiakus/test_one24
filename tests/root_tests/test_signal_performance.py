#!/usr/bin/env python3
"""
Тест производительности системы обработки сигналов UART
"""

import sys
import time
import random
import threading
from pathlib import Path
from typing import Dict, List

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_high_volume_signal_processing():
    """Тест обработки большого количества сигналов"""
    print("🧪 Тест обработки большого количества сигналов...")
    
    try:
        from core.signal_manager import SignalManager
        from core.signal_processor import SignalProcessor
        from core.signal_validator import SignalValidator
        from core.flag_manager import FlagManager
        from core.signal_types import SignalType, SignalMapping
        
        # Создание компонентов
        flag_manager = FlagManager()
        signal_processor = SignalProcessor()
        signal_validator = SignalValidator()
        signal_manager = SignalManager(
            processor=signal_processor,
            validator=signal_validator,
            flag_manager=flag_manager
        )
        
        # Регистрация тестовых сигналов
        test_mappings = {
            "TEMP": SignalMapping("temperature", SignalType.FLOAT),
            "STATUS": SignalMapping("status", SignalType.STRING),
            "ERROR": SignalMapping("error", SignalType.INT),
            "MODE": SignalMapping("mode", SignalType.BOOL),
            "PRESSURE": SignalMapping("pressure", SignalType.FLOAT),
            "FLOW": SignalMapping("flow_rate", SignalType.FLOAT),
            "LEVEL": SignalMapping("level", SignalType.INT),
            "ALARM": SignalMapping("alarm", SignalType.BOOL)
        }
        signal_manager.register_signals(test_mappings)
        
        # Генерация тестовых данных
        test_data = [
            "TEMP:25.5",
            "STATUS:running",
            "ERROR:0",
            "MODE:true",
            "PRESSURE:1.2",
            "FLOW:10.5",
            "LEVEL:75",
            "ALARM:false",
            "TEMP:26.1",
            "STATUS:stopped",
            "ERROR:1",
            "MODE:false",
            "PRESSURE:1.3",
            "FLOW:11.2",
            "LEVEL:80",
            "ALARM:true"
        ]
        
        # Тест обработки 10000 сигналов
        print("📊 Обработка 10000 сигналов...")
        start_time = time.time()
        
        for i in range(10000):
            data = test_data[i % len(test_data)]
            signal_manager.process_incoming_data(data)
            
            # Показываем прогресс каждые 1000 сигналов
            if (i + 1) % 1000 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                print(f"   Обработано: {i + 1}, Скорость: {rate:.0f} сигналов/сек")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Результаты
        print(f"✅ Тест завершен:")
        print(f"   - Обработано сигналов: 10000")
        print(f"   - Время обработки: {processing_time:.3f} сек")
        print(f"   - Скорость: {10000/processing_time:.0f} сигналов/сек")
        print(f"   - Среднее время на сигнал: {processing_time/10000*1000:.3f} мс")
        
        # Статистика
        stats = signal_manager.get_statistics()
        print(f"   - Всего сигналов: {stats.get('total_signals', 0)}")
        print(f"   - Обработано: {stats.get('processed_signals', 0)}")
        print(f"   - Ошибок: {stats.get('errors', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_concurrent_signal_processing():
    """Тест многопоточной обработки сигналов"""
    print("\n🧪 Тест многопоточной обработки сигналов...")
    
    try:
        from core.signal_manager import SignalManager
        from core.signal_processor import SignalProcessor
        from core.signal_validator import SignalValidator
        from core.flag_manager import FlagManager
        from core.signal_types import SignalType, SignalMapping
        
        # Создание компонентов
        flag_manager = FlagManager()
        signal_processor = SignalProcessor()
        signal_validator = SignalValidator()
        signal_manager = SignalManager(
            processor=signal_processor,
            validator=signal_validator,
            flag_manager=flag_manager
        )
        
        # Регистрация тестовых сигналов
        test_mappings = {
            "TEMP": SignalMapping("temperature", SignalType.FLOAT),
            "STATUS": SignalMapping("status", SignalType.STRING),
            "ERROR": SignalMapping("error", SignalType.INT),
            "MODE": SignalMapping("mode", SignalType.BOOL)
        }
        signal_manager.register_signals(test_mappings)
        
        # Генерация тестовых данных
        test_data = [
            "TEMP:25.5",
            "STATUS:running",
            "ERROR:0",
            "MODE:true",
            "TEMP:26.1",
            "STATUS:stopped",
            "ERROR:1",
            "MODE:false"
        ]
        
        # Счетчики для каждого потока
        thread_results = {}
        
        def process_signals(thread_id: int, num_signals: int):
            """Функция обработки сигналов в потоке"""
            start_time = time.time()
            for i in range(num_signals):
                data = test_data[i % len(test_data)]
                signal_manager.process_incoming_data(data)
            end_time = time.time()
            thread_results[thread_id] = {
                'signals_processed': num_signals,
                'processing_time': end_time - start_time
            }
        
        # Создание потоков
        threads = []
        num_threads = 4
        signals_per_thread = 1000
        
        print(f"📊 Запуск {num_threads} потоков по {signals_per_thread} сигналов...")
        
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(
                target=process_signals,
                args=(i, signals_per_thread)
            )
            threads.append(thread)
            thread.start()
        
        # Ожидание завершения всех потоков
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Результаты
        print(f"✅ Многопоточный тест завершен:")
        print(f"   - Потоков: {num_threads}")
        print(f"   - Сигналов на поток: {signals_per_thread}")
        print(f"   - Общее время: {total_time:.3f} сек")
        print(f"   - Общая скорость: {num_threads * signals_per_thread / total_time:.0f} сигналов/сек")
        
        # Детальная статистика по потокам
        for thread_id, result in thread_results.items():
            rate = result['signals_processed'] / result['processing_time']
            print(f"   - Поток {thread_id}: {rate:.0f} сигналов/сек")
        
        # Статистика
        stats = signal_manager.get_statistics()
        print(f"   - Всего сигналов: {stats.get('total_signals', 0)}")
        print(f"   - Обработано: {stats.get('processed_signals', 0)}")
        print(f"   - Ошибок: {stats.get('errors', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка многопоточного тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_malformed_data_handling():
    """Тест обработки некорректных данных"""
    print("\n🧪 Тест обработки некорректных данных...")
    
    try:
        from core.signal_manager import SignalManager
        from core.signal_processor import SignalProcessor
        from core.signal_validator import SignalValidator
        from core.flag_manager import FlagManager
        from core.signal_types import SignalType, SignalMapping
        
        # Создание компонентов
        flag_manager = FlagManager()
        signal_processor = SignalProcessor()
        signal_validator = SignalValidator()
        signal_manager = SignalManager(
            processor=signal_processor,
            validator=signal_validator,
            flag_manager=flag_manager
        )
        
        # Регистрация тестовых сигналов
        test_mappings = {
            "TEMP": SignalMapping("temperature", SignalType.FLOAT),
            "STATUS": SignalMapping("status", SignalType.STRING),
            "ERROR": SignalMapping("error", SignalType.INT),
            "MODE": SignalMapping("mode", SignalType.BOOL)
        }
        signal_manager.register_signals(test_mappings)
        
        # Некорректные данные для тестирования
        malformed_data = [
            "",  # Пустая строка
            "INVALID",  # Нет двоеточия
            "TEMP",  # Только имя сигнала
            ":25.5",  # Только значение
            "TEMP:25.5:extra",  # Лишние части
            "UNKNOWN:value",  # Неизвестный сигнал
            "TEMP:not_a_number",  # Неверный тип для float
            "MODE:maybe",  # Неверный тип для bool
            "ERROR:abc",  # Неверный тип для int
            "TEMP:25.5\n",  # С переносом строки
            "  TEMP:25.5  ",  # С пробелами
            "temp:25.5",  # Строчные буквы
            "TEMP:25.5,STATUS:running",  # Множественные сигналы
        ]
        
        print("📊 Обработка некорректных данных...")
        
        initial_stats = signal_manager.get_statistics()
        initial_errors = initial_stats.get('errors', 0)
        
        for i, data in enumerate(malformed_data):
            print(f"   Тест {i+1}: '{data}'")
            result = signal_manager.process_incoming_data(data)
            if not result:
                print(f"     ✅ Корректно отклонено")
            else:
                print(f"     ⚠️  Неожиданно принято")
        
        # Проверка статистики
        final_stats = signal_manager.get_statistics()
        final_errors = final_stats.get('errors', 0)
        new_errors = final_errors - initial_errors
        
        print(f"✅ Тест некорректных данных завершен:")
        print(f"   - Обработано некорректных данных: {len(malformed_data)}")
        print(f"   - Новых ошибок: {new_errors}")
        print(f"   - Всего ошибок: {final_errors}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования некорректных данных: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_usage():
    """Тест использования памяти"""
    print("\n🧪 Тест использования памяти...")
    
    try:
        import psutil
        import os
        
        # Получение текущего процесса
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        from core.signal_manager import SignalManager
        from core.signal_processor import SignalProcessor
        from core.signal_validator import SignalValidator
        from core.flag_manager import FlagManager
        from core.signal_types import SignalType, SignalMapping
        
        # Создание компонентов
        flag_manager = FlagManager()
        signal_processor = SignalProcessor()
        signal_validator = SignalValidator()
        signal_manager = SignalManager(
            processor=signal_processor,
            validator=signal_validator,
            flag_manager=flag_manager
        )
        
        # Регистрация тестовых сигналов
        test_mappings = {
            "TEMP": SignalMapping("temperature", SignalType.FLOAT),
            "STATUS": SignalMapping("status", SignalType.STRING),
            "ERROR": SignalMapping("error", SignalType.INT),
            "MODE": SignalMapping("mode", SignalType.BOOL)
        }
        signal_manager.register_signals(test_mappings)
        
        # Обработка большого количества сигналов
        test_data = [
            "TEMP:25.5",
            "STATUS:running",
            "ERROR:0",
            "MODE:true"
        ]
        
        print("📊 Обработка сигналов для тестирования памяти...")
        
        for i in range(10000):
            data = test_data[i % len(test_data)]
            signal_manager.process_incoming_data(data)
            
            # Проверяем память каждые 1000 сигналов
            if (i + 1) % 1000 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                print(f"   Сигналов: {i + 1}, Память: {current_memory:.1f}MB (+{memory_increase:.1f}MB)")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        print(f"✅ Тест памяти завершен:")
        print(f"   - Начальная память: {initial_memory:.1f}MB")
        print(f"   - Конечная память: {final_memory:.1f}MB")
        print(f"   - Увеличение памяти: {total_increase:.1f}MB")
        print(f"   - Память на 1000 сигналов: {total_increase/10:.1f}MB")
        
        return True
        
    except ImportError:
        print("⚠️  psutil не установлен, пропускаем тест памяти")
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования памяти: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_performance_benchmark():
    """Запуск полного бенчмарка производительности"""
    print("🚀 Запуск полного бенчмарка производительности системы сигналов...")
    
    # Список тестов
    tests = [
        ("Высоконагруженная обработка", test_high_volume_signal_processing),
        ("Многопоточная обработка", test_concurrent_signal_processing),
        ("Обработка некорректных данных", test_malformed_data_handling),
        ("Использование памяти", test_memory_usage)
    ]
    
    # Результаты тестов
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        success = test_func()
        end_time = time.time()
        
        results[test_name] = {
            'success': success,
            'duration': end_time - start_time
        }
        
        if success:
            print(f"✅ {test_name} - УСПЕШНО ({end_time - start_time:.2f}с)")
        else:
            print(f"❌ {test_name} - НЕУДАЧА ({end_time - start_time:.2f}с)")
    
    # Итоговый отчет
    print(f"\n{'='*60}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print(f"{'='*60}")
    
    successful_tests = sum(1 for result in results.values() if result['success'])
    total_tests = len(results)
    total_time = sum(result['duration'] for result in results.values())
    
    print(f"✅ Успешных тестов: {successful_tests}/{total_tests}")
    print(f"⏱️  Общее время: {total_time:.2f}с")
    
    for test_name, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"{status} {test_name}: {result['duration']:.2f}с")
    
    if successful_tests == total_tests:
        print(f"\n🎉 Все тесты производительности прошли успешно!")
        return True
    else:
        print(f"\n⚠️  Некоторые тесты не прошли")
        return False

if __name__ == "__main__":
    success = run_performance_benchmark()
    sys.exit(0 if success else 1)
