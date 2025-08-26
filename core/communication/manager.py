"""
Модуль для управления последовательной связью.

Содержит основной класс SerialManager который объединяет все компоненты
для управления последовательными соединениями, протоколами и потоками.
"""

import logging
import threading
import time
from typing import Optional, Callable, List, Dict, Any, Union
from PyQt6.QtCore import QThread, pyqtSignal as Signal

from .connection import SerialConnection
from .protocol import SerialProtocol, ProtocolType, ProtocolCommand, ProtocolResponse
from .threading import ThreadManager


class SerialReader(QThread):
    """Поток для чтения данных с Serial-порта"""

    data_received = Signal(str)
    error_occurred = Signal(str)
    signal_processed = Signal(str, str, str)  # signal_name, variable_name, value

    def __init__(self, connection: SerialConnection, signal_manager=None):
        super().__init__()
        self.connection = connection
        self.running = True
        self.logger = logging.getLogger(__name__)
        self._stop_event = threading.Event()
        self._interrupt_event = threading.Event()
        self._shutdown_timeout = 2.0  # Таймаут для graceful shutdown
        self.signal_manager = signal_manager  # Менеджер сигналов для обработки входящих данных

    def run(self):
        """Основной цикл чтения с поддержкой прерывания и обработки сигналов"""
        self.logger.debug("Запуск цикла чтения Serial")
        
        while (self.running and 
               self.connection.is_connected() and 
               not self._stop_event.is_set() and 
               not self._interrupt_event.is_set()):
            try:
                # Читаем данные из порта
                data = self.connection.read_line()
                if data:
                    # Эмитим сигнал для обычной обработки данных
                    self.data_received.emit(data)
                    self.logger.debug(f"Получено: {data}")
                    
                    # Обрабатываем данные как потенциальный сигнал UART
                    if self.signal_manager:
                        try:
                            result = self.signal_manager.process_incoming_data(data)
                            if result and result.is_success:
                                # Эмитим сигнал о успешной обработке сигнала
                                self.signal_processed.emit(
                                    result.signal_name,
                                    result.variable_name,
                                    str(result.value)
                                )
                                self.logger.debug(f"Сигнал обработан: {result.signal_name} = {result.value}")
                        except Exception as e:
                            self.logger.warning(f"Ошибка обработки сигнала '{data}': {e}")
                
                # Используем более короткий sleep для быстрого отклика на остановку
                for _ in range(10):  # 10 * 5ms = 50ms
                    if self._stop_event.is_set() or self._interrupt_event.is_set():
                        break
                    self.msleep(5)
                    
            except Exception as e:
                self.error_occurred.emit(f"Неожиданная ошибка: {e}")
                self.logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
                break
        
        self.logger.debug("Цикл чтения Serial завершен")

    def stop(self):
        """Graceful остановка потока с таймаутом и interrupt mechanism"""
        self.logger.info("Запрос остановки потока чтения...")
        self.running = False
        self._stop_event.set()
        
        # Ждем graceful остановки с таймаутом
        if not self.wait(int(self._shutdown_timeout * 1000)):  # Конвертируем в миллисекунды
            self.logger.warning(f"Таймаут graceful остановки потока чтения ({self._shutdown_timeout}s)")
            self.interrupt()  # Используем interrupt mechanism
            if not self.wait(500):  # Ждем еще 500ms
                self.logger.error("Не удалось остановить поток чтения")
                self.terminate()  # Принудительная остановка
                if not self.wait(500):
                    self.logger.error("Принудительная остановка потока чтения не удалась")
                else:
                    self.logger.info("Поток чтения принудительно остановлен")
            else:
                self.logger.info("Поток чтения остановлен через interrupt")
        else:
            self.logger.info("Поток чтения gracefully остановлен")

    def interrupt(self):
        """Прерывание потока чтения"""
        self.logger.debug("Прерывание потока чтения")
        self._interrupt_event.set()
        self.running = False


