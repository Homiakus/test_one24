#!/usr/bin/env python3
"""
Инструменты для профилирования и мониторинга производительности

Этот модуль содержит исполняемые инструменты для анализа и оптимизации
производительности приложения управления устройством.
"""

import sys
import time
import json
import cProfile
import pstats
import psutil
import threading
import tracemalloc
from pathlib import Path
from typing import Dict, List, Optional, Callable
from collections import defaultdict
from datetime import datetime
import argparse

try:
    from PyQt6.QtCore import QTimer, QElapsedTimer, QObject, pyqtSignal
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    print("PyQt6 недоступен, UI компоненты отключены")


class PerformanceMonitor:
    """Монитор производительности"""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = None
        self.monitoring = False
        self.monitor_thread = None
        self.metrics_data = defaultdict(list)
        self.lock = threading.Lock()
    
    def start_measurement(self, name: str):
        """Начать измерение"""
        self.start_time = time.time()
        self.metrics[name] = {
            'start_time': self.start_time,
            'cpu_start': psutil.cpu_percent(),
            'memory_start': psutil.Process().memory_info().rss
        }
    
    def end_measurement(self, name: str) -> dict:
        """Завершить измерение и вернуть метрики"""
        if name not in self.metrics:
            return {}
        
        end_time = time.time()
        cpu_end = psutil.cpu_percent()
        memory_end = psutil.Process().memory_info().rss
        
        result = {
            'duration': end_time - self.metrics[name]['start_time'],
            'cpu_usage': cpu_end - self.metrics[name]['cpu_start'],
            'memory_usage': memory_end - self.metrics[name]['memory_start']
        }
        
        # Сохранение метрики
        with self.lock:
            self.metrics_data[name].append({
                'timestamp': time.time(),
                **result
            })
        
        return result
    
    def start_monitoring(self, interval: float = 1.0):
        """Запуск непрерывного мониторинга"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self, interval: float):
        """Цикл мониторинга"""
        while self.monitoring:
            with self.lock:
                self.metrics_data['system'].append({
                    'timestamp': time.time(),
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'memory_used': psutil.virtual_memory().used,
                    'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
                })
            
            time.sleep(interval)
    
    def get_metric_stats(self, name: str) -> Dict:
        """Получение статистики метрики"""
        with self.lock:
            values = self.metrics_data[name]
            if not values:
                return {}
            
            durations = [m.get('duration', 0) for m in values if 'duration' in m]
            if durations:
                return {
                    'count': len(durations),
                    'min': min(durations),
                    'max': max(durations),
                    'avg': sum(durations) / len(durations),
                    'latest': durations[-1] if durations else None
                }
            
            return {'count': len(values)}
    
    def save_metrics(self, filename: str = "performance_metrics.json"):
        """Сохранение метрик в файл"""
        with self.lock:
            data = {
                'timestamp': datetime.now().isoformat(),
                'metrics': dict(self.metrics_data)
            }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"Метрики сохранены в {filename}")


class Profiler:
    """Профилировщик приложения"""
    
    def __init__(self):
        self.profiler = None
        self.stats_file = None
    
    def start_profiling(self):
        """Начать профилирование"""
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        print("Профилирование запущено")
    
    def stop_profiling(self, stats_file: str = "profile_stats.prof"):
        """Остановить профилирование и сохранить результаты"""
        if not self.profiler:
            print("Профилирование не запущено")
            return
        
        self.profiler.disable()
        self.stats_file = stats_file
        self.profiler.dump_stats(stats_file)
        print(f"Результаты профилирования сохранены в {stats_file}")
    
    def print_stats(self, top_n: int = 20):
        """Вывод статистики профилирования"""
        if not self.stats_file:
            print("Нет файла статистики")
            return
        
        stats = pstats.Stats(self.stats_file)
        stats.sort_stats('cumulative')
        stats.print_stats(top_n)
    
    def profile_function(self, func: Callable, *args, **kwargs):
        """Профилирование конкретной функции"""
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        
        # Вывод статистики
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)
        
        return result


class MemoryProfiler:
    """Профилировщик памяти"""
    
    def __init__(self):
        self.tracemalloc_started = False
    
    def start_tracking(self):
        """Начать отслеживание памяти"""
        tracemalloc.start()
        self.tracemalloc_started = True
        print("Отслеживание памяти запущено")
    
    def stop_tracking(self):
        """Остановить отслеживание памяти"""
        if not self.tracemalloc_started:
            print("Отслеживание памяти не запущено")
            return
        
        current, peak = tracemalloc.get_traced_memory()
        print(f"Текущее использование памяти: {current / 1024 / 1024:.1f} MB")
        print(f"Пиковое использование памяти: {peak / 1024 / 1024:.1f} MB")
        
        # Получение топ-10 блоков памяти
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        print("\nТоп-10 блоков памяти:")
        for stat in top_stats[:10]:
            print(stat)
        
        tracemalloc.stop()
        self.tracemalloc_started = False
    
    def take_snapshot(self):
        """Создать снимок памяти"""
        if not self.tracemalloc_started:
            print("Отслеживание памяти не запущено")
            return None
        
        return tracemalloc.take_snapshot()


class PerformanceAlerts:
    """Система алертов производительности"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 500 * 1024 * 1024,  # 500MB
            'response_time': 1000,  # 1s
        }
        self.alert_callbacks = []
    
    def add_alert_callback(self, callback: Callable):
        """Добавление callback для алертов"""
        self.alert_callbacks.append(callback)
    
    def check_alerts(self):
        """Проверка алертов"""
        for metric_name, threshold in self.thresholds.items():
            stats = self.monitor.get_metric_stats(metric_name)
            if stats and stats.get('latest', 0) > threshold:
                self._trigger_alert(metric_name, stats['latest'], threshold)
    
    def _trigger_alert(self, metric: str, value: float, threshold: float):
        """Срабатывание алерта"""
        alert = {
            'metric': metric,
            'value': value,
            'threshold': threshold,
            'timestamp': time.time()
        }
        
        print(f"🚨 АЛЕРТ: {metric} = {value} (порог: {threshold})")
        
        for callback in self.alert_callbacks:
            callback(alert)


