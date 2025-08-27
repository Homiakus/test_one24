"""
@file: multizone_manager.py
@description: Упрощенный менеджер мультизональных операций
@dependencies: interfaces.py, di_container.py
@created: 2025-01-25
@updated: 2025-01-25 - Упрощение кода
"""

import logging
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

from core.interfaces import IMultizoneManager


class ZoneStatus(Enum):
    """Статус зоны"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ZoneInfo:
    """Информация о зоне"""
    zone_id: int
    status: ZoneStatus
    progress: float = 0.0
    error_message: Optional[str] = None


class MultizoneManager(IMultizoneManager):
    """Упрощенный менеджер мультизональных операций"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.zone_mask = 0b0000
        self.active_zones = []
        self.zone_status = {}
        self._init_zones()
    
    def _init_zones(self):
        """Инициализация зон"""
        for zone_id in range(1, 5):
            self.zone_status[zone_id] = ZoneInfo(zone_id, ZoneStatus.INACTIVE)
    
    def set_zones(self, zones: List[int]) -> bool:
        """Установка активных зон с валидацией"""
        if not self._validate_zones(zones):
            return False
        
        self.active_zones = sorted(zones)
        self.zone_mask = sum(1 << (zone - 1) for zone in zones)
        
        # Обновляем статус зон
        for zone_id in range(1, 5):
            self.zone_status[zone_id].status = (
                ZoneStatus.ACTIVE if zone_id in zones else ZoneStatus.INACTIVE
            )
        
        self.logger.info(f"Установлены зоны: {zones}, маска: {bin(self.zone_mask)}")
        return True
    
    def get_zone_mask(self) -> int:
        """Получение битовой маски зон"""
        return self.zone_mask
    
    def get_active_zones(self) -> List[int]:
        """Получение списка активных зон"""
        return self.active_zones.copy()
    
    def is_zone_active(self, zone: int) -> bool:
        """Проверка активности зоны"""
        return zone in self.active_zones
    
    def get_zone_status(self, zone: int) -> Optional[ZoneInfo]:
        """Получение статуса зоны"""
        return self.zone_status.get(zone)
    
    def set_zone_status(self, zone: int, status: ZoneStatus, 
                       progress: float = 0.0, error_message: Optional[str] = None):
        """Установка статуса зоны"""
        if zone in self.zone_status:
            zone_info = self.zone_status[zone]
            zone_info.status = status
            zone_info.progress = progress
            zone_info.error_message = error_message
    
    def validate_zones(self, zones: List[int]) -> bool:
        """Валидация выбора зон"""
        return self._validate_zones(zones)
    
    def _validate_zones(self, zones: List[int]) -> bool:
        """Внутренняя валидация зон"""
        if not zones:
            self.logger.error("Не выбрано ни одной зоны")
            return False
        
        # Проверяем диапазон и уникальность
        if not all(1 <= zone <= 4 for zone in zones) or len(zones) != len(set(zones)):
            self.logger.error("Некорректные зоны: диапазон 1-4, без дублирования")
            return False
        
        return True
    
    def get_zone_mask_commands(self) -> List[str]:
        """Получение команд для установки зон"""
        return [f"multizone {1 << (zone - 1):04b}" for zone in self.active_zones]
    
    def reset_zones(self):
        """Сброс всех зон"""
        self.zone_mask = 0b0000
        self.active_zones = []
        self._init_zones()
        self.logger.info("Зоны сброшены")
