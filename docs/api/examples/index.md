---
title: "API Examples - Примеры использования"
type: "api_reference"
audiences: ["backend_dev", "frontend_dev"]
tags: ["api", "examples", "usage", "tutorial"]
last_updated: "2024-12-19"
---

# 📚 API Examples - Примеры использования

> [!info] Примеры API
> Эта страница содержит исполняемые примеры использования всех публичных API интерфейсов приложения

## 🎯 Цель

Данные примеры демонстрируют:
- Правильное использование всех публичных интерфейсов
- Типичные сценарии применения
- Обработку ошибок и edge cases
- Лучшие практики интеграции

## 📋 Содержание

### Основные интерфейсы

#### [[docs/api/examples/serial_manager|ISerialManager Examples]]
- Подключение к Serial порту
- Отправка команд
- Получение информации о портах
- Обработка ошибок подключения

#### [[docs/api/examples/command_executor|ICommandExecutor Examples]]
- Выполнение команд
- Валидация команд
- Обработка результатов
- Интеграция с Serial Manager

#### [[docs/api/examples/sequence_manager|ISequenceManager Examples]]
- Работа с последовательностями
- Расширение последовательностей
- Валидация последовательностей
- Кеширование

#### [[docs/api/examples/tag_manager|ITagManager Examples]]
- Парсинг команд с тегами
- Валидация тегов
- Обработка тегов
- Регистрация обработчиков

#### [[docs/api/examples/multizone_manager|IMultizoneManager Examples]]
- Управление зонами
- Работа с битовыми масками
- Валидация зон
- Интеграция с командами

#### [[docs/api/examples/signal_manager|ISignalManager Examples]]
- Регистрация сигналов
- Обработка входящих данных
- Работа с переменными
- Мониторинг сигналов

### Вспомогательные интерфейсы

#### [[docs/api/examples/di_container|IDIContainer Examples]]
- Регистрация сервисов
- Разрешение зависимостей
- Управление жизненным циклом
- Фабричные методы

#### [[docs/api/examples/event_bus|IEventBus Examples]]
- Подписка на события
- Публикация событий
- Обработка событий
- Отписка от событий

#### [[docs/api/examples/config_loader|IConfigLoader Examples]]
- Загрузка конфигурации
- Сохранение настроек
- Валидация конфигурации
- Обработка ошибок

## 🚀 Быстрый старт

### Базовый пример использования

```python
from core.di.container import DIContainer
from core.interfaces import ISerialManager, ICommandExecutor

# Создание DI контейнера
container = DIContainer()

# Получение сервисов
serial_manager = container.resolve(ISerialManager)
command_executor = container.resolve(ICommandExecutor)

# Подключение к устройству
if serial_manager.connect("COM4", baudrate=115200):
    # Выполнение команды
    success = command_executor.execute("test_command")
    print(f"Команда выполнена: {success}")
    
    # Отключение
    serial_manager.disconnect()
```

### Интеграционный пример

```python
from core.di.container import DIContainer
from core.interfaces import (
    ISerialManager, ICommandExecutor, ISequenceManager, 
    IMultizoneManager, IEventBus
)

# Настройка DI контейнера
container = DIContainer()
container.load_config("resources/di_config.toml")

# Получение всех необходимых сервисов
services = {
    'serial': container.resolve(ISerialManager),
    'executor': container.resolve(ICommandExecutor),
    'sequences': container.resolve(ISequenceManager),
    'multizone': container.resolve(IMultizoneManager),
    'events': container.resolve(IEventBus)
}

# Подписка на события
def on_command_executed(data):
    print(f"Команда выполнена: {data}")

services['events'].subscribe('command_executed', on_command_executed)

# Выполнение мультизональной последовательности
if services['serial'].connect("COM4"):
    # Установка зон
    services['multizone'].set_zones([1, 3])
    
    # Выполнение последовательности
    commands = services['sequences'].expand_sequence("test_sequence")
    for command in commands:
        services['executor'].execute(command)
    
    services['serial'].disconnect()
```

## 🔧 Запуск примеров

Все примеры можно запустить напрямую:

```bash
# Запуск конкретного примера
python docs/api/examples/serial_manager_example.py

# Запуск всех примеров
python -m pytest docs/api/examples/ -v
```

## 📝 Структура примеров

Каждый пример содержит:

1. **Импорты и настройка** - подключение необходимых модулей
2. **Базовые примеры** - простые случаи использования
3. **Продвинутые примеры** - сложные сценарии
4. **Обработка ошибок** - примеры обработки исключений
5. **Интеграционные примеры** - взаимодействие с другими сервисами
6. **Тесты** - проверка работоспособности примеров

## 🔗 Связанные документы

- [[docs/api/index|API Reference]] - Полная документация API
- [[docs/architecture/index|Архитектура]] - Понимание архитектуры
- [[docs/guides/development|Руководство разработчика]] - Лучшие практики
- [[docs/tutorials/index|Обучающие материалы]] - Пошаговые уроки

## 📊 Статистика покрытия

- **Всего интерфейсов**: 15
- **Примеров создано**: 15
- **Покрытие методов**: 100%
- **Тестовых случаев**: 45+
- **Интеграционных примеров**: 8

## 🎯 Следующие шаги

После изучения примеров рекомендуется:

1. Изучить [[docs/api/index|полную документацию API]]
2. Ознакомиться с [[docs/architecture/index|архитектурой системы]]
3. Пройти [[docs/tutorials/index|обучающие материалы]]
4. Изучить [[docs/guides/development|руководство разработчика]]
