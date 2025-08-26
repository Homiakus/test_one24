"""
Менеджер последовательного соединения
"""
import logging
import threading
import time
import signal
from typing import Optional, Callable, List, Dict, Any, Union
from contextlib import contextmanager

import serial
import serial.tools.list_ports
from PyQt6.QtCore import QThread, pyqtSignal as Signal


class InterruptibleThread(threading.Thread):
    """
    Поток с поддержкой прерывания и graceful shutdown.
    
    Расширяет стандартный threading.Thread для безопасного прерывания
    и корректного завершения работы.
    
    Attributes:
        _stop_event: Событие для сигнализации остановки
        _timeout: Таймаут для graceful shutdown
        _start_time: Время запуска потока
        _interrupted: Флаг прерывания
        logger: Логгер для записи событий
    """
    
    def __init__(self, target: Callable[..., Any], name: Optional[str] = None, 
                 timeout: float = 5.0, **kwargs: Any) -> None:
        """
        Инициализация прерываемого потока.
        
        Args:
            target: Функция для выполнения в потоке
            name: Имя потока
            timeout: Таймаут для graceful shutdown в секундах
            **kwargs: Дополнительные аргументы для базового класса
        """
        super().__init__(target=target, name=name, **kwargs)
        self.daemon = False  # Не используем daemon threads
        self._stop_event = threading.Event()
        self._timeout = timeout
        self._start_time: Optional[float] = None
        self._interrupted = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def start(self) -> None:
        """
        Запуск потока с отслеживанием времени.
        
        Устанавливает время запуска и сбрасывает флаг прерывания.
        """
        self._start_time = time.time()
        self._interrupted = False
        super().start()
        self.logger.debug(f"Поток {self.name} запущен")
    
    def stop(self, timeout: Optional[float] = None) -> bool:
        """
        Graceful остановка потока.
        
        Пытается корректно остановить поток, устанавливая флаг остановки
        и ожидая завершения с таймаутом.
        
        Args:
            timeout: Таймаут для остановки в секундах (по умолчанию использует self._timeout)
            
        Returns:
            True если поток остановлен успешно, False при таймауте
        """
        if not self.is_alive():
            return True
        
        timeout = timeout or self._timeout
        self.logger.debug(f"Запрос остановки потока {self.name} (таймаут: {timeout}s)")
        
        # Устанавливаем флаг остановки
        self._stop_event.set()
        self._interrupted = True
        
        # Ждем завершения с таймаутом
        self.join(timeout=timeout)
        
        if self.is_alive():
            self.logger.warning(f"Таймаут остановки потока {self.name}")
            return False
        else:
            self.logger.debug(f"Поток {self.name} успешно остановлен")
            return True
    
    def interrupt(self) -> None:
        """
        Прерывание потока.
        
        Устанавливает флаг прерывания и событие остановки.
        """
        self._interrupted = True
        self._stop_event.set()
        self.logger.debug(f"Поток {self.name} прерван")
    
    def is_interrupted(self) -> bool:
        """
        Проверка прерывания потока.
        
        Returns:
            True если поток прерван или остановлен, False в противном случае
        """
        return self._interrupted or self._stop_event.is_set()
    
    def get_runtime(self) -> float:
        """
        Получение времени выполнения потока.
        
        Returns:
            Время выполнения в секундах с момента запуска
        """
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time


class SerialReader(QThread):
    """Поток для чтения данных с Serial-порта"""

    data_received = Signal(str)
    error_occurred = Signal(str)
    signal_processed = Signal(str, str, str)  # signal_name, variable_name, value

    def __init__(self, serial_port: serial.Serial, signal_manager=None):
        super().__init__()
        self.serial_port = serial_port
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
               self.serial_port.is_open and 
               not self._stop_event.is_set() and 
               not self._interrupt_event.is_set()):
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.readline().decode('utf-8',
                                                              errors='ignore').strip()
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
            except serial.SerialException as e:
                self.error_occurred.emit(f"Ошибка чтения: {e}")
                self.logger.error(f"Ошибка чтения Serial: {e}")
                break
            except Exception as e:
                self.error_occurred.emit(f"Неожиданная ошибка: {e}")
                self.logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
                break

            # Используем более короткий sleep для быстрого отклика на остановку
            for _ in range(10):  # 10 * 5ms = 50ms
                if self._stop_event.is_set() or self._interrupt_event.is_set():
                    break
                self.msleep(5)
        
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


