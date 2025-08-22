"""
@file: usage_metrics.py
@description: Статистика использования приложения
@dependencies: threading, datetime, utils.logger
@created: 2024-12-19
"""

import threading
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

from utils.logger import Logger


@dataclass
class UsageEvent:
    """Событие использования"""
    event_type: str
    user_id: Optional[str]
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None


@dataclass
class SessionInfo:
    """Информация о сессии пользователя"""
    session_id: str
    user_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    events: List[UsageEvent] = field(default_factory=list)
    total_duration: Optional[timedelta] = None


class UsageMetrics:
    """
    Статистика использования приложения
    
    Отслеживает:
    - Активность пользователей
    - Популярные функции
    - Время сессий
    - Частоту использования команд
    - Паттерны использования
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger(__name__)
        self._lock = threading.Lock()
        self._events: List[UsageEvent] = []
        self._sessions: Dict[str, SessionInfo] = {}
        self._current_session_id: Optional[str] = None
        self._session_start_time: Optional[datetime] = None
        
        # Настройки
        self.max_events_history = 10000
        self.max_sessions_history = 1000
        self.session_timeout_minutes = 30
        
        # Статистика
        self._command_usage = Counter()
        self._page_visits = Counter()
        self._error_counts = Counter()
        
    def start_session(self, user_id: Optional[str] = None) -> str:
        """Начало новой сессии"""
        session_id = f"session_{int(time.time())}_{threading.get_ident()}"
        
        session = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.now()
        )
        
        with self._lock:
            self._sessions[session_id] = session
            self._current_session_id = session_id
            self._session_start_time = datetime.now()
            
        self.logger.info(f"Started session {session_id} for user {user_id}")
        return session_id
        
    def end_session(self, session_id: Optional[str] = None) -> None:
        """Завершение сессии"""
        if session_id is None:
            session_id = self._current_session_id
            
        if not session_id:
            return
            
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.end_time = datetime.now()
                session.total_duration = session.end_time - session.start_time
                
                if session_id == self._current_session_id:
                    self._current_session_id = None
                    self._session_start_time = None
                    
        self.logger.info(f"Ended session {session_id}")
        
    def record_event(self, event_type: str, details: Optional[Dict[str, Any]] = None, 
                    user_id: Optional[str] = None) -> None:
        """Запись события использования"""
        # Убеждаемся что есть активная сессия
        if not self._current_session_id:
            self.start_session(user_id)
            
        event = UsageEvent(
            event_type=event_type,
            user_id=user_id,
            timestamp=datetime.now(),
            details=details or {},
            session_id=self._current_session_id
        )
        
        with self._lock:
            self._events.append(event)
            
            # Добавляем в текущую сессию
            if self._current_session_id in self._sessions:
                self._sessions[self._current_session_id].events.append(event)
                
            # Ограничиваем историю событий
            if len(self._events) > self.max_events_history:
                self._events = self._events[-self.max_events_history:]
                
        # Обновляем статистику
        self._update_statistics(event)
        
    def record_command_usage(self, command: str, success: bool, execution_time: float) -> None:
        """Запись использования команды"""
        self.record_event(
            event_type="command_executed",
            details={
                "command": command,
                "success": success,
                "execution_time": execution_time
            }
        )
        
    def record_page_visit(self, page_name: str, duration: Optional[float] = None) -> None:
        """Запись посещения страницы"""
        self.record_event(
            event_type="page_visited",
            details={
                "page": page_name,
                "duration": duration
            }
        )
        
    def record_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Запись ошибки"""
        self.record_event(
            event_type="error_occurred",
            details={
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {}
            }
        )
        
    def record_sequence_execution(self, sequence_name: str, success: bool, duration: float) -> None:
        """Запись выполнения последовательности"""
        self.record_event(
            event_type="sequence_executed",
            details={
                "sequence": sequence_name,
                "success": success,
                "duration": duration
            }
        )
        
    def _update_statistics(self, event: UsageEvent) -> None:
        """Обновление статистики на основе события"""
        if event.event_type == "command_executed":
            command = event.details.get("command", "unknown")
            self._command_usage[command] += 1
            
        elif event.event_type == "page_visited":
            page = event.details.get("page", "unknown")
            self._page_visits[page] += 1
            
        elif event.event_type == "error_occurred":
            error_type = event.details.get("error_type", "unknown")
            self._error_counts[error_type] += 1
            
    def get_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Получение сводки использования за период"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            recent_events = [e for e in self._events if e.timestamp > cutoff_time]
            recent_sessions = [
                s for s in self._sessions.values()
                if s.start_time > cutoff_time
            ]
            
        # Статистика по типам событий
        event_types = Counter(event.event_type for event in recent_events)
        
        # Популярные команды
        command_events = [e for e in recent_events if e.event_type == "command_executed"]
        command_stats = {}
        for event in command_events:
            command = event.details.get("command", "unknown")
            if command not in command_stats:
                command_stats[command] = {"count": 0, "success_count": 0, "total_time": 0}
            
            command_stats[command]["count"] += 1
            if event.details.get("success", False):
                command_stats[command]["success_count"] += 1
            command_stats[command]["total_time"] += event.details.get("execution_time", 0)
            
        # Вычисляем средние значения
        for command, stats in command_stats.items():
            if stats["count"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["count"]
                stats["success_rate"] = stats["success_count"] / stats["count"]
                
        # Статистика сессий
        active_sessions = [s for s in recent_sessions if s.end_time is None]
        completed_sessions = [s for s in recent_sessions if s.end_time is not None]
        
        avg_session_duration = None
        if completed_sessions:
            total_duration = sum(
                (s.total_duration or timedelta(0)).total_seconds()
                for s in completed_sessions
            )
            avg_session_duration = total_duration / len(completed_sessions)
            
        return {
            "period_hours": hours,
            "total_events": len(recent_events),
            "event_types": dict(event_types),
            "command_stats": command_stats,
            "sessions": {
                "total": len(recent_sessions),
                "active": len(active_sessions),
                "completed": len(completed_sessions),
                "avg_duration_minutes": avg_session_duration / 60 if avg_session_duration else None
            },
            "popular_pages": dict(self._page_visits.most_common(10)),
            "error_summary": dict(self._error_counts.most_common(10))
        }
        
    def get_user_activity(self, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Получение активности конкретного пользователя"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            user_events = [
                e for e in self._events
                if e.user_id == user_id and e.timestamp > cutoff_time
            ]
            user_sessions = [
                s for s in self._sessions.values()
                if s.user_id == user_id and s.start_time > cutoff_time
            ]
            
        return {
            "user_id": user_id,
            "period_hours": hours,
            "total_events": len(user_events),
            "sessions_count": len(user_sessions),
            "last_activity": max(e.timestamp for e in user_events) if user_events else None,
            "event_types": dict(Counter(e.event_type for e in user_events))
        }
        
    def get_command_usage_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Анализ использования команд"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self._lock:
            command_events = [
                e for e in self._events
                if e.event_type == "command_executed" and e.timestamp > cutoff_time
            ]
            
        # Группируем по дням
        daily_usage = defaultdict(lambda: defaultdict(int))
        for event in command_events:
            day = event.timestamp.date().isoformat()
            command = event.details.get("command", "unknown")
            daily_usage[day][command] += 1
            
        # Топ команд
        command_totals = Counter()
        for event in command_events:
            command = event.details.get("command", "unknown")
            command_totals[command] += 1
            
        return {
            "period_days": days,
            "total_commands": len(command_events),
            "unique_commands": len(command_totals),
            "top_commands": dict(command_totals.most_common(20)),
            "daily_usage": dict(daily_usage)
        }
        
    def get_session_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Анализ сессий пользователей"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self._lock:
            recent_sessions = [
                s for s in self._sessions.values()
                if s.start_time > cutoff_time
            ]
            
        # Статистика по продолжительности
        durations = []
        for session in recent_sessions:
            if session.total_duration:
                durations.append(session.total_duration.total_seconds() / 60)  # в минутах
                
        # Группируем по пользователям
        user_sessions = defaultdict(list)
        for session in recent_sessions:
            user_id = session.user_id or "anonymous"
            user_sessions[user_id].append(session)
            
        user_stats = {}
        for user_id, sessions in user_sessions.items():
            completed_sessions = [s for s in sessions if s.total_duration]
            user_stats[user_id] = {
                "total_sessions": len(sessions),
                "completed_sessions": len(completed_sessions),
                "avg_duration_minutes": sum(s.total_duration.total_seconds() for s in completed_sessions) / 60 / len(completed_sessions) if completed_sessions else 0
            }
            
        return {
            "period_days": days,
            "total_sessions": len(recent_sessions),
            "unique_users": len(user_sessions),
            "avg_session_duration_minutes": sum(durations) / len(durations) if durations else 0,
            "user_statistics": user_stats
        }
        
    def get_error_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Анализ ошибок"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self._lock:
            error_events = [
                e for e in self._events
                if e.event_type == "error_occurred" and e.timestamp > cutoff_time
            ]
            
        # Группируем по типам ошибок
        error_types = Counter()
        error_contexts = defaultdict(list)
        
        for event in error_events:
            error_type = event.details.get("error_type", "unknown")
            error_types[error_type] += 1
            error_contexts[error_type].append(event.details.get("context", {}))
            
        # Группируем по дням
        daily_errors = defaultdict(int)
        for event in error_events:
            day = event.timestamp.date().isoformat()
            daily_errors[day] += 1
            
        return {
            "period_days": days,
            "total_errors": len(error_events),
            "error_types": dict(error_types.most_common(20)),
            "daily_errors": dict(daily_errors),
            "error_contexts": dict(error_contexts)
        }
        
    def clear_old_data(self, days: int = 30) -> None:
        """Очистка старых данных"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self._lock:
            self._events = [e for e in self._events if e.timestamp > cutoff_time]
            
            # Очищаем завершенные сессии
            self._sessions = {
                session_id: session
                for session_id, session in self._sessions.items()
                if session.start_time > cutoff_time or session.end_time is None
            }
            
        self.logger.info(f"Cleared usage data older than {days} days")
        
    def get_usage_export(self) -> Dict[str, Any]:
        """Экспорт данных использования"""
        with self._lock:
            return {
                "export_timestamp": datetime.now().isoformat(),
                "total_events": len(self._events),
                "total_sessions": len(self._sessions),
                "events": [
                    {
                        "event_type": event.event_type,
                        "user_id": event.user_id,
                        "timestamp": event.timestamp.isoformat(),
                        "details": event.details,
                        "session_id": event.session_id
                    }
                    for event in self._events[-1000:]  # Последние 1000 событий
                ],
                "sessions": [
                    {
                        "session_id": session.session_id,
                        "user_id": session.user_id,
                        "start_time": session.start_time.isoformat(),
                        "end_time": session.end_time.isoformat() if session.end_time else None,
                        "total_duration_seconds": session.total_duration.total_seconds() if session.total_duration else None,
                        "events_count": len(session.events)
                    }
                    for session in list(self._sessions.values())[-100:]  # Последние 100 сессий
                ],
                "statistics": {
                    "command_usage": dict(self._command_usage.most_common(50)),
                    "page_visits": dict(self._page_visits.most_common(20)),
                    "error_counts": dict(self._error_counts.most_common(20))
                }
            }
