#!/usr/bin/env python3
"""
Тестовый файл для проверки типизации.
"""
from typing import List, Dict, Optional, Any, Callable


def test_function(data: List[str], config: Dict[str, Any]) -> bool:
    """
    Тестовая функция с type hints.
    
    Args:
        data: Список строк
        config: Конфигурация
        
    Returns:
        True если успешно
    """
    return len(data) > 0


def test_optional(param: Optional[str] = None) -> str:
    """
    Тестовая функция с Optional параметром.
    
    Args:
        param: Опциональный параметр
        
    Returns:
        Строка результата
    """
    return param or "default"


def test_callback(callback: Callable[[str], bool]) -> bool:
    """
    Тестовая функция с callback.
    
    Args:
        callback: Функция обратного вызова
        
    Returns:
        Результат callback
    """
    return callback("test")


if __name__ == "__main__":
    # Тестируем функции
    result1 = test_function(["test"], {"key": "value"})
    result2 = test_optional("hello")
    result3 = test_callback(lambda x: len(x) > 0)
    
    print(f"Test 1: {result1}")
    print(f"Test 2: {result2}")
    print(f"Test 3: {result3}")
