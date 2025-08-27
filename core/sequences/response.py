"""
Модуль для анализа ответов от устройств.

Содержит класс ResponseAnalyzer для анализа и обработки
ответов от устройств с поддержкой различных форматов.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from .types import SequenceKeywords


class ResponseAnalyzer:
    """Анализатор ответов от устройств"""
    
    def __init__(self, keywords: Optional[SequenceKeywords] = None):
        self.keywords = keywords or SequenceKeywords()
        self.logger = logging.getLogger(__name__)
        
        # Регулярные выражения для анализа ответов
        self.patterns = {
            'complete': re.compile(r'\b(complete|completed|done|COMPLETE)\b', re.IGNORECASE),
            'received': re.compile(r'\b(received|recv|ack)\b', re.IGNORECASE),
            'error': re.compile(r'\b(err|error|fail|failure|failed)\b', re.IGNORECASE),
            'timeout': re.compile(r'\b(timeout|time_out|timed_out)\b', re.IGNORECASE),
            'busy': re.compile(r'\b(busy|BUSY|processing)\b', re.IGNORECASE)
        }
        
        # Статистика ответов
        self.response_stats = {
            'total_responses': 0,
            'successful_responses': 0,
            'error_responses': 0,
            'timeout_responses': 0,
            'busy_responses': 0
        }
    
    def analyze_response(self, response: str) -> Dict[str, Any]:
        """
        Проанализировать ответ от устройства.
        
        Args:
            response: Строка ответа для анализа
            
        Returns:
            Словарь с результатами анализа
        """
        if not response or not response.strip():
            return self._create_analysis_result("empty", "Пустой ответ", False)
        
        response = response.strip()
        self.response_stats['total_responses'] += 1
        
        try:
            # Проверяем различные типы ответов
            if self._is_complete_response(response):
                self.response_stats['successful_responses'] += 1
                return self._create_analysis_result("complete", "Команда выполнена успешно", True)
            
            if self._is_error_response(response):
                self.response_stats['error_responses'] += 1
                return self._create_analysis_result("error", f"Ошибка: {response}", False)
            
            if self._is_timeout_response(response):
                self.response_stats['timeout_responses'] += 1
                return self._create_analysis_result("timeout", "Превышено время ожидания", False)
            
            if self._is_busy_response(response):
                self.response_stats['busy_responses'] += 1
                return self._create_analysis_result("busy", "Устройство занято", False)
            
            if self._is_received_response(response):
                return self._create_analysis_result("received", "Команда получена", True)
            
            # Анализируем числовые ответы
            numeric_result = self._analyze_numeric_response(response)
            if numeric_result:
                return numeric_result
            
            # Анализируем структурированные ответы
            structured_result = self._analyze_structured_response(response)
            if structured_result:
                return structured_result
            
            # По умолчанию считаем ответ успешным
            self.response_stats['successful_responses'] += 1
            return self._create_analysis_result("unknown", f"Неизвестный формат ответа: {response}", True)
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа ответа '{response}': {e}")
            return self._create_analysis_result("error", f"Ошибка анализа: {e}", False)
    
    def _is_complete_response(self, response: str) -> bool:
        """Проверить, является ли ответ подтверждением выполнения"""
        for keyword in self.keywords.complete:
            if keyword.lower() in response.lower():
                return True
        return False
    
    def _is_error_response(self, response: str) -> bool:
        """Проверить, является ли ответ сообщением об ошибке"""
        for keyword in self.keywords.error:
            if keyword.lower() in response.lower():
                return True
        return False
    
    def _is_timeout_response(self, response: str) -> bool:
        """Проверить, является ли ответ сообщением о таймауте"""
        return bool(self.patterns['timeout'].search(response))
    
    def _is_busy_response(self, response: str) -> bool:
        """Проверить, является ли ответ сообщением о занятости"""
        return bool(self.patterns['busy'].search(response))
    
    def _is_received_response(self, response: str) -> bool:
        """Проверить, является ли ответ подтверждением получения"""
        for keyword in self.keywords.received:
            if keyword.lower() in response.lower():
                return True
        return False
    
    def _analyze_numeric_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Проанализировать числовой ответ"""
        try:
            # Пытаемся преобразовать в число
            value = float(response)
            
            # Определяем тип числового ответа
            if value == 0:
                return self._create_analysis_result("numeric_zero", "Нулевое значение", True, {'value': value})
            elif value > 0:
                return self._create_analysis_result("numeric_positive", "Положительное значение", True, {'value': value})
            else:
                return self._create_analysis_result("numeric_negative", "Отрицательное значение", True, {'value': value})
                
        except ValueError:
            return None
    
    def _analyze_structured_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Проанализировать структурированный ответ"""
        try:
            # Проверяем JSON-подобные ответы
            if response.startswith('{') and response.endswith('}'):
                return self._create_analysis_result("json", "JSON ответ", True, {'raw': response})
            
            # Проверяем ответы с разделителями
            if '=' in response:
                parts = response.split('=', 1)
                if len(parts) == 2:
                    key, value = parts[0].strip(), parts[1].strip()
                    return self._create_analysis_result("key_value", "Ответ ключ-значение", True, {
                        'key': key,
                        'value': value
                    })
            
            # Проверяем ответы с запятыми
            if ',' in response:
                values = [v.strip() for v in response.split(',')]
                return self._create_analysis_result("list", "Список значений", True, {'values': values})
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Ошибка анализа структурированного ответа: {e}")
            return None
    
    def _create_analysis_result(self, response_type: str, message: str, success: bool, 
                               data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Создать результат анализа"""
        result = {
            'type': response_type,
            'message': message,
            'success': success,
            'timestamp': self._get_timestamp()
        }
        
        if data:
            result.update(data)
        
        return result
    
    def _get_timestamp(self) -> float:
        """Получить текущий timestamp"""
        import time
        return time.time()
    
    def wait_for_response(self, timeout: float = 30.0, 
                         expected_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Ожидать ответ определенного типа.
        
        Args:
            timeout: Время ожидания в секундах
            expected_types: Ожидаемые типы ответов
            
        Returns:
            Результат ожидания
        """
        import time
        
        start_time = time.time()
        expected_types = expected_types or ['complete', 'received']
        
        while time.time() - start_time < timeout:
            # Здесь должна быть логика получения ответа
            # Пока просто возвращаем заглушку
            time.sleep(0.1)
        
        return self._create_analysis_result("timeout", "Превышено время ожидания", False)
    
    def get_response_statistics(self) -> Dict[str, int]:
        """Получить статистику ответов"""
        return self.response_stats.copy()
    
    def reset_statistics(self):
        """Сбросить статистику ответов"""
        self.response_stats = {
            'total_responses': 0,
            'successful_responses': 0,
            'error_responses': 0,
            'timeout_responses': 0,
            'busy_responses': 0
        }
        self.logger.debug("Статистика ответов сброшена")
    
    def set_keywords(self, keywords: SequenceKeywords):
        """Установить ключевые слова для анализа"""
        self.keywords = keywords
        self.logger.debug("Ключевые слова обновлены")
    
    def add_custom_pattern(self, name: str, pattern: str):
        """Добавить пользовательский паттерн для анализа"""
        try:
            self.patterns[name] = re.compile(pattern, re.IGNORECASE)
            self.logger.debug(f"Добавлен пользовательский паттерн: {name}")
        except Exception as e:
            self.logger.error(f"Ошибка добавления паттерна '{name}': {e}")
    
    def get_success_rate(self) -> float:
        """Получить процент успешных ответов"""
        if self.response_stats['total_responses'] == 0:
            return 0.0
        
        return (self.response_stats['successful_responses'] / 
                self.response_stats['total_responses']) * 100.0

