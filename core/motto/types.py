"""
Базовые типы данных для MOTTO системы

Определяет все структуры данных, используемые в MOTTO стандарте:
- Конфигурации
- Последовательности
- Условия и гварды
- Политики
- Ресурсы
- События
- И другие компоненты
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
from datetime import datetime


class SequenceType(Enum):
    """Типы последовательностей"""
    SEQUENCE = "sequence"
    PARALLEL = "parallel"


class GuardWhen(Enum):
    """Когда выполнять гвард"""
    PRE = "pre"
    POST = "post"


class GuardAction(Enum):
    """Действия при срабатывании гварда"""
    ABORT = "abort"
    RETRY = "retry"
    COOLDOWN_THEN_RETRY = "cooldown_then_retry"
    FALLBACK = "fallback"
    GOTO = "goto"


class ResourceType(Enum):
    """Типы ресурсов"""
    MUTEX = "mutex"
    SEMAPHORE = "semaphore"
    QUOTA = "quota"


class EventSource(Enum):
    """Источники событий"""
    HARDWARE = "hardware"
    SENSOR = "sensor"
    SYSTEM = "system"
    CUSTOM = "custom"


class BarrierType(Enum):
    """Типы барьеров для параллельного выполнения"""
    ALL = "all"
    ANY = "any"


@dataclass
class Profile:
    """Профиль конфигурации"""
    name: str
    extends: Optional[str] = None
    env: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Context:
    """Контекст выполнения"""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Step:
    """Шаг последовательности"""
    command: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout_ms: Optional[int] = None
    can_skip: bool = False
    guards: List[str] = field(default_factory=list)
    locks: List[str] = field(default_factory=list)
    on_fail: Optional[Dict[str, Any]] = None


@dataclass
class Sequence:
    """Последовательность команд"""
    name: str
    description: str = ""
    type: SequenceType = SequenceType.SEQUENCE
    inputs: Dict[str, str] = field(default_factory=dict)  # name -> type
    defaults: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)  # name -> type
    steps: List[str] = field(default_factory=list)  # Ссылки на команды или другие последовательности
    policy: Optional[str] = None
    guards: List[str] = field(default_factory=list)
    post_checks: List[str] = field(default_factory=list)
    
    # Для параллельных последовательностей
    branches: List[Dict[str, Any]] = field(default_factory=list)
    barrier: BarrierType = BarrierType.ALL
    
    # Для транзакций
    transaction: Optional[Dict[str, str]] = None  # begin, commit, rollback
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Condition:
    """Условие для проверки"""
    name: str
    expr: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Guard:
    """Гвард для проверки условий"""
    name: str
    when: GuardWhen
    condition: str  # Ссылка на условие
    on_fail: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Policy:
    """Политика выполнения"""
    name: str
    retry_on: List[str] = field(default_factory=list)
    max_attempts: int = 3
    backoff: Dict[str, Any] = field(default_factory=dict)
    step_timeout_ms: int = 60000
    sequence_timeout_ms: int = 600000
    idempotency_key: Optional[str] = None
    transaction: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Resource:
    """Ресурс для управления"""
    name: str
    type: ResourceType
    members: List[str] = field(default_factory=list)
    capacity: Optional[int] = None
    scope: str = "machine"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Event:
    """Событие системы"""
    name: str
    source: EventSource
    filter: str  # Выражение для фильтрации
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Handler:
    """Обработчик событий"""
    name: str
    on: str  # Ссылка на событие
    do: List[str] = field(default_factory=list)  # Ссылки на команды/последовательности
    priority: int = 0
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Template:
    """Шаблон для генерации"""
    name: str
    for_type: str  # "commands" или "sequences"
    matrix: List[Dict[str, Any]] = field(default_factory=list)
    args: List[str] = field(default_factory=list)
    pattern: Dict[str, Any] = field(default_factory=dict)
    expand: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Validator:
    """Валидатор значений"""
    name: str
    key: str  # Ключ для валидации
    range: Optional[Dict[str, Any]] = None
    pattern: Optional[str] = None
    custom_expr: Optional[str] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Контекст выполнения"""
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sequence_name: str = ""
    profile: Optional[str] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Результат выполнения"""
    success: bool
    sequence_name: str
    run_id: str
    start_time: datetime
    end_time: datetime
    duration_ms: int
    steps_executed: int
    steps_total: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    """Результат выполнения шага"""
    success: bool
    step_index: int
    step_name: str
    command: str
    start_time: datetime
    end_time: datetime
    duration_ms: int
    response: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GuardResult:
    """Результат проверки гварда"""
    passed: bool
    guard_name: str
    condition_name: str
    when: GuardWhen
    evaluated_at: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    action: Optional[GuardAction] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Результат валидации"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceStatus:
    """Статус ресурса"""
    name: str
    type: ResourceType
    available: bool
    current_holders: List[str] = field(default_factory=list)
    waiting_queue: List[str] = field(default_factory=list)
    capacity: Optional[int] = None
    used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Operation:
    """Операция для аудита"""
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str = ""
    sequence_name: str = ""
    step_name: str = ""
    run_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    user: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    duration_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Trace:
    """Трассировка выполнения"""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = ""
    sequence_name: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    steps: List[StepResult] = field(default_factory=list)
    guards: List[GuardResult] = field(default_factory=list)
    operations: List[Operation] = field(default_factory=list)
    context_snapshots: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MOTTOConfig:
    """Основная конфигурация MOTTO"""
    version: str = "1.1"
    vars: Dict[str, Any] = field(default_factory=dict)
    profiles: Dict[str, Profile] = field(default_factory=dict)
    contexts: Dict[str, Context] = field(default_factory=dict)
    sequences: Dict[str, Sequence] = field(default_factory=dict)
    conditions: Dict[str, Condition] = field(default_factory=dict)
    guards: Dict[str, Guard] = field(default_factory=dict)
    policies: Dict[str, Policy] = field(default_factory=dict)
    resources: Dict[str, Resource] = field(default_factory=dict)
    events: Dict[str, Event] = field(default_factory=dict)
    handlers: Dict[str, Handler] = field(default_factory=dict)
    templates: Dict[str, Template] = field(default_factory=dict)
    units: Dict[str, List[str]] = field(default_factory=dict)
    validators: Dict[str, Validator] = field(default_factory=dict)
    
    # Runtime конфигурация
    runtime: Dict[str, Any] = field(default_factory=dict)
    audit: Dict[str, Any] = field(default_factory=dict)
    
    metadata: Dict[str, Any] = field(default_factory=dict)