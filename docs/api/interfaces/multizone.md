---
title: "IMultizoneManager Interface"
type: "api_reference"
audiences: ["backend_dev", "frontend_dev"]
tags: ["api", "multizone", "management", "interface"]
last_updated: "2024-12-20"
sources:
  - path: "core/interfaces.py"
    lines: "L282-L350"
    permalink: "core/interfaces.py#L282-L350"
related: ["docs/api/examples/multizone_manager", "docs/architecture/multizone", "docs/runbooks/troubleshooting"]
---

# 🌐 IMultizoneManager Interface

> [!info] Навигация
> Родитель: [[docs/api/index]] • Раздел: [[docs/api/interfaces]] • См. также: [[docs/api/examples/multizone_manager]]

## 📋 Обзор

`IMultizoneManager` - интерфейс для управления многозонными устройствами. Обеспечивает создание, настройку и управление зонами, их синхронизацию и координацию работы в рамках единой системы.

## 🔧 Методы интерфейса

### `create_zone(zone_config) -> bool`

Создает новую зону с указанной конфигурацией.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `zone_config` | `Dict[str, Any]` | Конфигурация создаваемой зоны |

#### Возвращаемое значение

- `True` - зона создана успешно
- `False` - зона не создана

#### Исключения

- `ZoneValidationError` - ошибка валидации конфигурации зоны
- `DuplicateZoneError` - зона с таким именем уже существует

#### Пример использования

```python
from core.interfaces import IMultizoneManager

class MultizoneManager(IMultizoneManager):
    def create_zone(self, zone_config: Dict[str, Any]) -> bool:
        try:
            # Валидация конфигурации зоны
            if not self._validate_zone_config(zone_config):
                logger.error(f"Некорректная конфигурация зоны: {zone_config}")
                return False
            
            zone_name = zone_config['name']
            
            # Проверка на дублирование
            if self._zone_exists(zone_name):
                logger.error(f"Зона с именем {zone_name} уже существует")
                return False
            
            # Создание зоны
            zone = {
                'name': zone_name,
                'type': zone_config.get('type', 'standard'),
                'enabled': zone_config.get('enabled', True),
                'created_at': datetime.now().isoformat(),
                'modified_at': datetime.now().isoformat(),
                'version': 1,
                'status': 'inactive',
                'devices': zone_config.get('devices', []),
                'settings': zone_config.get('settings', {}),
                'metadata': zone_config.get('metadata', {}),
                'parent_zone': zone_config.get('parent_zone'),
                'child_zones': [],
                'synchronization': zone_config.get('synchronization', {})
            }
            
            # Проверка иерархии зон
            if zone['parent_zone'] and not self._validate_parent_zone(zone['parent_zone']):
                logger.error(f"Некорректная родительская зона: {zone['parent_zone']}")
                return False
            
            # Сохранение зоны
            self._zones[zone_name] = zone
            
            # Обновление иерархии
            if zone['parent_zone']:
                self._zones[zone['parent_zone']]['child_zones'].append(zone_name)
            
            self._save_zones()
            
            logger.info(f"Зона {zone_name} создана успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания зоны: {e}")
            return False

def _validate_zone_config(self, zone_config: Dict[str, Any]) -> bool:
    """Валидация конфигурации зоны"""
    if not zone_config or not isinstance(zone_config, dict):
        return False
    
    # Обязательные поля
    required_fields = ['name']
    for field in required_fields:
        if field not in zone_config:
            return False
    
    # Валидация имени
    name = zone_config['name']
    if not isinstance(name, str) or len(name) < 1 or len(name) > 100:
        return False
    
    # Валидация типа зоны
    zone_type = zone_config.get('type', 'standard')
    valid_types = ['standard', 'master', 'slave', 'coordinator']
    if zone_type not in valid_types:
        return False
    
    # Валидация устройств
    devices = zone_config.get('devices', [])
    if not isinstance(devices, list):
        return False
    
    # Валидация настроек
    settings = zone_config.get('settings', {})
    if not isinstance(settings, dict):
        return False
    
    return True
```

