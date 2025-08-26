"""
Обработчик сигналов для системы обработки входящих сигналов UART
"""
import logging
import time
from typing import List, Any, Dict
from core.interfaces import ISignalProcessor
from .types import SignalType, SignalResult, SignalTypeConverter, SignalParser


class SignalProcessor(ISignalProcessor):
    """
    Обработчик сигналов.
    
    Реализует интерфейс ISignalProcessor для обработки
    входящих сигналов UART, включая парсинг, валидацию и конвертацию.
    """
    
    def __init__(self):
        """Инициализация обработчика сигналов"""
        self.logger = logging.getLogger(__name__)
        self._signal_mappings: Dict[str, SignalType] = {}
    
    def process_signal(self, signal_name: str, value: str, signal_type: SignalType) -> SignalResult:
        """
        Обработать сигнал.
        
        Args:
            signal_name: Имя сигнала
            value: Строковое значение сигнала
            signal_type: Тип данных сигнала
            
        Returns:
            Результат обработки сигнала
        """
        try:
            self.logger.debug(f"Обработка сигнала: {signal_name} = {value} ({signal_type})")
            
            # Валидируем сигнал
            if not self.validate_signal(signal_name, value, signal_type):
                return SignalResult(
                    success=False,
                    signal_name=signal_name,
                    variable_name="",
                    value=None,
                    signal_type=signal_type,
                    error_message=f"Ошибка валидации сигнала {signal_name}",
                    timestamp=time.time()
                )
            
            # Конвертируем значение
            converted_value = self.convert_signal_value(value, signal_type)
            
            # Получаем имя переменной из маппинга
            variable_name = self._get_variable_name(signal_name)
            
            return SignalResult(
                success=True,
                signal_name=signal_name,
                variable_name=variable_name,
                value=converted_value,
                signal_type=signal_type,
                timestamp=time.time()
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки сигнала {signal_name}: {e}")
            return SignalResult(
                success=False,
                signal_name=signal_name,
                variable_name="",
                value=None,
                signal_type=signal_type,
                error_message=str(e),
                timestamp=time.time()
            )
    
    def process_uart_data(self, data: str) -> List[SignalResult]:
        """
        Обработать данные UART.
        
        Args:
            data: Строка данных UART в формате "SIGNAL:VALUE"
            
        Returns:
            Список результатов обработки сигналов
        """
        try:
            self.logger.debug(f"Обработка UART данных: {data}")
            
            # Парсим данные UART
            signal_data = SignalParser.parse_uart_data(data)
            
            results = []
            for signal_name, value in signal_data.items():
                # Получаем тип сигнала из маппинга
                signal_type = self._get_signal_type(signal_name)
                if signal_type is None:
                    self.logger.warning(f"Неизвестный сигнал: {signal_name}")
                    continue
                
                # Обрабатываем сигнал
                result = self.process_signal(signal_name, value, signal_type)
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки UART данных: {e}")
            return []
    
    def validate_signal(self, signal_name: str, value: str, signal_type: SignalType) -> bool:
        """
        Валидировать сигнал.
        
        Args:
            signal_name: Имя сигнала
            value: Строковое значение сигнала
            signal_type: Тип данных сигнала
            
        Returns:
            True если сигнал валиден, False в противном случае
        """
        try:
            # Проверяем, что сигнал зарегистрирован
            if signal_name not in self._signal_mappings:
                self.logger.warning(f"Незарегистрированный сигнал: {signal_name}")
                return False
            
            # Проверяем, что тип сигнала соответствует зарегистрированному
            if self._signal_mappings[signal_name] != signal_type:
                self.logger.warning(f"Несоответствие типа сигнала {signal_name}: ожидается {self._signal_mappings[signal_name]}, получен {signal_type}")
                return False
            
            # Проверяем, что значение не пустое
            if not value or not value.strip():
                self.logger.warning(f"Пустое значение сигнала: {signal_name}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации сигнала {signal_name}: {e}")
            return False
    
    def convert_signal_value(self, value: str, signal_type: SignalType) -> Any:
        """
        Конвертировать значение сигнала.
        
        Args:
            value: Строковое значение сигнала
            signal_type: Тип данных сигнала
            
        Returns:
            Конвертированное значение
            
        Raises:
            Exception: При ошибке конвертации
        """
        try:
            return SignalTypeConverter.convert_value(value, signal_type)
        except Exception as e:
            self.logger.error(f"Ошибка конвертации значения '{value}' в тип {signal_type}: {e}")
            raise
    
    def register_signal_mapping(self, signal_name: str, signal_type: SignalType) -> None:
        """
        Зарегистрировать маппинг сигнала.
        
        Args:
            signal_name: Имя сигнала
            signal_type: Тип данных сигнала
        """
        try:
            self._signal_mappings[signal_name] = signal_type
            self.logger.info(f"Зарегистрирован маппинг сигнала: {signal_name} -> {signal_type}")
        except Exception as e:
            self.logger.error(f"Ошибка регистрации маппинга сигнала {signal_name}: {e}")
    
    def unregister_signal_mapping(self, signal_name: str) -> bool:
        """
        Отменить регистрацию маппинга сигнала.
        
        Args:
            signal_name: Имя сигнала
            
        Returns:
            True если маппинг был удален, False в противном случае
        """
        try:
            if signal_name in self._signal_mappings:
                del self._signal_mappings[signal_name]
                self.logger.info(f"Удален маппинг сигнала: {signal_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Ошибка удаления маппинга сигнала {signal_name}: {e}")
            return False
    
    def get_signal_mappings(self) -> Dict[str, SignalType]:
        """
        Получить все зарегистрированные маппинги сигналов.
        
        Returns:
            Словарь маппингов сигналов
        """
        return self._signal_mappings.copy()
    
    def _get_signal_type(self, signal_name: str) -> SignalType:
        """
        Получить тип сигнала по имени.
        
        Args:
            signal_name: Имя сигнала
            
        Returns:
            Тип сигнала или None если не найден
        """
        return self._signal_mappings.get(signal_name)
    
    def _get_variable_name(self, signal_name: str) -> str:
        """
        Получить имя переменной по имени сигнала.
        
        Args:
            signal_name: Имя сигнала
            
        Returns:
            Имя переменной (пока возвращаем имя сигнала)
        """
        # TODO: Реализовать маппинг сигнал -> переменная
        return signal_name.lower()
    
    def clear_mappings(self) -> None:
        """Очистить все маппинги сигналов"""
        try:
            self._signal_mappings.clear()
            self.logger.info("Очищены все маппинги сигналов")
        except Exception as e:
            self.logger.error(f"Ошибка очистки маппингов сигналов: {e}")
    
    def get_registered_signals(self) -> List[str]:
        """
        Получить список зарегистрированных сигналов.
        
        Returns:
            Список имен зарегистрированных сигналов
        """
        return list(self._signal_mappings.keys())
