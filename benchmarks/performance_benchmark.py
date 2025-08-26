"""
@file: performance_benchmark.py
@description: Бенчмарк производительности оптимизированных компонентов
@dependencies: core.sequences.optimized_*, time, statistics
@created: 2024-12-19
"""

import time
import statistics
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

from core.sequences.optimized_validator import OptimizedCommandValidator
from core.sequences.optimized_expander import OptimizedSequenceExpander
from core.sequences.optimized_searcher import OptimizedSequenceSearcher
from core.sequences.optimized_manager import OptimizedSequenceManager


@dataclass
class BenchmarkResult:
    """Результат бенчмарка"""
    operation: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    throughput: float  # операций в секунду


class PerformanceBenchmark:
    """
    Бенчмарк производительности для оптимизированных компонентов
    """
    
    def __init__(self):
        self.validator = OptimizedCommandValidator()
        self.expander = OptimizedSequenceExpander()
        self.searcher = OptimizedSequenceSearcher()
        self.manager = OptimizedSequenceManager()
        
        # Тестовые данные
        self.test_commands = self._generate_test_commands()
        self.test_sequences = self._generate_test_sequences()
        self.test_buttons = self._generate_test_buttons()
        
        # Результаты бенчмарков
        self.results: List[BenchmarkResult] = []
    
    def run_all_benchmarks(self, iterations: int = 1000) -> Dict[str, Any]:
        """
        Запуск всех бенчмарков
        
        Args:
            iterations: Количество итераций для каждого теста
            
        Returns:
            Словарь с результатами всех бенчмарков
        """
        print(f"🚀 Запуск бенчмарков производительности ({iterations} итераций)")
        print("=" * 60)
        
        # Бенчмарк валидации
        self._benchmark_validation(iterations)
        
        # Бенчмарк расширения
        self._benchmark_expansion(iterations)
        
        # Бенчмарк поиска
        self._benchmark_search(iterations)
        
        # Бенчмарк менеджера
        self._benchmark_manager(iterations)
        
        # Сводный отчет
        summary = self._generate_summary()
        
        print("\n" + "=" * 60)
        print("📊 СВОДНЫЙ ОТЧЕТ")
        print("=" * 60)
        self._print_summary(summary)
        
        return summary
    
    def _benchmark_validation(self, iterations: int):
        """Бенчмарк валидации команд"""
        print("\n🔍 Бенчмарк валидации команд...")
        
        # Тест валидации wait команд
        times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            self.validator.validate_command(f"wait {i % 100}.5")
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        result = self._calculate_benchmark_result("validation_wait", iterations, times)
        self.results.append(result)
        self._print_benchmark_result(result)
        
        # Тест валидации if команд
        times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            self.validator.validate_command(f"if flag_{i % 50}")
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        result = self._calculate_benchmark_result("validation_if", iterations, times)
        self.results.append(result)
        self._print_benchmark_result(result)
        
        # Тест валидации последовательностей
        times = []
        for i in range(iterations):
            commands = [f"wait {i % 10}.0", f"if flag_{i % 20}", "test_command", "endif"]
            start_time = time.perf_counter()
            self.validator.validate_sequence(commands)
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        result = self._calculate_benchmark_result("validation_sequence", iterations, times)
        self.results.append(result)
        self._print_benchmark_result(result)
    
    def _benchmark_expansion(self, iterations: int):
        """Бенчмарк расширения последовательностей"""
        print("\n📈 Бенчмарк расширения последовательностей...")
        
        # Тест расширения простых последовательностей
        times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            self.expander.expand_sequence("seq1", self.test_sequences, self.test_buttons)
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        result = self._calculate_benchmark_result("expansion_simple", iterations, times)
        self.results.append(result)
        self._print_benchmark_result(result)
        
        # Тест расширения сложных последовательностей
        times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            self.expander.expand_sequence("seq3", self.test_sequences, self.test_buttons)
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        result = self._calculate_benchmark_result("expansion_complex", iterations, times)
        self.results.append(result)
        self._print_benchmark_result(result)
    
    def _benchmark_search(self, iterations: int):
        """Бенчмарк поиска последовательностей"""
        print("\n🔎 Бенчмарк поиска последовательностей...")
        
        # Строим индекс
        self.searcher.build_index(self.test_sequences, self.test_buttons)
        
        # Тест точного поиска
        times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            self.searcher.search_sequences(f"seq{i % len(self.test_sequences)}", "exact")
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        result = self._calculate_benchmark_result("search_exact", iterations, times)
        self.results.append(result)
        self._print_benchmark_result(result)
        
        # Тест поиска по содержимому
        times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            self.searcher.search_sequences("command", "contains")
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        result = self._calculate_benchmark_result("search_contains", iterations, times)
        self.results.append(result)
        self._print_benchmark_result(result)
        
        # Тест поиска по типу
        times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            self.searcher.search_by_command_type("REGULAR")
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        result = self._calculate_benchmark_result("search_by_type", iterations, times)
        self.results.append(result)
        self._print_benchmark_result(result)
    
    def _benchmark_manager(self, iterations: int):
        """Бенчмарк менеджера последовательностей"""
        print("\n⚙️ Бенчмарк менеджера последовательностей...")
        
        # Тест добавления последовательностей
        times = []
        for i in range(iterations):
            commands = [f"wait {i % 10}.0", f"command_{i}"]
            start_time = time.perf_counter()
            self.manager.add_sequence(f"benchmark_seq_{i}", commands)
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        result = self._calculate_benchmark_result("manager_add", iterations, times)
        self.results.append(result)
        self._print_benchmark_result(result)
        
        # Тест расширения через менеджер
        times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            self.manager.expand_sequence(f"benchmark_seq_{i % 100}")
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        result = self._calculate_benchmark_result("manager_expand", iterations, times)
        self.results.append(result)
        self._print_benchmark_result(result)
        
        # Тест поиска через менеджер
        times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            self.manager.search_sequences(f"command_{i % 100}")
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        result = self._calculate_benchmark_result("manager_search", iterations, times)
        self.results.append(result)
        self._print_benchmark_result(result)
    
    def _calculate_benchmark_result(self, operation: str, iterations: int, times: List[float]) -> BenchmarkResult:
        """Вычисление результата бенчмарка"""
        total_time = sum(times)
        avg_time = total_time / iterations
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        throughput = iterations / total_time if total_time > 0 else 0.0
        
        return BenchmarkResult(
            operation=operation,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_dev=std_dev,
            throughput=throughput
        )
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Генерация сводного отчета"""
        summary = {
            'total_operations': sum(r.iterations for r in self.results),
            'total_time': sum(r.total_time for r in self.results),
            'operations': {}
        }
        
        for result in self.results:
            summary['operations'][result.operation] = {
                'iterations': result.iterations,
                'total_time': result.total_time,
                'avg_time': result.avg_time,
                'throughput': result.throughput
            }
        
        # Вычисляем общую производительность
        if summary['total_time'] > 0:
            summary['overall_throughput'] = summary['total_operations'] / summary['total_time']
        else:
            summary['overall_throughput'] = 0.0
        
        return summary
    
    def _print_benchmark_result(self, result: BenchmarkResult):
        """Вывод результата бенчмарка"""
        print(f"  {result.operation:20} | "
              f"{result.avg_time*1000:8.3f}ms | "
              f"{result.throughput:8.0f} ops/s | "
              f"{result.total_time:6.3f}s total")
    
    def _print_summary(self, summary: Dict[str, Any]):
        """Вывод сводного отчета"""
        print(f"Общее количество операций: {summary['total_operations']:,}")
        print(f"Общее время выполнения: {summary['total_time']:.3f} секунд")
        print(f"Общая производительность: {summary['overall_throughput']:.0f} операций/сек")
        
        print("\nДетальная статистика по операциям:")
        print("-" * 60)
        print(f"{'Операция':20} | {'Итерации':>10} | {'Время (с)':>10} | {'Произв-ть':>12}")
        print("-" * 60)
        
        for op_name, op_data in summary['operations'].items():
            print(f"{op_name:20} | "
                  f"{op_data['iterations']:10,} | "
                  f"{op_data['total_time']:10.3f} | "
                  f"{op_data['throughput']:12.0f} ops/s")
    
    def _generate_test_commands(self) -> List[str]:
        """Генерация тестовых команд"""
        commands = []
        
        # Wait команды
        for i in range(100):
            commands.append(f"wait {i % 50}.5")
        
        # If команды
        for i in range(50):
            commands.append(f"if flag_{i}")
        
        # Мультизональные команды
        for i in range(30):
            commands.append(f"og_multizone-command_{i}")
        
        # Обычные команды
        for i in range(200):
            commands.append(f"command_{i}")
        
        return commands
    
    def _generate_test_sequences(self) -> Dict[str, List[str]]:
        """Генерация тестовых последовательностей"""
        sequences = {
            "seq1": ["wait 1.0", "command1", "command2"],
            "seq2": ["seq1", "wait 2.0", "command3"],
            "seq3": ["seq2", "if flag1", "command4", "endif", "command5"],
            "seq4": ["seq3", "og_multizone-test", "wait 0.5"],
            "seq5": ["seq4", "seq1", "command6"]
        }
        
        # Добавляем простые последовательности
        for i in range(20):
            sequences[f"simple_seq_{i}"] = [f"command_{i}", f"wait {i % 5}.0"]
        
        return sequences
    
    def _generate_test_buttons(self) -> Dict[str, str]:
        """Генерация тестовых конфигураций кнопок"""
        buttons = {}
        
        for i in range(10):
            buttons[f"button_{i}"] = f"button_command_{i}"
        
        return buttons
    
    def run_memory_benchmark(self) -> Dict[str, Any]:
        """Бенчмарк использования памяти"""
        print("\n💾 Бенчмарк использования памяти...")
        
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Измеряем базовое использование памяти
        gc.collect()
        base_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Выполняем операции для измерения роста памяти
        for i in range(1000):
            self.validator.validate_command(f"wait {i % 100}.0")
            self.expander.expand_sequence("seq1", self.test_sequences, self.test_buttons)
            self.searcher.search_sequences("command", "contains")
        
        # Измеряем память после операций
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_result = {
            'base_memory_mb': base_memory,
            'final_memory_mb': final_memory,
            'memory_increase_mb': final_memory - base_memory,
            'memory_increase_percent': ((final_memory - base_memory) / base_memory * 100) if base_memory > 0 else 0
        }
        
        print(f"  Базовая память: {base_memory:.1f} MB")
        print(f"  Память после операций: {final_memory:.1f} MB")
        print(f"  Увеличение: {memory_result['memory_increase_mb']:.1f} MB ({memory_result['memory_increase_percent']:.1f}%)")
        
        return memory_result
    
    def run_cache_efficiency_benchmark(self) -> Dict[str, Any]:
        """Бенчмарк эффективности кеша"""
        print("\n📊 Бенчмарк эффективности кеша...")
        
        # Очищаем кеши
        self.validator.clear_cache()
        self.expander.clear_cache()
        self.searcher.clear_cache()
        
        # Первый проход - без кеша
        start_time = time.perf_counter()
        for i in range(100):
            self.validator.validate_command(f"wait {i % 50}.0")
            self.expander.expand_sequence("seq1", self.test_sequences, self.test_buttons)
            self.searcher.search_sequences("command", "contains")
        first_pass_time = time.perf_counter() - start_time
        
        # Второй проход - с кешем
        start_time = time.perf_counter()
        for i in range(100):
            self.validator.validate_command(f"wait {i % 50}.0")
            self.expander.expand_sequence("seq1", self.test_sequences, self.test_buttons)
            self.searcher.search_sequences("command", "contains")
        second_pass_time = time.perf_counter() - start_time
        
        # Вычисляем эффективность кеша
        cache_efficiency = {
            'first_pass_time': first_pass_time,
            'second_pass_time': second_pass_time,
            'time_improvement': first_pass_time - second_pass_time,
            'improvement_percent': ((first_pass_time - second_pass_time) / first_pass_time * 100) if first_pass_time > 0 else 0,
            'cache_hit_rate': self._calculate_cache_hit_rate()
        }
        
        print(f"  Время без кеша: {first_pass_time:.3f} сек")
        print(f"  Время с кешем: {second_pass_time:.3f} сек")
        print(f"  Улучшение: {cache_efficiency['time_improvement']:.3f} сек ({cache_efficiency['improvement_percent']:.1f}%)")
        
        return cache_efficiency
    
    def _calculate_cache_hit_rate(self) -> float:
        """Вычисление hit rate кеша"""
        validator_stats = self.validator.get_cache_stats()
        expander_stats = self.expander.get_cache_stats()
        searcher_stats = self.searcher.get_cache_stats()
        
        total_hits = (
            validator_stats.get('cache_hits', 0) +
            expander_stats.get('cache_hits', 0) +
            searcher_stats.get('cache_hits', 0)
        )
        
        total_requests = (
            validator_stats.get('cache_misses', 0) +
            expander_stats.get('cache_misses', 0) +
            searcher_stats.get('cache_misses', 0)
        ) + total_hits
        
        if total_requests > 0:
            return (total_hits / total_requests) * 100
        else:
            return 0.0


def main():
    """Основная функция для запуска бенчмарков"""
    benchmark = PerformanceBenchmark()
    
    # Запускаем основные бенчмарки
    summary = benchmark.run_all_benchmarks(iterations=1000)
    
    # Запускаем дополнительные бенчмарки
    memory_result = benchmark.run_memory_benchmark()
    cache_result = benchmark.run_cache_efficiency_benchmark()
    
    # Сохраняем результаты
    results = {
        'performance_summary': summary,
        'memory_benchmark': memory_result,
        'cache_efficiency': cache_result
    }
    
    print("\n🎉 Бенчмарки завершены!")
    print(f"Результаты сохранены в переменной 'results'")
    
    return results


if __name__ == "__main__":
    main()