### `configure_zone(zone_name, settings) -> bool`

Настраивает существующую зону.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `zone_name` | `str` | Имя настраиваемой зоны |
| `settings` | `Dict[str, Any]` | Новые настройки зоны |

#### Возвращаемое значение

- `True` - зона настроена успешно
- `False` - зона не настроена

#### Исключения

- `ZoneNotFoundError` - зона не найдена
- `ZoneConfigurationError` - ошибка конфигурации зоны

#### Пример использования

```python
def configure_zone(self, zone_name: str, settings: Dict[str, Any]) -> bool:
    try:
        # Проверка существования зоны
        if not self._zone_exists(zone_name):
            logger.error(f"Зона {zone_name} не найдена")
            return False
        
        # Валидация настроек
        if not self._validate_zone_settings(settings):
            logger.error(f"Некорректные настройки для зоны {zone_name}")
            return False
        
        # Получение зоны
        zone = self._zones[zone_name]
        
        # Применение настроек
        for key, value in settings.items():
            if key in ['devices', 'synchronization', 'metadata']:
                # Обновление сложных объектов
                if isinstance(value, dict) and key in zone:
                    zone[key].update(value)
                else:
                    zone[key] = value
            elif key in ['enabled', 'type']:
                # Обновление базовых свойств
                zone[key] = value
            else:
                # Обновление пользовательских настроек
                zone['settings'][key] = value
        
        # Обновление метаданных
        zone['modified_at'] = datetime.now().isoformat()
        zone['version'] += 1
        
        # Сохранение изменений
        self._save_zones()
        
        # Уведомление об изменениях
        self._notify_zone_changed(zone_name)
        
        logger.info(f"Зона {zone_name} настроена успешно")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка настройки зоны {zone_name}: {e}")
        return False

def _validate_zone_settings(self, settings: Dict[str, Any]) -> bool:
    """Валидация настроек зоны"""
    if not settings or not isinstance(settings, dict):
        return False
    
    # Валидация устройств
    if 'devices' in settings:
        devices = settings['devices']
        if not isinstance(devices, list):
            return False
        
        for device in devices:
            if not isinstance(device, dict) or 'id' not in device:
                return False
    
    # Валидация синхронизации
    if 'synchronization' in settings:
        sync = settings['synchronization']
        if not isinstance(sync, dict):
            return False
        
        valid_sync_keys = ['enabled', 'mode', 'interval', 'master_zone']
        if not all(key in valid_sync_keys for key in sync.keys()):
            return False
    
    return True
```

### `synchronize_zones(zone_names=None) -> bool`

Синхронизирует указанные зоны или все зоны.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `zone_names` | `Optional[List[str]]` | Список имен зон для синхронизации (None - все зоны) |

#### Возвращаемое значение

- `True` - синхронизация выполнена успешно
- `False` - синхронизация не выполнена

#### Исключения

- `ZoneSynchronizationError` - ошибка синхронизации зон
- `ZoneNotReadyError` - зона не готова к синхронизации

#### Пример использования

