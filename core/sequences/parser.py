"""
Модуль для парсинга команд последовательностей.

Содержит класс SequenceParser для анализа и разбора команд
различных типов с поддержкой условной логики.
"""

import re
import logging
import threading
import time
from typing import Dict, Any, Optional, Tuple
from .types import CommandType, ValidationResult


class RegexTimeoutError(Exception):
    """Исключение для таймаутов regex операций"""
    pass


class SequenceParser:
    """Парсер команд последовательностей"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.max_wait_time = 3600  # 1 час по умолчанию
        self.regex_timeout = 1.0  # 1 секунда таймаут для regex
        
        # Регулярные выражения для парсинга с компиляцией
        self.patterns = {
            'wait': re.compile(r'^wait\s+(\d+(?:\.\d+)?)$', re.IGNORECASE),
            'conditional_if': re.compile(r'^if\s+(.+)$', re.IGNORECASE),
            'conditional_else': re.compile(r'^else$', re.IGNORECASE),
            'conditional_endif': re.compile(r'^endif$', re.IGNORECASE),
            'stop_if_not': re.compile(r'^stop_if_not\s+(.+)$', re.IGNORECASE),
            'multizone': re.compile(r'^multizone\s+(.+)$', re.IGNORECASE),
            'sequence': re.compile(r'^sequence\s+(.+)$', re.IGNORECASE),
            'button': re.compile(r'^button\s+(.+)$', re.IGNORECASE),
            'tagged': re.compile(r'^tagged\s+(.+)$', re.IGNORECASE)
        }
        
        # Лимиты для защиты от атак
        self.max_pattern_length = 1000  # Максимальная длина паттерна
        self.max_match_groups = 10      # Максимальное количество групп
        
        # Флаг для отслеживания таймаутов
        self._timeout_flag = False
        self._timeout_lock = threading.Lock()
    
    def _safe_regex_match(self, pattern: re.Pattern, string: str) -> Optional[re.Match]:
        """
        Безопасное выполнение regex с таймаутом.
        
        Args:
            pattern: Скомпилированный regex паттерн
            string: Строка для поиска
            
        Returns:
            Match объект или None
            
        Raises:
            RegexTimeoutError: При превышении таймаута
        """
        # Проверяем длину строки
        if len(string) > self.max_pattern_length:
            self.logger.warning(f"Строка слишком длинная для regex: {len(string)} > {self.max_pattern_length}")
            return None
        
        # Сбрасываем флаг таймаута
        with self._timeout_lock:
            self._timeout_flag = False
        
        result = [None]  # Используем список для передачи результата между потоками
        
        def regex_operation():
            """Выполнение regex операции в отдельном потоке"""
            try:
                result[0] = pattern.match(string)
            except Exception as e:
                self.logger.error(f"Ошибка regex операции: {e}")
                result[0] = None
        
        def timeout_handler():
            """Обработчик таймаута"""
            with self._timeout_lock:
                self._timeout_flag = True
        
        try:
            # Запускаем regex операцию в отдельном потоке
            regex_thread = threading.Thread(target=regex_operation)
            regex_thread.daemon = True
            regex_thread.start()
            
            # Запускаем таймер
            timer = threading.Timer(self.regex_timeout, timeout_handler)
            timer.start()
            
            # Ждем завершения regex операции или таймаута
            regex_thread.join(timeout=self.regex_timeout)
            timer.cancel()
            
            # Проверяем таймаут
            with self._timeout_lock:
                if self._timeout_flag:
                    self.logger.error(f"Regex таймаут для паттерна: {pattern.pattern}")
                    raise RegexTimeoutError("Regex операция превысила таймаут")
            
            return result[0]
                
        except RegexTimeoutError:
            raise
        except Exception as e:
            self.logger.error(f"Ошибка regex операции: {e}")
            return None
    
    def parse_command(self, command: str) -> ValidationResult:
        """
        Парсить команду и определить её тип.
        
        Args:
            command: Строка команды для парсинга
            
        Returns:
            ValidationResult с типом команды и распарсенными данными
        """
        if not command or not command.strip():
            return ValidationResult(
                False, 
                "Пустая команда", 
                CommandType.UNKNOWN
            )
        
        command = command.strip()
        
        # Проверяем длину команды
        if len(command) > self.max_pattern_length:
            return ValidationResult(
                False,
                f"Команда слишком длинная (максимум {self.max_pattern_length} символов)",
                CommandType.UNKNOWN
            )
        
        # Проверяем wait команду
        if command.lower().startswith("wait"):
            return self._parse_wait_command(command)
        
        # Проверяем условные команды
        if command.lower().startswith("if"):
            return self._parse_conditional_if(command)
        
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
            return self._parse_stop_if_not(command)
        
        # Проверяем multizone команду
        if command.lower().startswith("multizone"):
            return self._parse_multizone_command(command)
        
        # Проверяем sequence команду
        if command.lower().startswith("sequence"):
            return self._parse_sequence_command(command)
        
        # Проверяем button команду
        if command.lower().startswith("button"):
            return self._parse_button_command(command)
        
        # Проверяем tagged команду
        if command.lower().startswith("tagged"):
            return self._parse_tagged_command(command)
        
        # Обычная команда
        return ValidationResult(
            True, 
            "", 
            CommandType.REGULAR, 
            {"command": command}
        )
    
    def _parse_wait_command(self, command: str) -> ValidationResult:
        """Парсить wait команду"""
        try:
            # Используем безопасный regex с таймаутом
            match = self._safe_regex_match(self.patterns['wait'], command)
            if not match:
                return ValidationResult(
                    False, 
                    "Неверный синтаксис wait команды. Используйте: wait <время>", 
                    CommandType.WAIT
                )
            
            wait_time = float(match.group(1))
            
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
            
        except RegexTimeoutError:
            return ValidationResult(
                False,
                "Таймаут при парсинге wait команды",
                CommandType.WAIT
            )
        except ValueError:
            return ValidationResult(
                False, 
                "Неверный формат времени в wait команде", 
                CommandType.WAIT
            )
        except Exception as e:
            return ValidationResult(
                False,
                f"Ошибка парсинга wait команды: {e}",
                CommandType.WAIT
            )
    
    def _parse_conditional_if(self, command: str) -> ValidationResult:
        """Парсить условную команду if"""
        try:
            # Используем безопасный regex с таймаутом
            match = self._safe_regex_match(self.patterns['conditional_if'], command)
            if not match:
                return ValidationResult(
                    False, 
                    "Неверный синтаксис if команды", 
                    CommandType.CONDITIONAL_IF
                )
            
            condition = match.group(1).strip()
            if not condition:
                return ValidationResult(
                    False, 
                    "Условие не может быть пустым", 
                    CommandType.CONDITIONAL_IF
                )
            
            # Проверяем количество групп
            if len(match.groups()) > self.max_match_groups:
                return ValidationResult(
                    False,
                    f"Слишком много групп в условии (максимум {self.max_match_groups})",
                    CommandType.CONDITIONAL_IF
                )
            
            return ValidationResult(
                True, 
                "", 
                CommandType.CONDITIONAL_IF, 
                {"condition": condition}
            )
            
        except RegexTimeoutError:
            return ValidationResult(
                False,
                "Таймаут при парсинге if команды",
                CommandType.CONDITIONAL_IF
            )
        except Exception as e:
            return ValidationResult(
                False, 
                f"Ошибка парсинга условной команды: {e}", 
                CommandType.CONDITIONAL_IF
            )
    
    def _parse_stop_if_not(self, command: str) -> ValidationResult:
        """Парсить команду stop_if_not"""
        try:
            # Используем безопасный regex с таймаутом
            match = self._safe_regex_match(self.patterns['stop_if_not'], command)
            if not match:
                return ValidationResult(
                    False, 
                    "Неверный синтаксис stop_if_not команды", 
                    CommandType.STOP_IF_NOT
                )
            
            condition = match.group(1).strip()
            if not condition:
                return ValidationResult(
                    False, 
                    "Условие не может быть пустым", 
                    CommandType.STOP_IF_NOT
                )
            
            # Проверяем количество групп
            if len(match.groups()) > self.max_match_groups:
                return ValidationResult(
                    False,
                    f"Слишком много групп в условии (максимум {self.max_match_groups})",
                    CommandType.STOP_IF_NOT
                )
            
            return ValidationResult(
                True, 
                "", 
                CommandType.STOP_IF_NOT, 
                {"condition": condition}
            )
            
        except RegexTimeoutError:
            return ValidationResult(
                False,
                "Таймаут при парсинге stop_if_not команды",
                CommandType.STOP_IF_NOT
            )
        except Exception as e:
            return ValidationResult(
                False,
                f"Ошибка парсинга stop_if_not команды: {e}",
                CommandType.STOP_IF_NOT
            )
    
    def _parse_multizone_command(self, command: str) -> ValidationResult:
        """Парсить multizone команду"""
        try:
            # Используем безопасный regex с таймаутом
            match = self._safe_regex_match(self.patterns['multizone'], command)
            if not match:
                return ValidationResult(
                    False, 
                    "Неверный синтаксис multizone команды", 
                    CommandType.MULTIZONE
                )
            
            params = match.group(1).strip()
            if not params:
                return ValidationResult(
                    False, 
                    "Параметры multizone не могут быть пустыми", 
                    CommandType.MULTIZONE
                )
            
            # Проверяем количество групп
            if len(match.groups()) > self.max_match_groups:
                return ValidationResult(
                    False,
                    f"Слишком много групп в multizone команде (максимум {self.max_match_groups})",
                    CommandType.MULTIZONE
                )
            
            return ValidationResult(
                True, 
                "", 
                CommandType.MULTIZONE, 
                {"params": params}
            )
            
        except RegexTimeoutError:
            return ValidationResult(
                False,
                "Таймаут при парсинге multizone команды",
                CommandType.MULTIZONE
            )
        except Exception as e:
            return ValidationResult(
                False, 
                f"Ошибка парсинга multizone команды: {e}", 
                CommandType.MULTIZONE
            )
    
    def _parse_sequence_command(self, command: str) -> ValidationResult:
        """Парсить sequence команду"""
        try:
            # Используем безопасный regex с таймаутом
            match = self._safe_regex_match(self.patterns['sequence'], command)
            if not match:
                return ValidationResult(
                    False, 
                    "Неверный синтаксис sequence команды", 
                    CommandType.SEQUENCE
                )
            
            sequence_name = match.group(1).strip()
            if not sequence_name:
                return ValidationResult(
                    False, 
                    "Имя последовательности не может быть пустым", 
                    CommandType.SEQUENCE
                )
            
            # Проверяем количество групп
            if len(match.groups()) > self.max_match_groups:
                return ValidationResult(
                    False,
                    f"Слишком много групп в sequence команде (максимум {self.max_match_groups})",
                    CommandType.SEQUENCE
                )
            
            return ValidationResult(
                True, 
                "", 
                CommandType.SEQUENCE, 
                {"sequence_name": sequence_name}
            )
            
        except RegexTimeoutError:
            return ValidationResult(
                False,
                "Таймаут при парсинге sequence команды",
                CommandType.SEQUENCE
            )
        except Exception as e:
            return ValidationResult(
                False, 
                f"Ошибка парсинга sequence команды: {e}", 
                CommandType.SEQUENCE
            )
    
    def _parse_button_command(self, command: str) -> ValidationResult:
        """Парсить button команду"""
        try:
            # Используем безопасный regex с таймаутом
            match = self._safe_regex_match(self.patterns['button'], command)
            if not match:
                return ValidationResult(
                    False, 
                    "Неверный синтаксис button команды", 
                    CommandType.BUTTON
                )
            
            button_params = match.group(1).strip()
            if not button_params:
                return ValidationResult(
                    False, 
                    "Параметры кнопки не могут быть пустыми", 
                    CommandType.BUTTON
                )
            
            # Проверяем количество групп
            if len(match.groups()) > self.max_match_groups:
                return ValidationResult(
                    False,
                    f"Слишком много групп в button команде (максимум {self.max_match_groups})",
                    CommandType.BUTTON
                )
            
            return ValidationResult(
                True, 
                "", 
                CommandType.BUTTON, 
                {"button_params": button_params}
            )
            
        except RegexTimeoutError:
            return ValidationResult(
                False,
                "Таймаут при парсинге button команды",
                CommandType.BUTTON
            )
        except Exception as e:
            return ValidationResult(
                False, 
                f"Ошибка парсинга button команды: {e}", 
                CommandType.BUTTON
            )
    
    def _parse_tagged_command(self, command: str) -> ValidationResult:
        """Парсить tagged команду"""
        try:
            # Используем безопасный regex с таймаутом
            match = self._safe_regex_match(self.patterns['tagged'], command)
            if not match:
                return ValidationResult(
                    False, 
                    "Неверный синтаксис tagged команды", 
                    CommandType.TAGGED
                )
            
            tag = match.group(1).strip()
            if not tag:
                return ValidationResult(
                    False, 
                    "Тег не может быть пустым", 
                    CommandType.TAGGED
                )
            
            # Проверяем количество групп
            if len(match.groups()) > self.max_match_groups:
                return ValidationResult(
                    False,
                    f"Слишком много групп в tagged команде (максимум {self.max_match_groups})",
                    CommandType.TAGGED
                )
            
            return ValidationResult(
                True, 
                "", 
                CommandType.TAGGED, 
                {"tag": tag}
            )
            
        except RegexTimeoutError:
            return ValidationResult(
                False,
                "Таймаут при парсинге tagged команды",
                CommandType.TAGGED
            )
        except Exception as e:
            return ValidationResult(
                False, 
                f"Ошибка парсинга tagged команды: {e}", 
                CommandType.TAGGED
            )
    
    def set_max_wait_time(self, max_time: float) -> None:
        """Установить максимальное время ожидания"""
        if max_time > 0:
            self.max_wait_time = max_time
        else:
            self.logger.warning("Максимальное время ожидания должно быть положительным")
    
    def get_max_wait_time(self) -> float:
        """Получить максимальное время ожидания"""
        return self.max_wait_time
    
    def set_regex_timeout(self, timeout: float) -> None:
        """Установить таймаут для regex операций"""
        if timeout > 0:
            self.regex_timeout = timeout
            self.logger.info(f"Regex таймаут установлен: {timeout} сек")
        else:
            self.logger.warning("Regex таймаут должен быть положительным")
    
    def get_regex_timeout(self) -> float:
        """Получить текущий regex таймаут"""
        return self.regex_timeout
    
    def set_max_pattern_length(self, max_length: int) -> None:
        """Установить максимальную длину паттерна для защиты от атак"""
        if max_length > 0:
            self.max_pattern_length = max_length
            self.logger.info(f"Максимальная длина паттерна установлена: {max_length}")
        else:
            self.logger.warning("Максимальная длина паттерна должна быть положительной")
    
    def get_max_pattern_length(self) -> int:
        """Получить максимальную длину паттерна"""
        return self.max_pattern_length
    
    def set_max_match_groups(self, max_groups: int) -> None:
        """Установить максимальное количество групп для защиты от атак"""
        if max_groups > 0:
            self.max_match_groups = max_groups
            self.logger.info(f"Максимальное количество групп установлено: {max_groups}")
        else:
            self.logger.warning("Максимальное количество групп должно быть положительным")
    
    def get_max_match_groups(self) -> int:
        """Получить максимальное количество групп"""
        return self.max_match_groups
    
    def get_security_info(self) -> Dict[str, Any]:
        """Получить информацию о настройках безопасности"""
        return {
            'regex_timeout': self.regex_timeout,
            'max_pattern_length': self.max_pattern_length,
            'max_match_groups': self.max_match_groups,
            'max_wait_time': self.max_wait_time,
            'compiled_patterns': len(self.patterns),
            'security_enabled': True
        }
