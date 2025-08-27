"""
@file: test_multizone_manager.py
@description: Тесты для упрощенного MultizoneManager
@dependencies: core.multizone_manager
@created: 2025-01-25
@updated: 2025-01-25 - Обновление для упрощенной версии
"""

import pytest
from core.multizone_manager import MultizoneManager, ZoneStatus


class TestMultizoneManager:
    """Тесты для упрощенного MultizoneManager"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.manager = MultizoneManager()
    
    def test_multizone_manager_initialization(self):
        """Тест инициализации менеджера"""
        assert self.manager.zone_mask == 0b0000
        assert self.manager.active_zones == []
    
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
    
    def test_zone_status_management(self):
        """Тест управления статусом зон"""
        # Проверяем начальный статус
        zone1_status = self.manager.get_zone_status(1)
        assert zone1_status.status == ZoneStatus.INACTIVE
        
        # Устанавливаем зоны и проверяем статус
        self.manager.set_zones([1, 2])
        zone1_status = self.manager.get_zone_status(1)
        zone2_status = self.manager.get_zone_status(2)
        zone3_status = self.manager.get_zone_status(3)
        
        assert zone1_status.status == ZoneStatus.ACTIVE
        assert zone2_status.status == ZoneStatus.ACTIVE
        assert zone3_status.status == ZoneStatus.INACTIVE
    
    def test_set_zone_status(self):
        """Тест установки статуса зоны"""
        self.manager.set_zones([1])
        
        # Устанавливаем статус выполнения
        self.manager.set_zone_status(1, ZoneStatus.EXECUTING, 0.5, "Тест")
        zone1_status = self.manager.get_zone_status(1)
        
        assert zone1_status.status == ZoneStatus.EXECUTING
        assert zone1_status.progress == 0.5
        assert zone1_status.error_message == "Тест"
    
    def test_is_zone_active(self):
        """Тест проверки активности зоны"""
        self.manager.set_zones([1, 3])
        
        assert self.manager.is_zone_active(1) is True
        assert self.manager.is_zone_active(2) is False
        assert self.manager.is_zone_active(3) is True
        assert self.manager.is_zone_active(4) is False
    
    def test_get_zone_mask_commands(self):
        """Тест получения команд для установки зон"""
        self.manager.set_zones([1, 2, 4])
        commands = self.manager.get_zone_mask_commands()
        
        expected_commands = [
            "multizone 0001",  # Зона 1
            "multizone 0010",  # Зона 2
            "multizone 1000"   # Зона 4
        ]
        assert commands == expected_commands
    
    def test_reset_zones(self):
        """Тест сброса зон"""
        self.manager.set_zones([1, 2, 3])
        assert self.manager.get_active_zones() == [1, 2, 3]
        assert self.manager.get_zone_mask() == 0b0111
        
        self.manager.reset_zones()
        assert self.manager.get_active_zones() == []
        assert self.manager.get_zone_mask() == 0b0000
        
        # Проверяем, что все зоны неактивны
        for zone_id in range(1, 5):
            zone_status = self.manager.get_zone_status(zone_id)
            assert zone_status.status == ZoneStatus.INACTIVE
