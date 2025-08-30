---
title: "Схемы команд"
type: "schema"
audiences: ["backend_dev", "architect"]
tags: ["doc", "lab-equipment-system", "schemas", "commands"]
status: "approved"
last_updated: "2024-12-19"
sources:
  - path: "core/interfaces.py"
    lines: "L200-L300"
    permalink: "https://github.com/lab-equipment-system/blob/main/core/interfaces.py#L200-L300"
related: ["docs/api/commands", "docs/modules/core/command-executor"]
---

> [!info] Навигация
> Родитель: [[docs/schemas]] • Раздел: [[_moc/API]] • См. также: [[docs/api/commands]]

# Схемы команд

## Обзор

Схемы команд определяют структуру данных для команд, отправляемых на лабораторное оборудование, и ответов, получаемых от него.

## Command

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Command",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Уникальный идентификатор команды"
    },
    "type": {
      "type": "string",
      "enum": ["MOVE", "HOME", "STATUS", "STOP", "CUSTOM"],
      "description": "Тип команды"
    },
    "device": {
      "type": "string",
      "enum": ["Multi", "RRight", "Clamp"],
      "description": "Целевое устройство"
    },
    "parameters": {
      "type": "object",
      "description": "Параметры команды",
      "additionalProperties": true
    },
    "timeout": {
      "type": "number",
      "description": "Таймаут выполнения в секундах",
      "default": 10.0
    },
    "retry_attempts": {
      "type": "integer",
      "description": "Количество попыток повторного выполнения",
      "default": 3
    }
  },
  "required": ["id", "type", "device"],
  "additionalProperties": false
}
```

## CommandResult

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CommandResult",
  "type": "object",
  "properties": {
    "command_id": {
      "type": "string",
      "description": "ID исходной команды"
    },
    "success": {
      "type": "boolean",
      "description": "Успешность выполнения"
    },
    "response": {
      "type": "string",
      "description": "Ответ от устройства"
    },
    "error_message": {
      "type": "string",
      "description": "Сообщение об ошибке"
    },
    "execution_time": {
      "type": "number",
      "description": "Время выполнения в секундах"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Временная метка выполнения"
    }
  },
  "required": ["command_id", "success", "timestamp"],
  "additionalProperties": false
}
```

## Sequence

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Sequence",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Уникальный идентификатор последовательности"
    },
    "name": {
      "type": "string",
      "description": "Название последовательности"
    },
    "description": {
      "type": "string",
      "description": "Описание последовательности"
    },
    "commands": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/Command"
      },
      "description": "Список команд в последовательности"
    },
    "metadata": {
      "type": "object",
      "description": "Дополнительные метаданные",
      "additionalProperties": true
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Дата создания"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "Дата последнего обновления"
    }
  },
  "required": ["id", "name", "commands"],
  "additionalProperties": false
}
```

## Примеры

### Команда перемещения

```json
{
  "id": "cmd_001",
  "type": "MOVE",
  "device": "Multi",
  "parameters": {
    "position": 100,
    "speed": 50
  },
  "timeout": 15.0,
  "retry_attempts": 3
}
```

### Команда получения статуса

```json
{
  "id": "cmd_002",
  "type": "STATUS",
  "device": "RRight",
  "parameters": {},
  "timeout": 5.0
}
```

### Результат успешного выполнения

```json
{
  "command_id": "cmd_001",
  "success": true,
  "response": "OK",
  "execution_time": 2.5,
  "timestamp": "2024-12-19T10:30:00Z"
}
```

### Результат с ошибкой

```json
{
  "command_id": "cmd_001",
  "success": false,
  "error_message": "Device not connected",
  "execution_time": 0.1,
  "timestamp": "2024-12-19T10:30:00Z"
}
```

### Последовательность команд

```json
{
  "id": "seq_001",
  "name": "Sample Processing",
  "description": "Обработка образца",
  "commands": [
    {
      "id": "cmd_001",
      "type": "MOVE",
      "device": "Multi",
      "parameters": {"position": 0}
    },
    {
      "id": "cmd_002",
      "type": "MOVE",
      "device": "RRight",
      "parameters": {"position": 50}
    },
    {
      "id": "cmd_003",
      "type": "STATUS",
      "device": "Clamp"
    }
  ],
  "created_at": "2024-12-19T10:00:00Z",
  "updated_at": "2024-12-19T10:00:00Z"
}
```

## Валидация

### Python примеры

```python
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Command:
    id: str
    type: str
    device: str
    parameters: Dict[str, Any] = None
    timeout: float = 10.0
    retry_attempts: int = 3
    
    def validate(self) -> bool:
        """Валидация команды"""
        if self.type not in ["MOVE", "HOME", "STATUS", "STOP", "CUSTOM"]:
            return False
        if self.device not in ["Multi", "RRight", "Clamp"]:
            return False
        if self.timeout <= 0:
            return False
        return True

@dataclass
class CommandResult:
    command_id: str
    success: bool
    response: str = ""
    error_message: str = ""
    execution_time: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
```

## Обработка ошибок

### Типы ошибок

```json
{
  "error_types": {
    "VALIDATION_ERROR": "Ошибка валидации параметров",
    "DEVICE_ERROR": "Ошибка устройства",
    "TIMEOUT_ERROR": "Таймаут операции",
    "CONNECTION_ERROR": "Ошибка подключения",
    "EXECUTION_ERROR": "Ошибка выполнения"
  }
}
```

### Пример обработки

```python
def handle_command_result(result: CommandResult):
    if result.success:
        print(f"Команда {result.command_id} выполнена успешно")
        print(f"Ответ: {result.response}")
    else:
        print(f"Ошибка в команде {result.command_id}")
        print(f"Сообщение: {result.error_message}")
    
    print(f"Время выполнения: {result.execution_time}s")
```