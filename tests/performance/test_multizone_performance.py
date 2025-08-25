"""
Тесты производительности мультизонального алгоритма
"""
import pytest
import time
import psutil
import os
import threading
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.multizone_manager import MultizoneManager
from core.command_executor import CommandExecutorFactory
from core.sequence_manager import CommandSequenceExecutor
from monitoring import MonitoringManager


class TestMultizonePerformance:
    """Тесты производительности мультизонального алгоритма"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        # Создаем моки для внешних зависимостей
        self.serial_manager = Mock()
        self.serial_manager.is_connected = True
        self.serial_manager.send_command = Mock(return_value=True)
        self.serial_manager.receive_response = Mock(return_value="ok")
        
        # Создаем MultizoneManager
        self.multizone_manager = MultizoneManager()
        
        # Создаем MonitoringManager
        self.monitoring_manager = MonitoringManager(multizone_manager=self.multizone_manager)
        
        # Создаем исполнитель команд
        self.executor = CommandExecutorFactory.create_executor(
            'basic',
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
        
        # Создаем исполнитель последовательностей
        self.sequence_executor = CommandSequenceExecutor(
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
    
    def test_single_command_execution_time(self):
        """Тест времени выполнения одиночной команды"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3])
        
        # Измеряем время выполнения
        start_time = time.time()
        
        result = self.executor.execute("og_multizone-test")
        
        execution_time = time.time() - start_time
        
        # Проверяем результат
        assert result == True
        
        # Проверяем время выполнения (должно быть менее 100ms)
        assert execution_time < 0.1, f"Время выполнения {execution_time:.3f}с превышает 100ms"
        
        print(f"Время выполнения одиночной команды: {execution_time:.3f}с")
    
    def test_sequence_execution_time(self):
        """Тест времени выполнения последовательности команд"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        # Определяем последовательность
        sequence = [
            "og_multizone-test",
            "og_multizone-paint",
            "og_multizone-rinse",
            "og_multizone-clean"
        ]
        
        # Измеряем время выполнения
        start_time = time.time()
        
        result = self.sequence_executor.run(sequence)
        
        execution_time = time.time() - start_time
        
        # Проверяем результат
        assert result == True
        
        # Проверяем время выполнения (должно быть менее 500ms)
        assert execution_time < 0.5, f"Время выполнения {execution_time:.3f}с превышает 500ms"
        
        print(f"Время выполнения последовательности: {execution_time:.3f}с")
    
    def test_memory_usage_single_operation(self):
        """Тест использования памяти при одиночной операции"""
        # Получаем текущий процесс
        process = psutil.Process(os.getpid())
        
        # Измеряем использование памяти до операции
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        # Выполняем операцию
        result = self.executor.execute("og_multizone-test")
        
        # Измеряем использование памяти после операции
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Вычисляем прирост памяти
        memory_increase = memory_after - memory_before
        
        # Проверяем результат
        assert result == True
        
        # Проверяем, что прирост памяти не превышает 10MB
        assert memory_increase < 10, f"Прирост памяти {memory_increase:.2f}MB превышает 10MB"
        
        print(f"Прирост памяти при одиночной операции: {memory_increase:.2f}MB")
    
    def test_memory_usage_multiple_operations(self):
        """Тест использования памяти при множественных операциях"""
        # Получаем текущий процесс
        process = psutil.Process(os.getpid())
        
        # Измеряем использование памяти до операций
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        # Выполняем множество операций
        for i in range(100):
            result = self.executor.execute("og_multizone-test")
            assert result == True
        
        # Измеряем использование памяти после операций
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Вычисляем прирост памяти
        memory_increase = memory_after - memory_before
        
        # Проверяем, что прирост памяти не превышает 50MB
        assert memory_increase < 50, f"Прирост памяти {memory_increase:.2f}MB превышает 50MB"
        
        print(f"Прирост памяти при 100 операциях: {memory_increase:.2f}MB")
    
    def test_concurrent_execution_performance(self):
        """Тест производительности при конкурентном выполнении"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        results = []
        execution_times = []
        
        def worker(worker_id):
            """Рабочая функция для тестирования конкурентности"""
            start_time = time.time()
            
            try:
                # Выполняем команду
                result = self.executor.execute("og_multizone-test")
                results.append(f"worker_{worker_id}_success")
            except Exception as e:
                results.append(f"worker_{worker_id}_error: {e}")
            
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
        
        # Запускаем потоки
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем результаты
        assert len(results) == 10
        assert all("success" in result for result in results)
        
        # Проверяем время выполнения (каждый поток должен завершиться менее чем за 1 секунду)
        max_execution_time = max(execution_times)
        assert max_execution_time < 1.0, f"Максимальное время выполнения {max_execution_time:.3f}с превышает 1 секунду"
        
        avg_execution_time = sum(execution_times) / len(execution_times)
        print(f"Среднее время выполнения при конкурентности: {avg_execution_time:.3f}с")
        print(f"Максимальное время выполнения: {max_execution_time:.3f}с")
    
    def test_zone_management_performance(self):
        """Тест производительности управления зонами"""
        # Измеряем время установки зон
        start_time = time.time()
        
        # Устанавливаем зоны в цикле
        for i in range(1000):
            zones = [(i % 4) + 1]  # Циклически меняем зоны
            self.multizone_manager.set_zones(zones)
            active_zones = self.multizone_manager.get_active_zones()
            zone_mask = self.multizone_manager.get_zone_mask()
        
        zone_management_time = time.time() - start_time
        
        # Проверяем время управления зонами (должно быть менее 1 секунды)
        assert zone_management_time < 1.0, f"Время управления зонами {zone_management_time:.3f}с превышает 1 секунду"
        
        print(f"Время управления 1000 зон: {zone_management_time:.3f}с")
    
    def test_monitoring_performance(self):
        """Тест производительности системы мониторинга"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        # Измеряем время записи статистики
        start_time = time.time()
        
        # Записываем статистику в цикле
        for i in range(1000):
            self.monitoring_manager.record_multizone_execution(
                zones=[1, 2, 3, 4],
                command=f"test_command_{i}",
                success=True,
                execution_time=0.1
            )
        
        recording_time = time.time() - start_time
        
        # Измеряем время получения статистики
        start_time = time.time()
        
        stats = self.monitoring_manager.get_multizone_stats()
        
        retrieval_time = time.time() - start_time
        
        # Проверяем время записи статистики (должно быть менее 1 секунды)
        assert recording_time < 1.0, f"Время записи статистики {recording_time:.3f}с превышает 1 секунду"
        
        # Проверяем время получения статистики (должно быть менее 100ms)
        assert retrieval_time < 0.1, f"Время получения статистики {retrieval_time:.3f}с превышает 100ms"
        
        # Проверяем статистику
        assert stats['total_executions'] == 1000
        assert stats['successful_executions'] == 1000
        assert stats['success_rate'] == 100.0
        
        print(f"Время записи 1000 записей статистики: {recording_time:.3f}с")
        print(f"Время получения статистики: {retrieval_time:.3f}с")
    
    def test_large_sequence_performance(self):
        """Тест производительности больших последовательностей"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        # Создаем большую последовательность
        large_sequence = []
        for i in range(100):
            large_sequence.extend([
                "og_multizone-test",
                "og_multizone-paint",
                "og_multizone-rinse"
            ])
        
        # Измеряем время выполнения
        start_time = time.time()
        
        result = self.sequence_executor.run(large_sequence)
        
        execution_time = time.time() - start_time
        
        # Проверяем результат
        assert result == True
        
        # Проверяем время выполнения (должно быть менее 5 секунд)
        assert execution_time < 5.0, f"Время выполнения {execution_time:.3f}с превышает 5 секунд"
        
        # Проверяем количество отправленных команд
        # 300 команд * 4 зоны * 2 команды на зону = 2400 команд
        assert self.serial_manager.send_command.call_count == 2400
        
        print(f"Время выполнения большой последовательности (300 команд): {execution_time:.3f}с")
    
    def test_cpu_usage_performance(self):
        """Тест использования CPU"""
        import psutil
        
        # Получаем текущий процесс
        process = psutil.Process(os.getpid())
        
        # Измеряем использование CPU до операций
        cpu_percent_before = process.cpu_percent()
        
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        # Выполняем интенсивные операции
        for i in range(1000):
            self.multizone_manager.set_zones([(i % 4) + 1])
            active_zones = self.multizone_manager.get_active_zones()
            zone_mask = self.multizone_manager.get_zone_mask()
            zone_status = self.multizone_manager.get_zone_status(1)
        
        # Измеряем использование CPU после операций
        cpu_percent_after = process.cpu_percent()
        
        # Проверяем, что использование CPU не превышает разумных пределов
        # (обычно менее 50% для одного ядра)
        assert cpu_percent_after < 50, f"Использование CPU {cpu_percent_after:.1f}% превышает 50%"
        
        print(f"Использование CPU до операций: {cpu_percent_before:.1f}%")
        print(f"Использование CPU после операций: {cpu_percent_after:.1f}%")
    
    def test_scalability_performance(self):
        """Тест масштабируемости"""
        # Тестируем с разным количеством зон
        zone_configurations = [
            [1],           # 1 зона
            [1, 2],        # 2 зоны
            [1, 2, 3],     # 3 зоны
            [1, 2, 3, 4]   # 4 зоны
        ]
        
        execution_times = []
        
        for zones in zone_configurations:
            # Устанавливаем зоны
            self.multizone_manager.set_zones(zones)
            
            # Измеряем время выполнения
            start_time = time.time()
            
            result = self.executor.execute("og_multizone-test")
            
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            # Проверяем результат
            assert result == True
        
        # Проверяем, что время выполнения растет линейно
        # (не экспоненциально)
        for i in range(1, len(execution_times)):
            time_ratio = execution_times[i] / execution_times[i-1]
            # Время не должно расти более чем в 2 раза при добавлении одной зоны
            assert time_ratio < 2.0, f"Время выполнения растет слишком быстро: {time_ratio:.2f}x"
        
        print("Время выполнения по количеству зон:")
        for i, zones in enumerate(zone_configurations):
            print(f"  {len(zones)} зон: {execution_times[i]:.3f}с")
    
    def test_memory_leak_performance(self):
        """Тест на утечки памяти"""
        import gc
        
        # Получаем текущий процесс
        process = psutil.Process(os.getpid())
        
        # Измеряем использование памяти до теста
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Выполняем множество операций
        for cycle in range(10):
            # Устанавливаем зоны
            self.multizone_manager.set_zones([1, 2, 3, 4])
            
            # Выполняем команды
            for i in range(100):
                result = self.executor.execute("og_multizone-test")
                assert result == True
            
            # Записываем статистику
            for i in range(10):
                self.monitoring_manager.record_multizone_execution(
                    zones=[1, 2, 3, 4],
                    command=f"cycle_{cycle}_command_{i}",
                    success=True,
                    execution_time=0.1
                )
            
            # Принудительно запускаем сборщик мусора
            gc.collect()
        
        # Измеряем использование памяти после теста
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Вычисляем прирост памяти
        memory_increase = memory_after - memory_before
        
        # Проверяем, что прирост памяти не превышает 20MB
        # (допускается небольшой прирост из-за кэширования)
        assert memory_increase < 20, f"Прирост памяти {memory_increase:.2f}MB превышает 20MB (возможная утечка)"
        
        print(f"Прирост памяти после 10 циклов операций: {memory_increase:.2f}MB")
    
    def test_stress_test_performance(self):
        """Стресс-тест производительности"""
        # Устанавливаем активные зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        # Создаем множество потоков
        results = []
        errors = []
        
        def stress_worker(worker_id):
            """Рабочая функция для стресс-теста"""
            try:
                for i in range(100):
                    # Выполняем команду
                    result = self.executor.execute("og_multizone-test")
                    if not result:
                        errors.append(f"worker_{worker_id}_command_{i}_failed")
                    
                    # Записываем статистику
                    self.monitoring_manager.record_multizone_execution(
                        zones=[1, 2, 3, 4],
                        command=f"stress_test_{worker_id}_{i}",
                        success=result,
                        execution_time=0.01
                    )
                
                results.append(f"worker_{worker_id}_completed")
                
            except Exception as e:
                errors.append(f"worker_{worker_id}_error: {e}")
        
        # Запускаем множество потоков
        threads = []
        for i in range(20):  # 20 потоков
            thread = threading.Thread(target=stress_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем результаты
        assert len(results) == 20, f"Завершилось только {len(results)} из 20 потоков"
        assert len(errors) == 0, f"Обнаружены ошибки: {errors}"
        
        # Проверяем статистику
        stats = self.monitoring_manager.get_multizone_stats()
        assert stats['total_executions'] == 2000  # 20 потоков * 100 команд
        
        print(f"Стресс-тест завершен: {len(results)} потоков, {len(errors)} ошибок")
        print(f"Всего выполнено команд: {stats['total_executions']}")
        print(f"Успешных выполнений: {stats['successful_executions']}")
        print(f"Процент успеха: {stats['success_rate']:.1f}%")


class TestMultizonePerformanceBenchmarks:
    """Бенчмарки производительности мультизонального алгоритма"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.serial_manager = Mock()
        self.serial_manager.is_connected = True
        self.serial_manager.send_command = Mock(return_value=True)
        
        self.multizone_manager = MultizoneManager()
        self.executor = CommandExecutorFactory.create_executor(
            'basic',
            serial_manager=self.serial_manager,
            multizone_manager=self.multizone_manager
        )
    
    def benchmark_zone_operations(self):
        """Бенчмарк операций с зонами"""
        import timeit
        
        # Устанавливаем зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        # Бенчмарк получения активных зон
        get_active_zones_time = timeit.timeit(
            lambda: self.multizone_manager.get_active_zones(),
            number=10000
        )
        
        # Бенчмарк получения битовой маски
        get_zone_mask_time = timeit.timeit(
            lambda: self.multizone_manager.get_zone_mask(),
            number=10000
        )
        
        # Бенчмарк получения статуса зоны
        get_zone_status_time = timeit.timeit(
            lambda: self.multizone_manager.get_zone_status(1),
            number=10000
        )
        
        print("Бенчмарк операций с зонами (10000 операций):")
        print(f"  get_active_zones: {get_active_zones_time:.3f}с")
        print(f"  get_zone_mask: {get_zone_mask_time:.3f}с")
        print(f"  get_zone_status: {get_zone_status_time:.3f}с")
        
        # Проверяем, что операции выполняются быстро
        assert get_active_zones_time < 1.0, "get_active_zones слишком медленно"
        assert get_zone_mask_time < 1.0, "get_zone_mask слишком медленно"
        assert get_zone_status_time < 1.0, "get_zone_status слишком медленно"
    
    def benchmark_command_execution(self):
        """Бенчмарк выполнения команд"""
        import timeit
        
        # Устанавливаем зоны
        self.multizone_manager.set_zones([1, 2, 3, 4])
        
        # Бенчмарк выполнения мультизональной команды
        multizone_command_time = timeit.timeit(
            lambda: self.executor.execute("og_multizone-test"),
            number=1000
        )
        
        print("Бенчмарк выполнения команд (1000 операций):")
        print(f"  multizone_command: {multizone_command_time:.3f}с")
        
        # Проверяем, что команды выполняются быстро
        assert multizone_command_time < 5.0, "Выполнение команд слишком медленно"
    
    def benchmark_memory_efficiency(self):
        """Бенчмарк эффективности использования памяти"""
        import sys
        import gc
        
        # Получаем текущий процесс
        process = psutil.Process(os.getpid())
        
        # Измеряем базовое использование памяти
        gc.collect()
        base_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Создаем множество объектов
        objects = []
        for i in range(10000):
            multizone_manager = MultizoneManager()
            multizone_manager.set_zones([1, 2, 3, 4])
            objects.append(multizone_manager)
        
        # Измеряем использование памяти после создания объектов
        gc.collect()
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Удаляем объекты
        objects.clear()
        gc.collect()
        
        # Измеряем использование памяти после удаления объектов
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Вычисляем метрики
        memory_increase = peak_memory - base_memory
        memory_recovery = peak_memory - final_memory
        
        print("Бенчмарк эффективности использования памяти:")
        print(f"  Базовое использование: {base_memory:.2f}MB")
        print(f"  Пиковое использование: {peak_memory:.2f}MB")
        print(f"  Финальное использование: {final_memory:.2f}MB")
        print(f"  Прирост памяти: {memory_increase:.2f}MB")
        print(f"  Восстановление памяти: {memory_recovery:.2f}MB")
        
        # Проверяем эффективность
        assert memory_increase < 100, "Слишком большой прирост памяти"
        assert memory_recovery > memory_increase * 0.8, "Плохое восстановление памяти"
