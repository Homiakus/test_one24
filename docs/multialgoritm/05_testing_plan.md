# План тестирования мультизонального алгоритма

## Обзор тестирования

### Цели тестирования
1. **Функциональное тестирование** - проверка корректности работы мультизонального алгоритма
2. **Интеграционное тестирование** - проверка взаимодействия с существующими компонентами
3. **Производительное тестирование** - проверка производительности при множественных зонах
4. **Тестирование безопасности** - проверка валидации и обработки ошибок

### Критерии покрытия
- **Код покрытие**: минимум 90%
- **Функциональное покрытие**: 100% сценариев использования
- **Интеграционное покрытие**: все точки интеграции

## Структура тестов

### 1. Модульные тесты
```
tests/unit/
├── test_multizone_manager.py      # Тесты MultizoneManager
├── test_multizone_validator.py    # Тесты валидации
├── test_multizone_types.py        # Тесты типов данных
└── test_multizone_utils.py        # Тесты утилит
```

### 2. Интеграционные тесты
```
tests/integration/
├── test_multizone_integration.py  # Интеграция с UI
├── test_multizone_commands.py     # Интеграция с командной системой
├── test_multizone_sequences.py    # Интеграция с последовательностями
└── test_multizone_config.py       # Интеграция с конфигурацией
```

### 3. Тесты производительности
```
tests/performance/
├── test_multizone_performance.py  # Тесты производительности
├── test_multizone_memory.py       # Тесты памяти
└── test_multizone_stress.py       # Стресс-тесты
```

## Детальные тесты

### 1. Тесты MultizoneManager

#### 1.1 Базовые операции
```python
def test_multizone_manager_initialization():
    """Тест инициализации менеджера"""
    manager = MultizoneManager()
    assert manager.zone_mask == 0b0000
    assert manager.active_zones == []
    assert manager.zone_count == 0

def test_set_zones_single():
    """Тест установки одной зоны"""
    manager = MultizoneManager()
    result = manager.set_zones([1])
    assert result is True
    assert manager.get_active_zones() == [1]
    assert manager.get_zone_mask() == 0b0001

def test_set_zones_multiple():
    """Тест установки нескольких зон"""
    manager = MultizoneManager()
    result = manager.set_zones([1, 3, 4])
    assert result is True
    assert manager.get_active_zones() == [1, 3, 4]
    assert manager.get_zone_mask() == 0b1101

def test_set_zones_all():
    """Тест установки всех зон"""
    manager = MultizoneManager()
    result = manager.set_zones([1, 2, 3, 4])
    assert result is True
    assert manager.get_active_zones() == [1, 2, 3, 4]
    assert manager.get_zone_mask() == 0b1111
```

#### 1.2 Валидация зон
```python
def test_validate_zones_invalid_range():
    """Тест валидации некорректного диапазона зон"""
    manager = MultizoneManager()
    result = manager.set_zones([0])  # Зона 0 не существует
    assert result is False
    
    result = manager.set_zones([5])  # Зона 5 не существует
    assert result is False

def test_validate_zones_duplicates():
    """Тест валидации дублирующихся зон"""
    manager = MultizoneManager()
    result = manager.set_zones([1, 1, 2])  # Дублирующаяся зона 1
    assert result is False

def test_validate_zones_empty():
    """Тест валидации пустого списка зон"""
    manager = MultizoneManager()
    result = manager.set_zones([])
    assert result is False
```

#### 1.3 Преобразования битовых масок
```python
def test_zones_to_mask():
    """Тест преобразования зон в битовую маску"""
    manager = MultizoneManager()
    
    # Тест отдельных зон
    assert manager._zones_to_mask([1]) == 0b0001
    assert manager._zones_to_mask([2]) == 0b0010
    assert manager._zones_to_mask([3]) == 0b0100
    assert manager._zones_to_mask([4]) == 0b1000
    
    # Тест комбинаций
    assert manager._zones_to_mask([1, 2]) == 0b0011
    assert manager._zones_to_mask([1, 3, 4]) == 0b1101
    assert manager._zones_to_mask([1, 2, 3, 4]) == 0b1111

def test_mask_to_zones():
    """Тест преобразования битовой маски в зоны"""
    manager = MultizoneManager()
    
    # Тест отдельных зон
    assert manager._mask_to_zones(0b0001) == [1]
    assert manager._mask_to_zones(0b0010) == [2]
    assert manager._mask_to_zones(0b0100) == [3]
    assert manager._mask_to_zones(0b1000) == [4]
    
    # Тест комбинаций
    assert manager._mask_to_zones(0b0011) == [1, 2]
    assert manager._mask_to_zones(0b1101) == [1, 3, 4]
    assert manager._mask_to_zones(0b1111) == [1, 2, 3, 4]

def test_count_active_bits():
    """Тест подсчета активных битов"""
    manager = MultizoneManager()
    
    assert manager._count_active_bits(0b0000) == 0
    assert manager._count_active_bits(0b0001) == 1
    assert manager._count_active_bits(0b0011) == 2
    assert manager._count_active_bits(0b1111) == 4
```

