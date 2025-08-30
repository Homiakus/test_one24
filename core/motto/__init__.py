"""
MOTTO (Machine Orchestration in TOML) - Расширенная система оркестрации процессов

Этот модуль предоставляет полную поддержку стандарта MOTTO v1.1 для управления
лабораторным оборудованием с возможностями:
- Параметризуемых последовательностей
- Условий и гвардов
- Ретраев и идемпотентности
- Ресурсов и мьютексов
- Событий и обработчиков
- Параллельного выполнения
- Транзакций
- Юнитов и валидации
- Шаблонов и макросов
- Аудита и телеметрии
"""

from .types import (
    MOTTOConfig,
    Sequence,
    Condition,
    Guard,
    Policy,
    Resource,
    Event,
    Handler,
    Template,
    Validator,
    Profile,
    Context,
    ExecutionContext,
    ExecutionResult,
    StepResult,
    GuardResult,
    ValidationResult,
    ResourceStatus,
    Operation,
    Trace
)

from .parser import MOTTOParser
from .validator import MOTTOValidator
from .executor import MOTTOExecutor
from .guards import GuardSystem
from .resources import ResourceManager
from .events import EventSystem
from .templates import TemplateEngine
from .policies import PolicyManager
from .audit import AuditSystem
from .compatibility import CompatibilityAdapter

__version__ = "1.1.0"
__author__ = "MOTTO Team"

__all__ = [
    # Types
    "MOTTOConfig",
    "Sequence", 
    "Condition",
    "Guard",
    "Policy",
    "Resource",
    "Event",
    "Handler",
    "Template",
    "Validator",
    "Profile",
    "Context",
    "ExecutionContext",
    "ExecutionResult",
    "StepResult",
    "GuardResult",
    "ValidationResult",
    "ResourceStatus",
    "Operation",
    "Trace",
    
    # Components
    "MOTTOParser",
    "MOTTOValidator",
    "MOTTOExecutor",
    "GuardSystem",
    "ResourceManager",
    "EventSystem",
    "TemplateEngine",
    "PolicyManager",
    "AuditSystem",
    "CompatibilityAdapter",
]