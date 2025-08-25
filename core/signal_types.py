"""
Типы данных для системы обработки входящих сигналов UART
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, Union
import json
import logging


class SignalType(Enum):
    """Типы данных сигналов"""
    FLOAT = "float"
    INT = "int"
    STRING = "string"
    BOOL = "bool"
    JSON = "json"


@dataclass
class SignalInfo:
    """Информация о сигнале"""
    signal_name: str
    variable_name: str
    signal_type: SignalType
    description: Optional[str] = None
    unit: Optional[str] = None
    min_value: Optional[Union[float, int]] = None
    max_value: Optional[Union[float, int]] = None


@dataclass
class SignalMapping:
    """Маппинг сигнала на переменную"""
    signal_name: str
    variable_name: str
    signal_type: SignalType
    config: Dict[str, Any]


@dataclass
class SignalValue:
    """Значение сигнала с типом"""
    signal_name: str
    value: Any
    signal_type: SignalType
    timestamp: float
    raw_data: str


@dataclass
class SignalResult:
    """Результат обработки сигнала"""
    success: bool
    signal_name: str
    variable_name: str
    value: Any
    signal_type: SignalType
    error_message: Optional[str] = None
    timestamp: Optional[float] = None


class SignalProcessingError(Exception):
    """Ошибка обработки сигнала"""
    pass


class SignalValidationError(Exception):
    """Ошибка валидации сигнала"""
    pass


class SignalConfigError(Exception):
    """Ошибка конфигурации сигнала"""
    pass


class SignalTypeConverter:
    """Конвертер типов данных сигналов"""
    
    @staticmethod
    def convert_value(value: str, signal_type: SignalType) -> Any:
        """
        Конвертирует строковое значение в соответствующий тип данных
        
        Args:
            value: Строковое значение для конвертации
            signal_type: Тип данных сигнала
            
        Returns:
            Конвертированное значение
            
        Raises:
            SignalProcessingError: При ошибке конвертации
        """
        try:
            if signal_type == SignalType.FLOAT:
                return float(value)
            elif signal_type == SignalType.INT:
                return int(value)
            elif signal_type == SignalType.STRING:
                return str(value)
            elif signal_type == SignalType.BOOL:
                return SignalTypeConverter._convert_bool(value)
            elif signal_type == SignalType.JSON:
                return json.loads(value)
            else:
                raise SignalProcessingError(f"Неизвестный тип сигнала: {signal_type}")
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            raise SignalProcessingError(f"Ошибка конвертации значения '{value}' в тип {signal_type}: {e}")
    
    @staticmethod
    def _convert_bool(value: str) -> bool:
        """
        Конвертирует строковое значение в boolean
        
        Args:
            value: Строковое значение
            
        Returns:
            Boolean значение
        """
        value_lower = value.lower().strip()
        if value_lower in ('true', '1', 'yes', 'on', 'enabled'):
            return True
        elif value_lower in ('false', '0', 'no', 'off', 'disabled'):
            return False
        else:
            raise SignalProcessingError(f"Невозможно конвертировать '{value}' в boolean")


class SignalValidator:
    """Валидатор сигналов"""
    
    @staticmethod
    def validate_signal_name(signal_name: str) -> bool:
        """
        Валидирует имя сигнала
        
        Args:
            signal_name: Имя сигнала
            
        Returns:
            True если имя корректно
        """
        if not signal_name or not isinstance(signal_name, str):
            return False
        
        # Проверяем, что имя содержит только буквы, цифры и подчеркивания
        return signal_name.replace('_', '').isalnum()
    
    @staticmethod
    def validate_variable_name(variable_name: str) -> bool:
        """
        Валидирует имя переменной
        
        Args:
            variable_name: Имя переменной
            
        Returns:
            True если имя корректно
        """
        if not variable_name or not isinstance(variable_name, str):
            return False
        
        # Проверяем, что имя начинается с буквы и содержит только буквы, цифры и подчеркивания
        if not variable_name[0].isalpha():
            return False
        
        return variable_name.replace('_', '').isalnum()
    
    @staticmethod
    def validate_signal_type(signal_type_str: str) -> bool:
        """
        Валидирует строковое представление типа сигнала
        
        Args:
            signal_type_str: Строковое представление типа
            
        Returns:
            True если тип корректный
        """
        try:
            SignalType(signal_type_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_value_range(value: Union[float, int], min_value: Optional[Union[float, int]], 
                           max_value: Optional[Union[float, int]]) -> bool:
        """
        Валидирует значение по диапазону
        
        Args:
            value: Значение для проверки
            min_value: Минимальное значение
            max_value: Максимальное значение
            
        Returns:
            True если значение в диапазоне
        """
        if min_value is not None and value < min_value:
            return False
        
        if max_value is not None and value > max_value:
            return False
        
        return True


class SignalParser:
    """Парсер сигналов из строки конфигурации"""
    
    @staticmethod
    def parse_signal_config(config_str: str) -> SignalMapping:
        """
        Парсит строку конфигурации сигнала
        
        Args:
            config_str: Строка вида "variable_name (type)"
            
        Returns:
            SignalMapping объект
            
        Raises:
            SignalConfigError: При ошибке парсинга
        """
        try:
            # Убираем лишние пробелы
            config_str = config_str.strip()
            
            # Ищем открывающую скобку
            if '(' not in config_str or ')' not in config_str:
                raise SignalConfigError(f"Неверный формат конфигурации: {config_str}")
            
            # Разделяем на имя переменной и тип
            parts = config_str.split('(', 1)
            variable_name = parts[0].strip()
            signal_type_str = parts[1].rstrip(')').strip()
            
            # Валидируем имя переменной
            if not SignalValidator.validate_variable_name(variable_name):
                raise SignalConfigError(f"Некорректное имя переменной: {variable_name}")
            
            # Валидируем тип сигнала
            if not SignalValidator.validate_signal_type(signal_type_str):
                raise SignalConfigError(f"Некорректный тип сигнала: {signal_type_str}")
            
            signal_type = SignalType(signal_type_str)
            
            return SignalMapping(
                signal_name="",  # Будет установлено позже
                variable_name=variable_name,
                signal_type=signal_type,
                config={}
            )
            
        except Exception as e:
            if isinstance(e, SignalConfigError):
                raise
            raise SignalConfigError(f"Ошибка парсинга конфигурации '{config_str}': {e}")
    
    @staticmethod
    def parse_uart_data(data: str) -> Dict[str, str]:
        """
        Парсит данные UART в формате "SIGNAL:VALUE"
        
        Args:
            data: Строка данных UART
            
        Returns:
            Словарь сигнал -> значение
            
        Raises:
            SignalProcessingError: При ошибке парсинга
        """
        try:
            result = {}
            lines = data.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if ':' not in line:
                    raise SignalProcessingError(f"Неверный формат данных: {line}")
                
                parts = line.split(':', 1)
                signal_name = parts[0].strip()
                value = parts[1].strip()
                
                if not signal_name:
                    raise SignalProcessingError(f"Пустое имя сигнала в строке: {line}")
                
                result[signal_name] = value
            
            return result
            
        except Exception as e:
            if isinstance(e, SignalProcessingError):
                raise
            raise SignalProcessingError(f"Ошибка парсинга UART данных: {e}")
