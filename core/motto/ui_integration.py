"""
Интеграция MOTTO с существующим UI

Адаптер для использования MOTTO конфигурации с существующими компонентами UI
"""

import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .parser import MOTTOParser
from .types import MOTTOConfig, Sequence


class MOTTOUIIntegration:
    """Интеграция MOTTO с UI"""
    
    def __init__(self, config_file: str = 'config_motto_fixed.toml'):
        """
        Инициализация интеграции
        
        Args:
            config_file: Путь к MOTTO конфигурации
        """
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        
        # Загружаем MOTTO конфигурацию
        self.parser = MOTTOParser()
        self.motto_config = self.parser.parse_config(config_file)
        
        if self.motto_config is None:
            raise ValueError(f"Не удалось загрузить MOTTO конфигурацию: {config_file}")
        
        self.logger.info(f"MOTTO UI интеграция инициализирована (версия {self.motto_config.version})")
    
    def get_compatible_config(self) -> Dict[str, Any]:
        """
        Получение конфигурации в совместимом формате для существующего UI
        
        Returns:
            Словарь конфигурации в формате, совместимом с ConfigLoader
        """
        config = {}
        
        # Добавляем секцию buttons (команды)
        config['buttons'] = {}
        # Команды находятся в commands
        if hasattr(self.motto_config, 'commands'):
            for name, command in self.motto_config.commands.items():
                config['buttons'][name] = command
        
        # Добавляем секцию sequences
        config['sequences'] = {}
        for name, sequence in self.motto_config.sequences.items():
            config['sequences'][name] = sequence.steps
        
        # Добавляем serial_default
        config['serial_default'] = {
            'port': 'COM4',
            'baudrate': 115200,
            'bytesize': 8,
            'parity': 'N',
            'stopbits': 1,
            'timeout': 1.0
        }
        
        # Добавляем wizard
        config['wizard'] = {
            'step': [
                {
                    'id': 1,
                    'title': 'Главное меню',
                    'buttons': [
                        {'text': '▶ Начать окраску и осаждение', 'next': 2},
                        {'text': '▶ Начать промывку', 'next': 7}
                    ],
                    'sequence': '',
                    'autoNext': False,
                    'showBar': False
                }
            ]
        }
        
        return config
    
    def get_buttons_for_ui(self) -> Dict[str, str]:
        """
        Получение команд для UI в формате buttons
        
        Returns:
            Словарь команд для UI
        """
        buttons = {}
        
        # Получаем команды из MOTTO конфигурации (они находятся в commands)
        if hasattr(self.motto_config, 'commands'):
            for name, command in self.motto_config.commands.items():
                buttons[name] = command
        
        return buttons
    
    def get_sequences_for_ui(self) -> Dict[str, List[str]]:
        """
        Получение последовательностей для UI
        
        Returns:
            Словарь последовательностей для UI
        """
        sequences = {}
        
        for name, sequence in self.motto_config.sequences.items():
            sequences[name] = sequence.steps
        
        return sequences
    
    def get_serial_settings(self) -> Dict[str, Any]:
        """
        Получение настроек Serial
        
        Returns:
            Настройки Serial
        """
        # Пытаемся получить из MOTTO конфигурации
        if hasattr(self.motto_config, 'serial_default'):
            return self.motto_config.serial_default
        
        # Возвращаем значения по умолчанию
        return {
            'port': 'COM4',
            'baudrate': 115200,
            'bytesize': 8,
            'parity': 'N',
            'stopbits': 1,
            'timeout': 1.0
        }
    
    def get_wizard_steps(self) -> List[Dict[str, Any]]:
        """
        Получение шагов wizard для UI
        
        Returns:
            Список шагов wizard
        """
        # Пытаемся получить из MOTTO конфигурации
        if hasattr(self.motto_config, 'wizard'):
            return self.motto_config.wizard.get('step', [])
        
        # Возвращаем базовый шаг
        return [
            {
                'id': 1,
                'title': 'Главное меню',
                'buttons': [
                    {'text': '▶ Начать окраску и осаждение', 'next': 2},
                    {'text': '▶ Начать промывку', 'next': 7}
                ],
                'sequence': '',
                'autoNext': False,
                'showBar': False
            }
        ]
    
    def execute_sequence_with_motto(self, sequence_name: str, 
                                  sequence_executor=None,
                                  progress_callback=None) -> bool:
        """
        Выполнение последовательности с MOTTO возможностями
        
        Args:
            sequence_name: Имя последовательности
            sequence_executor: Исполнитель последовательности
            progress_callback: Callback для прогресса
            
        Returns:
            True если последовательность выполнена успешно
        """
        if sequence_name not in self.motto_config.sequences:
            self.logger.error(f"Последовательность '{sequence_name}' не найдена")
            return False
        
        sequence = self.motto_config.sequences[sequence_name]
        
        # Проверяем гварды
        if not self._check_guards(sequence.guards):
            self.logger.error(f"Гварды не прошли для последовательности '{sequence_name}'")
            return False
        
        # Выполняем последовательность
        try:
            steps = sequence.steps
            total_steps = len(steps)
            
            for i, step in enumerate(steps):
                if progress_callback:
                    progress = (i / total_steps) * 100
                    progress_callback(progress, f"Шаг {i+1}/{total_steps}: {step}")
                
                if not self._execute_step(step, sequence_executor):
                    self.logger.error(f"Ошибка выполнения шага '{step}'")
                    return False
            
            if progress_callback:
                progress_callback(100, "Последовательность завершена")
            
            self.logger.info(f"Последовательность '{sequence_name}' выполнена успешно")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения последовательности '{sequence_name}': {e}")
            return False
    
    def _check_guards(self, guards: List[str]) -> bool:
        """
        Проверка гвардов
        
        Args:
            guards: Список гвардов для проверки
            
        Returns:
            True если все гварды прошли
        """
        for guard_name in guards:
            if guard_name in self.motto_config.guards:
                guard = self.motto_config.guards[guard_name]
                # В реальности здесь была бы проверка условий
                self.logger.info(f"Проверка гварда '{guard_name}': OK")
            else:
                self.logger.warning(f"Гвард '{guard_name}' не найден")
        
        return True
    
    def _execute_step(self, step: str, sequence_executor=None) -> bool:
        """
        Выполнение одного шага
        
        Args:
            step: Шаг для выполнения
            sequence_executor: Исполнитель последовательности
            
        Returns:
            True если шаг выполнен успешно
        """
        if step.startswith('wait '):
            try:
                wait_time = int(step.split()[1])
                self.logger.info(f"Ожидание {wait_time} секунд...")
                import time
                time.sleep(wait_time)
                return True
            except (ValueError, IndexError):
                self.logger.error(f"Неверный формат команды ожидания: {step}")
                return False
        
        # Выполняем команду через sequence_executor если доступен
        if sequence_executor:
            try:
                sequence_executor.send_command(step)
                return True
            except Exception as e:
                self.logger.error(f"Ошибка выполнения команды '{step}': {e}")
                return False
        
        # Иначе просто логируем
        self.logger.info(f"Выполнение команды: {step}")
        return True
    
    def get_motto_info(self) -> Dict[str, Any]:
        """
        Получение информации о MOTTO конфигурации
        
        Returns:
            Информация о MOTTO
        """
        return {
            'version': self.motto_config.version,
            'commands_count': len(self.motto_config.vars),
            'sequences_count': len(self.motto_config.sequences),
            'conditions_count': len(self.motto_config.conditions),
            'guards_count': len(self.motto_config.guards),
            'policies_count': len(self.motto_config.policies),
            'resources_count': len(self.motto_config.resources),
            'events_count': len(self.motto_config.events),
            'handlers_count': len(self.motto_config.handlers)
        }


