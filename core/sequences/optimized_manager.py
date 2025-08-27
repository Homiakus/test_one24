"""
@file: optimized_manager.py
@description: Оптимизированный менеджер последовательностей с улучшенными алгоритмами
@dependencies: core.interfaces, core.sequences.types, optimized_validator, optimized_expander, optimized_searcher
@created: 2024-12-19
"""

import threading
import time
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

from core.interfaces import ISequenceManager
from core.sequences.types import ValidationResult, CommandType
from .optimized_validator import OptimizedCommandValidator
from .optimized_expander import OptimizedSequenceExpander
from .optimized_searcher import OptimizedSequenceSearcher


@dataclass
class PerformanceMetrics:
    """Метрики производительности"""
    validation_time: float = 0.0
    expansion_time: float = 0.0
    search_time: float = 0.0
    cache_hit_rate: float = 0.0
    total_operations: int = 0


class OptimizedSequenceManager(ISequenceManager):
    """
    Оптимизированный менеджер последовательностей
    
    Объединяет все оптимизации:
    - Быстрая валидация с кешированием
    - Эффективное расширение с многоуровневым кешем
    - Индексированный поиск
    - Мониторинг производительности
    """
    
    def __init__(self, max_cache_size: int = 10000):
        self.max_cache_size = max_cache_size
        
        # Оптимизированные компоненты
        self._validator = OptimizedCommandValidator()
        self._expander = OptimizedSequenceExpander(max_cache_size=max_cache_size)
        self._searcher = OptimizedSequenceSearcher(max_cache_size=max_cache_size)
        
        # Данные последовательностей
        self._sequences: Dict[str, List[str]] = {}
        self._buttons_config: Dict[str, str] = {}
        
        # Блокировки для thread-safety
        self._sequences_lock = threading.RLock()
        self._buttons_lock = threading.RLock()
        
        # Метрики производительности
        self._metrics = PerformanceMetrics()
        self._metrics_lock = threading.Lock()
        
        # Флаги оптимизации
        self._optimizations_enabled = {
            'caching': True,
            'indexing': True,
            'preprocessing': True,
            'parallel_processing': False  # Пока отключено
        }
    
    def add_sequence(self, sequence_name: str, commands: List[str]) -> bool:
        """
        Добавление последовательности с оптимизациями
        
        Временная сложность: O(n) где n - количество команд
        """
        if not sequence_name or not commands:
            return False
        
        # Валидируем последовательность
        start_time = time.time()
        is_valid, errors = self._validator.validate_sequence(commands)
        validation_time = time.time() - start_time
        
        if not is_valid:
            return False
        
        with self._sequences_lock:
            self._sequences[sequence_name] = commands.copy()
            
            # Обновляем индексы поиска
            if self._optimizations_enabled['indexing']:
                self._searcher.build_index(self._sequences, self._buttons_config)
        
        # Обновляем метрики
        self._update_metrics('validation_time', validation_time)
        
        return True
    
    def remove_sequence(self, sequence_name: str) -> bool:
        """
        Удаление последовательности с обновлением индексов
        """
        with self._sequences_lock:
            if sequence_name not in self._sequences:
                return False
            
            del self._sequences[sequence_name]
            
            # Обновляем индексы поиска
            if self._optimizations_enabled['indexing']:
                self._searcher.build_index(self._sequences, self._buttons_config)
            
            return True
    
    def get_sequence(self, sequence_name: str) -> Optional[List[str]]:
        """
        Получение последовательности с кешированием
        """
        with self._sequences_lock:
            return self._sequences.get(sequence_name, []).copy()
    
    def get_all_sequences(self) -> Dict[str, List[str]]:
        """
        Получение всех последовательностей
        """
        with self._sequences_lock:
            return {name: commands.copy() for name, commands in self._sequences.items()}
    
    def expand_sequence(self, sequence_name: str) -> List[str]:
        """
        Расширение последовательности с оптимизациями
        
        Временная сложность: O(1) для кешированных, O(n) для новых
        """
        if not sequence_name:
            return []
        
        start_time = time.time()
        
        # Используем оптимизированный расширитель
        result = self._expander.expand_sequence(
            sequence_name, self._sequences, self._buttons_config
        )
        
        expansion_time = time.time() - start_time
        self._update_metrics('expansion_time', expansion_time)
        
        return result
    
    def validate_sequence(self, sequence_name: str) -> Tuple[bool, List[str]]:
        """
        Валидация последовательности с оптимизациями
        """
        if not sequence_name:
            return False, ["Пустое имя последовательности"]
        
        start_time = time.time()
        
        # Получаем команды
        commands = self.get_sequence(sequence_name)
        if not commands:
            return False, [f"Последовательность '{sequence_name}' не найдена"]
        
        # Валидируем с оптимизированным валидатором
        is_valid, errors = self._validator.validate_sequence(commands)
        
        validation_time = time.time() - start_time
        self._update_metrics('validation_time', validation_time)
        
        return is_valid, errors
    
    def search_sequences(self, query: str, search_type: str = "contains", 
                        max_results: int = 100) -> List[str]:
        """
        Поиск последовательностей с оптимизациями
        
        Временная сложность: O(1) для точного поиска, O(log n) для индексированного
        """
        if not query:
            return []
        
        start_time = time.time()
        
        # Используем оптимизированный поисковик
        results = self._searcher.search_sequences(query, search_type, max_results)
        
        search_time = time.time() - start_time
        self._update_metrics('search_time', search_time)
        
        return results
    
    def search_by_command_type(self, command_type: CommandType) -> List[str]:
        """
        Поиск по типу команды
        """
        return self._searcher.search_by_command_type(command_type)
    
    def search_by_keyword(self, keyword: str) -> List[str]:
        """
        Поиск по ключевому слову
        """
        return self._searcher.search_by_keyword(keyword)
    
    def get_search_suggestions(self, partial_query: str, max_suggestions: int = 10) -> List[str]:
        """
        Получение предложений для автодополнения
        """
        return self._searcher.get_search_suggestions(partial_query, max_suggestions)
    
    def add_button_config(self, button_name: str, command: str) -> bool:
        """
        Добавление конфигурации кнопки
        """
        if not button_name or not command:
            return False
        
        with self._buttons_lock:
            self._buttons_config[button_name] = command
            
            # Обновляем индексы поиска
            if self._optimizations_enabled['indexing']:
                self._searcher.build_index(self._sequences, self._buttons_config)
            
            return True
    
    def remove_button_config(self, button_name: str) -> bool:
        """
        Удаление конфигурации кнопки
        """
        with self._buttons_lock:
            if button_name not in self._buttons_config:
                return False
            
            del self._buttons_config[button_name]
            
            # Обновляем индексы поиска
            if self._optimizations_enabled['indexing']:
                self._searcher.build_index(self._sequences, self._buttons_config)
            
            return True
    
    def get_button_config(self, button_name: str) -> Optional[str]:
        """
        Получение конфигурации кнопки
        """
        with self._buttons_lock:
            return self._buttons_config.get(button_name)
    
    def get_all_button_configs(self) -> Dict[str, str]:
        """
        Получение всех конфигураций кнопок
        """
        with self._buttons_lock:
            return self._buttons_config.copy()
    
    def clear_cache(self):
        """
        Очистка всех кешей
        """
        self._validator.clear_cache()
        self._expander.clear_cache()
        self._searcher.clear_cache()
    
    def optimize_cache(self):
        """
        Оптимизация кешей для улучшения производительности
        """
        self._expander.optimize_cache()
        
        # Пересчитываем статистику кеша
        self._update_cache_metrics()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Получение метрик производительности
        """
        with self._metrics_lock:
            metrics = self._metrics.__dict__.copy()
            
            # Добавляем статистику кешей
            cache_stats = {
                'validator_cache': self._validator.get_cache_stats(),
                'expander_cache': self._expander.get_cache_stats(),
                'searcher_cache': self._searcher.get_cache_stats(),
                'searcher_index': self._searcher.get_index_stats()
            }
            
            metrics['cache_stats'] = cache_stats
            metrics['optimizations_enabled'] = self._optimizations_enabled.copy()
            
            return metrics
    
    def enable_optimization(self, optimization_name: str, enabled: bool = True):
        """
        Включение/отключение оптимизаций
        """
        if optimization_name in self._optimizations_enabled:
            self._optimizations_enabled[optimization_name] = enabled
            
            # Если включаем индексирование, перестраиваем индексы
            if optimization_name == 'indexing' and enabled:
                with self._sequences_lock:
                    self._searcher.build_index(self._sequences, self._buttons_config)
    
    def get_optimization_status(self) -> Dict[str, bool]:
        """
        Получение статуса оптимизаций
        """
        return self._optimizations_enabled.copy()
    
    def _update_metrics(self, metric_name: str, value: float):
        """
        Обновление метрик производительности
        """
        with self._metrics_lock:
            if hasattr(self._metrics, metric_name):
                current_value = getattr(self._metrics, metric_name)
                # Усредняем значения
                setattr(self._metrics, metric_name, (current_value + value) / 2)
            
            self._metrics.total_operations += 1
    
    def _update_cache_metrics(self):
        """
        Обновление метрик кеша
        """
        validator_stats = self._validator.get_cache_stats()
        expander_stats = self._expander.get_cache_stats()
        searcher_stats = self._searcher.get_cache_stats()
        
        # Вычисляем общий hit rate
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
            hit_rate = (total_hits / total_requests) * 100
        else:
            hit_rate = 0.0
        
        with self._metrics_lock:
            self._metrics.cache_hit_rate = hit_rate
    
    def get_sequence_info(self, sequence_name: str) -> Dict[str, Any]:
        """
        Получение подробной информации о последовательности
        """
        if not sequence_name:
            return {}
        
        commands = self.get_sequence(sequence_name)
        if not commands:
            return {}
        
        # Анализируем команды
        command_types = defaultdict(int)
        for command in commands:
            command_type = self._validator._get_command_type_fast(command)
            command_types[command_type] += 1
        
        # Валидируем последовательность
        is_valid, errors = self.validate_sequence(sequence_name)
        
        return {
            'name': sequence_name,
            'command_count': len(commands),
            'is_valid': is_valid,
            'errors': errors,
            'command_types': dict(command_types),
            'estimated_execution_time': self._estimate_execution_time(commands),
            'complexity_score': self._calculate_complexity_score(commands)
        }
    
    def _estimate_execution_time(self, commands: List[str]) -> float:
        """
        Оценка времени выполнения последовательности
        """
        total_time = 0.0
        
        for command in commands:
            if command.lower().startswith('wait'):
                try:
                    parts = command.split()
                    if len(parts) == 2:
                        wait_time = float(parts[1])
                        total_time += wait_time
                except (ValueError, IndexError):
                    pass
            else:
                # Оценка времени выполнения обычной команды
                total_time += 0.1  # 100ms по умолчанию
        
        return total_time
    
    def _calculate_complexity_score(self, commands: List[str]) -> int:
        """
        Вычисление оценки сложности последовательности
        """
        score = 0
        
        for command in commands:
            command_lower = command.lower()
            
            if command_lower.startswith('if '):
                score += 2  # Условные команды сложнее
            elif command_lower.startswith('wait'):
                score += 1  # Ожидание добавляет сложности
            elif command_lower.startswith('og_multizone-'):
                score += 3  # Мультизональные команды самые сложные
            else:
                score += 1  # Обычные команды
        
        return score

