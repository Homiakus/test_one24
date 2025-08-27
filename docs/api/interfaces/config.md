---
title: "IConfigLoader Interface"
type: "api_reference"
audiences: ["backend_dev", "frontend_dev"]
tags: ["api", "config", "loading", "interface"]
last_updated: "2024-12-20"
sources:
  - path: "core/interfaces.py"
    lines: "L422-L480"
    permalink: "core/interfaces.py#L422-L480"
related: ["docs/api/examples/config_loader", "docs/architecture/configuration", "docs/runbooks/troubleshooting"]
---

# ⚙️ IConfigLoader Interface

> [!info] Навигация
> Родитель: [[docs/api/index]] • Раздел: [[docs/api/interfaces]] • См. также: [[docs/api/examples/config_loader]]

## 📋 Обзор

`IConfigLoader` - интерфейс для загрузки и управления конфигурацией приложения. Обеспечивает загрузку конфигурационных файлов различных форматов, валидацию настроек и предоставление доступа к конфигурации через единообразный API.

## 🔧 Методы интерфейса

### `load_config(config_path) -> bool`

Загружает конфигурацию из указанного файла.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `config_path` | `str` | Путь к файлу конфигурации |

#### Возвращаемое значение

- `True` - конфигурация загружена успешно
- `False` - конфигурация не загружена

#### Исключения

- `ConfigFileNotFoundError` - файл конфигурации не найден
- `ConfigValidationError` - ошибка валидации конфигурации
- `ConfigFormatError` - ошибка формата файла

#### Пример использования

```python
from core.interfaces import IConfigLoader

class ConfigLoader(IConfigLoader):
    def load_config(self, config_path: str) -> bool:
        try:
            # Проверка существования файла
            if not os.path.exists(config_path):
                logger.error(f"Файл конфигурации не найден: {config_path}")
                return False
            
            # Определение формата файла
            file_extension = os.path.splitext(config_path)[1].lower()
            
            # Загрузка в зависимости от формата
            if file_extension == '.json':
                config_data = self._load_json_config(config_path)
            elif file_extension == '.toml':
                config_data = self._load_toml_config(config_path)
            elif file_extension == '.yaml' or file_extension == '.yml':
                config_data = self._load_yaml_config(config_path)
            elif file_extension == '.ini':
                config_data = self._load_ini_config(config_path)
            else:
                logger.error(f"Неподдерживаемый формат файла: {file_extension}")
                return False
            
            if config_data is None:
                return False
            
            # Валидация конфигурации
            if not self._validate_config(config_data):
                logger.error(f"Конфигурация не прошла валидацию: {config_path}")
                return False
            
            # Сохранение конфигурации
            self._config = config_data
            self._config_path = config_path
            self._last_loaded = datetime.now().isoformat()
            
            # Уведомление об изменении конфигурации
            self._notify_config_changed()
            
            logger.info(f"Конфигурация загружена успешно: {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации {config_path}: {e}")
            return False

def _load_json_config(self, config_path: str) -> Optional[Dict[str, Any]]:
    """Загрузка JSON конфигурации"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return config_data
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON в {config_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка чтения JSON файла {config_path}: {e}")
        return None

def _load_toml_config(self, config_path: str) -> Optional[Dict[str, Any]]:
    """Загрузка TOML конфигурации"""
    try:
        import tomli
        with open(config_path, 'rb') as f:
            config_data = tomli.load(f)
        return config_data
    except Exception as e:
        logger.error(f"Ошибка загрузки TOML файла {config_path}: {e}")
        return None

def _load_yaml_config(self, config_path: str) -> Optional[Dict[str, Any]]:
    """Загрузка YAML конфигурации"""
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        return config_data
    except yaml.YAMLError as e:
        logger.error(f"Ошибка парсинга YAML в {config_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка чтения YAML файла {config_path}: {e}")
        return None
```

### `get_config_value(key, default=None) -> Any`

Получает значение конфигурации по ключу.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `key` | `str` | Ключ для получения значения |
| `default` | `Any` | Значение по умолчанию, если ключ не найден |

#### Возвращаемое значение

- `Any` - значение конфигурации или значение по умолчанию

#### Исключения

Нет

#### Пример использования

```python
def get_config_value(self, key: str, default: Any = None) -> Any:
    try:
        if not self._config:
            logger.warning("Конфигурация не загружена")
            return default
        
        # Поддержка вложенных ключей (например, "database.host")
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                logger.debug(f"Ключ {key} не найден в конфигурации")
                return default
        
        return value
        
    except Exception as e:
        logger.error(f"Ошибка получения значения конфигурации {key}: {e}")
        return default

def get_nested_config(self, key_path: str, default: Any = None) -> Any:
    """Получение вложенного значения конфигурации"""
    try:
        if not self._config:
            return default
        
        keys = key_path.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            elif isinstance(value, list) and k.isdigit():
                index = int(k)
                if 0 <= index < len(value):
                    value = value[index]
                else:
                    return default
            else:
                return default
        
        return value
        
    except Exception as e:
        logger.error(f"Ошибка получения вложенного значения {key_path}: {e}")
        return default
```

