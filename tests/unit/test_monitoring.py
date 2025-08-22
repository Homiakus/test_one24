"""
@file: test_monitoring.py
@description: Unit тесты для системы мониторинга
@dependencies: pytest, monitoring
@created: 2024-12-19
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from monitoring import (
    MonitoringManager, PerformanceMonitor, ErrorAlerter, 
    HealthChecker, UsageMetrics, AlertLevel
)


class TestPerformanceMonitor:
    """Тесты для PerformanceMonitor"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.monitor = PerformanceMonitor()
        
    def test_initialization(self):
        """Тест инициализации"""
        assert self.monitor._metrics == []
        assert self.monitor._command_performance == []
        assert not self.monitor._monitoring_active
        
    def test_add_metric(self):
        """Тест добавления метрики"""
        self.monitor._add_metric("test_metric", 42.5, "units")
        
        assert len(self.monitor._metrics) == 1
        metric = self.monitor._metrics[0]
        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.unit == "units"
        
    def test_record_command_execution(self):
        """Тест записи выполнения команды"""
        self.monitor.record_command_execution("test_command", 1.5, True)
        
        assert len(self.monitor._command_performance) == 1
        perf = self.monitor._command_performance[0]
        assert perf.command == "test_command"
        assert perf.execution_time == 1.5
        assert perf.success is True
        
    def test_get_uptime(self):
        """Тест получения времени работы"""
        uptime = self.monitor.get_uptime()
        assert isinstance(uptime, timedelta)
        assert uptime.total_seconds() >= 0
        
    def test_get_system_metrics_summary(self):
        """Тест получения сводки системных метрик"""
        # Добавляем тестовые данные
        test_metrics = [
            {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": 50.0,
                "memory_mb": 100.0
            }
        ]
        self.monitor._system_metrics.extend(test_metrics)
        
        summary = self.monitor.get_system_metrics_summary(minutes=5)
        assert "cpu" in summary
        assert "memory" in summary
        
    def test_get_command_performance_summary(self):
        """Тест получения сводки производительности команд"""
        # Добавляем тестовые данные
        from monitoring.performance_monitor import CommandPerformance
        
        test_command = CommandPerformance(
            command="test_cmd",
            execution_time=1.0,
            success=True,
            timestamp=datetime.now()
        )
        self.monitor._command_performance.append(test_command)
        
        summary = self.monitor.get_command_performance_summary(minutes=5)
        assert "commands" in summary
        assert "test_cmd" in summary["commands"]
        
    def test_clear_old_metrics(self):
        """Тест очистки старых метрик"""
        # Добавляем старые метрики
        old_time = datetime.now() - timedelta(days=10)
        new_time = datetime.now()
        
        from monitoring.performance_monitor import PerformanceMetric
        
        old_metric = PerformanceMetric("old", 1.0, old_time)
        new_metric = PerformanceMetric("new", 2.0, new_time)
        
        self.monitor._metrics = [old_metric, new_metric]
        
        self.monitor.clear_old_metrics(days=5)
        
        assert len(self.monitor._metrics) == 1
        assert self.monitor._metrics[0].name == "new"


class TestErrorAlerter:
    """Тесты для ErrorAlerter"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.alerter = ErrorAlerter()
        
    def test_initialization(self):
        """Тест инициализации"""
        assert self.alerter._alerts == []
        assert self.alerter._alert_handlers == []
        assert not self.alerter.enable_email_alerts
        
    def test_send_alert(self):
        """Тест отправки уведомления"""
        self.alerter.send_alert(
            AlertLevel.ERROR,
            "Test error message",
            "test_source"
        )
        
        assert len(self.alerter._alerts) == 1
        alert = self.alerter._alerts[0]
        assert alert.level == AlertLevel.ERROR
        assert alert.message == "Test error message"
        assert alert.source == "test_source"
        
    def test_add_alert_handler(self):
        """Тест добавления обработчика"""
        handler = Mock()
        self.alerter.add_alert_handler(handler)
        
        assert len(self.alerter._alert_handlers) == 1
        assert self.alerter._alert_handlers[0] == handler
        
    def test_acknowledge_alert(self):
        """Тест подтверждения уведомления"""
        # Добавляем уведомление
        self.alerter.send_alert(AlertLevel.INFO, "Test", "source")
        
        # Подтверждаем
        result = self.alerter.acknowledge_alert(0, "test_user")
        
        assert result is True
        assert self.alerter._alerts[0].acknowledged is True
        assert self.alerter._alerts[0].acknowledged_by == "test_user"
        
    def test_get_active_alerts(self):
        """Тест получения активных уведомлений"""
        # Добавляем уведомления
        self.alerter.send_alert(AlertLevel.INFO, "Active", "source")
        self.alerter.send_alert(AlertLevel.ERROR, "Active 2", "source")
        
        # Подтверждаем одно
        self.alerter.acknowledge_alert(0, "user")
        
        active_alerts = self.alerter.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].message == "Active 2"
        
    def test_get_alerts_summary(self):
        """Тест получения сводки уведомлений"""
        # Добавляем уведомления разных уровней
        self.alerter.send_alert(AlertLevel.INFO, "Info", "source1")
        self.alerter.send_alert(AlertLevel.ERROR, "Error", "source2")
        
        summary = self.alerter.get_alerts_summary(hours=24)
        
        assert summary["total_alerts"] == 2
        assert "by_level" in summary
        assert "by_source" in summary


class TestHealthChecker:
    """Тесты для HealthChecker"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.checker = HealthChecker()
        
    def test_initialization(self):
        """Тест инициализации"""
        assert self.checker._health_checks == []
        assert not self.checker._monitoring_active
        
    def test_add_custom_check(self):
        """Тест добавления пользовательской проверки"""
        def custom_check():
            from monitoring.health_checker import HealthCheck, HealthStatus
            return HealthCheck(
                name="custom_test",
                status=HealthStatus.HEALTHY,
                message="Custom check passed",
                timestamp=datetime.now()
            )
            
        self.checker.add_custom_check("test_check", custom_check)
        assert "test_check" in self.checker._custom_checks
        
    def test_get_current_health(self):
        """Тест получения текущего состояния"""
        # Сначала нет данных
        assert self.checker.get_current_health() is None
        
        # Добавляем проверку
        health = self.checker.run_health_checks()
        current = self.checker.get_current_health()
        
        assert current is not None
        assert current.overall_status == health.overall_status
        
    def test_get_health_summary(self):
        """Тест получения сводки состояния"""
        # Добавляем несколько проверок
        for _ in range(3):
            self.checker.run_health_checks()
            
        summary = self.checker.get_health_summary(hours=24)
        
        assert "total_checks" in summary
        assert "current_status" in summary
        assert "status_distribution" in summary


