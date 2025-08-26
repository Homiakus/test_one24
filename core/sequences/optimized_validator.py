"""
@file: optimized_validator.py
@description: Оптимизированный валидатор команд с улучшенными алгоритмами
@dependencies: core.interfaces, core.sequences.types
@created: 2024-12-19
"""

import re
import threading
from typing import Dict, List, Tuple, Optional, Set
from functools import lru_cache
from collections import defaultdict

from core.interfaces import ICommandValidator
from core.sequences.types import ValidationResult, CommandType


class OptimizedCommandValidator(ICommandValidator):
    """
    Оптимизированный валидатор команд с улучшенными алгоритмами
    
    Оптимизации:
    - Кеширование результатов валидации
    - Компиляция регулярных выражений
    - Оптимизированные алгоритмы поиска
    - Уменьшение количества строковых операций
    """
    
    def __init__(self, max_wait_time: float = 3600.0):
        self.max_wait_time = max_wait_time
        
        # Кеш для результатов валидации
        self._validation_cache: Dict[str, ValidationResult] = {}
        self._cache_lock = threading.RLock()
        self._max_cache_size = 10000
        
        # Компилированные регулярные выражения для быстрого поиска
        self._wait_pattern = re.compile(r'^wait\s+(\d+(?:\.\d+)?)$', re.IGNORECASE)
        self._if_pattern = re.compile(r'^if\s+(\w+)$', re.IGNORECASE)
        self._stop_if_not_pattern = re.compile(r'^stop_if_not\s+(\w+)$', re.IGNORECASE)
        self._multizone_pattern = re.compile(r'^og_multizone-(.+)$')
        
        # Оптимизированные проверки команд
        self._command_checks = {
            'wait': self._validate_wait_command_optimized,
            'if': self._validate_if_command_optimized,
            'else': self._validate_else_command_optimized,
            'endif': self._validate_endif_command_optimized,
            'stop_if_not': self._validate_stop_if_not_command_optimized,
            'og_multizone': self._validate_multizone_command_optimized
        }
        
        # Быстрые проверки типов команд
        self._type_indicators = {
            'wait': CommandType.WAIT,
            'if': CommandType.CONDITIONAL_IF,
            'else': CommandType.CONDITIONAL_ELSE,
            'endif': CommandType.CONDITIONAL_ENDIF,
            'stop_if_not': CommandType.STOP_IF_NOT,
            'og_multizone': CommandType.MULTIZONE
        }
    
    def validate_command(self, command: str) -> ValidationResult:
        """
        Оптимизированная валидация команды с кешированием
        
        Временная сложность: O(1) для кешированных, O(n) для новых команд
        """
        if not command or not command.strip():
            return ValidationResult(False, "Пустая команда", CommandType.UNKNOWN)
        
        # Проверяем кеш
        cached_result = self._get_cached_validation(command)
        if cached_result:
            return cached_result
        
        # Определяем тип команды и валидируем
        command_type = self._get_command_type_fast(command)
        validation_result = self._validate_by_type(command, command_type)
        
        # Кешируем результат
        self._cache_validation_result(command, validation_result)
        
        return validation_result
    
    def validate_sequence(self, sequence: List[str]) -> Tuple[bool, List[str]]:
        """
        Оптимизированная валидация последовательности команд
        
        Временная сложность: O(n) вместо O(n²) в оригинале
        """
        if not sequence:
            return True, []
        
        errors = []
        validation_results = []
        
        # Валидируем все команды за один проход
        for i, command in enumerate(sequence):
            result = self.validate_command(command)
            validation_results.append((i, result))
            
            if not result.is_valid:
                errors.append(f"Команда {i+1}: {result.error_message}")
        
        return len(errors) == 0, errors
    
    def _get_command_type_fast(self, command: str) -> CommandType:
        """
        Быстрое определение типа команды без полного парсинга
        
        Временная сложность: O(1) для большинства случаев
        """
        command_lower = command.lower().strip()
        
        # Быстрые проверки для известных типов
        for indicator, command_type in self._type_indicators.items():
            if command_lower.startswith(indicator):
                return command_type
        
        return CommandType.REGULAR
    
    def _validate_by_type(self, command: str, command_type: CommandType) -> ValidationResult:
        """
        Валидация команды по типу с использованием оптимизированных алгоритмов
        """
        command_lower = command.lower().strip()
        
        # Используем оптимизированные валидаторы
        for prefix, validator_func in self._command_checks.items():
            if command_lower.startswith(prefix):
                return validator_func(command)
        
        # Обычная команда
        return ValidationResult(True, "", CommandType.REGULAR, {"command": command})
    
    def _validate_wait_command_optimized(self, command: str) -> ValidationResult:
        """
        Оптимизированная валидация wait команды с регулярным выражением
        
        Временная сложность: O(1) вместо O(n) в оригинале
        """
        match = self._wait_pattern.match(command)
        if not match:
            return ValidationResult(
                False,
                "Неверный синтаксис wait команды. Используйте: wait <время>",
                CommandType.WAIT
            )
        
        try:
            wait_time = float(match.group(1))
            
            if wait_time < 0:
                return ValidationResult(
                    False,
                    "Время ожидания не может быть отрицательным",
                    CommandType.WAIT
                )
            
            if wait_time > self.max_wait_time:
                return ValidationResult(
                    False,
                    f"Время ожидания превышает максимальное ({self.max_wait_time} сек)",
                    CommandType.WAIT
                )
            
            return ValidationResult(
                True,
                "",
                CommandType.WAIT,
                {"wait_time": wait_time}
            )
            
        except ValueError:
            return ValidationResult(
                False,
                "Неверный формат времени в wait команде",
                CommandType.WAIT
            )
    
    def _validate_if_command_optimized(self, command: str) -> ValidationResult:
        """
        Оптимизированная валидация if команды
        """
        match = self._if_pattern.match(command)
        if not match:
            return ValidationResult(
                False,
                "Команда if должна содержать имя флага",
                CommandType.CONDITIONAL_IF
            )
        
        flag_name = match.group(1)
        if not flag_name:
            return ValidationResult(
                False,
                "Имя флага не может быть пустым",
                CommandType.CONDITIONAL_IF
            )
        
        return ValidationResult(
            True,
            "",
            CommandType.CONDITIONAL_IF,
            {"flag_name": flag_name, "command": command}
        )
    
    def _validate_else_command_optimized(self, command: str) -> ValidationResult:
        """
        Оптимизированная валидация else команды
        """
        if command.lower().strip() != "else":
            return ValidationResult(
                False,
                "Команда else должна быть в точности 'else'",
                CommandType.CONDITIONAL_ELSE
            )
        
        return ValidationResult(
            True,
            "",
            CommandType.CONDITIONAL_ELSE,
            {"command": command}
        )
    
    def _validate_endif_command_optimized(self, command: str) -> ValidationResult:
        """
        Оптимизированная валидация endif команды
        """
        if command.lower().strip() != "endif":
            return ValidationResult(
                False,
                "Команда endif должна быть в точности 'endif'",
                CommandType.CONDITIONAL_ENDIF
            )
        
        return ValidationResult(
            True,
            "",
            CommandType.CONDITIONAL_ENDIF,
            {"command": command}
        )
    
    def _validate_stop_if_not_command_optimized(self, command: str) -> ValidationResult:
        """
        Оптимизированная валидация stop_if_not команды
        """
        match = self._stop_if_not_pattern.match(command)
        if not match:
            return ValidationResult(
                False,
                "Команда stop_if_not должна содержать имя флага",
                CommandType.STOP_IF_NOT
            )
        
        flag_name = match.group(1)
        if not flag_name:
            return ValidationResult(
                False,
                "Имя флага не может быть пустым",
                CommandType.STOP_IF_NOT
            )
        
        return ValidationResult(
            True,
            "",
            CommandType.STOP_IF_NOT,
            {"flag_name": flag_name, "command": command}
        )
    
    def _validate_multizone_command_optimized(self, command: str) -> ValidationResult:
        """
        Оптимизированная валидация мультизональной команды
        """
        match = self._multizone_pattern.match(command)
        if not match:
            return ValidationResult(
                False,
                "Мультизональная команда должна начинаться с 'og_multizone-'",
                CommandType.MULTIZONE
            )
        
        base_command = match.group(1)
        if not base_command:
            return ValidationResult(
                False,
                "Мультизональная команда должна содержать базовую команду",
                CommandType.MULTIZONE
            )
        
        return ValidationResult(
            True,
            "",
            CommandType.MULTIZONE,
            {
                "command": command,
                "base_command": base_command,
                "is_multizone": True
            }
        )
    
    def _get_cached_validation(self, command: str) -> Optional[ValidationResult]:
        """
        Получение результата валидации из кеша
        
        Временная сложность: O(1)
        """
        with self._cache_lock:
            return self._validation_cache.get(command)
    
    def _cache_validation_result(self, command: str, result: ValidationResult) -> None:
        """
        Кеширование результата валидации с ограничением размера кеша
        """
        with self._cache_lock:
            # Если кеш переполнен, удаляем старые записи
            if len(self._validation_cache) >= self._max_cache_size:
                # Удаляем 20% старых записей
                items_to_remove = self._max_cache_size // 5
                keys_to_remove = list(self._validation_cache.keys())[:items_to_remove]
                for key in keys_to_remove:
                    del self._validation_cache[key]
            
            self._validation_cache[command] = result
    
    def clear_cache(self) -> None:
        """Очистка кеша валидации"""
        with self._cache_lock:
            self._validation_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Получение статистики кеша"""
        with self._cache_lock:
            return {
                "cache_size": len(self._validation_cache),
                "max_cache_size": self._max_cache_size,
                "cache_utilization": len(self._validation_cache) / self._max_cache_size * 100
            }
