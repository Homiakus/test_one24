# Руководство по использованию DI контейнера

## Обзор

DI (Dependency Injection) контейнер - это система для управления зависимостями между компонентами приложения. Он устраняет циклические зависимости, улучшает тестируемость и обеспечивает централизованное управление зависимостями.

## Основные возможности

- ✅ **Singleton и Transient жизненные циклы**
- ✅ **Автоматическое разрешение зависимостей**
- ✅ **Обнаружение циклических зависимостей**
- ✅ **Конфигурация через TOML файлы**
- ✅ **Thread-safety**
- ✅ **Валидация регистраций**
- ✅ **Глобальный контейнер**

## Быстрый старт

### 1. Базовое использование

```python
from core.di_container import DIContainer
from core.interfaces import ISerialManager, ICommandExecutor

# Создаем контейнер
container = DIContainer()

# Регистрируем сервисы
container.register(ISerialManager, SerialManager)
container.register(ICommandExecutor, CommandExecutor)

# Разрешаем зависимости
serial_manager = container.resolve(ISerialManager)
command_executor = container.resolve(ICommandExecutor)
```

### 2. Использование глобального контейнера

```python
from core.di_container import register, resolve, get_container

# Регистрация сервиса
register(ISerialManager, SerialManager)

# Разрешение зависимости
serial_manager = resolve(ISerialManager)
```

### 3. Конфигурация через TOML

```toml
[di_container.services.serial_manager]
interface = "ISerialManager"
implementation = "SerialManager"
singleton = true
dependencies = {}

[di_container.services.command_executor]
interface = "ICommandExecutor"
implementation = "BasicCommandExecutor"
singleton = true
dependencies = { "serial_manager" = "ISerialManager" }
```

```python
from core.di_config_loader import DIConfigLoader

# Загружаем конфигурацию
config_loader = DIConfigLoader()
config_loader.load_config("resources/di_config.toml")

# Получаем настроенный контейнер
container = config_loader.get_container()
```

## Интерфейсы

Все сервисы приложения должны реализовывать соответствующие интерфейсы:

### ISerialManager
```python
class ISerialManager(ABC):
    @abstractmethod
    def connect(self, port: str, baudrate: int = 115200, timeout: float = 1.0, **kwargs) -> bool:
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        pass
    
    @abstractmethod
    def send_command(self, command: str) -> bool:
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        pass
```

### ICommandExecutor
```python
class ICommandExecutor(ABC):
    @abstractmethod
    def execute(self, command: str, **kwargs) -> bool:
        pass
    
    @abstractmethod
    def validate_command(self, command: str) -> bool:
        pass
```

### ISequenceManager
```python
class ISequenceManager(ABC):
    @abstractmethod
    def expand_sequence(self, sequence_name: str) -> List[str]:
        pass
    
    @abstractmethod
    def validate_sequence(self, sequence_name: str) -> tuple[bool, List[str]]:
        pass
```

## Жизненные циклы

### Singleton (по умолчанию)
```python
# Один экземпляр на весь жизненный цикл приложения
container.register(ISerialManager, SerialManager, singleton=True)

service1 = container.resolve(ISerialManager)
service2 = container.resolve(ISerialManager)
# service1 is service2 == True
```

### Transient
```python
# Новый экземпляр при каждом разрешении
container.register(ILogger, Logger, singleton=False)

service1 = container.resolve(ILogger)
service2 = container.resolve(ILogger)
# service1 is service2 == False
```

## Зависимости

### Автоматическое разрешение по типу
```python
class CommandExecutor:
    def __init__(self, serial_manager: ISerialManager):
        self.serial_manager = serial_manager

# Контейнер автоматически разрешит ISerialManager
container.register(ICommandExecutor, CommandExecutor)
```

### Явное указание зависимостей
```python
class CommandExecutor:
    def __init__(self, serial_manager):
        self.serial_manager = serial_manager

# Явно указываем зависимости
container.register(
    ICommandExecutor, 
    CommandExecutor, 
    dependencies={"serial_manager": ISerialManager}
)
```

## Фабричные методы

```python
def create_command_executor(serial_manager: ISerialManager, executor_type: str = "basic"):
    if executor_type == "basic":
        return BasicCommandExecutor(serial_manager)
    else:
        return InteractiveCommandExecutor(serial_manager)

# Регистрация фабрики
container.register(
    ICommandExecutor,
    CommandExecutor,
    factory=create_command_executor,
    dependencies={"serial_manager": ISerialManager}
)
```

## Области видимости (Scopes)

```python
# Создание области видимости
with container.scope() as scope_container:
    service = scope_container.resolve(IService)
    # Сервис существует только в рамках этой области
```

## Обработка ошибок