```python
def synchronize_zones(self, zone_names: Optional[List[str]] = None) -> bool:
    try:
        # Определение зон для синхронизации
        if zone_names is None:
            zones_to_sync = list(self._zones.keys())
        else:
            zones_to_sync = [name for name in zone_names if self._zone_exists(name)]
        
        if not zones_to_sync:
            logger.warning("Нет зон для синхронизации")
            return True
        
        logger.info(f"Начало синхронизации {len(zones_to_sync)} зон")
        
        # Группировка зон по иерархии
        master_zones = []
        slave_zones = []
        
        for zone_name in zones_to_sync:
            zone = self._zones[zone_name]
            if zone['type'] == 'master':
                master_zones.append(zone_name)
            elif zone['type'] == 'slave':
                slave_zones.append(zone_name)
        
        # Синхронизация мастер-зон
        for master_zone in master_zones:
            if not self._synchronize_master_zone(master_zone):
                logger.error(f"Ошибка синхронизации мастер-зоны {master_zone}")
                return False
        
        # Синхронизация подчиненных зон
        for slave_zone in slave_zones:
            if not self._synchronize_slave_zone(slave_zone):
                logger.error(f"Ошибка синхронизации подчиненной зоны {slave_zone}")
                return False
        
        logger.info("Синхронизация зон завершена успешно")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка синхронизации зон: {e}")
        return False

def _synchronize_master_zone(self, zone_name: str) -> bool:
    """Синхронизация мастер-зоны"""
    zone = self._zones[zone_name]
    
    try:
        # Проверка готовности зоны
        if not self._is_zone_ready(zone_name):
            logger.warning(f"Зона {zone_name} не готова к синхронизации")
            return False
        
        # Обновление статуса
        zone['status'] = 'synchronizing'
        zone['last_sync'] = datetime.now().isoformat()
        
        # Синхронизация устройств в зоне
        for device in zone['devices']:
            if not self._synchronize_device(device):
                logger.warning(f"Ошибка синхронизации устройства {device['id']} в зоне {zone_name}")
        
        # Синхронизация дочерних зон
        for child_zone in zone['child_zones']:
            if self._zone_exists(child_zone):
                self._synchronize_slave_zone(child_zone)
        
        zone['status'] = 'synchronized'
        return True
        
    except Exception as e:
        logger.error(f"Ошибка синхронизации мастер-зоны {zone_name}: {e}")
        zone['status'] = 'error'
        return False

def _synchronize_slave_zone(self, zone_name: str) -> bool:
    """Синхронизация подчиненной зоны"""
    zone = self._zones[zone_name]
    
    try:
        # Проверка готовности зоны
        if not self._is_zone_ready(zone_name):
            return False
        
        # Получение родительской зоны
        parent_zone_name = zone.get('parent_zone')
        if not parent_zone_name or not self._zone_exists(parent_zone_name):
            logger.warning(f"Родительская зона не найдена для {zone_name}")
            return False
        
        parent_zone = self._zones[parent_zone_name]
        
        # Проверка синхронизации родительской зоны
        if parent_zone['status'] != 'synchronized':
            logger.warning(f"Родительская зона {parent_zone_name} не синхронизирована")
            return False
        
        # Синхронизация с родительской зоной
        zone['status'] = 'synchronizing'
        zone['last_sync'] = datetime.now().isoformat()
        
        # Копирование настроек от родительской зоны
        if zone.get('synchronization', {}).get('enabled', False):
            self._copy_settings_from_parent(zone_name, parent_zone_name)
        
        zone['status'] = 'synchronized'
        return True
        
    except Exception as e:
        logger.error(f"Ошибка синхронизации подчиненной зоны {zone_name}: {e}")
        zone['status'] = 'error'
        return False
```

### `get_zone_status(zone_name) -> Dict[str, Any]`

Получает статус указанной зоны.

#### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `zone_name` | `str` | Имя зоны для получения статуса |

#### Возвращаемое значение

`Dict[str, Any]` - словарь со статусом зоны

#### Исключения

- `ZoneNotFoundError` - зона не найдена

#### Пример использования

