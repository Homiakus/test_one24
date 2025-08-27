"""
Метрики и мониторинг для DI контейнера.

Содержит компоненты для:
- Сбора метрик производительности
- Мониторинга использования сервисов
- Анализа производительности разрешения зависимостей
- Отчетов о состоянии контейнера
"""

import time
import threading
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass, field
from collections import defaultdict, deque

from .types import ServiceInstance


@dataclass
class ServiceMetrics:
    """
    Метрики отдельного сервиса.
    
    Attributes:
        service_name: Имя сервиса
        registration_time: Время регистрации
        first_resolution_time: Время первого разрешения
        last_resolution_time: Время последнего разрешения
        resolution_count: Количество разрешений
        total_resolution_time: Общее время разрешения
        average_resolution_time: Среднее время разрешения
        error_count: Количество ошибок
        last_error: Последняя ошибка
        dependencies_resolved: Количество разрешенных зависимостей
    """
    service_name: str
    registration_time: float = field(default_factory=time.time)
    first_resolution_time: Optional[float] = None
    last_resolution_time: Optional[float] = None
    resolution_count: int = 0
    total_resolution_time: float = 0.0
    average_resolution_time: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None
    dependencies_resolved: int = 0
    
    def update_resolution_time(self, resolution_time: float) -> None:
        """Обновление времени разрешения"""
        self.last_resolution_time = time.time()
        self.resolution_count += 1
        self.total_resolution_time += resolution_time
        self.average_resolution_time = self.total_resolution_time / self.resolution_count
        
        if self.first_resolution_time is None:
            self.first_resolution_time = self.last_resolution_time
    
    def record_error(self, error: str) -> None:
        """Запись ошибки"""
        self.error_count += 1
        self.last_error = error
    
    def increment_dependencies(self) -> None:
        """Увеличение счетчика зависимостей"""
        self.dependencies_resolved += 1


@dataclass
class ContainerMetrics:
    """
    Общие метрики контейнера.
    
    Attributes:
        total_services: Общее количество сервисов
        singleton_services: Количество singleton сервисов
        transient_services: Количество transient сервисов
        total_resolutions: Общее количество разрешений
        total_errors: Общее количество ошибок
        startup_time: Время запуска контейнера
        last_activity: Время последней активности
        memory_usage: Использование памяти (если доступно)
    """
    total_services: int = 0
    singleton_services: int = 0
    transient_services: int = 0
    total_resolutions: int = 0
    total_errors: int = 0
    startup_time: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    memory_usage: Optional[float] = None


