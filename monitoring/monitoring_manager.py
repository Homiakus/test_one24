"""
@file: monitoring_manager.py
@description: Главный менеджер системы мониторинга
@dependencies: performance_monitor, error_alerter, health_checker, usage_metrics
@created: 2024-12-19
"""

import threading
import time
import json
import os
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path

from utils.logger import Logger
from .performance_monitor import PerformanceMonitor
from .error_alerter import ErrorAlerter, AlertLevel
from .health_checker import HealthChecker
from .usage_metrics import UsageMetrics


class MonitoringManager:
    """
    Главный менеджер системы мониторинга
    
    Объединяет все компоненты мониторинга:
    - PerformanceMonitor - мониторинг производительности
    - ErrorAlerter - система уведомлений об ошибках
    - HealthChecker - проверка состояния системы
    - UsageMetrics - статистика использования
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger(__name__)
        self._lock = threading.Lock()
        self._monitoring_active = False
        self._export_thread: Optional[threading.Thread] = None
        
        # Компоненты мониторинга
        self.performance_monitor = PerformanceMonitor(logger)
        self.error_alerter = ErrorAlerter(logger)
        self.health_checker = HealthChecker(logger)
        self.usage_metrics = UsageMetrics(logger)
        
        # Настройки
        self.export_interval_hours = 24
        self.export_directory = Path("logs/monitoring")
        self.retention_days = 30
        
        # Создаем директорию для экспорта
        self.export_directory.mkdir(parents=True, exist_ok=True)
        
        # Обработчики событий
        self._event_handlers: List[Callable[[str, Dict[str, Any]], None]] = []
        
    def start_monitoring(self) -> None:
        """Запуск всей системы мониторинга"""
        if self._monitoring_active:
            return
            
        self.logger.info("Starting monitoring system...")
        
        # Запускаем компоненты
        self.performance_monitor.start_monitoring()
        self.health_checker.start_monitoring()
        
        # Настраиваем обработчики уведомлений
        self._setup_alert_handlers()
        
        # Запускаем экспорт данных
        self._start_export_thread()
        
        self._monitoring_active = True
        self.logger.info("Monitoring system started successfully")
        
    def stop_monitoring(self) -> None:
        """Остановка системы мониторинга"""
        if not self._monitoring_active:
            return
            
        self.logger.info("Stopping monitoring system...")
        
        # Останавливаем компоненты
        self.performance_monitor.stop_monitoring()
        self.health_checker.stop_monitoring()
        
        # Останавливаем экспорт
        self._stop_export_thread()
        
        # Завершаем текущую сессию
        self.usage_metrics.end_session()
        
        self._monitoring_active = False
        self.logger.info("Monitoring system stopped")
        
    def _setup_alert_handlers(self) -> None:
        """Настройка обработчиков уведомлений"""
        # Обработчик для критических ошибок
        def critical_alert_handler(alert):
            if alert.level == AlertLevel.CRITICAL:
                self.logger.critical(f"CRITICAL ALERT: {alert.message}")
                # Здесь можно добавить дополнительные действия
                # например, отправку SMS, уведомление администратора и т.д.
                
        self.error_alerter.add_alert_handler(critical_alert_handler)
        
        # Обработчик для всех уведомлений
        def general_alert_handler(alert):
            # Записываем в метрики использования
            self.usage_metrics.record_error(
                error_type=alert.level.value,
                error_message=alert.message,
                context={"source": alert.source, "details": alert.details}
            )
            
        self.error_alerter.add_alert_handler(general_alert_handler)
        
    def _start_export_thread(self) -> None:
        """Запуск потока экспорта данных"""
        self._export_thread = threading.Thread(
            target=self._export_loop,
            daemon=True,
            name="MonitoringExport"
        )
        self._export_thread.start()
        
    def _stop_export_thread(self) -> None:
        """Остановка потока экспорта"""
        if self._export_thread:
            self._export_thread.join(timeout=10.0)
            
    def _export_loop(self) -> None:
        """Цикл экспорта данных"""
        while self._monitoring_active:
            try:
                time.sleep(self.export_interval_hours * 3600)  # Конвертируем часы в секунды
                if self._monitoring_active:
                    self.export_all_data()
            except Exception as e:
                self.logger.error(f"Error in export loop: {e}")
                
    def export_all_data(self) -> None:
        """Экспорт всех данных мониторинга"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Экспортируем данные каждого компонента
            data = {
                "export_timestamp": datetime.now().isoformat(),
                "performance": self.performance_monitor.get_metrics_export(),
                "alerts": self.error_alerter.get_alerts_export(),
                "health": self.health_checker.get_health_export(),
                "usage": self.usage_metrics.get_usage_export()
            }
            
            # Сохраняем в файл
            filename = self.export_directory / f"monitoring_export_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Monitoring data exported to {filename}")
            
            # Очищаем старые файлы
            self._cleanup_old_exports()
            
        except Exception as e:
            self.logger.error(f"Failed to export monitoring data: {e}")
            
    def _cleanup_old_exports(self) -> None:
        """Очистка старых файлов экспорта"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.retention_days)
            
            for file_path in self.export_directory.glob("monitoring_export_*.json"):
                if file_path.stat().st_mtime < cutoff_time.timestamp():
                    file_path.unlink()
                    self.logger.info(f"Deleted old export file: {file_path}")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up old exports: {e}")
            
    def set_services(self, serial_manager, command_executor) -> None:
        """Установка сервисов для мониторинга"""
        self.health_checker.set_services(serial_manager, command_executor)
        
    def configure_email_alerts(self, smtp_server: str, smtp_port: int,
                             username: str, password: str, recipients: List[str]) -> None:
        """Настройка email уведомлений"""
        self.error_alerter.configure_email(smtp_server, smtp_port, username, password, recipients)
        
    def add_event_handler(self, handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """Добавление обработчика событий"""
        self._event_handlers.append(handler)
        
    def record_command_execution(self, command: str, execution_time: float,
                               success: bool, error_message: Optional[str] = None) -> None:
        """Запись выполнения команды"""
        # Записываем в мониторинг производительности
        self.performance_monitor.record_command_execution(command, execution_time, success, error_message)
        
        # Записываем в метрики использования
        self.usage_metrics.record_command_usage(command, success, execution_time)
        
        # Отправляем уведомление об ошибке
        if not success:
            self.error_alerter.send_alert(
                level=AlertLevel.ERROR,
                message=f"Command execution failed: {command}",
                source="command_executor",
                details={
                    "command": command,
                    "execution_time": execution_time,
                    "error_message": error_message
                }
            )
            
    def record_page_visit(self, page_name: str, duration: Optional[float] = None) -> None:
        """Запись посещения страницы"""
        self.usage_metrics.record_page_visit(page_name, duration)
        
    def record_sequence_execution(self, sequence_name: str, success: bool, duration: float) -> None:
        """Запись выполнения последовательности"""
        self.usage_metrics.record_sequence_execution(sequence_name, success, duration)
        
        if not success:
            self.error_alerter.send_alert(
                level=AlertLevel.WARNING,
                message=f"Sequence execution failed: {sequence_name}",
                source="sequence_manager",
                details={
                    "sequence": sequence_name,
                    "duration": duration
                }
            )
            
    def get_comprehensive_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Получение комплексной сводки мониторинга"""
        return {
            "timestamp": datetime.now().isoformat(),
            "monitoring_active": self._monitoring_active,
            "performance": self.performance_monitor.get_system_metrics_summary(hours),
            "command_performance": self.performance_monitor.get_command_performance_summary(hours),
            "alerts": self.error_alerter.get_alerts_summary(hours),
            "health": self.health_checker.get_health_summary(hours),
            "usage": self.usage_metrics.get_usage_summary(hours)
        }
        
    def get_current_status(self) -> Dict[str, Any]:
        """Получение текущего статуса системы"""
        current_health = self.health_checker.get_current_health()
        active_alerts = self.error_alerter.get_active_alerts()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "monitoring_active": self._monitoring_active,
            "system_health": {
                "status": current_health.overall_status.value if current_health else "unknown",
                "uptime": current_health.uptime.total_seconds() if current_health else 0
            },
            "active_alerts": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
            "performance": {
                "uptime": self.performance_monitor.get_uptime().total_seconds()
            }
        }
        
    def run_health_check(self) -> Any:
        """Выполнение проверки состояния"""
        return self.health_checker.run_health_checks()
        
    def send_alert(self, level: AlertLevel, message: str, source: str,
                  details: Optional[Dict[str, Any]] = None) -> None:
        """Отправка уведомления"""
        self.error_alerter.send_alert(level, message, source, details)
        
    def start_user_session(self, user_id: Optional[str] = None) -> str:
        """Начало сессии пользователя"""
        return self.usage_metrics.start_session(user_id)
        
    def end_user_session(self, session_id: Optional[str] = None) -> None:
        """Завершение сессии пользователя"""
        self.usage_metrics.end_session(session_id)
        
    def cleanup_old_data(self, days: int = None) -> None:
        """Очистка старых данных"""
        if days is None:
            days = self.retention_days
            
        self.performance_monitor.clear_old_metrics(days)
        self.error_alerter.clear_old_alerts(days)
        self.health_checker.clear_old_health_data(days)
        self.usage_metrics.clear_old_data(days)
        
        self.logger.info(f"Cleaned up monitoring data older than {days} days")
        
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Получение конфигурации мониторинга"""
        return {
            "monitoring_active": self._monitoring_active,
            "export_interval_hours": self.export_interval_hours,
            "export_directory": str(self.export_directory),
            "retention_days": self.retention_days,
            "performance_monitor": {
                "system_monitor_interval": self.performance_monitor.system_monitor_interval,
                "max_metrics_history": self.performance_monitor.max_metrics_history
            },
            "health_checker": {
                "check_interval": self.health_checker.check_interval,
                "max_health_history": self.health_checker.max_health_history
            },
            "error_alerter": {
                "enable_email_alerts": self.error_alerter.enable_email_alerts,
                "enable_ui_alerts": self.error_alerter.enable_ui_alerts,
                "auto_acknowledge_after_hours": self.error_alerter.auto_acknowledge_after_hours
            },
            "usage_metrics": {
                "max_events_history": self.usage_metrics.max_events_history,
                "max_sessions_history": self.usage_metrics.max_sessions_history,
                "session_timeout_minutes": self.usage_metrics.session_timeout_minutes
            }
        }
        
    def set_monitoring_config(self, config: Dict[str, Any]) -> None:
        """Установка конфигурации мониторинга"""
        if "export_interval_hours" in config:
            self.export_interval_hours = config["export_interval_hours"]
            
        if "retention_days" in config:
            self.retention_days = config["retention_days"]
            
        if "performance_monitor" in config:
            pm_config = config["performance_monitor"]
            if "system_monitor_interval" in pm_config:
                self.performance_monitor.system_monitor_interval = pm_config["system_monitor_interval"]
            if "max_metrics_history" in pm_config:
                self.performance_monitor.max_metrics_history = pm_config["max_metrics_history"]
                
        if "health_checker" in config:
            hc_config = config["health_checker"]
            if "check_interval" in hc_config:
                self.health_checker.check_interval = hc_config["check_interval"]
            if "max_health_history" in hc_config:
                self.health_checker.max_health_history = hc_config["max_health_history"]
                
        if "error_alerter" in config:
            ea_config = config["error_alerter"]
            if "auto_acknowledge_after_hours" in ea_config:
                self.error_alerter.auto_acknowledge_after_hours = ea_config["auto_acknowledge_after_hours"]
                
        if "usage_metrics" in config:
            um_config = config["usage_metrics"]
            if "max_events_history" in um_config:
                self.usage_metrics.max_events_history = um_config["max_events_history"]
            if "max_sessions_history" in um_config:
                self.usage_metrics.max_sessions_history = um_config["max_sessions_history"]
            if "session_timeout_minutes" in um_config:
                self.usage_metrics.session_timeout_minutes = um_config["session_timeout_minutes"]
                
        self.logger.info("Monitoring configuration updated")
