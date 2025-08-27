# План Очистки и Реорганизации Проекта

## Анализ Текущего Состояния

### Дублирующиеся Компоненты:
1. **Arduino директории:**
   - `arduino/` - основная версия
   - `arduino copy/` - копия (удалить)
   - `arduino_main/` - альтернативная версия (проанализировать)

### Тестовые файлы в корне (переместить в tests/):
- `test_simple.py`
- `test_signal_integration.py`
- `test_signal_performance.py`
- `test_ui_signals.py`
- `test_uart_integration.py`
- `test_tag_system_simple.py`
- `test_monitoring_simple.py`
- `test_monitoring_working.py`
- `test_monitoring_final.py`
- `test_monitoring_panel.py`
- `test_monitoring_complete.py`
- `test_send_command_fix.py`
- `test_serial_timeout.py`
- `test_type_hints.py`
- `test_di_container.py`
- `test_error_handling.py`
- `test_sequence_manager_threading.py`
- `test_thread_management.py`
- `test_race_conditions.py`
- `test_serial_threading.py`

### Временные/Отладочные файлы (удалить):
- `debug_tag_parsing.py`
- `check_types.py`
- `main_improved.py` (если это временная версия)

### Файлы покрытия (переместить в logs/):
- `coverage.xml`
- `htmlcov/` (директория)

### Дублирующиеся main файлы:
- `main.py` - основная версия
- `main_improved.py` - улучшенная версия (проанализировать)

## План Действий

### Фаза 1: Анализ и Резервное Копирование
1. Создать резервную копию проекта
2. Проанализировать различия между arduino версиями
3. Определить актуальную версию main файла

### Фаза 2: Очистка Дублирующихся Компонентов
1. Удалить `arduino copy/`
2. Проанализировать и объединить arduino_main/ если необходимо
3. Удалить временные файлы

### Фаза 3: Реорганизация Тестов
1. Переместить все тестовые файлы из корня в tests/
2. Организовать структуру тестов по категориям
3. Обновить импорты и пути

### Фаза 4: Очистка Временных Файлов
1. Удалить отладочные файлы
2. Переместить файлы покрытия
3. Очистить кэш директории

### Фаза 5: Финальная Оптимизация
1. Обновить .gitignore
2. Проверить зависимости
3. Обновить документацию

## Ожидаемый Результат

### Структура после очистки:
```
test_one24/
├── arduino/           # Единая arduino версия
├── core/             # Основная логика
├── ui/               # Пользовательский интерфейс
├── tests/            # Все тесты
├── docs/             # Документация
├── config/           # Конфигурация
├── utils/            # Утилиты
├── monitoring/       # Мониторинг
├── resources/        # Ресурсы
├── scripts/          # Скрипты
├── logs/             # Логи и отчеты
├── main.py           # Основной файл
├── requirements.txt  # Зависимости
└── README.md         # Документация
```

### Метрики улучшения:
- **Удалено файлов:** ~25+
- **Упрощена структура:** 15+ директорий → 10
- **Улучшена организация:** Все тесты в одном месте
- **Устранены дубликаты:** 100% дублирующихся компонентов

