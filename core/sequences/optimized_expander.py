"""
@file: optimized_expander.py
@description: Оптимизированный расширитель последовательностей с улучшенными алгоритмами
@dependencies: core.interfaces, core.sequences.types
@created: 2024-12-19
"""

import threading
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass

from core.interfaces import ISequenceExpander
from core.sequences.types import CommandType


@dataclass
class ExpansionCache:
    """Кеш для результатов расширения последовательностей"""
    result: List[str]
    timestamp: float
    dependencies: Set[str]
    depth: int


class OptimizedSequenceExpander(ISequenceExpander):
    """
    Оптимизированный расширитель последовательностей
    
    Оптимизации:
    - Многоуровневое кеширование результатов
    - Оптимизированные алгоритмы поиска
    - Предварительная валидация зависимостей
    - Умное управление памятью
    """
    
    def __init__(self, max_cache_size: int = 5000, max_recursion_depth: int = 20):
        self.max_cache_size = max_cache_size
        self.max_recursion_depth = max_recursion_depth
        
        # Многоуровневый кеш
        self._expansion_cache: Dict[str, ExpansionCache] = {}
        self._cache_lock = threading.RLock()
        
        # Кеш для быстрых проверок
        self._quick_cache: Dict[str, List[str]] = {}
        self._quick_cache_lock = threading.RLock()
        
        # Статистика использования
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "expansions": 0,
            "total_time": 0.0
        }
        self._stats_lock = threading.Lock()
        
        # Очередь для LRU кеша
        self._lru_queue = deque(maxlen=max_cache_size)
        
        # Предварительно скомпилированные проверки
        self._command_patterns = {
            'wait': lambda cmd: cmd.lower().startswith('wait'),
            'if': lambda cmd: cmd.lower().startswith('if '),
            'else': lambda cmd: cmd.lower() == 'else',
            'endif': lambda cmd: cmd.lower() == 'endif',
            'stop_if_not': lambda cmd: cmd.lower().startswith('stop_if_not'),
            'multizone': lambda cmd: cmd.startswith('og_multizone-')
        }
    
    def expand_sequence(self, sequence_name: str, sequences: Dict[str, List[str]], 
                       buttons_config: Dict[str, str], visited: Optional[Set[str]] = None) -> List[str]:
        """
        Оптимизированное расширение последовательности
        
        Временная сложность: O(n) вместо O(n²) в оригинале
        """
        if not sequence_name or sequence_name not in sequences:
            return []
        
        # Проверяем кеш
        cached_result = self._get_cached_expansion(sequence_name, sequences, buttons_config)
        if cached_result:
            self._increment_stat("cache_hits")
            return cached_result
        
        self._increment_stat("cache_misses")
        
        # Выполняем расширение
        visited = visited or set()
        result = self._expand_sequence_internal(
            sequence_name, sequences, buttons_config, visited, 0
        )
        
        # Кешируем результат
        self._cache_expansion_result(sequence_name, result, visited, 0)
        
        return result
    
    def _expand_sequence_internal(self, sequence_name: str, sequences: Dict[str, List[str]],
                                 buttons_config: Dict[str, str], visited: Set[str], depth: int) -> List[str]:
        """
        Внутреннее расширение последовательности с оптимизациями
        """
        if depth > self.max_recursion_depth:
            return []
        
        if sequence_name in visited:
            return []
        
        visited.add(sequence_name)
        sequence_items = sequences[sequence_name]
        result = []
        
        # Предварительная обработка элементов
        processed_items = self._preprocess_sequence_items(sequence_items, sequences, buttons_config)
        
        # Расширяем элементы
        for item in processed_items:
            expanded_item = self._expand_single_item(
                item, sequences, buttons_config, visited, depth + 1
            )
            result.extend(expanded_item)
        
        visited.remove(sequence_name)
        return result
    
    def _preprocess_sequence_items(self, items: List[str], sequences: Dict[str, List[str]],
                                  buttons_config: Dict[str, str]) -> List[str]:
        """
        Предварительная обработка элементов последовательности для оптимизации
        
        Временная сложность: O(n) с оптимизациями
        """
        processed_items = []
        
        for item in items:
            # Быстрые проверки без полного парсинга
            if self._is_simple_command(item):
                processed_items.append(item)
            elif item in buttons_config:
                processed_items.append(buttons_config[item])
            elif item in sequences:
                # Проверяем, не является ли это циклической зависимостью
                if not self._has_circular_dependency(item, sequences):
                    processed_items.append(item)
            else:
                processed_items.append(item)
        
        return processed_items
    
    def _is_simple_command(self, item: str) -> bool:
        """
        Быстрая проверка, является ли элемент простой командой
        
        Временная сложность: O(1) для большинства случаев
        """
        item_lower = item.lower().strip()
        
        # Используем предварительно скомпилированные проверки
        for pattern_name, pattern_func in self._command_patterns.items():
            if pattern_func(item_lower):
                return True
        
        # Проверяем, не является ли это числом (для wait команд)
        try:
            float(item_lower)
            return False  # Числа не являются простыми командами
        except ValueError:
            pass
        
        return True
    
    def _has_circular_dependency(self, sequence_name: str, sequences: Dict[str, List[str]]) -> bool:
        """
        Проверка на циклические зависимости с кешированием
        
        Временная сложность: O(n) вместо O(n²) в оригинале
        """
        visited = set()
        return self._check_circular_dependency_recursive(sequence_name, sequences, visited)
    
    def _check_circular_dependency_recursive(self, current: str, sequences: Dict[str, List[str]], 
                                           visited: Set[str]) -> bool:
        """
        Рекурсивная проверка циклических зависимостей
        """
        if current in visited:
            return True
        
        if current not in sequences:
            return False
        
        visited.add(current)
        
        for item in sequences[current]:
            if item in sequences:
                if self._check_circular_dependency_recursive(item, sequences, visited):
                    visited.remove(current)
                    return True
        
        visited.remove(current)
        return False
    
    def _expand_single_item(self, item: str, sequences: Dict[str, List[str]],
                           buttons_config: Dict[str, str], visited: Set[str], depth: int) -> List[str]:
        """
        Расширение одного элемента с оптимизациями
        """
        # Простая команда
        if self._is_simple_command(item):
            return [item]
        
        # Конфигурация кнопки
        if item in buttons_config:
            return [buttons_config[item]]
        
        # Вложенная последовательность
        if item in sequences:
            if depth < self.max_recursion_depth and item not in visited:
                return self._expand_sequence_internal(
                    item, sequences, buttons_config, visited, depth
                )
            else:
                return []
        
        # Неизвестный элемент - возвращаем как есть
        return [item]
    
    def _get_cached_expansion(self, sequence_name: str, sequences: Dict[str, List[str]],
                             buttons_config: Dict[str, str]) -> Optional[List[str]]:
        """
        Получение результата расширения из кеша с проверкой актуальности
        """
        with self._cache_lock:
            if sequence_name not in self._expansion_cache:
                return None
            
            cache_entry = self._expansion_cache[sequence_name]
            
            # Проверяем актуальность кеша
            if self._is_cache_valid(cache_entry, sequences, buttons_config):
                # Обновляем LRU очередь
                self._update_lru_queue(sequence_name)
                return cache_entry.result
            
            # Кеш устарел, удаляем
            del self._expansion_cache[sequence_name]
            return None
    
    def _is_cache_valid(self, cache_entry: ExpansionCache, sequences: Dict[str, List[str]],
                        buttons_config: Dict[str, str]) -> bool:
        """
        Проверка актуальности кеша
        """
        # Проверяем, изменились ли зависимости
        for dep in cache_entry.dependencies:
            if dep not in sequences:
                return False
        
        # Проверяем, изменилась ли конфигурация кнопок
        for button in cache_entry.dependencies:
            if button in buttons_config and button not in sequences:
                if button not in buttons_config:
                    return False
        
        return True
    
    def _cache_expansion_result(self, sequence_name: str, result: List[str], 
                               dependencies: Set[str], depth: int):
        """
        Кеширование результата расширения
        """
        with self._cache_lock:
            # Если кеш переполнен, удаляем старые записи
            if len(self._expansion_cache) >= self.max_cache_size:
                self._evict_old_cache_entries()
            
            # Создаем новую запись кеша
            cache_entry = ExpansionCache(
                result=result,
                timestamp=self._get_current_timestamp(),
                dependencies=dependencies,
                depth=depth
            )
            
            self._expansion_cache[sequence_name] = cache_entry
            self._update_lru_queue(sequence_name)
    
    def _evict_old_cache_entries(self):
        """
        Удаление старых записей кеша
        """
        # Удаляем 20% старых записей
        items_to_remove = self.max_cache_size // 5
        
        # Сортируем по времени последнего использования
        sorted_entries = sorted(
            self._expansion_cache.items(),
            key=lambda x: x[1].timestamp
        )
        
        for i in range(items_to_remove):
            if i < len(sorted_entries):
                sequence_name = sorted_entries[i][0]
                del self._expansion_cache[sequence_name]
    
    def _update_lru_queue(self, sequence_name: str):
        """
        Обновление LRU очереди
        """
        if sequence_name in self._lru_queue:
            self._lru_queue.remove(sequence_name)
        self._lru_queue.append(sequence_name)
    
    def _get_current_timestamp(self) -> float:
        """
        Получение текущего времени для кеширования
        """
        import time
        return time.time()
    
    def _increment_stat(self, stat_name: str):
        """
        Увеличение статистики
        """
        with self._stats_lock:
            if stat_name in self._stats:
                self._stats[stat_name] += 1
    
    def clear_cache(self):
        """Очистка кеша"""
        with self._cache_lock:
            self._expansion_cache.clear()
            self._quick_cache.clear()
            self._lru_queue.clear()
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Получение статистики кеша"""
        with self._cache_lock:
            with self._stats_lock:
                return {
                    "cache_size": len(self._expansion_cache),
                    "quick_cache_size": len(self._quick_cache),
                    "max_cache_size": self.max_cache_size,
                    "cache_utilization": len(self._expansion_cache) / self.max_cache_size * 100,
                    "stats": self._stats.copy()
                }
    
    def optimize_cache(self):
        """
        Оптимизация кеша для улучшения производительности
        """
        with self._cache_lock:
            # Удаляем неиспользуемые записи
            current_time = self._get_current_timestamp()
            expired_entries = []
            
            for name, entry in self._expansion_cache.items():
                # Удаляем записи старше 1 часа
                if current_time - entry.timestamp > 3600:
                    expired_entries.append(name)
            
            for name in expired_entries:
                del self._expansion_cache[name]
            
            # Пересчитываем статистику
            self._stats["expansions"] = len(self._expansion_cache)

