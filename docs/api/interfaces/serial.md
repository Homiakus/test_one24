---
title: "ISerialManager Interface"
type: "api_reference"
audiences: ["backend_dev", "frontend_dev"]
tags: ["api", "serial", "communication", "interface"]
last_updated: "2024-12-20"
sources:
  - path: "core/interfaces.py"
    lines: "L25-L95"
    permalink: "core/interfaces.py#L25-L95"
related: ["docs/api/examples/serial_manager", "docs/architecture/serial", "docs/runbooks/troubleshooting"]
---

# 🔌 ISerialManager Interface

> [!info] Навигация
> Родитель: [[docs/api/index]] • Раздел: [[docs/api/interfaces]] • См. также: [[docs/api/examples/serial_manager]]

## 📋 Обзор

`ISerialManager` - основной интерфейс для управления Serial-коммуникацией с устройствами. Обеспечивает абстракцию над последовательными портами и предоставляет единообразный API для подключения, отправки команд и получения информации о портах.

## 🔧 Методы интерфейса

### `connect(port, baudrate, timeout, **kwargs) -> bool`

Устанавливает соединение с указанным последовательным портом.

#### Параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|---------------|----------|
| `port` | `str` | - | Имя порта (например, 'COM4' или '/dev/ttyUSB0') |
| `baudrate` | `int` | `115200` | Скорость передачи данных в бодах |
| `timeout` | `float` | `1.0` | Таймаут чтения в секундах |
| `**kwargs` | `Any` | - | Дополнительные параметры подключения |

#### Возвращаемое значение

- `True` - подключение успешно установлено
- `False` - подключение не удалось установить

#### Исключения

- `SerialException` - при ошибке подключения к порту

#### Пример использования

```python
from core.interfaces import ISerialManager

class SerialManager(ISerialManager):
    def connect(self, port: str, baudrate: int = 115200, 
                timeout: float = 1.0, **kwargs: Any) -> bool:
        try:
            import serial
            self._connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                **kwargs
            )
            return True
        except serial.SerialException as e:
            logger.error(f"Ошибка подключения к {port}: {e}")
            return False
```

### `disconnect() -> None`

Отключает активное соединение и освобождает ресурсы.

#### Параметры

Нет

#### Возвращаемое значение

`None`

#### Исключения

Нет

#### Пример использования

```python
def disconnect(self) -> None:
    if hasattr(self, '_connection') and self._connection:
        try:
            self._connection.close()
            self._connection = None
            logger.info("Соединение закрыто")
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединения: {e}")
```

### `send_command(command) -> bool`

Отправляет команду на подключенное устройство.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `command` | `str` | Команда для отправки |

#### Возвращаемое значение

- `True` - команда отправлена успешно
- `False` - команда не отправлена

#### Исключения

- `SerialException` - при ошибке отправки команды

#### Пример использования

```python
def send_command(self, command: str) -> bool:
    if not self.is_connected():
        logger.error("Нет активного соединения")
        return False
    
    try:
        command_bytes = command.encode('utf-8')
        bytes_written = self._connection.write(command_bytes)
        self._connection.flush()
        
        if bytes_written == len(command_bytes):
            logger.debug(f"Команда отправлена: {command}")
            return True
        else:
            logger.error(f"Неполная отправка команды: {bytes_written}/{len(command_bytes)}")
            return False
    except serial.SerialException as e:
        logger.error(f"Ошибка отправки команды: {e}")
        return False
```

### `is_connected() -> bool`

Проверяет состояние подключения.

#### Параметры

Нет

#### Возвращаемое значение

- `True` - подключение активно
- `False` - подключение неактивно

#### Исключения

Нет

#### Пример использования

```python
def is_connected(self) -> bool:
    if not hasattr(self, '_connection') or not self._connection:
        return False
    
    try:
        return self._connection.is_open
    except Exception:
        return False
```

### `get_available_ports() -> List[str]`

Получает список доступных последовательных портов.

#### Параметры

Нет

#### Возвращаемое значение

`List[str]` - список имен доступных последовательных портов

#### Исключения

Нет

#### Пример использования

```python
def get_available_ports(self) -> List[str]:
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    except Exception as e:
        logger.error(f"Ошибка получения списка портов: {e}")
        return []
```

### `get_port_info() -> Dict[str, Any]`

Получает информацию о текущем порте.

#### Параметры

Нет

#### Возвращаемое значение

`Dict[str, Any]` - словарь с информацией о порте

#### Исключения

Нет

#### Пример использования

```python
def get_port_info(self) -> Dict[str, Any]:
    if not self.is_connected():
        return {}
    
    try:
        return {
            'port': self._connection.port,
            'baudrate': self._connection.baudrate,
            'timeout': self._connection.timeout,
            'bytesize': self._connection.bytesize,
            'parity': self._connection.parity,
            'stopbits': self._connection.stopbits,
            'is_open': self._connection.is_open
        }
    except Exception as e:
        logger.error(f"Ошибка получения информации о порте: {e}")
        return {}
```

## 🚨 Обработка ошибок

### Типичные ошибки

1. **SerialException** - общая ошибка Serial-операций
2. **PortNotOpenError** - попытка операции с закрытым портом
3. **SerialTimeoutException** - превышение таймаута
4. **SerialWriteTimeoutException** - превышение таймаута записи

### Стратегии обработки

```python
def safe_serial_operation(self, operation: Callable, *args, **kwargs):
    """Безопасное выполнение Serial-операций с повторными попытками"""
    max_retries = 3
    retry_delay = 0.1
    
    for attempt in range(max_retries):
        try:
            return operation(*args, **kwargs)
        except serial.SerialTimeoutException:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            raise
        except serial.SerialException as e:
            logger.error(f"Критическая ошибка Serial: {e}")
            raise
```

## 🔗 Связанные интерфейсы

- [[docs/api/interfaces/command|ICommandExecutor]] - для выполнения команд через Serial
- [[docs/api/interfaces/sequence|ISequenceManager]] - для управления последовательностями команд
- [[docs/api/interfaces/signal|ISignalManager]] - для обработки сигналов от устройств

## 📚 Примеры использования

См. [[docs/api/examples/serial_manager]] для полных примеров использования.

## 🧪 Тестирование

```python
import pytest
from unittest.mock import Mock, patch
from core.interfaces import ISerialManager

class TestSerialManager:
    @patch('serial.Serial')
    def test_connect_success(self, mock_serial):
        manager = SerialManager()
        mock_serial.return_value.is_open = True
        
        result = manager.connect('COM4')
        
        assert result is True
        mock_serial.assert_called_once()
```

## 📝 Примечания реализации

- Все методы должны быть потокобезопасными
- Рекомендуется использовать контекстные менеджеры для автоматического закрытия соединений
- При ошибках подключения следует логировать детальную информацию для диагностики
- Методы должны корректно обрабатывать случаи отсутствия соединения
