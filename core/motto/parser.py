"""
Парсер MOTTO конфигураций

Парсит TOML файлы в структуры данных MOTTO с поддержкой:
- Базовых секций MOTTO
- Валидации структуры
- Обработки ошибок
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import tomli

from .types import (
    MOTTOConfig, Sequence, Condition, Guard, Policy, Resource,
    Event, Handler, Template, Validator, Profile, Context,
    SequenceType, GuardWhen, ResourceType, EventSource
)


class MOTTOParser:
    """
    Парсер MOTTO конфигураций из TOML файлов
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._parsed_configs: Dict[str, MOTTOConfig] = {}
    
    def parse_config(self, config_path: str) -> Optional[MOTTOConfig]:
        """
        Парсинг конфигурации из TOML файла
        
        Args:
            config_path: Путь к файлу конфигурации
            
        Returns:
            MOTTOConfig или None при ошибке
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                self.logger.error(f"Файл конфигурации не найден: {config_path}")
                return None
            
            # Загружаем TOML
            with open(config_file, 'rb') as f:
                raw_config = tomli.load(f)
            self.logger.info(f"Загружен TOML файл: {config_path}")
            
            # Парсим в MOTTO структуры
            config = self._parse_motto_config(raw_config)
            
            # Кэшируем результат
            self._parsed_configs[config_path] = config
            
            self.logger.info(f"Конфигурация MOTTO успешно распарсена: {config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"Ошибка парсинга конфигурации {config_path}: {e}")
            return None
    
    def _parse_motto_config(self, raw_config: Dict[str, Any]) -> MOTTOConfig:
        """
        Парсинг сырой конфигурации в MOTTOConfig
        
        Args:
            raw_config: Словарь из TOML
            
        Returns:
            MOTTOConfig
        """
        config = MOTTOConfig()
        
        # Базовые поля
        config.version = raw_config.get('version', '1.1')
        config.vars = raw_config.get('vars', {})
        
        # Профили
        profiles_data = raw_config.get('profiles', {})
        for name, profile_data in profiles_data.items():
            config.profiles[name] = self._parse_profile(name, profile_data)
        
        # Контексты
        contexts_data = raw_config.get('contexts', {})
        for name, context_data in contexts_data.items():
            config.contexts[name] = self._parse_context(name, context_data)
        
        # Последовательности
        sequences_data = raw_config.get('sequences', {})
        for name, sequence_data in sequences_data.items():
            config.sequences[name] = self._parse_sequence(name, sequence_data)
        
        # Условия
        conditions_data = raw_config.get('conditions', {})
        for name, condition_data in conditions_data.items():
            config.conditions[name] = self._parse_condition(name, condition_data)
        
        # Гварды
        guards_data = raw_config.get('guards', {})
        for name, guard_data in guards_data.items():
            config.guards[name] = self._parse_guard(name, guard_data)
        
        # Политики
        policies_data = raw_config.get('policies', {})
        for name, policy_data in policies_data.items():
            config.policies[name] = self._parse_policy(name, policy_data)
        
        # Ресурсы
        resources_data = raw_config.get('resources', {})
        for name, resource_data in resources_data.items():
            config.resources[name] = self._parse_resource(name, resource_data)
        
        # События
        events_data = raw_config.get('events', {})
        for name, event_data in events_data.items():
            config.events[name] = self._parse_event(name, event_data)
        
        # Обработчики
        handlers_data = raw_config.get('handlers', {})
        for name, handler_data in handlers_data.items():
            config.handlers[name] = self._parse_handler(name, handler_data)
        
        # Шаблоны
        templates_data = raw_config.get('templates', {})
        for name, template_data in templates_data.items():
            config.templates[name] = self._parse_template(name, template_data)
        
        # Юниты
        config.units = raw_config.get('units', {})
        
        # Валидаторы
        validators_data = raw_config.get('validators', {})
        for name, validator_data in validators_data.items():
            config.validators[name] = self._parse_validator(name, validator_data)
        
        # Runtime и аудит
        config.runtime = raw_config.get('runtime', {})
        config.audit = raw_config.get('audit', {})
        
        # Метаданные
        config.metadata = raw_config.get('metadata', {})
        
        return config
    
    def _parse_profile(self, name: str, data: Dict[str, Any]) -> Profile:
        """Парсинг профиля"""
        return Profile(
            name=name,
            extends=data.get('extends'),
            env=data.get('env', {}),
            metadata=data.get('metadata', {})
        )
    
    def _parse_context(self, name: str, data: Dict[str, Any]) -> Context:
        """Парсинг контекста"""
        return Context(
            name=name,
            data=data.get('data', {}),
            metadata=data.get('metadata', {})
        )
    
    def _parse_sequence(self, name: str, data: Dict[str, Any]) -> Sequence:
        """Парсинг последовательности"""
        sequence_type = SequenceType(data.get('type', 'sequence'))
        
        return Sequence(
            name=name,
            description=data.get('description', ''),
            type=sequence_type,
            inputs=data.get('inputs', {}),
            defaults=data.get('defaults', {}),
            outputs=data.get('outputs', {}),
            steps=data.get('steps', []),
            policy=data.get('policy'),
            guards=data.get('guards', []),
            post_checks=data.get('post_checks', []),
            branches=data.get('branches', []),
            barrier=data.get('barrier', 'all'),
            transaction=data.get('transaction'),
            metadata=data.get('metadata', {})
        )
    
    def _parse_condition(self, name: str, data: Dict[str, Any]) -> Condition:
        """Парсинг условия"""
        return Condition(
            name=name,
            expr=data.get('expr', ''),
            description=data.get('description', ''),
            metadata=data.get('metadata', {})
        )
    
    def _parse_guard(self, name: str, data: Dict[str, Any]) -> Guard:
        """Парсинг гварда"""
        return Guard(
            name=name,
            when=GuardWhen(data.get('when', 'pre')),
            condition=data.get('condition', ''),
            on_fail=data.get('on_fail', {}),
            description=data.get('description', ''),
            metadata=data.get('metadata', {})
        )
    
    def _parse_policy(self, name: str, data: Dict[str, Any]) -> Policy:
        """Парсинг политики"""
        return Policy(
            name=name,
            retry_on=data.get('retry_on', []),
            max_attempts=data.get('max_attempts', 3),
            backoff=data.get('backoff', {}),
            step_timeout_ms=data.get('step_timeout_ms', 60000),
            sequence_timeout_ms=data.get('sequence_timeout_ms', 600000),
            idempotency_key=data.get('idempotency_key'),
            transaction=data.get('transaction'),
            metadata=data.get('metadata', {})
        )
    
    def _parse_resource(self, name: str, data: Dict[str, Any]) -> Resource:
        """Парсинг ресурса"""
        return Resource(
            name=name,
            type=ResourceType(data.get('type', 'mutex')),
            members=data.get('members', []),
            capacity=data.get('capacity'),
            scope=data.get('scope', 'machine'),
            metadata=data.get('metadata', {})
        )
    
    def _parse_event(self, name: str, data: Dict[str, Any]) -> Event:
        """Парсинг события"""
        return Event(
            name=name,
            source=EventSource(data.get('source', 'system')),
            filter=data.get('filter', ''),
            description=data.get('description', ''),
            metadata=data.get('metadata', {})
        )
    
    def _parse_handler(self, name: str, data: Dict[str, Any]) -> Handler:
        """Парсинг обработчика"""
        return Handler(
            name=name,
            on=data.get('on', ''),
            do=data.get('do', []),
            priority=data.get('priority', 0),
            description=data.get('description', ''),
            metadata=data.get('metadata', {})
        )
    
    def _parse_template(self, name: str, data: Dict[str, Any]) -> Template:
        """Парсинг шаблона"""
        return Template(
            name=name,
            for_type=data.get('for', ''),
            matrix=data.get('matrix', []),
            args=data.get('args', []),
            pattern=data.get('pattern', {}),
            expand=data.get('expand', []),
            metadata=data.get('metadata', {})
        )
    
    def _parse_validator(self, name: str, data: Dict[str, Any]) -> Validator:
        """Парсинг валидатора"""
        return Validator(
            name=name,
            key=data.get('key', ''),
            range=data.get('range'),
            pattern=data.get('pattern'),
            custom_expr=data.get('custom_expr'),
            description=data.get('description', ''),
            metadata=data.get('metadata', {})
        )
    
    def get_cached_config(self, config_path: str) -> Optional[MOTTOConfig]:
        """
        Получение кэшированной конфигурации
        
        Args:
            config_path: Путь к файлу
            
        Returns:
            Кэшированная конфигурация или None
        """
        return self._parsed_configs.get(config_path)
    
    def clear_cache(self, config_path: Optional[str] = None):
        """
        Очистка кэша
        
        Args:
            config_path: Путь к файлу или None для очистки всего кэша
        """
        if config_path:
            self._parsed_configs.pop(config_path, None)
        else:
            self._parsed_configs.clear()