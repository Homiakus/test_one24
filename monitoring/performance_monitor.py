"""
@file: performance_monitor.py
@description: Мониторинг производительности приложения
@dependencies: time, psutil, threading, utils.logger
@created: 2024-12-19
"""

import time
import psutil
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

from utils.logger import Logger


@dataclass
class PerformanceMetric:
    """Метрика производительности"""
    name: str
    value: float
    timestamp: datetime
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class CommandPerformance:
    """Производительность выполнения команд"""
    command: str
    execution_time: float
    success: bool
    timestamp: datetime
    error_message: Optional[str] = None


class PerformanceMonitor:
    """
    Мониторинг производительности приложения
    
    Отслеживает:
    - Время выполнения команд
    - Использование CPU и памяти
    - Время отклика UI
    - Статистику ошибок
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger(__name__)
        self._lock = threading.Lock()
        self._metrics: List[PerformanceMetric] = []
        self._command_performance: List[CommandPerformance] = []
        self._system_metrics = deque(maxlen=1000)  # Храним последние 1000 измерений
        self._start_time = datetime.now()
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Настройки мониторинга
        self.system_monitor_interval = 5.0  # секунды
        self.max_metrics_history = 10000
        
    def start_monitoring(self) -> None:
        """Запуск мониторинга системы"""
        if self._monitoring_active:
            return
            
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._system_monitor_loop,
            daemon=True,
            name="PerformanceMonitor"
        )
        self._monitor_thread.start()
        self.logger.info("Performance monitoring started")
        
    def stop_monitoring(self) -> None:
        """Остановка мониторинга системы"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        self.logger.info("Performance monitoring stopped")
        
    def _system_monitor_loop(self) -> None:
        """Цикл мониторинга системных ресурсов"""
        while self._monitoring_active:
            try:
                self._collect_system_metrics()
                time.sleep(self.system_monitor_interval)
            except Exception as e:
                self.logger.error(f"Error in system monitoring: {e}")
                
    def _collect_system_metrics(self) -> None:
        """Сбор системных метрик"""
        try:
            process = psutil.Process()
            
            # CPU
            cpu_percent = process.cpu_percent()
            self._add_metric("cpu_usage", cpu_percent, "%")
            
            # Memory
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            self._add_metric("memory_usage_mb", memory_info.rss / 1024 / 1024, "MB")
            self._add_metric("memory_percent", memory_percent, "%")
            
            # System metrics
            system_metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_mb": memory_info.rss / 1024 / 1024,
                "memory_percent": memory_percent,
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            }
            
            with self._lock:
                self._system_metrics.append(system_metrics)
                
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            
    def _add_metric(self, name: str, value: float, unit: str = "", tags: Optional[Dict[str, str]] = None) -> None:
        """Добавление метрики"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            unit=unit,
            tags=tags or {}
        )
        
        with self._lock:
            self._metrics.append(metric)
            # Ограничиваем историю метрик
            if len(self._metrics) > self.max_metrics_history:
                self._metrics = self._metrics[-self.max_metrics_history:]
                
    def record_command_execution(self, command: str, execution_time: float, 
                               success: bool, error_message: Optional[str] = None) -> None:
        """Запись выполнения команды"""
        perf = CommandPerformance(
            command=command,
            execution_time=execution_time,
            success=success,
            timestamp=datetime.now(),
            error_message=error_message
        )
        
        with self._lock:
            self._command_performance.append(perf)
            # Ограничиваем историю команд
            if len(self._command_performance) > self.max_metrics_history:
                self._command_performance = self._command_performance[-self.max_metrics_history:]
                
        # Добавляем метрику времени выполнения
        self._add_metric("command_execution_time", execution_time, "seconds", 
                        {"command": command, "success": str(success)})
        
    def record_ui_response_time(self, operation: str, response_time: float) -> None:
        """Запись времени отклика UI"""
        self._add_metric("ui_response_time", response_time, "seconds", {"operation": operation})
        
    def get_uptime(self) -> timedelta:
        """Получение времени работы приложения"""
        return datetime.now() - self._start_time
        
    def get_system_metrics_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """Получение сводки системных метрик за последние N минут"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self._lock:
            recent_metrics = [
                m for m in self._system_metrics 
                if datetime.fromisoformat(m["timestamp"]) > cutoff_time
            ]
            
        if not recent_metrics:
            return {}
            
        # Вычисляем статистику
        cpu_values = [m["cpu_percent"] for m in recent_metrics]
        memory_values = [m["memory_mb"] for m in recent_metrics]
        
        return {
            "period_minutes": minutes,
            "samples_count": len(recent_metrics),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory": {
                "avg_mb": sum(memory_values) / len(memory_values),
                "max_mb": max(memory_values),
                "min_mb": min(memory_values)
            }
        }
        
    def get_command_performance_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """Получение сводки производительности команд"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self._lock:
            recent_commands = [
                c for c in self._command_performance 
                if c.timestamp > cutoff_time
            ]
            
        if not recent_commands:
            return {}
            
        # Группируем по командам
        command_stats = defaultdict(lambda: {"count": 0, "total_time": 0, "success_count": 0})
        
        for cmd in recent_commands:
            stats = command_stats[cmd.command]
            stats["count"] += 1
            stats["total_time"] += cmd.execution_time
            if cmd.success:
                stats["success_count"] += 1
                
        # Вычисляем средние значения
        for cmd_name, stats in command_stats.items():
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["success_rate"] = stats["success_count"] / stats["count"]
            
        return {
            "period_minutes": minutes,
            "total_commands": len(recent_commands),
            "commands": dict(command_stats)
        }
        
    def get_metrics_export(self) -> Dict[str, Any]:
        """Экспорт всех метрик для сохранения"""
        with self._lock:
            return {
                "export_timestamp": datetime.now().isoformat(),
                "uptime_seconds": self.get_uptime().total_seconds(),
                "metrics_count": len(self._metrics),
                "commands_count": len(self._command_performance),
                "system_metrics_count": len(self._system_metrics),
                "metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "timestamp": m.timestamp.isoformat(),
                        "unit": m.unit,
                        "tags": m.tags
                    }
                    for m in self._metrics[-1000:]  # Последние 1000 метрик
                ],
                "commands": [
                    {
                        "command": c.command,
                        "execution_time": c.execution_time,
                        "success": c.success,
                        "timestamp": c.timestamp.isoformat(),
                        "error_message": c.error_message
                    }
                    for c in self._command_performance[-1000:]  # Последние 1000 команд
                ]
            }
            
    def clear_old_metrics(self, days: int = 7) -> None:
        """Очистка старых метрик"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self._lock:
            self._metrics = [m for m in self._metrics if m.timestamp > cutoff_time]
            self._command_performance = [c for c in self._command_performance if c.timestamp > cutoff_time]
            
        self.logger.info(f"Cleared metrics older than {days} days")
