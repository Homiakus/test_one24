---
title: "ITagManager Interface"
type: "api_reference"
audiences: ["backend_dev", "frontend_dev"]
tags: ["api", "tag", "management", "interface"]
last_updated: "2024-12-20"
sources:
  - path: "core/interfaces.py"
    lines: "L202-L280"
    permalink: "core/interfaces.py#L202-L280"
related: ["docs/api/examples/tag_manager", "docs/architecture/tags", "docs/runbooks/troubleshooting"]
---

# 🏷️ ITagManager Interface

> [!info] Навигация
> Родитель: [[docs/api/index]] • Раздел: [[docs/api/interfaces]] • См. также: [[docs/api/examples/tag_manager]]

## 📋 Обзор

`ITagManager` - интерфейс для управления тегами команд и их метаданными. Обеспечивает создание, поиск, валидацию и управление тегами, которые используются для категоризации и организации команд в системе.

## 🔧 Методы интерфейса

### `create_tag(tag_info) -> bool`

Создает новый тег с указанными параметрами.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `tag_info` | `TagInfo` | Информация о создаваемом теге |

#### Возвращаемое значение

- `True` - тег создан успешно
- `False` - тег не создан

#### Исключения

- `TagValidationError` - ошибка валидации тега
- `DuplicateTagError` - тег с таким именем уже существует

#### Пример использования

```python
from core.interfaces import ITagManager, TagInfo
from core.tag_types import TagType

class TagManager(ITagManager):
    def create_tag(self, tag_info: TagInfo) -> bool:
        try:
            # Валидация информации о теге
            if not self._validate_tag_info(tag_info):
                logger.error(f"Некорректная информация о теге: {tag_info}")
                return False
            
            # Проверка на дублирование
            if self._tag_exists(tag_info.name):
                logger.error(f"Тег с именем {tag_info.name} уже существует")
                return False
            
            # Создание тега
            tag = {
                'name': tag_info.name,
                'description': tag_info.description,
                'tag_type': tag_info.tag_type,
                'created_at': datetime.now().isoformat(),
                'modified_at': datetime.now().isoformat(),
                'version': 1,
                'enabled': True,
                'metadata': tag_info.metadata.copy() if tag_info.metadata else {},
                'usage_count': 0,
                'last_used': None
            }
            
            # Сохранение тега
            self._tags[tag_info.name] = tag
            self._save_tags()
            
            logger.info(f"Тег {tag_info.name} создан успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания тега {tag_info.name}: {e}")
            return False

def _validate_tag_info(self, tag_info: TagInfo) -> bool:
    """Валидация информации о теге"""
    if not tag_info or not isinstance(tag_info, TagInfo):
        return False
    
    # Проверка имени
    if not tag_info.name or not isinstance(tag_info.name, str):
        return False
    
    if len(tag_info.name) < 1 or len(tag_info.name) > 50:
        return False
    
    # Проверка символов имени
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', tag_info.name):
        return False
    
    # Проверка описания
    if tag_info.description and len(tag_info.description) > 500:
        return False
    
    # Проверка типа тега
    if tag_info.tag_type not in TagType:
        return False
    
    return True
```

### `get_tag(name) -> Optional[TagInfo]`

Получает информацию о теге по имени.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `name` | `str` | Имя тега для поиска |

#### Возвращаемое значение

- `TagInfo` - информация о найденном теге
- `None` - тег не найден

#### Исключения

Нет

#### Пример использования

```python
def get_tag(self, name: str) -> Optional[TagInfo]:
    try:
        if not name or not isinstance(name, str):
            return None
        
        # Поиск тега
        tag_data = self._tags.get(name)
        if not tag_data:
            return None
        
        # Создание объекта TagInfo
        tag_info = TagInfo(
            name=tag_data['name'],
            description=tag_data['description'],
            tag_type=tag_data['tag_type'],
            metadata=tag_data.get('metadata', {})
        )
        
        # Обновление статистики использования
        self._update_usage_statistics(name)
        
        return tag_info
        
    except Exception as e:
        logger.error(f"Ошибка получения тега {name}: {e}")
        return None

def _update_usage_statistics(self, tag_name: str):
    """Обновление статистики использования тега"""
    if tag_name in self._tags:
        self._tags[tag_name]['usage_count'] += 1
        self._tags[tag_name]['last_used'] = datetime.now().isoformat()
```

