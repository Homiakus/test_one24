"""
Модуль для управления потоками связи.

Содержит классы InterruptibleThread и ThreadManager для безопасного
управления потоками с поддержкой graceful shutdown и мониторинга.
"""

import logging
import threading
import time
import signal
from typing import Optional, Callable, Dict, Any, List
from contextlib import contextmanager


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
    
    def should_stop(self) -> bool:
        """
        Проверка, должен ли поток остановиться.
        
        Returns:
            True если поток должен остановиться
        """
        return self._stop_event.is_set()
    
    def wait_for_stop(self, check_interval: float = 0.1) -> None:
        """
        Ожидание сигнала остановки.
        
        Args:
            check_interval: Интервал проверки сигнала остановки в секундах
        """
        while not self.should_stop():
            time.sleep(check_interval)


class ThreadManager:
    """Менеджер для управления потоками с proper shutdown"""
    
    def __init__(self):
        self._threads: Dict[str, InterruptibleThread] = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
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
                    'timeout': thread._timeout,
                    'daemon': thread.daemon,
                    'ident': thread.ident
                }
            return info
    
    def get_thread_count(self) -> int:
        """Получение количества активных потоков"""
        with self._lock:
            return len(self._threads)
    
    def is_thread_running(self, name: str) -> bool:
        """Проверка, запущен ли поток с указанным именем"""
        with self._lock:
            if name not in self._threads:
                return False
            return self._threads[name].is_alive()
    
    def wait_for_thread(self, name: str, timeout: float = None) -> bool:
        """
        Ожидание завершения потока
        
        Args:
            name: Имя потока
            timeout: Таймаут ожидания
            
        Returns:
            True если поток завершился, False при таймауте
        """
        with self._lock:
            if name not in self._threads:
                return True
            
            thread = self._threads[name]
        
        try:
            thread.join(timeout=timeout)
            return not thread.is_alive()
        except Exception as e:
            self.logger.error(f"Ошибка ожидания потока {name}: {e}")
            return False
    
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
    
    def graceful_shutdown(self, timeout: float = 10.0):
        """
        Graceful shutdown всех потоков
        
        Args:
            timeout: Общий таймаут для shutdown
        """
        self.logger.info("Начало graceful shutdown")
        
        # Останавливаем все потоки
        results = self.stop_all_threads(timeout=timeout)
        
        # Очищаем завершенные потоки
        self.cleanup()
        
        self.logger.info(f"Graceful shutdown завершен. Результаты: {results}")
    
    def get_thread_stats(self) -> Dict[str, Any]:
        """Получение статистики потоков"""
        with self._lock:
            total_threads = len(self._threads)
            running_threads = sum(1 for t in self._threads.values() if t.is_alive())
            interrupted_threads = sum(1 for t in self._threads.values() if t.is_interrupted())
            
            total_runtime = sum(t.get_runtime() for t in self._threads.values())
            avg_runtime = total_runtime / total_threads if total_threads > 0 else 0
            
            return {
                'total_threads': total_threads,
                'running_threads': running_threads,
                'interrupted_threads': interrupted_threads,
                'stopped_threads': total_threads - running_threads,
                'total_runtime': total_runtime,
                'average_runtime': avg_runtime
            }
    
    def reset_stats(self):
        """Сброс статистики потоков"""
        # Для потоков статистика сбрасывается автоматически при остановке
        self.logger.debug("Статистика потоков сброшена")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.graceful_shutdown()
