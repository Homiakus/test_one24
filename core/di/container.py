"""
Основной DI контейнер.

Объединяет все компоненты для:
- Регистрации и разрешения сервисов
- Управления жизненными циклами
- Валидации и метрик
- Конфигурации через TOML
"""

import logging
import threading
import importlib
import re
from typing import Dict, List, Optional, Any, Type, Callable, Union
from contextlib import contextmanager

from .types import ServiceRegistration, ServiceInstance, ServiceLifecycle
from .resolver import ServiceResolver
from .validator import ServiceValidator
from .metrics import DIMetrics


class ConfigurationSecurityError(Exception):
    """Исключение для ошибок безопасности конфигурации"""
    pass


class TOMLValidator:
    """Валидатор TOML конфигурации для безопасности"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Запрещенные паттерны для безопасности
        self.forbidden_patterns = [
            r'__import__',
            r'eval\s*\(',
            r'exec\s*\(',
            r'open\s*\(',
            r'file\s*\(',
            r'input\s*\(',
            r'raw_input\s*\(',
            r'compile\s*\(',
            r'globals\s*\(',
            r'locals\s*\(',
            r'vars\s*\(',
            r'dir\s*\(',
            r'getattr\s*\(',
            r'setattr\s*\(',
            r'delattr\s*\(',
            r'hasattr\s*\(',
            r'isinstance\s*\(',
            r'issubclass\s*\(',
            r'super\s*\(',
            r'property\s*\(',
            r'staticmethod\s*\(',
            r'classmethod\s*\(',
            r'type\s*\(',
            r'object\s*\(',
            r'str\s*\(',
            r'int\s*\(',
            r'float\s*\(',
            r'bool\s*\(',
            r'list\s*\(',
            r'dict\s*\(',
            r'set\s*\(',
            r'tuple\s*\(',
            r'frozenset\s*\(',
            r'bytes\s*\(',
            r'bytearray\s*\(',
            r'memoryview\s*\(',
            r'complex\s*\(',
            r'range\s*\(',
            r'enumerate\s*\(',
            r'filter\s*\(',
            r'map\s*\(',
            r'zip\s*\(',
            r'reversed\s*\(',
            r'sorted\s*\(',
            r'any\s*\(',
            r'all\s*\(',
            r'sum\s*\(',
            r'min\s*\(',
            r'max\s*\(',
            r'abs\s*\(',
            r'round\s*\(',
            r'pow\s*\(',
            r'divmod\s*\(',
            r'len\s*\(',
            r'hash\s*\(',
            r'id\s*\(',
            r'ord\s*\(',
            r'chr\s*\(',
            r'bin\s*\(',
            r'oct\s*\(',
            r'hex\s*\(',
            r'ascii\s*\(',
            r'repr\s*\(',
            r'format\s*\(',
            r'print\s*\(',
            r'breakpoint\s*\(',
        ]
        
        # Компилируем запрещенные паттерны
        self.forbidden_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.forbidden_patterns]
        
        # Максимальные лимиты для безопасности
        self.max_config_size = 1024 * 1024  # 1MB
        self.max_nesting_depth = 10
        self.max_array_size = 1000
        self.max_string_length = 10000
    
    def validate_toml_content(self, content: str) -> bool:
        """
        Валидировать содержимое TOML на безопасность.
        
        Args:
            content: Содержимое TOML файла
            
        Returns:
            True если конфигурация безопасна
            
        Raises:
            ConfigurationSecurityError: При обнаружении небезопасных паттернов
        """
        # Проверяем размер конфигурации
        if len(content) > self.max_config_size:
            raise ConfigurationSecurityError(f"Конфигурация слишком большая: {len(content)} > {self.max_config_size}")
        
        # Проверяем на запрещенные паттерны
        for pattern in self.forbidden_regex:
            if pattern.search(content):
                raise ConfigurationSecurityError(f"Обнаружен запрещенный паттерн: {pattern.pattern}")
        
        # Проверяем длину строк
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > self.max_string_length:
                raise ConfigurationSecurityError(f"Строка {i} слишком длинная: {len(line)} > {self.max_string_length}")
        
        # Проверяем глубину вложенности (примерно по отступам)
        max_depth = 0
        current_depth = 0
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            if stripped.startswith('['):
                current_depth = 0
            elif stripped.startswith('['):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
        
        if max_depth > self.max_nesting_depth:
            raise ConfigurationSecurityError(f"Слишком глубокая вложенность: {max_depth} > {self.max_nesting_depth}")
        
        self.logger.info("TOML конфигурация прошла проверку безопасности")
        return True
    
    def validate_toml_file(self, file_path: str) -> bool:
        """
        Валидировать TOML файл на безопасность.
        
        Args:
            file_path: Путь к TOML файлу
            
        Returns:
            True если файл безопасен
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.validate_toml_content(content)
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации TOML файла {file_path}: {e}")
            raise ConfigurationSecurityError(f"Ошибка валидации TOML файла: {e}")


