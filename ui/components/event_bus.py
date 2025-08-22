"""
/**
 * @file: event_bus.py
 * @description: Централизованная система событий для координации компонентов
 * @dependencies: PySide6.QtCore
 * @created: 2024-12-19
 */

Централизованная система событий для координации компонентов приложения.
Позволяет компонентам общаться друг с другом без прямых зависимостей.
"""

import logging
from typing import Dict, List, Callable, Any, Optional
from PySide6.QtCore import QObject, Signal, QTimer


class EventBus(QObject):
    """
    Централизованная система событий для координации компонентов приложения.
    
    Позволяет компонентам подписываться на события и отправлять их,
    обеспечивая слабую связанность между компонентами.
    """
    
    # Сигналы для основных событий приложения
    connection_status_changed = Signal(str, str)  # status, message
    page_changed = Signal(str)  # page_name
    sequence_started = Signal(str)  # sequence_name
    sequence_finished = Signal(bool, str)  # success, message
    command_executed = Signal(str, bool)  # command, success
    config_reloaded = Signal()
    error_occurred = Signal(str, str)  # error_type, message
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Реестр подписчиков на события
        self._subscribers: Dict[str, List[Callable]] = {}
        
        # Очередь событий для асинхронной обработки
        self._event_queue: List[Dict[str, Any]] = []
        
        # Таймер для обработки очереди событий
        self._queue_timer = QTimer()
        self._queue_timer.timeout.connect(self._process_event_queue)
        self._queue_timer.start(10)  # Обрабатываем каждые 10мс
        
        self.logger.info("EventBus инициализирован")
    
    def subscribe(self, event_type: str, callback: Callable) -> bool:
        """
        Подписка на событие определенного типа.
        
        Args:
            event_type: Тип события
            callback: Функция-обработчик события
            
        Returns:
            True если подписка успешна, False в противном случае
        """
        try:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
                self.logger.debug(f"Подписка на событие '{event_type}' добавлена")
                return True
            else:
                self.logger.warning(f"Callback уже подписан на событие '{event_type}'")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка подписки на событие '{event_type}': {e}")
            return False
    
    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """
        Отписка от события.
        
        Args:
            event_type: Тип события
            callback: Функция-обработчик для отписки
            
        Returns:
            True если отписка успешна, False в противном случае
        """
        try:
            if event_type in self._subscribers and callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                self.logger.debug(f"Отписка от события '{event_type}' выполнена")
                return True
            else:
                self.logger.warning(f"Callback не найден для события '{event_type}'")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка отписки от события '{event_type}': {e}")
            return False
    
    def emit(self, event_type: str, **kwargs) -> bool:
        """
        Отправка события всем подписчикам.
        
        Args:
            event_type: Тип события
            **kwargs: Параметры события
            
        Returns:
            True если событие отправлено, False в противном случае
        """
        try:
            # Добавляем событие в очередь для асинхронной обработки
            event_data = {
                'type': event_type,
                'kwargs': kwargs,
                'timestamp': QTimer.currentTime()
            }
            self._event_queue.append(event_data)
            
            self.logger.debug(f"Событие '{event_type}' добавлено в очередь")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления события '{event_type}' в очередь: {e}")
            return False
    
    def emit_sync(self, event_type: str, **kwargs) -> bool:
        """
        Синхронная отправка события всем подписчикам.
        
        Args:
            event_type: Тип события
            **kwargs: Параметры события
            
        Returns:
            True если событие отправлено, False в противном случае
        """
        try:
            if event_type in self._subscribers:
                for callback in self._subscribers[event_type]:
                    try:
                        callback(**kwargs)
                    except Exception as e:
                        self.logger.error(f"Ошибка в callback для события '{event_type}': {e}")
                
                self.logger.debug(f"Событие '{event_type}' синхронно отправлено {len(self._subscribers[event_type])} подписчикам")
                return True
            else:
                self.logger.debug(f"Нет подписчиков на событие '{event_type}'")
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка синхронной отправки события '{event_type}': {e}")
            return False
    
    def _process_event_queue(self):
        """Обработка очереди событий"""
        try:
            if not self._event_queue:
                return
            
            # Обрабатываем события из очереди
            events_to_process = self._event_queue.copy()
            self._event_queue.clear()
            
            for event_data in events_to_process:
                event_type = event_data['type']
                kwargs = event_data['kwargs']
                
                if event_type in self._subscribers:
                    for callback in self._subscribers[event_type]:
                        try:
                            callback(**kwargs)
                        except Exception as e:
                            self.logger.error(f"Ошибка в callback для события '{event_type}': {e}")
                    
                    self.logger.debug(f"Событие '{event_type}' обработано {len(self._subscribers[event_type])} подписчиками")
                else:
                    self.logger.debug(f"Нет подписчиков на событие '{event_type}'")
                    
        except Exception as e:
            self.logger.error(f"Ошибка обработки очереди событий: {e}")
    
    def get_subscriber_count(self, event_type: str) -> int:
        """
        Получение количества подписчиков на событие.
        
        Args:
            event_type: Тип события
            
        Returns:
            Количество подписчиков
        """
        return len(self._subscribers.get(event_type, []))
    
    def get_all_event_types(self) -> List[str]:
        """
        Получение списка всех типов событий.
        
        Returns:
            Список типов событий
        """
        return list(self._subscribers.keys())
    
    def clear_subscribers(self, event_type: Optional[str] = None):
        """
        Очистка подписчиков.
        
        Args:
            event_type: Тип события для очистки, если None - очищаем все
        """
        try:
            if event_type is None:
                self._subscribers.clear()
                self.logger.info("Все подписчики очищены")
            elif event_type in self._subscribers:
                self._subscribers[event_type].clear()
                self.logger.info(f"Подписчики события '{event_type}' очищены")
                
        except Exception as e:
            self.logger.error(f"Ошибка очистки подписчиков: {e}")
    
    def cleanup(self):
        """Очистка ресурсов EventBus"""
        try:
            self._queue_timer.stop()
            self.clear_subscribers()
            self._event_queue.clear()
            self.logger.info("EventBus очищен")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки EventBus: {e}")


# Глобальный экземпляр EventBus для использования в приложении
event_bus = EventBus()
