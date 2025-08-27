"""
Разрешение зависимостей в DI контейнере.

Содержит компоненты для:
- Разрешения сервисов по типу
- Создания экземпляров через конструктор
- Создания экземпляров через фабричные функции
- Обработки циклических зависимостей
"""

import logging
import inspect
import time
from typing import Dict, Any, Optional, Type, Callable, List
from contextlib import contextmanager

from .types import ServiceRegistration, ServiceInstance


class DependencyResolver:
    """
    Разрешитель зависимостей для сервисов.
    
    Отвечает за:
    - Анализ параметров конструкторов и фабричных функций
    - Разрешение зависимостей по типу и имени
    - Обработку значений по умолчанию
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def resolve_constructor_dependencies(self, implementation: Type, 
                                      explicit_dependencies: Optional[Dict[str, Type]] = None,
                                      resolve_func: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Разрешение зависимостей для конструктора.
        
        Args:
            implementation: Класс реализации
            explicit_dependencies: Явно указанные зависимости
            resolve_func: Функция для разрешения зависимостей
            
        Returns:
            Словарь параметров для конструктора
            
        Raises:
            ValueError: При невозможности разрешить обязательный параметр
        """
        if not resolve_func:
            raise ValueError("Функция разрешения зависимостей обязательна")
        
        # Анализируем конструктор
        sig = inspect.signature(implementation.__init__)
        params = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # Пытаемся разрешить параметр
            resolved_value = self._resolve_parameter(
                param_name, param, explicit_dependencies, resolve_func
            )
            
            if resolved_value is not None:
                params[param_name] = resolved_value
            elif param.default == inspect.Parameter.empty:
                # Обязательный параметр без значения по умолчанию
                raise ValueError(
                    f"Не удалось разрешить обязательный параметр {param_name} "
                    f"для {implementation.__name__}"
                )
        
        return params
    
    def resolve_factory_dependencies(self, factory: Callable,
                                   explicit_dependencies: Optional[Dict[str, Type]] = None,
                                   resolve_func: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Разрешение зависимостей для фабричной функции.
        
        Args:
            factory: Фабричная функция
            explicit_dependencies: Явно указанные зависимости
            resolve_func: Функция для разрешения зависимостей
            
        Returns:
            Словарь параметров для фабричной функции
            
        Raises:
            ValueError: При невозможности разрешить обязательный параметр
        """
        if not resolve_func:
            raise ValueError("Функция разрешения зависимостей обязательна")
        
        # Анализируем параметры фабричной функции
        sig = inspect.signature(factory)
        params = {}
        
        for param_name, param in sig.parameters.items():
            # Пытаемся разрешить параметр
            resolved_value = self._resolve_parameter(
                param_name, param, explicit_dependencies, resolve_func
            )
            
            if resolved_value is not None:
                params[param_name] = resolved_value
            elif param.default == inspect.Parameter.empty:
                # Обязательный параметр без значения по умолчанию
                raise ValueError(
                    f"Не удалось разрешить обязательный параметр {param_name} "
                    f"для фабричной функции {factory.__name__}"
                )
        
        return params
    
    def _resolve_parameter(self, param_name: str, param: inspect.Parameter,
                          explicit_dependencies: Optional[Dict[str, Type]],
                          resolve_func: Callable) -> Optional[Any]:
        """
        Разрешение отдельного параметра.
        
        Args:
            param_name: Имя параметра
            param: Объект параметра
            explicit_dependencies: Явно указанные зависимости
            resolve_func: Функция для разрешения зависимостей
            
        Returns:
            Разрешенное значение или None
        """
        # 1. Проверяем явно указанные зависимости
        if explicit_dependencies and param_name in explicit_dependencies:
            dependency_interface = explicit_dependencies[param_name]
            try:
                return resolve_func(dependency_interface)
            except Exception as e:
                self.logger.error(
                    f"Ошибка разрешения явной зависимости {param_name}: {e}"
                )
                return None
        
        # 2. Проверяем аннотацию типа
        if param.annotation != inspect.Parameter.empty:
            try:
                return resolve_func(param.annotation)
            except Exception as e:
                self.logger.debug(
                    f"Не удалось разрешить зависимость по типу для {param_name}: {e}"
                )
        
        # 3. Используем значение по умолчанию
        if param.default != inspect.Parameter.empty:
            return param.default
        
        return None


class ServiceResolver:
    """
    Разрешитель сервисов в DI контейнере.
    
    Отвечает за:
    - Создание экземпляров сервисов
    - Управление жизненными циклами
    - Кэширование singleton экземпляров
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.dependency_resolver = DependencyResolver(logger)
        self._max_resolution_depth = 50
    
    def resolve_service(self, service_instance: ServiceInstance,
                       resolve_func: Callable,
                       resolution_stack: List[Type]) -> Any:
        """
        Разрешение сервиса.
        
        Args:
            service_instance: Экземпляр сервиса
            resolve_func: Функция для разрешения зависимостей
            resolution_stack: Стек разрешения для обнаружения циклов
            
        Returns:
            Экземпляр сервиса
            
        Raises:
            RuntimeError: При циклических зависимостях или превышении глубины
        """
        registration = service_instance.registration
        
        # Проверяем циклические зависимости
        if registration.interface in resolution_stack:
            stack_str = " -> ".join([t.__name__ for t in resolution_stack + [registration.interface]])
            raise RuntimeError(f"Обнаружена циклическая зависимость: {stack_str}")
        
        # Проверяем глубину разрешения
        if len(resolution_stack) > self._max_resolution_depth:
            raise RuntimeError(
                f"Превышена максимальная глубина разрешения зависимостей: {self._max_resolution_depth}"
            )
        
        # Для singleton проверяем существующий экземпляр
        if service_instance.can_reuse_instance():
            self._update_access_metrics(service_instance)
            return service_instance.instance
        
        # Создаем новый экземпляр
        try:
            resolution_stack.append(registration.interface)
            
            if registration.factory:
                instance = self._create_with_factory(service_instance, resolve_func, resolution_stack)
            else:
                instance = self._create_with_constructor(service_instance, resolve_func, resolution_stack)
            
            # Обновляем метрики
            self._update_creation_metrics(service_instance)
            
            # Для singleton сохраняем экземпляр
            if service_instance.is_singleton():
                service_instance.instance = instance
            
            return instance
            
        finally:
            resolution_stack.pop()
    
    def _create_with_factory(self, service_instance: ServiceInstance,
                           resolve_func: Callable,
                           resolution_stack: List[Type]) -> Any:
        """Создание экземпляра через фабричную функцию"""
        factory = service_instance.registration.factory
        
        # Разрешаем зависимости фабричной функции
        params = self.dependency_resolver.resolve_factory_dependencies(
            factory, 
            service_instance.registration.dependencies,
            resolve_func
        )
        
        # Вызываем фабричную функцию
        try:
            return factory(**params)
        except Exception as e:
            self.logger.error(f"Ошибка создания экземпляра через фабрику: {e}")
            raise
    
    def _create_with_constructor(self, service_instance: ServiceInstance,
                               resolve_func: Callable,
                               resolution_stack: List[Type]) -> Any:
        """Создание экземпляра через конструктор"""
        implementation = service_instance.registration.implementation
        
        # Разрешаем зависимости конструктора
        params = self.dependency_resolver.resolve_constructor_dependencies(
            implementation,
            service_instance.registration.dependencies,
            resolve_func
        )
        
        # Создаем экземпляр
        try:
            return implementation(**params)
        except Exception as e:
            self.logger.error(f"Ошибка создания экземпляра через конструктор: {e}")
            raise
    
    def _update_access_metrics(self, service_instance: ServiceInstance) -> None:
        """Обновление метрик доступа к сервису"""
        service_instance.last_accessed = time.time()
        service_instance.access_count += 1
    
    def _update_creation_metrics(self, service_instance: ServiceInstance) -> None:
        """Обновление метрик создания сервиса"""
        service_instance.created_at = time.time()
        service_instance.last_accessed = time.time()
        service_instance.access_count += 1

