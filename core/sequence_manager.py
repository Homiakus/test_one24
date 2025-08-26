"""
Менеджер последовательностей команд
"""
import logging
import time
import threading
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import re

from PyQt6.QtCore import QThread, pyqtSignal as Signal

from .multizone_manager import MultizoneManager
from .tag_manager import TagManager


class CommandType(Enum):
    """Типы команд"""
    REGULAR = "regular"
    WAIT = "wait"
    SEQUENCE = "sequence"
    BUTTON = "button"
    CONDITIONAL_IF = "conditional_if"
    CONDITIONAL_ELSE = "conditional_else"
    CONDITIONAL_ENDIF = "conditional_endif"
    STOP_IF_NOT = "stop_if_not"
    MULTIZONE = "multizone"
    TAGGED = "tagged"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Результат валидации команды"""
    is_valid: bool
    error_message: str = ""
    command_type: CommandType = CommandType.UNKNOWN
    parsed_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionalState:
    """Состояние условного выполнения"""
    in_conditional_block: bool = False
    current_condition: bool = True
    skip_until_endif: bool = False
    condition_stack: List[bool] = field(default_factory=list)


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


class FlagManager:
    """Менеджер глобальных флагов для условного выполнения"""
    
    def __init__(self):
        self._flags: Dict[str, bool] = {}
        self._lock = threading.Lock()
    
    def set_flag(self, flag_name: str, value: bool) -> None:
        """Установить значение флага"""
        with self._lock:
            self._flags[flag_name] = value
    
    def get_flag(self, flag_name: str, default: bool = False) -> bool:
        """Получить значение флага"""
        with self._lock:
            return self._flags.get(flag_name, default)
    
    def has_flag(self, flag_name: str) -> bool:
        """Проверить существование флага"""
        with self._lock:
            return flag_name in self._flags
    
    def clear_flag(self, flag_name: str) -> None:
        """Очистить флаг"""
        with self._lock:
            self._flags.pop(flag_name, None)
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Получить все флаги"""
        with self._lock:
            return self._flags.copy()
    
    def load_flags_from_config(self, config: Dict[str, Any]) -> None:
        """Загрузить флаги из конфигурации"""
        flags_section = config.get('flags', {})
        with self._lock:
            for flag_name, value in flags_section.items():
                if isinstance(value, bool):
                    self._flags[flag_name] = value


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
    """Исполнитель последовательности команд с thread-safety и условным выполнением"""

    # Сигналы
    progress_updated = Signal(int, int)  # current, total
    command_sent = Signal(str)
    response_received = Signal(str)
    sequence_finished = Signal(bool, str)  # success, message
    flag_changed = Signal(str, bool)  # flag_name, new_value
    conditional_entered = Signal(str, bool)  # condition, result
    conditional_exited = Signal(str)  # condition

    def __init__(self, serial_manager, commands: List[str],
                 keywords: Optional[SequenceKeywords] = None,
                 cancellation_token: Optional[CancellationToken] = None,
                 flag_manager: Optional[FlagManager] = None,
                 multizone_manager: Optional[MultizoneManager] = None):
        super().__init__()
        self.serial_manager = serial_manager
        self.commands = commands
        self.keywords = keywords or SequenceKeywords()
        self.cancellation_token = cancellation_token or CancellationToken()
        self.flag_manager = flag_manager or FlagManager()
        self.multizone_manager = multizone_manager or MultizoneManager()
        self.response_collector = ThreadSafeResponseCollector()
        self.validator = CommandValidator(self.flag_manager)
        self.logger = logging.getLogger(__name__)
        
        # Состояние условного выполнения
        self.conditional_state = ConditionalState()
        
        # Валидируем команды перед выполнением
        is_valid, errors = self.validator.validate_sequence(self.commands)
        if not is_valid:
            self.logger.error(f"Ошибки валидации: {errors}")
            self.sequence_finished.emit(False, f"Ошибки валидации: {'; '.join(errors)}")

    def run(self):
        """Выполнение последовательности с поддержкой условного выполнения"""
        try:
            if not self.serial_manager.is_connected:
                self.sequence_finished.emit(False, "Устройство не подключено")
                return

            total_steps = len(self.commands)
            current_step = 0

            for i, command in enumerate(self.commands):
                # Проверяем отмену
                self.cancellation_token.throw_if_cancelled()

                # Обновляем прогресс
                current_step += 1
                self.progress_updated.emit(current_step, total_steps)

                # Обработка условных команд
                if self._is_conditional_command(command):
                    if not self._handle_conditional_command(command):
                        return
                    continue

                # Обработка команды остановки
                if self._is_stop_command(command):
                    if not self._handle_stop_command(command):
                        return
                    continue

                # Пропускаем команды если находимся в условном блоке с false
                if self.conditional_state.skip_until_endif:
                    continue

                # Обработка мультизональных команд
                if self._is_multizone_command(command):
                    if not self._handle_multizone_command(command):
                        return
                    continue

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

    def _is_conditional_command(self, command: str) -> bool:
        """Проверка, является ли команда условной"""
        command_lower = command.lower().strip()
        return (command_lower.startswith("if ") or 
                command_lower == "else" or 
                command_lower == "endif")
    
    def _is_multizone_command(self, command: str) -> bool:
        """Проверка, является ли команда мультизональной"""
        return command.startswith("og_multizone-")

    def _is_stop_command(self, command: str) -> bool:
        """Проверка, является ли команда командой остановки"""
        return command.lower().startswith("stop_if_not")

    def _handle_conditional_command(self, command: str) -> bool:
        """Обработка условных команд"""
        try:
            command_lower = command.lower().strip()
            
            if command_lower.startswith("if "):
                return self._handle_if_command(command)
            elif command_lower == "else":
                return self._handle_else_command(command)
            elif command_lower == "endif":
                return self._handle_endif_command(command)
            else:
                self.logger.error(f"Неизвестная условная команда: {command}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки условной команды: {e}")
            return False

    def _handle_if_command(self, command: str) -> bool:
        """Обработка команды if"""
        try:
            validation = self.validator.validate_command(command)
            if not validation.is_valid:
                self.logger.error(f"Невалидная if команда: {validation.error_message}")
                return False
            
            flag_name = validation.parsed_data["flag_name"]
            flag_value = self.flag_manager.get_flag(flag_name, False)
            
            # Сохраняем состояние в стек
            self.conditional_state.condition_stack.append(flag_value)
            self.conditional_state.in_conditional_block = True
            
            # Если условие false, пропускаем команды до endif
            if not flag_value:
                self.conditional_state.skip_until_endif = True
            
            self.conditional_entered.emit(f"if {flag_name}", flag_value)
            self.logger.info(f"Вход в условный блок if {flag_name} = {flag_value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки if команды: {e}")
            return False

    def _handle_else_command(self, command: str) -> bool:
        """Обработка команды else"""
        try:
            if not self.conditional_state.in_conditional_block:
                self.logger.error("else без соответствующего if")
                return False
            
            # Инвертируем текущее условие
            if self.conditional_state.condition_stack:
                current_condition = self.conditional_state.condition_stack[-1]
                self.conditional_state.skip_until_endif = current_condition
                self.conditional_state.condition_stack[-1] = not current_condition
            
            self.logger.info("Обработка else блока")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки else команды: {e}")
            return False

    def _handle_endif_command(self, command: str) -> bool:
        """Обработка команды endif"""
        try:
            if not self.conditional_state.in_conditional_block:
                self.logger.error("endif без соответствующего if")
                return False
            
            # Убираем условие из стека
            if self.conditional_state.condition_stack:
                self.conditional_state.condition_stack.pop()
            
            # Если стек пуст, выходим из условного блока
            if not self.conditional_state.condition_stack:
                self.conditional_state.in_conditional_block = False
                self.conditional_state.skip_until_endif = False
            
            self.conditional_exited.emit("endif")
            self.logger.info("Выход из условного блока")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки endif команды: {e}")
            return False

    def _handle_stop_command(self, command: str) -> bool:
        """Обработка команды stop_if_not"""
        try:
            validation = self.validator.validate_command(command)
            if not validation.is_valid:
                self.logger.error(f"Невалидная stop_if_not команда: {validation.error_message}")
                return False
            
            flag_name = validation.parsed_data["flag_name"]
            flag_value = self.flag_manager.get_flag(flag_name, False)
            
            if not flag_value:
                self.logger.warning(f"Остановка выполнения: флаг {flag_name} = false")
                self.sequence_finished.emit(False, f"Выполнение остановлено: флаг {flag_name} = false")
                return False
            
            self.logger.info(f"Продолжение выполнения: флаг {flag_name} = true")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки stop_if_not команды: {e}")
            return False

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

    def _handle_multizone_command(self, command: str) -> bool:
        """Обработка мультизональной команды"""
        try:
            # Валидируем команду
            result = self.validator.validate_command(command)
            if not result.is_valid:
                self.sequence_finished.emit(False, f"Ошибка в мультизональной команде: {result.error_message}")
                return False
            
            # Получаем активные зоны
            active_zones = self.multizone_manager.get_active_zones()
            if not active_zones:
                self.logger.warning("Нет активных зон для мультизональной команды")
                self.sequence_finished.emit(False, "Нет активных зон для мультизональной команды")
                return False
            
            base_command = result.parsed_data["base_command"]
            self.logger.info(f"Выполнение мультизональной команды '{command}' для зон: {active_zones}")
            
            # Выполняем команду для каждой активной зоны
            for zone in active_zones:
                # Проверяем отмену
                self.cancellation_token.throw_if_cancelled()
                
                # Устанавливаем зону
                zone_mask = self.multizone_manager._get_zone_bit(zone)
                zone_command = f"multizone {zone_mask:04b}"
                
                self.logger.info(f"Установка зоны {zone}: {zone_command}")
                if not self.serial_manager.send_command(zone_command):
                    self.sequence_finished.emit(False, f"Не удалось установить зону {zone}")
                    return False
                
                self.command_sent.emit(zone_command)
                
                # Ждем завершения установки зоны
                if not self._wait_for_completion(zone_command, timeout=5.0):
                    return False
                
                # Выполняем основную команду
                self.logger.info(f"Выполнение команды '{base_command}' для зоны {zone}")
                if not self.serial_manager.send_command(base_command):
                    self.sequence_finished.emit(False, f"Не удалось выполнить команду для зоны {zone}")
                    return False
                
                self.command_sent.emit(base_command)
                
                # Ждем завершения выполнения команды
                if not self._wait_for_completion(base_command):
                    return False
            
            self.logger.info(f"Мультизональная команда '{command}' выполнена успешно для всех зон")
            return True

        except CancellationException:
            return False
        except Exception as e:
            self.logger.error(f"Ошибка в мультизональной команде: {e}")
            self.sequence_finished.emit(False, f"Ошибка в мультизональной команде: {e}")
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

    def set_flag(self, flag_name: str, value: bool) -> None:
        """Установить значение флага"""
        self.flag_manager.set_flag(flag_name, value)
        self.flag_changed.emit(flag_name, value)
        self.logger.info(f"Флаг {flag_name} установлен в {value}")

    def get_flag(self, flag_name: str, default: bool = False) -> bool:
        """Получить значение флага"""
        return self.flag_manager.get_flag(flag_name, default)

    def get_all_flags(self) -> Dict[str, bool]:
        """Получить все флаги"""
        return self.flag_manager.get_all_flags()


