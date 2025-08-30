---
title: "API Reference"
type: "api_reference"
audiences: ["backend_dev", "frontend_dev", "architect"]
tags: ["doc", "lab-equipment-system", "api"]
aliases: ["docs/api", "docs/reference"]
status: "approved"
last_updated: "2024-12-19"
sources:
  - path: "core/interfaces.py"
    lines: "L1-L100"
    permalink: "https://github.com/lab-equipment-system/blob/main/core/interfaces.py#L1-L100"
  - path: "core/serial_manager.py"
    lines: "L1-L50"
    permalink: "https://github.com/lab-equipment-system/blob/main/core/serial_manager.py#L1-L50"
related: ["docs/architecture/index", "docs/modules/core", "docs/schemas/commands"]
---

> [!info] Навигация
> Родитель: [[docs/overview]] • Раздел: [[_moc/API]] • См. также: [[docs/architecture/index]]

# API Reference

## Обзор

API системы управления лабораторным оборудованием предоставляет интерфейсы для:
- Управления последовательными портами
- Выполнения команд на оборудовании
- Управления последовательностями операций
- Мониторинга состояния системы
- Конфигурации и настроек

## Основные интерфейсы

### ISerialManager
Управление последовательными портами и коммуникацией с оборудованием.

```python
class ISerialManager(Protocol):
    def connect(self, port: str, baudrate: int = 9600) -> bool:
        """Подключение к последовательному порту"""
        
    def disconnect(self) -> None:
        """Отключение от порта"""
        
    def send_command(self, command: str) -> str:
        """Отправка команды и получение ответа"""
        
    def is_connected(self) -> bool:
        """Проверка состояния подключения"""
```

### ICommandExecutor
Выполнение команд на лабораторном оборудовании.

```python
class ICommandExecutor(Protocol):
    def execute_command(self, command: Command) -> CommandResult:
        """Выполнение одиночной команды"""
        
    def execute_sequence(self, sequence: List[Command]) -> List[CommandResult]:
        """Выполнение последовательности команд"""
        
    def cancel_execution(self) -> None:
        """Отмена текущего выполнения"""
```

### ISequenceManager
Управление последовательностями операций.

```python
class ISequenceManager(Protocol):
    def load_sequence(self, sequence_id: str) -> Sequence:
        """Загрузка последовательности по ID"""
        
    def save_sequence(self, sequence: Sequence) -> bool:
        """Сохранение последовательности"""
        
    def execute_sequence(self, sequence_id: str) -> bool:
        """Выполнение последовательности"""
        
    def get_available_sequences(self) -> List[str]:
        """Получение списка доступных последовательностей"""
```

### IMonitoringManager
Мониторинг состояния системы и оборудования.

```python
class IMonitoringManager(Protocol):
    def start_monitoring(self) -> None:
        """Запуск мониторинга"""
        
    def stop_monitoring(self) -> None:
        """Остановка мониторинга"""
        
    def get_system_health(self) -> SystemHealth:
        """Получение состояния здоровья системы"""
        
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Получение метрик производительности"""
```

## Команды оборудования

### Базовые команды

| Команда | Описание | Параметры | Ответ |
|---------|----------|-----------|-------|
| `MOVE` | Перемещение механизма | `device`, `position` | `OK` или `ERROR` |
| `HOME` | Возврат в исходное положение | `device` | `OK` или `ERROR` |
| `STATUS` | Получение статуса | `device` | Статус устройства |
| `STOP` | Остановка операции | `device` | `OK` |

### Примеры использования

```python
# Перемещение механизма Multi в позицию 100
result = serial_manager.send_command("MOVE Multi 100")

# Возврат механизма RRight в исходное положение
result = serial_manager.send_command("HOME RRight")

# Получение статуса механизма Clamp
status = serial_manager.send_command("STATUS Clamp")
```

## Обработка ошибок

### Типы ошибок

- **ConnectionError**: Ошибки подключения к оборудованию
- **CommandError**: Ошибки выполнения команд
- **TimeoutError**: Таймауты операций
- **ValidationError**: Ошибки валидации параметров

### Пример обработки

```python
try:
    result = command_executor.execute_command(command)
    if result.success:
        print(f"Команда выполнена: {result.response}")
    else:
        print(f"Ошибка: {result.error_message}")
except ConnectionError as e:
    print(f"Ошибка подключения: {e}")
except TimeoutError as e:
    print(f"Таймаут операции: {e}")
```

## Конфигурация

### Настройки последовательного порта

```python
serial_config = {
    "port": "COM3",
    "baudrate": 9600,
    "timeout": 5.0,
    "parity": "N",
    "stopbits": 1,
    "bytesize": 8
}
```

### Настройки команд

```python
command_config = {
    "default_timeout": 10.0,
    "retry_attempts": 3,
    "retry_delay": 1.0,
    "validate_commands": True
}
```

## События и сигналы

### Основные события

- **connection_changed**: Изменение состояния подключения
- **command_executed**: Выполнение команды
- **sequence_completed**: Завершение последовательности
- **error_occurred**: Возникновение ошибки
- **status_updated**: Обновление статуса

### Пример подписки на события

```python
# Подписка на изменение подключения
serial_manager.connection_changed.connect(self.on_connection_changed)

# Подписка на выполнение команд
command_executor.command_executed.connect(self.on_command_executed)

# Подписка на ошибки
monitoring_manager.error_occurred.connect(self.on_error_occurred)
```

## Безопасность

### Валидация команд

Все команды проходят валидацию перед выполнением:
- Проверка синтаксиса
- Валидация параметров
- Проверка безопасности

### Логирование

Все операции логируются:
- Команды и их параметры
- Результаты выполнения
- Ошибки и исключения
- Временные метки

## Производительность

### Рекомендации

- Используйте асинхронные операции для длительных задач
- Кэшируйте часто используемые последовательности
- Мониторьте производительность через метрики
- Оптимизируйте размер команд и ответов