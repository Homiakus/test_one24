"""
Валидация сервисов в DI контейнере.

Содержит компоненты для:
- Валидации регистраций сервисов
- Проверки зависимостей
- Валидации конфигурации
- Обнаружения проблем в рантайме
"""

import logging
import inspect
from typing import Dict, List, Any, Type, Optional, Set
from dataclasses import dataclass

from .types import ServiceRegistration, ServiceInstance


@dataclass
class ValidationResult:
    """
    Результат валидации сервиса.
    
    Attributes:
        is_valid: True если валидация прошла успешно
        errors: Список ошибок валидации
        warnings: Список предупреждений
        service_name: Имя проверяемого сервиса
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    service_name: str
    
    def __post_init__(self):
        """Автоматическое определение валидности по наличию ошибок"""
        if self.is_valid is None:
            self.is_valid = len(self.errors) == 0


class ServiceValidator:
    """
    Валидатор сервисов в DI контейнере.
    
    Отвечает за:
    - Валидацию регистраций сервисов
    - Проверку корректности зависимостей
    - Валидацию конфигурации
    - Обнаружение потенциальных проблем
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def validate_registration(self, registration: ServiceRegistration) -> ValidationResult:
        """
        Валидация регистрации сервиса.
        
        Args:
            registration: Регистрация сервиса для валидации
            
        Returns:
            Результат валидации
        """
        errors = []
        warnings = []
        service_name = registration.interface.__name__
        
        # Проверяем базовые требования
        if not self._validate_basic_requirements(registration, errors):
            return ValidationResult(False, errors, warnings, service_name)
        
        # Проверяем конструктор
        if not registration.factory:
            constructor_errors = self._validate_constructor(registration)
            errors.extend(constructor_errors)
        
        # Проверяем фабричную функцию
        if registration.factory:
            factory_errors = self._validate_factory(registration)
            errors.extend(factory_errors)
        
        # Проверяем зависимости
        dependency_errors = self._validate_dependencies(registration)
        errors.extend(dependency_errors)
        
        # Проверяем потенциальные проблемы
        potential_warnings = self._check_potential_issues(registration)
        warnings.extend(potential_warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            service_name=service_name
        )
    
    def validate_all_registrations(self, services: Dict[Type, ServiceInstance]) -> List[ValidationResult]:
        """
        Валидация всех зарегистрированных сервисов.
        
        Args:
            services: Словарь зарегистрированных сервисов
            
        Returns:
            Список результатов валидации
        """
        results = []
        
        for interface, service_instance in services.items():
            try:
                result = self.validate_registration(service_instance.registration)
                results.append(result)
                
                if not result.is_valid:
                    self.logger.error(
                        f"Ошибки валидации для {result.service_name}: {result.errors}"
                    )
                elif result.warnings:
                    self.logger.warning(
                        f"Предупреждения для {result.service_name}: {result.warnings}"
                    )
                    
            except Exception as e:
                self.logger.error(f"Ошибка валидации {interface.__name__}: {e}")
                results.append(ValidationResult(
                    False, 
                    [f"Критическая ошибка валидации: {e}"], 
                    [], 
                    interface.__name__
                ))
        
        return results
    
    def _validate_basic_requirements(self, registration: ServiceRegistration, 
                                   errors: List[str]) -> bool:
        """Проверка базовых требований к регистрации"""
        # Проверяем, что интерфейс и реализация не одинаковые
        if registration.interface == registration.implementation:
            errors.append("Интерфейс и реализация не могут быть одинаковыми")
            return False
        
        # Проверяем, что интерфейс является типом
        if not isinstance(registration.interface, type):
            errors.append("Интерфейс должен быть типом")
            return False
        
        # Проверяем, что реализация является типом
        if not isinstance(registration.implementation, type):
            errors.append("Реализация должна быть типом")
            return False
        
        # Проверяем, что реализация наследует интерфейс
        if not issubclass(registration.implementation, registration.interface):
            errors.append(
                f"Реализация {registration.implementation.__name__} "
                f"должна наследовать интерфейс {registration.interface.__name__}"
            )
            return False
        
        return True
    
    def _validate_constructor(self, registration: ServiceRegistration) -> List[str]:
        """Валидация конструктора реализации"""
        errors = []
        implementation = registration.implementation
        
        try:
            # Проверяем наличие конструктора
            if not hasattr(implementation, '__init__'):
                errors.append("Класс должен иметь конструктор")
                return errors
            
            # Анализируем параметры конструктора
            sig = inspect.signature(implementation.__init__)
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                # Проверяем, что параметр имеет тип или значение по умолчанию
                if (param.annotation == inspect.Parameter.empty and 
                    param.default == inspect.Parameter.empty):
                    errors.append(
                        f"Параметр {param_name} должен иметь тип или значение по умолчанию"
                    )
                
                # Проверяем, что параметр не является self
                if param_name == 'self':
                    errors.append("Параметр не может называться 'self'")
            
        except Exception as e:
            errors.append(f"Ошибка анализа конструктора: {e}")
        
        return errors
    
    def _validate_factory(self, registration: ServiceRegistration) -> List[str]:
        """Валидация фабричной функции"""
        errors = []
        factory = registration.factory
        
        if not callable(factory):
            errors.append("Фабричная функция должна быть вызываемой")
            return errors
        
        try:
            # Анализируем параметры фабричной функции
            sig = inspect.signature(factory)
            
            for param_name, param in sig.parameters.items():
                # Проверяем, что параметр имеет тип или значение по умолчанию
                if (param.annotation == inspect.Parameter.empty and 
                    param.default == inspect.Parameter.empty):
                    errors.append(
                        f"Параметр фабричной функции {param_name} должен иметь тип или значение по умолчанию"
                    )
            
        except Exception as e:
            errors.append(f"Ошибка анализа фабричной функции: {e}")
        
        return errors
    
    def _validate_dependencies(self, registration: ServiceRegistration) -> List[str]:
        """Валидация зависимостей"""
        errors = []
        dependencies = registration.dependencies
        
        if not dependencies:
            return errors
        
        if not isinstance(dependencies, dict):
            errors.append("Зависимости должны быть словарем")
            return errors
        
        for param_name, dependency_type in dependencies.items():
            # Проверяем, что имя параметра является строкой
            if not isinstance(param_name, str):
                errors.append(f"Имя параметра зависимости должно быть строкой: {param_name}")
                continue
            
            # Проверяем, что тип зависимости является типом
            if not isinstance(dependency_type, type):
                errors.append(f"Тип зависимости должен быть типом: {dependency_type}")
                continue
            
            # Проверяем, что параметр существует в конструкторе/фабрике
            if not self._parameter_exists(registration, param_name):
                errors.append(
                    f"Параметр зависимости {param_name} не найден в конструкторе/фабрике"
                )
        
        return errors
    
    def _parameter_exists(self, registration: ServiceRegistration, param_name: str) -> bool:
        """Проверка существования параметра в конструкторе или фабрике"""
        try:
            if registration.factory:
                sig = inspect.signature(registration.factory)
            else:
                sig = inspect.signature(registration.implementation.__init__)
            
            return param_name in sig.parameters
            
        except Exception:
            return False
    
    def _check_potential_issues(self, registration: ServiceRegistration) -> List[str]:
        """Проверка потенциальных проблем"""
        warnings = []
        
        # Проверяем, не является ли сервис слишком большим
        if hasattr(registration.implementation, '__init__'):
            sig = inspect.signature(registration.implementation.__init__)
            param_count = len([p for p in sig.parameters.values() if p.name != 'self'])
            
            if param_count > 10:
                warnings.append(
                    f"Конструктор имеет много параметров ({param_count}), "
                    "рассмотрите использование Builder паттерна"
                )
        
        # Проверяем, не является ли фабричная функция слишком сложной
        if registration.factory:
            try:
                sig = inspect.signature(registration.factory)
                param_count = len(sig.parameters)
                
                if param_count > 5:
                    warnings.append(
                        f"Фабричная функция имеет много параметров ({param_count}), "
                        "рассмотрите упрощение"
                    )
            except Exception:
                pass
        
        return warnings
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """
        Валидация конфигурации DI контейнера.
        
        Args:
            config: Конфигурация для валидации
            
        Returns:
            Список ошибок валидации
        """
        errors = []
        
        if not isinstance(config, dict):
            errors.append("Конфигурация должна быть словарем")
            return errors
        
        services_config = config.get('services', {})
        
        if not isinstance(services_config, dict):
            errors.append("Секция 'services' должна быть словарем")
            return errors
        
        for service_name, service_config in services_config.items():
            if not isinstance(service_config, dict):
                errors.append(f"Конфигурация сервиса {service_name} должна быть словарем")
                continue
            
            # Проверяем обязательные поля
            required_fields = ['interface', 'implementation']
            for field in required_fields:
                if field not in service_config:
                    errors.append(f"Сервис {service_name} должен содержать поле '{field}'")
                    continue
                
                if not isinstance(service_config[field], str):
                    errors.append(f"Поле '{field}' сервиса {service_name} должно быть строкой")
            
            # Проверяем опциональные поля
            if 'singleton' in service_config:
                if not isinstance(service_config['singleton'], bool):
                    errors.append(f"Поле 'singleton' сервиса {service_name} должно быть булевым")
            
            if 'dependencies' in service_config:
                if not isinstance(service_config['dependencies'], dict):
                    errors.append(f"Поле 'dependencies' сервиса {service_name} должно быть словарем")
        
        return errors