```python
def get_zone_status(self, zone_name: str) -> Dict[str, Any]:
    try:
        # Проверка существования зоны
        if not self._zone_exists(zone_name):
            logger.error(f"Зона {zone_name} не найдена")
            return {}
        
        zone = self._zones[zone_name]
        
        # Сбор информации о статусе
        status = {
            'name': zone['name'],
            'type': zone['type'],
            'status': zone['status'],
            'enabled': zone['enabled'],
            'devices_count': len(zone['devices']),
            'child_zones_count': len(zone['child_zones']),
            'last_sync': zone.get('last_sync'),
            'created_at': zone['created_at'],
            'modified_at': zone['modified_at'],
            'version': zone['version']
        }
        
        # Добавление информации об устройствах
        device_statuses = []
        for device in zone['devices']:
            device_status = self._get_device_status(device['id'])
            if device_status:
                device_statuses.append(device_status)
        
        status['device_statuses'] = device_statuses
        
        # Добавление информации о синхронизации
        if 'synchronization' in zone:
            status['synchronization'] = zone['synchronization']
        
        return status
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса зоны {zone_name}: {e}")
        return {}

def _get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
    """Получение статуса устройства"""
    try:
        # Здесь должна быть логика получения статуса устройства
        # Пока возвращаем базовую информацию
        return {
            'id': device_id,
            'status': 'unknown',
            'last_seen': None
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса устройства {device_id}: {e}")
        return None
```

## 🚨 Обработка ошибок

### Типичные ошибки

1. **ZoneNotFoundError** - зона не найдена
2. **ZoneValidationError** - ошибка валидации зоны
3. **DuplicateZoneError** - дублирование имени зоны
4. **ZoneConfigurationError** - ошибка конфигурации зоны
5. **ZoneSynchronizationError** - ошибка синхронизации зон
6. **ZoneNotReadyError** - зона не готова к операции

### Стратегии обработки

```python
class ZoneNotFoundError(Exception):
    """Зона не найдена"""
    pass

class ZoneValidationError(Exception):
    """Ошибка валидации зоны"""
    pass

class ZoneSynchronizationError(Exception):
    """Ошибка синхронизации зон"""
    pass

def safe_zone_operation(self, operation: Callable, *args, **kwargs):
    """Безопасное выполнение операций с зонами"""
    try:
        return operation(*args, **kwargs)
    except ZoneNotFoundError as e:
        logger.error(f"Зона не найдена: {e}")
        return False
    except ZoneValidationError as e:
        logger.error(f"Ошибка валидации: {e}")
        return False
    except ZoneSynchronizationError as e:
        logger.error(f"Ошибка синхронизации: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return False
```

## 🔗 Связанные интерфейсы

- [[docs/api/interfaces/serial|ISerialManager]] - для связи с устройствами в зонах
- [[docs/api/interfaces/command|ICommandExecutor]] - для выполнения команд в зонах
- [[docs/api/interfaces/sequence|ISequenceManager]] - для управления последовательностями в зонах

## 📚 Примеры использования

См. [[docs/api/examples/multizone_manager]] для полных примеров использования.

## 🧪 Тестирование

```python
import pytest
from unittest.mock import Mock, patch
from core.interfaces import IMultizoneManager

class TestMultizoneManager:
    def test_create_zone_success(self):
        manager = MultizoneManager()
        zone_config = {
            'name': 'test_zone',
            'type': 'standard',
            'devices': []
        }
        
        result = manager.create_zone(zone_config)
        
        assert result is True
        assert 'test_zone' in manager._zones
    
    def test_configure_zone_success(self):
        manager = MultizoneManager()
        manager.create_zone({'name': 'test_zone', 'type': 'standard'})
        
        result = manager.configure_zone('test_zone', {'enabled': False})
        
        assert result is True
        assert manager._zones['test_zone']['enabled'] is False
    
    def test_synchronize_zones_success(self):
        manager = MultizoneManager()
        manager.create_zone({'name': 'master_zone', 'type': 'master'})
        manager.create_zone({'name': 'slave_zone', 'type': 'slave'})
        
        result = manager.synchronize_zones()
        
        assert result is True
```

## 📝 Примечания реализации

- Все методы должны быть потокобезопасными
- Рекомендуется использовать асинхронное выполнение для синхронизации
- Зоны должны поддерживать версионирование для отслеживания изменений
- Необходимо реализовать механизм отмены синхронизации
- Логирование должно включать детальную информацию о синхронизации
- Рекомендуется кэширование статуса зон для улучшения производительности
