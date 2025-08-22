"""
DI контейнер для управления зависимостями
"""
import logging
import threading
import inspect
from typing import Dict, List, Optional, Any, Type, Callable, Union
from dataclasses import dataclass, field
from contextlib import contextmanager

from .interfaces import IDIContainer, ServiceRegistration


@dataclass
class ServiceInstance:
    """Экземпляр сервиса в контейнере"""
    registration: ServiceRegistration
    instance: Optional[Any] = None
    factory_instance: Optional[Callable] = None


class DIContainer(IDIContainer):
    """
    Контейнер внедрения зависимостей с поддержкой:
    - Singleton и Transient жизненных циклов
    - Автоматическое разрешение зависимостей
    - Фабричные методы
    - Конфигурация через TOML
    - Thread-safety
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceInstance] = {}
        self._instances: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        self._resolution_stack: List[Type] = []
        self._max_resolution_depth = 50
        
    def register(self, interface: Type, implementation: Type, 
                singleton: bool = True, factory: Optional[Callable] = None,
                dependencies: Optional[Dict[str, str]] = None) -> None:
        """
        Регистрация сервиса в контейнере
        
        Args:
            interface: Интерфейс сервиса
            implementation: Реализация сервиса
            singleton: True для singleton, False для transient
            factory: Фабричная функция для создания экземпляра
            dependencies: Словарь зависимостей {param_name: service_interface}
        """
        with self._lock:
            registration = ServiceRegistration(
                interface=interface,
                implementation=implementation,
                singleton=singleton,
                factory=factory,
                dependencies=dependencies
            )
            
            service_instance = ServiceInstance(registration=registration)
            self._services[interface] = service_instance
            
            self.logger.debug(f"Зарегистрирован сервис: {interface.__name__} -> {implementation.__name__}")
    
    def register_instance(self, interface: Type, instance: Any) -> None:
        """
        Регистрация готового экземпляра сервиса
        
        Args:
            interface: Интерфейс сервиса
            instance: Готовый экземпляр
        """
        with self._lock:
            registration = ServiceRegistration(
                interface=interface,
                implementation=type(instance),
                singleton=True,
                factory=None
            )
            
            service_instance = ServiceInstance(
                registration=registration,
                instance=instance
            )
            self._services[interface] = service_instance
            
            self.logger.debug(f"Зарегистрирован экземпляр: {interface.__name__}")
    
    def resolve(self, interface: Type) -> Any:
        """
        Разрешение зависимости
        
        Args:
            interface: Интерфейс сервиса
            
        Returns:
            Экземпляр сервиса
            
        Raises:
            ValueError: Если сервис не зарегистрирован
            RuntimeError: При циклических зависимостях
        """
        with self._lock:
            return self._resolve_internal(interface)
    
    def _resolve_internal(self, interface: Type) -> Any:
        """Внутренний метод разрешения зависимостей"""
        # Проверяем циклические зависимости
        if interface in self._resolution_stack:
            stack_str = " -> ".join([t.__name__ for t in self._resolution_stack + [interface]])
            raise RuntimeError(f"Обнаружена циклическая зависимость: {stack_str}")
        
        # Проверяем глубину разрешения
        if len(self._resolution_stack) > self._max_resolution_depth:
            raise RuntimeError(f"Превышена максимальная глубина разрешения зависимостей: {self._max_resolution_depth}")
        
        # Проверяем регистрацию сервиса
        if interface not in self._services:
            raise ValueError(f"Сервис {interface.__name__} не зарегистрирован")
        
        service_instance = self._services[interface]
        registration = service_instance.registration
        
        # Для singleton проверяем существующий экземпляр
        if registration.singleton and service_instance.instance is not None:
            return service_instance.instance
        
        # Создаем новый экземпляр
        try:
            self._resolution_stack.append(interface)
            
            if registration.factory:
                # Используем фабричную функцию
                instance = self._create_with_factory(registration)
            else:
                # Используем конструктор
                instance = self._create_with_constructor(registration)
            
            # Для singleton сохраняем экземпляр
            if registration.singleton:
                service_instance.instance = instance
            
            return instance
            
        finally:
            self._resolution_stack.pop()
    
    def _create_with_factory(self, registration: ServiceRegistration) -> Any:
        """Создание экземпляра через фабричную функцию"""
        factory = registration.factory
        
        # Анализируем параметры фабричной функции
        sig = inspect.signature(factory)
        params = {}
        
        for param_name, param in sig.parameters.items():
            if param_name in (registration.dependencies or {}):
                # Разрешаем зависимость по имени
                dependency_interface = registration.dependencies[param_name]
                params[param_name] = self._resolve_internal(dependency_interface)
            elif param.annotation != inspect.Parameter.empty:
                # Разрешаем зависимость по типу
                params[param_name] = self._resolve_internal(param.annotation)
            elif param.default != inspect.Parameter.empty:
                # Используем значение по умолчанию
                params[param_name] = param.default
            else:
                # Обязательный параметр без значения по умолчанию
                raise ValueError(f"Не удалось разрешить параметр {param_name} для фабричной функции")
        
        return factory(**params)
    
    def _create_with_constructor(self, registration: ServiceRegistration) -> Any:
        """Создание экземпляра через конструктор"""
        implementation = registration.implementation
        
        # Анализируем конструктор
        sig = inspect.signature(implementation.__init__)
        params = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            if param_name in (registration.dependencies or {}):
                # Разрешаем зависимость по имени
                dependency_interface = registration.dependencies[param_name]
                params[param_name] = self._resolve_internal(dependency_interface)
            elif param.annotation != inspect.Parameter.empty:
                # Разрешаем зависимость по типу
                params[param_name] = self._resolve_internal(param.annotation)
            elif param.default != inspect.Parameter.empty:
                # Используем значение по умолчанию
                params[param_name] = param.default
            else:
                # Обязательный параметр без значения по умолчанию
                raise ValueError(f"Не удалось разрешить параметр {param_name} для {implementation.__name__}")
        
        return implementation(**params)
    
    def resolve_by_name(self, service_name: str) -> Any:
        """
        Разрешение зависимости по имени
        
        Args:
            service_name: Имя сервиса
            
        Returns:
            Экземпляр сервиса
        """
        with self._lock:
            # Ищем сервис по имени интерфейса
            for interface in self._services.keys():
                if interface.__name__ == service_name:
                    return self._resolve_internal(interface)
            
            raise ValueError(f"Сервис с именем '{service_name}' не найден")
    
    def has_service(self, interface: Type) -> bool:
        """
        Проверка наличия сервиса
        
        Args:
            interface: Интерфейс сервиса
            
        Returns:
            True если сервис зарегистрирован
        """
        with self._lock:
            return interface in self._services
    
    def clear(self) -> None:
        """Очистка контейнера"""
        with self._lock:
            self._services.clear()
            self._instances.clear()
            self._factories.clear()
            self._resolution_stack.clear()
            self.logger.debug("Контейнер очищен")
    
    def get_registered_services(self) -> List[str]:
        """
        Получение списка зарегистрированных сервисов
        
        Returns:
            Список имен зарегистрированных сервисов
        """
        with self._lock:
            return [interface.__name__ for interface in self._services.keys()]
    
    def get_service_info(self, interface: Type) -> Optional[Dict[str, Any]]:
        """
        Получение информации о сервисе
        
        Args:
            interface: Интерфейс сервиса
            
        Returns:
            Словарь с информацией о сервисе или None
        """
        with self._lock:
            if interface not in self._services:
                return None
            
            service_instance = self._services[interface]
            registration = service_instance.registration
            
            return {
                'interface': registration.interface.__name__,
                'implementation': registration.implementation.__name__,
                'singleton': registration.singleton,
                'has_factory': registration.factory is not None,
                'has_instance': service_instance.instance is not None,
                'dependencies': registration.dependencies
            }
    
    @contextmanager
    def scope(self):
        """
        Контекстный менеджер для создания области видимости
        
        Использование:
            with container.scope():
                service = container.resolve(IService)
        """
        # Создаем временный контейнер для области видимости
        temp_container = DIContainer()
        
        # Копируем регистрации
        with self._lock:
            for interface, service_instance in self._services.items():
                temp_container._services[interface] = ServiceInstance(
                    registration=service_instance.registration
                )
        
        try:
            yield temp_container
        finally:
            temp_container.clear()
    
    def configure_from_dict(self, config: Dict[str, Any]) -> None:
        """
        Конфигурация контейнера из словаря
        
        Args:
            config: Словарь конфигурации
        """
        services_config = config.get('services', {})
        
        for service_name, service_config in services_config.items():
            try:
                # Получаем классы из строковых имен
                interface_name = service_config.get('interface')
                implementation_name = service_config.get('implementation')
                
                if not interface_name or not implementation_name:
                    self.logger.warning(f"Пропущена неполная конфигурация сервиса: {service_name}")
                    continue
                
                # Здесь должна быть логика загрузки классов по именам
                # Пока что просто логируем
                self.logger.info(f"Конфигурация сервиса: {interface_name} -> {implementation_name}")
                
            except Exception as e:
                self.logger.error(f"Ошибка конфигурации сервиса {service_name}: {e}")
    
    def validate_registrations(self) -> List[str]:
        """
        Валидация всех регистраций
        
        Returns:
            Список ошибок валидации
        """
        errors = []
        
        with self._lock:
            for interface, service_instance in self._services.items():
                try:
                    # Проверяем возможность создания экземпляра
                    if not service_instance.registration.factory:
                        # Проверяем конструктор
                        sig = inspect.signature(service_instance.registration.implementation.__init__)
                        for param_name, param in sig.parameters.items():
                            if param_name == 'self':
                                continue
                            
                            if (param.annotation == inspect.Parameter.empty and 
                                param.default == inspect.Parameter.empty):
                                errors.append(f"Параметр {param_name} в {interface.__name__} не имеет типа или значения по умолчанию")
                
                except Exception as e:
                    errors.append(f"Ошибка валидации {interface.__name__}: {e}")
        
        return errors


# Глобальный экземпляр контейнера
_container: Optional[DIContainer] = None
_container_lock = threading.Lock()


def get_container() -> DIContainer:
    """
    Получение глобального экземпляра контейнера
    
    Returns:
        Глобальный экземпляр DI контейнера
    """
    global _container
    
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = DIContainer()
    
    return _container


def set_container(container: DIContainer) -> None:
    """
    Установка глобального экземпляра контейнера
    
    Args:
        container: Экземпляр DI контейнера
    """
    global _container
    
    with _container_lock:
        _container = container


def resolve(interface: Type) -> Any:
    """
    Удобная функция для разрешения зависимостей
    
    Args:
        interface: Интерфейс сервиса
        
    Returns:
        Экземпляр сервиса
    """
    return get_container().resolve(interface)


def register(interface: Type, implementation: Type, 
            singleton: bool = True, factory: Optional[Callable] = None,
            dependencies: Optional[Dict[str, str]] = None) -> None:
    """
    Удобная функция для регистрации сервисов
    
    Args:
        interface: Интерфейс сервиса
        implementation: Реализация сервиса
        singleton: True для singleton, False для transient
        factory: Фабричная функция для создания экземпляра
        dependencies: Словарь зависимостей
    """
    get_container().register(interface, implementation, singleton, factory, dependencies)
