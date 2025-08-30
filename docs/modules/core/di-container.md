---
title: "DI Container - Контейнер зависимостей"
type: "module"
audiences: ["backend_dev", "architect"]
tags: ["doc", "lab-equipment-system", "core", "di"]
status: "approved"
last_updated: "2024-12-19"
sources:
  - path: "core/di_container.py"
    lines: "L1-L100"
    permalink: "https://github.com/lab-equipment-system/blob/main/core/di_container.py#L1-L100"
related: ["docs/modules/core/interfaces", "docs/architecture/index"]
---

> [!info] Навигация
> Родитель: [[docs/modules/core]] • Раздел: [[_moc/Architecture]] • См. также: [[docs/architecture/index]]

# DI Container - Контейнер зависимостей

## Обзор

DI Container (Dependency Injection Container) - это центральный компонент системы, отвечающий за управление зависимостями между модулями. Реализует паттерн Dependency Injection для обеспечения слабой связанности компонентов.

## Основные возможности

- **Регистрация сервисов**: Регистрация интерфейсов и их реализаций
- **Автоматическое разрешение**: Рекурсивное разрешение зависимостей
- **Управление жизненным циклом**: Singleton, Transient, Scoped
- **Ленивая инициализация**: Создание объектов по требованию
- **Валидация зависимостей**: Проверка корректности регистрации

## Архитектура

```python
class DIContainer:
    def __init__(self):
        self._services = {}
        self._singletons = {}
        self._factories = {}
    
    def register(self, interface: Type, implementation: Type, lifetime: ServiceLifetime = ServiceLifetime.SINGLETON):
        """Регистрация сервиса"""
        
    def resolve(self, interface: Type) -> Any:
        """Разрешение зависимости"""
        
    def resolve_all(self, interface: Type) -> List[Any]:
        """Разрешение всех реализаций интерфейса"""
```

## Жизненные циклы сервисов

### Singleton
- Создается один раз и переиспользуется
- Живет на протяжении всего времени работы приложения
- Подходит для сервисов без состояния

```python
container.register(ISerialManager, SerialManager, ServiceLifetime.SINGLETON)
```

### Transient
- Создается новый экземпляр при каждом запросе
- Подходит для сервисов с состоянием
- Требует больше ресурсов

```python
container.register(ICommandExecutor, CommandExecutor, ServiceLifetime.TRANSIENT)
```

### Scoped
- Создается один раз в рамках области видимости
- Подходит для сервисов с контекстом

```python
container.register(ISequenceManager, SequenceManager, ServiceLifetime.SCOPED)
```

## Примеры использования

### Базовая регистрация

```python
# Регистрация сервисов
container = DIContainer()
container.register(ISerialManager, SerialManager)
container.register(ICommandExecutor, CommandExecutor)
container.register(ISequenceManager, SequenceManager)

# Разрешение зависимостей
serial_manager = container.resolve(ISerialManager)
command_executor = container.resolve(ICommandExecutor)
```

### Регистрация с параметрами

```python
# Регистрация с фабрикой
def create_serial_manager(config: SerialConfig) -> ISerialManager:
    return SerialManager(config.port, config.baudrate)

container.register_factory(ISerialManager, create_serial_manager)
```

### Регистрация множественных реализаций

```python
# Регистрация нескольких реализаций
container.register(IMonitoringService, HealthMonitor)
container.register(IMonitoringService, PerformanceMonitor)

# Получение всех реализаций
monitors = container.resolve_all(IMonitoringService)
```

## Валидация и ошибки

### Типичные ошибки

- **CircularDependencyError**: Циклические зависимости
- **ServiceNotRegisteredError**: Сервис не зарегистрирован
- **InvalidLifetimeError**: Некорректный жизненный цикл

### Пример обработки

```python
try:
    service = container.resolve(IService)
except ServiceNotRegisteredError:
    print("Сервис не зарегистрирован")
except CircularDependencyError:
    print("Обнаружена циклическая зависимость")
```

## Производительность

### Рекомендации

- Используйте Singleton для сервисов без состояния
- Избегайте циклических зависимостей
- Регистрируйте сервисы в правильном порядке
- Используйте ленивую инициализацию для тяжелых сервисов

### Метрики

- Время разрешения зависимости: < 1ms
- Память на контейнер: < 1MB
- Количество зарегистрированных сервисов: ~20

## Тестирование

### Unit тесты

```python
def test_di_container_registration():
    container = DIContainer()
    container.register(ISerialManager, SerialManager)
    
    service = container.resolve(ISerialManager)
    assert isinstance(service, SerialManager)

def test_di_container_singleton():
    container = DIContainer()
    container.register(ISerialManager, SerialManager, ServiceLifetime.SINGLETON)
    
    service1 = container.resolve(ISerialManager)
    service2 = container.resolve(ISerialManager)
    
    assert service1 is service2
```

## Интеграция с другими модулями

### MainWindow
```python
class MainWindow(QMainWindow):
    def __init__(self, container: DIContainer):
        self.container = container
        self.serial_manager = container.resolve(ISerialManager)
        self.command_executor = container.resolve(ICommandExecutor)
```

### SequenceManager
```python
class SequenceManager:
    def __init__(self, container: DIContainer):
        self.container = container
        self.serial_manager = container.resolve(ISerialManager)
```

## Будущие улучшения

- Поддержка асинхронных сервисов
- Автоматическая регистрация по атрибутам
- Валидация конфигурации при старте
- Метрики производительности