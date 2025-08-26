"""
Пакет для управления последовательностями команд.

Компоненты:
- types: Типы данных для последовательностей
- cancellation: Управление отменой операций
- flags: Управление флагами
- parser: Парсинг команд
- validator: Валидация команд
- executor: Выполнение последовательностей
- conditional: Обработка условных команд
- response: Анализ ответов
- worker: Рабочий поток для выполнения
- manager: Основной менеджер последовательностей
- optimized_validator: Оптимизированный валидатор
- optimized_expander: Оптимизированный расширитель
- optimized_searcher: Оптимизированный поисковик
- optimized_manager: Оптимизированный менеджер
"""

from .types import (
    CommandType, ValidationResult, CommandInfo, SequenceInfo,
    ConditionalState
)
from .cancellation import CancellationToken, CancellationException, CancellationManager
from .flags import FlagManager
from .parser import SequenceParser
from .validator import SequenceValidator
from .executor import SequenceExecutor
from .conditional import ConditionalProcessor
from .response import ResponseAnalyzer
from .worker import SequenceWorker
from .manager import SequenceManager

# Оптимизированные компоненты
from .optimized_validator import OptimizedCommandValidator
from .optimized_expander import OptimizedSequenceExpander
from .optimized_searcher import OptimizedSequenceSearcher
from .optimized_manager import OptimizedSequenceManager

__all__ = [
    # Основные компоненты
    'CommandType', 'ValidationResult', 'CommandInfo', 'SequenceInfo',
    'ConditionalState', 'CancellationToken', 'CancellationException',
    'CancellationManager', 'FlagManager', 'SequenceParser', 'SequenceValidator',
    'SequenceExecutor', 'ConditionalProcessor', 'ResponseAnalyzer',
    'SequenceWorker', 'SequenceManager',
    
    # Оптимизированные компоненты
    'OptimizedCommandValidator', 'OptimizedSequenceExpander',
    'OptimizedSequenceSearcher', 'OptimizedSequenceManager'
]