class ThreadManager:
    """Менеджер для управления потоками с proper shutdown"""
    
    def __init__(self):
        self._threads: Dict[str, InterruptibleThread] = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def start_thread(self, name: str, target: Callable, timeout: float = 5.0, **kwargs) -> InterruptibleThread:
        """
        Запуск потока с именем
        
        Args:
            name: Имя потока
            target: Целевая функция
            timeout: Таймаут для остановки
            **kwargs: Дополнительные аргументы для потока
            
        Returns:
            Созданный поток
        """
        with self._lock:
            # Останавливаем существующий поток с таким именем
            if name in self._threads:
                self.stop_thread(name)
            
            # Создаем новый поток
            thread = InterruptibleThread(target=target, name=name, timeout=timeout, **kwargs)
            self._threads[name] = thread
            thread.start()
            
            self.logger.debug(f"Запущен поток: {name}")
            return thread
    
    def stop_thread(self, name: str, timeout: float = None) -> bool:
        """
        Остановка потока по имени
        
        Args:
            name: Имя потока
            timeout: Таймаут для остановки
            
        Returns:
            True если поток остановлен успешно
        """
        with self._lock:
            if name not in self._threads:
                return True
            
            thread = self._threads[name]
            success = thread.stop(timeout=timeout)
            
            if success:
                del self._threads[name]
                self.logger.debug(f"Поток {name} остановлен и удален")
            else:
                self.logger.warning(f"Не удалось остановить поток {name}")
            
            return success
    
    def interrupt_thread(self, name: str):
        """Прерывание потока по имени"""
        with self._lock:
            if name in self._threads:
                self._threads[name].interrupt()
                self.logger.debug(f"Поток {name} прерван")
    
    def stop_all_threads(self, timeout: float = 10.0) -> Dict[str, bool]:
        """
        Остановка всех потоков
        
        Args:
            timeout: Общий таймаут для всех потоков
            
        Returns:
            Словарь результатов остановки потоков
        """
        results = {}
        start_time = time.time()
        
        with self._lock:
            thread_names = list(self._threads.keys())
        
        for name in thread_names:
            remaining_time = max(0, timeout - (time.time() - start_time))
            if remaining_time <= 0:
                self.logger.warning(f"Таймаут остановки всех потоков ({timeout}s)")
                break
            
            results[name] = self.stop_thread(name, timeout=remaining_time)
        
        self.logger.info(f"Остановка всех потоков завершена: {results}")
        return results
    
    def get_thread_info(self) -> Dict[str, Dict]:
        """Получение информации о всех потоках"""
        with self._lock:
            info = {}
            for name, thread in self._threads.items():
                info[name] = {
                    'alive': thread.is_alive(),
                    'interrupted': thread.is_interrupted(),
                    'runtime': thread.get_runtime(),
                    'timeout': thread._timeout
                }
            return info
    
    def cleanup(self):
        """Очистка завершенных потоков"""
        with self._lock:
            finished_threads = []
            for name, thread in self._threads.items():
                if not thread.is_alive():
                    finished_threads.append(name)
            
            for name in finished_threads:
                del self._threads[name]
                self.logger.debug(f"Удален завершенный поток: {name}")


