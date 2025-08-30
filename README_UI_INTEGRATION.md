# Интеграция UI с MOTTO - Краткое руководство

## 🚀 Быстрый старт

### Запуск приложения с MOTTO
```bash
# Запуск с автоматическим выбором конфигурации
python3 main_motto.py

# Или прямое указание конфигурации
python3 main_motto.py --config config_motto_fixed.toml
```

### Использование в коде
```python
from core.motto.ui_integration import MOTTOUIIntegration

# Создание интеграции
integration = MOTTOUIIntegration('config_motto_fixed.toml')

# Получение совместимой конфигурации
config = integration.get_compatible_config()

# Выполнение последовательности с MOTTO возможностями
success = integration.execute_sequence_with_motto('load_tubes')
```

## 📋 Основные компоненты

### 1. MOTTOUIIntegration
Основной адаптер для интеграции MOTTO с UI.

**Возможности:**
- Загрузка MOTTO конфигурации
- Преобразование в совместимый формат
- Выполнение последовательностей с гвардами и политиками
- Получение информации о системе

### 2. MOTTOConfigLoader
Загрузчик конфигурации с автоматическим определением типа.

**Возможности:**
- Автоматическое определение MOTTO/стандартной конфигурации
- Загрузка в совместимом формате
- Доступ к MOTTO возможностям

### 3. MainWindowMOTTO
Модифицированное главное окно с поддержкой MOTTO.

**Возможности:**
- Отображение MOTTO информации
- Интерактивное выполнение последовательностей
- Переключение между конфигурациями
- Прогресс выполнения

## 🔧 Использование

### Загрузка конфигурации
```python
from core.motto.ui_integration import MOTTOConfigLoader

# Автоматическое определение типа
loader = MOTTOConfigLoader('config_motto_fixed.toml')

# Загрузка в совместимом формате
config = loader.load()

# Информация о MOTTO
motto_info = loader.get_motto_info()
print(f"MOTTO версия: {motto_info['version']}")
print(f"Команд: {motto_info['commands_count']}")
print(f"Последовательностей: {motto_info['sequences_count']}")
```

### Выполнение последовательностей
```python
# Простое выполнение
success = integration.execute_sequence_with_motto('load_tubes')

# С прогрессом
def progress_callback(progress, message):
    print(f"Прогресс: {progress}% - {message}")

success = integration.execute_sequence_with_motto(
    'load_tubes',
    progress_callback=progress_callback
)
```

### Получение данных для UI
```python
# Команды для UI
buttons = integration.get_buttons_for_ui()
print(f"Доступно команд: {len(buttons)}")

# Последовательности для UI
sequences = integration.get_sequences_for_ui()
print(f"Доступно последовательностей: {len(sequences)}")

# Настройки Serial
serial_settings = integration.get_serial_settings()
print(f"Порт: {serial_settings['port']}")
```

## 🎯 MOTTO возможности

### Гварды и условия
```python
# Последовательности автоматически проверяют гварды
# Например: no_alarms, serial_connected
sequence = integration.motto_config.sequences['og']
print(f"Гварды: {sequence.guards}")
```

### Политики выполнения
```python
# Политики определяют поведение при ошибках
# safe_retry - безопасные повторные попытки
# fast_fail - быстрый отказ
print(f"Политика: {sequence.policy}")
```

### События и обработчики
```python
# MOTTO поддерживает события и их обработчики
events = integration.motto_config.events
handlers = integration.motto_config.handlers
```

## 🔄 Совместимость

### Существующий код
```python
# Старый код продолжает работать без изменений
from config.config_loader import ConfigLoader

# Заменяем на MOTTOConfigLoader
from core.motto.ui_integration import MOTTOConfigLoader

loader = MOTTOConfigLoader('config_motto_fixed.toml')
config = loader.load()

# Существующий код работает как прежде
sequence_manager = SequenceManager(config['sequences'], config['buttons'])
```

### Переключение конфигураций
```python
# В UI можно переключаться между конфигурациями
# Файл -> Переключить конфигурацию
# Или программно:
loader = MOTTOConfigLoader('config.toml')  # Стандартная
loader = MOTTOConfigLoader('config_motto_fixed.toml')  # MOTTO
```

## 📊 Мониторинг

### Информация о системе
```python
info = integration.get_motto_info()
print(f"""
MOTTO Система:
  Версия: {info['version']}
  Команд: {info['commands_count']}
  Последовательностей: {info['sequences_count']}
  Условий: {info['conditions_count']}
  Гвардов: {info['guards_count']}
  Политик: {info['policies_count']}
""")
```

### Логирование
```python
import logging

# MOTTO интеграция использует стандартное логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('core.motto.ui_integration')

# Логи будут показывать:
# - Загрузку конфигурации
# - Выполнение последовательностей
# - Проверку гвардов
# - Ошибки и предупреждения
```

## 🧪 Тестирование

### Запуск тестов
```bash
# Тесты интеграции
python3 test_ui_integration.py

# Демонстрация функциональности
python3 test_ui_integration.py --demo
```

### Проверка совместимости
```bash
# Тесты совместимости
python3 test_compatibility.py
```

## 🚨 Устранение неполадок

### Проблема: Конфигурация не загружается
```python
# Проверьте наличие файла
import os
if not os.path.exists('config_motto_fixed.toml'):
    print("Файл конфигурации не найден")

# Проверьте формат TOML
import tomli
try:
    with open('config_motto_fixed.toml', 'rb') as f:
        config = tomli.load(f)
except Exception as e:
    print(f"Ошибка TOML: {e}")
```

### Проблема: Команды не загружаются
```python
# Проверьте секцию commands в TOML
config = tomli.load(open('config_motto_fixed.toml', 'rb'))
if 'commands' not in config:
    print("Секция commands отсутствует")
```

### Проблема: Последовательности не выполняются
```python
# Проверьте наличие последовательности
sequences = integration.get_sequences_for_ui()
if 'load_tubes' not in sequences:
    print("Последовательность load_tubes не найдена")

# Проверьте гварды
sequence = integration.motto_config.sequences['load_tubes']
print(f"Гварды: {sequence.guards}")
```

## 📚 Дополнительная документация

- [Полная документация MOTTO](README_MOTTO.md)
- [Отчёт об интеграции](DocsPro/09_Reports/ui_integration_report.md)
- [Отчёт о совместимости](DocsPro/09_Reports/compatibility_verification.md)
- [Архитектура MOTTO](DocsPro/03_Design/architecture.md)

## 🎯 Следующие шаги

1. **Изучите возможности**: Ознакомьтесь с гвардами, политиками, событиями
2. **Создайте свои последовательности**: Используйте MOTTO возможности для новых задач
3. **Настройте мониторинг**: Добавьте логирование и трассировку
4. **Расширьте функциональность**: Используйте параллельные последовательности и транзакции

---

**Готово к использованию!** 🚀