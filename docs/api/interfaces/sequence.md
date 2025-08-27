---
title: "ISequenceManager Interface"
type: "api_reference"
audiences: ["backend_dev", "frontend_dev"]
tags: ["api", "sequence", "management", "interface"]
last_updated: "2024-12-20"
sources:
  - path: "core/interfaces.py"
    lines: "L152-L200"
    permalink: "core/interfaces.py#L152-L200"
related: ["docs/api/examples/sequence_manager", "docs/architecture/sequences", "docs/runbooks/troubleshooting"]
---

# 🔄 ISequenceManager Interface

> [!info] Навигация
> Родитель: [[docs/api/index]] • Раздел: [[docs/api/interfaces]] • См. также: [[docs/api/examples/sequence_manager]]

## 📋 Обзор

`ISequenceManager` - интерфейс для управления последовательностями команд. Позволяет создавать, выполнять и управлять группами команд, которые должны выполняться в определенном порядке или с определенными условиями.

## 🔧 Методы интерфейса

### `execute_sequence(sequence_name) -> bool`

Выполняет последовательность команд по имени.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `sequence_name` | `str` | Имя последовательности для выполнения |

#### Возвращаемое значение

- `True` - последовательность выполнена успешно
- `False` - последовательность не выполнена

#### Исключения

- `SequenceNotFoundError` - последовательность не найдена
- `SequenceExecutionError` - ошибка выполнения последовательности

#### Пример использования

```python
from core.interfaces import ISequenceManager

class SequenceManager(ISequenceManager):
    def execute_sequence(self, sequence_name: str) -> bool:
        try:
            # Получение последовательности
            sequence = self._get_sequence(sequence_name)
            if not sequence:
                logger.error(f"Последовательность не найдена: {sequence_name}")
                return False
            
            # Проверка зависимостей
            if not self._check_dependencies(sequence):
                logger.error(f"Зависимости не выполнены для: {sequence_name}")
                return False
            
            # Выполнение команд последовательности
            success_count = 0
            total_commands = len(sequence['commands'])
            
            for i, command in enumerate(sequence['commands']):
                try:
                    logger.info(f"Выполнение команды {i+1}/{total_commands}: {command}")
                    
                    if self._execute_command(command):
                        success_count += 1
                    else:
                        # Обработка ошибки в зависимости от настроек
                        if sequence.get('stop_on_error', True):
                            logger.error(f"Остановка последовательности из-за ошибки в команде: {command}")
                            break
                        else:
                            logger.warning(f"Продолжение последовательности после ошибки в команде: {command}")
                            
                except Exception as e:
                    logger.error(f"Критическая ошибка в команде {command}: {e}")
                    if sequence.get('stop_on_error', True):
                        break
            
            # Логирование результата
            success_rate = (success_count / total_commands) * 100
            logger.info(f"Последовательность {sequence_name} выполнена: {success_count}/{total_commands} ({success_rate:.1f}%)")
            
            return success_count == total_commands
            
        except Exception as e:
            logger.error(f"Ошибка выполнения последовательности {sequence_name}: {e}")
            return False
```

### `add_sequence(name, commands) -> bool`

Добавляет новую последовательность команд.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `name` | `str` | Имя последовательности |
| `commands` | `List[str]` | Список команд для выполнения |

#### Возвращаемое значение

- `True` - последовательность добавлена успешно
- `False` - последовательность не добавлена

#### Исключения

- `SequenceValidationError` - ошибка валидации последовательности
- `DuplicateSequenceError` - последовательность с таким именем уже существует

#### Пример использования

```python
def add_sequence(self, name: str, commands: List[str]) -> bool:
    try:
        # Валидация имени
        if not self._validate_sequence_name(name):
            logger.error(f"Некорректное имя последовательности: {name}")
            return False
        
        # Проверка на дублирование
        if self._sequence_exists(name):
            logger.error(f"Последовательность с именем {name} уже существует")
            return False
        
        # Валидация команд
        if not self._validate_commands(commands):
            logger.error(f"Некорректные команды в последовательности {name}")
            return False
        
        # Создание последовательности
        sequence = {
            'name': name,
            'commands': commands.copy(),
            'created_at': datetime.now().isoformat(),
            'modified_at': datetime.now().isoformat(),
            'version': 1,
            'enabled': True,
            'stop_on_error': True,
            'timeout': 300.0,  # 5 минут по умолчанию
            'retry_count': 0,
            'retry_delay': 1.0
        }
        
        # Сохранение последовательности
        self._sequences[name] = sequence
        self._save_sequences()
        
        logger.info(f"Последовательность {name} добавлена с {len(commands)} командами")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка добавления последовательности {name}: {e}")
        return False

def _validate_sequence_name(self, name: str) -> bool:
    """Валидация имени последовательности"""
    if not name or not isinstance(name, str):
        return False
    
    # Проверка длины
    if len(name) < 1 or len(name) > 100:
        return False
    
    # Проверка символов
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False
    
    return True

def _validate_commands(self, commands: List[str]) -> bool:
    """Валидация команд в последовательности"""
    if not commands or not isinstance(commands, list):
        return False
    
    if len(commands) == 0:
        return False
    
    if len(commands) > 1000:  # Максимум 1000 команд
        return False
    
    # Проверка каждой команды
    for command in commands:
        if not isinstance(command, str) or len(command.strip()) == 0:
            return False
    
    return True
```

