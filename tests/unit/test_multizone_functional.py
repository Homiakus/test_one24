"""
Функциональные тесты для упрощенного мультизонального менеджера
"""
import pytest
from unittest.mock import Mock, patch
from core.multizone_manager import MultizoneManager
from core.multizone_manager import ZoneStatus, ZoneInfo
from core.multizone_validator import MultizoneValidator


class TestMultizoneFunctional:
    """Тесты функциональности упрощенного мультизонального менеджера"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.manager = MultizoneManager()
        self.validator = MultizoneValidator()
    
    def test_single_zone_selection(self):
        """Тест выбора одной зоны"""
        # Выбираем зону 1
        self.manager.set_zones([1])
        
        # Проверяем активные зоны
        active_zones = self.manager.get_active_zones()
        assert active_zones == [1]
        
        # Проверяем битовую маску
        zone_mask = self.manager.get_zone_mask()
        assert zone_mask == 1  # 0001 в двоичной системе
        
        # Проверяем статус зоны
        zone_status = self.manager.get_zone_status(1)
        assert zone_status.status == ZoneStatus.ACTIVE
    
    def test_multiple_zone_selection(self):
        """Тест выбора нескольких зон"""
        # Выбираем зоны 1, 3, 4
        self.manager.set_zones([1, 3, 4])
        
        # Проверяем активные зоны
        active_zones = self.manager.get_active_zones()
        assert set(active_zones) == {1, 3, 4}
        
        # Проверяем битовую маску
        zone_mask = self.manager.get_zone_mask()
        assert zone_mask == 13  # 1101 в двоичной системе (1 + 4 + 8)
        
        # Проверяем статусы зон
        for zone_id in [1, 3, 4]:
            zone_status = self.manager.get_zone_status(zone_id)
            assert zone_status.status == ZoneStatus.ACTIVE
        
        # Проверяем неактивную зону
        zone_status = self.manager.get_zone_status(2)
        assert zone_status.status == ZoneStatus.INACTIVE
    
    def test_all_zones_selection(self):
        """Тест выбора всех зон"""
        # Выбираем все зоны
        self.manager.set_zones([1, 2, 3, 4])
        
        # Проверяем активные зоны
        active_zones = self.manager.get_active_zones()
        assert set(active_zones) == {1, 2, 3, 4}
        
        # Проверяем битовую маску
        zone_mask = self.manager.get_zone_mask()
        assert zone_mask == 15  # 1111 в двоичной системе
        
        # Проверяем статусы всех зон
        for zone_id in range(1, 5):
            zone_status = self.manager.get_zone_status(zone_id)
            assert zone_status.status == ZoneStatus.ACTIVE
    
    def test_reset_zones(self):
        """Тест сброса выбора зон"""
        # Выбираем зоны
        self.manager.set_zones([1, 2, 3])
        
        # Сбрасываем выбор
        self.manager.reset_zones()
        
        # Проверяем, что нет активных зон
        active_zones = self.manager.get_active_zones()
        assert active_zones == []
        
        # Проверяем битовую маску
        zone_mask = self.manager.get_zone_mask()
        assert zone_mask == 0
        
        # Проверяем статусы всех зон
        for zone_id in range(1, 5):
            zone_status = self.manager.get_zone_status(zone_id)
            assert zone_status.status == ZoneStatus.INACTIVE
    
    def test_zone_validation(self):
        """Тест валидации зон"""
        # Валидные зоны
        assert self.manager.validate_zones([1]) is True
        assert self.manager.validate_zones([1, 2]) is True
        assert self.manager.validate_zones([1, 2, 3, 4]) is True
        
        # Невалидные зоны
        assert self.manager.validate_zones([]) is False  # Пустой список
        assert self.manager.validate_zones([0]) is False  # Зона 0
        assert self.manager.validate_zones([5]) is False  # Зона 5
        assert self.manager.validate_zones([1, 1]) is False  # Дублирование
    
    def test_zone_status_management(self):
        """Тест управления статусом зон"""
        # Устанавливаем зоны
        self.manager.set_zones([1, 2])
        
        # Изменяем статус зоны
        self.manager.set_zone_status(1, ZoneStatus.EXECUTING, 0.5, "Выполняется")
        zone1_status = self.manager.get_zone_status(1)
        
        assert zone1_status.status == ZoneStatus.EXECUTING
        assert zone1_status.progress == 0.5
        assert zone1_status.error_message == "Выполняется"
        
        # Завершаем выполнение
        self.manager.set_zone_status(1, ZoneStatus.COMPLETED, 1.0)
        zone1_status = self.manager.get_zone_status(1)
        assert zone1_status.status == ZoneStatus.COMPLETED
        assert zone1_status.progress == 1.0
    
    def test_zone_commands_generation(self):
        """Тест генерации команд для зон"""
        # Устанавливаем зоны
        self.manager.set_zones([1, 3])
        
        # Получаем команды
        commands = self.manager.get_zone_mask_commands()
        expected_commands = ["multizone 0001", "multizone 0100"]
        
        assert commands == expected_commands
    
    def test_validator_multizone_command(self):
        """Тест валидатора мультизональных команд"""
        # Валидные команды
        valid, command = self.validator.validate_multizone_command("og_multizone-test")
        assert valid is True
        assert command.base_command == "test"
        
        # Невалидные команды
        valid, command = self.validator.validate_multizone_command("multizone-test")
        assert valid is False
        
        valid, command = self.validator.validate_multizone_command("og_multizone")
        assert valid is False
    
    def test_validator_zone_mask(self):
        """Тест валидации битовой маски"""
        # Валидные маски
        assert self.validator.validate_zone_mask(0) is True
        assert self.validator.validate_zone_mask(15) is True
        assert self.validator.validate_zone_mask(7) is True
        
        # Невалидные маски
        assert self.validator.validate_zone_mask(-1) is False
        assert self.validator.validate_zone_mask(16) is False
    
    def test_validator_zone_list(self):
        """Тест валидации списка зон"""
        # Валидные списки
        assert self.validator.validate_zone_list([1]) is True
        assert self.validator.validate_zone_list([1, 2, 3]) is True
        assert self.validator.validate_zone_list([1, 2, 3, 4]) is True
        
        # Невалидные списки
        assert self.validator.validate_zone_list([]) is False  # Пустой
        assert self.validator.validate_zone_list([0]) is False  # Зона 0
        assert self.validator.validate_zone_list([5]) is False  # Зона 5
        assert self.validator.validate_zone_list([1, 1]) is False  # Дублирование
