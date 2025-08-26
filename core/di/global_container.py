"""
Глобальные функции для DI контейнера.

Предоставляет удобные функции для:
- Получения глобального экземпляра контейнера
- Установки глобального контейнера
- Быстрого разрешения зависимостей
- Регистрации сервисов
"""

import threading
from typing import Type, Any, Optional, Callable, Dict

from .container import DIContainer


# Глобальный экземпляр контейнера
_container: Optional[DIContainer] = None
_container_lock = threading.Lock()


def get_container() -> DIContainer:
    """
    Получение глобального экземпляра контейнера.
    
    Returns:
        Глобальный экземпляр DI контейнера
        
    Note:
        Если контейнер не создан, создается новый экземпляр
    """
    global _container
    
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = DIContainer()
    
    return _container


def set_container(container: DIContainer) -> None:
    """
    Установка глобального экземпляра контейнера.
    
    Args:
        container: Экземпляр DI контейнера
        
    Note:
        Позволяет заменить глобальный контейнер на пользовательский
    """
    global _container
    
    with _container_lock:
        _container = container


def resolve(interface: Type) -> Any:
    """
    Удобная функция для разрешения зависимостей.
    
    Args:
        interface: Интерфейс сервиса
        
    Returns:
        Экземпляр сервиса
        
    Raises:
        ValueError: Если сервис не зарегистрирован
        RuntimeError: При циклических зависимостях
        
    Example:
        >>> service = resolve(IService)
        >>> result = service.do_something()
    """
    return get_container().resolve(interface)


def register(interface: Type, implementation: Type, 
            singleton: bool = True, factory: Optional[Callable] = None,
            dependencies: Optional[Dict[str, Type]] = None,
            metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Удобная функция для регистрации сервисов.
    
    Args:
        interface: Интерфейс сервиса
        implementation: Реализация сервиса
        singleton: True для singleton, False для transient
        factory: Фабричная функция для создания экземпляра
        dependencies: Словарь зависимостей {param_name: service_interface}
        metadata: Дополнительные метаданные сервиса
        
    Example:
        >>> register(IService, ServiceImpl, singleton=True)
        >>> register(IFactory, FactoryImpl, factory=create_factory)
    """
    get_container().register(
        interface, implementation, singleton, factory, dependencies, metadata
    )


def register_instance(interface: Type, instance: Any) -> None:
    """
    Удобная функция для регистрации готового экземпляра.
    
    Args:
        interface: Интерфейс сервиса
        instance: Готовый экземпляр
        
    Example:
        >>> config = Config()
        >>> register_instance(IConfig, config)
    """
    get_container().register_instance(interface, instance)


def has_service(interface: Type) -> bool:
    """
    Удобная функция для проверки наличия сервиса.
    
    Args:
        interface: Интерфейс сервиса
        
    Returns:
        True если сервис зарегистрирован
        
    Example:
        >>> if has_service(IService):
        ...     service = resolve(IService)
    """
    return get_container().has_service(interface)


def get_service_info(interface: Type) -> Optional[Dict[str, Any]]:
    """
    Удобная функция для получения информации о сервисе.
    
    Args:
        interface: Интерфейс сервиса
        
    Returns:
        Словарь с информацией о сервисе или None
        
    Example:
        >>> info = get_service_info(IService)
        >>> print(f"Service: {info['interface']} -> {info['implementation']}")
    """
    return get_container().get_service_info(interface)


def get_registered_services() -> list[str]:
    """
    Удобная функция для получения списка зарегистрированных сервисов.
    
    Returns:
        Список имен зарегистрированных сервисов
        
    Example:
        >>> services = get_registered_services()
        >>> print(f"Registered services: {', '.join(services)}")
    """
    return get_container().get_registered_services()


def clear_container() -> None:
    """
    Удобная функция для очистки глобального контейнера.
    
    Note:
        Удаляет все зарегистрированные сервисы и метрики
    """
    get_container().clear()


def validate_container() -> list[str]:
    """
    Удобная функция для валидации всех регистраций.
    
    Returns:
        Список ошибок валидации
        
    Example:
        >>> errors = validate_container()
        >>> if errors:
        ...     print(f"Validation errors: {errors}")
    """
    return get_container().validate_registrations()


def get_performance_report() -> Dict[str, Any]:
    """
    Удобная функция для получения отчета о производительности.
    
    Returns:
        Словарь с метриками производительности
        
    Example:
        >>> report = get_performance_report()
        >>> print(f"Total resolutions: {report['performance']['total_resolutions']}")
    """
    return get_container().get_performance_report()


def configure_from_dict(config: Dict[str, Any]) -> None:
    """
    Удобная функция для конфигурации контейнера из словаря.
    
    Args:
        config: Словарь конфигурации
        
    Example:
        >>> config = {
        ...     'services': {
        ...         'service1': {
        ...             'interface': 'core.interfaces.IService',
        ...             'implementation': 'core.services.ServiceImpl',
        ...             'singleton': True
        ...         }
        ...     }
        ... }
        >>> configure_from_dict(config)
    """
    get_container().configure_from_dict(config)


# Контекстный менеджер для области видимости
def scope():
    """
    Контекстный менеджер для создания области видимости.
    
    Returns:
        Временный контейнер с копией регистраций
        
    Example:
        >>> with scope() as temp_container:
        ...     service = temp_container.resolve(IService)
        ...     # Изменения в temp_container не влияют на глобальный контейнер
    """
    return get_container().scope()