class DIMetrics:
    """
    Система метрик для DI контейнера.
    
    Отвечает за:
    - Сбор метрик производительности
    - Мониторинг использования сервисов
    - Анализ производительности
    - Генерацию отчетов
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        self._lock = threading.RLock()
        self._service_metrics: Dict[Type, ServiceMetrics] = {}
        self._container_metrics = ContainerMetrics()
        self._resolution_times: deque = deque(maxlen=1000)  # Последние 1000 разрешений
        self._error_history: deque = deque(maxlen=100)      # Последние 100 ошибок
        
    def register_service(self, interface: Type, service_instance: ServiceInstance) -> None:
        """Регистрация сервиса для отслеживания метрик"""
        with self._lock:
            service_name = interface.__name__
            metrics = ServiceMetrics(service_name)
            self._service_metrics[interface] = metrics
            
            # Обновляем общие метрики
            self._container_metrics.total_services += 1
            if service_instance.is_singleton():
                self._container_metrics.singleton_services += 1
            else:
                self._container_metrics.transient_services += 1
            
            self._update_activity()
    
    def record_resolution_start(self, interface: Type) -> float:
        """Запись начала разрешения сервиса"""
        return time.time()
    
    def record_resolution_complete(self, interface: Type, start_time: float, 
                                 success: bool = True, error: Optional[str] = None,
                                 dependencies_count: int = 0) -> None:
        """Запись завершения разрешения сервиса"""
        with self._lock:
            if interface not in self._service_metrics:
                return
            
            metrics = self._service_metrics[interface]
            resolution_time = time.time() - start_time
            
            # Обновляем метрики сервиса
            metrics.update_resolution_time(resolution_time)
            metrics.dependencies_resolved += dependencies_count
            
            # Обновляем общие метрики
            self._container_metrics.total_resolutions += 1
            self._resolution_times.append(resolution_time)
            
            # Записываем ошибку если есть
            if not success and error:
                metrics.record_error(error)
                self._container_metrics.total_errors += 1
                self._error_history.append({
                    'service': interface.__name__,
                    'error': error,
                    'timestamp': time.time()
                })
            
            self._update_activity()
    
    def record_dependency_resolution(self, interface: Type, dependency_interface: Type) -> None:
        """Запись разрешения зависимости"""
        with self._lock:
            if interface in self._service_metrics:
                self._service_metrics[interface].increment_dependencies()
    
    def get_service_metrics(self, interface: Type) -> Optional[ServiceMetrics]:
        """Получение метрик конкретного сервиса"""
        with self._lock:
            return self._service_metrics.get(interface)
    
    def get_all_service_metrics(self) -> Dict[str, ServiceMetrics]:
        """Получение метрик всех сервисов"""
        with self._lock:
            return {
                interface.__name__: metrics 
                for interface, metrics in self._service_metrics.items()
            }
    
    def get_container_metrics(self) -> ContainerMetrics:
        """Получение общих метрик контейнера"""
        with self._lock:
            return ContainerMetrics(
                total_services=self._container_metrics.total_services,
                singleton_services=self._container_metrics.singleton_services,
                transient_services=self._container_metrics.transient_services,
                total_resolutions=self._container_metrics.total_resolutions,
                total_errors=self._container_metrics.total_errors,
                startup_time=self._container_metrics.startup_time,
                last_activity=self._container_metrics.last_activity,
                memory_usage=self._get_memory_usage()
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Получение сводки по производительности"""
        with self._lock:
            if not self._resolution_times:
                return {
                    'average_resolution_time': 0.0,
                    'min_resolution_time': 0.0,
                    'max_resolution_time': 0.0,
                    'total_resolutions': 0
                }
            
            times = list(self._resolution_times)
            return {
                'average_resolution_time': sum(times) / len(times),
                'min_resolution_time': min(times),
                'max_resolution_time': max(times),
                'total_resolutions': len(times)
            }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Получение сводки по ошибкам"""
        with self._lock:
            error_counts = defaultdict(int)
            for error_record in self._error_history:
                error_counts[error_record['error']] += 1
            
            return {
                'total_errors': self._container_metrics.total_errors,
                'error_types': dict(error_counts),
                'recent_errors': list(self._error_history)[-10:]  # Последние 10 ошибок
            }
    
    def get_service_usage_report(self) -> List[Dict[str, Any]]:
        """Получение отчета об использовании сервисов"""
        with self._lock:
            report = []
            for interface, metrics in self._service_metrics.items():
                report.append({
                    'service_name': metrics.service_name,
                    'resolution_count': metrics.resolution_count,
                    'average_resolution_time': metrics.average_resolution_time,
                    'error_count': metrics.error_count,
                    'dependencies_resolved': metrics.dependencies_resolved,
                    'last_used': metrics.last_resolution_time,
                    'uptime': time.time() - metrics.registration_time if metrics.registration_time else 0
                })
            
            # Сортируем по количеству использований
            report.sort(key=lambda x: x['resolution_count'], reverse=True)
            return report
    
    def reset_metrics(self) -> None:
        """Сброс всех метрик"""
        with self._lock:
            self._service_metrics.clear()
            self._container_metrics = ContainerMetrics()
            self._resolution_times.clear()
            self._error_history.clear()
    
    def export_metrics(self) -> Dict[str, Any]:
        """Экспорт всех метрик в словарь"""
        with self._lock:
            return {
                'container': self.get_container_metrics().__dict__,
                'services': {
                    name: metrics.__dict__ 
                    for name, metrics in self.get_all_service_metrics().items()
                },
                'performance': self.get_performance_summary(),
                'errors': self.get_error_summary(),
                'export_time': time.time()
            }
    
    def _update_activity(self) -> None:
        """Обновление времени последней активности"""
        self._container_metrics.last_activity = time.time()
    
    def _get_memory_usage(self) -> Optional[float]:
        """Получение использования памяти (если доступно)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # В МБ
        except ImportError:
            return None

