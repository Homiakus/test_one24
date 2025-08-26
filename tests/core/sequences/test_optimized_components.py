"""
@file: test_optimized_components.py
@description: Тесты для оптимизированных компонентов последовательностей
@dependencies: pytest, core.sequences.optimized_*
@created: 2024-12-19
"""

import pytest
import time
from unittest.mock import Mock, patch

from core.sequences.optimized_validator import OptimizedCommandValidator
from core.sequences.optimized_expander import OptimizedSequenceExpander
from core.sequences.optimized_searcher import OptimizedSequenceSearcher
from core.sequences.optimized_manager import OptimizedSequenceManager
from core.sequences.types import CommandType, ValidationResult


class TestOptimizedCommandValidator:
    """Тесты для оптимизированного валидатора команд"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.validator = OptimizedCommandValidator()
    
    def test_validate_command_wait_optimized(self):
        """Тест оптимизированной валидации wait команды"""
        # Первый вызов - без кеша
        result1 = self.validator.validate_command("wait 5.5")
        assert result1.is_valid
        assert result1.command_type == CommandType.WAIT
        assert result1.parsed_data["wait_time"] == 5.5
        
        # Второй вызов - должен использовать кеш
        result2 = self.validator.validate_command("wait 5.5")
        assert result2.is_valid
        assert result2.command_type == CommandType.WAIT
        
        # Проверяем статистику кеша
        stats = self.validator.get_cache_stats()
        assert stats["cache_size"] > 0
    
    def test_validate_command_if_optimized(self):
        """Тест оптимизированной валидации if команды"""
        result = self.validator.validate_command("if flag_name")
        assert result.is_valid
        assert result.command_type == CommandType.CONDITIONAL_IF
        assert result.parsed_data["flag_name"] == "flag_name"
    
    def test_validate_command_multizone_optimized(self):
        """Тест оптимизированной валидации мультизональной команды"""
        result = self.validator.validate_command("og_multizone-test_command")
        assert result.is_valid
        assert result.command_type == CommandType.MULTIZONE
        assert result.parsed_data["base_command"] == "test_command"
    
    def test_validate_sequence_optimized(self):
        """Тест оптимизированной валидации последовательности"""
        commands = ["wait 1.0", "if flag1", "test_command", "endif"]
        is_valid, errors = self.validator.validate_sequence(commands)
        assert is_valid
        assert len(errors) == 0
    
    def test_cache_management(self):
        """Тест управления кешем"""
        # Заполняем кеш
        for i in range(100):
            self.validator.validate_command(f"test_command_{i}")
        
        # Проверяем размер кеша
        stats = self.validator.get_cache_stats()
        assert stats["cache_size"] > 0
        
        # Очищаем кеш
        self.validator.clear_cache()
        stats = self.validator.get_cache_stats()
        assert stats["cache_size"] == 0


class TestOptimizedSequenceExpander:
    """Тесты для оптимизированного расширителя последовательностей"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.expander = OptimizedSequenceExpander(max_cache_size=100)
        self.sequences = {
            "seq1": ["wait 1.0", "command1"],
            "seq2": ["seq1", "command2"],
            "seq3": ["seq2", "command3"]
        }
        self.buttons_config = {
            "btn1": "button_command1",
            "btn2": "button_command2"
        }
    
    def test_expand_sequence_optimized(self):
        """Тест оптимизированного расширения последовательности"""
        # Первое расширение - без кеша
        result1 = self.expander.expand_sequence("seq3", self.sequences, self.buttons_config)
        assert len(result1) == 5  # seq3 -> seq2 -> seq1 -> 3 команды
        
        # Второе расширение - должно использовать кеш
        result2 = self.expander.expand_sequence("seq3", self.sequences, self.buttons_config)
        assert result2 == result1
        
        # Проверяем статистику
        stats = self.expander.get_cache_stats()
        assert stats["cache_hits"] > 0
    
    def test_circular_dependency_detection(self):
        """Тест обнаружения циклических зависимостей"""
        # Создаем циклическую зависимость
        circular_sequences = {
            "seq1": ["seq2"],
            "seq2": ["seq3"],
            "seq3": ["seq1"]
        }
        
        result = self.expander.expand_sequence("seq1", circular_sequences, {})
        assert len(result) == 0  # Должно вернуть пустой список
    
    def test_cache_eviction(self):
        """Тест вытеснения старых записей кеша"""
        # Заполняем кеш до предела
        for i in range(150):  # Больше max_cache_size
            self.expander.expand_sequence(f"seq{i}", {"seq{i}": [f"cmd{i}"]}, {})
        
        # Проверяем, что кеш не превышает лимит
        stats = self.expander.get_cache_stats()
        assert stats["cache_size"] <= self.expander.max_cache_size


