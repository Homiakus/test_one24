"""
@file: test_multizone_manager.py
@description: Тесты для MultizoneManager
@dependencies: core.multizone_manager
@created: 2025-01-25
"""

import pytest
from core.multizone_manager import MultizoneManager, ZoneStatus


class TestMultizoneManager:
    """Тесты для MultizoneManager"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.manager = MultizoneManager()
    
    def test_multizone_manager_initialization(self):
        """Тест инициализации менеджера"""
        assert self.manager.zone_mask == 0b0000
        assert self.manager.active_zones == []
        assert self.manager.zone_count == 0
    
    def test_set_zones_single(self):
        """Тест установки одной зоны"""
        result = self.manager.set_zones([1])
        assert result is True
        assert self.manager.get_active_zones() == [1]
        assert self.manager.get_zone_mask() == 0b0001
    
    def test_set_zones_multiple(self):
        """Тест установки нескольких зон"""
        result = self.manager.set_zones([1, 3, 4])
        assert result is True
        assert self.manager.get_active_zones() == [1, 3, 4]
        assert self.manager.get_zone_mask() == 0b1101
    
    def test_set_zones_all(self):
        """Тест установки всех зон"""
        result = self.manager.set_zones([1, 2, 3, 4])
        assert result is True
        assert self.manager.get_active_zones() == [1, 2, 3, 4]
        assert self.manager.get_zone_mask() == 0b1111
    
    def test_validate_zones_invalid_range(self):
        """Тест валидации некорректного диапазона зон"""
        result = self.manager.set_zones([0])  # Зона 0 не существует
        assert result is False
        
        result = self.manager.set_zones([5])  # Зона 5 не существует
        assert result is False
    
    def test_validate_zones_duplicates(self):
        """Тест валидации дублирующихся зон"""
        result = self.manager.set_zones([1, 1, 2])  # Дублирующаяся зона 1
        assert result is False
    
    def test_validate_zones_empty(self):
        """Тест валидации пустого списка зон"""
        result = self.manager.set_zones([])
        assert result is False
    
    def test_zones_to_mask(self):
        """Тест преобразования зон в битовую маску"""
        # Тест отдельных зон
        assert self.manager._zones_to_mask([1]) == 0b0001
        assert self.manager._zones_to_mask([2]) == 0b0010
        assert self.manager._zones_to_mask([3]) == 0b0100
        assert self.manager._zones_to_mask([4]) == 0b1000
        
        # Тест комбинаций
        assert self.manager._zones_to_mask([1, 2]) == 0b0011
        assert self.manager._zones_to_mask([1, 3, 4]) == 0b1101
        assert self.manager._zones_to_mask([1, 2, 3, 4]) == 0b1111
    
    def test_mask_to_zones(self):
        """Тест преобразования битовой маски в зоны"""
        # Тест отдельных зон
        assert self.manager._mask_to_zones(0b0001) == [1]
        assert self.manager._mask_to_zones(0b0010) == [2]
        assert self.manager._mask_to_zones(0b0100) == [3]
        assert self.manager._mask_to_zones(0b1000) == [4]
        
        # Тест комбинаций
        assert self.manager._mask_to_zones(0b0011) == [1, 2]
        assert self.manager._mask_to_zones(0b1101) == [1, 3, 4]
        assert self.manager._mask_to_zones(0b1111) == [1, 2, 3, 4]
    
    def test_count_active_bits(self):
        """Тест подсчета активных битов"""
        assert self.manager._count_active_bits(0b0000) == 0
        assert self.manager._count_active_bits(0b0001) == 1
        assert self.manager._count_active_bits(0b0011) == 2
        assert self.manager._count_active_bits(0b1111) == 4
    
    def test_zone_status_management(self):
        """Тест управления статусом зон"""
        # Проверяем начальный статус
        zone1_status = self.manager.get_zone_status(1)
        assert zone1_status.status == ZoneStatus.INACTIVE
        
        # Устанавливаем зоны
        self.manager.set_zones([1, 2])
        
        # Проверяем статус активных зон
        zone1_status = self.manager.get_zone_status(1)
        assert zone1_status.status == ZoneStatus.ACTIVE
        
        zone2_status = self.manager.get_zone_status(2)
        assert zone2_status.status == ZoneStatus.ACTIVE
        
        # Проверяем статус неактивных зон
        zone3_status = self.manager.get_zone_status(3)
        assert zone3_status.status == ZoneStatus.INACTIVE
    
    def test_set_zone_status(self):
        """Тест установки статуса зоны"""
        self.manager.set_zones([1])
        
        # Устанавливаем статус выполнения
        self.manager.set_zone_status(1, ZoneStatus.EXECUTING, 0.5)
        zone1_status = self.manager.get_zone_status(1)
        assert zone1_status.status == ZoneStatus.EXECUTING
        assert zone1_status.progress == 0.5
        
        # Устанавливаем статус завершения
        self.manager.set_zone_status(1, ZoneStatus.COMPLETED, 1.0)
        zone1_status = self.manager.get_zone_status(1)
        assert zone1_status.status == ZoneStatus.COMPLETED
        assert zone1_status.progress == 1.0
    
    def test_get_zone_mask_commands(self):
        """Тест получения команд для установки зон"""
        self.manager.set_zones([1, 3])
        commands = self.manager.get_zone_mask_commands()
        expected_commands = ["multizone 0001", "multizone 0100"]
        assert commands == expected_commands
    
    def test_reset_zones(self):
        """Тест сброса зон"""
        self.manager.set_zones([1, 2, 3])
        assert self.manager.get_active_zones() == [1, 2, 3]
        
        self.manager.reset_zones()
        assert self.manager.get_active_zones() == []
        assert self.manager.get_zone_mask() == 0b0000
        assert self.manager.zone_count == 0
