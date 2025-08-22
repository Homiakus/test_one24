"""
/**
 * @file: connection_manager.py
 * @description: Менеджер Serial подключений и управления состоянием соединения
 * @dependencies: PySide6.QtCore, PySide6.QtWidgets, core.serial_manager, event_bus
 * @created: 2024-12-19
 */

Менеджер подключений отвечает за управление Serial соединениями,
мониторинг состояния подключения и координацию с другими компонентами.
"""

import logging
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QLabel, QStatusBar

from core.serial_manager import SerialManager
from .event_bus import event_bus


class ConnectionManager(QObject):
    """
    Менеджер Serial подключений и управления состоянием соединения.
    
    Отвечает за подключение/отключение от устройств, мониторинг состояния
    и координацию с другими компонентами через EventBus.
    """
    
    # Сигналы состояния подключения
    connection_status_changed = Signal(str, str)  # status, message
    connection_established = Signal(str)  # port
    connection_lost = Signal(str)  # reason
    data_received = Signal(str)  # data
    error_occurred = Signal(str, str)  # error_type, message
    
    def __init__(self, serial_manager: SerialManager, status_bar: QStatusBar = None):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Основные компоненты
        self.serial_manager = serial_manager
        self.status_bar = status_bar
        
        # Состояние подключения
        self.connection_status = "disconnected"
        self.current_port = None
        
        # Таймеры
        self.connection_check_timer = QTimer()
        self.connection_check_timer.timeout.connect(self._check_connection_status)
        self.connection_check_timer.start(5000)  # Проверяем каждые 5 секунд
        
        # Автоподключение
        self.auto_connect_enabled = False
        self.auto_connect_delay = 2000  # мс
        
        # Подписка на события
        self._setup_event_subscriptions()
        
        # Подключение сигналов SerialManager
        self._setup_serial_connections()
        
        self.logger.info("ConnectionManager инициализирован")
    
    def _setup_event_subscriptions(self):
        """Настройка подписок на события"""
        try:
            # Подписываемся на события управления подключениями
            event_bus.subscribe("connect_requested", self._on_connect_requested)
            event_bus.subscribe("disconnect_requested", self._on_disconnect_requested)
            event_bus.subscribe("auto_connect_enabled", self._on_auto_connect_enabled)
            event_bus.subscribe("auto_connect_disabled", self._on_auto_connect_disabled)
            
        except Exception as e:
            self.logger.error(f"Ошибка настройки подписок на события: {e}")
    
    def _setup_serial_connections(self):
        """Настройка соединений с SerialManager"""
        try:
            if self.serial_manager.reader_thread:
                self.serial_manager.reader_thread.data_received.connect(
                    self._on_data_received
                )
                self.serial_manager.reader_thread.error_occurred.connect(
                    self._on_serial_error
                )
                self.logger.info("Сигналы SerialManager подключены")
            else:
                self.logger.warning("Reader thread недоступен для подключения сигналов")
                
        except Exception as e:
            self.logger.error(f"Ошибка настройки соединений с SerialManager: {e}")
    
    def connect_to_port(self, port: str, settings: Dict[str, Any] = None) -> bool:
        """
        Подключение к указанному порту.
        
        Args:
            port: Имя порта для подключения
            settings: Настройки подключения
            
        Returns:
            True если подключение успешно, False в противном случае
        """
        try:
            if not port or port.strip() == '':
                self.logger.error("Порт не указан")
                self._update_status("error", "Порт не указан")
                return False
            
            # Проверяем доступность порта
            available_ports = SerialManager.get_available_ports()
            if port not in available_ports:
                self.logger.warning(f"Порт {port} недоступен. Доступные: {available_ports}")
                self._update_status("error", f"Порт {port} недоступен")
                return False
            
            # Обновляем статус
            self._update_status("connecting", f"Подключение к {port}...")
            
            # Выполняем подключение
            if settings:
                success = self.serial_manager.connect(
                    port=port,
                    baudrate=settings.get('baudrate', 9600),
                    bytesize=settings.get('bytesize', 8),
                    parity=settings.get('parity', 'N'),
                    stopbits=settings.get('stopbits', 1),
                    timeout=settings.get('timeout', 1)
                )
            else:
                success = self.serial_manager.connect(port=port)
            
            if success:
                self.current_port = port
                self.connection_status = "connected"
                self._update_status("connected", f"Подключено к {port}")
                
                # Отправляем событие
                event_bus.emit("connection_established", port=port)
                self.connection_established.emit(port)
                
                self.logger.info(f"Успешно подключено к {port}")
                return True
            else:
                self._update_status("error", f"Не удалось подключиться к {port}")
                self.logger.error(f"Не удалось подключиться к {port}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка подключения к {port}: {e}")
            self._update_status("error", f"Ошибка подключения: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        Отключение от текущего порта.
        
        Returns:
            True если отключение успешно, False в противном случае
        """
        try:
            if not self.serial_manager.is_connected:
                self.logger.debug("Уже отключено")
                return True
            
            # Отключаем обработчики данных
            self._disconnect_data_handlers()
            
            # Отключаемся от порта
            self.serial_manager.disconnect()
            
            # Обновляем состояние
            old_port = self.current_port
            self.current_port = None
            self.connection_status = "disconnected"
            self._update_status("disconnected", "Отключено")
            
            # Отправляем событие
            event_bus.emit("connection_lost", reason="manual_disconnect")
            self.connection_lost.emit("manual_disconnect")
            
            self.logger.info(f"Отключено от {old_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка отключения: {e}")
            self._update_status("error", f"Ошибка отключения: {e}")
            return False
    
    def enable_auto_connect(self, enabled: bool = True):
        """
        Включение/выключение автоподключения.
        
        Args:
            enabled: True для включения, False для выключения
        """
        try:
            self.auto_connect_enabled = enabled
            
            if enabled:
                self.logger.info("Автоподключение включено")
                event_bus.emit("auto_connect_enabled")
            else:
                self.logger.info("Автоподключение выключено")
                event_bus.emit("auto_connect_disabled")
                
        except Exception as e:
            self.logger.error(f"Ошибка изменения состояния автоподключения: {e}")
    
    def perform_auto_connect(self, port: str, settings: Dict[str, Any] = None):
        """
        Выполнение автоподключения с задержкой.
        
        Args:
            port: Порт для подключения
            settings: Настройки подключения
        """
        try:
            if not self.auto_connect_enabled:
                self.logger.debug("Автоподключение отключено")
                return
            
            self.logger.info(f"Запуск автоподключения к {port} через {self.auto_connect_delay}мс")
            
            # Запускаем подключение с задержкой
            QTimer.singleShot(self.auto_connect_delay, 
                             lambda: self._safe_auto_connect(port, settings))
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска автоподключения: {e}")
    
    def _safe_auto_connect(self, port: str, settings: Dict[str, Any] = None):
        """
        Безопасное автоподключение с обработкой ошибок.
        
        Args:
            port: Порт для подключения
            settings: Настройки подключения
        """
        try:
            if self.connection_status == "connected":
                self.logger.debug("Уже подключено, автоподключение не требуется")
                return
            
            self.connect_to_port(port, settings)
            
        except Exception as e:
            self.logger.error(f"Ошибка безопасного автоподключения: {e}")
    
    def _check_connection_status(self):
        """Проверка состояния подключения"""
        try:
            if self.serial_manager.is_connected:
                if self.connection_status != "connected":
                    self.connection_status = "connected"
                    self._update_status("connected", "Подключено")
            else:
                if self.connection_status != "disconnected":
                    self.connection_status = "disconnected"
                    self._update_status("disconnected", "Отключено")
                    
        except Exception as e:
            self.logger.error(f"Ошибка проверки состояния подключения: {e}")
    
    def _update_status(self, status: str, message: str = ""):
        """
        Обновление статуса подключения.
        
        Args:
            status: Новый статус
            message: Сообщение о статусе
        """
        try:
            self.connection_status = status
            
            # Отправляем событие
            event_bus.emit("connection_status_changed", status=status, message=message)
            self.connection_status_changed.emit(status, message)
            
            # Обновляем статусную строку
            if self.status_bar and message:
                self.status_bar.showMessage(message, 3000)
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса: {e}")
    
    def _disconnect_data_handlers(self):
        """Отключение обработчиков данных"""
        try:
            if self.serial_manager.reader_thread:
                try:
                    self.serial_manager.reader_thread.data_received.disconnect()
                    self.serial_manager.reader_thread.error_occurred.disconnect()
                except:
                    pass  # Игнорируем ошибки отключения
                    
        except Exception as e:
            self.logger.error(f"Ошибка отключения обработчиков данных: {e}")
    
    def _on_data_received(self, data: str):
        """
        Обработчик получения данных.
        
        Args:
            data: Полученные данные
        """
        try:
            self.logger.debug(f"Получено: {data}")
            
            # Отправляем событие
            event_bus.emit("data_received", data=data)
            self.data_received.emit(data)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки полученных данных: {e}")
    
    def _on_serial_error(self, error: str):
        """
        Обработчик ошибки Serial.
        
        Args:
            error: Описание ошибки
        """
        try:
            self.logger.error(f"Ошибка Serial: {error}")
            
            # Обновляем статус
            self._update_status("error", f"Ошибка: {error}")
            
            # Отправляем событие
            event_bus.emit("error_occurred", error_type="serial_error", message=error)
            self.error_occurred.emit("serial_error", error)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки ошибки Serial: {e}")
    
    def _on_connect_requested(self, port: str, settings: Dict[str, Any] = None):
        """
        Обработчик события запроса подключения.
        
        Args:
            port: Порт для подключения
            settings: Настройки подключения
        """
        try:
            self.connect_to_port(port, settings)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки запроса подключения: {e}")
    
    def _on_disconnect_requested(self):
        """Обработчик события запроса отключения"""
        try:
            self.disconnect()
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки запроса отключения: {e}")
    
    def _on_auto_connect_enabled(self):
        """Обработчик события включения автоподключения"""
        try:
            self.enable_auto_connect(True)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки включения автоподключения: {e}")
    
    def _on_auto_connect_disabled(self):
        """Обработчик события выключения автоподключения"""
        try:
            self.enable_auto_connect(False)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки выключения автоподключения: {e}")
    
    def get_connection_status(self) -> str:
        """
        Получение текущего статуса подключения.
        
        Returns:
            Текущий статус подключения
        """
        return self.connection_status
    
    def get_current_port(self) -> Optional[str]:
        """
        Получение текущего порта подключения.
        
        Returns:
            Текущий порт или None если не подключено
        """
        return self.current_port
    
    def is_connected(self) -> bool:
        """
        Проверка состояния подключения.
        
        Returns:
            True если подключено, False в противном случае
        """
        return self.connection_status == "connected"
    
    def get_available_ports(self) -> list:
        """
        Получение списка доступных портов.
        
        Returns:
            Список доступных портов
        """
        try:
            return SerialManager.get_available_ports()
        except Exception as e:
            self.logger.error(f"Ошибка получения списка портов: {e}")
            return []
    
    def cleanup(self):
        """Очистка ресурсов ConnectionManager"""
        try:
            # Отписываемся от событий
            event_bus.unsubscribe("connect_requested", self._on_connect_requested)
            event_bus.unsubscribe("disconnect_requested", self._on_disconnect_requested)
            event_bus.unsubscribe("auto_connect_enabled", self._on_auto_connect_enabled)
            event_bus.unsubscribe("auto_connect_disabled", self._on_auto_connect_disabled)
            
            # Останавливаем таймеры
            self.connection_check_timer.stop()
            
            # Отключаемся если подключены
            if self.is_connected():
                self.disconnect()
            
            # Отключаем обработчики данных
            self._disconnect_data_handlers()
            
            self.logger.info("ConnectionManager очищен")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки ConnectionManager: {e}")
