"""
Модуль для асинхронного выполнения последовательностей.

Содержит класс SequenceWorker для выполнения последовательностей
в отдельном потоке с поддержкой отмены и мониторинга.
"""

import logging
import threading
import time
from typing import List, Dict, Any, Optional, Callable
from .types import CommandType, ValidationResult
from .cancellation import CancellationToken, CancellationException
from .flags import FlagManager


class SequenceWorker:
    """Асинхронный исполнитель последовательностей команд"""
    
    def __init__(self, 
                 serial_manager,
                 flag_manager: FlagManager,
                 cancellation_token: Optional[CancellationToken] = None):
        self.serial_manager = serial_manager
        self.flag_manager = flag_manager
        self.cancellation_token = cancellation_token or CancellationToken()
        self.logger = logging.getLogger(__name__)
        
        # Состояние выполнения
        self._is_running = False
        self._is_paused = False
        self._current_command_index = 0
        self._total_commands = 0
        self._execution_thread: Optional[threading.Thread] = None
        
        # Callbacks для событий
        self.on_command_executed: Optional[Callable[[str, bool], None]] = None
        self.on_progress_updated: Optional[Callable[[int, int], None]] = None
        self.on_sequence_finished: Optional[Callable[[bool, str], None]] = None
        self.on_worker_started: Optional[Callable[[], None]] = None
        self.on_worker_stopped: Optional[Callable[[], None]] = None
        self.on_worker_paused: Optional[Callable[[], None]] = None
        self.on_worker_resumed: Optional[Callable[[], None]] = None
        
        # Результаты выполнения
        self._execution_results: List[Dict[str, Any]] = []
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
    
    def start_execution(self, commands: List[str]) -> bool:
        """
        Начать асинхронное выполнение последовательности.
        
        Args:
            commands: Список команд для выполнения
            
        Returns:
            True если выполнение запущено успешно
        """
        if self._is_running:
            self.logger.warning("Выполнение уже запущено")
            return False
        
        if not commands:
            self.logger.warning("Пустая последовательность команд")
            return False
        
        if not self.serial_manager.is_connected:
            error_msg = "Устройство не подключено"
            self.logger.error(error_msg)
            self._notify_sequence_finished(False, error_msg)
            return False
        
        # Инициализируем состояние
        self._is_running = True
        self._is_paused = False
        self._current_command_index = 0
        self._total_commands = len(commands)
        self._execution_results = []
        self._start_time = time.time()
        self._end_time = None
        
        # Создаем и запускаем поток выполнения
        self._execution_thread = threading.Thread(
            target=self._execute_sequence_worker,
            args=(commands,),
            daemon=True
        )
        self._execution_thread.start()
        
        self.logger.info(f"Запущено асинхронное выполнение {len(commands)} команд")
        self._notify_worker_started()
        
        return True
    
    def stop_execution(self) -> bool:
        """
        Остановить выполнение последовательности.
        
        Returns:
            True если выполнение остановлено успешно
        """
        if not self._is_running:
            self.logger.warning("Выполнение не запущено")
            return False
        
        self.logger.info("Остановка выполнения последовательности")
        
        # Отменяем выполнение
        if self.cancellation_token:
            self.cancellation_token.cancel()
        
        # Ждем завершения потока
        if self._execution_thread and self._execution_thread.is_alive():
            self._execution_thread.join(timeout=5.0)
        
        self._is_running = False
        self._end_time = time.time()
        
        self._notify_worker_stopped()
        return True
    
    def pause_execution(self) -> bool:
        """
        Приостановить выполнение последовательности.
        
        Returns:
            True если выполнение приостановлено успешно
        """
        if not self._is_running:
            self.logger.warning("Выполнение не запущено")
            return False
        
        if self._is_paused:
            self.logger.warning("Выполнение уже приостановлено")
            return False
        
        self._is_paused = True
        self.logger.info("Выполнение последовательности приостановлено")
        self._notify_worker_paused()
        
        return True
    
    def resume_execution(self) -> bool:
        """
        Возобновить выполнение последовательности.
        
        Returns:
            True если выполнение возобновлено успешно
        """
        if not self._is_running:
            self.logger.warning("Выполнение не запущено")
            return False
        
        if not self._is_paused:
            self.logger.warning("Выполнение не приостановлено")
            return False
        
        self._is_paused = False
        self.logger.info("Выполнение последовательности возобновлено")
        self._notify_worker_resumed()
        
        return True
    
    def _execute_sequence_worker(self, commands: List[str]):
        """Основной метод выполнения в отдельном потоке"""
        try:
            self.logger.debug("Начало выполнения в рабочем потоке")
            
            for i, command in enumerate(commands):
                # Проверяем отмену
                self.cancellation_token.throw_if_cancelled()
                
                # Ждем возобновления если приостановлено
                while self._is_paused and not self.cancellation_token.is_cancelled():
                    time.sleep(0.1)
                
                # Проверяем отмену после паузы
                self.cancellation_token.throw_if_cancelled()
                
                # Обновляем прогресс
                self._current_command_index = i + 1
                self._notify_progress_updated(self._current_command_index, self._total_commands)
                
                self.logger.debug(f"Выполняю команду {self._current_command_index}/{self._total_commands}: {command}")
                
                # Выполняем команду
                command_result = self._execute_single_command(command)
                self._execution_results.append(command_result)
                
                # Уведомляем о выполнении команды
                self._notify_command_executed(command, command_result['success'])
                
                # Проверяем успешность выполнения
                if not command_result['success'] and command_result.get('critical', False):
                    error_msg = f"Критическая ошибка в команде {self._current_command_index}: {command_result['message']}"
                    self.logger.error(error_msg)
                    self._notify_sequence_finished(False, error_msg)
                    return
            
            # Последовательность выполнена успешно
            success_msg = f"Последовательность выполнена успешно: {len(commands)} команд"
            self.logger.info(success_msg)
            self._notify_sequence_finished(True, success_msg)
            
        except CancellationException:
            cancel_msg = "Выполнение последовательности отменено"
            self.logger.info(cancel_msg)
            self._notify_sequence_finished(False, cancel_msg)
        except Exception as e:
            error_msg = f"Ошибка выполнения последовательности: {e}"
            self.logger.error(error_msg)
            self._notify_sequence_finished(False, error_msg)
        finally:
            self._is_running = False
            self._end_time = time.time()
            self.logger.debug("Рабочий поток завершен")
    
    def _execute_single_command(self, command: str) -> Dict[str, Any]:
        """Выполнить одну команду"""
        try:
            start_time = time.time()
            
            # Отправляем команду
            if not self.serial_manager.send_command(command):
                return {
                    'command': command,
                    'success': False,
                    'message': 'Не удалось отправить команду',
                    'execution_time': 0.0,
                    'critical': True
                }
            
            # Ждем ответа (здесь должна быть логика ожидания)
            # Пока просто возвращаем успешный результат
            execution_time = time.time() - start_time
            
            return {
                'command': command,
                'success': True,
                'message': 'Команда выполнена успешно',
                'execution_time': execution_time,
                'critical': False
            }
            
        except Exception as e:
            return {
                'command': command,
                'success': False,
                'message': f'Ошибка выполнения: {e}',
                'execution_time': 0.0,
                'critical': True
            }
    
    def is_running(self) -> bool:
        """Проверить, запущено ли выполнение"""
        return self._is_running
    
    def is_paused(self) -> bool:
        """Проверить, приостановлено ли выполнение"""
        return self._is_paused
    
    def get_progress(self) -> tuple[int, int]:
        """Получить текущий прогресс выполнения"""
        return self._current_command_index, self._total_commands
    
    def get_execution_time(self) -> float:
        """Получить время выполнения"""
        if not self._start_time:
            return 0.0
        
        end_time = self._end_time or time.time()
        return end_time - self._start_time
    
    def get_execution_results(self) -> List[Dict[str, Any]]:
        """Получить результаты выполнения"""
        return self._execution_results.copy()
    
    def get_success_rate(self) -> float:
        """Получить процент успешных команд"""
        if not self._execution_results:
            return 0.0
        
        successful = sum(1 for result in self._execution_results if result['success'])
        return (successful / len(self._execution_results)) * 100.0
    
    def set_callbacks(self, 
                     on_command_executed: Optional[Callable[[str, bool], None]] = None,
                     on_progress_updated: Optional[Callable[[int, int], None]] = None,
                     on_sequence_finished: Optional[Callable[[bool, str], None]] = None,
                     on_worker_started: Optional[Callable[[], None]] = None,
                     on_worker_stopped: Optional[Callable[[], None]] = None,
                     on_worker_paused: Optional[Callable[[], None]] = None,
                     on_worker_resumed: Optional[Callable[[], None]] = None):
        """Установить callbacks для событий"""
        self.on_command_executed = on_command_executed
        self.on_progress_updated = on_progress_updated
        self.on_sequence_finished = on_sequence_finished
        self.on_worker_started = on_worker_started
        self.on_worker_stopped = on_worker_stopped
        self.on_worker_paused = on_worker_paused
        self.on_worker_resumed = on_worker_resumed
    
    def _notify_command_executed(self, command: str, success: bool):
        """Уведомить о выполнении команды"""
        if self.on_command_executed:
            try:
                self.on_command_executed(command, success)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_command_executed: {e}")
    
    def _notify_progress_updated(self, current: int, total: int):
        """Уведомить об обновлении прогресса"""
        if self.on_progress_updated:
            try:
                self.on_progress_updated(current, total)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_progress_updated: {e}")
    
    def _notify_sequence_finished(self, success: bool, message: str):
        """Уведомить о завершении последовательности"""
        if self.on_sequence_finished:
            try:
                self.on_sequence_finished(success, message)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_sequence_finished: {e}")
    
    def _notify_worker_started(self):
        """Уведомить о запуске воркера"""
        if self.on_worker_started:
            try:
                self.on_worker_started()
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_worker_started: {e}")
    
    def _notify_worker_stopped(self):
        """Уведомить об остановке воркера"""
        if self.on_worker_stopped:
            try:
                self.on_worker_stopped()
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_worker_stopped: {e}")
    
    def _notify_worker_paused(self):
        """Уведомить о приостановке воркера"""
        if self.on_worker_paused:
            try:
                self.on_worker_paused()
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_worker_paused: {e}")
    
    def _notify_worker_resumed(self):
        """Уведомить о возобновлении воркера"""
        if self.on_worker_resumed:
            try:
                self.on_worker_resumed()
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_worker_resumed: {e}")
    
    def reset_state(self):
        """Сбросить состояние воркера"""
        self._is_running = False
        self._is_paused = False
        self._current_command_index = 0
        self._total_commands = 0
        self._execution_results = []
        self._start_time = None
        self._end_time = None
        
        if self.cancellation_token:
            self.cancellation_token.reset()
        
        self.logger.debug("Состояние воркера сброшено")

