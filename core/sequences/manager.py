"""
Модуль для управления последовательностями команд.

Содержит основной класс SequenceManager который объединяет все компоненты
для парсинга, валидации и выполнения последовательностей команд.
"""

import logging
import threading
from typing import List, Dict, Any, Optional, Callable, Tuple
from .types import CommandType, ValidationResult, SequenceKeywords
from .parser import SequenceParser
from .validator import SequenceValidator
from .executor import SequenceExecutor
from .conditional import ConditionalProcessor
from .response import ResponseAnalyzer
from .worker import SequenceWorker
from .flags import FlagManager
from .cancellation import CancellationToken


class SequenceManager:
    """
    Основной менеджер последовательностей команд.
    
    Объединяет все компоненты для полного управления последовательностями:
    - Парсинг команд
    - Валидация последовательностей
    - Выполнение команд
    - Обработка условной логики
    - Анализ ответов
    - Асинхронное выполнение
    """
    
    def __init__(self, serial_manager, flag_manager: Optional[FlagManager] = None):
        self.serial_manager = serial_manager
        self.flag_manager = flag_manager or FlagManager()
        self.logger = logging.getLogger(__name__)
        
        # Инициализируем компоненты
        self.parser = SequenceParser()
        self.validator = SequenceValidator(self.flag_manager)
        self.executor = SequenceExecutor(serial_manager, self.flag_manager)
        self.conditional = ConditionalProcessor(self.flag_manager)
        self.response_analyzer = ResponseAnalyzer()
        self.worker = SequenceWorker(serial_manager, self.flag_manager)
        
        # Состояние менеджера
        self._is_initialized = False
        self._lock = threading.RLock()
        
        # Статистика выполнения
        self._execution_stats = {
            'total_sequences': 0,
            'successful_sequences': 0,
            'failed_sequences': 0,
            'total_commands': 0,
            'successful_commands': 0,
            'failed_commands': 0
        }
        
        # Callbacks для событий
        self.on_sequence_started: Optional[Callable[[List[str]], None]] = None
        self.on_sequence_completed: Optional[Callable[[bool, str], None]] = None
        self.on_command_executed: Optional[Callable[[str, bool], None]] = None
        self.on_progress_updated: Optional[Callable[[int, int], None]] = None
        self.on_error_occurred: Optional[Callable[[str, Exception], None]] = None
        
        # Инициализируем менеджер
        self._initialize()
    
    def _initialize(self):
        """Инициализация менеджера"""
        try:
            # Устанавливаем callbacks для компонентов
            self._setup_callbacks()
            
            # Проверяем подключение
            if not self.serial_manager.is_connected:
                self.logger.warning("Serial manager не подключен")
            
            self._is_initialized = True
            self.logger.info("SequenceManager инициализирован успешно")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации SequenceManager: {e}")
            raise
    
    def _setup_callbacks(self):
        """Настройка callbacks для компонентов"""
        # Callbacks для executor
        self.executor.set_callbacks(
            on_command_executed=self._on_command_executed,
            on_progress_updated=self._on_progress_updated,
            on_sequence_finished=self._on_sequence_finished
        )
        
        # Callbacks для worker
        self.worker.set_callbacks(
            on_command_executed=self._on_command_executed,
            on_progress_updated=self._on_progress_updated,
            on_sequence_finished=self._on_sequence_finished,
            on_worker_started=self._on_worker_started,
            on_worker_stopped=self._on_worker_stopped
        )
        
        # Callbacks для conditional processor
        self.conditional.set_callbacks(
            on_conditional_entered=self._on_conditional_entered,
            on_conditional_exited=self._on_conditional_exited,
            on_condition_evaluated=self._on_condition_evaluated
        )
    
    def execute_sequence(self, commands: List[str], 
                        async_execution: bool = False,
                        timeout: Optional[float] = None) -> bool:
        """
        Выполнить последовательность команд.
        
        Args:
            commands: Список команд для выполнения
            async_execution: True для асинхронного выполнения
            timeout: Таймаут выполнения в секундах
            
        Returns:
            True если последовательность выполнена успешно
        """
        with self._lock:
            if not self._is_initialized:
                self.logger.error("SequenceManager не инициализирован")
                return False
            
            if not commands:
                self.logger.warning("Пустая последовательность команд")
                return False
            
            # Валидируем последовательность
            is_valid, errors = self.validator.validate_sequence(commands)
            if not is_valid:
                error_msg = f"Ошибки валидации: {', '.join(errors)}"
                self.logger.error(error_msg)
                self._notify_error_occurred(error_msg, ValueError(error_msg))
                return False
            
            # Обновляем статистику
            self._execution_stats['total_sequences'] += 1
            self._execution_stats['total_commands'] += len(commands)
            
            # Уведомляем о начале выполнения
            self._notify_sequence_started(commands)
            
            try:
                if async_execution:
                    # Асинхронное выполнение через worker
                    success = self.worker.start_execution(commands)
                    if not success:
                        self._execution_stats['failed_sequences'] += 1
                        return False
                    
                    # Ждем завершения с таймаутом
                    if timeout:
                        import time
                        start_time = time.time()
                        while self.worker.is_running() and (time.time() - start_time) < timeout:
                            time.sleep(0.1)
                        
                        if self.worker.is_running():
                            self.worker.stop_execution()
                            self.logger.warning("Превышен таймаут выполнения")
                            return False
                    
                    # Ждем завершения
                    while self.worker.is_running():
                        time.sleep(0.1)
                    
                    return self.worker.get_success_rate() > 0
                else:
                    # Синхронное выполнение через executor
                    success = self.executor.execute_sequence(commands)
                    if success:
                        self._execution_stats['successful_sequences'] += 1
                    else:
                        self._execution_stats['failed_sequences'] += 1
                    return success
                    
            except Exception as e:
                error_msg = f"Ошибка выполнения последовательности: {e}"
                self.logger.error(error_msg)
                self._notify_error_occurred(error_msg, e)
                self._execution_stats['failed_sequences'] += 1
                return False
    
    def execute_single_command(self, command: str) -> bool:
        """
        Выполнить одну команду.
        
        Args:
            command: Команда для выполнения
            
        Returns:
            True если команда выполнена успешно
        """
        with self._lock:
            if not self._is_initialized:
                self.logger.error("SequenceManager не инициализирован")
                return False
            
            # Валидируем команду
            result = self.validator.validate_command(command)
            if not result.is_valid:
                self.logger.error(f"Ошибка валидации команды: {result.error_message}")
                return False
            
            # Обновляем статистику
            self._execution_stats['total_commands'] += 1
            
            try:
                # Выполняем команду
                success = self.executor._send_and_wait_command(command)
                if success:
                    self._execution_stats['successful_commands'] += 1
                else:
                    self._execution_stats['failed_commands'] += 1
                return success
                
            except Exception as e:
                error_msg = f"Ошибка выполнения команды '{command}': {e}"
                self.logger.error(error_msg)
                self._notify_error_occurred(error_msg, e)
                self._execution_stats['failed_commands'] += 1
                return False
    
    def parse_command(self, command: str) -> ValidationResult:
        """
        Парсить команду.
        
        Args:
            command: Строка команды для парсинга
            
        Returns:
            ValidationResult с результатом парсинга
        """
        return self.parser.parse_command(command)
    
    def validate_sequence(self, commands: List[str]) -> Tuple[bool, List[str]]:
        """
        Валидировать последовательность команд.
        
        Args:
            commands: Список команд для валидации
            
        Returns:
            Tuple (is_valid, errors) где errors - список ошибок
        """
        return self.validator.validate_sequence(commands)
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Получить статистику выполнения"""
        with self._lock:
            stats = self._execution_stats.copy()
            
            # Добавляем статистику от компонентов
            if hasattr(self.response_analyzer, 'get_response_statistics'):
                stats['response_stats'] = self.response_analyzer.get_response_statistics()
            
            if hasattr(self.worker, 'get_success_rate'):
                stats['worker_success_rate'] = self.worker.get_success_rate()
            
            if hasattr(self.conditional, 'get_conditional_stack_depth'):
                stats['conditional_stack_depth'] = self.conditional.get_conditional_stack_depth()
            
            return stats
    
    def reset_statistics(self):
        """Сбросить статистику выполнения"""
        with self._lock:
            self._execution_stats = {
                'total_sequences': 0,
                'successful_sequences': 0,
                'failed_sequences': 0,
                'total_commands': 0,
                'successful_commands': 0,
                'failed_commands': 0
            }
            
            # Сбрасываем статистику компонентов
            if hasattr(self.response_analyzer, 'reset_statistics'):
                self.response_analyzer.reset_statistics()
            
            self.logger.debug("Статистика выполнения сброшена")
    
    def get_success_rate(self) -> float:
        """Получить общий процент успешных команд"""
        with self._lock:
            if self._execution_stats['total_commands'] == 0:
                return 0.0
            
            return (self._execution_stats['successful_commands'] / 
                    self._execution_stats['total_commands']) * 100.0
    
    def is_worker_running(self) -> bool:
        """Проверить, запущен ли worker"""
        return self.worker.is_running()
    
    def stop_worker(self) -> bool:
        """Остановить worker"""
        return self.worker.stop_execution()
    
    def pause_worker(self) -> bool:
        """Приостановить worker"""
        return self.worker.pause_execution()
    
    def resume_worker(self) -> bool:
        """Возобновить worker"""
        return self.worker.resume_execution()
    
    def get_worker_progress(self) -> Tuple[int, int]:
        """Получить прогресс worker"""
        return self.worker.get_progress()
    
    def set_callbacks(self, 
                     on_sequence_started: Optional[Callable[[List[str]], None]] = None,
                     on_sequence_completed: Optional[Callable[[bool, str], None]] = None,
                     on_command_executed: Optional[Callable[[str, bool], None]] = None,
                     on_progress_updated: Optional[Callable[[int, int], None]] = None,
                     on_error_occurred: Optional[Callable[[str, Exception], None]] = None):
        """Установить callbacks для событий"""
        self.on_sequence_started = on_sequence_started
        self.on_sequence_completed = on_sequence_completed
        self.on_command_executed = on_command_executed
        self.on_progress_updated = on_progress_updated
        self.on_error_occurred = on_error_occurred
    
    def _on_command_executed(self, command: str, success: bool):
        """Callback для выполнения команды"""
        if self.on_command_executed:
            try:
                self.on_command_executed(command, success)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_command_executed: {e}")
    
    def _on_progress_updated(self, current: int, total: int):
        """Callback для обновления прогресса"""
        if self.on_progress_updated:
            try:
                self.on_progress_updated(current, total)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_progress_updated: {e}")
    
    def _on_sequence_finished(self, success: bool, message: str):
        """Callback для завершения последовательности"""
        if self.on_sequence_completed:
            try:
                self.on_sequence_completed(success, message)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_sequence_completed: {e}")
    
    def _on_worker_started(self):
        """Callback для запуска worker"""
        self.logger.debug("Worker запущен")
    
    def _on_worker_stopped(self):
        """Callback для остановки worker"""
        self.logger.debug("Worker остановлен")
    
    def _on_conditional_entered(self, condition: str, result: bool):
        """Callback для входа в условный блок"""
        self.logger.debug(f"Вход в условный блок: {condition} = {result}")
    
    def _on_conditional_exited(self, command: str):
        """Callback для выхода из условного блока"""
        self.logger.debug(f"Выход из условного блока: {command}")
    
    def _on_condition_evaluated(self, condition: str, result: bool):
        """Callback для вычисления условия"""
        self.logger.debug(f"Условие вычислено: {condition} = {result}")
    
    def _notify_sequence_started(self, commands: List[str]):
        """Уведомить о начале выполнения последовательности"""
        if self.on_sequence_started:
            try:
                self.on_sequence_started(commands)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_sequence_started: {e}")
    
    def _notify_error_occurred(self, message: str, exception: Exception):
        """Уведомить об ошибке"""
        if self.on_error_occurred:
            try:
                self.on_error_occurred(message, exception)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_error_occurred: {e}")
    
    def reset_state(self):
        """Сбросить состояние менеджера"""
        with self._lock:
            self.executor.reset_state()
            self.conditional.reset_state()
            self.worker.reset_state()
            self.logger.debug("Состояние SequenceManager сброшено")
    
    def cleanup(self):
        """Очистка ресурсов"""
        with self._lock:
            try:
                # Останавливаем worker если запущен
                if self.worker.is_running():
                    self.worker.stop_execution()
                
                # Сбрасываем состояние
                self.reset_state()
                
                self._is_initialized = False
                self.logger.info("SequenceManager очищен")
                
            except Exception as e:
                self.logger.error(f"Ошибка очистки SequenceManager: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
