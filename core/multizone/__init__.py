"""
Пакет для управления мультизоной.

Этот пакет содержит компоненты для:
- Управления мультизонными командами
- Валидации мультизонных операций
- Обработки мультизонных результатов
- Конфигурации мультизоны
"""

from .types import (
    MultizoneCommandType, MultizoneCommand, MultizoneExecutionResult
)
from .manager import MultizoneManager
from .validator import MultizoneValidator

__all__ = [
    # Типы и структуры данных
    'MultizoneCommandType',
    'MultizoneCommand',
    'MultizoneExecutionResult',
    
    # Основные компоненты
    'MultizoneManager',
    'MultizoneValidator'
]