class TestOptimizedSequenceSearcher:
    """Тесты для оптимизированного поисковика последовательностей"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.searcher = OptimizedSequenceSearcher(max_cache_size=100)
        self.sequences = {
            "test_sequence": ["wait 1.0", "test_command"],
            "multizone_sequence": ["og_multizone-command1"],
            "conditional_sequence": ["if flag1", "command1", "endif"]
        }
        self.buttons_config = {
            "test_button": "button_command"
        }
    
    def test_build_index(self):
        """Тест построения индекса"""
        self.searcher.build_index(self.sequences, self.buttons_config)
        
        # Проверяем, что индексы построены
        index_stats = self.searcher.get_index_stats()
        assert index_stats["total_commands"] > 0
        assert index_stats["total_keywords"] > 0
    
    def test_search_sequences_exact(self):
        """Тест точного поиска"""
        self.searcher.build_index(self.sequences, self.buttons_config)
        
        results = self.searcher.search_sequences("test_sequence", "exact")
        assert "test_sequence" in results
    
    def test_search_sequences_contains(self):
        """Тест поиска по содержимому"""
        self.searcher.build_index(self.sequences, self.buttons_config)
        
        results = self.searcher.search_sequences("test", "contains")
        assert len(results) > 0
        assert "test_sequence" in results
    
    def test_search_by_command_type(self):
        """Тест поиска по типу команды"""
        self.searcher.build_index(self.sequences, self.buttons_config)
        
        results = self.searcher.search_by_command_type(CommandType.WAIT)
        assert len(results) > 0
    
    def test_search_suggestions(self):
        """Тест получения предложений для автодополнения"""
        self.searcher.build_index(self.sequences, self.buttons_config)
        
        suggestions = self.searcher.get_search_suggestions("test")
        assert len(suggestions) > 0
        assert any("test" in s.lower() for s in suggestions)
    
    def test_cache_functionality(self):
        """Тест функциональности кеша"""
        self.searcher.build_index(self.sequences, self.buttons_config)
        
        # Первый поиск
        results1 = self.searcher.search_sequences("test", "contains")
        
        # Второй поиск - должен использовать кеш
        results2 = self.searcher.search_sequences("test", "contains")
        assert results1 == results2
        
        # Проверяем статистику
        stats = self.searcher.get_search_stats()
        assert stats["cache_hits"] > 0


class TestOptimizedSequenceManager:
    """Тесты для оптимизированного менеджера последовательностей"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.manager = OptimizedSequenceManager(max_cache_size=100)
    
    def test_add_sequence_optimized(self):
        """Тест оптимизированного добавления последовательности"""
        commands = ["wait 1.0", "test_command"]
        success = self.manager.add_sequence("test_seq", commands)
        assert success
        
        # Проверяем, что последовательность добавлена
        sequence = self.manager.get_sequence("test_seq")
        assert sequence == commands
    
    def test_expand_sequence_optimized(self):
        """Тест оптимизированного расширения последовательности"""
        # Добавляем последовательность
        self.manager.add_sequence("test_seq", ["wait 1.0", "command1"])
        
        # Расширяем
        expanded = self.manager.expand_sequence("test_seq")
        assert len(expanded) == 2
        assert "wait 1.0" in expanded
        assert "command1" in expanded
    
    def test_search_sequences_optimized(self):
        """Тест оптимизированного поиска последовательностей"""
        # Добавляем несколько последовательностей
        self.manager.add_sequence("seq1", ["command1"])
        self.manager.add_sequence("seq2", ["command2"])
        
        # Ищем
        results = self.manager.search_sequences("command")
        assert len(results) > 0
    
    def test_performance_metrics(self):
        """Тест сбора метрик производительности"""
        # Выполняем несколько операций
        self.manager.add_sequence("test_seq", ["wait 1.0", "command1"])
        self.manager.expand_sequence("test_seq")
        self.manager.search_sequences("test")
        
        # Получаем метрики
        metrics = self.manager.get_performance_metrics()
        assert metrics["total_operations"] > 0
        assert "cache_stats" in metrics
    
    def test_optimization_control(self):
        """Тест управления оптимизациями"""
        # Проверяем статус оптимизаций
        status = self.manager.get_optimization_status()
        assert status["caching"] == True
        assert status["indexing"] == True
        
        # Отключаем индексирование
        self.manager.enable_optimization("indexing", False)
        status = self.manager.get_optimization_status()
        assert status["indexing"] == False
    
    def test_cache_optimization(self):
        """Тест оптимизации кеша"""
        # Добавляем последовательности
        for i in range(10):
            self.manager.add_sequence(f"seq{i}", [f"cmd{i}"])
        
        # Оптимизируем кеш
        self.manager.optimize_cache()
        
        # Проверяем, что кеш работает
        metrics = self.manager.get_performance_metrics()
        assert "cache_stats" in metrics


class TestPerformanceOptimizations:
    """Тесты производительности оптимизаций"""
    
    def test_validation_performance(self):
        """Тест производительности валидации"""
        validator = OptimizedCommandValidator()
        
        # Тестируем скорость валидации
        start_time = time.time()
        for i in range(1000):
            validator.validate_command(f"wait {i}.0")
        validation_time = time.time() - start_time
        
        # Валидация должна быть быстрой
        assert validation_time < 1.0  # Менее 1 секунды для 1000 команд
    
    def test_expansion_performance(self):
        """Тест производительности расширения"""
        expander = OptimizedSequenceExpander()
        sequences = {
            "seq1": ["command1"],
            "seq2": ["seq1", "command2"],
            "seq3": ["seq2", "command3"]
        }
        
        # Тестируем скорость расширения
        start_time = time.time()
        for i in range(100):
            expander.expand_sequence("seq3", sequences, {})
        expansion_time = time.time() - start_time
        
        # Расширение должно быть быстрым
        assert expansion_time < 1.0  # Менее 1 секунды для 100 расширений
    
    def test_search_performance(self):
        """Тест производительности поиска"""
        searcher = OptimizedSequenceSearcher()
        sequences = {f"seq{i}": [f"command{i}"] for i in range(100)}
        searcher.build_index(sequences, {})
        
        # Тестируем скорость поиска
        start_time = time.time()
        for i in range(1000):
            searcher.search_sequences(f"command{i % 100}")
        search_time = time.time() - start_time
        
        # Поиск должен быть быстрым
        assert search_time < 1.0  # Менее 1 секунды для 1000 поисков


if __name__ == "__main__":
    pytest.main([__file__])
