"""
Модуль для управления протоколами связи.

Содержит класс SerialProtocol для обработки различных протоколов
последовательной связи, включая команды, ответы и обработку ошибок.
"""

import logging
import re
import time
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class ProtocolType(Enum):
    """Типы протоколов связи"""
    CUSTOM = "custom"
    MODBUS = "modbus"
    AT_COMMANDS = "at_commands"
    BINARY = "binary"
    TEXT = "text"


class ResponseStatus(Enum):
    """Статусы ответов"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    INVALID = "invalid"
    PARTIAL = "partial"


@dataclass
class ProtocolCommand:
    """Команда протокола"""
    command: str
    parameters: Optional[Dict[str, Any]] = None
    timeout: float = 5.0
    retries: int = 0
    expected_response: Optional[str] = None
    response_pattern: Optional[str] = None


@dataclass
class ProtocolResponse:
    """Ответ протокола"""
    status: ResponseStatus
    data: Optional[str] = None
    raw_data: Optional[bytes] = None
    timestamp: float = 0.0
    command: Optional[str] = None
    error_message: Optional[str] = None
    response_time: float = 0.0


class SerialProtocol:
    """
    Управление протоколами последовательной связи.
    
    Отвечает за обработку команд, анализ ответов и управление
    различными протоколами связи.
    """
    
    def __init__(self, protocol_type: ProtocolType = ProtocolType.CUSTOM):
        self.protocol_type = protocol_type
        self.logger = logging.getLogger(__name__)
        
        # Настройки протокола
        self.command_terminator = b'\r\n'
        self.response_terminator = b'\r\n'
        self.encoding = 'utf-8'
        self.default_timeout = 5.0
        self.max_retries = 3
        
        # Шаблоны ответов для разных протоколов
        self.response_patterns = self._init_response_patterns()
        
        # Статистика протокола
        self.stats = {
            'commands_sent': 0,
            'responses_received': 0,
            'errors': 0,
            'timeouts': 0,
            'total_response_time': 0.0
        }
    
    def _init_response_patterns(self) -> Dict[str, re.Pattern]:
        """Инициализация шаблонов ответов"""
        patterns = {
            'success': re.compile(r'\b(ok|success|complete|done)\b', re.IGNORECASE),
            'error': re.compile(r'\b(error|fail|failure|failed)\b', re.IGNORECASE),
            'busy': re.compile(r'\b(busy|processing|wait)\b', re.IGNORECASE),
            'timeout': re.compile(r'\b(timeout|timed_out|time_out)\b', re.IGNORECASE)
        }
        
        # Добавляем специфичные для протокола шаблоны
        if self.protocol_type == ProtocolType.AT_COMMANDS:
            patterns.update({
                'at_ok': re.compile(r'^OK$', re.IGNORECASE),
                'at_error': re.compile(r'^ERROR$', re.IGNORECASE),
                'at_busy': re.compile(r'^BUSY$', re.IGNORECASE)
            })
        elif self.protocol_type == ProtocolType.MODBUS:
            patterns.update({
                'modbus_response': re.compile(r'^[0-9A-F]{2}[0-9A-F]{2}[0-9A-F]{2}$', re.IGNORECASE),
                'modbus_error': re.compile(r'^[0-9A-F]{2}[0-9A-F]{2}[0-9A-F]{2}$', re.IGNORECASE)
            })
        
        return patterns
    
    def format_command(self, command: Union[str, ProtocolCommand], **kwargs) -> bytes:
        """
        Форматирование команды для отправки.
        
        Args:
            command: Команда или объект ProtocolCommand
            **kwargs: Дополнительные параметры
            
        Returns:
            Отформатированная команда в байтах
        """
        if isinstance(command, ProtocolCommand):
            cmd = command.command
            params = command.parameters or {}
            params.update(kwargs)
        else:
            cmd = command
            params = kwargs
        
        try:
            # Форматируем команду с параметрами
            if params:
                formatted_cmd = self._format_with_parameters(cmd, params)
            else:
                formatted_cmd = cmd
            
            # Кодируем и добавляем терминатор
            if isinstance(formatted_cmd, str):
                formatted_cmd = formatted_cmd.encode(self.encoding)
            
            if not formatted_cmd.endswith(self.command_terminator):
                formatted_cmd += self.command_terminator
            
            self.logger.debug(f"Отформатирована команда: {formatted_cmd}")
            return formatted_cmd
            
        except Exception as e:
            self.logger.error(f"Ошибка форматирования команды '{cmd}': {e}")
            raise
    
    def _format_with_parameters(self, command: str, params: Dict[str, Any]) -> str:
        """Форматирование команды с параметрами"""
        try:
            # Простая подстановка параметров в команду
            formatted = command
            for key, value in params.items():
                placeholder = f"{{{key}}}"
                if placeholder in formatted:
                    formatted = formatted.replace(placeholder, str(value))
            
            return formatted
        except Exception as e:
            self.logger.error(f"Ошибка форматирования с параметрами: {e}")
            return command
    
    def parse_response(self, raw_data: bytes, command: Optional[str] = None) -> ProtocolResponse:
        """
        Парсинг ответа от устройства.
        
        Args:
            raw_data: Сырые данные ответа
            command: Команда, на которую получен ответ
            
        Returns:
            Объект ProtocolResponse с результатом парсинга
        """
        start_time = time.time()
        
        try:
            # Декодируем данные
            if isinstance(raw_data, bytes):
                decoded_data = raw_data.decode(self.encoding, errors='ignore').strip()
            else:
                decoded_data = str(raw_data).strip()
            
            self.logger.debug(f"Парсинг ответа: {decoded_data}")
            
            # Определяем статус ответа
            status = self._determine_response_status(decoded_data)
            
            # Создаем объект ответа
            response = ProtocolResponse(
                status=status,
                data=decoded_data,
                raw_data=raw_data,
                timestamp=start_time,
                command=command,
                response_time=time.time() - start_time
            )
            
            # Обновляем статистику
            self._update_stats(response)
            
            self.logger.debug(f"Ответ распарсен: {status.value}")
            return response
            
        except Exception as e:
            error_msg = f"Ошибка парсинга ответа: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            return ProtocolResponse(
                status=ResponseStatus.INVALID,
                raw_data=raw_data,
                timestamp=start_time,
                command=command,
                error_message=error_msg,
                response_time=time.time() - start_time
            )
    
    def _determine_response_status(self, data: str) -> ResponseStatus:
        """Определение статуса ответа на основе содержимого"""
        if not data:
            return ResponseStatus.INVALID
        
        # Проверяем шаблоны ответов
        if self.response_patterns['success'].search(data):
            return ResponseStatus.SUCCESS
        
        if self.response_patterns['error'].search(data):
            return ResponseStatus.ERROR
        
        if self.response_patterns['busy'].search(data):
            return ResponseStatus.PARTIAL
        
        if self.response_patterns['timeout'].search(data):
            return ResponseStatus.TIMEOUT
        
        # Проверяем специфичные для протокола шаблоны
        if self.protocol_type == ProtocolType.AT_COMMANDS:
            if self.response_patterns['at_ok'].search(data):
                return ResponseStatus.SUCCESS
            if self.response_patterns['at_error'].search(data):
                return ResponseStatus.ERROR
            if self.response_patterns['at_busy'].search(data):
                return ResponseStatus.PARTIAL
        
        # По умолчанию считаем успешным
        return ResponseStatus.SUCCESS
    
    def validate_command(self, command: Union[str, ProtocolCommand]) -> Tuple[bool, List[str]]:
        """
        Валидация команды протокола.
        
        Args:
            command: Команда для валидации
            
        Returns:
            Tuple (is_valid, errors) где errors - список ошибок
        """
        errors = []
        
        try:
            if isinstance(command, ProtocolCommand):
                cmd = command.command
            else:
                cmd = command
            
            # Проверяем базовые требования
            if not cmd or not cmd.strip():
                errors.append("Команда не может быть пустой")
            
            if len(cmd) > 1024:
                errors.append("Команда слишком длинная (максимум 1024 символа)")
            
            # Проверяем специфичные для протокола требования
            if self.protocol_type == ProtocolType.AT_COMMANDS:
                if not cmd.upper().startswith('AT'):
                    errors.append("AT команда должна начинаться с 'AT'")
            
            elif self.protocol_type == ProtocolType.MODBUS:
                if not re.match(r'^[0-9A-F]{2}[0-9A-F]{2}[0-9A-F]{2}$', cmd, re.IGNORECASE):
                    errors.append("Modbus команда должна быть в hex формате")
            
            # Проверяем параметры если это ProtocolCommand
            if isinstance(command, ProtocolCommand):
                if command.timeout <= 0:
                    errors.append("Таймаут должен быть положительным числом")
                
                if command.retries < 0:
                    errors.append("Количество повторов не может быть отрицательным")
                
                if command.retries > self.max_retries:
                    errors.append(f"Количество повторов превышает максимум ({self.max_retries})")
            
            is_valid = len(errors) == 0
            if not is_valid:
                self.logger.warning(f"Команда '{cmd}' не прошла валидацию: {errors}")
            
            return is_valid, errors
            
        except Exception as e:
            error_msg = f"Ошибка валидации команды: {e}"
            self.logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            return False, errors
    
    def create_command(self, command: str, **kwargs) -> ProtocolCommand:
        """
        Создание объекта команды протокола.
        
        Args:
            command: Строка команды
            **kwargs: Параметры команды
            
        Returns:
            Объект ProtocolCommand
        """
        return ProtocolCommand(
            command=command,
            parameters=kwargs,
            timeout=kwargs.get('timeout', self.default_timeout),
            retries=kwargs.get('retries', 0),
            expected_response=kwargs.get('expected_response'),
            response_pattern=kwargs.get('response_pattern')
        )
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """Получение информации о протоколе"""
        return {
            'type': self.protocol_type.value,
            'command_terminator': self.command_terminator,
            'response_terminator': self.response_terminator,
            'encoding': self.encoding,
            'default_timeout': self.default_timeout,
            'max_retries': self.max_retries,
            'response_patterns': list(self.response_patterns.keys()),
            'statistics': self.stats.copy()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики протокола"""
        stats = self.stats.copy()
        
        # Вычисляем среднее время ответа
        if stats['responses_received'] > 0:
            stats['average_response_time'] = stats['total_response_time'] / stats['responses_received']
        else:
            stats['average_response_time'] = 0.0
        
        # Вычисляем процент ошибок
        total_operations = stats['commands_sent'] + stats['responses_received']
        if total_operations > 0:
            stats['error_rate'] = (stats['errors'] / total_operations) * 100.0
        else:
            stats['error_rate'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Сброс статистики протокола"""
        self.stats = {
            'commands_sent': 0,
            'responses_received': 0,
            'errors': 0,
            'timeouts': 0,
            'total_response_time': 0.0
        }
        self.logger.debug("Статистика протокола сброшена")
    
    def _update_stats(self, response: ProtocolResponse):
        """Обновление статистики на основе ответа"""
        self.stats['responses_received'] += 1
        self.stats['total_response_time'] += response.response_time
        
        if response.status == ResponseStatus.ERROR:
            self.stats['errors'] += 1
        elif response.status == ResponseStatus.TIMEOUT:
            self.stats['timeouts'] += 1
    
    def set_protocol_type(self, protocol_type: ProtocolType):
        """Установка типа протокола"""
        self.protocol_type = protocol_type
        self.response_patterns = self._init_response_patterns()
        self.logger.info(f"Тип протокола изменен на: {protocol_type.value}")
    
    def add_response_pattern(self, name: str, pattern: str):
        """Добавление пользовательского шаблона ответа"""
        try:
            self.response_patterns[name] = re.compile(pattern, re.IGNORECASE)
            self.logger.debug(f"Добавлен шаблон ответа: {name}")
        except Exception as e:
            self.logger.error(f"Ошибка добавления шаблона '{name}': {e}")
    
    def remove_response_pattern(self, name: str):
        """Удаление шаблона ответа"""
        if name in self.response_patterns:
            del self.response_patterns[name]
            self.logger.debug(f"Удален шаблон ответа: {name}")
        else:
            self.logger.warning(f"Шаблон ответа '{name}' не найден")
    
    def cleanup(self):
        """Очистка ресурсов протокола"""
        try:
            self.reset_statistics()
            self.logger.debug("Ресурсы протокола очищены")
        except Exception as e:
            self.logger.error(f"Ошибка очистки ресурсов протокола: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()