### `set_config_value(key, value) -> bool`

Устанавливает значение конфигурации по ключу.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `key` | `str` | Ключ для установки значения |
| `value` | `Any` | Новое значение конфигурации |

#### Возвращаемое значение

- `True` - значение установлено успешно
- `False` - значение не установлено

#### Исключения

- `ConfigValidationError` - ошибка валидации значения
- `ConfigKeyError` - некорректный ключ конфигурации

#### Пример использования

```python
def set_config_value(self, key: str, value: Any) -> bool:
    try:
        if not self._config:
            logger.error("Конфигурация не загружена")
            return False
        
        # Валидация ключа
        if not self._validate_config_key(key):
            logger.error(f"Некорректный ключ конфигурации: {key}")
            return False
        
        # Валидация значения
        if not self._validate_config_value(key, value):
            logger.error(f"Некорректное значение для ключа {key}: {value}")
            return False
        
        # Установка значения
        keys = key.split('.')
        config = self._config
        
        # Создание вложенной структуры
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        # Установка финального значения
        config[keys[-1]] = value
        
        # Обновление метаданных
        self._last_modified = datetime.now().isoformat()
        self._config_changed = True
        
        # Уведомление об изменении
        self._notify_config_changed()
        
        logger.info(f"Значение конфигурации установлено: {key} = {value}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка установки значения конфигурации {key}: {e}")
        return False

def _validate_config_key(self, key: str) -> bool:
    """Валидация ключа конфигурации"""
    if not key or not isinstance(key, str):
        return False
    
    # Проверка длины
    if len(key) < 1 or len(key) > 200:
        return False
    
    # Проверка символов
    import re
    if not re.match(r'^[a-zA-Z0-9_.-]+$', key):
        return False
    
    # Проверка на зарезервированные ключи
    reserved_keys = {'__version__', '__metadata__', '__schema__'}
    if key in reserved_keys:
        return False
    
    return True

def _validate_config_value(self, key: str, value: Any) -> bool:
    """Валидация значения конфигурации"""
    try:
        # Проверка схемы конфигурации
        if hasattr(self, '_schema') and self._schema:
            return self._validate_against_schema(key, value)
        
        # Базовая валидация
        if value is None:
            return True
        
        # Проверка типов для известных ключей
        type_mapping = {
            'database.port': int,
            'database.timeout': (int, float),
            'logging.level': str,
            'logging.enabled': bool
        }
        
        if key in type_mapping:
            expected_type = type_mapping[key]
            if not isinstance(value, expected_type):
                return False
        
        return True
        
    except Exception:
        return False
```

### `save_config(config_path=None) -> bool`

Сохраняет текущую конфигурацию в файл.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `config_path` | `Optional[str]` | Путь для сохранения (None - текущий путь) |

#### Возвращаемое значение

- `True` - конфигурация сохранена успешно
- `False` - конфигурация не сохранена

#### Исключения

- `ConfigSaveError` - ошибка сохранения конфигурации
- `ConfigNotLoadedError` - конфигурация не загружена

#### Пример использования

```python
def save_config(self, config_path: Optional[str] = None) -> bool:
    try:
        if not self._config:
            logger.error("Конфигурация не загружена")
            return False
        
        # Определение пути сохранения
        save_path = config_path or self._config_path
        if not save_path:
            logger.error("Путь для сохранения не указан")
            return False
        
        # Создание резервной копии
        if os.path.exists(save_path):
            backup_path = f"{save_path}.backup.{int(time.time())}"
            shutil.copy2(save_path, backup_path)
            logger.info(f"Создана резервная копия: {backup_path}")
        
        # Определение формата файла
        file_extension = os.path.splitext(save_path)[1].lower()
        
        # Сохранение в зависимости от формата
        if file_extension == '.json':
            success = self._save_json_config(save_path)
        elif file_extension == '.toml':
            success = self._save_toml_config(save_path)
        elif file_extension == '.yaml' or file_extension == '.yml':
            success = self._save_yaml_config(save_path)
        else:
            logger.error(f"Неподдерживаемый формат файла для сохранения: {file_extension}")
            return False
        
        if success:
            # Обновление метаданных
            self._config_path = save_path
            self._last_saved = datetime.now().isoformat()
            self._config_changed = False
            
            logger.info(f"Конфигурация сохранена успешно: {save_path}")
            return True
        else:
            return False
        
    except Exception as e:
        logger.error(f"Ошибка сохранения конфигурации: {e}")
        return False

def _save_json_config(self, config_path: str) -> bool:
    """Сохранение JSON конфигурации"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения JSON конфигурации: {e}")
        return False

def _save_toml_config(self, config_path: str) -> bool:
    """Сохранение TOML конфигурации"""
    try:
        import tomli_w
        with open(config_path, 'wb') as f:
            tomli_w.dump(self._config, f)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения TOML конфигурации: {e}")
        return False

def _save_yaml_config(self, config_path: str) -> bool:
    """Сохранение YAML конфигурации"""
    try:
        import yaml
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения YAML конфигурации: {e}")
        return False
```

