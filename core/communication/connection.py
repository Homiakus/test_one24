"""
Модуль для управления последовательными соединениями.

Содержит класс SerialConnection для управления физическим подключением
к последовательным портам с поддержкой различных настроек и состояний.
"""

import logging
import threading
import time
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from collections import deque

import serial
import serial.tools.list_ports


class ConnectionPool:
    """Пул соединений для защиты от DoS атак"""
    
    def __init__(self, max_connections: int = 10, max_idle_time: float = 300.0):
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.connection_queue = deque()
        self._lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
    
    def can_create_connection(self, port: str) -> bool:
        """Проверить, можно ли создать новое соединение"""
        with self._lock:
            # Проверяем лимит активных соединений
            if len(self.active_connections) >= self.max_connections:
                self.logger.warning(f"Достигнут лимит соединений: {self.max_connections}")
                return False
            
            # Проверяем, не существует ли уже соединение с этим портом
            if port in self.active_connections:
                self.logger.warning(f"Соединение с портом {port} уже существует")
                return False
            
            return True
    
    def register_connection(self, port: str, connection_info: Dict[str, Any]) -> bool:
        """Зарегистрировать новое соединение"""
        with self._lock:
            if not self.can_create_connection(port):
                return False
            
            connection_info['created_at'] = time.time()
            connection_info['last_activity'] = time.time()
            self.active_connections[port] = connection_info
            
            self.logger.info(f"Зарегистрировано соединение с портом {port}. "
                           f"Активных соединений: {len(self.active_connections)}")
            return True
    
    def update_activity(self, port: str) -> None:
        """Обновить время последней активности соединения"""
        with self._lock:
            if port in self.active_connections:
                self.active_connections[port]['last_activity'] = time.time()
    
    def remove_connection(self, port: str) -> bool:
        """Удалить соединение из пула"""
        with self._lock:
            if port in self.active_connections:
                del self.active_connections[port]
                self.logger.info(f"Удалено соединение с портом {port}. "
                               f"Активных соединений: {len(self.active_connections)}")
                return True
            return False
    
    def cleanup_idle_connections(self) -> int:
        """Очистить неактивные соединения"""
        current_time = time.time()
        removed_count = 0
        
        with self._lock:
            ports_to_remove = []
            for port, info in self.active_connections.items():
                idle_time = current_time - info['last_activity']
                if idle_time > self.max_idle_time:
                    ports_to_remove.append(port)
            
            for port in ports_to_remove:
                self.remove_connection(port)
                removed_count += 1
        
        if removed_count > 0:
            self.logger.info(f"Очищено {removed_count} неактивных соединений")
        
        return removed_count
    
    def get_connection_info(self, port: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о соединении"""
        with self._lock:
            return self.active_connections.get(port)
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Получить статистику пула соединений"""
        with self._lock:
            current_time = time.time()
            idle_connections = sum(
                1 for info in self.active_connections.values()
                if current_time - info['last_activity'] > self.max_idle_time
            )
            
            return {
                'max_connections': self.max_connections,
                'active_connections': len(self.active_connections),
                'idle_connections': idle_connections,
                'available_slots': self.max_connections - len(self.active_connections),
                'max_idle_time': self.max_idle_time
            }


class SerialConnection:
    """
    Управление последовательным соединением.
    
    Отвечает за физическое подключение к последовательным портам,
    управление настройками соединения и мониторинг состояния.
    """
    
    def __init__(self, connection_pool: Optional[ConnectionPool] = None):
        self.port: Optional[serial.Serial] = None
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        self.connection_pool = connection_pool or ConnectionPool()
        
        self._connection_state = {
            'connected': False,
            'connecting': False,
            'disconnecting': False,
            'last_operation': None,
            'operation_timestamp': 0,
            'port_info': None,
            'connection_attempts': 0,
            'last_error': None
        }
        
        # Настройки по умолчанию
        self.default_settings = {
            'baudrate': 9600,
            'bytesize': serial.EIGHTBITS,
            'parity': serial.PARITY_NONE,
            'stopbits': serial.STOPBITS_ONE,
            'timeout': 1.0,
            'write_timeout': 1.0
        }
    
    def connect(self, port: str, **kwargs) -> bool:
        """
        Подключение к последовательному порту.
        
        Args:
            port: Имя порта (например, 'COM1', '/dev/ttyUSB0')
            **kwargs: Дополнительные настройки соединения
            
        Returns:
            True если подключение успешно
        """
        with self._lock:
            if self._connection_state['connected']:
                self.logger.warning(f"Уже подключен к порту {port}")
                return True
            
            if self._connection_state['connecting']:
                self.logger.warning("Подключение уже выполняется")
                return False
            
            # Проверяем лимиты пула соединений
            if not self.connection_pool.can_create_connection(port):
                self.logger.error(f"Не удалось создать соединение с портом {port}: превышен лимит")
                return False
            
            self._update_connection_state(connecting=True, last_error=None)
            
            try:
                # Объединяем настройки по умолчанию с пользовательскими
                settings = self.default_settings.copy()
                settings.update(kwargs)
                
                self.logger.info(f"Подключение к порту {port} с настройками: {settings}")
                
                # Создаем соединение
                self.port = serial.Serial(
                    port=port,
                    **settings
                )
                
                # Проверяем, что порт действительно открыт
                if not self.port.is_open:
                    raise serial.SerialException("Порт не открылся после создания")
                
                # Регистрируем соединение в пуле
                connection_info = {
                    'port': port,
                    'settings': settings,
                    'connection_time': time.time()
                }
                
                if not self.connection_pool.register_connection(port, connection_info):
                    self.logger.error(f"Не удалось зарегистрировать соединение в пуле для порта {port}")
                    self.port.close()
                    self.port = None
                    return False
                
                # Обновляем состояние
                port_info = self._get_port_info(port)
                self._update_connection_state(
                    connected=True,
                    connecting=False,
                    port_info=port_info,
                    connection_attempts=self._connection_state['connection_attempts'] + 1
                )
                
                self.logger.info(f"Успешно подключен к порту {port}")
                return True
                
            except serial.SerialException as e:
                error_msg = f"Ошибка подключения к порту {port}: {e}"
                self.logger.error(error_msg)
                self._update_connection_state(
                    connecting=False,
                    last_error=str(e)
                )
                return False
                
            except Exception as e:
                error_msg = f"Неожиданная ошибка подключения к порту {port}: {e}"
                self.logger.error(error_msg, exc_info=True)
                self._update_connection_state(
                    connecting=False,
                    last_error=str(e)
                )
                return False
    
    def disconnect(self) -> bool:
        """
        Отключение от последовательного порта.
        
        Returns:
            True если отключение успешно
        """
        with self._lock:
            if not self._connection_state['connected']:
                self.logger.warning("Не подключен к порту")
                return True
            
            if self._connection_state['disconnecting']:
                self.logger.warning("Отключение уже выполняется")
                return False
            
            self._update_connection_state(disconnecting=True)
            
            try:
                # Получаем информацию о порте для удаления из пула
                port_info = self._connection_state['port_info']
                port_name = None
                if port_info and 'port' in port_info:
                    port_name = port_info['port']
                
                if self.port and self.port.is_open:
                    self.logger.info("Отключение от порта")
                    self.port.close()
                
                self.port = None
                
                # Удаляем соединение из пула
                if port_name:
                    self.connection_pool.remove_connection(port_name)
                
                self._update_connection_state(
                    connected=False,
                    disconnecting=False,
                    port_info=None
                )
                
                self.logger.info("Успешно отключен от порта")
                return True
                
            except Exception as e:
                error_msg = f"Ошибка отключения от порта: {e}"
                self.logger.error(error_msg, exc_info=True)
                self._update_connection_state(
                    disconnecting=False,
                    last_error=str(e)
                )
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
            if not self._connection_state['connected']:
                self.logger.warning("Не подключен к порту для переподключения")
                return False
            
            port_info = self._connection_state['port_info']
            if not port_info:
                self.logger.error("Нет информации о текущем порте")
                return False
            
            port_name = port_info.get('port')
            if not port_name:
                self.logger.error("Не удалось определить имя порта")
                return False
            
            self.logger.info(f"Переподключение к порту {port_name}")
            
            # Отключаемся
            if not self.disconnect():
                return False
            
            # Ждем немного перед повторным подключением
            time.sleep(0.5)
            
            # Подключаемся заново
            return self.connect(port_name, **kwargs)
    
    def send_data(self, data: bytes) -> bool:
        """
        Отправка данных в порт.
        
        Args:
            data: Данные для отправки
            
        Returns:
            True если данные отправлены успешно
        """
        with self._lock:
            if not self._connection_state['connected']:
                self.logger.error("Не подключен к порту")
                return False
            
            if not self.port or not self.port.is_open:
                self.logger.error("Порт не открыт")
                return False
            
            try:
                bytes_written = self.port.write(data)
                if bytes_written == len(data):
                    self.logger.debug(f"Отправлено {bytes_written} байт")
                    return True
                else:
                    self.logger.warning(f"Отправлено {bytes_written} из {len(data)} байт")
                    return False
                    
            except serial.SerialException as e:
                error_msg = f"Ошибка отправки данных: {e}"
                self.logger.error(error_msg)
                self._update_connection_state(last_error=str(e))
                return False
                
            except Exception as e:
                error_msg = f"Неожиданная ошибка отправки данных: {e}"
                self.logger.error(error_msg, exc_info=True)
                self._update_connection_state(last_error=str(e))
                return False
    
    def read_data(self, size: int = 1) -> Optional[bytes]:
        """
        Чтение данных из порта.
        
        Args:
            size: Количество байт для чтения
            
        Returns:
            Прочитанные данные или None при ошибке
        """
        with self._lock:
            if not self._connection_state['connected']:
                self.logger.error("Не подключен к порту")
                return None
            
            if not self.port or not self.port.is_open:
                self.logger.error("Порт не открыт")
                return None
            
            try:
                data = self.port.read(size)
                if data:
                    self.logger.debug(f"Прочитано {len(data)} байт")
                    return data
                else:
                    self.logger.debug("Нет данных для чтения")
                    return b''
                    
            except serial.SerialException as e:
                error_msg = f"Ошибка чтения данных: {e}"
                self.logger.error(error_msg)
                self._update_connection_state(last_error=str(e))
                return None
                
            except Exception as e:
                error_msg = f"Неожиданная ошибка чтения данных: {e}"
                self.logger.error(error_msg, exc_info=True)
                self._update_connection_state(last_error=str(e))
                return None
    
    def read_line(self) -> Optional[str]:
        """
        Чтение строки из порта.
        
        Returns:
            Прочитанная строка или None при ошибке
        """
        with self._lock:
            if not self._connection_state['connected']:
                self.logger.error("Не подключен к порту")
                return None
            
            if not self.port or not self.port.is_open:
                self.logger.error("Порт не открыт")
                return None
            
            try:
                line = self.port.readline()
                if line:
                    decoded_line = line.decode('utf-8', errors='ignore').strip()
                    self.logger.debug(f"Прочитана строка: {decoded_line}")
                    return decoded_line
                else:
                    self.logger.debug("Нет строк для чтения")
                    return None
                    
            except serial.SerialException as e:
                error_msg = f"Ошибка чтения строки: {e}"
                self.logger.error(error_msg)
                self._update_connection_state(last_error=str(e))
                return None
                
            except Exception as e:
                error_msg = f"Неожиданная ошибка чтения строки: {e}"
                self.logger.error(error_msg, exc_info=True)
                self._update_connection_state(last_error=str(e))
                return None
    
    def flush_buffers(self):
        """Очистка буферов ввода/вывода"""
        with self._lock:
            if self.port and self.port.is_open:
                try:
                    self.port.reset_input_buffer()
                    self.port.reset_output_buffer()
                    self.logger.debug("Буферы очищены")
                except Exception as e:
                    self.logger.warning(f"Ошибка очистки буферов: {e}")
    
    def get_port_info(self) -> Optional[Dict[str, Any]]:
        """Получение информации о текущем порте"""
        with self._lock:
            return self._connection_state['port_info'].copy() if self._connection_state['port_info'] else None
    
    def get_connection_state(self) -> Dict[str, Any]:
        """Получение состояния соединения"""
        with self._lock:
            return self._connection_state.copy()
    
    def is_connected(self) -> bool:
        """Проверка состояния подключения"""
        with self._lock:
            if not self._connection_state['connected']:
                return False
            
            # Дополнительная проверка физического состояния порта
            if self.port is None:
                self._update_connection_state(connected=False)
                return False
            
            try:
                if not hasattr(self.port, 'is_open') or not self.port.is_open:
                    self._update_connection_state(connected=False)
                    return False
                return True
            except Exception as e:
                self.logger.error(f"Ошибка проверки состояния порта: {e}")
                self._update_connection_state(connected=False)
                return False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Получить статистику соединения"""
        with self._lock:
            stats = self._connection_state.copy()
            if self.port:
                stats['port_open'] = self.port.is_open
                stats['port_name'] = self.port.port
                stats['baudrate'] = self.port.baudrate
            else:
                stats['port_open'] = False
                stats['port_name'] = None
                stats['baudrate'] = None
            
            # Добавляем статистику пула соединений
            pool_stats = self.connection_pool.get_pool_stats()
            stats['pool_stats'] = pool_stats
            
            return stats
    
    def get_security_info(self) -> Dict[str, Any]:
        """Получить информацию о безопасности соединения"""
        with self._lock:
            pool_stats = self.connection_pool.get_pool_stats()
            
            return {
                'max_connections': pool_stats['max_connections'],
                'active_connections': pool_stats['active_connections'],
                'available_slots': pool_stats['available_slots'],
                'max_idle_time': pool_stats['max_idle_time'],
                'connection_limits_enabled': True,
                'dos_protection': True,
                'connection_pooling': True
            }
    
    def cleanup_idle_connections(self) -> int:
        """Очистить неактивные соединения в пуле"""
        return self.connection_pool.cleanup_idle_connections()
    
    def set_connection_limits(self, max_connections: int, max_idle_time: float) -> bool:
        """Установить лимиты соединений"""
        try:
            self.connection_pool.max_connections = max_connections
            self.connection_pool.max_idle_time = max_idle_time
            self.logger.info(f"Лимиты соединений обновлены: max={max_connections}, idle={max_idle_time}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка установки лимитов соединений: {e}")
            return False
    
    @staticmethod
    def get_available_ports() -> List[Dict[str, Any]]:
        """
        Получение списка доступных портов.
        
        Returns:
            Список словарей с информацией о портах
        """
        try:
            ports = []
            available_ports = serial.tools.list_ports.comports()
            
            for port in available_ports:
                port_info = {
                    'port': port.device,
                    'description': port.description,
                    'manufacturer': port.manufacturer,
                    'product': port.product,
                    'vid': port.vid,
                    'pid': port.pid,
                    'serial_number': port.serial_number,
                    'hwid': port.hwid
                }
                ports.append(port_info)
            
            logging.getLogger(__name__).info(f"Найдено портов: {len(ports)}")
            return ports
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Ошибка получения списка портов: {e}")
            return []
    
    def _update_connection_state(self, **kwargs):
        """Обновление состояния соединения"""
        self._connection_state.update(kwargs)
        self._connection_state['last_operation'] = kwargs.get('connected', self._connection_state['connected'])
        self._connection_state['operation_timestamp'] = time.time()
    
    def _get_port_info(self, port_name: str) -> Dict[str, Any]:
        """Получение информации о порте"""
        try:
            available_ports = serial.tools.list_ports.comports()
            for port in available_ports:
                if port.device == port_name:
                    return {
                        'port': port.device,
                        'description': port.description,
                        'manufacturer': port.manufacturer,
                        'product': port.product,
                        'vid': port.vid,
                        'pid': port.pid,
                        'serial_number': port.serial_number,
                        'hwid': port.hwid
                    }
            return {'port': port_name}
        except Exception as e:
            self.logger.warning(f"Не удалось получить информацию о порте {port_name}: {e}")
            return {'port': port_name}
    
    @contextmanager
    def temporary_connection(self, port: str, **kwargs):
        """
        Контекстный менеджер для временного соединения.
        
        Args:
            port: Имя порта
            **kwargs: Настройки соединения
        """
        try:
            if self.connect(port, **kwargs):
                yield self
            else:
                yield None
        finally:
            self.disconnect()
    
    def cleanup(self):
        """Очистка ресурсов соединения"""
        with self._lock:
            try:
                if self.port and self.port.is_open:
                    self.port.close()
                self.port = None
                self._connection_state = {
                    'connected': False,
                    'connecting': False,
                    'disconnecting': False,
                    'last_operation': None,
                    'operation_timestamp': 0,
                    'port_info': None,
                    'connection_attempts': 0,
                    'last_error': None
                }
                self.logger.debug("Ресурсы соединения очищены")
            except Exception as e:
                self.logger.error(f"Ошибка очистки ресурсов соединения: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