class CommandValidator:
    """Валидатор команд с поддержкой условного выполнения и тегов"""
    
    def __init__(self, flag_manager: Optional[FlagManager] = None, tag_manager: Optional['TagManager'] = None):
        self.flag_manager = flag_manager
        self.tag_manager = tag_manager
        self.logger = logging.getLogger(__name__)
    
    def validate_command(self, command: str) -> ValidationResult:
        """Валидация отдельной команды"""
        command = command.strip()
        
        # Мультизональные команды
        if command.startswith("og_multizone-"):
            return self._validate_multizone_command(command)
        
        # Команда ожидания
        elif command.lower().startswith("wait"):
            return self._validate_wait_command(command)
        
        # Условные команды
        elif command.lower().startswith("if "):
            return self._validate_if_command(command)
        
        elif command.lower() == "else":
            return ValidationResult(
                is_valid=True,
                command_type=CommandType.CONDITIONAL_ELSE,
                parsed_data={"command": command}
            )
        
        elif command.lower() == "endif":
            return ValidationResult(
                is_valid=True,
                command_type=CommandType.CONDITIONAL_ENDIF,
                parsed_data={"command": command}
            )
        
        # Команда остановки
        elif command.lower().startswith("stop_if_not "):
            return self._validate_stop_if_not_command(command)
        
        # Команда с тегами
        elif self.tag_manager and self._has_tags(command):
            return self._validate_tagged_command(command)
        
        # Обычная команда
        else:
            return ValidationResult(
                is_valid=True,
                command_type=CommandType.REGULAR,
                parsed_data={"command": command}
            )
    
    def _validate_wait_command(self, command: str) -> ValidationResult:
        """Валидация команды ожидания"""
        try:
            parts = command.split()
            if len(parts) != 2:
                return ValidationResult(
                    is_valid=False,
                    error_message="Команда wait должна содержать время в секундах",
                    command_type=CommandType.WAIT
                )
            
            wait_time = float(parts[1])
            if wait_time < 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="Время ожидания должно быть положительным",
                    command_type=CommandType.WAIT
                )
            
            return ValidationResult(
                is_valid=True,
                command_type=CommandType.WAIT,
                parsed_data={"wait_time": wait_time, "command": command}
            )
        
        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_message="Неверный формат времени ожидания",
                command_type=CommandType.WAIT
            )
    
    def _validate_if_command(self, command: str) -> ValidationResult:
        """Валидация условной команды if"""
        try:
            parts = command.split()
            if len(parts) != 2:
                return ValidationResult(
                    is_valid=False,
                    error_message="Команда if должна содержать имя флага",
                    command_type=CommandType.CONDITIONAL_IF
                )
            
            flag_name = parts[1]
            if not flag_name:
                return ValidationResult(
                    is_valid=False,
                    error_message="Имя флага не может быть пустым",
                    command_type=CommandType.CONDITIONAL_IF
                )
            
            return ValidationResult(
                is_valid=True,
                command_type=CommandType.CONDITIONAL_IF,
                parsed_data={"flag_name": flag_name, "command": command}
            )
        
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Ошибка валидации if команды: {e}",
                command_type=CommandType.CONDITIONAL_IF
            )
    
    def _validate_multizone_command(self, command: str) -> ValidationResult:
        """Валидация мультизональной команды"""
        try:
            # Проверяем формат команды og_multizone-*
            if not command.startswith("og_multizone-"):
                return ValidationResult(
                    is_valid=False,
                    error_message="Мультизональная команда должна начинаться с 'og_multizone-'",
                    command_type=CommandType.MULTIZONE
                )
            
            # Извлекаем базовую команду
            base_command = command[13:]  # Убираем "og_multizone-"
            if not base_command:
                return ValidationResult(
                    is_valid=False,
                    error_message="Мультизональная команда должна содержать базовую команду",
                    command_type=CommandType.MULTIZONE
                )
            
            return ValidationResult(
                is_valid=True,
                command_type=CommandType.MULTIZONE,
                parsed_data={
                    "command": command,
                    "base_command": base_command,
                    "is_multizone": True
                }
            )
        
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Ошибка валидации мультизональной команды: {e}",
                command_type=CommandType.MULTIZONE
            )
    
    def _validate_stop_if_not_command(self, command: str) -> ValidationResult:
        """Валидация команды stop_if_not"""
        try:
            parts = command.split()
            if len(parts) != 2:
                return ValidationResult(
                    is_valid=False,
                    error_message="Команда stop_if_not должна содержать имя флага",
                    command_type=CommandType.STOP_IF_NOT
                )
            
            flag_name = parts[1]
            if not flag_name:
                return ValidationResult(
                    is_valid=False,
                    error_message="Имя флага не может быть пустым",
                    command_type=CommandType.STOP_IF_NOT
                )
            
            return ValidationResult(
                is_valid=True,
                command_type=CommandType.STOP_IF_NOT,
                parsed_data={"flag_name": flag_name, "command": command}
            )
        
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Ошибка валидации stop_if_not команды: {e}",
                command_type=CommandType.STOP_IF_NOT
            )
    
    def _has_tags(self, command: str) -> bool:
        """Проверить, содержит ли команда теги"""
        return '_' in command and any(part.startswith('_') for part in command.split())
    
    def _validate_tagged_command(self, command: str) -> ValidationResult:
        """Валидация команды с тегами"""
        try:
            # Парсим команду с тегами
            parsed_command = self.tag_manager.parse_command(command)
            
            # Валидируем теги
            if not self.tag_manager.validate_tags(parsed_command.tags):
                return ValidationResult(
                    is_valid=False,
                    error_message="Ошибка валидации тегов в команде",
                    command_type=CommandType.TAGGED
                )
            
            return ValidationResult(
                is_valid=True,
                command_type=CommandType.TAGGED,
                parsed_data={
                    "command": command,
                    "base_command": parsed_command.base_command,
                    "tags": parsed_command.tags,
                    "parsed_command": parsed_command
                }
            )
        
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Ошибка валидации команды с тегами: {e}",
                command_type=CommandType.TAGGED
            )
    
    def validate_sequence(self, commands: List[str]) -> Tuple[bool, List[str]]:
        """Валидация последовательности команд"""
        errors = []
        conditional_stack = []
        
        for i, command in enumerate(commands):
            result = self.validate_command(command)
            
            if not result.is_valid:
                errors.append(f"Команда {i+1}: {result.error_message}")
                continue
            
            # Проверяем баланс условных блоков
            if result.command_type == CommandType.CONDITIONAL_IF:
                conditional_stack.append("if")
            elif result.command_type == CommandType.CONDITIONAL_ELSE:
                if not conditional_stack or conditional_stack[-1] != "if":
                    errors.append(f"Команда {i+1}: else без соответствующего if")
                else:
                    conditional_stack[-1] = "else"
            elif result.command_type == CommandType.CONDITIONAL_ENDIF:
                if not conditional_stack:
                    errors.append(f"Команда {i+1}: endif без соответствующего if")
                else:
                    conditional_stack.pop()
        
        # Проверяем незакрытые блоки
        if conditional_stack:
            errors.append(f"Незакрытые условные блоки: {conditional_stack}")
        
        return len(errors) == 0, errors