### `update_tag(name, updates) -> bool`

Обновляет существующий тег.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `name` | `str` | Имя обновляемого тега |
| `updates` | `Dict[str, Any]` | Словарь с обновлениями |

#### Возвращаемое значение

- `True` - тег обновлен успешно
- `False` - тег не обновлен

#### Исключения

- `TagNotFoundError` - тег не найден
- `TagValidationError` - ошибка валидации обновлений

#### Пример использования

```python
def update_tag(self, name: str, updates: Dict[str, Any]) -> bool:
    try:
        # Проверка существования тега
        if not self._tag_exists(name):
            logger.error(f"Тег {name} не найден")
            return False
        
        # Валидация обновлений
        if not self._validate_updates(updates):
            logger.error(f"Некорректные обновления для тега {name}")
            return False
        
        # Применение обновлений
        tag = self._tags[name]
        
        # Разрешенные поля для обновления
        allowed_fields = {'description', 'metadata', 'enabled'}
        
        for field, value in updates.items():
            if field in allowed_fields:
                if field == 'metadata':
                    # Слияние метаданных
                    tag['metadata'].update(value)
                else:
                    tag[field] = value
        
        # Обновление метаданных
        tag['modified_at'] = datetime.now().isoformat()
        tag['version'] += 1
        
        # Сохранение изменений
        self._save_tags()
        
        logger.info(f"Тег {name} обновлен успешно")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка обновления тега {name}: {e}")
        return False

def _validate_updates(self, updates: Dict[str, Any]) -> bool:
    """Валидация обновлений тега"""
    if not updates or not isinstance(updates, dict):
        return False
    
    # Проверка разрешенных полей
    allowed_fields = {'description', 'metadata', 'enabled'}
    if not all(field in allowed_fields for field in updates.keys()):
        return False
    
    # Валидация описания
    if 'description' in updates:
        desc = updates['description']
        if desc and (not isinstance(desc, str) or len(desc) > 500):
            return False
    
    # Валидация метаданных
    if 'metadata' in updates:
        metadata = updates['metadata']
        if not isinstance(metadata, dict):
            return False
    
    # Валидация флага enabled
    if 'enabled' in updates:
        enabled = updates['enabled']
        if not isinstance(enabled, bool):
            return False
    
    return True
```

### `delete_tag(name) -> bool`

Удаляет тег по имени.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `name` | `str` | Имя удаляемого тега |

#### Возвращаемое значение

- `True` - тег удален успешно
- `False` - тег не удален

#### Исключения

- `TagNotFoundError` - тег не найден
- `TagInUseError` - тег используется в данный момент

#### Пример использования

```python
def delete_tag(self, name: str) -> bool:
    try:
        # Проверка существования тега
        if not self._tag_exists(name):
            logger.error(f"Тег {name} не найден")
            return False
        
        # Проверка использования
        if self._is_tag_in_use(name):
            logger.error(f"Нельзя удалить используемый тег: {name}")
            return False
        
        # Удаление тега
        removed_tag = self._tags.pop(name)
        self._save_tags()
        
        logger.info(f"Тег {name} удален успешно")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка удаления тега {name}: {e}")
        return False

def _is_tag_in_use(self, name: str) -> bool:
    """Проверка, используется ли тег"""
    # Проверка использования в командах
    for command in self._command_tags.values():
        if name in command:
            return True
    
    # Проверка использования в последовательностях
    for sequence in self._sequence_tags.values():
        if name in sequence:
            return True
    
    return False
```

### `search_tags(query, tag_type=None) -> List[TagInfo]`

Выполняет поиск тегов по запросу.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `query` | `str` | Поисковый запрос |
| `tag_type` | `Optional[TagType]` | Фильтр по типу тега |

#### Возвращаемое значение

`List[TagInfo]` - список найденных тегов

#### Исключения

Нет

#### Пример использования

