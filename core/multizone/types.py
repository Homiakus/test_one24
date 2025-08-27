"""
@file: multizone_types.py
@description: Упрощенные типы данных для мультизонального функционала
@dependencies: None
@created: 2025-01-25
@updated: 2025-01-25 - Упрощение кода
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class MultizoneCommandType(Enum):
    """Типы мультизональных команд"""
    ZONE_EXECUTION = "zone_execution"


@dataclass
class MultizoneCommand:
    """Упрощенная мультизональная команда"""
    command_type: MultizoneCommandType
    base_command: str
    zone_mask: int
    zones: List[int]


@dataclass
class MultizoneExecutionResult:
    """Результат выполнения мультизональной команды"""
    success: bool
    executed_zones: List[int]
    failed_zones: List[int]
    error_messages: List[str]
