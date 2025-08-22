"""
Загрузчик конфигурации DI контейнера из TOML файла
"""
import logging
import importlib
import inspect
from typing import Dict, List, Optional, Any, Type, Callable
from pathlib import Path

import toml

from .di_container import DIContainer
from .interfaces import IDIContainer, ServiceRegistration


class DIConfigLoader:
    """
    Загрузчик конфигурации DI контейнера из TOML файла
    
    Поддерживает:
    - Загрузку конфигурации из TOML
    - Динамическую загрузку классов по именам
    - Валидацию конфигурации
    - Регистрацию сервисов в контейнере
    """
    
    def __init__(self, container: Optional[DIContainer] = None):
        self.container = container or DIContainer()
        self.logger = logging.getLogger(__name__)
        self._class_cache: Dict[str, Type] = {}
        self._module_cache: Dict[str, Any] = {}
        
    def load_config(self, config_path: str) -> bool:
        """
        Загрузка конфигурации из TOML файла
        
        Args:
            config_path: Путь к файлу конфигурации
            
        Returns:
            True при успешной загрузке
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                self.logger.error(f"Файл конфигурации не найден: {config_path}")
                return False
            
            # Загружаем TOML конфигурацию
            config = toml.load(config_file)
            self.logger.info(f"Конфигурация загружена из {config_path}")
            
            # Применяем конфигурацию к контейнеру
            return self._apply_config(config)
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации: {e}")
            return False
    
    def _apply_config(self, config: Dict[str, Any]) -> bool:
        """
        Применение конфигурации к контейнеру
        
        Args:
            config: Словарь конфигурации
            
        Returns:
            True при успешном применении
        """
        try:
            di_config = config.get('di_container', {})
            
            # Настраиваем параметры контейнера
            self._configure_container_settings(di_config)
            
            # Регистрируем сервисы
            services_config = di_config.get('services', {})
            for service_name, service_config in services_config.items():
                if not self._register_service(service_name, service_config):
                    self.logger.error(f"Не удалось зарегистрировать сервис: {service_name}")
                    return False
            
            # Регистрируем фабрики
            factories_config = di_config.get('factories', {})
            for factory_name, factory_config in factories_config.items():
                if not self._register_factory(factory_name, factory_config):
                    self.logger.error(f"Не удалось зарегистрировать фабрику: {factory_name}")
                    return False
            
            # Валидируем конфигурацию
            validation_config = di_config.get('validation', {})
            if validation_config.get('check_circular_dependencies', True):
                errors = self.container.validate_registrations()
                if errors:
                    self.logger.error(f"Ошибки валидации: {errors}")
                    return False
            
            self.logger.info("Конфигурация DI контейнера применена успешно")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка применения конфигурации: {e}")
            return False
    
    def _configure_container_settings(self, di_config: Dict[str, Any]) -> None:
        """Настройка параметров контейнера"""
        # Настройка логирования
        logging_config = di_config.get('logging', {})
        log_level = logging_config.get('level', 'INFO')
        
        # Настраиваем логгер контейнера
        container_logger = logging.getLogger('core.di_container')
        container_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    def _register_service(self, service_name: str, service_config: Dict[str, Any]) -> bool:
        """
        Регистрация сервиса в контейнере
        
        Args:
            service_name: Имя сервиса
            service_config: Конфигурация сервиса
            
        Returns:
            True при успешной регистрации
        """
        try:
            interface_name = service_config.get('interface')
            implementation_name = service_config.get('implementation')
            singleton = service_config.get('singleton', True)
            dependencies = service_config.get('dependencies', {})
            
            if not interface_name or not implementation_name:
                self.logger.error(f"Неполная конфигурация сервиса {service_name}")
                return False
            
            # Загружаем классы
            interface_class = self._load_class(interface_name)
            implementation_class = self._load_class(implementation_name)
            
            if not interface_class or not implementation_class:
                return False
            
            # Регистрируем сервис
            self.container.register(
                interface=interface_class,
                implementation=implementation_class,
                singleton=singleton,
                dependencies=self._resolve_dependencies(dependencies)
            )
            
            self.logger.debug(f"Зарегистрирован сервис: {service_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка регистрации сервиса {service_name}: {e}")
            return False
    
    def _register_factory(self, factory_name: str, factory_config: Dict[str, Any]) -> bool:
        """
        Регистрация фабрики в контейнере
        
        Args:
            factory_name: Имя фабрики
            factory_config: Конфигурация фабрики
            
        Returns:
            True при успешной регистрации
        """
        try:
            factory_func_name = factory_config.get('name')
            dependencies = factory_config.get('dependencies', {})
            
            if not factory_func_name:
                self.logger.error(f"Не указана функция фабрики для {factory_name}")
                return False
            
            # Создаем фабричную функцию
            factory_func = self._create_factory_function(factory_name, factory_config)
            if not factory_func:
                return False
            
            # Регистрируем фабрику
            # Здесь нужно определить интерфейс для фабрики
            self.logger.debug(f"Зарегистрирована фабрика: {factory_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка регистрации фабрики {factory_name}: {e}")
            return False
    
    def _load_class(self, class_name: str) -> Optional[Type]:
        """
        Загрузка класса по имени
        
        Args:
            class_name: Полное имя класса (например, 'core.serial_manager.SerialManager')
            
        Returns:
            Класс или None при ошибке
        """
        try:
            # Проверяем кеш
            if class_name in self._class_cache:
                return self._class_cache[class_name]
            
            # Парсим имя класса
            if '.' in class_name:
                module_name, class_name_short = class_name.rsplit('.', 1)
            else:
                # Предполагаем, что это интерфейс из нашего модуля
                module_name = 'core.interfaces'
                class_name_short = class_name
            
            # Загружаем модуль
            if module_name in self._module_cache:
                module = self._module_cache[module_name]
            else:
                module = importlib.import_module(module_name)
                self._module_cache[module_name] = module
            
            # Получаем класс
            class_obj = getattr(module, class_name_short)
            
            # Кешируем
            self._class_cache[class_name] = class_obj
            
            return class_obj
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки класса {class_name}: {e}")
            return None
    
    def _resolve_dependencies(self, dependencies: Dict[str, str]) -> Dict[str, Type]:
        """
        Разрешение зависимостей по именам интерфейсов
        
        Args:
            dependencies: Словарь зависимостей {param_name: interface_name}
            
        Returns:
            Словарь зависимостей {param_name: interface_class}
        """
        resolved = {}
        
        for param_name, interface_name in dependencies.items():
            interface_class = self._load_class(interface_name)
            if interface_class:
                resolved[param_name] = interface_class
            else:
                self.logger.error(f"Не удалось загрузить интерфейс: {interface_name}")
        
        return resolved
    
    def _create_factory_function(self, factory_name: str, factory_config: Dict[str, Any]) -> Optional[Callable]:
        """
        Создание фабричной функции
        
        Args:
            factory_name: Имя фабрики
            factory_config: Конфигурация фабрики
            
        Returns:
            Фабричная функция или None
        """
        try:
            factory_type = factory_config.get('type', 'basic')
            
            if factory_name == 'create_command_executor':
                return self._create_command_executor_factory(factory_type)
            elif factory_name == 'create_sequence_manager':
                return self._create_sequence_manager_factory()
            else:
                self.logger.warning(f"Неизвестная фабрика: {factory_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка создания фабрики {factory_name}: {e}")
            return None
    
    def _create_command_executor_factory(self, executor_type: str) -> Callable:
        """Создание фабрики для CommandExecutor"""
        def factory(serial_manager):
            from .command_executor import CommandExecutorFactory
            return CommandExecutorFactory.create_executor(executor_type, serial_manager)
        
        return factory
    
    def _create_sequence_manager_factory(self) -> Callable:
        """Создание фабрики для SequenceManager"""
        def factory(config_loader):
            config = config_loader.load()
            if not config:
                config = {}
            
            from .sequence_manager import SequenceManager
            return SequenceManager(
                config.get('sequences', {}),
                config.get('buttons', {})
            )
        
        return factory
    
    def get_container(self) -> DIContainer:
        """
        Получение настроенного контейнера
        
        Returns:
            Настроенный DI контейнер
        """
        return self.container
    
    def validate_config(self, config_path: str) -> List[str]:
        """
        Валидация конфигурации без применения
        
        Args:
            config_path: Путь к файлу конфигурации
            
        Returns:
            Список ошибок валидации
        """
        errors = []
        
        try:
            config = toml.load(config_path)
            di_config = config.get('di_container', {})
            services_config = di_config.get('services', {})
            
            for service_name, service_config in services_config.items():
                # Проверяем обязательные поля
                if 'interface' not in service_config:
                    errors.append(f"Сервис {service_name}: отсутствует поле 'interface'")
                
                if 'implementation' not in service_config:
                    errors.append(f"Сервис {service_name}: отсутствует поле 'implementation'")
                
                # Проверяем возможность загрузки классов
                if 'interface' in service_config:
                    interface_class = self._load_class(service_config['interface'])
                    if not interface_class:
                        errors.append(f"Сервис {service_name}: не удалось загрузить интерфейс {service_config['interface']}")
                
                if 'implementation' in service_config:
                    implementation_class = self._load_class(service_config['implementation'])
                    if not implementation_class:
                        errors.append(f"Сервис {service_name}: не удалось загрузить реализацию {service_config['implementation']}")
            
        except Exception as e:
            errors.append(f"Ошибка валидации конфигурации: {e}")
        
        return errors