class TestUsageMetrics:
    """Тесты для UsageMetrics"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.metrics = UsageMetrics()
        
    def test_initialization(self):
        """Тест инициализации"""
        assert self.metrics._events == []
        assert self.metrics._sessions == {}
        assert self.metrics._current_session_id is None
        
    def test_start_session(self):
        """Тест начала сессии"""
        session_id = self.metrics.start_session("test_user")
        
        assert session_id in self.metrics._sessions
        assert self.metrics._current_session_id == session_id
        assert self.metrics._sessions[session_id].user_id == "test_user"
        
    def test_end_session(self):
        """Тест завершения сессии"""
        session_id = self.metrics.start_session("test_user")
        self.metrics.end_session(session_id)
        
        session = self.metrics._sessions[session_id]
        assert session.end_time is not None
        assert session.total_duration is not None
        
    def test_record_event(self):
        """Тест записи события"""
        self.metrics.record_event("test_event", {"key": "value"})
        
        assert len(self.metrics._events) == 1
        event = self.metrics._events[0]
        assert event.event_type == "test_event"
        assert event.details["key"] == "value"
        
    def test_record_command_usage(self):
        """Тест записи использования команды"""
        self.metrics.record_command_usage("test_command", True, 1.5)
        
        assert len(self.metrics._events) == 1
        event = self.metrics._events[0]
        assert event.event_type == "command_executed"
        assert event.details["command"] == "test_command"
        assert event.details["success"] is True
        assert event.details["execution_time"] == 1.5
        
    def test_get_usage_summary(self):
        """Тест получения сводки использования"""
        # Добавляем тестовые данные
        self.metrics.record_command_usage("cmd1", True, 1.0)
        self.metrics.record_page_visit("page1")
        
        summary = self.metrics.get_usage_summary(hours=24)
        
        assert "total_events" in summary
        assert "event_types" in summary
        assert "command_stats" in summary
        
    def test_get_command_usage_analysis(self):
        """Тест анализа использования команд"""
        # Добавляем тестовые данные
        self.metrics.record_command_usage("cmd1", True, 1.0)
        self.metrics.record_command_usage("cmd2", False, 2.0)
        
        analysis = self.metrics.get_command_usage_analysis(days=7)
        
        assert "total_commands" in analysis
        assert "unique_commands" in analysis
        assert "top_commands" in analysis


class TestMonitoringManager:
    """Тесты для MonitoringManager"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.manager = MonitoringManager()
        
    def test_initialization(self):
        """Тест инициализации"""
        assert isinstance(self.manager.performance_monitor, PerformanceMonitor)
        assert isinstance(self.manager.error_alerter, ErrorAlerter)
        assert isinstance(self.manager.health_checker, HealthChecker)
        assert isinstance(self.manager.usage_metrics, UsageMetrics)
        assert not self.manager._monitoring_active
        
    def test_record_command_execution(self):
        """Тест записи выполнения команды"""
        self.manager.record_command_execution("test_cmd", 1.5, True)
        
        # Проверяем что данные записались в оба компонента
        assert len(self.manager.performance_monitor._command_performance) == 1
        assert len(self.manager.usage_metrics._events) == 1
        
    def test_record_command_execution_error(self):
        """Тест записи ошибки выполнения команды"""
        self.manager.record_command_execution("test_cmd", 1.5, False, "Test error")
        
        # Проверяем что уведомление об ошибке было отправлено
        assert len(self.manager.error_alerter._alerts) == 1
        alert = self.manager.error_alerter._alerts[0]
        assert alert.level == AlertLevel.ERROR
        assert "test_cmd" in alert.message
        
    def test_record_page_visit(self):
        """Тест записи посещения страницы"""
        self.manager.record_page_visit("test_page", 30.0)
        
        assert len(self.manager.usage_metrics._events) == 1
        event = self.manager.usage_metrics._events[0]
        assert event.event_type == "page_visited"
        assert event.details["page"] == "test_page"
        assert event.details["duration"] == 30.0
        
    def test_record_sequence_execution(self):
        """Тест записи выполнения последовательности"""
        self.manager.record_sequence_execution("test_seq", True, 60.0)
        
        assert len(self.manager.usage_metrics._events) == 1
        event = self.manager.usage_metrics._events[0]
        assert event.event_type == "sequence_executed"
        assert event.details["sequence"] == "test_seq"
        assert event.details["success"] is True
        assert event.details["duration"] == 60.0
        
    def test_get_comprehensive_summary(self):
        """Тест получения комплексной сводки"""
        # Добавляем тестовые данные
        self.manager.record_command_execution("test_cmd", 1.0, True)
        self.manager.record_page_visit("test_page")
        
        summary = self.manager.get_comprehensive_summary(hours=24)
        
        assert "timestamp" in summary
        assert "performance" in summary
        assert "alerts" in summary
        assert "health" in summary
        assert "usage" in summary
        
    def test_get_current_status(self):
        """Тест получения текущего статуса"""
        status = self.manager.get_current_status()
        
        assert "timestamp" in status
        assert "monitoring_active" in status
        assert "system_health" in status
        assert "active_alerts" in status
        
    def test_cleanup_old_data(self):
        """Тест очистки старых данных"""
        # Добавляем тестовые данные
        self.manager.record_command_execution("test_cmd", 1.0, True)
        self.manager.send_alert(AlertLevel.INFO, "Test alert", "test")
        
        # Очищаем данные
        self.manager.cleanup_old_data(days=0)  # Очищаем все
        
        # Проверяем что данные очистились
        assert len(self.manager.performance_monitor._command_performance) == 0
        assert len(self.manager.error_alerter._alerts) == 0


