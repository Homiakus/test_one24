"""
Типы данных для управления последовательностями команд.

Этот модуль содержит все типы данных, используемые в пакете sequences:
- CommandType - типы команд
- ValidationResult - результат валидации
- ConditionalState - состояние условного выполнения
- SequenceKeywords - ключевые слова для анализа ответов
- CommandInfo - информация о команде
- SequenceInfo - информация о последовательности
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class CommandType(Enum):
    """Типы команд"""
    REGULAR = "regular"
    WAIT = "wait"
    SEQUENCE = "sequence"
    BUTTON = "button"
    CONDITIONAL_IF = "conditional_if"
    CONDITIONAL_ELSE = "conditional_else"
    CONDITIONAL_ENDIF = "conditional_endif"
    STOP_IF_NOT = "stop_if_not"
    MULTIZONE = "multizone"
    TAGGED = "tagged"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Результат валидации команды"""
    is_valid: bool
    error_message: str = ""
    command_type: CommandType = CommandType.UNKNOWN
    parsed_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionalState:
    """Состояние условного выполнения"""
    in_conditional_block: bool = False
    current_condition: bool = True
    skip_until_endif: bool = False
    condition_stack: List[bool] = field(default_factory=list)


@dataclass
class SequenceKeywords:
    """Ключевые слова для анализа ответов"""
    complete: List[str] = None
    received: List[str] = None
    error: List[str] = None
    complete_line: List[str] = None

    def __post_init__(self):
        if self.complete is None:
            self.complete = ['complete', 'completed', 'done', 'COMPLETE']
        if self.received is None:
            self.received = ['received']
        if self.error is None:
            self.error = ['err', 'error', 'fail']
        if self.complete_line is None:
            self.complete_line = ['complete']


@dataclass
class CommandInfo:
    """Информация о команде"""
    command: str
    command_type: CommandType
    is_valid: bool = True
    error_message: str = ""
    parsed_data: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    response: Optional[str] = None
    status: str = "pending"  # pending, executing, completed, failed


@dataclass
class SequenceInfo:
    """Информация о последовательности"""
    name: str
    commands: List[str]
    total_commands: int = 0
    executed_commands: int = 0
    failed_commands: int = 0
    total_time: float = 0.0
    status: str = "idle"  # idle, running, completed, failed, paused
    current_command_index: int = -1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.total_commands == 0:
            self.total_commands = len(self.commands)
