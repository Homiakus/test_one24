"""
Главный менеджер сигналов для системы обработки входящих сигналов UART
"""
import logging
import time
from typing import Dict, List, Optional, Any
from .interfaces import ISignalManager
from .signal_types import SignalType, SignalMapping, SignalValue, SignalResult
from .signal_processor import SignalProcessor
from .signal_validator import SignalValidator
from .signal_types import SignalParser


class SignalManager(ISignalManager):
    """
    Главный менеджер сигналов.
    
    Реализует интерфейс ISignalManager для управления сигналами,
    включая регистрацию, обработку и мониторинг.
    """
    
    def __init__(self, flag_manager=None):
        """
        Инициализация менеджера сигналов.
        
        Args:
            flag_manager: Менеджер флагов для обновления переменных
        """
        self.logger = logging.getLogger(__name__)
        self.flag_manager = flag_manager
        
        # Компоненты системы
        self.validator = SignalValidator()
        self.processor = SignalProcessor()
        
        # Хранилище данных
        self._signal_mappings: Dict[str, SignalMapping] = {}
        self._signal_values: Dict[str, SignalValue] = {}
        self._variables: Dict[str, Any] = {}
        
        # Статистика
        self._processed_signals = 0
        self._error_count = 0
        self._last_update_time = time.time()
    
    def register_signal(self, signal_name: str, mapping: SignalMapping) -> bool:
        """
        Зарегистрировать сигнал.
        
        Args:
            signal_name: Имя сигнала
            mapping: Маппинг сигнала
            
        Returns:
            True если регистрация успешна, False в противном случае
        """
        try:
            # Валидируем маппинг
            if not self.validator.validate_signal_mapping(mapping):
                self.logger.error(f"Некорректный маппинг сигнала: {signal_name}")
                return False
            
            # Устанавливаем имя сигнала в маппинг
            mapping.signal_name = signal_name
            
            # Регистрируем маппинг
            self._signal_mappings[signal_name] = mapping
            
            # Регистрируем в процессоре
            self.processor.register_signal_mapping(signal_name, mapping.signal_type)
            
            self.logger.info(f"Зарегистрирован сигнал: {signal_name} -> {mapping.variable_name} ({mapping.signal_type})")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка регистрации сигнала {signal_name}: {e}")
            return False
    
    def unregister_signal(self, signal_name: str) -> bool:
        """
        Отменить регистрацию сигнала.
        
        Args:
            signal_name: Имя сигнала
            
        Returns:
            True если отмена регистрации успешна, False в противном случае
        """
        try:
            # Удаляем из маппингов
            if signal_name in self._signal_mappings:
                del self._signal_mappings[signal_name]
            
            # Удаляем из процессора
            self.processor.unregister_signal_mapping(signal_name)
            
            # Удаляем значение сигнала
            if signal_name in self._signal_values:
                del self._signal_values[signal_name]
            
            self.logger.info(f"Отменена регистрация сигнала: {signal_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка отмены регистрации сигнала {signal_name}: {e}")
            return False
    
    def process_incoming_data(self, data: str) -> List[SignalResult]:
        """
        Обработать входящие данные.
        
        Args:
            data: Строка данных UART
            
        Returns:
            Список результатов обработки сигналов
        """
        try:
            self.logger.debug(f"Обработка входящих данных: {data}")
            
            # Обрабатываем данные через процессор
            results = self.processor.process_uart_data(data)
            
            # Обновляем статистику
            self._processed_signals += len(results)
            self._last_update_time = time.time()
            
            # Обрабатываем результаты
            for result in results:
                if result.success:
                    self._update_signal_value(result)
                    self._update_variable(result)
                else:
                    self._error_count += 1
                    self.logger.warning(f"Ошибка обработки сигнала {result.signal_name}: {result.error_message}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки входящих данных: {e}")
            return []
    
    def get_signal_value(self, signal_name: str) -> Optional[SignalValue]:
        """
        Получить значение сигнала.
        
        Args:
            signal_name: Имя сигнала
            
        Returns:
            Значение сигнала или None если не найдено
        """
        return self._signal_values.get(signal_name)
    
    def get_all_signal_values(self) -> Dict[str, SignalValue]:
        """
        Получить все значения сигналов.
        
        Returns:
            Словарь значений сигналов
        """
        return self._signal_values.copy()
    
    def get_signal_mappings(self) -> Dict[str, SignalMapping]:
        """
        Получить маппинги сигналов.
        
        Returns:
            Словарь маппингов сигналов
        """
        return self._signal_mappings.copy()
    
    def update_variable(self, variable_name: str, value: Any) -> bool:
        """
        Обновить переменную.
        
        Args:
            variable_name: Имя переменной
            value: Новое значение
            
        Returns:
            True если обновление успешно, False в противном случае
        """
        try:
            # Обновляем в локальном хранилище
            self._variables[variable_name] = value
            
            # Обновляем в FlagManager если доступен
            if self.flag_manager and hasattr(self.flag_manager, 'set_flag'):
                self.flag_manager.set_flag(variable_name, value)
            
            self.logger.debug(f"Обновлена переменная: {variable_name} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления переменной {variable_name}: {e}")
            return False
    
    def get_variable_value(self, variable_name: str) -> Optional[Any]:
        """
        Получить значение переменной.
        
        Args:
            variable_name: Имя переменной
            
        Returns:
            Значение переменной или None если не найдено
        """
        return self._variables.get(variable_name)
    
    def get_all_variables(self) -> Dict[str, Any]:
        """
        Получить все переменные.
        
        Returns:
            Словарь всех переменных
        """
        return self._variables.copy()
    
    def load_config_from_dict(self, config: Dict[str, str]) -> bool:
        """
        Загрузить конфигурацию сигналов из словаря.
        
        Args:
            config: Словарь конфигурации (сигнал -> переменная (тип))
            
        Returns:
            True если загрузка успешна, False в противном случае
        """
        try:
            # Валидируем конфигурацию
            if not self.validator.validate_signal_config(config):
                self.logger.error("Некорректная конфигурация сигналов")
                return False
            
            # Очищаем текущие маппинги
            self._signal_mappings.clear()
            self.processor.clear_mappings()
            
            # Загружаем новые маппинги
            for signal_name, config_str in config.items():
                try:
                    # Парсим конфигурацию
                    mapping = SignalParser.parse_signal_config(config_str)
                    mapping.signal_name = signal_name
                    
                    # Регистрируем сигнал
                    if not self.register_signal(signal_name, mapping):
                        self.logger.error(f"Не удалось зарегистрировать сигнал: {signal_name}")
                        return False
                        
                except Exception as e:
                    self.logger.error(f"Ошибка парсинга конфигурации сигнала {signal_name}: {e}")
                    return False
            
            self.logger.info(f"Загружена конфигурация {len(config)} сигналов")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации сигналов: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику работы менеджера сигналов.
        
        Returns:
            Словарь со статистикой
        """
        return {
            'total_signals': len(self._signal_mappings),
            'processed_signals': self._processed_signals,
            'error_count': self._error_count,
            'last_update_time': self._last_update_time,
            'signal_values_count': len(self._signal_values),
            'variables_count': len(self._variables)
        }
    
    def clear_all(self) -> None:
        """Очистить все данные"""
        try:
            self._signal_mappings.clear()
            self._signal_values.clear()
            self._variables.clear()
            self.processor.clear_mappings()
            self._processed_signals = 0
            self._error_count = 0
            self.logger.info("Очищены все данные менеджера сигналов")
        except Exception as e:
            self.logger.error(f"Ошибка очистки данных: {e}")
    
    def _update_signal_value(self, result: SignalResult) -> None:
        """
        Обновить значение сигнала.
        
        Args:
            result: Результат обработки сигнала
        """
        try:
            signal_value = SignalValue(
                signal_name=result.signal_name,
                value=result.value,
                signal_type=result.signal_type,
                timestamp=result.timestamp or time.time(),
                raw_data=str(result.value)
            )
            
            self._signal_values[result.signal_name] = signal_value
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления значения сигнала {result.signal_name}: {e}")
    
    def _update_variable(self, result: SignalResult) -> None:
        """
        Обновить переменную на основе результата обработки сигнала.
        
        Args:
            result: Результат обработки сигнала
        """
        try:
            if result.variable_name:
                self.update_variable(result.variable_name, result.value)
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления переменной {result.variable_name}: {e}")
