"""
Валидатор сигналов для системы обработки входящих сигналов UART
"""
import logging
from typing import Dict, Any, Optional, Union
from .interfaces import ISignalValidator
from .signal_types import SignalType, SignalMapping, SignalValidator as BaseSignalValidator


class SignalValidator(ISignalValidator):
    """
    Валидатор сигналов.
    
    Реализует интерфейс ISignalValidator для валидации
    сигналов, включая проверку имен, типов и значений.
    """
    
    def __init__(self):
        """Инициализация валидатора сигналов"""
        self.logger = logging.getLogger(__name__)
        self._supported_types = list(SignalType)
    
    def validate_signal_name(self, signal_name: str) -> bool:
        """
        Валидация имени сигнала.
        
        Args:
            signal_name: Имя сигнала для валидации
            
        Returns:
            True если имя корректно, False в противном случае
        """
        try:
            result = BaseSignalValidator.validate_signal_name(signal_name)
            if not result:
                self.logger.warning(f"Некорректное имя сигнала: {signal_name}")
            return result
        except Exception as e:
            self.logger.error(f"Ошибка валидации имени сигнала '{signal_name}': {e}")
            return False
    
    def validate_signal_type(self, signal_type: SignalType) -> bool:
        """
        Валидация типа сигнала.
        
        Args:
            signal_type: Тип сигнала для валидации
            
        Returns:
            True если тип поддерживается, False в противном случае
        """
        try:
            result = signal_type in self._supported_types
            if not result:
                self.logger.warning(f"Неподдерживаемый тип сигнала: {signal_type}")
            return result
        except Exception as e:
            self.logger.error(f"Ошибка валидации типа сигнала '{signal_type}': {e}")
            return False
    
    def validate_signal_value(self, value: Any, signal_type: SignalType) -> bool:
        """
        Валидация значения сигнала.
        
        Args:
            value: Значение для валидации
            signal_type: Тип сигнала
            
        Returns:
            True если значение корректно, False в противном случае
        """
        try:
            if signal_type == SignalType.FLOAT:
                return isinstance(value, (int, float)) and not isinstance(value, bool)
            elif signal_type == SignalType.INT:
                return isinstance(value, int) and not isinstance(value, bool)
            elif signal_type == SignalType.STRING:
                return isinstance(value, str)
            elif signal_type == SignalType.BOOL:
                return isinstance(value, bool)
            elif signal_type == SignalType.JSON:
                return isinstance(value, (dict, list))
            else:
                self.logger.warning(f"Неизвестный тип сигнала для валидации: {signal_type}")
                return False
        except Exception as e:
            self.logger.error(f"Ошибка валидации значения '{value}' для типа {signal_type}: {e}")
            return False
    
    def validate_signal_mapping(self, mapping: SignalMapping) -> bool:
        """
        Валидация маппинга сигнала.
        
        Args:
            mapping: Маппинг сигнала для валидации
            
        Returns:
            True если маппинг корректный, False в противном случае
        """
        try:
            # Проверяем имя сигнала
            if not self.validate_signal_name(mapping.signal_name):
                return False
            
            # Проверяем имя переменной
            if not BaseSignalValidator.validate_variable_name(mapping.variable_name):
                self.logger.warning(f"Некорректное имя переменной: {mapping.variable_name}")
                return False
            
            # Проверяем тип сигнала
            if not self.validate_signal_type(mapping.signal_type):
                return False
            
            # Проверяем конфигурацию
            if not isinstance(mapping.config, dict):
                self.logger.warning(f"Некорректная конфигурация маппинга: {mapping.config}")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Ошибка валидации маппинга сигнала: {e}")
            return False
    
    def validate_signal_config(self, config: Dict[str, str]) -> bool:
        """
        Валидация конфигурации сигналов.
        
        Args:
            config: Конфигурация сигналов (сигнал -> переменная (тип))
            
        Returns:
            True если конфигурация корректная, False в противном случае
        """
        try:
            if not isinstance(config, dict):
                self.logger.error("Конфигурация сигналов должна быть словарем")
                return False
            
            # Проверяем каждую запись в конфигурации
            for signal_name, config_str in config.items():
                # Проверяем имя сигнала
                if not self.validate_signal_name(signal_name):
                    self.logger.error(f"Некорректное имя сигнала в конфигурации: {signal_name}")
                    return False
                
                # Проверяем строку конфигурации
                if not isinstance(config_str, str):
                    self.logger.error(f"Некорректная строка конфигурации для сигнала {signal_name}: {config_str}")
                    return False
                
                # Проверяем формат конфигурации
                if '(' not in config_str or ')' not in config_str:
                    self.logger.error(f"Неверный формат конфигурации для сигнала {signal_name}: {config_str}")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Ошибка валидации конфигурации сигналов: {e}")
            return False
    
    def validate_value_range(self, value: Union[float, int], min_value: Optional[Union[float, int]], 
                           max_value: Optional[Union[float, int]]) -> bool:
        """
        Валидация значения по диапазону.
        
        Args:
            value: Значение для проверки
            min_value: Минимальное значение
            max_value: Максимальное значение
            
        Returns:
            True если значение в диапазоне, False в противном случае
        """
        try:
            return BaseSignalValidator.validate_value_range(value, min_value, max_value)
        except Exception as e:
            self.logger.error(f"Ошибка валидации диапазона значения {value}: {e}")
            return False
    
    def get_supported_types(self) -> list:
        """
        Получить список поддерживаемых типов сигналов.
        
        Returns:
            Список поддерживаемых типов
        """
        return self._supported_types.copy()
    
    def add_supported_type(self, signal_type: SignalType) -> None:
        """
        Добавить поддерживаемый тип сигнала.
        
        Args:
            signal_type: Тип сигнала для добавления
        """
        if signal_type not in self._supported_types:
            self._supported_types.append(signal_type)
            self.logger.info(f"Добавлен поддерживаемый тип сигнала: {signal_type}")
    
    def remove_supported_type(self, signal_type: SignalType) -> None:
        """
        Удалить поддерживаемый тип сигнала.
        
        Args:
            signal_type: Тип сигнала для удаления
        """
        if signal_type in self._supported_types:
            self._supported_types.remove(signal_type)
            self.logger.info(f"Удален поддерживаемый тип сигнала: {signal_type}")
