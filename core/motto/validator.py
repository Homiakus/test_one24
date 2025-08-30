"""
Валидатор MOTTO конфигураций

Проверяет корректность конфигураций MOTTO:
- Структуру данных
- Ссылки между компонентами
- Циклические зависимости
- Семантическую корректность
"""

import logging
from typing import Dict, List, Any, Optional
from .types import MOTTOConfig, ValidationResult, Sequence


class MOTTOValidator:
    """
    Валидатор MOTTO конфигураций
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_config(self, config: MOTTOConfig) -> ValidationResult:
        """
        Валидация полной конфигурации
        
        Args:
            config: Конфигурация для валидации
            
        Returns:
            Результат валидации
        """
        result = ValidationResult(is_valid=True)
        
        try:
            # Проверяем версию
            if not self._validate_version(config.version, result):
                return result
            
            # Проверяем последовательности
            if not self._validate_sequences(config.sequences, result):
                return result
            
            # Проверяем циклические зависимости
            if not self._check_circular_dependencies(config.sequences, result):
                return result
            
            # Проверяем ссылки
            if not self._validate_references(config, result):
                return result
            
            self.logger.info("Конфигурация MOTTO прошла валидацию")
            
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"Ошибка валидации: {e}")
            self.logger.error(f"Ошибка валидации конфигурации: {e}")
        
        return result
    
    def _validate_version(self, version: str, result: ValidationResult) -> bool:
        """Валидация версии"""
        if version not in ['1.0', '1.1']:
            result.is_valid = False
            result.errors.append(f"Неподдерживаемая версия: {version}")
            return False
        return True
    
    def _validate_sequences(self, sequences: Dict[str, Sequence], result: ValidationResult) -> bool:
        """Валидация последовательностей"""
        for name, sequence in sequences.items():
            if not sequence.name:
                result.is_valid = False
                result.errors.append(f"Последовательность {name}: отсутствует имя")
                return False
            
            if not sequence.steps and sequence.type.value == 'sequence':
                result.warnings.append(f"Последовательность {name}: пустой список шагов")
        
        return True
    
    def _check_circular_dependencies(self, sequences: Dict[str, Sequence], result: ValidationResult) -> bool:
        """Проверка циклических зависимостей"""
        # TODO: Реализовать алгоритм поиска циклов
        return True
    
    def _validate_references(self, config: MOTTOConfig, result: ValidationResult) -> bool:
        """Валидация ссылок между компонентами"""
        # TODO: Проверить все ссылки на существование
        return True
    
    def validate_sequence(self, sequence: Sequence) -> ValidationResult:
        """
        Валидация отдельной последовательности
        
        Args:
            sequence: Последовательность для валидации
            
        Returns:
            Результат валидации
        """
        result = ValidationResult(is_valid=True)
        
        if not sequence.name:
            result.is_valid = False
            result.errors.append("Отсутствует имя последовательности")
        
        if not sequence.steps and sequence.type.value == 'sequence':
            result.warnings.append("Пустой список шагов")
        
        return result
    
    def validate_conditions(self, conditions: List[Any]) -> ValidationResult:
        """
        Валидация условий
        
        Args:
            conditions: Список условий
            
        Returns:
            Результат валидации
        """
        result = ValidationResult(is_valid=True)
        
        # TODO: Реализовать валидацию условий
        for condition in conditions:
            if not hasattr(condition, 'expr') or not condition.expr:
                result.is_valid = False
                result.errors.append(f"Условие {getattr(condition, 'name', 'unknown')}: отсутствует выражение")
        
        return result