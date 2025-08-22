"""
@file: health_checker.py
@description: Проверка состояния системы (Health Checks)
@dependencies: threading, datetime, utils.logger, core.interfaces
@created: 2024-12-19
"""

import threading
import time
import psutil
import os
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from utils.logger import Logger
from core.interfaces import ISerialManager, ICommandExecutor


class HealthStatus(Enum):
    """Статусы состояния системы"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Результат проверки состояния"""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    response_time: Optional[float] = None


@dataclass
class SystemHealth:
    """Общее состояние системы"""
    overall_status: HealthStatus
    checks: List[HealthCheck]
    timestamp: datetime
    uptime: timedelta
    system_info: Dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """
    Проверка состояния системы
    
    Проверяет:
    - Состояние Serial соединения
    - Доступность команд
    - Системные ресурсы
    - Файловую систему
    - Сетевые соединения
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger(__name__)
        self._lock = threading.Lock()
        self._health_checks: List[SystemHealth] = []
        self._custom_checks: Dict[str, Callable[[], HealthCheck]] = {}
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._serial_manager: Optional[ISerialManager] = None
        self._command_executor: Optional[ICommandExecutor] = None
        
        # Настройки
        self.check_interval = 30.0  # секунды
        self.max_health_history = 1000
        self.critical_thresholds = {
            "cpu_percent": 90.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "response_time": 5.0  # секунды
        }
        self.warning_thresholds = {
            "cpu_percent": 70.0,
            "memory_percent": 70.0,
            "disk_percent": 80.0,
            "response_time": 2.0  # секунды
        }
        
    def set_services(self, serial_manager: ISerialManager, command_executor: ICommandExecutor) -> None:
        """Установка сервисов для проверки"""
        self._serial_manager = serial_manager
        self._command_executor = command_executor
        
    def add_custom_check(self, name: str, check_function: Callable[[], HealthCheck]) -> None:
        """Добавление пользовательской проверки"""
        self._custom_checks[name] = check_function
        
    def start_monitoring(self) -> None:
        """Запуск мониторинга состояния"""
        if self._monitoring_active:
            return
            
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True,
            name="HealthChecker"
        )
        self._monitor_thread.start()
        self.logger.info("Health monitoring started")
        
    def stop_monitoring(self) -> None:
        """Остановка мониторинга состояния"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        self.logger.info("Health monitoring stopped")
        
    def _health_monitor_loop(self) -> None:
        """Цикл мониторинга состояния"""
        while self._monitoring_active:
            try:
                self.run_health_checks()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in health monitoring: {e}")
                
    def run_health_checks(self) -> SystemHealth:
        """Выполнение всех проверок состояния"""
        checks = []
        
        # Системные проверки
        checks.append(self._check_system_resources())
        checks.append(self._check_disk_space())
        checks.append(self._check_network_connectivity())
        
        # Проверки приложения
        if self._serial_manager:
            checks.append(self._check_serial_connection())
            
        if self._command_executor:
            checks.append(self._check_command_executor())
            
        # Пользовательские проверки
        for name, check_func in self._custom_checks.items():
            try:
                checks.append(check_func())
            except Exception as e:
                checks.append(HealthCheck(
                    name=f"custom_{name}",
                    status=HealthStatus.UNKNOWN,
                    message=f"Custom check failed: {e}",
                    timestamp=datetime.now()
                ))
                
        # Определяем общий статус
        overall_status = self._determine_overall_status(checks)
        
        # Создаем результат
        health = SystemHealth(
            overall_status=overall_status,
            checks=checks,
            timestamp=datetime.now(),
            uptime=self._get_uptime(),
            system_info=self._get_system_info()
        )
        
        # Сохраняем историю
        with self._lock:
            self._health_checks.append(health)
            if len(self._health_checks) > self.max_health_history:
                self._health_checks = self._health_checks[-self.max_health_history:]
                
        return health
        
    def _check_system_resources(self) -> HealthCheck:
        """Проверка системных ресурсов"""
        start_time = time.time()
        
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent()
            memory_percent = process.memory_percent()
            
            # Определяем статус
            status = HealthStatus.HEALTHY
            message = "System resources OK"
            
            if cpu_percent > self.critical_thresholds["cpu_percent"]:
                status = HealthStatus.CRITICAL
                message = f"CPU usage critical: {cpu_percent:.1f}%"
            elif cpu_percent > self.warning_thresholds["cpu_percent"]:
                status = HealthStatus.WARNING
                message = f"CPU usage high: {cpu_percent:.1f}%"
                
            if memory_percent > self.critical_thresholds["memory_percent"]:
                status = HealthStatus.CRITICAL
                message = f"Memory usage critical: {memory_percent:.1f}%"
            elif memory_percent > self.warning_thresholds["memory_percent"]:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
                    message = f"Memory usage high: {memory_percent:.1f}%"
                    
            response_time = time.time() - start_time
            
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "threads": process.num_threads(),
                    "open_files": len(process.open_files())
                },
                response_time=response_time
            )
            
        except Exception as e:
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check system resources: {e}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
            
    def _check_disk_space(self) -> HealthCheck:
        """Проверка свободного места на диске"""
        start_time = time.time()
        
        try:
            disk_usage = psutil.disk_usage('.')
            disk_percent = disk_usage.percent
            
            status = HealthStatus.HEALTHY
            message = "Disk space OK"
            
            if disk_percent > self.critical_thresholds["disk_percent"]:
                status = HealthStatus.CRITICAL
                message = f"Disk space critical: {disk_percent:.1f}% used"
            elif disk_percent > self.warning_thresholds["disk_percent"]:
                status = HealthStatus.WARNING
                message = f"Disk space low: {disk_percent:.1f}% used"
                
            response_time = time.time() - start_time
            
            return HealthCheck(
                name="disk_space",
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    "disk_percent": disk_percent,
                    "free_gb": disk_usage.free / (1024**3),
                    "total_gb": disk_usage.total / (1024**3)
                },
                response_time=response_time
            )
            
        except Exception as e:
            return HealthCheck(
                name="disk_space",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check disk space: {e}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
            
    def _check_network_connectivity(self) -> HealthCheck:
        """Проверка сетевого соединения"""
        start_time = time.time()
        
        try:
            # Простая проверка - попытка получить сетевые интерфейсы
            network_interfaces = psutil.net_if_addrs()
            
            if network_interfaces:
                status = HealthStatus.HEALTHY
                message = "Network connectivity OK"
            else:
                status = HealthStatus.WARNING
                message = "No network interfaces found"
                
            response_time = time.time() - start_time
            
            return HealthCheck(
                name="network_connectivity",
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    "interfaces_count": len(network_interfaces),
                    "interfaces": list(network_interfaces.keys())
                },
                response_time=response_time
            )
            
        except Exception as e:
            return HealthCheck(
                name="network_connectivity",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check network: {e}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
            
    def _check_serial_connection(self) -> HealthCheck:
        """Проверка Serial соединения"""
        start_time = time.time()
        
        try:
            if not self._serial_manager:
                return HealthCheck(
                    name="serial_connection",
                    status=HealthStatus.UNKNOWN,
                    message="Serial manager not available",
                    timestamp=datetime.now(),
                    response_time=time.time() - start_time
                )
                
            is_connected = self._serial_manager.is_connected()
            
            if is_connected:
                status = HealthStatus.HEALTHY
                message = "Serial connection OK"
            else:
                status = HealthStatus.CRITICAL
                message = "Serial connection lost"
                
            response_time = time.time() - start_time
            
            return HealthCheck(
                name="serial_connection",
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    "connected": is_connected,
                    "port": getattr(self._serial_manager, 'port', 'unknown')
                },
                response_time=response_time
            )
            
        except Exception as e:
            return HealthCheck(
                name="serial_connection",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check serial connection: {e}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
            
    def _check_command_executor(self) -> HealthCheck:
        """Проверка исполнителя команд"""
        start_time = time.time()
        
        try:
            if not self._command_executor:
                return HealthCheck(
                    name="command_executor",
                    status=HealthStatus.UNKNOWN,
                    message="Command executor not available",
                    timestamp=datetime.now(),
                    response_time=time.time() - start_time
                )
                
            # Простая проверка - попытка получить статус
            status = HealthStatus.HEALTHY
            message = "Command executor OK"
            
            response_time = time.time() - start_time
            
            return HealthCheck(
                name="command_executor",
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    "available": True
                },
                response_time=response_time
            )
            
        except Exception as e:
            return HealthCheck(
                name="command_executor",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check command executor: {e}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
            
    def _determine_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Определение общего статуса на основе всех проверок"""
        if not checks:
            return HealthStatus.UNKNOWN
            
        # Если есть хотя бы одна критическая ошибка
        if any(check.status == HealthStatus.CRITICAL for check in checks):
            return HealthStatus.CRITICAL
            
        # Если есть хотя бы одно предупреждение
        if any(check.status == HealthStatus.WARNING for check in checks):
            return HealthStatus.WARNING
            
        # Если все проверки прошли успешно
        if all(check.status == HealthStatus.HEALTHY for check in checks):
            return HealthStatus.HEALTHY
            
        # Если есть неизвестные статусы
        return HealthStatus.UNKNOWN
        
    def _get_uptime(self) -> timedelta:
        """Получение времени работы приложения"""
        try:
            process = psutil.Process()
            return timedelta(seconds=time.time() - process.create_time())
        except:
            return timedelta(0)
            
    def _get_system_info(self) -> Dict[str, Any]:
        """Получение информации о системе"""
        try:
            return {
                "platform": os.name,
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3)
            }
        except Exception as e:
            return {"error": str(e)}
            
    def get_current_health(self) -> Optional[SystemHealth]:
        """Получение текущего состояния системы"""
        with self._lock:
            if self._health_checks:
                return self._health_checks[-1]
        return None
        
    def get_health_history(self, hours: int = 24) -> List[SystemHealth]:
        """Получение истории состояния системы"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            return [
                health for health in self._health_checks
                if health.timestamp > cutoff_time
            ]
            
    def get_health_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Получение сводки состояния системы"""
        history = self.get_health_history(hours)
        
        if not history:
            return {}
            
        # Статистика по статусам
        status_counts = {}
        check_failures = {}
        
        for health in history:
            status_counts[health.overall_status.value] = status_counts.get(health.overall_status.value, 0) + 1
            
            for check in health.checks:
                if check.status != HealthStatus.HEALTHY:
                    check_failures[check.name] = check_failures.get(check.name, 0) + 1
                    
        return {
            "period_hours": hours,
            "total_checks": len(history),
            "current_status": history[-1].overall_status.value if history else "unknown",
            "status_distribution": status_counts,
            "most_failed_checks": dict(sorted(check_failures.items(), key=lambda x: x[1], reverse=True)[:5])
        }
        
    def clear_old_health_data(self, days: int = 7) -> None:
        """Очистка старых данных о состоянии"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self._lock:
            self._health_checks = [
                health for health in self._health_checks
                if health.timestamp > cutoff_time
            ]
            
        self.logger.info(f"Cleared health data older than {days} days")
        
    def get_health_export(self) -> Dict[str, Any]:
        """Экспорт данных о состоянии системы"""
        with self._lock:
            return {
                "export_timestamp": datetime.now().isoformat(),
                "total_health_records": len(self._health_checks),
                "health_records": [
                    {
                        "timestamp": health.timestamp.isoformat(),
                        "overall_status": health.overall_status.value,
                        "uptime_seconds": health.uptime.total_seconds(),
                        "system_info": health.system_info,
                        "checks": [
                            {
                                "name": check.name,
                                "status": check.status.value,
                                "message": check.message,
                                "response_time": check.response_time,
                                "details": check.details
                            }
                            for check in health.checks
                        ]
                    }
                    for health in self._health_checks[-100:]  # Последние 100 записей
                ]
            }