#### 1.4 Статус зон
```python
def test_zone_status_management():
    """Тест управления статусом зон"""
    manager = MultizoneManager()
    
    # Проверяем начальный статус
    zone1_status = manager.get_zone_status(1)
    assert zone1_status.status == ZoneStatus.INACTIVE
    
    # Устанавливаем зоны
    manager.set_zones([1, 2])
    
    # Проверяем статус активных зон
    zone1_status = manager.get_zone_status(1)
    assert zone1_status.status == ZoneStatus.ACTIVE
    
    zone2_status = manager.get_zone_status(2)
    assert zone2_status.status == ZoneStatus.ACTIVE
    
    # Проверяем статус неактивных зон
    zone3_status = manager.get_zone_status(3)
    assert zone3_status.status == ZoneStatus.INACTIVE

def test_set_zone_status():
    """Тест установки статуса зоны"""
    manager = MultizoneManager()
    manager.set_zones([1])
    
    # Устанавливаем статус выполнения
    manager.set_zone_status(1, ZoneStatus.EXECUTING, 0.5)
    zone1_status = manager.get_zone_status(1)
    assert zone1_status.status == ZoneStatus.EXECUTING
    assert zone1_status.progress == 0.5
    
    # Устанавливаем статус завершения
    manager.set_zone_status(1, ZoneStatus.COMPLETED, 1.0)
    zone1_status = manager.get_zone_status(1)
    assert zone1_status.status == ZoneStatus.COMPLETED
    assert zone1_status.progress == 1.0
```

### 2. Тесты валидатора

#### 2.1 Валидация мультизональных команд
```python
def test_validate_multizone_command_valid():
    """Тест валидации корректных мультизональных команд"""
    validator = MultizoneValidator()
    
    # Корректные команды
    result, command = validator.validate_multizone_command("og_multizone-test")
    assert result is True
    assert command.base_command == "test"
    
    result, command = validator.validate_multizone_command("og_multizone-paint")
    assert result is True
    assert command.base_command == "paint"
    
    result, command = validator.validate_multizone_command("og_multizone-rinse_cycle")
    assert result is True
    assert command.base_command == "rinse_cycle"

def test_validate_multizone_command_invalid():
    """Тест валидации некорректных мультизональных команд"""
    validator = MultizoneValidator()
    
    # Некорректные команды
    result, command = validator.validate_multizone_command("multizone-test")
    assert result is False
    assert command is None
    
    result, command = validator.validate_multizone_command("og_multizone")
    assert result is False
    assert command is None
    
    result, command = validator.validate_multizone_command("test")
    assert result is False
    assert command is None
```

#### 2.2 Валидация битовых масок
```python
def test_validate_zone_mask():
    """Тест валидации битовых масок"""
    validator = MultizoneValidator()
    
    # Корректные маски
    assert validator.validate_zone_mask(0b0000) is True
    assert validator.validate_zone_mask(0b0001) is True
    assert validator.validate_zone_mask(0b1111) is True
    
    # Некорректные маски
    assert validator.validate_zone_mask(-1) is False
    assert validator.validate_zone_mask(16) is False
    assert validator.validate_zone_mask(0b10000) is False
```

### 3. Интеграционные тесты

#### 3.1 Интеграция с UI
```python
def test_wizard_page_multizone_integration():
    """Тест интеграции WizardPage с мультизональным функционалом"""
    # Создаем WizardPage с MultizoneManager
    multizone_manager = MultizoneManager()
    wizard_page = WizardPage(wizard_config, multizone_manager)
    
    # Симулируем выбор зон
    wizard_page._on_zone_changed('left', True, False)  # Зона 1
    wizard_page._on_zone_changed('right', True, False)  # Зона 3
    
    # Проверяем состояние MultizoneManager
    assert multizone_manager.get_active_zones() == [1, 3]
    assert multizone_manager.get_zone_mask() == 0b0101

def test_overlay_panel_multizone_integration():
    """Тест интеграции OverlayPanel с мультизональным функционалом"""
    # Создаем OverlayPanel
    panel = OverlayPanel("left", "Зона 1", "Зона 2", "back")
    
    # Симулируем выбор зон
    panel.top_btn.setChecked(True)
    panel.bottom_btn.setChecked(True)
    
    # Проверяем состояние
    assert panel.top_btn.isChecked() is True
    assert panel.bottom_btn.isChecked() is True
```

