# Thread-Safety Улучшения в Sequence Manager

## Обзор

Внесены значительные улучшения в `core/sequence_manager.py` для обеспечения thread-safety, валидации команд и защиты от рекурсии.

## Новые Компоненты

### 1. CommandValidator

Класс для валидации команд с поддержкой различных типов:

```python
class CommandValidator:
    def __init__(self, max_recursion_depth: int = 10, max_wait_time: float = 3600.0):
        self.max_recursion_depth = max_recursion_depth
        self.max_wait_time = max_wait_time
    
    def validate_command(self, command: str) -> ValidationResult:
        # Валидирует команду и возвращает результат
```

**Возможности:**
- Валидация синтаксиса wait команд
- Проверка диапазонов времени ожидания
- Обнаружение пустых команд
- Типизация команд (REGULAR, WAIT, SEQUENCE, BUTTON, UNKNOWN)

### 2. ThreadSafeResponseCollector

Thread-safe коллектор ответов с использованием Queue:

```python
class ThreadSafeResponseCollector:
    def __init__(self, max_size: int = 1000):
        self._queue = Queue(maxsize=max_size)
        self._lock = threading.Lock()
    
    def add_response(self, response: str) -> bool:
        # Добавляет ответ в thread-safe очередь
    
    def get_responses(self, timeout: float = 0.1) -> List[str]:
        # Получает все доступные ответы
```

**Преимущества:**
- Замена небезопасного `list` на `Queue`
- Атомарные операции с использованием locks
- Ограничение размера буфера
- Подсчет общего количества ответов

### 3. CancellationToken

Токен для безопасной отмены операций:

```python
class CancellationToken:
    def __init__(self):
        self._cancelled = False
        self._lock = threading.Lock()
    
    def cancel(self):
        # Отменяет операцию
    
    def is_cancelled(self) -> bool:
        # Проверяет статус отмены
    
    def throw_if_cancelled(self):
        # Выбрасывает исключение если операция отменена
```

**Применение:**
- Замена флага `running` в CommandSequenceExecutor
- Thread-safe отмена длительных операций
- Исключение CancellationException для обработки отмены

### 4. RecursionProtector

Защита от рекурсии и кеширование результатов:

```python
class RecursionProtector:
    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self._call_stack = threading.local()
        self._cache = {}
        self._cache_lock = threading.Lock()
    
    def enter_sequence(self, sequence_name: str) -> bool:
        # Проверяет возможность входа в последовательность
    
    def cache_result(self, cache_key: str, result: List[str]):
        # Кеширует результат разворачивания
```

**Функции:**
- Ограничение глубины рекурсии
- Детекция циклических зависимостей
- Кеширование результатов expand_sequence
- Thread-local стек вызовов

## Улучшения в Существующих Классах

### CommandSequenceExecutor

**Thread-Safety улучшения:**
- Замена `self.responses = []` на `ThreadSafeResponseCollector`
- Замена `self.running` на `CancellationToken`
- Валидация команд перед выполнением
- Обработка исключений отмены

**Новые возможности:**
```python
def __init__(self, serial_manager, commands: List[str],
             keywords: Optional[SequenceKeywords] = None,
             cancellation_token: Optional[CancellationToken] = None):
    # Добавлен cancellation_token для безопасной отмены
```

### SequenceManager

**Thread-Safety улучшения:**
- Добавлен `threading.Lock()` для защиты shared state
- Thread-safe валидация последовательностей
- Защита от рекурсии в expand_sequence

**Новые методы:**
```python
def validate_sequence(self, sequence_name: str) -> Tuple[bool, List[str]]:
    # Возвращает (is_valid, errors) вместо bool

def get_sequence_info(self, sequence_name: str) -> Dict[str, Any]:
    # Полная информация о последовательности

def clear_cache(self):
    # Очистка кеша рекурсии
```

## Валидация Команд

### Wait Команды

Строгая валидация синтаксиса:
```python
# Валидные команды
"wait 5.0"     # ✓
"wait 0.1"     # ✓

# Невалидные команды
"wait"         # ✗ Неверный синтаксис
"wait -1"      # ✗ Отрицательное время
"wait abc"     # ✗ Неверный формат
"wait 5000"    # ✗ Превышение лимита
```

### Обычные Команды

- Проверка на пустые команды
- Валидация синтаксиса
- Типизация команд

## Защита от Рекурсии

### Ограничения

1. **Максимальная глубина:** 10 уровней (настраивается)
2. **Детекция циклов:** Автоматическое обнаружение циклических зависимостей
3. **Кеширование:** Результаты разворачивания кешируются для производительности

### Примеры

```python
# Рекурсивная последовательность (обнаруживается)
config = {
    "recursive": ["recursive", "cmd1"]  # ✗ Цикл
}

# Глубокая вложенность (ограничивается)
config = {
    "level1": ["level2"],
    "level2": ["level3"],
    # ... до max_depth
}
```

## Тестирование

Создан тестовый файл `test_sequence_manager_threading.py` с проверками:

1. **CommandValidator** - валидация различных типов команд
2. **ThreadSafeResponseCollector** - многопоточное добавление/получение ответов
3. **CancellationToken** - отмена операций
4. **RecursionProtector** - защита от рекурсии
5. **SequenceManager** - thread-safety при многопоточном доступе
6. **CommandSequenceExecutor** - выполнение с отменой

## Использование

### Базовое использование

```python
from core.sequence_manager import SequenceManager, CommandValidator

# Создание менеджера
config = {"test_seq": ["cmd1", "wait 1.0", "cmd2"]}
buttons_config = {"button1": "button_cmd1"}
manager = SequenceManager(config, buttons_config)

# Валидация
is_valid, errors = manager.validate_sequence("test_seq")
if not is_valid:
    print(f"Ошибки: {errors}")

# Получение информации
info = manager.get_sequence_info("test_seq")
print(f"Команд: {info['command_count']}")
```

### С отменой операций

```python
from core.sequence_manager import CommandSequenceExecutor, CancellationToken

# Создание токена отмены
token = CancellationToken()

# Исполнитель с отменой
executor = CommandSequenceExecutor(
    serial_manager, 
    commands, 
    cancellation_token=token
)

# Запуск
executor.start()

# Отмена через некоторое время
time.sleep(5)
token.cancel()
executor.wait()
```

## Производительность

### Кеширование

- Результаты `expand_sequence` кешируются
- Ключ кеша включает имя последовательности и посещенные узлы
- Автоматическая очистка кеша при необходимости

### Thread-Safety

- Минимальные блокировки для максимальной производительности
- Использование `Queue` для эффективной передачи данных между потоками
- Thread-local переменные для изоляции состояния

## Совместимость

Все изменения обратно совместимы:
- Существующие интерфейсы сохранены
- Добавлены новые опциональные параметры
- Поведение по умолчанию не изменилось

## Заключение

Внесенные улучшения обеспечивают:

1. **Thread-safety** - безопасная работа в многопоточной среде
2. **Валидацию** - строгая проверка команд и последовательностей
3. **Защиту от рекурсии** - предотвращение бесконечных циклов
4. **Производительность** - кеширование и оптимизированные структуры данных
5. **Надежность** - обработка исключений и отмена операций