if PYQT6_AVAILABLE:
    class UIPerformanceMonitor(QObject):
        """Монитор производительности UI"""
        
        def __init__(self):
            super().__init__()
            self.timer = QElapsedTimer()
            self.measurements = []
        
        def measure_ui_operation(self, operation_name: str):
            """Измерение времени выполнения UI операции"""
            def decorator(func):
                def wrapper(*args, **kwargs):
                    self.timer.start()
                    result = func(*args, **kwargs)
                    elapsed = self.timer.elapsed()
                    
                    self.measurements.append({
                        'operation': operation_name,
                        'time': elapsed
                    })
                    
                    if elapsed > 100:  # Предупреждение при медленных операциях
                        print(f"⚠️ Медленная UI операция: {operation_name} - {elapsed}ms")
                    
                    return result
                return wrapper
            return decorator


class PerformanceBenchmark:
    """Бенчмарк производительности"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.results = {}
    
    def benchmark_function(self, name: str, func: Callable, *args, iterations: int = 100, **kwargs):
        """Бенчмарк функции"""
        print(f"Запуск бенчмарка: {name}")
        
        times = []
        for i in range(iterations):
            self.monitor.start_measurement(f"{name}_iter_{i}")
            start_time = time.time()
            
            result = func(*args, **kwargs)
            
            end_time = time.time()
            self.monitor.end_measurement(f"{name}_iter_{i}")
            
            times.append(end_time - start_time)
        
        # Статистика
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        self.results[name] = {
            'iterations': iterations,
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'total_time': sum(times)
        }
        
        print(f"Результаты {name}:")
        print(f"  Итераций: {iterations}")
        print(f"  Среднее время: {avg_time:.6f}s")
        print(f"  Минимальное время: {min_time:.6f}s")
        print(f"  Максимальное время: {max_time:.6f}s")
        print(f"  Общее время: {sum(times):.6f}s")
    
    def save_results(self, filename: str = "benchmark_results.json"):
        """Сохранение результатов бенчмарка"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"Результаты бенчмарка сохранены в {filename}")


def demo_performance_tools():
    """Демонстрация инструментов производительности"""
    print("🚀 Демонстрация инструментов производительности")
    print("=" * 50)
    
    # Создание монитора
    monitor = PerformanceMonitor()
    
    # Демонстрация измерения
    print("\n1. Измерение производительности функции:")
    monitor.start_measurement("demo_function")
    
    def demo_function():
        """Демонстрационная функция"""
        time.sleep(0.1)
        return "done"
    
    result = demo_function()
    metrics = monitor.end_measurement("demo_function")
    print(f"Результат: {result}")
    print(f"Метрики: {metrics}")
    
    # Демонстрация профилирования
    print("\n2. Профилирование функции:")
    profiler = Profiler()
    profiler.profile_function(demo_function)
    
    # Демонстрация бенчмарка
    print("\n3. Бенчмарк функции:")
    benchmark = PerformanceBenchmark()
    benchmark.benchmark_function("demo_function", demo_function, iterations=10)
    
    # Демонстрация мониторинга
    print("\n4. Мониторинг системы (5 секунд):")
    monitor.start_monitoring(interval=0.5)
    time.sleep(5)
    monitor.stop_monitoring()
    
    # Сохранение результатов
    monitor.save_metrics("demo_metrics.json")
    benchmark.save_results("demo_benchmark.json")
    
    print("\n✅ Демонстрация завершена!")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="Инструменты производительности")
    parser.add_argument("--demo", action="store_true", help="Запустить демонстрацию")
    parser.add_argument("--monitor", type=int, default=0, help="Время мониторинга в секундах")
    parser.add_argument("--profile", action="store_true", help="Запустить профилирование")
    parser.add_argument("--benchmark", action="store_true", help="Запустить бенчмарк")
    
    args = parser.parse_args()
    
    if args.demo:
        demo_performance_tools()
    elif args.monitor > 0:
        monitor = PerformanceMonitor()
        print(f"Мониторинг системы в течение {args.monitor} секунд...")
        monitor.start_monitoring()
        time.sleep(args.monitor)
        monitor.stop_monitoring()
        monitor.save_metrics()
    elif args.profile:
        profiler = Profiler()
        profiler.start_profiling()
        print("Профилирование запущено. Нажмите Ctrl+C для остановки.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            profiler.stop_profiling()
            profiler.print_stats()
    elif args.benchmark:
        benchmark = PerformanceBenchmark()
        
        # Бенчмарк различных операций
        def test_function():
            return sum(range(1000))
        
        benchmark.benchmark_function("test_function", test_function, iterations=1000)
        benchmark.save_results()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
