---
title: "Serial Manager - Управление последовательными портами"
type: "module"
audiences: ["backend_dev", "architect"]
tags: ["doc", "lab-equipment-system", "core", "serial"]
status: "approved"
last_updated: "2024-12-19"
sources:
  - path: "core/serial_manager.py"
    lines: "L1-L100"
    permalink: "https://github.com/lab-equipment-system/blob/main/core/serial_manager.py#L1-L100"
related: ["docs/modules/core/interfaces", "docs/api/serial"]
---

> [!info] Навигация
> Родитель: [[docs/modules/core]] • Раздел: [[_moc/Architecture]] • См. также: [[docs/api/serial]]

# Serial Manager - Управление последовательными портами

## Обзор

Serial Manager - это компонент, отвечающий за управление последовательными портами и коммуникацию с лабораторным оборудованием. Обеспечивает надежную передачу команд и получение ответов от устройств.

## Основные возможности

- **Управление подключениями**: Подключение/отключение к последовательным портам
- **Отправка команд**: Передача команд на оборудование
- **Получение ответов**: Чтение ответов от устройств
- **Обработка ошибок**: Обработка ошибок связи
- **Мониторинг состояния**: Отслеживание состояния подключения
- **Таймауты**: Управление таймаутами операций

## Архитектура

```python
class SerialManager:
    def __init__(self, config: SerialConfig):
        self.config = config
        self.connection = None
        self.is_connected = False
        
    def connect(self, port: str, baudrate: int = 9600) -> bool:
        """Подключение к последовательному порту"""
        
    def disconnect(self) -> None:
        """Отключение от порта"""
        
    def send_command(self, command: str) -> str:
        """Отправка команды и получение ответа"""
        
    def is_connected(self) -> bool:
        """Проверка состояния подключения"""
```

## Конфигурация

### SerialConfig

```python
@dataclass
class SerialConfig:
    port: str
    baudrate: int = 9600
    timeout: float = 5.0
    parity: str = "N"
    stopbits: int = 1
    bytesize: int = 8
    retry_attempts: int = 3
    retry_delay: float = 1.0
```

### Пример конфигурации

```python
config = SerialConfig(
    port="COM3",
    baudrate=9600,
    timeout=5.0,
    retry_attempts=3
)

serial_manager = SerialManager(config)
```

## Основные методы

### Подключение

```python
# Подключение к порту
success = serial_manager.connect("COM3", 9600)
if success:
    print("Подключение установлено")
else:
    print("Ошибка подключения")
```

### Отправка команд

```python
# Отправка простой команды
response = serial_manager.send_command("STATUS")
print(f"Ответ: {response}")

# Отправка команды с параметрами
response = serial_manager.send_command("MOVE Multi 100")
print(f"Ответ: {response}")
```

### Проверка состояния

```python
# Проверка подключения
if serial_manager.is_connected():
    print("Подключение активно")
else:
    print("Нет подключения")
```

## Обработка ошибок

### Типы ошибок

- **ConnectionError**: Ошибки подключения
- **TimeoutError**: Таймауты операций
- **SerialException**: Ошибки последовательного порта
- **CommandError**: Ошибки выполнения команд

### Пример обработки

```python
try:
    response = serial_manager.send_command("MOVE Multi 100")
    if response.startswith("OK"):
        print("Команда выполнена успешно")
    else:
        print(f"Ошибка: {response}")
except ConnectionError as e:
    print(f"Ошибка подключения: {e}")
except TimeoutError as e:
    print(f"Таймаут операции: {e}")
except SerialException as e:
    print(f"Ошибка последовательного порта: {e}")
```

## События

### Основные события

- **connection_changed**: Изменение состояния подключения
- **command_sent**: Отправка команды
- **response_received**: Получение ответа
- **error_occurred**: Возникновение ошибки

### Пример подписки

```python
# Подписка на изменение подключения
serial_manager.connection_changed.connect(self.on_connection_changed)

# Подписка на ошибки
serial_manager.error_occurred.connect(self.on_error_occurred)

def on_connection_changed(self, connected: bool):
    if connected:
        print("Подключение установлено")
    else:
        print("Подключение потеряно")

def on_error_occurred(self, error: Exception):
    print(f"Ошибка: {error}")
```

## Протокол команд

### Формат команд

```
<COMMAND> <DEVICE> [PARAMETERS]
```

### Примеры команд

| Команда | Описание | Пример |
|---------|----------|--------|
| `STATUS` | Получение статуса | `STATUS Multi` |
| `MOVE` | Перемещение | `MOVE Multi 100` |
| `HOME` | Возврат в исходное положение | `HOME RRight` |
| `STOP` | Остановка | `STOP Clamp` |

### Формат ответов

- **Успех**: `OK` или `OK <data>`
- **Ошибка**: `ERROR <message>`
- **Таймаут**: Пустой ответ

## Производительность

### Рекомендации

- Используйте подходящие таймауты
- Обрабатывайте ошибки связи
- Мониторьте состояние подключения
- Используйте retry механизм для критичных операций

### Метрики

- Время отправки команды: < 100ms
- Время получения ответа: < 5s
- Надежность связи: > 99%

## Тестирование

### Unit тесты

```python
def test_serial_manager_connection():
    config = SerialConfig(port="COM3")
    manager = SerialManager(config)
    
    # Тест подключения
    success = manager.connect("COM3")
    assert success == True
    assert manager.is_connected() == True

def test_serial_manager_command():
    config = SerialConfig(port="COM3")
    manager = SerialManager(config)
    manager.connect("COM3")
    
    # Тест отправки команды
    response = manager.send_command("STATUS")
    assert response is not None
```

### Mock тесты

```python
def test_serial_manager_mock():
    mock_serial = Mock()
    mock_serial.read.return_value = b"OK\n"
    
    with patch('serial.Serial', return_value=mock_serial):
        manager = SerialManager(SerialConfig(port="COM3"))
        manager.connect("COM3")
        
        response = manager.send_command("STATUS")
        assert response == "OK"
```

## Интеграция с другими модулями

### CommandExecutor
```python
class CommandExecutor:
    def __init__(self, serial_manager: ISerialManager):
        self.serial_manager = serial_manager
    
    def execute_command(self, command: Command) -> CommandResult:
        response = self.serial_manager.send_command(command.to_string())
        return CommandResult.from_response(response)
```

### SequenceManager
```python
class SequenceManager:
    def __init__(self, serial_manager: ISerialManager):
        self.serial_manager = serial_manager
    
    def execute_sequence(self, sequence: List[Command]):
        for command in sequence:
            self.serial_manager.send_command(command.to_string())
```

## Будущие улучшения

- Поддержка множественных портов
- Асинхронные операции
- Буферизация команд
- Автоматическое переподключение
- Метрики производительности