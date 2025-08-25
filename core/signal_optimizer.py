#!/usr/bin/env python3
"""
Оптимизированные компоненты для системы обработки сигналов UART
"""

import re
import time
import threading
from typing import Dict, List, Set, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from core.signal_types import SignalType, SignalMapping, SignalValue
from core.interfaces import ISignalProcessor, ISignalValidator, ISignalManager


class PerformanceMetric(Enum):
    """Метрики производительности"""
    PROCESSING_TIME = "processing_time"
    MEMORY_USAGE = "memory_usage"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"


@dataclass
class PerformanceData:
    """Данные о производительности"""
    metric: PerformanceMetric
    value: float
    timestamp: float
    context: Optional[str] = None


class PerformanceMonitor:
    """Монитор производительности системы сигналов"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: Dict[PerformanceMetric, List[PerformanceData]] = {
            metric: [] for metric in PerformanceMetric
        }
        self._lock = threading.Lock()
    
    def record_metric(self, metric: PerformanceMetric, value: float, context: Optional[str] = None):
        """Запись метрики производительности"""
        with self._lock:
            data = PerformanceData(
                metric=metric,
                value=value,
                timestamp=time.time(),
                context=context
            )
            
            self.metrics[metric].append(data)
            
            # Ограничиваем размер истории
            if len(self.metrics[metric]) > self.max_history:
                self.metrics[metric] = self.metrics[metric][-self.max_history:]
    
    def get_average(self, metric: PerformanceMetric, window_seconds: float = 60.0) -> float:
        """Получение среднего значения метрики за период"""
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - window_seconds
            
            values = [
                data.value for data in self.metrics[metric]
                if data.timestamp >= cutoff_time
            ]
            
            return sum(values) / len(values) if values else 0.0
    
    def get_statistics(self) -> Dict[str, float]:
        """Получение статистики производительности"""
        stats = {}
        
        for metric in PerformanceMetric:
            avg_value = self.get_average(metric)
            stats[f"avg_{metric.value}"] = avg_value
            
            # Специальные вычисления для некоторых метрик
            if metric == PerformanceMetric.THROUGHPUT:
                stats["current_throughput"] = avg_value
            elif metric == PerformanceMetric.ERROR_RATE:
                stats["error_percentage"] = avg_value * 100
        
        return stats


class OptimizedSignalParser:
    """Оптимизированный парсер сигналов с кэшированием"""
    
    # Кэшированные регулярные выражения
    _SIGNAL_PATTERN = re.compile(r'^([A-Z_]+):(.+)$')
    _MAPPING_PATTERN = re.compile(r'^([A-Z_]+)\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([a-z]+)\)$')
    
    # Кэш валидных типов
    _VALID_TYPES = {t.value for t in SignalType}
    
    @classmethod
    def parse_signal_data(cls, data: str) -> Optional[tuple[str, str]]:
        """Парсинг данных сигнала с оптимизацией"""
        if not data or not isinstance(data, str):
            return None
        
        # Быстрая проверка на наличие двоеточия
        if ':' not in data:
            return None
        
        match = cls._SIGNAL_PATTERN.match(data.strip())
        if not match:
            return None
        
        signal_name, value = match.groups()
        return signal_name.strip(), value.strip()
    
    @classmethod
    def parse_mapping_string(cls, mapping_str: str) -> Optional[tuple[str, str, str]]:
        """Парсинг строки маппинга с оптимизацией"""
        if not mapping_str or not isinstance(mapping_str, str):
            return None
        
        match = cls._MAPPING_PATTERN.match(mapping_str.strip())
        if not match:
            return None
        
        signal_name, variable_name, signal_type = match.groups()
        
        # Быстрая проверка типа
        if signal_type not in cls._VALID_TYPES:
            return None
        
        return signal_name.strip(), variable_name.strip(), signal_type.strip()


class OptimizedSignalValidator:
    """Оптимизированный валидатор сигналов"""
    
    # Кэш валидных типов
    _VALID_TYPES = {t.value for t in SignalType}
    
    # Кэш валидных имен сигналов (регулярное выражение)
    _SIGNAL_NAME_PATTERN = re.compile(r'^[A-Z_][A-Z0-9_]*$')
    
    # Кэш валидных имен переменных
    _VARIABLE_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    
    @classmethod
    def validate_signal_name(cls, signal_name: str) -> bool:
        """Быстрая валидация имени сигнала"""
        return bool(signal_name and cls._SIGNAL_NAME_PATTERN.match(signal_name))
    
    @classmethod
    def validate_variable_name(cls, variable_name: str) -> bool:
        """Быстрая валидация имени переменной"""
        return bool(variable_name and cls._VARIABLE_NAME_PATTERN.match(variable_name))
    
    @classmethod
    def validate_signal_type(cls, signal_type: str) -> bool:
        """Быстрая валидация типа сигнала"""
        return signal_type in cls._VALID_TYPES
    
    @classmethod
    def validate_signal_value(cls, value: str, signal_type: SignalType) -> bool:
        """Валидация значения сигнала с оптимизацией"""
        if not value:
            return False
        
        try:
            if signal_type == SignalType.FLOAT:
                float(value)
            elif signal_type == SignalType.INT:
                int(value)
            elif signal_type == SignalType.BOOL:
                return value.lower() in ('true', 'false', '1', '0', 'yes', 'no')
            elif signal_type == SignalType.STRING:
                return True  # Любая строка валидна
            return True
        except (ValueError, TypeError):
            return False


class BatchProcessor:
    """Батчевый процессор для оптимизации обработки"""
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.pending_items: List = []
        self.last_flush_time = time.time()
        self._lock = threading.Lock()
        self._flush_callback: Optional[Callable] = None
    
    def set_flush_callback(self, callback: Callable[[List], None]):
        """Установка callback для обработки батча"""
        self._flush_callback = callback
    
    def add_item(self, item) -> bool:
        """Добавление элемента в батч"""
        with self._lock:
            self.pending_items.append(item)
            
            # Проверяем условия для сброса батча
            should_flush = (
                len(self.pending_items) >= self.batch_size or
                time.time() - self.last_flush_time >= self.flush_interval
            )
            
            if should_flush:
                return self._flush_batch()
            
            return True
    
    def _flush_batch(self) -> bool:
        """Сброс батча"""
        if not self.pending_items or not self._flush_callback:
            return True
        
        try:
            items_to_process = self.pending_items.copy()
            self.pending_items.clear()
            self.last_flush_time = time.time()
            
            self._flush_callback(items_to_process)
            return True
        except Exception:
            # Возвращаем элементы обратно в случае ошибки
            self.pending_items.extend(items_to_process)
            return False
    
    def force_flush(self) -> bool:
        """Принудительный сброс батча"""
        with self._lock:
            return self._flush_batch()


class MemoryOptimizer:
    """Оптимизатор использования памяти"""
    
    def __init__(self, max_history_size: int = 1000, cleanup_interval: float = 300.0):
        self.max_history_size = max_history_size
        self.cleanup_interval = cleanup_interval
        self.last_cleanup_time = time.time()
        self._lock = threading.Lock()
    
    def should_cleanup(self) -> bool:
        """Проверка необходимости очистки"""
        return time.time() - self.last_cleanup_time >= self.cleanup_interval
    
    def cleanup_history(self, history_dict: Dict, max_age: float = 3600.0):
        """Очистка истории данных"""
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - max_age
            
            # Удаляем старые записи
            keys_to_remove = []
            for key, value in history_dict.items():
                if hasattr(value, 'timestamp') and value.timestamp < cutoff_time:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del history_dict[key]
            
            # Ограничиваем размер
            if len(history_dict) > self.max_history_size:
                # Сортируем по времени и оставляем только новые
                sorted_items = sorted(
                    history_dict.items(),
                    key=lambda x: getattr(x[1], 'timestamp', 0),
                    reverse=True
                )
                
                history_dict.clear()
                for key, value in sorted_items[:self.max_history_size]:
                    history_dict[key] = value
            
            self.last_cleanup_time = current_time


class OptimizedSignalProcessor(ISignalProcessor):
    """Оптимизированный процессор сигналов"""
    
    def __init__(self, performance_monitor: Optional[PerformanceMonitor] = None):
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.batch_processor = BatchProcessor()
        self.memory_optimizer = MemoryOptimizer()
        
        # Настройка батчевой обработки
        self.batch_processor.set_flush_callback(self._process_batch)
    
    def process_signal(self, signal_name: str, value: str, mapping: SignalMapping) -> Optional[SignalValue]:
        """Обработка сигнала с измерением производительности"""
        start_time = time.time()
        
        try:
            # Валидация
            if not OptimizedSignalValidator.validate_signal_value(value, mapping.signal_type):
                return None
            
            # Конвертация типа
            converted_value = self._convert_value(value, mapping.signal_type)
            if converted_value is None:
                return None
            
            # Создание результата
            result = SignalValue(
                signal_name=signal_name,
                variable_name=mapping.variable_name,
                value=converted_value,
                signal_type=mapping.signal_type,
                timestamp=time.time()
            )
            
            # Измерение производительности
            processing_time = time.time() - start_time
            self.performance_monitor.record_metric(
                PerformanceMetric.PROCESSING_TIME,
                processing_time,
                f"signal_{signal_name}"
            )
            
            return result
            
        except Exception as e:
            # Запись ошибки
            self.performance_monitor.record_metric(
                PerformanceMetric.ERROR_RATE,
                1.0,
                f"error_{signal_name}"
            )
            return None
    
    def _convert_value(self, value: str, signal_type: SignalType):
        """Конвертация значения с оптимизацией"""
        try:
            if signal_type == SignalType.FLOAT:
                return float(value)
            elif signal_type == SignalType.INT:
                return int(value)
            elif signal_type == SignalType.BOOL:
                return value.lower() in ('true', '1', 'yes')
            elif signal_type == SignalType.STRING:
                return value
            else:
                return None
        except (ValueError, TypeError):
            return None
    
    def _process_batch(self, items: List):
        """Обработка батча элементов"""
        # Здесь можно реализовать батчевую обработку
        # для оптимизации производительности
        pass
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Получение статистики производительности"""
        return self.performance_monitor.get_statistics()


