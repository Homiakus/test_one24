"""
Адаптер совместимости MOTTO

Преобразует конфигурации v1.0 в v1.1 формат MOTTO
"""

import logging
from typing import Dict, List, Any, Optional
from .types import MOTTOConfig, Sequence


class CompatibilityAdapter:
    """Адаптер для совместимости с существующими конфигурациями"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def convert_v1_to_v1_1(self, v1_config: dict) -> MOTTOConfig:
        """
        Конвертация конфигурации v1.0 в v1.1
        
        Args:
            v1_config: Словарь конфигурации v1.0
            
        Returns:
            MOTTOConfig v1.1
        """
        config = MOTTOConfig()
        config.version = "1.1"
        
        # Конвертируем переменные
        config.vars = self._convert_vars(v1_config)
        
        # Конвертируем профили
        config.profiles = self._convert_profiles(v1_config)
        
        # Конвертируем команды из buttons
        commands = self._convert_buttons(v1_config.get('buttons', {}))
        
        # Конвертируем последовательности
        config.sequences = self._convert_sequences(v1_config.get('sequences', {}), commands)
        
        # Конвертируем wizard
        config.metadata['wizard'] = v1_config.get('wizard', {})
        
        # Конвертируем serial_default
        config.metadata['serial_default'] = v1_config.get('serial_default', {})
        
        # Добавляем базовые условия и гварды
        config.conditions.update(self._get_default_conditions())
        config.guards.update(self._get_default_guards())
        
        # Добавляем базовые политики
        config.policies.update(self._get_default_policies())
        
        # Добавляем базовые ресурсы
        config.resources.update(self._get_default_resources())
        
        # Добавляем базовые события и обработчики
        config.events.update(self._get_default_events())
        config.handlers.update(self._get_default_handlers())
        
        return config
    
    def _convert_vars(self, v1_config: dict) -> Dict[str, Any]:
        """Конвертация переменных"""
        vars_dict = {
            'plant': 'LAB-01',
            'line': 'stain-processor',
            'operator': 'auto'
        }
        
        # Добавляем настройки из serial_default
        serial_default = v1_config.get('serial_default', {})
        if serial_default:
            vars_dict.update({
                'default_port': serial_default.get('port', 'COM4'),
                'default_baudrate': serial_default.get('baudrate', 115200)
            })
        
        return vars_dict
    
    def _convert_profiles(self, v1_config: dict) -> Dict[str, Any]:
        """Конвертация профилей"""
        profiles = {}
        
        # Создаём профиль по умолчанию
        serial_default = v1_config.get('serial_default', {})
        profiles['default'] = {
            'name': 'default',
            'extends': None,
            'env': {
                'port': serial_default.get('port', 'COM4'),
                'baudrate': serial_default.get('baudrate', 115200),
                'timeout': serial_default.get('timeout', 1.0),
                'safety_mode': 'normal',
                'max_retries': 3
            },
            'metadata': {}
        }
        
        return profiles
    
    def _convert_buttons(self, buttons: dict) -> Dict[str, str]:
        """Конвертация кнопок в команды"""
        commands = {}
        
        for button_name, command in buttons.items():
            # Преобразуем имя кнопки в имя команды
            command_name = self._normalize_command_name(button_name)
            commands[command_name] = command
        
        return commands
    
    def _normalize_command_name(self, button_name: str) -> str:
        """Нормализация имени команды"""
        # Убираем специальные символы и пробелы
        name = button_name.replace(' ', '_').replace('→', '_').replace('(', '').replace(')', '')
        name = name.lower()
        
        # Убираем множественные подчёркивания
        while '__' in name:
            name = name.replace('__', '_')
        
        # Убираем подчёркивания в конце
        name = name.rstrip('_')
        
        # Заменяем русские символы на английские
        replacements = {
            'multi': 'multi',
            'rright': 'rright',
            'clamp': 'clamp',
            'kl1': 'kl1',
            'kl2': 'kl2',
            'насос': 'pump',
            'хоминг': 'home',
            'слив': 'drain',
            'экспозиция': 'exposure',
            'верх': 'up',
            'загрузка_пробирок': 'load_tubes',
            'извлечение_пробирок': 'extract_tubes',
            'предноль': 'pre_zero',
            'сжать': 'close',
            'разжать': 'open',
            'включить': 'on',
            'выключить': 'off',
            'продувка': 'flush',
            'тестовая_команда': 'test_command',
            'статус_системы': 'system_status'
        }
        
        for ru, en in replacements.items():
            name = name.replace(ru, en)
        
        return name
    
    def _convert_sequences(self, sequences: dict, commands: dict) -> Dict[str, Sequence]:
        """Конвертация последовательностей"""
        converted_sequences = {}
        
        for seq_name, steps in sequences.items():
            if isinstance(steps, list):
                # Преобразуем шаги
                converted_steps = []
                for step in steps:
                    if step.startswith('wait '):
                        # Оставляем wait как есть
                        converted_steps.append(step)
                    else:
                        # Ищем соответствующую команду
                        command_name = self._find_command_for_step(step, commands)
                        if command_name:
                            converted_steps.append(command_name)
                        else:
                            # Если команда не найдена, оставляем как есть
                            converted_steps.append(step)
                
                # Создаём последовательность
                sequence = Sequence(
                    name=seq_name,
                    description=f"Конвертированная последовательность {seq_name}",
                    type="sequence",
                    steps=converted_steps,
                    policy="safe_retry",
                    guards=["no_alarms"],
                    post_checks=[],
                    metadata={}
                )
                
                converted_sequences[seq_name] = sequence
        
        return converted_sequences
    
    def _find_command_for_step(self, step: str, commands: dict) -> Optional[str]:
        """Поиск команды для шага"""
        # Прямое совпадение
        if step in commands:
            return step
        
        # Нормализованное имя
        normalized = self._normalize_command_name(step)
        if normalized in commands:
            return normalized
        
        # Поиск по частичному совпадению
        for command_name, command_value in commands.items():
            if step in command_value or command_value in step:
                return command_name
        
        return None
    
    def _get_default_conditions(self) -> Dict[str, Any]:
        """Получение базовых условий"""
        return {
            'no_alarms': {
                'name': 'no_alarms',
                'expr': 'status("alarm") == 0',
                'description': 'Проверка отсутствия аварий',
                'metadata': {}
            },
            'serial_connected': {
                'name': 'serial_connected',
                'expr': 'status("serial") == "connected"',
                'description': 'Проверка подключения к UART',
                'metadata': {}
            }
        }
    
    def _get_default_guards(self) -> Dict[str, Any]:
        """Получение базовых гвардов"""
        return {
            'no_alarms': {
                'name': 'no_alarms',
                'when': 'pre',
                'condition': 'no_alarms',
                'on_fail': {'action': 'abort', 'reason': 'Active alarms detected'},
                'description': 'Проверка отсутствия аварий перед выполнением',
                'metadata': {}
            },
            'serial_connected': {
                'name': 'serial_connected',
                'when': 'pre',
                'condition': 'serial_connected',
                'on_fail': {'action': 'retry', 'max_attempts': 3, 'cooldown_ms': 1000},
                'description': 'Проверка подключения к UART',
                'metadata': {}
            }
        }
    
    def _get_default_policies(self) -> Dict[str, Any]:
        """Получение базовых политик"""
        return {
            'safe_retry': {
                'name': 'safe_retry',
                'retry_on': ['timeout', 'serial_error'],
                'max_attempts': 3,
                'backoff': {'type': 'exponential', 'base_ms': 500, 'factor': 2.0, 'jitter': 'full'},
                'step_timeout_ms': 60000,
                'sequence_timeout_ms': 600000,
                'metadata': {}
            },
            'fast_retry': {
                'name': 'fast_retry',
                'retry_on': ['timeout'],
                'max_attempts': 2,
                'backoff': {'type': 'linear', 'base_ms': 1000},
                'step_timeout_ms': 30000,
                'sequence_timeout_ms': 300000,
                'metadata': {}
            }
        }
    
    def _get_default_resources(self) -> Dict[str, Any]:
        """Получение базовых ресурсов"""
        return {
            'serial_port': {
                'name': 'serial_port',
                'type': 'mutex',
                'members': ['COM3', 'COM4', 'COM5'],
                'scope': 'machine',
                'metadata': {}
            },
            'pump': {
                'name': 'pump',
                'type': 'mutex',
                'members': ['pump_main'],
                'scope': 'machine',
                'metadata': {}
            }
        }
    
    def _get_default_events(self) -> Dict[str, Any]:
        """Получение базовых событий"""
        return {
            'estop': {
                'name': 'estop',
                'source': 'hardware',
                'filter': 'status("estop") == 1',
                'description': 'Аварийная остановка',
                'metadata': {}
            },
            'serial_error': {
                'name': 'serial_error',
                'source': 'system',
                'filter': 'status("serial") == "error"',
                'description': 'Ошибка UART',
                'metadata': {}
            }
        }
    
    def _get_default_handlers(self) -> Dict[str, Any]:
        """Получение базовых обработчиков"""
        return {
            'on_estop': {
                'name': 'on_estop',
                'on': 'estop',
                'do': ['EMERGENCY_STOP', 'CLOSE_ALL_VALVES'],
                'priority': 100,
                'description': 'Обработка аварийной остановки',
                'metadata': {}
            },
            'on_serial_error': {
                'name': 'on_serial_error',
                'on': 'serial_error',
                'do': ['RECONNECT_SERIAL', 'RETRY_COMMAND'],
                'priority': 50,
                'description': 'Обработка ошибки UART',
                'metadata': {}
            }
        }
    
    def convert_sequence(self, old_sequence: List[str]) -> Sequence:
        """Конвертация старой последовательности"""
        return Sequence(
            name="converted_sequence",
            description="Конвертированная последовательность",
            type="sequence",
            steps=old_sequence,
            policy="safe_retry",
            guards=["no_alarms"],
            post_checks=[],
            metadata={}
        )
    
    def convert_buttons(self, buttons: dict) -> Dict[str, str]:
        """Конвертация кнопок"""
        return self._convert_buttons(buttons)