class SerialManager:
    """Менеджер Serial-соединения с улучшенным управлением потоками и поддержкой обработки сигналов"""

    def __init__(self, signal_manager=None, protocol_type: ProtocolType = ProtocolType.CUSTOM):
        # Компоненты
        self.connection = SerialConnection()
        self.protocol = SerialProtocol(protocol_type)
        self.thread_manager = ThreadManager()
        
        # Поток чтения
        self.reader_thread: Optional[SerialReader] = None
        
        # Логгер и блокировки
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        
        # Менеджер сигналов для обработки входящих данных UART
        self.signal_manager = signal_manager
        
        # Callbacks для событий
        self.on_data_received: Optional[Callable[[str], None]] = None
        self.on_error_occurred: Optional[Callable[[str], None]] = None
        self.on_signal_processed: Optional[Callable[[str, str, str], None]] = None
        self.on_connection_changed: Optional[Callable[[bool], None]] = None
        
        # Статистика
        self._stats = {
            'commands_sent': 0,
            'responses_received': 0,
            'errors': 0,
            'total_response_time': 0.0
        }
    
    def set_signal_manager(self, signal_manager):
        """
        Установка менеджера сигналов для обработки входящих данных
        
        Args:
            signal_manager: Экземпляр SignalManager
        """
        self.signal_manager = signal_manager
        self.logger.info("Менеджер сигналов установлен")
        
        # Обновляем менеджер сигналов в существующем потоке чтения
        if self.reader_thread:
            self.reader_thread.signal_manager = signal_manager
            self.logger.debug("Менеджер сигналов обновлен в потоке чтения")
    
    def get_signal_manager(self):
        """
        Получение текущего менеджера сигналов
        
        Returns:
            Текущий SignalManager или None
        """
        return self.signal_manager
    
    def connect(self, port: str, **kwargs) -> bool:
        """
        Подключение к последовательному порту.
        
        Args:
            port: Имя порта
            **kwargs: Настройки соединения
            
        Returns:
            True если подключение успешно
        """
        with self._lock:
            try:
                # Подключаемся через connection
                if self.connection.connect(port, **kwargs):
                    # Запускаем поток чтения
                    self._start_reader_thread()
                    
                    # Уведомляем об изменении состояния
                    self._notify_connection_changed(True)
                    
                    self.logger.info(f"Успешно подключен к порту {port}")
                    return True
                else:
                    self.logger.error(f"Не удалось подключиться к порту {port}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Ошибка подключения к порту {port}: {e}", exc_info=True)
                return False
    
    def disconnect(self) -> bool:
        """
        Отключение от последовательного порта.
        
        Returns:
            True если отключение успешно
        """
        with self._lock:
            try:
                # Останавливаем поток чтения
                self._stop_reader_thread()
                
                # Отключаемся через connection
                if self.connection.disconnect():
                    # Уведомляем об изменении состояния
                    self._notify_connection_changed(False)
                    
                    self.logger.info("Успешно отключен от порта")
                    return True
                else:
                    self.logger.error("Не удалось отключиться от порта")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Ошибка отключения от порта: {e}", exc_info=True)
                return False
    
    def reconnect(self, **kwargs) -> bool:
        """
        Переподключение к порту.
        
        Args:
            **kwargs: Настройки для нового соединения
            
        Returns:
            True если переподключение успешно
        """
        with self._lock:
            try:
                if self.connection.reconnect(**kwargs):
                    # Перезапускаем поток чтения
                    self._stop_reader_thread()
                    self._start_reader_thread()
                    
                    self.logger.info("Переподключение успешно")
                    return True
                else:
                    self.logger.error("Переподключение не удалось")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Ошибка переподключения: {e}", exc_info=True)
                return False
    
    def send_command(self, command: Union[str, ProtocolCommand], **kwargs) -> bool:
        """
        Отправка команды в порт.
        
        Args:
            command: Команда для отправки
            **kwargs: Дополнительные параметры
            
        Returns:
            True если команда отправлена успешно
        """
        with self._lock:
            if not self.connection.is_connected():
                self.logger.error("Не подключен к порту")
                return False
            
            try:
                # Валидируем команду
                is_valid, errors = self.protocol.validate_command(command)
                if not is_valid:
                    self.logger.error(f"Команда не прошла валидацию: {errors}")
                    return False
                
                # Форматируем команду
                formatted_command = self.protocol.format_command(command, **kwargs)
                
                # Отправляем данные
                if self.connection.send_data(formatted_command):
                    self._stats['commands_sent'] += 1
                    self.logger.debug(f"Команда отправлена: {formatted_command}")
                    return True
                else:
                    self.logger.error("Не удалось отправить команду")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Ошибка отправки команды: {e}", exc_info=True)
                return False
    
    def send_and_wait(self, command: Union[str, ProtocolCommand], 
                      timeout: Optional[float] = None, **kwargs) -> Optional[ProtocolResponse]:
        """
        Отправка команды и ожидание ответа.
        
        Args:
            command: Команда для отправки
            timeout: Таймаут ожидания ответа
            **kwargs: Дополнительные параметры
            
        Returns:
            Объект ProtocolResponse или None при ошибке
        """
        with self._lock:
            if not self.connection.is_connected():
                self.logger.error("Не подключен к порту")
                return None
            
            try:
                # Отправляем команду
                if not self.send_command(command, **kwargs):
                    return None
                
                # Ждем ответа
                start_time = time.time()
                timeout = timeout or self.protocol.default_timeout
                
                while time.time() - start_time < timeout:
                    # Читаем данные
                    data = self.connection.read_data()
                    if data:
                        # Парсим ответ
                        response = self.protocol.parse_response(data, str(command))
                        self._stats['responses_received'] += 1
                        self._stats['total_response_time'] += response.response_time
                        
                        self.logger.debug(f"Получен ответ: {response.status.value}")
                        return response
                    
                    # Небольшая пауза
                    time.sleep(0.01)
                
                # Таймаут
                self.logger.warning(f"Таймаут ожидания ответа на команду: {command}")
                return None
                
            except Exception as e:
                self.logger.error(f"Ошибка отправки и ожидания: {e}", exc_info=True)
                return None
    
    def _start_reader_thread(self):
        """Запуск потока чтения"""
        if self.reader_thread and self.reader_thread.isRunning():
            self.logger.warning("Поток чтения уже запущен")
            return
        
        try:
            self.reader_thread = SerialReader(self.connection, self.signal_manager)
            
            # Подключаем сигналы
            self.reader_thread.data_received.connect(self._on_data_received)
            self.reader_thread.error_occurred.connect(self._on_error_occurred)
            self.reader_thread.signal_processed.connect(self._on_signal_processed)
            
            # Запускаем поток
            self.reader_thread.start()
            self.logger.debug("Поток чтения запущен")
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска потока чтения: {e}", exc_info=True)
    
    def _stop_reader_thread(self):
        """Остановка потока чтения"""
        if self.reader_thread and self.reader_thread.isRunning():
            try:
                self.reader_thread.stop()
                self.reader_thread = None
                self.logger.debug("Поток чтения остановлен")
            except Exception as e:
                self.logger.error(f"Ошибка остановки потока чтения: {e}", exc_info=True)
    
    def _on_data_received(self, data: str):
        """Обработка полученных данных"""
        if self.on_data_received:
            try:
                self.on_data_received(data)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_data_received: {e}")
    
    def _on_error_occurred(self, error: str):
        """Обработка ошибок"""
        if self.on_error_occurred:
            try:
                self.on_error_occurred(error)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_error_occurred: {e}")
    
    def _on_signal_processed(self, signal_name: str, variable_name: str, value: str):
        """Обработка обработанных сигналов"""
        if self.on_signal_processed:
            try:
                self.on_signal_processed(signal_name, variable_name, value)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_signal_processed: {e}")
    
    def _notify_connection_changed(self, connected: bool):
        """Уведомление об изменении состояния подключения"""
        if self.on_connection_changed:
            try:
                self.on_connection_changed(connected)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_connection_changed: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Проверка состояния подключения"""
        return self.connection.is_connected()
    
    def get_available_ports(self) -> List[Dict[str, Any]]:
        """Получение списка доступных портов"""
        return SerialConnection.get_available_ports()
    
    def get_connection_info(self) -> Optional[Dict[str, Any]]:
        """Получение информации о текущем соединении"""
        return self.connection.get_port_info()
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """Получение информации о протоколе"""
        return self.protocol.get_protocol_info()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        stats = self._stats.copy()
        
        # Добавляем статистику протокола
        protocol_stats = self.protocol.get_statistics()
        stats.update(protocol_stats)
        
        # Добавляем статистику потоков
        thread_stats = self.thread_manager.get_thread_stats()
        stats.update(thread_stats)
        
        return stats
    
    def reset_statistics(self):
        """Сброс статистики"""
        self._stats = {
            'commands_sent': 0,
            'responses_received': 0,
            'errors': 0,
            'total_response_time': 0.0
        }
        self.protocol.reset_statistics()
        self.thread_manager.reset_stats()
        self.logger.debug("Статистика сброшена")
    
    def set_callbacks(self, 
                     on_data_received: Optional[Callable[[str], None]] = None,
                     on_error_occurred: Optional[Callable[[str], None]] = None,
                     on_signal_processed: Optional[Callable[[str, str, str], None]] = None,
                     on_connection_changed: Optional[Callable[[bool], None]] = None):
        """Установка callbacks для событий"""
        self.on_data_received = on_data_received
        self.on_error_occurred = on_error_occurred
        self.on_signal_processed = on_signal_processed
        self.on_connection_changed = on_connection_changed
    
    def set_protocol_type(self, protocol_type: ProtocolType):
        """Установка типа протокола"""
        self.protocol.set_protocol_type(protocol_type)
        self.logger.info(f"Тип протокола изменен на: {protocol_type.value}")
    
    def graceful_shutdown(self, timeout: float = 10.0):
        """
        Graceful shutdown всех компонентов
        
        Args:
            timeout: Общий таймаут для shutdown
        """
        self.logger.info("Начало graceful shutdown")
        
        # Останавливаем поток чтения
        self._stop_reader_thread()
        
        # Отключаемся от порта
        self.disconnect()
        
        # Останавливаем все потоки
        self.thread_manager.graceful_shutdown(timeout=timeout/2)
        
        self.logger.info("Graceful shutdown завершен")
    
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.graceful_shutdown()
            self.connection.cleanup()
            self.protocol.cleanup()
            self.logger.info("Ресурсы SerialManager очищены")
        except Exception as e:
            self.logger.error(f"Ошибка очистки ресурсов: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
