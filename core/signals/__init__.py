"""
Пакет для управления сигналами.

Этот пакет содержит компоненты для:
- Обработки и валидации сигналов
- Управления типами сигналов
- Оптимизации обработки сигналов
- Конфигурации сигналов
"""

from .types import (
    SignalType, SignalInfo, SignalMapping, SignalValue, SignalResult,
    SignalProcessingError, SignalValidationError, SignalConfigError,
    SignalTypeConverter, SignalValidator, SignalParser
)
from .processor import SignalProcessor
from .validator import SignalValidator as SignalValidatorImpl
from .manager import SignalManager
from .optimizer import (
    OptimizedSignalParser, OptimizedSignalValidator,
    OptimizedSignalProcessor, OptimizedSignalManager
)

__all__ = [
    # Типы и структуры данных
    'SignalType',
    'SignalInfo', 
    'SignalMapping',
    'SignalValue',
    'SignalResult',
    
    # Исключения
    'SignalProcessingError',
    'SignalValidationError', 
    'SignalConfigError',
    
    # Утилиты
    'SignalTypeConverter',
    'SignalValidator',
    'SignalParser',
    
    # Основные компоненты
    'SignalProcessor',
    'SignalValidatorImpl',
    'SignalManager',
    
    # Оптимизированные компоненты
    'OptimizedSignalParser',
    'OptimizedSignalValidator',
    'OptimizedSignalProcessor',
    'OptimizedSignalManager'
]