#### 3.2 Интеграция с командной системой
```python
def test_sequence_manager_multizone_integration():
    """Тест интеграции SequenceManager с мультизональными командами"""
    sequence_manager = SequenceManager()
    multizone_manager = MultizoneManager()
    
    # Устанавливаем зоны
    multizone_manager.set_zones([1, 2])
    
    # Разворачиваем мультизональную команду
    commands = sequence_manager.expand_multizone_command(
        "og_multizone-test", 
        multizone_manager
    )
    
    # Проверяем результат
    expected_commands = [
        "multizone 0001",  # Зона 1
        "og_multizone-test",
        "multizone 0010",  # Зона 2
        "og_multizone-test"
    ]
    assert commands == expected_commands

def test_command_executor_multizone_integration():
    """Тест интеграции CommandExecutor с мультизональными командами"""
    # Создаем мок SerialManager
    mock_serial_manager = MockSerialManager()
    command_executor = CommandSequenceExecutor(mock_serial_manager)
    
    # Устанавливаем зоны
    multizone_manager = MultizoneManager()
    multizone_manager.set_zones([1, 3])
    
    # Выполняем мультизональную команду
    commands = [
        "multizone 0001",
        "og_multizone-test",
        "multizone 0100",
        "og_multizone-test"
    ]
    
    result = command_executor.execute_multizone_commands(commands, multizone_manager)
    assert result.success is True
    assert result.executed_zones == [1, 3]
```

### 4. Тесты производительности

#### 4.1 Тесты производительности
```python
def test_multizone_performance_single_zone():
    """Тест производительности для одной зоны"""
    manager = MultizoneManager()
    
    start_time = time.time()
    for _ in range(1000):
        manager.set_zones([1])
        manager.get_zone_mask()
        manager.get_active_zones()
    end_time = time.time()
    
    execution_time = end_time - start_time
    assert execution_time < 1.0  # Должно выполняться менее 1 секунды

def test_multizone_performance_all_zones():
    """Тест производительности для всех зон"""
    manager = MultizoneManager()
    
    start_time = time.time()
    for _ in range(1000):
        manager.set_zones([1, 2, 3, 4])
        manager.get_zone_mask()
        manager.get_active_zones()
    end_time = time.time()
    
    execution_time = end_time - start_time
    assert execution_time < 1.0  # Должно выполняться менее 1 секунды
```

#### 4.2 Тесты памяти
```python
def test_multizone_memory_usage():
    """Тест использования памяти"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Создаем множество менеджеров
    managers = []
    for _ in range(100):
        manager = MultizoneManager()
        manager.set_zones([1, 2, 3, 4])
        managers.append(manager)
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Увеличение памяти должно быть разумным (менее 10MB)
    assert memory_increase < 10 * 1024 * 1024
```

### 5. Стресс-тесты

#### 5.1 Стресс-тесты
```python
def test_multizone_stress_rapid_changes():
    """Стресс-тест быстрых изменений зон"""
    manager = MultizoneManager()
    
    # Быстрое переключение зон
    for i in range(1000):
        zones = [(i % 4) + 1, ((i + 1) % 4) + 1]
        manager.set_zones(zones)
        
        # Проверяем корректность
        assert len(manager.get_active_zones()) == 2
        assert manager.zone_count == 2

def test_multizone_stress_concurrent_access():
    """Стресс-тест конкурентного доступа"""
    import threading
    
    manager = MultizoneManager()
    results = []
    
    def worker(thread_id):
        for i in range(100):
            zones = [(thread_id + i) % 4 + 1]
            result = manager.set_zones(zones)
            results.append((thread_id, result))
    
    # Запускаем несколько потоков
    threads = []
    for i in range(4):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Ждем завершения
    for thread in threads:
        thread.join()
    
    # Проверяем результаты
    assert len(results) == 400
    assert all(result[1] for result in results)
```

## План выполнения тестов

### Неделя 1: Модульные тесты
- [ ] Тесты MultizoneManager
- [ ] Тесты валидатора
- [ ] Тесты типов данных
- [ ] Достижение 90% покрытия кода

### Неделя 2: Интеграционные тесты
- [ ] Тесты интеграции с UI
- [ ] Тесты интеграции с командной системой
- [ ] Тесты интеграции с конфигурацией
- [ ] Проверка всех сценариев использования

### Неделя 3: Тесты производительности
- [ ] Тесты производительности
- [ ] Тесты памяти
- [ ] Стресс-тесты
- [ ] Оптимизация при необходимости

### Неделя 4: Финальное тестирование
- [ ] Полное тестирование системы
- [ ] Исправление найденных проблем
- [ ] Документирование результатов
- [ ] Подготовка к развертыванию

## Критерии успеха тестирования

### Функциональные критерии
- [ ] Все мультизональные команды работают корректно
- [ ] Битовые маски преобразуются правильно
- [ ] Валидация зон работает корректно
- [ ] UI отображает статус зон правильно

### Качественные критерии
- [ ] 90% покрытие кода тестами
- [ ] Все тесты проходят успешно
- [ ] Производительность не хуже существующей
- [ ] Нет утечек памяти

### Критерии готовности
- [ ] Все критические баги исправлены
- [ ] Документация обновлена
- [ ] Тесты автоматизированы
- [ ] Готово к развертыванию
