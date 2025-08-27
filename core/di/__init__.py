"""
Пакет для управления зависимостями (Dependency Injection).

Этот пакет содержит компоненты для:
- Регистрации и разрешения сервисов
- Управления жизненными циклами (Singleton/Transient)
- Валидации зависимостей
- Метрик и мониторинга
- Конфигурации через TOML
"""

from .types import ServiceRegistration, ServiceInstance, ServiceLifecycle
from .resolver import ServiceResolver, DependencyResolver
from .validator import ServiceValidator, ValidationResult
from .metrics import DIMetrics, ServiceMetrics
from .container import DIContainer
from .global_container import get_container, set_container, resolve, register

__all__ = [
    # Основные типы
    'ServiceRegistration',
    'ServiceInstance', 
    'ServiceLifecycle',
    
    # Компоненты разрешения
    'ServiceResolver',
    'DependencyResolver',
    
    # Валидация
    'ServiceValidator',
    'ValidationResult',
    
    # Метрики
    'DIMetrics',
    'ServiceMetrics',
    
    # Основной контейнер
    'DIContainer',
    
    # Глобальные функции
    'get_container',
    'set_container', 
    'resolve',
    'register'
]