### Незарегистрированный сервис
```python
try:
    service = container.resolve(IService)
except ValueError as e:
    print(f"Сервис не зарегистрирован: {e}")
```

### Циклические зависимости
```python
try:
    service = container.resolve(IService)
except RuntimeError as e:
    print(f"Обнаружена циклическая зависимость: {e}")
```

### Ошибки валидации
```python
errors = container.validate_registrations()
if errors:
    for error in errors:
        print(f"Ошибка валидации: {error}")
```

## Конфигурация TOML

### Структура файла конфигурации

```toml
[di_container]
max_resolution_depth = 50
timeout = 30.0

[di_container.services.serial_manager]
interface = "ISerialManager"
implementation = "SerialManager"
singleton = true
dependencies = {}

[di_container.services.command_executor]
interface = "ICommandExecutor"
implementation = "BasicCommandExecutor"
singleton = true
dependencies = { "serial_manager" = "ISerialManager" }

[di_container.factories.command_executor_factory]
name = "create_command_executor"
type = "basic"
dependencies = { "serial_manager" = "ISerialManager" }

[di_container.validation]
check_circular_dependencies = true
check_missing_dependencies = true
check_dependency_types = true
max_warnings = 100

[di_container.logging]
level = "INFO"
log_registration = true
log_resolution = true
log_resolution_errors = true
log_resolution_time = false
```

### Валидация конфигурации

```python
from core.di_config_loader import DIConfigLoader

config_loader = DIConfigLoader()
errors = config_loader.validate_config("resources/di_config.toml")

if errors:
    for error in errors:
        print(f"Ошибка: {error}")
else:
    print("Конфигурация валидна")
```

## Тестирование

### Создание mock объектов

```python
class MockSerialManager:
    def __init__(self):
        self.connected = False
        self.commands = []
    
    def connect(self, port: str, **kwargs):
        self.connected = True
        return True
    
    def send_command(self, command: str):
        self.commands.append(command)
        return True
    
    def is_connected(self):
        return self.connected

# Регистрация mock для тестов
container.register(ISerialManager, MockSerialManager)
```

### Тестирование с DI

```python
def test_command_execution():
    # Создаем тестовый контейнер
    container = DIContainer()
    container.register(ISerialManager, MockSerialManager)
    container.register(ICommandExecutor, CommandExecutor)
    
    # Получаем сервисы
    command_executor = container.resolve(ICommandExecutor)
    
    # Выполняем тест
    result = command_executor.execute("test command")
    assert result == True
```

## Интеграция с существующим кодом

### Пошаговый рефакторинг

1. **Создание интерфейсов**
   ```python
   # Определите интерфейсы для всех сервисов
   class IService(ABC):
       @abstractmethod
       def method(self):
           pass
   ```

2. **Реализация интерфейсов**
   ```python
   # Существующий класс реализует интерфейс
   class Service(IService):
       def method(self):
           return "implementation"
   ```

3. **Регистрация в контейнере**
   ```python
   # Регистрируем в DI контейнере
   container.register(IService, Service)
   ```

4. **Использование через DI**
   ```python
   # Вместо прямого создания
   # service = Service()
   
   # Используем DI
   service = container.resolve(IService)
   ```

## Лучшие практики

### 1. Используйте интерфейсы
```python
# Хорошо
def process_data(service: IService):
    return service.process()

# Плохо
def process_data(service: Service):
    return service.process()
```

### 2. Избегайте циклических зависимостей
```python
# Хорошо - используйте события или callback
class ServiceA:
    def __init__(self, event_bus: IEventBus):
        self.event_bus = event_bus

class ServiceB:
    def __init__(self, event_bus: IEventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe("event", self.handle_event)
```

### 3. Используйте фабрики для сложных объектов
```python
def create_complex_service(config: Dict, logger: ILogger):
    return ComplexService(config, logger)

container.register(
    IComplexService,
    ComplexService,
    factory=create_complex_service
)
```

### 4. Тестируйте с mock объектами
```python
# В тестах используйте mock объекты
container.register(ISerialManager, MockSerialManager)
container.register(ILogger, MockLogger)
```

## Примеры

Смотрите файл `examples/di_usage_example.py` для полных примеров использования.

## Устранение неполадок

### Проблема: "Сервис не зарегистрирован"
**Решение:** Убедитесь, что сервис зарегистрирован перед его использованием.

### Проблема: "Циклическая зависимость"
**Решение:** Пересмотрите архитектуру, используйте события или callback.

### Проблема: "Не удалось загрузить класс"
**Решение:** Проверьте правильность имен классов в конфигурации TOML.

### Проблема: "Ошибка разрешения зависимостей"
**Решение:** Убедитесь, что все зависимости зарегистрированы и доступны.
