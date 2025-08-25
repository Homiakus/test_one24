# План внедрения мультизонального алгоритма

## Этап 1: Подготовка инфраструктуры

### 1.1 Создание модуля мультизонального управления
**Файл:** `core/multizone_manager.py`
- Класс `MultizoneManager` для управления зонами
- Методы для работы с битовыми масками
- Валидация выбора зон
- Интеграция с DI контейнером

### 1.2 Расширение интерфейсов
**Файл:** `core/interfaces.py`
- Добавить `IMultizoneManager` интерфейс
- Расширить `ISequenceManager` для мультизональных команд
- Добавить типы для мультизональных операций

### 1.3 Обновление DI конфигурации
**Файл:** `resources/di_config.toml`
- Зарегистрировать `MultizoneManager`
- Настроить зависимости для мультизонального функционала

## Этап 2: Реализация мультизонального менеджера

### 2.1 Основной класс MultizoneManager
```python
class MultizoneManager:
    def __init__(self):
        self.zone_mask = 0b0000
        self.active_zones = []
        self.zone_count = 0
        
    def set_zones(self, zones: List[int]) -> bool
    def get_zone_mask(self) -> int
    def get_active_zones(self) -> List[int]
    def is_zone_active(self, zone: int) -> bool
    def validate_zones(self, zones: List[int]) -> bool
```

### 2.2 Методы работы с битовыми масками
```python
def _zones_to_mask(self, zones: List[int]) -> int
def _mask_to_zones(self, mask: int) -> List[int]
def _get_zone_bit(self, zone: int) -> int
def _count_active_bits(self, mask: int) -> int
```

### 2.3 Валидация и безопасность
```python
def validate_zone_selection(self, zones: List[int]) -> Tuple[bool, str]
def check_zone_combinations(self, zones: List[int]) -> bool
def get_zone_restrictions(self) -> Dict[str, List[int]]
```

## Этап 3: Расширение системы команд

### 3.1 Новый тип команд
**Файл:** `core/sequence_manager.py`
- Добавить `MULTIZONE` в `CommandType`
- Расширить `CommandValidator` для мультизональных команд
- Добавить парсинг мультизональных команд

### 3.2 Обработка мультизональных команд
```python
def _parse_multizone_command(self, command: str) -> MultizoneCommand:
    # Парсинг команд вида "og_multizone-test"
    # Извлечение базовой команды и параметров

def _expand_multizone_command(self, command: str) -> List[str]:
    # Развертывание мультизональной команды в последовательность
    # Добавление команд multizone для каждой активной зоны
```

### 3.3 Интеграция с CommandSequenceExecutor
**Файл:** `core/command_executor.py`
- Добавить обработку мультизональных команд
- Реализовать логику повторного выполнения
- Добавить логирование по зонам

## Этап 4: Обновление UI компонентов

### 4.1 Расширение WizardPage
**Файл:** `ui/pages/wizard_page.py`
- Добавить глобальные переменные зон
- Интеграция с MultizoneManager
- Обновление обработчиков выбора зон

### 4.2 Обновление OverlayPanel
**Файл:** `ui/widgets/overlay_panel.py`
- Добавить поддержку 4 зон
- Обновить логику отображения состояний
- Добавить валидацию выбора зон

### 4.3 Добавление индикаторов статуса
**Файл:** `ui/widgets/multizone_status.py` (новый)
- Компонент для отображения статуса зон
- Прогресс-бар для мультизональных операций
- Индикаторы выполнения по зонам

## Этап 5: Конфигурация и команды

### 5.1 Добавление мультизональных команд
**Файл:** `config.toml`
```toml
[buttons]
"og_multizone-test" = "multizone_test"
"og_multizone-paint" = "multizone_paint"
"og_multizone-rinse" = "multizone_rinse"

[sequences]
multizone_test = ["og_multizone-test"]
multizone_paint = ["og_multizone-paint"]
multizone_rinse = ["og_multizone-rinse"]
```

### 5.2 Добавление флагов для зон
```toml
[flags]
zone_1_active = false
zone_2_active = false
zone_3_active = false
zone_4_active = false
multizone_mode = false
```

## Этап 6: Тестирование

### 6.1 Модульные тесты
**Файл:** `tests/unit/test_multizone_manager.py`
- Тесты для MultizoneManager
- Тесты валидации зон
- Тесты битовых масок

### 6.2 Интеграционные тесты
**Файл:** `tests/integration/test_multizone_integration.py`
- Тесты интеграции с UI
- Тесты выполнения команд
- Тесты конфигурации

### 6.3 Тесты производительности
**Файл:** `tests/performance/test_multizone_performance.py`
- Тесты производительности при множественных зонах
- Тесты памяти и ресурсов
- Стресс-тесты

## Этап 7: Документация и развертывание

### 7.1 Обновление документации
- Обновить `docs/algoritm.md`
- Добавить руководство по мультизональным командам
- Создать примеры использования

### 7.2 Миграция данных
- Скрипт миграции конфигурации
- Обновление существующих последовательностей
- Совместимость с существующими данными

## Детальный план реализации

### Неделя 1: Инфраструктура
- [ ] Создание MultizoneManager
- [ ] Расширение интерфейсов
- [ ] Обновление DI конфигурации
- [ ] Базовые тесты

### Неделя 2: Система команд
- [ ] Расширение CommandValidator
- [ ] Обработка мультизональных команд
- [ ] Интеграция с CommandSequenceExecutor
- [ ] Тесты команд

### Неделя 3: UI компоненты
- [ ] Обновление WizardPage
- [ ] Расширение OverlayPanel
- [ ] Создание индикаторов статуса
- [ ] UI тесты

### Неделя 4: Конфигурация и тестирование
- [ ] Добавление мультизональных команд
- [ ] Интеграционные тесты
- [ ] Производительность
- [ ] Документация

## Риски и митигация

### Технические риски
1. **Сложность интеграции** - Поэтапное внедрение с тестированием
2. **Производительность** - Оптимизация и кеширование
3. **Совместимость** - Обратная совместимость и миграция

### Риски качества
1. **Ошибки в логике зон** - Тщательное тестирование
2. **UI неудобство** - Пользовательское тестирование
3. **Документация** - Постоянное обновление

## Критерии успеха

### Функциональные
- [ ] Поддержка всех 4 зон
- [ ] Корректная работа битовых масок
- [ ] Выполнение мультизональных команд
- [ ] Валидация выбора зон

### Качественные
- [ ] 90% покрытие тестами
- [ ] Производительность не хуже существующей
- [ ] Обратная совместимость
- [ ] Полная документация