### `reload_config() -> bool`

Перезагружает конфигурацию из файла.

#### Параметры

Нет

#### Возвращаемое значение

- `True` - конфигурация перезагружена успешно
- `False` - конфигурация не перезагружена

#### Исключения

- `ConfigFileNotFoundError` - файл конфигурации не найден
- `ConfigValidationError` - ошибка валидации конфигурации

#### Пример использования

```python
def reload_config(self) -> bool:
    try:
        if not self._config_path:
            logger.error("Путь к файлу конфигурации не установлен")
            return False
        
        logger.info(f"Перезагрузка конфигурации: {self._config_path}")
        
        # Сохранение текущих изменений
        if self._config_changed:
            logger.info("Сохранение текущих изменений перед перезагрузкой")
            if not self.save_config():
                logger.warning("Не удалось сохранить текущие изменения")
        
        # Перезагрузка конфигурации
        return self.load_config(self._config_path)
        
    except Exception as e:
        logger.error(f"Ошибка перезагрузки конфигурации: {e}")
        return False
```

## 🚨 Обработка ошибок

### Типичные ошибки

1. **ConfigFileNotFoundError** - файл конфигурации не найден
2. **ConfigValidationError** - ошибка валидации конфигурации
3. **ConfigFormatError** - ошибка формата файла
4. **ConfigSaveError** - ошибка сохранения конфигурации
5. **ConfigNotLoadedError** - конфигурация не загружена
6. **ConfigKeyError** - некорректный ключ конфигурации

### Стратегии обработки

```python
class ConfigFileNotFoundError(Exception):
    """Файл конфигурации не найден"""
    pass

class ConfigValidationError(Exception):
    """Ошибка валидации конфигурации"""
    pass

class ConfigFormatError(Exception):
    """Ошибка формата файла"""
    pass

def safe_config_operation(self, operation: Callable, *args, **kwargs):
    """Безопасное выполнение операций с конфигурацией"""
    try:
        return operation(*args, **kwargs)
    except ConfigFileNotFoundError as e:
        logger.error(f"Файл конфигурации не найден: {e}")
        return False
    except ConfigValidationError as e:
        logger.error(f"Ошибка валидации: {e}")
        return False
    except ConfigFormatError as e:
        logger.error(f"Ошибка формата: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return False
```

## 🔗 Связанные интерфейсы

- [[docs/api/interfaces/serial|ISerialManager]] - для загрузки конфигурации Serial
- [[docs/api/interfaces/command|ICommandExecutor]] - для загрузки конфигурации команд
- [[docs/api/interfaces/sequence|ISequenceManager]] - для загрузки конфигурации последовательностей

## 📚 Примеры использования

См. [[docs/api/examples/config_loader]] для полных примеров использования.

## 🧪 Тестирование

```python
import pytest
from unittest.mock import Mock, patch
from core.interfaces import IConfigLoader

class TestConfigLoader:
    def test_load_config_success(self):
        loader = ConfigLoader()
        
        result = loader.load_config("test_config.json")
        
        assert result is True
        assert loader._config is not None
    
    def test_get_config_value_success(self):
        loader = ConfigLoader()
        loader._config = {"database": {"host": "localhost"}}
        
        value = loader.get_config_value("database.host")
        
        assert value == "localhost"
    
    def test_set_config_value_success(self):
        loader = ConfigLoader()
        loader._config = {}
        
        result = loader.set_config_value("database.port", 5432)
        
        assert result is True
        assert loader.get_config_value("database.port") == 5432
```

## 📝 Примечания реализации

- Все методы должны быть потокобезопасными
- Рекомендуется использовать кэширование для часто запрашиваемых значений
- Конфигурация должна поддерживать версионирование для отслеживания изменений
- Необходимо реализовать механизм валидации схемы конфигурации
- Логирование должно включать информацию об операциях с конфигурацией
- Рекомендуется поддержка hot-reload для автоматического обновления конфигурации
