---
title: "ICommandExecutor Interface"
type: "api_reference"
audiences: ["backend_dev", "frontend_dev"]
tags: ["api", "command", "execution", "interface"]
last_updated: "2024-12-20"
sources:
  - path: "core/interfaces.py"
    lines: "L97-L150"
    permalink: "core/interfaces.py#L97-L150"
related: ["docs/api/examples/command_executor", "docs/architecture/commands", "docs/runbooks/troubleshooting"]
---

# ⚡ ICommandExecutor Interface

> [!info] Навигация
> Родитель: [[docs/api/index]] • Раздел: [[docs/api/interfaces]] • См. также: [[docs/api/examples/command_executor]]

## 📋 Обзор

`ICommandExecutor` - интерфейс для выполнения команд и управления их жизненным циклом. Обеспечивает валидацию, выполнение и отслеживание команд с поддержкой различных типов команд и параметров.

## 🔧 Методы интерфейса

### `execute(command, **kwargs) -> bool`

Выполняет команду с указанными параметрами.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `command` | `str` | Команда для выполнения |
| `**kwargs` | `Any` | Дополнительные параметры команды |

#### Возвращаемое значение

- `True` - команда выполнена успешно
- `False` - команда не выполнена

#### Исключения

- `CommandExecutionError` - при ошибке выполнения команды
- `CommandValidationError` - при ошибке валидации команды

#### Пример использования

```python
from core.interfaces import ICommandExecutor

class CommandExecutor(ICommandExecutor):
    def execute(self, command: str, **kwargs: Any) -> bool:
        try:
            # Валидация команды
            if not self.validate_command(command):
                logger.error(f"Команда не прошла валидацию: {command}")
                return False
            
            # Парсинг команды
            parsed_command = self._parse_command(command)
            
            # Выполнение команды
            result = self._execute_parsed_command(parsed_command, **kwargs)
            
            # Логирование результата
            self._log_execution(command, result, **kwargs)
            
            return result
        except Exception as e:
            logger.error(f"Ошибка выполнения команды {command}: {e}")
            return False
```

### `validate_command(command) -> bool`

Проверяет корректность команды перед выполнением.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `command` | `str` | Команда для валидации |

#### Возвращаемое значение

- `True` - команда корректна
- `False` - команда некорректна

#### Исключения

Нет

#### Пример использования

```python
def validate_command(self, command: str) -> bool:
    if not command or not isinstance(command, str):
        return False
    
    # Проверка длины команды
    if len(command) > 1024:
        logger.warning(f"Команда слишком длинная: {len(command)} символов")
        return False
    
    # Проверка на запрещенные символы
    forbidden_chars = ['<', '>', '"', "'", '&']
    if any(char in command for char in forbidden_chars):
        logger.warning(f"Команда содержит запрещенные символы: {command}")
        return False
    
    # Проверка синтаксиса команды
    if not self._check_command_syntax(command):
        return False
    
    return True

def _check_command_syntax(self, command: str) -> bool:
    """Проверка синтаксиса команды"""
    # Базовая проверка формата
    if not command.startswith(('GET', 'SET', 'CMD', 'QUERY')):
        return False
    
    # Проверка структуры команды
    parts = command.split()
    if len(parts) < 2:
        return False
    
    return True
```

### `get_execution_history() -> List[Dict[str, Any]]`

Получает историю выполнения команд.

#### Параметры

Нет

#### Возвращаемое значение

`List[Dict[str, Any]]` - список записей о выполненных командах

#### Исключения

Нет

#### Пример использования

```python
def get_execution_history(self) -> List[Dict[str, Any]]:
    """Получение истории выполнения команд"""
    try:
        return sorted(
            self._execution_history,
            key=lambda x: x['timestamp'],
            reverse=True
        )
    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        return []

def _log_execution(self, command: str, result: bool, **kwargs):
    """Логирование выполнения команды"""
    execution_record = {
        'command': command,
        'result': result,
        'timestamp': datetime.now().isoformat(),
        'parameters': kwargs,
        'execution_time': kwargs.get('execution_time', 0.0)
    }
    
    self._execution_history.append(execution_record)
    
    # Ограничение размера истории
    if len(self._execution_history) > 1000:
        self._execution_history = self._execution_history[-1000:]
```

## 🚨 Обработка ошибок

### Типичные ошибки

1. **CommandExecutionError** - ошибка выполнения команды
2. **CommandValidationError** - ошибка валидации команды
3. **CommandTimeoutError** - превышение таймаута выполнения
4. **CommandNotSupportedError** - неподдерживаемая команда

### Стратегии обработки

```python
class CommandExecutionError(Exception):
    """Ошибка выполнения команды"""
    pass

class CommandValidationError(Exception):
    """Ошибка валидации команды"""
    pass

def safe_command_execution(self, command: str, **kwargs) -> bool:
    """Безопасное выполнение команды с обработкой ошибок"""
    try:
        # Валидация
        if not self.validate_command(command):
            raise CommandValidationError(f"Команда не прошла валидацию: {command}")
        
        # Выполнение с таймаутом
        result = self._execute_with_timeout(command, **kwargs)
        
        return result
    except CommandValidationError as e:
        logger.error(f"Ошибка валидации: {e}")
        return False
    except CommandExecutionError as e:
        logger.error(f"Ошибка выполнения: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return False

def _execute_with_timeout(self, command: str, timeout: float = 30.0, **kwargs) -> bool:
    """Выполнение команды с таймаутом"""
    import signal
    
    def timeout_handler(signum, frame):
        raise CommandTimeoutError(f"Превышен таймаут выполнения команды: {command}")
    
    # Установка таймаута
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(timeout))
    
    try:
        result = self._execute_internal(command, **kwargs)
        return result
    finally:
        # Сброс таймаута
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
```

## 🔗 Связанные интерфейсы

- [[docs/api/interfaces/serial|ISerialManager]] - для отправки команд через Serial
- [[docs/api/interfaces/sequence|ISequenceManager]] - для выполнения последовательностей команд
- [[docs/api/interfaces/tag|ITagManager]] - для управления тегами команд

## 📚 Примеры использования

См. [[docs/api/examples/command_executor]] для полных примеров использования.

## 🧪 Тестирование

```python
import pytest
from unittest.mock import Mock, patch
from core.interfaces import ICommandExecutor

class TestCommandExecutor:
    def test_execute_success(self):
        executor = CommandExecutor()
        
        result = executor.execute("GET STATUS")
        
        assert result is True
    
    def test_validate_command_invalid(self):
        executor = CommandExecutor()
        
        result = executor.validate_command("")
        
        assert result is False
    
    def test_execution_history(self):
        executor = CommandExecutor()
        executor.execute("GET STATUS")
        executor.execute("SET MODE 1")
        
        history = executor.get_execution_history()
        
        assert len(history) == 2
        assert history[0]['command'] == "SET MODE 1"
        assert history[1]['command'] == "GET STATUS"
```

## 📝 Примечания реализации

- Все методы должны быть потокобезопасными
- Рекомендуется использовать асинхронное выполнение для длительных операций
- История выполнения должна иметь ограничение по размеру для предотвращения утечек памяти
- Валидация команд должна быть расширяемой для поддержки новых типов команд
- Логирование должно включать контекстную информацию для диагностики
