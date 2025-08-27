---
title: "ISignalManager Interface"
type: "api_reference"
audiences: ["backend_dev", "frontend_dev"]
tags: ["api", "signal", "management", "interface"]
last_updated: "2024-12-20"
sources:
  - path: "core/interfaces.py"
    lines: "L352-L420"
    permalink: "core/interfaces.py#L352-L420"
related: ["docs/api/examples/signal_manager", "docs/architecture/signals", "docs/runbooks/troubleshooting"]
---

# 📡 ISignalManager Interface

> [!info] Навигация
> Родитель: [[docs/api/index]] • Раздел: [[docs/api/interfaces]] • См. также: [[docs/api/examples/signal_manager]]

## 📋 Обзор

`ISignalManager` - интерфейс для управления сигналами и событиями в системе. Обеспечивает регистрацию, обработку и распространение сигналов между различными компонентами приложения, поддерживая паттерн Observer и event-driven архитектуру.

## 🔧 Методы интерфейса

### `register_signal(signal_info) -> bool`

Регистрирует новый сигнал в системе.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `signal_info` | `SignalInfo` | Информация о регистрируемом сигнале |

#### Возвращаемое значение

- `True` - сигнал зарегистрирован успешно
- `False` - сигнал не зарегистрирован

#### Исключения

- `SignalValidationError` - ошибка валидации сигнала
- `DuplicateSignalError` - сигнал с таким именем уже существует

#### Пример использования

```python
from core.interfaces import ISignalManager, SignalInfo
from core.signal_types import SignalType

class SignalManager(ISignalManager):
    def register_signal(self, signal_info: SignalInfo) -> bool:
        try:
            # Валидация информации о сигнале
            if not self._validate_signal_info(signal_info):
                logger.error(f"Некорректная информация о сигнале: {signal_info}")
                return False
            
            signal_name = signal_info.name
            
            # Проверка на дублирование
            if self._signal_exists(signal_name):
                logger.error(f"Сигнал с именем {signal_name} уже существует")
                return False
            
            # Создание сигнала
            signal = {
                'name': signal_name,
                'signal_type': signal_info.signal_type,
                'description': signal_info.description,
                'created_at': datetime.now().isoformat(),
                'modified_at': datetime.now().isoformat(),
                'version': 1,
                'enabled': True,
                'handlers': [],
                'metadata': signal_info.metadata.copy() if signal_info.metadata else {},
                'emission_count': 0,
                'last_emitted': None,
                'subscribers': set(),
                'priority': signal_info.priority or 'normal'
            }
            
            # Сохранение сигнала
            self._signals[signal_name] = signal
            self._save_signals()
            
            logger.info(f"Сигнал {signal_name} зарегистрирован успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка регистрации сигнала {signal_info.name}: {e}")
            return False

def _validate_signal_info(self, signal_info: SignalInfo) -> bool:
    """Валидация информации о сигнале"""
    if not signal_info or not isinstance(signal_info, SignalInfo):
        return False
    
    # Проверка имени
    if not signal_info.name or not isinstance(signal_info.name, str):
        return False
    
    if len(signal_info.name) < 1 or len(signal_info.name) > 100:
        return False
    
    # Проверка символов имени
    import re
    if not re.match(r'^[a-zA-Z0-9_.-]+$', signal_info.name):
        return False
    
    # Проверка описания
    if signal_info.description and len(signal_info.description) > 500:
        return False
    
    # Проверка типа сигнала
    if signal_info.signal_type not in SignalType:
        return False
    
    # Проверка приоритета
    if signal_info.priority and signal_info.priority not in ['low', 'normal', 'high', 'critical']:
        return False
    
    return True
```

### `subscribe_to_signal(signal_name, handler) -> bool`

Подписывает обработчик на указанный сигнал.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `signal_name` | `str` | Имя сигнала для подписки |
| `handler` | `Callable` | Функция-обработчик сигнала |

#### Возвращаемое значение

- `True` - подписка выполнена успешно
- `False` - подписка не выполнена

#### Исключения

- `SignalNotFoundError` - сигнал не найден
- `HandlerValidationError` - ошибка валидации обработчика

#### Пример использования

