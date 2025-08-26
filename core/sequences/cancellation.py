"""
Модуль для управления отменой операций.

Содержит классы для безопасной отмены длительных операций:
- CancellationToken - токен для отмены операций
- CancellationException - исключение при отмене
- CancellationManager - менеджер для управления отменой операций
"""

import threading
import logging
from typing import Dict, Optional


class CancellationException(Exception):
    """Исключение при отмене операции"""
    pass


class CancellationToken:
    """Токен для отмены операций"""
    
    def __init__(self):
        self._cancelled = False
        self._lock = threading.Lock()
    
    def cancel(self):
        """Отменить операцию"""
        with self._lock:
            self._cancelled = True
    
    def is_cancelled(self) -> bool:
        """Проверить, отменена ли операция"""
        with self._lock:
            return self._cancelled
    
    def throw_if_cancelled(self):
        """Выбросить исключение если операция отменена"""
        if self.is_cancelled():
            raise CancellationException("Операция была отменена")
    
    def reset(self):
        """Сбросить состояние отмены"""
        with self._lock:
            self._cancelled = False


class CancellationManager:
    """Менеджер для управления отменой операций"""
    
    def __init__(self):
        self._tokens: Dict[str, CancellationToken] = {}
        self._lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
    
    def create_token(self, operation_id: str) -> CancellationToken:
        """Создать новый токен отмены для операции"""
        with self._lock:
            if operation_id in self._tokens:
                self.logger.warning(f"Токен для операции {operation_id} уже существует")
                return self._tokens[operation_id]
            
            token = CancellationToken()
            self._tokens[operation_id] = token
            self.logger.debug(f"Создан токен отмены для операции {operation_id}")
            return token
    
    def get_token(self, operation_id: str) -> Optional[CancellationToken]:
        """Получить токен отмены для операции"""
        with self._lock:
            return self._tokens.get(operation_id)
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Отменить операцию по ID"""
        with self._lock:
            token = self._tokens.get(operation_id)
            if token:
                token.cancel()
                self.logger.info(f"Операция {operation_id} отменена")
                return True
            else:
                self.logger.warning(f"Токен для операции {operation_id} не найден")
                return False
    
    def remove_token(self, operation_id: str) -> bool:
        """Удалить токен отмены для операции"""
        with self._lock:
            if operation_id in self._tokens:
                del self._tokens[operation_id]
                self.logger.debug(f"Токен для операции {operation_id} удален")
                return True
            return False
    
    def cleanup_completed_operations(self) -> int:
        """Очистить завершенные операции"""
        with self._lock:
            initial_count = len(self._tokens)
            # В реальной реализации здесь была бы логика определения завершенных операций
            # Пока просто возвращаем количество активных токенов
            return initial_count
    
    def get_active_operations_count(self) -> int:
        """Получить количество активных операций"""
        with self._lock:
            return len(self._tokens)
    
    def get_operation_status(self, operation_id: str) -> Optional[str]:
        """Получить статус операции"""
        with self._lock:
            token = self._tokens.get(operation_id)
            if token:
                return "cancelled" if token.is_cancelled() else "active"
            return None