class OptimizedSignalManager(ISignalManager):
    """Оптимизированный менеджер сигналов"""
    
    def __init__(self, processor: ISignalProcessor, validator: ISignalValidator, 
                 flag_manager=None, performance_monitor: Optional[PerformanceMonitor] = None):
        self.processor = processor
        self.validator = validator
        self.flag_manager = flag_manager
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.memory_optimizer = MemoryOptimizer()
        
        self._signal_mappings: Dict[str, SignalMapping] = {}
        self._signal_history: Dict[str, SignalValue] = {}
        self._statistics = {
            'total_signals': 0,
            'processed_signals': 0,
            'errors': 0,
            'last_signal': None
        }
        self._lock = threading.Lock()
    
    def register_signals(self, signal_mappings: Dict[str, SignalMapping]) -> bool:
        """Регистрация сигналов с оптимизацией"""
        with self._lock:
            # Валидация всех маппингов
            for signal_name, mapping in signal_mappings.items():
                if not self._validate_mapping(signal_name, mapping):
                    return False
            
            self._signal_mappings.update(signal_mappings)
            return True
    
    def process_incoming_data(self, data: str) -> bool:
        """Обработка входящих данных с оптимизацией"""
        start_time = time.time()
        
        with self._lock:
            self._statistics['total_signals'] += 1
            
            # Парсинг данных
            parsed = OptimizedSignalParser.parse_signal_data(data)
            if not parsed:
                self._statistics['errors'] += 1
                return False
            
            signal_name, value = parsed
            
            # Проверка регистрации сигнала
            if signal_name not in self._signal_mappings:
                self._statistics['errors'] += 1
                return False
            
            mapping = self._signal_mappings[signal_name]
            
            # Обработка сигнала
            result = self.processor.process_signal(signal_name, value, mapping)
            if not result:
                self._statistics['errors'] += 1
                return False
            
            # Обновление переменной
            if self.flag_manager:
                self.flag_manager.set_flag(mapping.variable_name, result.value)
            
            # Сохранение в историю
            self._signal_history[signal_name] = result
            
            # Обновление статистики
            self._statistics['processed_signals'] += 1
            self._statistics['last_signal'] = signal_name
            
            # Измерение производительности
            processing_time = time.time() - start_time
            self.performance_monitor.record_metric(
                PerformanceMetric.PROCESSING_TIME,
                processing_time,
                f"manager_{signal_name}"
            )
            
            # Проверка необходимости очистки памяти
            if self.memory_optimizer.should_cleanup():
                self.memory_optimizer.cleanup_history(self._signal_history)
            
            return True
    
    def _validate_mapping(self, signal_name: str, mapping: SignalMapping) -> bool:
        """Валидация маппинга сигнала"""
        return (
            OptimizedSignalValidator.validate_signal_name(signal_name) and
            OptimizedSignalValidator.validate_variable_name(mapping.variable_name) and
            OptimizedSignalValidator.validate_signal_type(mapping.signal_type.value)
        )
    
    def get_signal_mappings(self) -> Dict[str, SignalMapping]:
        """Получение маппингов сигналов"""
        with self._lock:
            return self._signal_mappings.copy()
    
    def get_statistics(self) -> Dict[str, any]:
        """Получение статистики с метриками производительности"""
        with self._lock:
            stats = self._statistics.copy()
            
            # Добавляем метрики производительности
            perf_stats = self.performance_monitor.get_statistics()
            stats.update(perf_stats)
            
            return stats
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Получение статистики производительности"""
        return self.performance_monitor.get_statistics()
