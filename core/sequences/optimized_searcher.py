"""
@file: optimized_searcher.py
@description: Оптимизированный поисковик последовательностей с улучшенными алгоритмами
@dependencies: core.interfaces, core.sequences.types
@created: 2024-12-19
"""

import threading
from typing import Dict, List, Set, Optional, Tuple, Callable
from collections import defaultdict, deque
from dataclasses import dataclass
import re

from core.interfaces import ISequenceSearcher
from core.sequences.types import CommandType


@dataclass
class SearchIndex:
    """Индекс для быстрого поиска последовательностей"""
    command_index: Dict[str, Set[str]]  # команда -> множество последовательностей
    type_index: Dict[CommandType, Set[str]]  # тип -> множество последовательностей
    keyword_index: Dict[str, Set[str]]  # ключевое слово -> множество последовательностей
    pattern_index: Dict[str, Set[str]]  # паттерн -> множество последовательностей


class OptimizedSequenceSearcher(ISequenceSearcher):
    """
    Оптимизированный поисковик последовательностей
    
    Оптимизации:
    - Инвертированные индексы для быстрого поиска
    - Кеширование результатов поиска
    - Оптимизированные алгоритмы фильтрации
    - Поддержка полнотекстового поиска
    """
    
    def __init__(self, max_cache_size: int = 1000):
        self.max_cache_size = max_cache_size
        
        # Инвертированные индексы
        self._search_index = SearchIndex(
            command_index=defaultdict(set),
            type_index=defaultdict(set),
            keyword_index=defaultdict(set),
            pattern_index=defaultdict(set)
        )
        
        # Кеш результатов поиска
        self._search_cache: Dict[str, List[str]] = {}
        self._cache_lock = threading.RLock()
        
        # Статистика поиска
        self._search_stats = {
            "searches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "index_updates": 0
        }
        self._stats_lock = threading.Lock()
        
        # Компилированные регулярные выражения для поиска
        self._search_patterns = {
            'exact': re.compile(r'^(.+)$'),
            'contains': re.compile(r'(.+)'),
            'starts_with': re.compile(r'^(.+)'),
            'ends_with': re.compile(r'(.+)$'),
            'wildcard': re.compile(r'^(.+)$'),
            'regex': None  # Будет компилироваться динамически
        }
    
    def build_index(self, sequences: Dict[str, List[str]], buttons_config: Dict[str, str]):
        """
        Построение инвертированного индекса для быстрого поиска
        
        Временная сложность: O(n*m) где n - количество последовательностей, m - средняя длина
        """
        with self._cache_lock:
            # Очищаем старые индексы
            self._clear_indexes()
            
            # Индексируем последовательности
            for sequence_name, commands in sequences.items():
                self._index_sequence(sequence_name, commands)
            
            # Индексируем конфигурацию кнопок
            for button_name, command in buttons_config.items():
                self._index_button(button_name, command)
            
            # Очищаем кеш поиска
            self._search_cache.clear()
            
            self._increment_stat("index_updates")
    
    def search_sequences(self, query: str, search_type: str = "contains", 
                        max_results: int = 100) -> List[str]:
        """
        Оптимизированный поиск последовательностей
        
        Временная сложность: O(1) для точного поиска, O(log n) для индексированного
        """
        if not query or not query.strip():
            return []
        
        self._increment_stat("searches")
        
        # Проверяем кеш
        cache_key = f"{query}:{search_type}:{max_results}"
        cached_result = self._get_cached_search(cache_key)
        if cached_result:
            self._increment_stat("cache_hits")
            return cached_result
        
        self._increment_stat("cache_misses")
        
        # Выполняем поиск
        result = self._execute_search(query, search_type, max_results)
        
        # Кешируем результат
        self._cache_search_result(cache_key, result)
        
        return result
    
    def search_by_command_type(self, command_type: CommandType) -> List[str]:
        """
        Поиск последовательностей по типу команды
        
        Временная сложность: O(1)
        """
        with self._cache_lock:
            return list(self._search_index.type_index.get(command_type, set()))
    
    def search_by_keyword(self, keyword: str) -> List[str]:
        """
        Поиск последовательностей по ключевому слову
        
        Временная сложность: O(1)
        """
        with self._cache_lock:
            return list(self._search_index.keyword_index.get(keyword.lower(), set()))
    
    def search_by_pattern(self, pattern: str, use_regex: bool = False) -> List[str]:
        """
        Поиск последовательностей по паттерну
        
        Временная сложность: O(n) где n - количество последовательностей
        """
        if use_regex:
            try:
                regex = re.compile(pattern, re.IGNORECASE)
            except re.error:
                return []
        else:
            regex = self._search_patterns['contains']
        
        with self._cache_lock:
            results = set()
            for sequence_name in self._search_index.command_index.keys():
                if regex.search(sequence_name):
                    results.add(sequence_name)
            
            return list(results)
    
    def get_search_suggestions(self, partial_query: str, max_suggestions: int = 10) -> List[str]:
        """
        Получение предложений для автодополнения
        
        Временная сложность: O(log n) с оптимизациями
        """
        if not partial_query or len(partial_query) < 2:
            return []
        
        partial_lower = partial_query.lower()
        suggestions = []
        
        with self._cache_lock:
            # Ищем в индексе команд
            for command in self._search_index.command_index.keys():
                if command.lower().startswith(partial_lower):
                    suggestions.append(command)
                    if len(suggestions) >= max_suggestions:
                        break
            
            # Если не нашли достаточно, ищем в ключевых словах
            if len(suggestions) < max_suggestions:
                for keyword in self._search_index.keyword_index.keys():
                    if keyword.lower().startswith(partial_lower):
                        suggestions.append(keyword)
                        if len(suggestions) >= max_suggestions:
                            break
        
        return suggestions[:max_suggestions]
    
    def _index_sequence(self, sequence_name: str, commands: List[str]):
        """
        Индексирование одной последовательности
        """
        # Индексируем по командам
        for command in commands:
            self._search_index.command_index[command].add(sequence_name)
            
            # Индексируем по типу команды
            command_type = self._get_command_type(command)
            self._search_index.type_index[command_type].add(sequence_name)
            
            # Индексируем по ключевым словам
            keywords = self._extract_keywords(command)
            for keyword in keywords:
                self._search_index.keyword_index[keyword].add(sequence_name)
            
            # Индексируем по паттернам
            patterns = self._extract_patterns(command)
            for pattern in patterns:
                self._search_index.pattern_index[pattern].add(sequence_name)
    
    def _index_button(self, button_name: str, command: str):
        """
        Индексирование конфигурации кнопки
        """
        # Индексируем как команду
        self._search_index.command_index[command].add(f"button:{button_name}")
        
        # Индексируем по типу
        command_type = self._get_command_type(command)
        self._search_index.type_index[command_type].add(f"button:{button_name}")
        
        # Индексируем по ключевым словам
        keywords = self._extract_keywords(command)
        for keyword in keywords:
            self._search_index.keyword_index[keyword].add(f"button:{button_name}")
    
    def _get_command_type(self, command: str) -> CommandType:
        """
        Быстрое определение типа команды
        """
        command_lower = command.lower().strip()
        
        if command_lower.startswith('wait'):
            return CommandType.WAIT
        elif command_lower.startswith('if '):
            return CommandType.CONDITIONAL_IF
        elif command_lower == 'else':
            return CommandType.CONDITIONAL_ELSE
        elif command_lower == 'endif':
            return CommandType.CONDITIONAL_ENDIF
        elif command_lower.startswith('stop_if_not'):
            return CommandType.STOP_IF_NOT
        elif command_lower.startswith('og_multizone-'):
            return CommandType.MULTIZONE
        else:
            return CommandType.REGULAR
    
    def _extract_keywords(self, command: str) -> Set[str]:
        """
        Извлечение ключевых слов из команды
        """
        # Разбиваем на слова и фильтруем
        words = command.lower().split()
        keywords = set()
        
        for word in words:
            # Убираем специальные символы
            clean_word = re.sub(r'[^\w]', '', word)
            if len(clean_word) >= 2:  # Минимальная длина ключевого слова
                keywords.add(clean_word)
        
        return keywords
    
    def _extract_patterns(self, command: str) -> Set[str]:
        """
        Извлечение паттернов из команды
        """
        patterns = set()
        
        # Паттерн для wait команд
        if re.match(r'^wait\s+\d+(?:\.\d+)?$', command, re.IGNORECASE):
            patterns.add('wait_numeric')
        
        # Паттерн для if команд
        if re.match(r'^if\s+\w+$', command, re.IGNORECASE):
            patterns.add('if_flag')
        
        # Паттерн для мультизональных команд
        if command.startswith('og_multizone-'):
            patterns.add('multizone_command')
        
        return patterns
    
    def _execute_search(self, query: str, search_type: str, max_results: int) -> List[str]:
        """
        Выполнение поиска с оптимизациями
        """
        query_lower = query.lower().strip()
        
        if search_type == "exact":
            # Точный поиск - O(1)
            with self._cache_lock:
                return list(self._search_index.command_index.get(query, set()))[:max_results]
        
        elif search_type == "contains":
            # Поиск по содержимому - используем индекс
            results = set()
            with self._cache_lock:
                for command, sequences in self._search_index.command_index.items():
                    if query_lower in command.lower():
                        results.update(sequences)
                        if len(results) >= max_results:
                            break
            
            return list(results)[:max_results]
        
        elif search_type == "starts_with":
            # Поиск по началу - используем индекс
            results = set()
            with self._cache_lock:
                for command, sequences in self._search_index.command_index.items():
                    if command.lower().startswith(query_lower):
                        results.update(sequences)
                        if len(results) >= max_results:
                            break
            
            return list(results)[:max_results]
        
        elif search_type == "keyword":
            # Поиск по ключевым словам - O(1)
            with self._cache_lock:
                return list(self._search_index.keyword_index.get(query_lower, set()))[:max_results]
        
        else:
            # Полнотекстовый поиск
            return self._full_text_search(query_lower, max_results)
    
    def _full_text_search(self, query: str, max_results: int) -> List[str]:
        """
        Полнотекстовый поиск по всем индексам
        """
        results = set()
        
        with self._cache_lock:
            # Поиск по командам
            for command, sequences in self._search_index.command_index.items():
                if query in command.lower():
                    results.update(sequences)
                    if len(results) >= max_results:
                        break
            
            # Поиск по ключевым словам
            for keyword, sequences in self._search_index.keyword_index.items():
                if query in keyword:
                    results.update(sequences)
                    if len(results) >= max_results:
                        break
            
            # Поиск по паттернам
            for pattern, sequences in self._search_index.pattern_index.items():
                if query in pattern:
                    results.update(sequences)
                    if len(results) >= max_results:
                        break
        
        return list(results)[:max_results]
    
    def _get_cached_search(self, cache_key: str) -> Optional[List[str]]:
        """
        Получение результата поиска из кеша
        """
        with self._cache_lock:
            return self._search_cache.get(cache_key)
    
    def _cache_search_result(self, cache_key: str, result: List[str]):
        """
        Кеширование результата поиска
        """
        with self._cache_lock:
            # Если кеш переполнен, удаляем старые записи
            if len(self._search_cache) >= self.max_cache_size:
                # Удаляем 20% старых записей
                items_to_remove = self.max_cache_size // 5
                keys_to_remove = list(self._search_cache.keys())[:items_to_remove]
                for key in keys_to_remove:
                    del self._search_cache[key]
            
            self._search_cache[cache_key] = result
    
    def _clear_indexes(self):
        """
        Очистка всех индексов
        """
        self._search_index.command_index.clear()
        self._search_index.type_index.clear()
        self._search_index.keyword_index.clear()
        self._search_index.pattern_index.clear()
    
    def _increment_stat(self, stat_name: str):
        """
        Увеличение статистики
        """
        with self._stats_lock:
            if stat_name in self._search_stats:
                self._search_stats[stat_name] += 1
    
    def clear_cache(self):
        """Очистка кеша поиска"""
        with self._cache_lock:
            self._search_cache.clear()
    
    def get_search_stats(self) -> Dict[str, any]:
        """Получение статистики поиска"""
        with self._stats_lock:
            return self._search_stats.copy()
    
    def get_index_stats(self) -> Dict[str, int]:
        """Получение статистики индексов"""
        with self._cache_lock:
            return {
                "total_commands": len(self._search_index.command_index),
                "total_types": len(self._search_index.type_index),
                "total_keywords": len(self._search_index.keyword_index),
                "total_patterns": len(self._search_index.pattern_index),
                "cache_size": len(self._search_cache),
                "max_cache_size": self.max_cache_size
            }

