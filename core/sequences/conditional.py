"""
Модуль для обработки условной логики последовательностей.

Содержит класс ConditionalProcessor для управления условным выполнением
команд с поддержкой вложенных блоков и сложных условий.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from .types import ConditionalState, CommandType
from .flags import FlagManager


class ConditionalProcessor:
    """Обработчик условной логики для последовательностей команд"""
    
    def __init__(self, flag_manager: FlagManager):
        self.flag_manager = flag_manager
        self.logger = logging.getLogger(__name__)
        
        # Состояние условного выполнения
        self.conditional_state = ConditionalState()
        
        # Callbacks для событий
        self.on_conditional_entered: Optional[Callable[[str, bool], None]] = None
        self.on_conditional_exited: Optional[Callable[[str], None]] = None
        self.on_condition_evaluated: Optional[Callable[[str, bool], None]] = None
    
    def process_conditional_command(self, command: str) -> bool:
        """
        Обработать условную команду.
        
        Args:
            command: Строка команды для обработки
            
        Returns:
            True если команда обработана успешно
        """
        try:
            if command.lower().startswith("if"):
                return self._handle_if_command(command)
            elif command.lower() == "else":
                return self._handle_else_command(command)
            elif command.lower() == "endif":
                return self._handle_endif_command(command)
            else:
                self.logger.warning(f"Неизвестная условная команда: {command}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки условной команды '{command}': {e}")
            return False
    
    def is_in_conditional_block(self) -> bool:
        """Проверить, находимся ли мы в условном блоке"""
        return self.conditional_state.in_conditional_block
    
    def should_skip_commands(self) -> bool:
        """Проверить, нужно ли пропускать команды"""
        return self.conditional_state.skip_until_endif
    
    def get_current_condition(self) -> bool:
        """Получить текущее значение условия"""
        return self.conditional_state.current_condition
    
    def _handle_if_command(self, command: str) -> bool:
        """Обработать команду if"""
        try:
            # Убираем 'if' и парсим условие
            condition = command[2:].strip()
            if not condition:
                self.logger.error("Условие не может быть пустым")
                return False
            
            # Вычисляем значение условия
            result = self._evaluate_condition(condition)
            
            # Обновляем состояние
            self.conditional_state.in_conditional_block = True
            self.conditional_state.current_condition = result
            self.conditional_state.skip_until_endif = not result
            self.conditional_state.condition_stack.append(result)
            
            self.logger.debug(f"Вход в условный блок: '{condition}' = {result}")
            
            # Уведомляем о событии
            self._notify_conditional_entered(condition, result)
            self._notify_condition_evaluated(condition, result)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки if команды: {e}")
            return False
    
    def _handle_else_command(self, command: str) -> bool:
        """Обработать команду else"""
        try:
            if not self.conditional_state.in_conditional_block:
                self.logger.error("else без соответствующего if")
                return False
            
            # Инвертируем текущее условие для else блока
            self.conditional_state.current_condition = not self.conditional_state.current_condition
            self.conditional_state.skip_until_endif = not self.conditional_state.current_condition
            
            self.logger.debug(f"else блок: условие = {self.conditional_state.current_condition}")
            
            # Уведомляем о событии
            self._notify_condition_evaluated("else", self.conditional_state.current_condition)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки else команды: {e}")
            return False
    
    def _handle_endif_command(self, command: str) -> bool:
        """Обработать команду endif"""
        try:
            if not self.conditional_state.in_conditional_block:
                self.logger.error("endif без соответствующего if")
                return False
            
            # Выходим из условного блока
            if self.conditional_state.condition_stack:
                self.conditional_state.condition_stack.pop()
            
            if not self.conditional_state.condition_stack:
                self.conditional_state.in_conditional_block = False
                self.conditional_state.skip_until_endif = False
                self.conditional_state.current_condition = True
            
            self.logger.debug("Выход из условного блока")
            
            # Уведомляем о событии
            self._notify_conditional_exited("endif")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки endif команды: {e}")
            return False
    
    def _evaluate_condition(self, condition: str) -> bool:
        """
        Вычислить значение условия.
        
        Args:
            condition: Строка условия для вычисления
            
        Returns:
            True если условие истинно
        """
        try:
            # Убираем лишние пробелы
            condition = condition.strip()
            
            # Проверяем простые условия с флагами
            if condition.startswith("flag:"):
                flag_name = condition[5:].strip()
                result = self.flag_manager.get_flag(flag_name, False)
                self.logger.debug(f"Флаг '{flag_name}' = {result}")
                return result
            
            # Проверяем отрицание
            if condition.startswith("!"):
                flag_name = condition[1:].strip()
                result = not self.flag_manager.get_flag(flag_name, False)
                self.logger.debug(f"Отрицание флага '{flag_name}' = {result}")
                return result
            
            # Проверяем сложные условия
            if "&&" in condition:
                return self._evaluate_and_condition(condition)
            
            if "||" in condition:
                return self._evaluate_or_condition(condition)
            
            # Проверяем сравнения
            if any(op in condition for op in ["==", "!=", "<", ">", "<=", ">="]):
                return self._evaluate_comparison(condition)
            
            # По умолчанию считаем условие истинным
            self.logger.debug(f"Условие '{condition}' принято как истинное по умолчанию")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка вычисления условия '{condition}': {e}")
            return False
    
    def _evaluate_and_condition(self, condition: str) -> bool:
        """Вычислить условие с логическим И (&&)"""
        try:
            parts = [part.strip() for part in condition.split("&&")]
            for part in parts:
                if not self._evaluate_condition(part):
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Ошибка вычисления AND условия '{condition}': {e}")
            return False
    
    def _evaluate_or_condition(self, condition: str) -> bool:
        """Вычислить условие с логическим ИЛИ (||)"""
        try:
            parts = [part.strip() for part in condition.split("||")]
            for part in parts:
                if self._evaluate_condition(part):
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Ошибка вычисления OR условия '{condition}': {e}")
            return False
    
    def _evaluate_comparison(self, condition: str) -> bool:
        """Вычислить условие сравнения"""
        try:
            # Простая реализация для сравнения флагов
            # В реальной системе здесь должна быть более сложная логика
            
            if "==" in condition:
                left, right = condition.split("==", 1)
                left = left.strip()
                right = right.strip()
                
                if left.startswith("flag:"):
                    flag_name = left[5:].strip()
                    flag_value = self.flag_manager.get_flag(flag_name, False)
                    return str(flag_value).lower() == right.lower()
                
                return left == right
            
            elif "!=" in condition:
                left, right = condition.split("!=", 1)
                left = left.strip()
                right = right.strip()
                
                if left.startswith("flag:"):
                    flag_name = left[5:].strip()
                    flag_value = self.flag_manager.get_flag(flag_name, False)
                    return str(flag_value).lower() != right.lower()
                
                return left != right
            
            # Для других операторов пока возвращаем True
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка вычисления сравнения '{condition}': {e}")
            return False
    
    def set_callbacks(self, 
                     on_conditional_entered: Optional[Callable[[str, bool], None]] = None,
                     on_conditional_exited: Optional[Callable[[str], None]] = None,
                     on_condition_evaluated: Optional[Callable[[str, bool], None]] = None):
        """Установить callbacks для событий"""
        self.on_conditional_entered = on_conditional_entered
        self.on_conditional_exited = on_conditional_exited
        self.on_condition_evaluated = on_condition_evaluated
    
    def _notify_conditional_entered(self, condition: str, result: bool):
        """Уведомить о входе в условный блок"""
        if self.on_conditional_entered:
            try:
                self.on_conditional_entered(condition, result)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_conditional_entered: {e}")
    
    def _notify_conditional_exited(self, command: str):
        """Уведомить о выходе из условного блока"""
        if self.on_conditional_exited:
            try:
                self.on_conditional_exited(command)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_conditional_exited: {e}")
    
    def _notify_condition_evaluated(self, condition: str, result: bool):
        """Уведомить о вычислении условия"""
        if self.on_condition_evaluated:
            try:
                self.on_condition_evaluated(condition, result)
            except Exception as e:
                self.logger.error(f"Ошибка в callback on_condition_evaluated: {e}")
    
    def reset_state(self):
        """Сбросить состояние условного процессора"""
        self.conditional_state = ConditionalState()
        self.logger.debug("Состояние условного процессора сброшено")
    
    def get_conditional_stack_depth(self) -> int:
        """Получить глубину стека условных блоков"""
        return len(self.conditional_state.condition_stack)
    
    def is_balanced(self) -> bool:
        """Проверить, сбалансированы ли условные блоки"""
        return not self.conditional_state.in_conditional_block

