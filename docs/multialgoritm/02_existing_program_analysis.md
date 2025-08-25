# Анализ существующей программы

## Архитектура системы

### Основные компоненты

#### 1. Core модули
- **`core/sequence_manager.py`** - Менеджер последовательностей команд
- **`core/command_executor.py`** - Исполнитель команд
- **`core/serial_manager.py`** - Управление Serial соединением
- **`core/di_container.py`** - DI контейнер для зависимостей

#### 2. UI модули
- **`ui/main_window.py`** - Главное окно приложения
- **`ui/pages/wizard_page.py`** - Страница мастера с выбором зон
- **`ui/widgets/overlay_panel.py`** - Панели выбора зон
- **`ui/components/`** - Дополнительные UI компоненты

#### 3. Конфигурация
- **`config.toml`** - Основной конфигурационный файл
- **`resources/di_config.toml`** - Конфигурация DI контейнера

## Текущая система выбора зон

### UI компоненты
```python
# ui/pages/wizard_page.py
class WizardPage(BasePage):
    zone_selected = {
        'left_top': False,      # Зона 1
        'left_bottom': False,   # Зона 2
        'right_top': False,     # Зона 3
        'right_bottom': False,  # Зона 4
    }
```

### Обработка выбора зон
```python
def _on_zone_changed(self, panel_id: str, top: bool, bottom: bool):
    if panel_id == 'left':
        self.zone_selected['left_top'] = top
        self.zone_selected['left_bottom'] = bottom
    elif panel_id == 'right':
        self.zone_selected['right_top'] = top
        self.zone_selected['right_bottom'] = bottom
    
    self.zone_selection_changed.emit(self.zone_selected)
```

## Система команд

### Типы команд
```python
class CommandType(Enum):
    REGULAR = "regular"
    WAIT = "wait"
    SEQUENCE = "sequence"
    BUTTON = "button"
    CONDITIONAL_IF = "conditional_if"
    CONDITIONAL_ELSE = "conditional_else"
    CONDITIONAL_ENDIF = "conditional_endif"
    STOP_IF = "stop_if"
```

### Обработка команд
- Команды валидируются через `CommandValidator`
- Выполняются через `CommandSequenceExecutor`
- Поддерживается условное выполнение и флаги

## Конфигурация команд

### Существующие команды в config.toml
```toml
[buttons]
"Multi → OG" = "sm -8 * * * *"
"Multi → продувка OG" = "sm -43 * * * *"
"Multi → EA" = "sm 95 * * * *"
# ... другие команды

[sequences]
coloring = ["Clamp → сжать ", "sedimantation", "alco", "gemo", "water", "water", "og", "alco", "ea", "alco", "alco", "alco", "waste_out"]
og = ["RRight → верх", "Multi → OG", "Насос включить", "KL2 включить", "wait 2", "Multi → продувка OG", "wait 3", "KL2 выключить", "Насос выключить", "RRight → экспозиция", "waste_out", "waste"]
```

## Система флагов

### Глобальные флаги
```toml
[flags]
auto_mode = true
safety_check = true
emergency_stop = false
maintenance_mode = false
test_mode = false
```

### Управление флагами
- Флаги управляются через `FlagManager`
- Поддерживается условное выполнение на основе флагов
- Флаги могут изменяться во время выполнения

## DI контейнер

### Зарегистрированные сервисы
```toml
[di_container.services]
serial_manager = { interface = "ISerialManager", implementation = "SerialManager" }
command_executor = { interface = "ICommandExecutor", implementation = "BasicCommandExecutor" }
sequence_manager = { interface = "ISequenceManager", implementation = "SequenceManager" }
config_loader = { interface = "IConfigLoader", implementation = "ConfigLoader" }
```

## Точки интеграции для мультизонального алгоритма

### 1. UI уровень
- **`ui/pages/wizard_page.py`** - Добавить обработку битовой маски
- **`ui/widgets/overlay_panel.py`** - Расширить для поддержки 4 зон
- **`ui/main_window.py`** - Добавить глобальные переменные зон

### 2. Core уровень
- **`core/sequence_manager.py`** - Добавить обработку мультизональных команд
- **`core/command_executor.py`** - Расширить для поддержки мультизонального выполнения
- **`core/interfaces.py`** - Добавить интерфейсы для мультизонального функционала

### 3. Конфигурация
- **`config.toml`** - Добавить мультизональные команды и последовательности
- **`resources/di_config.toml`** - Зарегистрировать новые сервисы

## Существующие ограничения

### 1. Архитектурные
- Текущая система зон ограничена 2 панелями (левая/правая)
- Нет поддержки битовых масок
- Отсутствует механизм повторного выполнения команд

### 2. Функциональные
- Нет валидации мультизональных команд
- Отсутствует логирование по зонам
- Нет механизма остановки для конкретных зон

### 3. UI ограничения
- Кнопки зон не связаны с глобальными переменными
- Нет отображения статуса выполнения по зонам
- Отсутствует прогресс-бар для мультизональных операций

## Рекомендации по интеграции

### 1. Минимальные изменения
- Расширить существующую систему зон без изменения архитектуры
- Добавить мультизональные команды как новый тип команд
- Использовать существующую систему флагов для управления

### 2. Обратная совместимость
- Сохранить поддержку существующих команд
- Не изменять API существующих компонентов
- Добавить новые функции через расширение

### 3. Тестирование
- Использовать существующую систему тестов
- Добавить тесты для мультизонального функционала
- Провести интеграционные тесты