```python
def subscribe_to_signal(self, signal_name: str, handler: Callable) -> bool:
    try:
        # Проверка существования сигнала
        if not self._signal_exists(signal_name):
            logger.error(f"Сигнал {signal_name} не найден")
            return False
        
        # Валидация обработчика
        if not self._validate_handler(handler):
            logger.error(f"Некорректный обработчик для сигнала {signal_name}")
            return False
        
        # Получение сигнала
        signal = self._signals[signal_name]
        
        # Проверка на дублирование подписки
        if handler in signal['handlers']:
            logger.warning(f"Обработчик уже подписан на сигнал {signal_name}")
            return True
        
        # Добавление обработчика
        signal['handlers'].append(handler)
        signal['subscribers'].add(id(handler))
        
        # Обновление метаданных
        signal['modified_at'] = datetime.now().isoformat()
        signal['version'] += 1
        
        # Сохранение изменений
        self._save_signals()
        
        logger.info(f"Обработчик подписан на сигнал {signal_name}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка подписки на сигнал {signal_name}: {e}")
        return False

def _validate_handler(self, handler: Callable) -> bool:
    """Валидация обработчика сигнала"""
    if not callable(handler):
        return False
    
    # Проверка сигнатуры обработчика
    import inspect
    
    try:
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())
        
        # Обработчик должен принимать минимум один параметр (сигнал)
        if len(params) < 1:
            return False
        
        # Первый параметр должен быть сигналом
        first_param = params[0]
        if first_param.annotation != inspect.Parameter.empty:
            # Проверка аннотации типа
            if not self._is_valid_signal_type(first_param.annotation):
                return False
        
        return True
        
    except Exception:
        # Если не удается проверить сигнатуру, считаем валидным
        return True

def _is_valid_signal_type(self, type_annotation) -> bool:
    """Проверка валидности типа сигнала"""
    try:
        from core.signal_types import SignalValue
        return type_annotation == SignalValue or issubclass(type_annotation, SignalValue)
    except Exception:
        return False
```

### `emit_signal(signal_name, data=None) -> bool`

Генерирует указанный сигнал с данными.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `signal_name` | `str` | Имя генерируемого сигнала |
| `data` | `Any` | Данные для передачи с сигналом |

#### Возвращаемое значение

- `True` - сигнал сгенерирован успешно
- `False` - сигнал не сгенерирован

#### Исключения

- `SignalNotFoundError` - сигнал не найден
- `SignalEmissionError` - ошибка генерации сигнала

#### Пример использования

```python
def emit_signal(self, signal_name: str, data: Any = None) -> bool:
    try:
        # Проверка существования сигнала
        if not self._signal_exists(signal_name):
            logger.error(f"Сигнал {signal_name} не найден")
            return False
        
        # Получение сигнала
        signal = self._signals[signal_name]
        
        # Проверка активности сигнала
        if not signal['enabled']:
            logger.warning(f"Сигнал {signal_name} отключен")
            return False
        
        # Создание объекта сигнала
        from core.signal_types import SignalValue
        signal_value = SignalValue(
            name=signal_name,
            data=data,
            timestamp=datetime.now().isoformat(),
            source=self._get_current_source(),
            metadata=signal.get('metadata', {})
        )
        
        # Обновление статистики
        signal['emission_count'] += 1
        signal['last_emitted'] = datetime.now().isoformat()
        
        # Вызов обработчиков
        success_count = 0
        total_handlers = len(signal['handlers'])
        
        for handler in signal['handlers']:
            try:
                # Вызов обработчика
                result = handler(signal_value)
                
                # Проверка результата
                if result is not False:  # False означает ошибку обработки
                    success_count += 1
                else:
                    logger.warning(f"Обработчик {handler.__name__} вернул ошибку для сигнала {signal_name}")
                    
            except Exception as e:
                logger.error(f"Ошибка в обработчике {handler.__name__} для сигнала {signal_name}: {e}")
                # Продолжаем выполнение других обработчиков
        
        # Логирование результата
        if total_handlers > 0:
            success_rate = (success_count / total_handlers) * 100
            logger.debug(f"Сигнал {signal_name} обработан: {success_count}/{total_handlers} ({success_rate:.1f}%)")
        
        # Сохранение изменений
        self._save_signals()
        
        logger.info(f"Сигнал {signal_name} сгенерирован успешно")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка генерации сигнала {signal_name}: {e}")
        return False

def _get_current_source(self) -> str:
    """Получение текущего источника сигнала"""
    try:
        import inspect
        frame = inspect.currentframe()
        
        # Поиск вызывающего модуля
        while frame:
            module_name = frame.f_globals.get('__name__', 'unknown')
            if module_name != 'core.signal_manager':
                return module_name
            frame = frame.f_back
        
        return 'unknown'
    except Exception:
        return 'unknown'
```

### `unsubscribe_from_signal(signal_name, handler) -> bool`

Отписывает обработчик от указанного сигнала.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `signal_name` | `str` | Имя сигнала для отписки |
| `handler` | `Callable` | Функция-обработчик для отписки |

#### Возвращаемое значение

- `True` - отписка выполнена успешно
- `False` - отписка не выполнена

#### Исключения

- `SignalNotFoundError` - сигнал не найден
- `HandlerNotFoundError` - обработчик не найден

#### Пример использования

