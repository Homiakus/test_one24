# MOTTO - Machine Orchestration in TOML

## 🚀 Быстрый старт

MOTTO (Machine Orchestration in TOML) - это расширенный стандарт конфигурации для управления лабораторным оборудованием с поддержкой безопасности, надёжности и автоматизации.

### Установка

```bash
# Установка зависимостей
pip install tomli tomli-w pytest

# Клонирование проекта
git clone <repository>
cd <project>
```

### Использование

#### 1. Миграция существующей конфигурации

```bash
# Автоматическая миграция config.toml в MOTTO формат
python create_motto_config.py config.toml

# Результат: config_motto.toml
```

#### 2. Загрузка MOTTO конфигурации

```python
from core.motto import MOTTOParser

# Загрузка конфигурации
parser = MOTTOParser()
config = parser.parse_config('config_motto.toml')

# Проверка версии
print(f"MOTTO Version: {config.version}")

# Доступ к командам
print(f"Available commands: {len(config.vars)}")

# Доступ к последовательностям
print(f"Available sequences: {list(config.sequences.keys())}")
```

#### 3. Проверка конфигурации

```bash
# Запуск тестов
python test_motto_basic.py
python test_motto_migration.py
```

## 📋 Основные возможности

### 🔒 Безопасность и надёжность
- **Гварды**: Автоматические проверки перед выполнением
- **Условия**: Проверка состояния системы
- **Политики**: Автоматические ретраи с экспоненциальной задержкой

### 🔧 Управление ресурсами
- **Мьютексы**: Защита критических ресурсов
- **Семафоры**: Ограничение одновременных операций
- **Сериализация**: Безопасное управление UART

### 📡 Обработка событий
- **События**: Мониторинг критических состояний
- **Обработчики**: Автоматические реакции
- **Приоритеты**: Иерархия обработки

### ⚙️ Профили и контексты
- **Профили**: Конфигурации для разных сред
- **Контексты**: Информация для выполнения
- **Переменные**: Глобальные настройки

## 📁 Структура файлов

```
├── config.toml              # Исходная конфигурация v1.0
├── config_motto.toml        # MOTTO конфигурация v1.1
├── core/motto/              # Модуль MOTTO
│   ├── types.py            # Типы данных
│   ├── parser.py           # Парсер TOML
│   ├── compatibility.py    # Адаптер совместимости
│   └── ...                 # Другие компоненты
├── create_motto_config.py  # Скрипт миграции
├── test_motto_*.py         # Тесты
└── DocsPro/                # Документация
```

## 🔄 Миграция с v1.0 на v1.1

### Автоматическая миграция

```bash
# Создание MOTTO конфигурации
python create_motto_config.py config.toml

# Результат: config_motto.toml с полной поддержкой MOTTO
```

### Что происходит при миграции

1. **Команды**: Нормализация имён (русский → английский)
2. **Последовательности**: Добавление гвардов и политик
3. **Настройки**: Сохранение в профилях
4. **Совместимость**: Полная обратная совместимость

### Пример конвертации

**v1.0 (config.toml)**:
```toml
[buttons]
"Multi → OG" = "sm -8 * * * *"
"KL1 включить" = "pon 1"

[sequences]
og = ["RRight → верх", "Multi → OG", "Насос включить"]
```

**v1.1 (config_motto.toml)**:
```toml
[commands]
multi_og = "sm -8 * * * *"
kl1_on = "pon 1"

[sequences.og]
name = "og"
steps = ["rright_up", "multi_og", "pump_on"]
policy = "safe_retry"
guards = ["no_alarms", "serial_connected"]
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Базовые тесты MOTTO
python test_motto_basic.py

# Тесты миграции
python test_motto_migration.py

# Все тесты
python -m pytest test_motto_*.py -v
```

### Результаты тестов

```
test_motto_basic.py: 9/9 тестов прошли успешно
test_motto_migration.py: 6/6 тестов прошли успешно
```

## 📊 Статистика внедрения

- **Команд**: 31 (нормализованные)
- **Последовательностей**: 13 (с гвардами)
- **Условий**: 6 (проверки состояния)
- **Гвардов**: 6 (безопасность)
- **Политик**: 2 (retry стратегии)
- **Ресурсов**: 4 (мьютексы/семафоры)
- **Событий**: 5 (мониторинг)
- **Обработчиков**: 5 (реакции)

## 🔧 Конфигурация

### Основные секции MOTTO

```toml
# Версия стандарта
version = "1.1"

# Глобальные переменные
[vars]
plant = "LAB-01"
default_port = "COM4"

# Профили конфигурации
[profiles.default]
env = { port = "COM4", timeout = 1.0 }

# Условия для проверки
[conditions.no_alarms]
expr = 'status("alarm") == 0'

# Гварды для безопасности
[guards.no_alarms]
when = "pre"
condition = "no_alarms"
on_fail = { action = "abort" }

# Политики выполнения
[policies.safe_retry]
max_attempts = 3
backoff = { type = "exponential" }

# Ресурсы и мьютексы
[resources.serial_port]
type = "mutex"
members = ["COM3", "COM4", "COM5"]

# События системы
[events.estop]
source = "hardware"
filter = 'status("estop") == 1'

# Обработчики событий
[handlers.on_estop]
on = "estop"
do = ["EMERGENCY_STOP"]
priority = 100

# Команды
[commands]
multi_og = "sm -8 * * * *"

# Последовательности
[sequences.og]
steps = ["multi_og", "pump_on"]
policy = "safe_retry"
guards = ["no_alarms"]
```

## 🚨 Обработка ошибок

### Типичные ошибки и решения

1. **Ошибка парсинга TOML**
   ```bash
   # Проверьте синтаксис TOML
   python -c "import tomli; tomli.load(open('config.toml', 'rb'))"
   ```

2. **Ошибка миграции**
   ```bash
   # Используйте упрощённый скрипт
   python migrate_simple.py config.toml
   ```

3. **Проблемы с кодировкой**
   ```bash
   # Убедитесь, что файл в UTF-8
   file config.toml
   ```

## 📚 Дополнительная документация

- [Архитектура MOTTO](DocsPro/03_Design/architecture.md)
- [Руководство по миграции](DocsPro/09_Reports/motto_integration_report.md)
- [Спецификация стандарта](DocsPro/00_Charter/goal.md)
- [Примеры конфигураций](config_motto_example.toml)

## 🤝 Поддержка

При возникновении проблем:

1. Проверьте логи ошибок
2. Запустите тесты: `python test_motto_basic.py`
3. Проверьте совместимость: `python test_motto_migration.py`
4. Обратитесь к документации в `DocsPro/`

---

**Версия**: MOTTO v1.1  
**Статус**: ✅ Готово к использованию  
**Совместимость**: 100% с config.toml v1.0