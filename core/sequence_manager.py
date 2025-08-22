"""
Менеджер последовательностей команд с thread-safety и валидацией
"""
import re
import time
import logging
import threading
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from queue import Queue, Empty
from enum import Enum
from contextlib import contextmanager

from PySide6.QtCore import QThread, Signal


class CommandType(Enum):
    """Типы команд"""
    REGULAR = "regular"
    WAIT = "wait"
    SEQUENCE = "sequence"
    BUTTON = "button"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Результат валидации команды"""
    is_valid: bool
    error_message: str = ""
    command_type: CommandType = CommandType.UNKNOWN
    parsed_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SequenceKeywords:
    """Ключевые слова для анализа ответов"""
    complete: List[str] = None
    received: List[str] = None
    error: List[str] = None
    complete_line: List[str] = None

    def __post_init__(self):
        if self.complete is None:
            self.complete = ['complete', 'completed', 'done', 'COMPLETE']
        if self.received is None:
            self.received = ['received']
        if self.error is None:
            self.error = ['err', 'error', 'fail']
        if self.complete_line is None:
            self.complete_line = ['complete']


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


class CancellationException(Exception):
    """Исключение при отмене операции"""
    pass


class ThreadSafeResponseCollector:
    """Thread-safe коллектор ответов"""
    
    def __init__(self, max_size: int = 1000):
        self._queue = Queue(maxsize=max_size)
        self._lock = threading.Lock()
        self._total_responses = 0
    
    def add_response(self, response: str) -> bool:
        """Добавить ответ в коллекцию"""
        try:
            with self._lock:
                self._total_responses += 1
            self._queue.put_nowait(response)
            return True
        except:
            return False
    
    def get_responses(self, timeout: float = 0.1) -> List[str]:
        """Получить все доступные ответы"""
        responses = []
        try:
            while True:
                response = self._queue.get_nowait()
                responses.append(response)
        except Empty:
            pass
        return responses
    
    def clear(self):
        """Очистить коллекцию"""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except Empty:
                break
        with self._lock:
            self._total_responses = 0
    
    def get_total_count(self) -> int:
        """Получить общее количество ответов"""
        with self._lock:
            return self._total_responses


class CommandValidator:
    """Валидатор команд"""
    
    def __init__(self, max_recursion_depth: int = 10, max_wait_time: float = 3600.0):
        self.max_recursion_depth = max_recursion_depth
        self.max_wait_time = max_wait_time
        self.logger = logging.getLogger(__name__)
    
    def validate_command(self, command: str) -> ValidationResult:
        """Валидировать команду"""
        command = command.strip()
        
        if not command:
            return ValidationResult(False, "Пустая команда", CommandType.UNKNOWN)
        
        # Проверка wait команды
        if command.lower().startswith("wait"):
            return self._validate_wait_command(command)
        
        # Проверка обычной команды
        return ValidationResult(True, "", CommandType.REGULAR, {"command": command})
    
    def _validate_wait_command(self, command: str) -> ValidationResult:
        """Валидировать wait команду"""
        try:
            parts = command.split()
            if len(parts) != 2:
                return ValidationResult(
                    False, 
                    "Неверный синтаксис wait команды. Используйте: wait <время>", 
                    CommandType.WAIT
                )
            
            wait_time = float(parts[1])
            
            if wait_time < 0:
                return ValidationResult(
                    False, 
                    "Время ожидания не может быть отрицательным", 
                    CommandType.WAIT
                )
            
            if wait_time > self.max_wait_time:
                return ValidationResult(
                    False, 
                    f"Время ожидания превышает максимальное ({self.max_wait_time} сек)", 
                    CommandType.WAIT
                )
            
            return ValidationResult(
                True, 
                "", 
                CommandType.WAIT, 
                {"wait_time": wait_time}
            )
            
        except ValueError:
            return ValidationResult(
                False, 
                "Неверный формат времени в wait команде", 
                CommandType.WAIT
            )
    
    def validate_sequence(self, sequence: List[str]) -> Tuple[bool, List[str]]:
        """Валидировать последовательность команд"""
        errors = []
        
        for i, command in enumerate(sequence):
            result = self.validate_command(command)
            if not result.is_valid:
                errors.append(f"Команда {i+1}: {result.error_message}")
        
        return len(errors) == 0, errors


class RecursionProtector:
    """Защита от рекурсии"""
    
    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self._call_stack = threading.local()
        self._cache = {}
        self._cache_lock = threading.Lock()
    
    def _get_call_stack(self) -> Set[str]:
        """Получить текущий стек вызовов"""
        if not hasattr(self._call_stack, 'stack'):
            self._call_stack.stack = set()
        return self._call_stack.stack
    
    def enter_sequence(self, sequence_name: str) -> bool:
        """Войти в последовательность"""
        stack = self._get_call_stack()
        
        if len(stack) >= self.max_depth:
            return False
        
        if sequence_name in stack:
            return False
        
        stack.add(sequence_name)
        return True
    
    def exit_sequence(self, sequence_name: str):
        """Выйти из последовательности"""
        stack = self._get_call_stack()
        stack.discard(sequence_name)
    
    def get_cache_key(self, sequence_name: str, visited: Set[str]) -> str:
        """Получить ключ кеша"""
        visited_str = ",".join(sorted(visited))
        return f"{sequence_name}:{visited_str}"
    
    def get_cached_result(self, cache_key: str) -> Optional[List[str]]:
        """Получить результат из кеша"""
        with self._cache_lock:
            return self._cache.get(cache_key)
    
    def cache_result(self, cache_key: str, result: List[str]):
        """Сохранить результат в кеш"""
        with self._cache_lock:
            self._cache[cache_key] = result
    
    def clear_cache(self):
        """Очистить кеш"""
        with self._cache_lock:
            self._cache.clear()


class CommandSequenceExecutor(QThread):
    """Исполнитель последовательности команд с thread-safety"""

    # Сигналы
    progress_updated = Signal(int, int)  # current, total
    command_sent = Signal(str)
    response_received = Signal(str)
    sequence_finished = Signal(bool, str)  # success, message

    def __init__(self, serial_manager, commands: List[str],
                 keywords: Optional[SequenceKeywords] = None,
                 cancellation_token: Optional[CancellationToken] = None):
        super().__init__()
        self.serial_manager = serial_manager
        self.commands = commands
        self.keywords = keywords or SequenceKeywords()
        self.cancellation_token = cancellation_token or CancellationToken()
        self.response_collector = ThreadSafeResponseCollector()
        self.validator = CommandValidator()
        self.logger = logging.getLogger(__name__)
        
        # Валидируем команды перед выполнением
        is_valid, errors = self.validator.validate_sequence(self.commands)
        if not is_valid:
            self.logger.error(f"Ошибки валидации: {errors}")
            self.sequence_finished.emit(False, f"Ошибки валидации: {'; '.join(errors)}")

    def run(self):
        """Выполнение последовательности"""
        try:
            if not self.serial_manager.is_connected:
                self.sequence_finished.emit(False, "Устройство не подключено")
                return

            total_steps = len(self.commands)

            for i, command in enumerate(self.commands):
                # Проверяем отмену
                self.cancellation_token.throw_if_cancelled()

                # Обновляем прогресс
                self.progress_updated.emit(i + 1, total_steps)

                # Обработка специальных команд
                if self._is_wait_command(command):
                    if not self._handle_wait_command(command):
                        return
                    continue

                # Отправка обычной команды
                if not self._send_and_wait_command(command):
                    return

            # Успешное завершение
            self.sequence_finished.emit(True, "Последовательность выполнена успешно")
            
        except CancellationException:
            self.sequence_finished.emit(False, "Выполнение прервано")
        except Exception as e:
            self.logger.error(f"Ошибка выполнения последовательности: {e}")
            self.sequence_finished.emit(False, f"Ошибка: {e}")

    def _is_wait_command(self, command: str) -> bool:
        """Проверка, является ли команда командой ожидания"""
        return command.lower().startswith("wait")

    def _handle_wait_command(self, command: str) -> bool:
        """Обработка команды ожидания"""
        try:
            # Валидируем команду
            result = self.validator.validate_command(command)
            if not result.is_valid:
                self.sequence_finished.emit(False, f"Ошибка в команде wait: {result.error_message}")
                return False
            
            wait_time = result.parsed_data["wait_time"]
            self.command_sent.emit(f"Ожидание {wait_time} секунд...")

            # Прерываемое ожидание
            start_time = time.time()
            while time.time() - start_time < wait_time:
                self.cancellation_token.throw_if_cancelled()
                time.sleep(0.1)

            return True

        except CancellationException:
            return False
        except Exception as e:
            self.sequence_finished.emit(False, f"Ошибка в команде wait: {e}")
            return False

    def _send_and_wait_command(self, command: str) -> bool:
        """Отправка команды и ожидание ответа"""
        try:
            # Очищаем буфер ответов
            self.response_collector.clear()

            # Отправляем команду
            if not self.serial_manager.send_command(command):
                self.sequence_finished.emit(False, f"Не удалось отправить: {command}")
                return False

            self.command_sent.emit(command)

            # Ожидаем завершения
            if not self._wait_for_completion(command):
                return False

            return True

        except CancellationException:
            return False
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении команды: {e}")
            self.sequence_finished.emit(False, f"Ошибка: {e}")
            return False

    def _wait_for_completion(self, command: str, timeout: float = 10.0) -> bool:
        """Ожидание завершения выполнения команды"""
        completed = False
        start_time = time.time()

        while not completed and time.time() - start_time < timeout:
            self.cancellation_token.throw_if_cancelled()

            current_responses = self.response_collector.get_responses()

            for response in current_responses:
                resp_lower = response.lower()

                # Проверка на завершение
                if resp_lower.strip() in self.keywords.complete_line:
                    completed = True
                    break

                # Проверка на ошибку
                if any(re.search(rf"\\b{re.escape(kw)}\\b", resp_lower)
                      for kw in self.keywords.error):
                    self.sequence_finished.emit(False, f"Ошибка: {response}")
                    return False

            if not completed:
                time.sleep(0.1)

        if not completed:
            self.sequence_finished.emit(False, f"Таймаут для команды: {command}")
            return False

        return True

    def add_response(self, response: str):
        """Добавление ответа от устройства"""
        self.response_collector.add_response(response)
        self.response_received.emit(response)

    def stop(self):
        """Остановка выполнения"""
        self.cancellation_token.cancel()
        self.wait()


class SequenceManager:
    """Менеджер последовательностей с thread-safety"""

    def __init__(self, config: Dict[str, List[str]],
                 buttons_config: Dict[str, str]):
        """
        Инициализация менеджера

        Args:
            config: Конфигурация последовательностей
            buttons_config: Конфигурация кнопок/команд
        """
        self.sequences = config
        self.buttons_config = buttons_config
        self.logger = logging.getLogger(__name__)
        
        # Thread-safe компоненты
        self.validator = CommandValidator()
        self.recursion_protector = RecursionProtector()
        self._lock = threading.Lock()

    def expand_sequence(self, sequence_name: str) -> List[str]:
        """
        Разворачивание последовательности в список команд с защитой от рекурсии

        Args:
            sequence_name: Имя последовательности

        Returns:
            Список развернутых команд
        """
        with self._lock:
            if sequence_name not in self.sequences:
                self.logger.error(f"Последовательность '{sequence_name}' не найдена")
                return []

            visited = set()
            return self._expand_items(self.sequences[sequence_name], visited, sequence_name)

    def _expand_items(self, items: List[str], visited: Set[str], current_sequence: str) -> List[str]:
        """Рекурсивное разворачивание элементов с защитой от рекурсии"""
        # Проверяем защиту от рекурсии
        if not self.recursion_protector.enter_sequence(current_sequence):
            self.logger.error(f"Обнаружена рекурсия или превышена глубина в '{current_sequence}'")
            return []

        try:
            # Проверяем кеш
            cache_key = self.recursion_protector.get_cache_key(current_sequence, visited)
            cached_result = self.recursion_protector.get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result

            result = []

            for item in items:
                # Команда ожидания
                if item.lower().startswith("wait"):
                    # Валидируем wait команду
                    validation = self.validator.validate_command(item)
                    if not validation.is_valid:
                        self.logger.warning(f"Невалидная wait команда: {validation.error_message}")
                        continue
                    result.append(item)
                
                # Команда из конфигурации
                elif item in self.buttons_config:
                    result.append(self.buttons_config[item])
                
                # Вложенная последовательность
                elif item in self.sequences:
                    if item in visited:
                        self.logger.warning(f"Обнаружена рекурсия в '{item}'")
                        continue

                    visited.add(item)
                    expanded = self._expand_items(self.sequences[item], visited, item)
                    result.extend(expanded)
                    visited.remove(item)
                
                # Неизвестная команда - валидируем и отправляем как есть
                else:
                    validation = self.validator.validate_command(item)
                    if validation.is_valid:
                        result.append(item)
                    else:
                        self.logger.warning(f"Невалидная команда '{item}': {validation.error_message}")

            # Кешируем результат
            self.recursion_protector.cache_result(cache_key, result)
            return result

        finally:
            self.recursion_protector.exit_sequence(current_sequence)

    def validate_sequence(self, sequence_name: str) -> Tuple[bool, List[str]]:
        """
        Валидация последовательности

        Args:
            sequence_name: Имя последовательности

        Returns:
            (is_valid, errors) - результат валидации и список ошибок
        """
        try:
            commands = self.expand_sequence(sequence_name)
            if not commands:
                return False, [f"Последовательность '{sequence_name}' пуста или не найдена"]
            
            return self.validator.validate_sequence(commands)
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации: {e}")
            return False, [f"Ошибка валидации: {e}"]

    def get_sequence_info(self, sequence_name: str) -> Dict[str, Any]:
        """
        Получить информацию о последовательности

        Args:
            sequence_name: Имя последовательности

        Returns:
            Словарь с информацией о последовательности
        """
        with self._lock:
            if sequence_name not in self.sequences:
                return {"exists": False, "error": "Последовательность не найдена"}

            try:
                commands = self.expand_sequence(sequence_name)
                is_valid, errors = self.validate_sequence(sequence_name)
                
                return {
                    "exists": True,
                    "is_valid": is_valid,
                    "errors": errors,
                    "command_count": len(commands),
                    "commands": commands
                }
            except Exception as e:
                return {
                    "exists": True,
                    "is_valid": False,
                    "errors": [f"Ошибка анализа: {e}"],
                    "command_count": 0,
                    "commands": []
                }

    def clear_cache(self):
        """Очистить кеш рекурсии"""
        self.recursion_protector.clear_cache()
