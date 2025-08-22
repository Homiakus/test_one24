"""
@file: error_alerter.py
@description: Система уведомлений об ошибках
@dependencies: threading, datetime, utils.logger
@created: 2024-12-19
"""

import threading
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from utils.logger import Logger


class AlertLevel(Enum):
    """Уровни важности уведомлений"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Уведомление об ошибке"""
    level: AlertLevel
    message: str
    source: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class ErrorAlerter:
    """
    Система уведомлений об ошибках
    
    Функции:
    - Отслеживание ошибок по уровням важности
    - Группировка похожих ошибок
    - Отправка уведомлений (email, webhook, UI)
    - Эскалация критических ошибок
    - История уведомлений
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger(__name__)
        self._lock = threading.Lock()
        self._alerts: List[Alert] = []
        self._alert_handlers: List[Callable[[Alert], None]] = []
        self._escalation_rules: Dict[AlertLevel, List[Dict[str, Any]]] = {}
        self._suppression_rules: Dict[str, timedelta] = {}
        self._last_alert_times: Dict[str, datetime] = {}
        
        # Настройки по умолчанию
        self.max_alerts_history = 1000
        self.auto_acknowledge_after_hours = 24
        self.enable_email_alerts = False
        self.enable_ui_alerts = True
        
        # Email настройки
        self.smtp_server = ""
        self.smtp_port = 587
        self.smtp_username = ""
        self.smtp_password = ""
        self.alert_recipients: List[str] = []
        
    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Добавление обработчика уведомлений"""
        self._alert_handlers.append(handler)
        
    def set_escalation_rule(self, level: AlertLevel, rule: Dict[str, Any]) -> None:
        """Установка правила эскалации для уровня"""
        self._escalation_rules[level] = rule
        
    def set_suppression_rule(self, alert_pattern: str, duration: timedelta) -> None:
        """Установка правила подавления повторяющихся уведомлений"""
        self._suppression_rules[alert_pattern] = duration
        
    def configure_email(self, smtp_server: str, smtp_port: int, 
                       username: str, password: str, recipients: List[str]) -> None:
        """Настройка email уведомлений"""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = username
        self.smtp_password = password
        self.alert_recipients = recipients
        self.enable_email_alerts = True
        
    def send_alert(self, level: AlertLevel, message: str, source: str, 
                  details: Optional[Dict[str, Any]] = None) -> None:
        """Отправка уведомления"""
        # Проверяем подавление
        if self._is_suppressed(message):
            return
            
        alert = Alert(
            level=level,
            message=message,
            source=source,
            timestamp=datetime.now(),
            details=details or {}
        )
        
        with self._lock:
            self._alerts.append(alert)
            # Ограничиваем историю
            if len(self._alerts) > self.max_alerts_history:
                self._alerts = self._alerts[-self.max_alerts_history:]
                
        # Обновляем время последнего уведомления
        self._last_alert_times[message] = datetime.now()
        
        # Логируем
        log_message = f"[{level.value.upper()}] {source}: {message}"
        if level == AlertLevel.ERROR or level == AlertLevel.CRITICAL:
            self.logger.error(log_message)
        elif level == AlertLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
            
        # Отправляем обработчикам
        self._notify_handlers(alert)
        
        # Проверяем эскалацию
        self._check_escalation(alert)
        
    def _is_suppressed(self, message: str) -> bool:
        """Проверка подавления уведомления"""
        for pattern, duration in self._suppression_rules.items():
            if pattern in message:
                last_time = self._last_alert_times.get(message)
                if last_time and datetime.now() - last_time < duration:
                    return True
        return False
        
    def _notify_handlers(self, alert: Alert) -> None:
        """Уведомление всех обработчиков"""
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")
                
    def _check_escalation(self, alert: Alert) -> None:
        """Проверка необходимости эскалации"""
        if alert.level not in self._escalation_rules:
            return
            
        rule = self._escalation_rules[alert.level]
        
        # Проверяем количество уведомлений за период
        if "max_alerts_per_hour" in rule:
            cutoff_time = datetime.now() - timedelta(hours=1)
            recent_alerts = [
                a for a in self._alerts 
                if a.level == alert.level and a.timestamp > cutoff_time
            ]
            
            if len(recent_alerts) > rule["max_alerts_per_hour"]:
                self._escalate_alert(alert, rule)
                
    def _escalate_alert(self, alert: Alert, rule: Dict[str, Any]) -> None:
        """Эскалация уведомления"""
        escalation_message = f"ESCALATION: {alert.message} (source: {alert.source})"
        
        # Отправляем email если настроено
        if self.enable_email_alerts and "email_escalation" in rule:
            self._send_email_alert(escalation_message, alert)
            
        # Логируем эскалацию
        self.logger.critical(f"Alert escalated: {escalation_message}")
        
    def _send_email_alert(self, message: str, alert: Alert) -> None:
        """Отправка email уведомления"""
        if not self.alert_recipients:
            return
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = ", ".join(self.alert_recipients)
            msg['Subject'] = f"Alert: {alert.level.value.upper()} - {alert.source}"
            
            body = f"""
            Alert Details:
            Level: {alert.level.value}
            Source: {alert.source}
            Message: {message}
            Time: {alert.timestamp}
            Details: {json.dumps(alert.details, indent=2)}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            self.logger.info(f"Email alert sent to {len(self.alert_recipients)} recipients")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            
    def acknowledge_alert(self, alert_index: int, acknowledged_by: str) -> bool:
        """Подтверждение уведомления"""
        with self._lock:
            if 0 <= alert_index < len(self._alerts):
                alert = self._alerts[alert_index]
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.now()
                return True
        return False
        
    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """Получение активных уведомлений"""
        with self._lock:
            alerts = [a for a in self._alerts if not a.acknowledged]
            if level:
                alerts = [a for a in alerts if a.level == level]
            return alerts
            
    def get_alerts_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Получение сводки уведомлений"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            recent_alerts = [a for a in self._alerts if a.timestamp > cutoff_time]
            
        # Группируем по уровням
        level_counts = {}
        source_counts = {}
        
        for alert in recent_alerts:
            level_counts[alert.level.value] = level_counts.get(alert.level.value, 0) + 1
            source_counts[alert.source] = source_counts.get(alert.source, 0) + 1
            
        return {
            "period_hours": hours,
            "total_alerts": len(recent_alerts),
            "active_alerts": len([a for a in recent_alerts if not a.acknowledged]),
            "by_level": level_counts,
            "by_source": source_counts
        }
        
    def auto_acknowledge_old_alerts(self) -> None:
        """Автоматическое подтверждение старых уведомлений"""
        cutoff_time = datetime.now() - timedelta(hours=self.auto_acknowledge_after_hours)
        
        with self._lock:
            for alert in self._alerts:
                if (not alert.acknowledged and 
                    alert.timestamp < cutoff_time and 
                    alert.level in [AlertLevel.INFO, AlertLevel.WARNING]):
                    alert.acknowledged = True
                    alert.acknowledged_by = "auto"
                    alert.acknowledged_at = datetime.now()
                    
    def clear_old_alerts(self, days: int = 30) -> None:
        """Очистка старых уведомлений"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self._lock:
            self._alerts = [a for a in self._alerts if a.timestamp > cutoff_time]
            
        self.logger.info(f"Cleared alerts older than {days} days")
        
    def get_alerts_export(self) -> Dict[str, Any]:
        """Экспорт уведомлений"""
        with self._lock:
            return {
                "export_timestamp": datetime.now().isoformat(),
                "total_alerts": len(self._alerts),
                "alerts": [
                    {
                        "level": alert.level.value,
                        "message": alert.message,
                        "source": alert.source,
                        "timestamp": alert.timestamp.isoformat(),
                        "details": alert.details,
                        "acknowledged": alert.acknowledged,
                        "acknowledged_by": alert.acknowledged_by,
                        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
                    }
                    for alert in self._alerts[-500:]  # Последние 500 уведомлений
                ]
            }