class SequenceManager:
    """Менеджер последовательностей с thread-safety"""

    def __init__(self, config: Dict[str, List[str]],
                 buttons_config: Dict[str, str],
                 flag_manager: Optional[FlagManager] = None):
        """
        Инициализация менеджера

        Args:
            config: Конфигурация последовательностей
            buttons_config: Конфигурация кнопок/команд
            flag_manager: Менеджер флагов для условного выполнения
        """
        self.sequences = config
        self.buttons_config = buttons_config
        self.flag_manager = flag_manager or FlagManager()
        self.logger = logging.getLogger(__name__)
        
        # Thread-safe компоненты
        self.validator = CommandValidator(self.flag_manager)
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

    def _extract_used_flags(self, commands: List[str]) -> Set[str]:
        """Извлечь используемые флаги из команд"""
        flags = set()
        for command in commands:
            command_lower = command.lower().strip()
            if command_lower.startswith("if "):
                parts = command.split()
                if len(parts) >= 2:
                    flags.add(parts[1])
            elif command_lower.startswith("stop_if_not "):
                parts = command.split()
                if len(parts) >= 2:
                    flags.add(parts[1])
        return flags

    def set_flag(self, flag_name: str, value: bool) -> None:
        """Установить значение флага"""
        self.flag_manager.set_flag(flag_name, value)

    def get_flag(self, flag_name: str, default: bool = False) -> bool:
        """Получить значение флага"""
        return self.flag_manager.get_flag(flag_name, default)

    def get_all_flags(self) -> Dict[str, bool]:
        """Получить все флаги"""
        return self.flag_manager.get_all_flags()

    def load_flags_from_config(self, config: Dict[str, Any]) -> None:
        """Загрузить флаги из конфигурации"""
        self.flag_manager.load_flags_from_config(config)
