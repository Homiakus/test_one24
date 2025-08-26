"""
Типы для системы Dependency Injection.

Содержит базовые классы и перечисления для:
- Регистрации сервисов
- Жизненных циклов
- Экземпляров сервисов
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, Type, Callable


class ServiceLifecycle(Enum):
    """Жизненные циклы сервисов"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceRegistration:
    """
    Регистрация сервиса в DI контейнере.
    
    Attributes:
        interface: Интерфейс сервиса
        implementation: Реализация сервиса
        lifecycle: Жизненный цикл сервиса
        factory: Фабричная функция для создания экземпляра
        dependencies: Словарь зависимостей {param_name: service_interface}
        metadata: Дополнительные метаданные сервиса
    """
    interface: Type
    implementation: Type
    lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON
    factory: Optional[Callable] = None
    dependencies: Optional[Dict[str, Type]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Валидация после инициализации"""
        if self.interface == self.implementation:
            raise ValueError("Интерфейс и реализация не могут быть одинаковыми")
        
        if self.factory and not callable(self.factory):
            raise ValueError("Фабричная функция должна быть вызываемой")
        
        if self.dependencies and not isinstance(self.dependencies, dict):
            raise ValueError("Зависимости должны быть словарем")


@dataclass
class ServiceInstance:
    """
    Экземпляр сервиса в DI контейнере.
    
    Attributes:
        registration: Регистрация сервиса
        instance: Созданный экземпляр (для singleton)
        factory_instance: Экземпляр фабрики
        created_at: Время создания экземпляра
        last_accessed: Время последнего обращения
        access_count: Количество обращений к сервису
    """
    registration: ServiceRegistration
    instance: Optional[Any] = None
    factory_instance: Optional[Callable] = None
    created_at: Optional[float] = None
    last_accessed: Optional[float] = None
    access_count: int = 0
    
    def has_instance(self) -> bool:
        """Проверка наличия созданного экземпляра"""
        return self.instance is not None
    
    def is_singleton(self) -> bool:
        """Проверка является ли сервис singleton"""
        return self.registration.lifecycle == ServiceLifecycle.SINGLETON
    
    def can_reuse_instance(self) -> bool:
        """Проверка возможности повторного использования экземпляра"""
        return self.is_singleton() and self.has_instance()
