"""
@file: multizone_types.py
@description: Типы данных для мультизонального функционала
@dependencies: None
@created: 2025-01-25
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum


class MultizoneCommandType(Enum):
    """Типы мультизональных команд"""
    ZONE_SELECTION = "zone_selection"
    ZONE_EXECUTION = "zone_execution"
    ZONE_STATUS = "zone_status"


@dataclass
class MultizoneCommand:
    """Мультизональная команда"""
    command_type: MultizoneCommandType
    base_command: str
    zone_mask: int
    zones: List[int]
    parameters: Optional[Dict] = None


@dataclass
class MultizoneExecutionResult:
    """Результат выполнения мультизональной команды"""
    success: bool
    executed_zones: List[int]
    failed_zones: List[int]
    error_messages: List[str]
    total_time: float