```python
def search_tags(self, query: str, tag_type: Optional[TagType] = None) -> List[TagInfo]:
    try:
        if not query or not isinstance(query, str):
            return []
        
        results = []
        query_lower = query.lower()
        
        for tag_data in self._tags.values():
            # Фильтр по типу
            if tag_type and tag_data['tag_type'] != tag_type:
                continue
            
            # Поиск по имени
            if query_lower in tag_data['name'].lower():
                results.append(self._create_tag_info(tag_data))
                continue
            
            # Поиск по описанию
            if tag_data['description'] and query_lower in tag_data['description'].lower():
                results.append(self._create_tag_info(tag_data))
                continue
            
            # Поиск по метаданным
            if self._search_in_metadata(tag_data.get('metadata', {}), query_lower):
                results.append(self._create_tag_info(tag_data))
                continue
        
        # Сортировка по релевантности
        results.sort(key=lambda x: self._calculate_relevance(x, query_lower), reverse=True)
        
        return results
        
    except Exception as e:
        logger.error(f"Ошибка поиска тегов: {e}")
        return []

def _search_in_metadata(self, metadata: Dict[str, Any], query: str) -> bool:
    """Поиск в метаданных тега"""
    for key, value in metadata.items():
        if isinstance(value, str) and query in value.lower():
            return True
        elif isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, str) and query in item.lower():
                    return True
    return False

def _calculate_relevance(self, tag_info: TagInfo, query: str) -> float:
    """Вычисление релевантности тега для запроса"""
    relevance = 0.0
    
    # Приоритет по имени
    if query in tag_info.name.lower():
        relevance += 10.0
    
    # Приоритет по описанию
    if tag_info.description and query in tag_info.description.lower():
        relevance += 5.0
    
    # Приоритет по метаданным
    if tag_info.metadata:
        for value in tag_info.metadata.values():
            if isinstance(value, str) and query in value.lower():
                relevance += 2.0
    
    return relevance
```

## 🚨 Обработка ошибок

### Типичные ошибки

1. **TagNotFoundError** - тег не найден
2. **TagValidationError** - ошибка валидации тега
3. **DuplicateTagError** - дублирование имени тега
4. **TagInUseError** - попытка удаления используемого тега
5. **TagTypeError** - некорректный тип тега

### Стратегии обработки

```python
class TagNotFoundError(Exception):
    """Тег не найден"""
    pass

class TagValidationError(Exception):
    """Ошибка валидации тега"""
    pass

class DuplicateTagError(Exception):
    """Дублирование имени тега"""
    pass

def safe_tag_operation(self, operation: Callable, *args, **kwargs):
    """Безопасное выполнение операций с тегами"""
    try:
        return operation(*args, **kwargs)
    except TagNotFoundError as e:
        logger.error(f"Тег не найден: {e}")
        return False
    except TagValidationError as e:
        logger.error(f"Ошибка валидации: {e}")
        return False
    except DuplicateTagError as e:
        logger.error(f"Дублирование тега: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return False
```

## 🔗 Связанные интерфейсы

- [[docs/api/interfaces/command|ICommandExecutor]] - для выполнения команд с тегами
- [[docs/api/interfaces/sequence|ISequenceManager]] - для управления последовательностями с тегами
- [[docs/api/interfaces/signal|ISignalManager]] - для обработки сигналов с тегами

## 📚 Примеры использования

См. [[docs/api/examples/tag_manager]] для полных примеров использования.

## 🧪 Тестирование

```python
import pytest
from unittest.mock import Mock, patch
from core.interfaces import ITagManager, TagInfo
from core.tag_types import TagType

class TestTagManager:
    def test_create_tag_success(self):
        manager = TagManager()
        tag_info = TagInfo(
            name="test_tag",
            description="Test tag",
            tag_type=TagType.COMMAND
        )
        
        result = manager.create_tag(tag_info)
        
        assert result is True
        assert "test_tag" in manager._tags
    
    def test_get_tag_success(self):
        manager = TagManager()
        manager.create_tag(TagInfo("test_tag", "Test", TagType.COMMAND))
        
        tag = manager.get_tag("test_tag")
        
        assert tag is not None
        assert tag.name == "test_tag"
    
    def test_search_tags_success(self):
        manager = TagManager()
        manager.create_tag(TagInfo("test_tag", "Test description", TagType.COMMAND))
        
        results = manager.search_tags("test")
        
        assert len(results) == 1
        assert results[0].name == "test_tag"
```

## 📝 Примечания реализации

- Все методы должны быть потокобезопасными
- Рекомендуется использовать кэширование для часто запрашиваемых тегов
- Теги должны поддерживать версионирование для отслеживания изменений
- Необходимо реализовать механизм очистки неиспользуемых тегов
- Логирование должно включать информацию об операциях с тегами
- Рекомендуется поддержка импорта/экспорта тегов для миграции
