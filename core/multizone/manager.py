"""
@file: multizone_manager.py
@description: Менеджер мультизональных операций
@dependencies: interfaces.py, di_container.py
@created: 2025-01-25
"""

import logging
from typing import List, Dict, Tuple, Optional
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
    """Менеджер мультизональных операций"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.zone_mask = 0b0000
        self.active_zones = []
        self.zone_count = 0
        self.zone_status = {}
        self._initialize_zones()
    
    def _initialize_zones(self):
        """Инициализация зон"""
        for zone_id in range(1, 5):
            self.zone_status[zone_id] = ZoneInfo(
                zone_id=zone_id,
                status=ZoneStatus.INACTIVE
            )
    
    def set_zones(self, zones: List[int]) -> bool:
        """Установка активных зон"""
        try:
            if not self.validate_zones(zones):
                return False
            
            self.active_zones = sorted(zones)
            self.zone_mask = self._zones_to_mask(zones)
            self.zone_count = len(zones)
            
            # Обновляем статус зон
            for zone_id in range(1, 5):
                if zone_id in zones:
                    self.zone_status[zone_id].status = ZoneStatus.ACTIVE
                else:
                    self.zone_status[zone_id].status = ZoneStatus.INACTIVE
            
            self.logger.info(f"Установлены зоны: {zones}, маска: {bin(self.zone_mask)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка установки зон: {e}")
            return False
    
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
            self.zone_status[zone].status = status
            self.zone_status[zone].progress = progress
            self.zone_status[zone].error_message = error_message
    
    def validate_zones(self, zones: List[int]) -> bool:
        """Валидация выбора зон"""
        try:
            # Проверяем диапазон зон
            for zone in zones:
                if not 1 <= zone <= 4:
                    self.logger.error(f"Некорректная зона: {zone}")
                    return False
            
            # Проверяем уникальность
            if len(zones) != len(set(zones)):
                self.logger.error("Дублирующиеся зоны")
                return False
            
            # Проверяем ограничения
            validation_result, message = self.validate_zone_selection(zones)
            if not validation_result:
                self.logger.error(f"Ошибка валидации: {message}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации зон: {e}")
            return False
    
    def validate_zone_selection(self, zones: List[int]) -> Tuple[bool, str]:
        """Валидация выбора зон с бизнес-логикой"""
        if not zones:
            return False, "Не выбрано ни одной зоны"
        
        # Проверяем диапазон зон
        for zone in zones:
            if not 1 <= zone <= 4:
                return False, f"Зона {zone} вне допустимого диапазона (1-4)"
        
        # Проверяем уникальность
        if len(zones) != len(set(zones)):
            return False, "Обнаружены дублирующиеся зоны"
        
        # Проверяем ограничения по комбинациям зон
        restrictions = self.get_zone_restrictions()
        
        for restriction_name, allowed_zones in restrictions.items():
            if set(zones) == set(allowed_zones):
                return True, f"Допустимая комбинация: {restriction_name}"
        
        return True, "Комбинация зон допустима"
    
    def get_zone_restrictions(self) -> Dict[str, List[int]]:
        """Получение ограничений по зонам"""
        return {
            "zones_1_2": [1, 2],
            "zones_3_4": [3, 4],
            "zones_1_2_3_4": [1, 2, 3, 4],
            "zones_1_2_3": [1, 2, 3],
            "zones_2_3_4": [2, 3, 4],
            "zones_2_3": [2, 3],
            "zones_1_3": [1, 3],
            "zones_2_4": [2, 4],
        }
    
    def _zones_to_mask(self, zones: List[int]) -> int:
        """Преобразование списка зон в битовую маску"""
        mask = 0
        for zone in zones:
            mask |= self._get_zone_bit(zone)
        return mask
    
    def _mask_to_zones(self, mask: int) -> List[int]:
        """Преобразование битовой маски в список зон"""
        zones = []
        for zone in range(1, 5):
            if mask & self._get_zone_bit(zone):
                zones.append(zone)
        return zones
    
    def _get_zone_bit(self, zone: int) -> int:
        """Получение бита для зоны"""
        return 1 << (zone - 1)
    
    def _count_active_bits(self, mask: int) -> int:
        """Подсчет активных битов в маске"""
        return bin(mask).count('1')
    
    def get_zone_mask_commands(self) -> List[str]:
        """Получение команд для установки зон"""
        commands = []
        for zone in self.active_zones:
            zone_mask = self._get_zone_bit(zone)
            commands.append(f"multizone {zone_mask:04b}")
        return commands
    
    def reset_zones(self):
        """Сброс всех зон"""
        self.zone_mask = 0b0000
        self.active_zones = []
        self.zone_count = 0
        self._initialize_zones()
        self.logger.info("Зоны сброшены")
