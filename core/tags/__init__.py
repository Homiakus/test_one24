"""
Пакет для управления тегами.

Этот пакет содержит компоненты для:
- Обработки и валидации тегов
- Управления типами тегов
- Обработки специальных тегов (wanted tags)
- Конфигурации тегов
"""

from .types import (
    TagType, TagInfo, TagResult, TagProcessingError, TagValidationError
)
from .processor import TagProcessor, BaseTagProcessor, WantedTagProcessor
from .validator import TagValidator
from .manager import TagManager

__all__ = [
    # Типы и структуры данных
    'TagType',
    'TagInfo',
    'TagResult',
    
    # Исключения
    'TagProcessingError',
    'TagValidationError',
    
    # Основные компоненты
    'TagProcessor',
    'BaseTagProcessor',
    'WantedTagProcessor',
    'TagValidator',
    'TagManager'
]