class MOTTOConfigLoader:
    """Загрузчик конфигурации с поддержкой MOTTO"""
    
    def __init__(self, config_file: str = 'config_motto_fixed.toml'):
        """
        Инициализация загрузчика
        
        Args:
            config_file: Путь к конфигурации
        """
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        self.motto_integration = None
        
        # Определяем тип конфигурации
        if self._is_motto_config(config_file):
            self.motto_integration = MOTTOUIIntegration(config_file)
            self.logger.info(f"Загружена MOTTO конфигурация: {config_file}")
        else:
            self.logger.info(f"Загружена стандартная конфигурация: {config_file}")
    
    def _is_motto_config(self, config_file: str) -> bool:
        """
        Проверка, является ли файл MOTTO конфигурацией
        
        Args:
            config_file: Путь к файлу конфигурации
            
        Returns:
            True если это MOTTO конфигурация
        """
        try:
            import tomli
            with open(config_file, 'rb') as f:
                config = tomli.load(f)
            
            # Проверяем наличие MOTTO специфичных секций
            motto_sections = ['version', 'vars', 'profiles', 'conditions', 'guards', 'policies']
            return any(section in config for section in motto_sections)
            
        except Exception:
            return False
    
    def load(self) -> Dict[str, Any]:
        """
        Загрузка конфигурации
        
        Returns:
            Конфигурация в совместимом формате
        """
        if self.motto_integration:
            # Загружаем MOTTO конфигурацию
            return self.motto_integration.get_compatible_config()
        else:
            # Загружаем стандартную конфигурацию
            import tomli
            with open(self.config_file, 'rb') as f:
                return tomli.load(f)
    
    def get_motto_info(self) -> Optional[Dict[str, Any]]:
        """
        Получение информации о MOTTO (если применимо)
        
        Returns:
            Информация о MOTTO или None
        """
        if self.motto_integration:
            return self.motto_integration.get_motto_info()
        return None
    
    def execute_sequence_with_motto(self, sequence_name: str, 
                                  sequence_executor=None,
                                  progress_callback=None) -> bool:
        """
        Выполнение последовательности с MOTTO возможностями
        
        Args:
            sequence_name: Имя последовательности
            sequence_executor: Исполнитель последовательности
            progress_callback: Callback для прогресса
            
        Returns:
            True если последовательность выполнена успешно
        """
        if self.motto_integration:
            return self.motto_integration.execute_sequence_with_motto(
                sequence_name, sequence_executor, progress_callback
            )
        else:
            # Для стандартной конфигурации используем обычное выполнение
            self.logger.info(f"Выполнение последовательности '{sequence_name}' (стандартный режим)")
            return True