```python
def unsubscribe_from_signal(self, signal_name: str, handler: Callable) -> bool:
    try:
        # Проверка существования сигнала
        if not self._signal_exists(signal_name):
            logger.error(f"Сигнал {signal_name} не найден")
            return False
        
        # Получение сигнала
        signal = self._signals[signal_name]
        
        # Проверка подписки обработчика
        if handler not in signal['handlers']:
            logger.warning(f"Обработчик не подписан на сигнал {signal_name}")
            return True
        
        # Удаление обработчика
        signal['handlers'].remove(handler)
        signal['subscribers'].discard(id(handler))
        
        # Обновление метаданных
        signal['modified_at'] = datetime.now().isoformat()
        signal['version'] += 1
        
        # Сохранение изменений
        self._save_signals()
        
        logger.info(f"Обработчик отписан от сигнала {signal_name}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отписки от сигнала {signal_name}: {e}")
        return False
```

### `get_signal_info(signal_name) -> Optional[SignalInfo]`

Получает информацию о сигнале по имени.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `signal_name` | `str` | Имя сигнала для получения информации |

#### Возвращаемое значение

- `SignalInfo` - информация о найденном сигнале
- `None` - сигнал не найден

#### Исключения

Нет

#### Пример использования

```python
def get_signal_info(self, signal_name: str) -> Optional[SignalInfo]:
    try:
        if not signal_name or not isinstance(signal_name, str):
            return None
        
        # Поиск сигнала
        signal_data = self._signals.get(signal_name)
        if not signal_data:
            return None
        
        # Создание объекта SignalInfo
        signal_info = SignalInfo(
            name=signal_data['name'],
            signal_type=signal_data['signal_type'],
            description=signal_data['description'],
            metadata=signal_data.get('metadata', {}),
            priority=signal_data.get('priority', 'normal')
        )
        
        return signal_info
        
    except Exception as e:
        logger.error(f"Ошибка получения информации о сигнале {signal_name}: {e}")
        return None
```

## 🚨 Обработка ошибок

### Типичные ошибки

1. **SignalNotFoundError** - сигнал не найден
2. **SignalValidationError** - ошибка валидации сигнала
3. **DuplicateSignalError** - дублирование имени сигнала
4. **HandlerValidationError** - ошибка валидации обработчика
5. **SignalEmissionError** - ошибка генерации сигнала
6. **HandlerNotFoundError** - обработчик не найден

### Стратегии обработки

```python
class SignalNotFoundError(Exception):
    """Сигнал не найден"""
    pass

class SignalValidationError(Exception):
    """Ошибка валидации сигнала"""
    pass

class HandlerValidationError(Exception):
    """Ошибка валидации обработчика"""
    pass

def safe_signal_operation(self, operation: Callable, *args, **kwargs):
    """Безопасное выполнение операций с сигналами"""
    try:
        return operation(*args, **kwargs)
    except SignalNotFoundError as e:
        logger.error(f"Сигнал не найден: {e}")
        return False
    except SignalValidationError as e:
        logger.error(f"Ошибка валидации: {e}")
        return False
    except HandlerValidationError as e:
        logger.error(f"Ошибка валидации обработчика: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return False
```

## 🔗 Связанные интерфейсы

- [[docs/api/interfaces/serial|ISerialManager]] - для генерации сигналов при событиях Serial
- [[docs/api/interfaces/command|ICommandExecutor]] - для генерации сигналов при выполнении команд
- [[docs/api/interfaces/sequence|ISequenceManager]] - для генерации сигналов при выполнении последовательностей

## 📚 Примеры использования

См. [[docs/api/examples/signal_manager]] для полных примеров использования.

## 🧪 Тестирование

```python
import pytest
from unittest.mock import Mock, patch
from core.interfaces import ISignalManager, SignalInfo
from core.signal_types import SignalType

class TestSignalManager:
    def test_register_signal_success(self):
        manager = SignalManager()
        signal_info = SignalInfo(
            name="test_signal",
            signal_type=SignalType.EVENT,
            description="Test signal"
        )
        
        result = manager.register_signal(signal_info)
        
        assert result is True
        assert "test_signal" in manager._signals
    
    def test_subscribe_to_signal_success(self):
        manager = SignalManager()
        manager.register_signal(SignalInfo("test_signal", SignalType.EVENT))
        
        handler = Mock()
        result = manager.subscribe_to_signal("test_signal", handler)
        
        assert result is True
        assert handler in manager._signals["test_signal"]["handlers"]
    
    def test_emit_signal_success(self):
        manager = SignalManager()
        manager.register_signal(SignalInfo("test_signal", SignalType.EVENT))
        
        handler = Mock()
        manager.subscribe_to_signal("test_signal", handler)
        
        result = manager.emit_signal("test_signal", "test_data")
        
        assert result is True
        handler.assert_called_once()
```

## 📝 Примечания реализации

- Все методы должны быть потокобезопасными
- Рекомендуется использовать асинхронное выполнение для обработчиков
- Сигналы должны поддерживать версионирование для отслеживания изменений
- Необходимо реализовать механизм отмены генерации сигналов
- Логирование должно включать детальную информацию о генерации и обработке
- Рекомендуется кэширование информации о сигналах для улучшения производительности
