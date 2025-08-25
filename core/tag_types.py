"""
Типы данных для системы тегов команд
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


class TagType(Enum):
    """Типы тегов команд"""
    WANTED = "wanted"  # Проверка переменной wanted
    # Будущие теги можно добавить здесь
    # OTHER = "other"
    # CONDITION = "condition"


@dataclass
class TagInfo:
    """Информация о теге"""
    tag_type: TagType
    tag_name: str
    parameters: Dict[str, Any]
    position: int  # Позиция тега в команде


@dataclass
class TagResult:
    """Результат обработки тега"""
    success: bool
    should_continue: bool  # Продолжать ли выполнение команды
    message: str
    data: Optional[Dict[str, Any]] = None


@dataclass
class ParsedCommand:
    """Распарсенная команда с тегами"""
    base_command: str
    tags: List[TagInfo]
    original_command: str
    
    def has_tag(self, tag_type: TagType) -> bool:
        """Проверка наличия тега определенного типа"""
        return any(tag.tag_type == tag_type for tag in self.tags)
    
    def get_tag(self, tag_type: TagType) -> Optional[TagInfo]:
        """Получение тега определенного типа"""
        for tag in self.tags:
            if tag.tag_type == tag_type:
                return tag
        return None
    
    def get_tags_by_type(self, tag_type: TagType) -> List[TagInfo]:
        """Получение всех тегов определенного типа"""
        return [tag for tag in self.tags if tag.tag_type == tag_type]


class TagProcessingError(Exception):
    """Ошибка обработки тега"""
    pass


class TagValidationError(Exception):
    """Ошибка валидации тега"""
    pass