class DIContainer:
    """
    Контейнер внедрения зависимостей с поддержкой:
    - Singleton и Transient жизненных циклов
    - Автоматическое разрешение зависимостей
    - Фабричные методы
    - Конфигурация через TOML
    - Thread-safety
    - Валидация и метрики
    - Безопасность конфигурации
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._services: Dict[Type, ServiceInstance] = {}
        self._lock = threading.RLock()
        
        # Компоненты
        self._resolver = ServiceResolver(self.logger)
        self._validator = ServiceValidator(self.logger)
        self._metrics = DIMetrics(self.logger)
        self._toml_validator = TOMLValidator()
        
        # Стек разрешения для обнаружения циклов
        self._resolution_stack: List[Type] = []
        
        # Настройки безопасности
        self._security_enabled = True
        self._max_services = 1000
        self._max_dependencies = 50
    
    def register(self, interface: Type, implementation: Type, 
                singleton: bool = True, factory: Optional[Callable] = None,
                dependencies: Optional[Dict[str, Type]] = None,
                metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Регистрация сервиса в контейнере.
        
        Args:
            interface: Интерфейс сервиса
            implementation: Реализация сервиса
            singleton: True для singleton, False для transient
            factory: Фабричная функция для создания экземпляра
            dependencies: Словарь зависимостей {param_name: service_interface}
            metadata: Дополнительные метаданные сервиса
        """
        with self._lock:
            # Определяем жизненный цикл
            lifecycle = ServiceLifecycle.SINGLETON if singleton else ServiceLifecycle.TRANSIENT
            
            # Создаем регистрацию
            registration = ServiceRegistration(
                interface=interface,
                implementation=implementation,
                lifecycle=lifecycle,
                factory=factory,
                dependencies=dependencies,
                metadata=metadata or {}
            )
            
            # Валидируем безопасность регистрации
            if not self.validate_service_security(registration):
                error_msg = f"Ошибка безопасности сервиса {interface.__name__}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Валидируем регистрацию
            validation_result = self._validator.validate_registration(registration)
            if not validation_result.is_valid:
                error_msg = f"Ошибка валидации сервиса {interface.__name__}: {validation_result.errors}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Создаем экземпляр сервиса
            service_instance = ServiceInstance(registration=registration)
            self._services[interface] = service_instance
            
            # Регистрируем в метриках
            self._metrics.register_service(interface, service_instance)
            
            self.logger.debug(f"Зарегистрирован сервис: {interface.__name__} -> {implementation.__name__}")
            
            # Логируем предупреждения если есть
            if validation_result.warnings:
                self.logger.warning(f"Предупреждения для {interface.__name__}: {validation_result.warnings}")
    
    def register_instance(self, interface: Type, instance: Any) -> None:
        """
        Регистрация готового экземпляра сервиса.
        
        Args:
            interface: Интерфейс сервиса
            instance: Готовый экземпляр
        """
        with self._lock:
            registration = ServiceRegistration(
                interface=interface,
                implementation=type(instance),
                lifecycle=ServiceLifecycle.SINGLETON,
                factory=None
            )
            
            # Валидируем безопасность регистрации
            if not self.validate_service_security(registration):
                error_msg = f"Ошибка безопасности экземпляра {interface.__name__}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            service_instance = ServiceInstance(
                registration=registration,
                instance=instance
            )
            self._services[interface] = service_instance
            
            # Регистрируем в метриках
            self._metrics.register_service(interface, service_instance)
            
            self.logger.debug(f"Зарегистрирован экземпляр: {interface.__name__}")
    
    def resolve(self, interface: Type) -> Any:
        """
        Разрешение зависимости.
        
        Args:
            interface: Интерфейс сервиса
            
        Returns:
            Экземпляр сервиса
            
        Raises:
            ValueError: Если сервис не зарегистрирован
            RuntimeError: При циклических зависимостях
        """
        with self._lock:
            # Проверяем регистрацию сервиса
            if interface not in self._services:
                raise ValueError(f"Сервис {interface.__name__} не зарегистрирован")
            
            # Записываем начало разрешения
            start_time = self._metrics.record_resolution_start(interface)
            
            try:
                # Разрешаем сервис
                service_instance = self._services[interface]
                instance = self._resolver.resolve_service(
                    service_instance, 
                    self._resolve_internal, 
                    self._resolution_stack
                )
                
                # Записываем успешное завершение
                self._metrics.record_resolution_complete(
                    interface, start_time, success=True
                )
                
                return instance
                
            except Exception as e:
                # Записываем ошибку
                error_msg = str(e)
                self._metrics.record_resolution_complete(
                    interface, start_time, success=False, error=error_msg
                )
                raise
    
    def _resolve_internal(self, interface: Type) -> Any:
        """Внутренний метод разрешения зависимостей"""
        # Проверяем регистрацию сервиса
        if interface not in self._services:
            raise ValueError(f"Сервис {interface.__name__} не зарегистрирован")
        
        service_instance = self._services[interface]
        
        # Для singleton проверяем существующий экземпляр
        if service_instance.can_reuse_instance():
            return service_instance.instance
        
        # Создаем новый экземпляр через резолвер
        instance = self._resolver.resolve_service(
            service_instance, 
            self._resolve_internal, 
            self._resolution_stack
        )
        
        # Для singleton сохраняем экземпляр
        if service_instance.is_singleton():
            service_instance.instance = instance
        
        return instance
    
    def resolve_by_name(self, service_name: str) -> Any:
        """
        Разрешение зависимости по имени.
        
        Args:
            service_name: Имя сервиса
            
        Returns:
            Экземпляр сервиса
        """
        with self._lock:
            # Ищем сервис по имени интерфейса
            for interface in self._services.keys():
                if interface.__name__ == service_name:
                    return self.resolve(interface)
            
            raise ValueError(f"Сервис с именем '{service_name}' не найден")
    
    def has_service(self, interface: Type) -> bool:
        """
        Проверка наличия сервиса.
        
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
            self._resolution_stack.clear()
            self._metrics.reset_metrics()
            self.logger.debug("Контейнер очищен")
    
    def get_registered_services(self) -> List[str]:
        """
        Получение списка зарегистрированных сервисов.
        
        Returns:
            Список имен зарегистрированных сервисов
        """
        with self._lock:
            return [interface.__name__ for interface in self._services.keys()]
    
    def get_service_info(self, interface: Type) -> Optional[Dict[str, Any]]:
        """
        Получение информации о сервисе.
        
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
                'lifecycle': registration.lifecycle.value,
                'has_factory': registration.factory is not None,
                'has_instance': service_instance.has_instance(),
                'dependencies': registration.dependencies,
                'metadata': registration.metadata
            }
    
    @contextmanager
    def scope(self):
        """
        Контекстный менеджер для создания области видимости.
        
        Использование:
            with container.scope():
                service = container.resolve(IService)
        """
        # Создаем временный контейнер для области видимости
        temp_container = DIContainer(self.logger)
        
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
        Конфигурация контейнера из словаря.
        
        Args:
            config: Словарь конфигурации
        """
        # Валидируем конфигурацию
        config_errors = self._validator.validate_configuration(config)
        if config_errors:
            error_msg = f"Ошибки конфигурации: {config_errors}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        services_config = config.get('services', {})
        
        for service_name, service_config in services_config.items():
            try:
                # Получаем классы из строковых имен
                interface_name = service_config.get('interface')
                implementation_name = service_config.get('implementation')
                
                # Загружаем классы по именам
                interface_class = self._load_class_by_name(interface_name)
                implementation_class = self._load_class_by_name(implementation_name)
                
                if not interface_class or not implementation_class:
                    self.logger.error(f"Не удалось загрузить классы для сервиса: {service_name}")
                    continue
                
                # Получаем дополнительные параметры
                singleton = service_config.get('singleton', True)
                dependencies = service_config.get('dependencies', {})
                metadata = service_config.get('metadata', {})
                
                # Регистрируем сервис
                self.register(
                    interface_class, 
                    implementation_class, 
                    singleton=singleton, 
                    dependencies=dependencies,
                    metadata=metadata
                )
                self.logger.info(f"Зарегистрирован сервис: {interface_name} -> {implementation_name}")
                
            except Exception as e:
                self.logger.error(f"Ошибка конфигурации сервиса {service_name}: {e}")
    
    def _load_class_by_name(self, class_name: str) -> Optional[Type]:
        """
        Загрузка класса по имени.
        
        Args:
            class_name: Полное имя класса (например, 'core.multizone_manager.MultizoneManager')
            
        Returns:
            Класс или None при ошибке
        """
        try:
            if '.' in class_name:
                # Полное имя с модулем
                module_name, class_name_only = class_name.rsplit('.', 1)
                module = importlib.import_module(module_name)
                return getattr(module, class_name_only)
            else:
                # Только имя класса - ищем в известных модулях
                known_modules = [
                    'core.multizone_manager',
                    'core.interfaces',
                    'core.sequences',
                    'core.communication',
                    'core.command_executor'
                ]
                
                for module_name in known_modules:
                    try:
                        module = importlib.import_module(module_name)
                        if hasattr(module, class_name):
                            return getattr(module, class_name)
                    except ImportError:
                        continue
                
                self.logger.error(f"Класс {class_name} не найден в известных модулях")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка загрузки класса {class_name}: {e}")
            return None
    
    def validate_registrations(self) -> List[str]:
        """
        Валидация всех регистраций.
        
        Returns:
            Список ошибок валидации
        """
        with self._lock:
            validation_results = self._validator.validate_all_registrations(self._services)
            
            errors = []
            for result in validation_results:
                if not result.is_valid:
                    errors.extend(result.errors)
            
            return errors
    
    def get_metrics(self) -> DIMetrics:
        """Получение системы метрик"""
        return self._metrics
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Получение отчета о производительности"""
        return {
            'performance': self._metrics.get_performance_summary(),
            'errors': self._metrics.get_error_summary(),
            'services': self._metrics.get_service_usage_report()
        }
    
    def load_config_from_toml(self, file_path: str) -> bool:
        """
        Загрузить конфигурацию из TOML файла с проверкой безопасности.
        
        Args:
            file_path: Путь к TOML файлу
            
        Returns:
            True если конфигурация загружена успешно
            
        Raises:
            ConfigurationSecurityError: При обнаружении небезопасных паттернов
        """
        try:
            # Валидируем TOML файл на безопасность
            if not self._toml_validator.validate_toml_file(file_path):
                raise ConfigurationSecurityError("TOML файл не прошел валидацию безопасности")
            
            # Здесь можно добавить загрузку и применение конфигурации
            self.logger.info(f"Конфигурация из {file_path} загружена успешно")
            return True
            
        except ConfigurationSecurityError:
            raise
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации из {file_path}: {e}")
            raise ConfigurationSecurityError(f"Ошибка загрузки конфигурации: {e}")
    
    def get_security_info(self) -> Dict[str, Any]:
        """Получить информацию о безопасности контейнера"""
        return {
            'security_enabled': self._security_enabled,
            'max_services': self._max_services,
            'max_dependencies': self._max_dependencies,
            'current_services': len(self._services),
            'toml_validation_enabled': True,
            'forbidden_patterns_count': len(self._toml_validator.forbidden_patterns),
            'max_config_size': self._toml_validator.max_config_size,
            'max_nesting_depth': self._toml_validator.max_nesting_depth,
            'max_string_length': self._toml_validator.max_string_length
        }
    
    def set_security_limits(self, max_services: int, max_dependencies: int) -> bool:
        """Установить лимиты безопасности"""
        try:
            if max_services > 0 and max_dependencies > 0:
                self._max_services = max_services
                self._max_dependencies = max_dependencies
                self.logger.info(f"Лимиты безопасности обновлены: services={max_services}, dependencies={max_dependencies}")
                return True
            else:
                self.logger.warning("Лимиты безопасности должны быть положительными")
                return False
        except Exception as e:
            self.logger.error(f"Ошибка установки лимитов безопасности: {e}")
            return False
    
    def enable_security(self, enabled: bool = True) -> None:
        """Включить/выключить проверки безопасности"""
        self._security_enabled = enabled
        status = "включены" if enabled else "выключены"
        self.logger.info(f"Проверки безопасности {status}")
    
    def validate_service_security(self, registration: ServiceRegistration) -> bool:
        """Валидировать безопасность регистрации сервиса"""
        if not self._security_enabled:
            return True
        
        try:
            # Проверяем лимит сервисов
            if len(self._services) >= self._max_services:
                self.logger.error(f"Достигнут лимит сервисов: {self._max_services}")
                return False
            
            # Проверяем лимит зависимостей
            if registration.dependencies and len(registration.dependencies) > self._max_dependencies:
                self.logger.error(f"Слишком много зависимостей: {len(registration.dependencies)} > {self._max_dependencies}")
                return False
            
            # Проверяем на подозрительные имена
            suspicious_names = ['eval', 'exec', 'import', 'open', 'file', 'input']
            service_name = registration.interface.__name__.lower()
            if any(name in service_name for name in suspicious_names):
                self.logger.warning(f"Подозрительное имя сервиса: {service_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации безопасности сервиса: {e}")
            return False
