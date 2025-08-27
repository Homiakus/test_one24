"""
Модуль для выполнения команд последовательностей.

Содержит класс SequenceExecutor для исполнения команд
с поддержкой условной логики и отмены операций.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Callable
from .types import CommandType, ValidationResult, ConditionalState
from .cancellation import CancellationToken, CancellationException
from .flags import FlagManager


class SequenceExecutor:
    """Исполнитель последовательности команд"""
    
    def __init__(self, 
                 serial_manager,
                 flag_manager: FlagManager,
                 cancellation_token: Optional[CancellationToken] = None):
        self.serial_manager = serial_manager
        self.flag_manager = flag_manager
        self.cancellation_token = cancellation_token or CancellationToken()
        self.logger = logging.getLogger(__name__)
        
        # Состояние условного выполнения
        self.conditional_state = ConditionalState()
        
        # Callbacks для событий
        self.on_command_executed: Optional[Callable[[str, bool], None]] = None
        self.on_progress_updated: Optional[Callable[[int, int], None]] = None
        self.on_sequence_finished: Optional[Callable[[bool, str], None]] = None
    
    def execute_sequence(self, commands: List[str]) -> bool:
        """
        Выполнить последовательность команд.
        
        Args:
            commands: Список команд для выполнения
            
        Returns:
            True если последовательность выполнена успешно
        """
        if not commands:
            self.logger.warning("Пустая последовательность команд")
            return False
        
        if not self.serial_manager.is_connected:
            error_msg = "Устройство не подключено"
            self.logger.error(error_msg)
            self._notify_sequence_finished(False, error_msg)
            return False
        
        self.logger.info(f"Начинаю выполнение последовательности из {len(commands)} команд")
        
        try:
            total_steps = len(commands)
            current_step = 0
            
            for i, command in enumerate(commands):
                # Проверяем отмену
                self.cancellation_token.throw_if_cancelled()
                
                # Обновляем прогресс
                current_step += 1
                self._notify_progress_updated(current_step, total_steps)
                
                self.logger.debug(f"Выполняю команду {current_step}/{total_steps}: {command}")
                
                # Обработка условных команд
                if self._is_conditional_command(command):
                    if not self._handle_conditional_command(command):
                        return False
                    continue
                
                # Обработка команды остановки
                if self._is_stop_command(command):
                    if not self._handle_stop_command(command):
                        return False
                    continue
                
                # Пропускаем команды если находимся в условном блоке с false
                if self.conditional_state.skip_until_endif:
                    self.logger.debug(f"Пропускаю команду в условном блоке: {command}")
                    continue
                
                # Обработка мультизональных команд
                if self._is_multizone_command(command):
                    if not self._handle_multizone_command(command):
                        return False
                    continue
                
                # Обработка специальных команд
                if self._is_wait_command(command):
                    if not self._handle_wait_command(command):
                        return False
                    continue
                
                # Отправка обычной команды
                if not self._send_and_wait_command(command):
                    return False
            
            # Проверяем, что все условные блоки закрыты
            if self.conditional_state.in_conditional_block:
                error_msg = "Незакрытый условный блок"
                self.logger.error(error_msg)
                self._notify_sequence_finished(False, error_msg)
                return False
            
            success_msg = f"Последовательность выполнена успешно: {len(commands)} команд"
            self.logger.info(success_msg)
            self._notify_sequence_finished(True, success_msg)
            return True
            
        except CancellationException:
            cancel_msg = "Выполнение последовательности отменено"
            self.logger.info(cancel_msg)
            self._notify_sequence_finished(False, cancel_msg)
            return False
        except Exception as e:
            error_msg = f"Ошибка выполнения последовательности: {e}"
            self.logger.error(error_msg)
            self._notify_sequence_finished(False, error_msg)
            return False
    
    def _is_conditional_command(self, command: str) -> bool:
        """Проверить, является ли команда условной"""
        return (command.lower().startswith("if") or 
                command.lower() == "else" or 
                command.lower() == "endif")
    
    def _is_stop_command(self, command: str) -> bool:
        """Проверить, является ли команда командой остановки"""
        return command.lower().startswith("stop_if_not")
    
    def _is_multizone_command(self, command: str) -> bool:
        """Проверить, является ли команда мультизональной"""
        return command.lower().startswith("multizone")
    
    def _is_wait_command(self, command: str) -> bool:
        """Проверить, является ли команда командой ожидания"""
        return command.lower().startswith("wait")
    
    def _handle_conditional_command(self, command: str) -> bool:
        """Обработать условную команду"""
        try:
            if command.lower().startswith("if"):
                condition = command[2:].strip()
                result = self._evaluate_condition(condition)
                
                self.conditional_state.in_conditional_block = True
                self.conditional_state.current_condition = result
                self.conditional_state.skip_until_endif = not result
                self.conditional_state.condition_stack.append(result)
                
                self.logger.debug(f"Условие '{condition}' = {result}")
                
            elif command.lower() == "else":
                if not self.conditional_state.in_conditional_block:
                    self.logger.error("else без соответствующего if")
                    return False
                
                # Инвертируем текущее условие для else блока
                self.conditional_state.current_condition = not self.conditional_state.current_condition
                self.conditional_state.skip_until_endif = not self.conditional_state.current_condition
                
                self.logger.debug(f"else блок: условие = {self.conditional_state.current_condition}")
                
            elif command.lower() == "endif":
                if not self.conditional_state.in_conditional_block:
                    self.logger.error("endif без соответствующего if")
                    return False
                
                # Выходим из условного блока
                if self.conditional_state.condition_stack:
                    self.conditional_state.condition_stack.pop()
                
                if not self.conditional_state.condition_stack:
                    self.conditional_state.in_conditional_block = False
                    self.conditional_state.skip_until_endif = False
                
                self.logger.debug("Выход из условного блока")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки условной команды '{command}': {e}")
            return False
    
    def _handle_stop_command(self, command: str) -> bool:
        """Обработать команду остановки"""
        try:
            condition = command[11:].strip()
            result = self._evaluate_condition(condition)
            
            if not result:
                self.logger.info(f"Остановка по условию: {condition}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки команды остановки '{command}': {e}")
            return False
    
    def _handle_multizone_command(self, command: str) -> bool:
        """Обработать мультизональную команду"""
        try:
            # Здесь должна быть логика для multizone команд
            # Пока просто логируем
            self.logger.debug(f"Обрабатываю multizone команду: {command}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки multizone команды '{command}': {e}")
            return False
    
    def _handle_wait_command(self, command: str) -> bool:
        """Обработать команду ожидания"""
        try:
            parts = command.split()
            if len(parts) != 2:
                self.logger.error(f"Неверный синтаксис wait команды: {command}")
                return False
            
            wait_time = float(parts[1])
            if wait_time < 0:
                self.logger.error(f"Отрицательное время ожидания: {wait_time}")
                return False
            
            self.logger.debug(f"Ожидание {wait_time} секунд")
            
            # Ожидаем с проверкой отмены каждые 100мс
            start_time = time.time()
            while time.time() - start_time < wait_time:
                self.cancellation_token.throw_if_cancelled()
                time.sleep(0.1)
            
            self.logger.debug("Ожидание завершено")
            return True
            
        except ValueError:
            self.logger.error(f"Неверный формат времени в wait команде: {command}")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка обработки wait команды '{command}': {e}")
            return False
    
    def _send_and_wait_command(self, command: str) -> bool:
        """Отправить команду и дождаться ответа"""
        try:
            # Отправляем команду
            if not self.serial_manager.send_command(command):
                self.logger.error(f"Не удалось отправить команду: {command}")
                return False
            
            self.logger.debug(f"Команда отправлена: {command}")
            self._notify_command_executed(command, True)
            
            # Ждем ответа (здесь должна быть логика ожидания)
            # Пока просто возвращаем True
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки команды '{command}': {e}")
            self._notify_command_executed(command, False)
            return False
    
    def _evaluate_condition(self, condition: str) -> bool:
        """Вычислить значение условия"""
        try:
            # Простая реализация - проверяем флаги
            # В реальной системе здесь должна быть более сложная логика
            
            # Убираем лишние пробелы
            condition = condition.strip()
            
            # Проверяем простые условия с флагами
            if condition.startswith("flag:"):
                flag_name = condition[5:].strip()
                return self.flag_manager.get_flag(flag_name, False)
            
            # Проверяем отрицание
            if condition.startswith("!"):
                flag_name = condition[1:].strip()
                return not self.flag_manager.get_flag(flag_name, False)
            
            # По умолчанию считаем условие истинным
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка вычисления условия '{condition}': {e}")
            return False
    
    def set_callbacks(self, 
                     on_command_executed: Optional[Callable[[str, bool], None]] = None,
                     on_progress_updated: Optional[Callable[[int, int], None]] = None,
                     on_sequence_finished: Optional[Callable[[bool, str], None]] = None):
        """Установить callbacks для событий"""
        self.on_command_executed = on_command_executed
        self.on_progress_updated = on_progress_updated
        self.on_sequence_finished = on_sequence_finished
    
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
    
    def cancel_execution(self):
        """Отменить выполнение последовательности"""
        if self.cancellation_token:
            self.cancellation_token.cancel()
            self.logger.info("Выполнение последовательности отменено")
    
    def reset_state(self):
        """Сбросить состояние исполнителя"""
        self.conditional_state = ConditionalState()
        if self.cancellation_token:
            self.cancellation_token.reset()
        self.logger.debug("Состояние исполнителя сброшено")

