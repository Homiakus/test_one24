"""
Функциональные тесты для мультизонального менеджера
"""
import pytest
from unittest.mock import Mock, patch
from core.multizone_manager import MultizoneManager
from core.multizone_manager import ZoneStatus, ZoneInfo
from core.multizone_validator import MultizoneValidator


class TestMultizoneFunctional:
    """Тесты функциональности мультизонального менеджера"""
    
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
    
    def test_zone_mask_conversion(self):
        """Тест конвертации зон в битовую маску"""
        test_cases = [
            ([1], 1),      # 0001
            ([2], 2),      # 0010
            ([3], 4),      # 0100
            ([4], 8),      # 1000
            ([1, 2], 3),   # 0011
            ([1, 3], 5),   # 0101
            ([2, 4], 10),  # 1010
            ([1, 2, 3, 4], 15),  # 1111
        ]
        
        for zones, expected_mask in test_cases:
            self.manager.set_zones(zones)
            zone_mask = self.manager.get_zone_mask()
            assert zone_mask == expected_mask, f"Ожидалась маска {expected_mask} для зон {zones}, получена {zone_mask}"
    
    def test_zone_validation(self):
        """Тест валидации зон"""
        # Валидные зоны
        result, message = self.manager.validate_zone_selection([1])
        assert result == True
        result, message = self.manager.validate_zone_selection([1, 2, 3, 4])
        assert result == True
        result, message = self.manager.validate_zone_selection([2, 4])
        assert result == True
        
        # Невалидные зоны
        result, message = self.manager.validate_zone_selection([0])
        assert result == False  # Зона 0 не существует
        result, message = self.manager.validate_zone_selection([5])
        assert result == False  # Зона 5 не существует
        result, message = self.manager.validate_zone_selection([1, 1])
        assert result == False  # Дублирование
        result, message = self.manager.validate_zone_selection([1, 2, 1])
        assert result == False  # Дублирование
        result, message = self.manager.validate_zone_selection([])
        assert result == False  # Пустой список
    
    def test_zone_status_management(self):
        """Тест управления статусами зон"""
        # Устанавливаем зоны
        self.manager.set_zones([1, 2])
        
        # Проверяем начальный статус
        assert self.manager.get_zone_status(1).status == ZoneStatus.ACTIVE
        
        # Устанавливаем статус "выполняется"
        self.manager.set_zone_status(1, ZoneStatus.EXECUTING)
        assert self.manager.get_zone_status(1).status == ZoneStatus.EXECUTING
        
        # Устанавливаем статус "завершено"
        self.manager.set_zone_status(1, ZoneStatus.COMPLETED)
        assert self.manager.get_zone_status(1).status == ZoneStatus.COMPLETED
        
        # Устанавливаем статус "ошибка"
        self.manager.set_zone_status(1, ZoneStatus.ERROR)
        assert self.manager.get_zone_status(1).status == ZoneStatus.ERROR
        
        # Возвращаем к активному статусу
        self.manager.set_zone_status(1, ZoneStatus.ACTIVE)
        assert self.manager.get_zone_status(1).status == ZoneStatus.ACTIVE
    
    def test_zone_status_retrieval(self):
        """Тест получения статуса зон"""
        # Устанавливаем зоны
        self.manager.set_zones([1, 3])
        
        # Получаем статус зоны 1
        zone_info = self.manager.get_zone_status(1)
        assert isinstance(zone_info, ZoneInfo)
        assert zone_info.zone_id == 1
        assert zone_info.status == ZoneStatus.ACTIVE
        
        # Получаем статус неактивной зоны
        zone_info = self.manager.get_zone_status(2)
        assert zone_info.zone_id == 2
        assert zone_info.status == ZoneStatus.INACTIVE
    
    def test_multizone_mode_detection(self):
        """Тест определения мультизонального режима"""
        # Одна зона - не мультизональный режим
        self.manager.set_zones([1])
        assert len(self.manager.get_active_zones()) == 1
        
        # Несколько зон - мультизональный режим
        self.manager.set_zones([1, 2])
        assert len(self.manager.get_active_zones()) == 2
        
        # Все зоны - мультизональный режим
        self.manager.set_zones([1, 2, 3, 4])
        assert len(self.manager.get_active_zones()) == 4
        
        # Нет зон - не мультизональный режим
        self.manager.reset_zones()
        assert len(self.manager.get_active_zones()) == 0
    
    def test_zone_count_operations(self):
        """Тест операций с количеством зон"""
        # Проверяем количество активных зон
        self.manager.set_zones([1, 2, 3])
        assert len(self.manager.get_active_zones()) == 3
        
        self.manager.set_zones([1])
        assert len(self.manager.get_active_zones()) == 1
        
        self.manager.reset_zones()
        assert len(self.manager.get_active_zones()) == 0
    
    def test_edge_cases(self):
        """Тест граничных случаев"""
        # Попытка установить несуществующую зону
        result = self.manager.set_zones([5])
        assert result == False
        
        # Попытка установить зону 0
        result = self.manager.set_zones([0])
        assert result == False
        
        # Попытка получить статус несуществующей зоны
        zone_status = self.manager.get_zone_status(5)
        assert zone_status is None
    
    def test_concurrent_access(self):
        """Тест конкурентного доступа"""
        import threading
        import time
        
        results = []
        
        def worker(zone_id):
            """Рабочая функция для тестирования конкурентности"""
            try:
                self.manager.set_zone_status(zone_id, ZoneStatus.EXECUTING)
                time.sleep(0.01)  # Имитация работы
                self.manager.set_zone_status(zone_id, ZoneStatus.COMPLETED)
                results.append(f"zone_{zone_id}_completed")
            except Exception as e:
                results.append(f"zone_{zone_id}_error: {e}")
        
        # Устанавливаем зоны
        self.manager.set_zones([1, 2, 3, 4])
        
        # Запускаем потоки
        threads = []
        for zone_id in [1, 2, 3, 4]:
            thread = threading.Thread(target=worker, args=(zone_id,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем результаты
        assert len(results) == 4
        assert all("completed" in result for result in results)
        
        # Проверяем статусы зон
        for zone_id in [1, 2, 3, 4]:
            zone_status = self.manager.get_zone_status(zone_id)
            assert zone_status.status == ZoneStatus.COMPLETED


class TestMultizoneValidator:
    """Тесты валидатора мультизональных операций"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.validator = MultizoneValidator()
    
    def test_validate_multizone_command(self):
        """Тест валидации мультизональных команд"""
        # Валидные команды
        result, command = self.validator.validate_multizone_command("og_multizone-test")
        assert result == True
        assert command is not None
        
        result, command = self.validator.validate_multizone_command("og_multizone-paint")
        assert result == True
        assert command is not None
        
        result, command = self.validator.validate_multizone_command("og_multizone-rinse")
        assert result == True
        assert command is not None
        
        # Невалидные команды
        result, command = self.validator.validate_multizone_command("test")
        assert result == False
        assert command is None
        
        result, command = self.validator.validate_multizone_command("multizone-test")
        assert result == False
        assert command is None
        
        result, command = self.validator.validate_multizone_command("")
        assert result == False
        assert command is None
    
    def test_validate_zone_mask(self):
        """Тест валидации битовой маски зон"""
        # Валидные маски
        assert self.validator.validate_zone_mask(0) == True   # Нет зон
        assert self.validator.validate_zone_mask(1) == True   # Зона 1
        assert self.validator.validate_zone_mask(15) == True  # Все зоны
        
        # Невалидные маски
        assert self.validator.validate_zone_mask(16) == False  # Выход за пределы
        assert self.validator.validate_zone_mask(-1) == False  # Отрицательная маска
