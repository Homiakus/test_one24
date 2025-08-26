"""
Модуль для валидации команд последовательностей.

Содержит класс SequenceValidator для проверки корректности
команд и последовательностей.
"""

import logging
from typing import List, Tuple, Dict, Any
from .types import CommandType, ValidationResult
from .flags import FlagManager


class SequenceValidator:
    """Валидатор команд последовательностей"""
    
    def __init__(self, flag_manager: FlagManager):
        self.flag_manager = flag_manager
        self.logger = logging.getLogger(__name__)
        
        # Максимальные значения для валидации
        self.max_wait_time = 3600  # 1 час
        self.max_command_length = 1000  # 1000 символов
        self.max_sequence_length = 10000  # 10000 команд
    
    def validate_command(self, command: str) -> ValidationResult:
        """
        Валидировать отдельную команду.
        
        Args:
            command: Строка команды для валидации
            
        Returns:
            ValidationResult с результатом валидации
        """
        if not command or not command.strip():
            return ValidationResult(
                False, 
                "Пустая команда", 
                CommandType.UNKNOWN
            )
        
        # Проверяем длину команды
        if len(command) > self.max_command_length:
            return ValidationResult(
                False, 
                f"Команда слишком длинная (максимум {self.max_command_length} символов)", 
                CommandType.UNKNOWN
            )
        
        # Проверяем wait команду
        if command.lower().startswith("wait"):
            return self._validate_wait_command(command)
        
        # Проверяем условные команды
        if command.lower().startswith("if"):
            return self._validate_conditional_if(command)
        
        if command.lower() == "else":
            return ValidationResult(
                True, 
                "", 
                CommandType.CONDITIONAL_ELSE, 
                {}
            )
        
        if command.lower() == "endif":
            return ValidationResult(
                True, 
                "", 
                CommandType.CONDITIONAL_ENDIF, 
                {}
            )
        
        # Проверяем stop_if_not команду
        if command.lower().startswith("stop_if_not"):
            return self._validate_stop_if_not(command)
        
        # Проверяем multizone команду
        if command.lower().startswith("multizone"):
            return self._validate_multizone_command(command)
        
        # Проверяем sequence команду
        if command.lower().startswith("sequence"):
            return self._validate_sequence_command(command)
        
        # Проверяем button команду
        if command.lower().startswith("button"):
            return self._validate_button_command(command)
        
        # Проверяем tagged команду
        if command.lower().startswith("tagged"):
            return self._validate_tagged_command(command)
        
        # Обычная команда
        return ValidationResult(
            True, 
            "", 
            CommandType.REGULAR, 
            {"command": command}
        )
    
    def validate_sequence(self, sequence: List[str]) -> Tuple[bool, List[str]]:
        """
        Валидировать последовательность команд.
        
        Args:
            sequence: Список команд для валидации
            
        Returns:
            Tuple (is_valid, errors) где errors - список ошибок
        """
        if not sequence:
            return False, ["Последовательность не может быть пустой"]
        
        if len(sequence) > self.max_sequence_length:
            return False, [f"Последовательность слишком длинная (максимум {self.max_sequence_length} команд)"]
        
        errors = []
        conditional_stack = []
        
        for i, command in enumerate(sequence):
            result = self.validate_command(command)
            if not result.is_valid:
                errors.append(f"Команда {i+1}: {result.error_message}")
                continue
            
            # Проверяем баланс условных блоков
            if result.command_type == CommandType.CONDITIONAL_IF:
                conditional_stack.append(i)
            elif result.command_type == CommandType.CONDITIONAL_ENDIF:
                if not conditional_stack:
                    errors.append(f"Команда {i+1}: endif без соответствующего if")
                else:
                    conditional_stack.pop()
        
        # Проверяем незакрытые условные блоки
        for block_start in conditional_stack:
            errors.append(f"Незакрытый условный блок, начинающийся с команды {block_start + 1}")
        
        return len(errors) == 0, errors
    
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
    
    def _validate_conditional_if(self, command: str) -> ValidationResult:
        """Валидировать условную команду if"""
        try:
            # Убираем 'if' и проверяем условие
            condition = command[2:].strip()
            if not condition:
                return ValidationResult(
                    False, 
                    "Условие не может быть пустым", 
                    CommandType.CONDITIONAL_IF
                )
            
            # Проверяем, что условие содержит допустимые символы
            if not self._is_valid_condition(condition):
                return ValidationResult(
                    False, 
                    "Условие содержит недопустимые символы", 
                    CommandType.CONDITIONAL_IF
                )
            
            return ValidationResult(
                True, 
                "", 
                CommandType.CONDITIONAL_IF, 
                {"condition": condition}
            )
            
        except Exception as e:
            return ValidationResult(
                False, 
                f"Ошибка валидации условной команды: {e}", 
                CommandType.CONDITIONAL_IF
            )
    
    def _validate_stop_if_not(self, command: str) -> ValidationResult:
        """Валидировать команду stop_if_not"""
        try:
            # Убираем 'stop_if_not' и проверяем условие
            condition = command[11:].strip()
            if not condition:
                return ValidationResult(
                    False, 
                    "Условие не может быть пустым", 
                    CommandType.STOP_IF_NOT
                )
            
            if not self._is_valid_condition(condition):
                return ValidationResult(
                    False, 
                    "Условие содержит недопустимые символы", 
                    CommandType.STOP_IF_NOT
                )
            
            return ValidationResult(
                True, 
                "", 
                CommandType.STOP_IF_NOT, 
                {"condition": condition}
            )
            
        except Exception as e:
            return ValidationResult(
                False, 
                f"Ошибка валидации команды stop_if_not: {e}", 
                CommandType.STOP_IF_NOT
            )
    
    def _validate_multizone_command(self, command: str) -> ValidationResult:
        """Валидировать multizone команду"""
        try:
            # Убираем 'multizone' и проверяем параметры
            params = command[9:].strip()
            if not params:
                return ValidationResult(
                    False, 
                    "Параметры multizone не могут быть пустыми", 
                    CommandType.MULTIZONE
                )
            
            # Проверяем формат параметров multizone
            if not self._is_valid_multizone_params(params):
                return ValidationResult(
                    False, 
                    "Неверный формат параметров multizone", 
                    CommandType.MULTIZONE
                )
            
            return ValidationResult(
                True, 
                "", 
                CommandType.MULTIZONE, 
                {"params": params}
            )
            
        except Exception as e:
            return ValidationResult(
                False, 
                f"Ошибка валидации multizone команды: {e}", 
                CommandType.MULTIZONE
            )
    
    def _validate_sequence_command(self, command: str) -> ValidationResult:
        """Валидировать sequence команду"""
        try:
            # Убираем 'sequence' и проверяем имя последовательности
            sequence_name = command[8:].strip()
            if not sequence_name:
                return ValidationResult(
                    False, 
                    "Имя последовательности не может быть пустым", 
                    CommandType.SEQUENCE
                )
            
            # Проверяем, что имя содержит только допустимые символы
            if not self._is_valid_sequence_name(sequence_name):
                return ValidationResult(
                    False, 
                    "Имя последовательности содержит недопустимые символы", 
                    CommandType.SEQUENCE
                )
            
            return ValidationResult(
                True, 
                "", 
                CommandType.SEQUENCE, 
                {"sequence_name": sequence_name}
            )
            
        except Exception as e:
            return ValidationResult(
                False, 
                f"Ошибка валидации sequence команды: {e}", 
                CommandType.SEQUENCE
            )
    
    def _validate_button_command(self, command: str) -> ValidationResult:
        """Валидировать button команду"""
        try:
            # Убираем 'button' и проверяем параметры кнопки
            button_params = command[6:].strip()
            if not button_params:
                return ValidationResult(
                    False, 
                    "Параметры кнопки не могут быть пустыми", 
                    CommandType.BUTTON
                )
            
            return ValidationResult(
                True, 
                "", 
                CommandType.BUTTON, 
                {"button_params": button_params}
            )
            
        except Exception as e:
            return ValidationResult(
                False, 
                f"Ошибка валидации button команды: {e}", 
                CommandType.BUTTON
            )
    
    def _validate_tagged_command(self, command: str) -> ValidationResult:
        """Валидировать tagged команду"""
        try:
            # Убираем 'tagged' и проверяем тег
            tag = command[6:].strip()
            if not tag:
                return ValidationResult(
                    False, 
                    "Тег не может быть пустым", 
                    CommandType.TAGGED
                )
            
            # Проверяем, что тег содержит только допустимые символы
            if not self._is_valid_tag(tag):
                return ValidationResult(
                    False, 
                    "Тег содержит недопустимые символы", 
                    CommandType.TAGGED
                )
            
            return ValidationResult(
                True, 
                "", 
                CommandType.TAGGED, 
                {"tag": tag}
            )
            
        except Exception as e:
            return ValidationResult(
                False, 
                f"Ошибка валидации tagged команды: {e}", 
                CommandType.TAGGED
            )
    
    def _is_valid_condition(self, condition: str) -> bool:
        """Проверить, что условие содержит допустимые символы"""
        # Разрешаем буквы, цифры, пробелы, скобки, операторы сравнения
        import re
        pattern = r'^[a-zA-Z0-9\s\(\)<>=!&\|]+$'
        return bool(re.match(pattern, condition))
    
    def _is_valid_multizone_params(self, params: str) -> bool:
        """Проверить, что параметры multizone корректны"""
        # Простая проверка - параметры должны содержать только допустимые символы
        import re
        pattern = r'^[a-zA-Z0-9\s,]+$'
        return bool(re.match(pattern, params))
    
    def _is_valid_sequence_name(self, name: str) -> bool:
        """Проверить, что имя последовательности корректно"""
        # Имя должно содержать только буквы, цифры, подчеркивания и дефисы
        import re
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, name))
    
    def _is_valid_tag(self, tag: str) -> bool:
        """Проверить, что тег корректный"""
        # Тег должен содержать только буквы, цифры, подчеркивания и дефисы
        import re
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, tag))
    
    def set_max_wait_time(self, max_time: float) -> None:
        """Установить максимальное время ожидания"""
        if max_time > 0:
            self.max_wait_time = max_time
        else:
            self.logger.warning("Максимальное время ожидания должно быть положительным")
    
    def set_max_command_length(self, max_length: int) -> None:
        """Установить максимальную длину команды"""
        if max_length > 0:
            self.max_command_length = max_length
        else:
            self.logger.warning("Максимальная длина команды должна быть положительной")
    
    def set_max_sequence_length(self, max_length: int) -> None:
        """Установить максимальную длину последовательности"""
        if max_length > 0:
            self.max_sequence_length = max_length
        else:
            self.logger.warning("Максимальная длина последовательности должна быть положительной")