### `remove_sequence(name) -> bool`

Удаляет последовательность команд по имени.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `name` | `str` | Имя последовательности для удаления |

#### Возвращаемое значение

- `True` - последовательность удалена успешно
- `False` - последовательность не удалена

#### Исключения

- `SequenceNotFoundError` - последовательность не найдена
- `SequenceInUseError` - последовательность используется в данный момент

#### Пример использования

```python
def remove_sequence(self, name: str) -> bool:
    try:
        # Проверка существования
        if not self._sequence_exists(name):
            logger.error(f"Последовательность {name} не найдена")
            return False
        
        # Проверка использования
        if self._is_sequence_running(name):
            logger.error(f"Нельзя удалить выполняющуюся последовательность: {name}")
            return False
        
        # Удаление последовательности
        removed_sequence = self._sequences.pop(name)
        self._save_sequences()
        
        logger.info(f"Последовательность {name} удалена")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка удаления последовательности {name}: {e}")
        return False

def _is_sequence_running(self, name: str) -> bool:
    """Проверка, выполняется ли последовательность"""
    return name in self._running_sequences
```

## 🚨 Обработка ошибок

### Типичные ошибки

1. **SequenceNotFoundError** - последовательность не найдена
2. **SequenceExecutionError** - ошибка выполнения последовательности
3. **SequenceValidationError** - ошибка валидации последовательности
4. **DuplicateSequenceError** - дублирование имени последовательности
5. **SequenceInUseError** - попытка удаления используемой последовательности

### Стратегии обработки

```python
class SequenceNotFoundError(Exception):
    """Последовательность не найдена"""
    pass

class SequenceExecutionError(Exception):
    """Ошибка выполнения последовательности"""
    pass

class SequenceValidationError(Exception):
    """Ошибка валидации последовательности"""
    pass

def safe_sequence_execution(self, sequence_name: str) -> bool:
    """Безопасное выполнение последовательности с обработкой ошибок"""
    try:
        # Проверка существования
        if not self._sequence_exists(sequence_name):
            raise SequenceNotFoundError(f"Последовательность {sequence_name} не найдена")
        
        # Проверка состояния
        if self._is_sequence_running(sequence_name):
            raise SequenceExecutionError(f"Последовательность {sequence_name} уже выполняется")
        
        # Выполнение с таймаутом
        return self._execute_with_timeout(sequence_name)
        
    except SequenceNotFoundError as e:
        logger.error(f"Ошибка поиска: {e}")
        return False
    except SequenceExecutionError as e:
        logger.error(f"Ошибка выполнения: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return False

def _execute_with_timeout(self, sequence_name: str) -> bool:
    """Выполнение последовательности с таймаутом"""
    import threading
    import time
    
    sequence = self._sequences[sequence_name]
    timeout = sequence.get('timeout', 300.0)
    
    # Создание события для остановки
    stop_event = threading.Event()
    
    def execution_thread():
        try:
            self._running_sequences.add(sequence_name)
            result = self._execute_sequence_internal(sequence_name, stop_event)
            return result
        finally:
            self._running_sequences.discard(sequence_name)
    
    # Запуск в отдельном потоке
    thread = threading.Thread(target=execution_thread)
    thread.daemon = True
    thread.start()
    
    # Ожидание завершения или таймаута
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        stop_event.set()
        thread.join(timeout=5.0)  # Дополнительное время для корректного завершения
        logger.error(f"Превышен таймаут выполнения последовательности: {sequence_name}")
        return False
    
    return True
```

## 🔗 Связанные интерфейсы

- [[docs/api/interfaces/command|ICommandExecutor]] - для выполнения отдельных команд
- [[docs/api/interfaces/serial|ISerialManager]] - для отправки команд через Serial
- [[docs/api/interfaces/tag|ITagManager]] - для управления тегами команд

## 📚 Примеры использования

См. [[docs/api/examples/sequence_manager]] для полных примеров использования.

## 🧪 Тестирование

```python
import pytest
from unittest.mock import Mock, patch
from core.interfaces import ISequenceManager

class TestSequenceManager:
    def test_add_sequence_success(self):
        manager = SequenceManager()
        
        result = manager.add_sequence("test_seq", ["GET STATUS", "SET MODE 1"])
        
        assert result is True
        assert "test_seq" in manager._sequences
    
    def test_execute_sequence_success(self):
        manager = SequenceManager()
        manager.add_sequence("test_seq", ["GET STATUS"])
        
        result = manager.execute_sequence("test_seq")
        
        assert result is True
    
    def test_remove_sequence_success(self):
        manager = SequenceManager()
        manager.add_sequence("test_seq", ["GET STATUS"])
        
        result = manager.remove_sequence("test_seq")
        
        assert result is True
        assert "test_seq" not in manager._sequences
```

## 📝 Примечания реализации

- Все методы должны быть потокобезопасными
- Рекомендуется использовать асинхронное выполнение для длительных последовательностей
- Последовательности должны поддерживать версионирование для отслеживания изменений
- Необходимо реализовать механизм отмены выполнения последовательности
- Логирование должно включать детальную информацию о каждом этапе выполнения
- Рекомендуется кэширование часто используемых последовательностей