class SerialManager:
    """Менеджер Serial-соединения с улучшенным управлением потоками и поддержкой обработки сигналов"""

    def __init__(self, signal_manager=None):
        self.port: Optional[serial.Serial] = None
        self.reader_thread: Optional[SerialReader] = None
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()  # Используем RLock для предотвращения deadlock
        self._connection_lock = threading.Lock()  # Отдельная блокировка для операций подключения
        self._port_operation_lock = threading.Lock()  # Блокировка для операций с портом
        self._state_lock = threading.Lock()  # Блокировка для изменения состояния
        self._thread_manager = ThreadManager()  # Менеджер потоков
        self._connection_state = {
            'connected': False,
            'connecting': False,
            'disconnecting': False,
            'last_operation': None,
            'operation_timestamp': 0
        }
        
        # Менеджер сигналов для обработки входящих данных UART
        self.signal_manager = signal_manager
        
        # Настройка обработчика сигналов для graceful shutdown
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Настройка обработчиков сигналов для graceful shutdown"""
        try:
            def signal_handler(signum, frame):
                self.logger.info(f"Получен сигнал {signum}, выполняется graceful shutdown")
                self.graceful_shutdown()
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except Exception as e:
            self.logger.warning(f"Не удалось настроить обработчики сигналов: {e}")

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

    def graceful_shutdown(self, timeout: float = 10.0):
        """
        Graceful shutdown всех компонентов
        
        Args:
            timeout: Общий таймаут для shutdown
        """
        self.logger.info("Начало graceful shutdown")
        
        # Останавливаем все потоки
        thread_results = self._thread_manager.stop_all_threads(timeout=timeout/2)
        
        # Отключаемся от порта
        self.disconnect()
        
        # Очищаем завершенные потоки
        self._thread_manager.cleanup()
        
        self.logger.info(f"Graceful shutdown завершен. Результаты потоков: {thread_results}")

    def _update_connection_state(self, **kwargs):
        """Атомарное обновление состояния подключения"""
        with self._state_lock:
            self._connection_state.update(kwargs)
            self._connection_state['last_operation'] = kwargs.get('connected', self._connection_state['connected'])
            self._connection_state['operation_timestamp'] = time.time()

    def _get_connection_state(self):
        """Атомарное получение состояния подключения"""
        with self._state_lock:
            return self._connection_state.copy()

    @property
    def is_connected(self) -> bool:
        """Проверка состояния подключения с атомарной проверкой"""
        with self._lock:
            # Проверяем состояние подключения
            state = self._get_connection_state()
            if not state['connected']:
                return False
            
            # Дополнительная проверка физического состояния порта
            if self.port is None:
                self._update_connection_state(connected=False)
                return False
            
            try:
                # Атомарная проверка состояния порта
                with self._port_operation_lock:
                    if not hasattr(self.port, 'is_open') or not self.port.is_open:
                        self._update_connection_state(connected=False)
                        return False
                    return True
            except Exception as e:
                self.logger.error(f"Ошибка проверки состояния порта: {e}")
                self._update_connection_state(connected=False)
                return False

    @staticmethod
    def get_available_ports() -> List[str]:
        """Получение списка доступных портов с полной обработкой ошибок"""
        try:
            import threading
            import time
            
            ports = []
            error_occurred = False
            
            def get_ports():
                nonlocal ports, error_occurred
                try:
                    # Пробуем получить порты с дополнительными проверками
                    available_ports = serial.tools.list_ports.comports()
                    if available_ports:
                        ports = [port.device for port in available_ports]
                        logging.getLogger(__name__).info(f"Найдено портов: {len(ports)}")
                    else:
                        logging.getLogger(__name__).warning("Не найдено доступных портов")
                        ports = []
                except serial.SerialException as e:
                    logging.getLogger(__name__).error(f"SerialException при получении портов: {e}")
                    error_occurred = True
                    ports = []
                except Exception as e:
                    logging.getLogger(__name__).error(f"Общая ошибка получения портов: {e}")
                    error_occurred = True
                    ports = []
            
            # Запускаем в отдельном потоке с таймаутом
            thread = threading.Thread(target=get_ports)
            thread.daemon = False  # Не используем daemon threads
            thread.start()
            thread.join(timeout=3.0)  # Уменьшаем таймаут до 3 секунд
            
            if thread.is_alive():
                logging.getLogger(__name__).warning("Таймаут получения списка портов")
                return []
            
            if error_occurred:
                logging.getLogger(__name__).error("Произошла ошибка при получении портов")
                return []
                
            return ports
        except Exception as e:
            logging.getLogger(__name__).error(f"Критическая ошибка получения портов: {e}")
            return []

    def connect(self, port: str, baudrate: int = 115200,
                timeout: float = 1.0, **kwargs) -> bool:
        """
        Подключение к Serial-порту с полной обработкой ошибок

        Args:
            port: Имя порта
            baudrate: Скорость
            timeout: Таймаут
            **kwargs: Дополнительные параметры

        Returns:
            True при успешном подключении
        """
        with self._connection_lock:  # Используем отдельную блокировку для подключения
            try:
                # Проверяем текущее состояние
                state = self._get_connection_state()
                if state['connected']:
                    self.logger.warning("Уже подключено к порту")
                    return True
                
                if state['connecting']:
                    self.logger.warning("Подключение уже выполняется")
                    return False
                
                if state['disconnecting']:
                    self.logger.warning("Выполняется отключение, подождите")
                    return False
                
                self.logger.info(f"Начало подключения к порту {port}")
                self._update_connection_state(connecting=True)
                
                # Закрываем предыдущее соединение
                self.logger.info("Закрытие предыдущего соединения...")
                self._disconnect_internal()

                # Проверяем доступность порта с таймаутом
                self.logger.info("Проверка доступности порта...")
                available_ports = self.get_available_ports()
                if not available_ports:
                    self.logger.error("Не удалось получить список доступных портов")
                    self._update_connection_state(connecting=False)
                    return False
                
                if port not in available_ports:
                    self.logger.error(f"Порт {port} не найден в списке доступных: {available_ports}")
                    self._update_connection_state(connecting=False)
                    return False
                
                # Дополнительная проверка порта перед подключением
                self.logger.info(f"Дополнительная проверка порта {port}...")
                try:
                    # Пробуем открыть порт для проверки доступности
                    test_port = serial.Serial(port=port, timeout=0.1)
                    test_port.close()
                    self.logger.info(f"Порт {port} доступен для подключения")
                except Exception as e:
                    self.logger.error(f"Порт {port} недоступен для подключения: {e}")
                    self._update_connection_state(connecting=False)
                    return False

                # Создаем соединение с таймаутом
                self.logger.info("Создание Serial объекта...")
                try:
                    # Пробуем создать соединение с ограниченным таймаутом
                    connection_result = {'success': False, 'error': None, 'port_obj': None}
                    
                    def create_connection():
                        try:
                            # Добавляем дополнительные параметры для предотвращения зависания
                            port_obj = serial.Serial(
                                port=port,
                                baudrate=baudrate,
                                timeout=timeout,
                                write_timeout=2,
                                xonxoff=False,
                                rtscts=False,
                                dsrdtr=False,
                                exclusive=True,  # Эксклюзивный доступ к порту
                                **kwargs
                            )
                            connection_result['success'] = True
                            connection_result['port_obj'] = port_obj
                        except Exception as e:
                            connection_result['error'] = e
                    
                    # Запускаем создание соединения через ThreadManager с более коротким таймаутом
                    conn_thread = self._thread_manager.start_thread(
                        name="connection_creator",
                        target=create_connection,
                        timeout=5.0  # Уменьшаем таймаут до 5 секунд
                    )
                    
                    # Ждем завершения с таймаутом
                    if not conn_thread.stop(timeout=5.0):  # Уменьшаем таймаут до 5 секунд
                        self.logger.error("Таймаут создания Serial соединения (5s)")
                        self._update_connection_state(connecting=False)
                        return False
                    
                    if not connection_result['success']:
                        error_msg = str(connection_result['error'])
                        self.logger.error(f"Ошибка создания Serial объекта: {error_msg}")
                        
                        # Добавляем специфичную обработку ошибок Windows
                        if "Неверная функция" in error_msg or "OSError(22" in error_msg:
                            self.logger.error("Ошибка конфигурации порта - возможно порт занят или недоступен")
                        elif "PermissionError" in error_msg or "Access denied" in error_msg:
                            self.logger.error("Нет прав доступа к порту - возможно порт используется другим приложением")
                        elif "FileNotFoundError" in error_msg or "Port not found" in error_msg:
                            self.logger.error("Порт не найден - проверьте подключение устройства")
                        
                        self._update_connection_state(connecting=False)
                        return False
                    
                    # Атомарно устанавливаем порт
                    with self._lock:
                        with self._port_operation_lock:
                            self.port = connection_result['port_obj']
                    self.logger.info("Serial объект создан успешно")
                    
                except Exception as e:
                    self.logger.error(f"Критическая ошибка создания Serial объекта: {e}")
                    self._update_connection_state(connecting=False)
                    return False

                # Запускаем поток чтения с поддержкой обработки сигналов
                self.logger.info("Запуск потока чтения...")
                try:
                    with self._lock:
                        self.reader_thread = SerialReader(self.port, self.signal_manager)
                        self.reader_thread.start()
                    self.logger.info("Поток чтения запущен")
                except Exception as e:
                    self.logger.error(f"Ошибка запуска потока чтения: {e}")
                    self._disconnect_internal()
                    self._update_connection_state(connecting=False)
                    return False

                # Обновляем состояние подключения
                self._update_connection_state(connected=True, connecting=False)
                self.logger.info(f"Успешно подключено к порту {port}")
                return True

            except Exception as e:
                self.logger.error(f"Общая ошибка подключения: {e}")
                self._disconnect_internal()
                self._update_connection_state(connecting=False)
                return False

    def _disconnect_internal(self):
        """Внутренний метод отключения без блокировки _connection_lock"""
        try:
            self.logger.info("Начало внутреннего отключения от порта...")
            self._update_connection_state(disconnecting=True)
            
            # Сначала останавливаем поток чтения
            reader_thread = None
            with self._lock:
                reader_thread = self.reader_thread
                self.reader_thread = None
            
            if reader_thread:
                if hasattr(reader_thread, 'isRunning') and reader_thread.isRunning():
                    self.logger.info("Остановка потока чтения...")
                    try:
                        # Останавливаем поток через ThreadManager
                        def stop_reader():
                            try:
                                reader_thread.stop()
                            except Exception as e:
                                self.logger.error(f"Ошибка остановки потока: {e}")
                        
                        stop_thread = self._thread_manager.start_thread(
                            name="reader_stopper",
                            target=stop_reader,
                            timeout=2.0
                        )
                        
                        if not stop_thread.stop(timeout=2.0):
                            self.logger.warning("Таймаут остановки потока чтения")
                        else:
                            self.logger.info("Поток чтения остановлен")
                    except Exception as e:
                        self.logger.error(f"Ошибка остановки потока: {e}")
                else:
                    self.logger.info("Поток чтения уже остановлен")
            else:
                self.logger.info("Поток чтения не существует")

            # Затем закрываем порт
            port_obj = None
            with self._lock:
                with self._port_operation_lock:
                    port_obj = self.port
                    self.port = None
            
            if port_obj:
                if hasattr(port_obj, 'is_open') and port_obj.is_open:
                    self.logger.info("Закрытие порта...")
                    try:
                        # Закрываем порт через ThreadManager
                        def close_port():
                            try:
                                with self._port_operation_lock:
                                    port_obj.close()
                            except Exception as e:
                                self.logger.error(f"Ошибка закрытия порта: {e}")
                        
                        close_thread = self._thread_manager.start_thread(
                            name="port_closer",
                            target=close_port,
                            timeout=1.0
                        )
                        
                        if not close_thread.stop(timeout=1.0):
                            self.logger.warning("Таймаут закрытия порта")
                        else:
                            self.logger.info("Порт закрыт")
                    except Exception as e:
                        self.logger.error(f"Ошибка закрытия порта: {e}")
                else:
                    self.logger.info("Порт уже закрыт")
            else:
                self.logger.info("Порт не существует")

            # Обновляем состояние
            self._update_connection_state(connected=False, disconnecting=False)
            self.logger.info("Внутреннее отключение от порта завершено")

        except Exception as e:
            self.logger.error(f"Ошибка при внутреннем отключении: {e}")
            # Сбрасываем состояние в любом случае
            with self._lock:
                self.reader_thread = None
                with self._port_operation_lock:
                    self.port = None
            self._update_connection_state(connected=False, disconnecting=False)

    def disconnect(self):
        """Отключение от порта с защитой от deadlock"""
        with self._connection_lock:
            self._disconnect_internal()

    def send_command(self, command: str) -> bool:
        """
        Отправка команды с таймаутом и атомарными операциями

        Args:
            command: Команда для отправки

        Returns:
            True при успешной отправке
        """
        # Проверяем состояние подключения
        if not self.is_connected:
            self.logger.warning("Попытка отправки команды без подключения")
            return False
        
        # Проверяем, не выполняется ли отключение
        state = self._get_connection_state()
        if state['disconnecting']:
            self.logger.warning("Попытка отправки команды во время отключения")
            return False

        try:
            full_command = command.strip() + '\n'
            
            # Простая отправка с таймаутом через threading
            send_result = {'success': False, 'error': None}
            
            def send_with_timeout():
                try:
                    with self._port_operation_lock:
                        # Дополнительная проверка состояния порта перед отправкой
                        if self.port is None or not hasattr(self.port, 'is_open') or not self.port.is_open:
                            self.logger.error("Порт недоступен для отправки команды")
                            send_result['success'] = False
                            send_result['error'] = "Порт недоступен"
                            return
                        
                        # Устанавливаем таймаут для записи
                        original_timeout = self.port.write_timeout
                        self.port.write_timeout = 2.0
                        
                        try:
                            self.port.write(full_command.encode('utf-8'))
                            send_result['success'] = True
                        finally:
                            # Восстанавливаем оригинальный таймаут
                            self.port.write_timeout = original_timeout
                            
                except Exception as e:
                    self.logger.error(f"Ошибка отправки команды: {e}")
                    send_result['success'] = False
                    send_result['error'] = str(e)
            
            # Запускаем отправку в отдельном потоке
            import threading
            send_thread = threading.Thread(target=send_with_timeout, daemon=True)
            send_thread.start()
            
            # Ждем завершения с таймаутом
            send_thread.join(timeout=3.0)  # Увеличиваем таймаут до 3 секунд
            
            if send_thread.is_alive():
                self.logger.error("Таймаут отправки команды")
                return False
            
            # Проверяем результат отправки
            if not send_result['success']:
                self.logger.error(f"Ошибка отправки команды: {send_result['error']}")
                return False
            
            self.logger.debug(f"Отправлено: {command}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка отправки команды: {e}")
            return False

    def get_port_info(self) -> dict:
        """
        Получение информации о порте с атомарными операциями
        
        Returns:
            Словарь с информацией о порте
        """
        with self._lock:
            with self._port_operation_lock:
                if self.port is None:
                    return {'connected': False, 'port': None, 'info': 'Порт не установлен'}
                
                try:
                    info = {
                        'connected': self.is_connected,
                        'port': str(self.port.port) if hasattr(self.port, 'port') else 'Unknown',
                        'baudrate': self.port.baudrate if hasattr(self.port, 'baudrate') else 'Unknown',
                        'is_open': self.port.is_open if hasattr(self.port, 'is_open') else False,
                        'timeout': self.port.timeout if hasattr(self.port, 'timeout') else 'Unknown',
                        'write_timeout': self.port.write_timeout if hasattr(self.port, 'write_timeout') else 'Unknown'
                    }
                    return info
                except Exception as e:
                    self.logger.error(f"Ошибка получения информации о порте: {e}")
                    return {'connected': False, 'port': None, 'info': f'Ошибка: {e}'}

    def is_port_available(self) -> bool:
        """
        Проверка доступности порта с атомарными операциями
        
        Returns:
            True если порт доступен
        """
        with self._lock:
            with self._port_operation_lock:
                if self.port is None:
                    return False
                
                try:
                    return hasattr(self.port, 'is_open') and self.port.is_open
                except Exception as e:
                    self.logger.error(f"Ошибка проверки доступности порта: {e}")
                    return False

    def get_thread_info(self) -> Dict[str, Dict]:
        """
        Получение информации о всех потоках
        
        Returns:
            Словарь с информацией о потоках
        """
        return self._thread_manager.get_thread_info()

    def interrupt_all_threads(self):
        """Прерывание всех потоков"""
        thread_info = self.get_thread_info()
        for thread_name in thread_info.keys():
            self._thread_manager.interrupt_thread(thread_name)
        self.logger.info("Все потоки прерваны")

    def get_signal_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики обработки сигналов
        
        Returns:
            Словарь со статистикой сигналов
        """
        if not self.signal_manager:
            return {'error': 'SignalManager не установлен'}
        
        try:
            return self.signal_manager.get_statistics()
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики сигналов: {e}")
            return {'error': str(e)}

    def process_signal_data(self, data: str) -> bool:
        """
        Обработка данных как сигнал UART
        
        Args:
            data: Входящие данные для обработки
            
        Returns:
            True если данные обработаны как сигнал
        """
        if not self.signal_manager:
            return False
        
        try:
            result = self.signal_manager.process_incoming_data(data)
            return result and result.is_success
        except Exception as e:
            self.logger.error(f"Ошибка обработки сигнала '{data}': {e}")
            return False

    @contextmanager
    def connection(self, *args, **kwargs):
        """Контекстный менеджер для автоматического управления соединением"""
        try:
            self.connect(*args, **kwargs)
            yield self
        finally:
            self.disconnect()

    def __del__(self):
        """Деструктор - гарантирует закрытие порта и остановку потоков"""
        try:
            self.graceful_shutdown(timeout=5.0)
        except:
            pass  # Игнорируем ошибки в деструкторе