class TestMonitoringIntegration:
    """Интеграционные тесты мониторинга"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.manager = MonitoringManager()
        
    def test_full_monitoring_cycle(self):
        """Тест полного цикла мониторинга"""
        # Запускаем мониторинг
        self.manager.start_monitoring()
        assert self.manager._monitoring_active is True
        
        # Добавляем данные
        self.manager.record_command_execution("test_cmd", 1.0, True)
        self.manager.record_page_visit("test_page")
        self.manager.send_alert(AlertLevel.INFO, "Test alert", "test")
        
        # Получаем сводку
        summary = self.manager.get_comprehensive_summary(hours=24)
        assert "performance" in summary
        assert "usage" in summary
        assert "alerts" in summary
        
        # Останавливаем мониторинг
        self.manager.stop_monitoring()
        assert self.manager._monitoring_active is False
        
    def test_alert_escalation(self):
        """Тест эскалации уведомлений"""
        # Настраиваем правило эскалации
        self.manager.error_alerter.set_escalation_rule(
            AlertLevel.ERROR,
            {"max_alerts_per_hour": 2}
        )
        
        # Отправляем несколько уведомлений
        for i in range(3):
            self.manager.send_alert(
                AlertLevel.ERROR,
                f"Error {i}",
                "test_source"
            )
            
        # Проверяем что уведомления были отправлены
        assert len(self.manager.error_alerter._alerts) == 3
        
    def test_health_check_integration(self):
        """Тест интеграции проверки состояния"""
        # Мокаем сервисы
        mock_serial = Mock()
        mock_serial.is_connected.return_value = True
        
        mock_executor = Mock()
        
        # Устанавливаем сервисы
        self.manager.set_services(mock_serial, mock_executor)
        
        # Запускаем проверку состояния
        health = self.manager.run_health_check()
        
        assert health is not None
        assert hasattr(health, 'overall_status')
        assert hasattr(health, 'checks')
        
    def test_usage_tracking(self):
        """Тест отслеживания использования"""
        # Начинаем сессию
        session_id = self.manager.start_user_session("test_user")
        assert session_id is not None
        
        # Добавляем активность
        self.manager.record_command_execution("cmd1", 1.0, True)
        self.manager.record_page_visit("page1")
        self.manager.record_sequence_execution("seq1", True, 30.0)
        
        # Получаем анализ использования
        usage_summary = self.manager.usage_metrics.get_usage_summary(hours=24)
        assert usage_summary["total_events"] >= 3
        
        # Завершаем сессию
        self.manager.end_user_session(session_id)
        
        session = self.manager.usage_metrics._sessions[session_id]
        assert session.end_time is not None
        assert session.total_duration is not None
