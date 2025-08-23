# 🚩 Руководство по условному выполнению последовательностей

## 📋 Обзор

Система условного выполнения позволяет создавать интеллектуальные последовательности команд, которые могут изменять свое поведение в зависимости от состояния глобальных флагов. Это обеспечивает гибкость и безопасность при автоматизации процессов.

## 🎯 Основные возможности

### ✅ Поддерживаемые условные конструкции

1. **Простое условие** - `if flag_name`
2. **Условие с альтернативой** - `if flag_name` + `else` + `endif`
3. **Остановка выполнения** - `stop_if_not flag_name`
4. **Вложенные условия** - поддержка многоуровневой вложенности

### 🔧 Типы команд

- **`if flag_name`** - начало условного блока
- **`else`** - альтернативная ветка выполнения
- **`endif`** - конец условного блока
- **`stop_if_not flag_name`** - остановка выполнения если флаг false

## 📝 Синтаксис конфигурации

### Флаги в config.toml

```toml
[flags]
auto_mode = true
safety_check = true
emergency_stop = false
maintenance_mode = false
test_mode = false
```

### Последовательности с условиями

```toml
[sequences]
# Простое условие
conditional_seq = [
    "if safety_check",
    "command1",
    "command2",
    "endif"
]

# Условие с else
if_else_seq = [
    "if auto_mode",
    "automatic_command1",
    "automatic_command2",
    "else",
    "manual_command1",
    "manual_command2",
    "endif"
]

# Остановка выполнения
safe_operation = [
    "stop_if_not safety_check",
    "dangerous_command1",
    "dangerous_command2"
]

# Вложенные условия
complex_sequence = [
    "if outer_flag",
    "command1",
    "if inner_flag",
    "command2",
    "else",
    "command3",
    "endif",
    "command4",
    "endif"
]
```

## 🎮 Управление флагами через UI

### Страница "Управление флагами"

1. **Откройте страницу** - нажмите "🚩 Управление флагами" в боковой панели
2. **Просмотр флагов** - флаги сгруппированы по категориям:
   - Системные флаги
   - Режимы работы
   - Пользовательские флаги
3. **Изменение состояния** - используйте чекбоксы для включения/выключения
4. **Сброс к значениям по умолчанию** - кнопка "🔄 Сброс"

### Программное управление

```python
# Установка флага
sequence_manager.set_flag("safety_check", True)

# Получение значения флага
value = sequence_manager.get_flag("safety_check", default=False)

# Получение всех флагов
all_flags = sequence_manager.get_all_flags()
```

## 🔄 Логика выполнения

### Условие if

```toml
conditional_seq = [
    "if flag_name",
    "command1",  # Выполнится если flag_name = true
    "command2",  # Выполнится если flag_name = true
    "endif"
]
```

**Поведение:**
- Если `flag_name = true` → выполняются `command1`, `command2`
- Если `flag_name = false` → команды пропускаются

### Условие if-else

```toml
if_else_seq = [
    "if flag_name",
    "command1",  # Выполнится если flag_name = true
    "else",
    "command2",  # Выполнится если flag_name = false
    "endif"
]
```

**Поведение:**
- Если `flag_name = true` → выполняется `command1`
- Если `flag_name = false` → выполняется `command2`

### Остановка выполнения

```toml
safe_operation = [
    "stop_if_not safety_flag",
    "command1",  # Выполнится только если safety_flag = true
    "command2"   # Выполнится только если safety_flag = true
]
```

**Поведение:**
- Если `safety_flag = true` → выполняются все команды
- Если `safety_flag = false` → выполнение останавливается с ошибкой

### Вложенные условия

```toml
nested_seq = [
    "if outer_flag",
    "command1",
    "if inner_flag",
    "command2",
    "else",
    "command3",
    "endif",
    "command4",
    "endif"
]
```

**Поведение:**
- `outer_flag = false` → ничего не выполняется
- `outer_flag = true, inner_flag = true` → `command1`, `command2`, `command4`
- `outer_flag = true, inner_flag = false` → `command1`, `command3`, `command4`

## 🛡️ Безопасность

### Валидация последовательностей

Система автоматически проверяет корректность условных конструкций:

- ✅ Сбалансированные `if`/`endif`
- ✅ Корректное использование `else`
- ✅ Отсутствие вложенности глубже 10 уровней
- ❌ Незакрытые условные блоки
- ❌ `else` без соответствующего `if`

### Обработка ошибок

```python
# Валидация последовательности
is_valid, errors = sequence_manager.validate_sequence("sequence_name")
if not is_valid:
    print(f"Ошибки валидации: {errors}")
```

## 📊 Мониторинг и отладка

### Логирование

Все операции с флагами и условным выполнением логируются:

```
INFO - Флаг 'safety_check' установлен в True
INFO - Вход в условный блок if safety_check = True
INFO - Выход из условного блока
WARNING - Остановка выполнения: флаг emergency_stop = True
```

### Сигналы Qt

```python
# Подписка на изменения флагов
executor.flag_changed.connect(lambda flag_name, value: print(f"Флаг {flag_name} = {value}"))

# Подписка на вход в условные блоки
executor.conditional_entered.connect(lambda condition, result: print(f"Условие {condition} = {result}"))

# Подписка на выход из условных блоков
executor.conditional_exited.connect(lambda condition: print(f"Выход из {condition}"))
```

## 🔧 Примеры использования

### Пример 1: Безопасная операция

```toml
[flags]
safety_check = true
emergency_stop = false

[sequences]
safe_operation = [
    "stop_if_not safety_check",
    "if emergency_stop",
    "emergency_shutdown",
    "else",
    "normal_operation",
    "endif"
]
```

### Пример 2: Адаптивная последовательность

```toml
[flags]
auto_mode = true
maintenance_mode = false
test_mode = false

[sequences]
adaptive_sequence = [
    "if auto_mode",
    "if maintenance_mode",
    "maintenance_procedure",
    "else",
    "if test_mode",
    "test_procedure",
    "else",
    "production_procedure",
    "endif",
    "endif",
    "else",
    "manual_procedure",
    "endif"
]
```

### Пример 3: Многоуровневая проверка безопасности

```toml
[flags]
primary_safety = true
secondary_safety = true
emergency_system = true

[sequences]
critical_operation = [
    "stop_if_not primary_safety",
    "stop_if_not secondary_safety",
    "if emergency_system",
    "emergency_protocol",
    "endif",
    "critical_command1",
    "critical_command2"
]
```

## 🚀 Рекомендации

### ✅ Лучшие практики

1. **Используйте осмысленные имена флагов** - `safety_check` лучше чем `flag1`
2. **Группируйте связанные флаги** - создавайте логические группы
3. **Проверяйте валидность** - всегда валидируйте последовательности перед использованием
4. **Документируйте логику** - добавляйте комментарии в конфигурацию
5. **Тестируйте сценарии** - проверяйте все возможные комбинации флагов

### ❌ Избегайте

1. **Слишком глубокой вложенности** - максимум 3-4 уровня
2. **Сложной логики** - разбивайте сложные последовательности на простые
3. **Магических флагов** - используйте понятные имена
4. **Отсутствия валидации** - всегда проверяйте корректность

## 🔍 Отладка

### Проверка состояния флагов

```python
# Получить все флаги
flags = sequence_manager.get_all_flags()
print(f"Текущие флаги: {flags}")

# Проверить конкретный флаг
if sequence_manager.get_flag("safety_check"):
    print("Проверка безопасности активна")
```

### Анализ последовательности

```python
# Получить информацию о последовательности
info = sequence_manager.get_sequence_info("sequence_name")
print(f"Команды: {info['commands']}")
print(f"Используемые флаги: {info['used_flags']}")
```

### Логирование выполнения

```python
# Включить подробное логирование
import logging
logging.getLogger('core.sequence_manager').setLevel(logging.DEBUG)
```

## 📈 Производительность

### Оптимизации

1. **Кэширование** - результаты разворачивания последовательностей кэшируются
2. **Thread-safety** - все операции с флагами потокобезопасны
3. **Минимальные проверки** - условия проверяются только при необходимости

### Мониторинг

```python
# Проверить производительность
import time

start_time = time.time()
sequence_manager.expand_sequence("complex_sequence")
execution_time = time.time() - start_time
print(f"Время разворачивания: {execution_time:.3f}с")
```

## 🔄 Миграция

### Обновление существующих последовательностей

1. **Добавьте флаги** в секцию `[flags]`
2. **Обновите последовательности** с условными конструкциями
3. **Протестируйте** все сценарии выполнения
4. **Обновите документацию** с описанием логики

### Обратная совместимость

- Существующие последовательности без условий работают как прежде
- Новые условные конструкции не влияют на старые последовательности
- Постепенная миграция возможна без прерывания работы

---

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи приложения
2. Убедитесь в корректности синтаксиса
3. Проверьте валидность последовательностей
4. Обратитесь к документации API

**Удачного использования условного выполнения! 🚀**