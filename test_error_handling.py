"""
Тест системы обработки ошибок
"""
import sys
import logging
from unittest.mock import patch, MagicMock
import pytest

# Добавляем путь к проекту
sys.path.insert(0, '.')

from utils.error_handler import (
    error_handler, 
    safe_execute, 
    critical_safe_execute,
    error_handler_decorator,
    check_imports
)
from utils.logger import setup_logging


def test_error_handler_basic():
    """Тест базовой функциональности ErrorHandler"""
    # Настройка логирования для тестов
    logging.basicConfig(level=logging.DEBUG)
    
    # Тест обработки обычной ошибки
    with patch('utils.error_handler.ErrorHandler._show_error_dialog') as mock_dialog:
        error_handler.handle_error(Exception("Тестовая ошибка"), "Тест")
        mock_dialog.assert_called_once()
    
    # Тест обработки критической ошибки
    with patch('utils.error_handler.ErrorHandler._show_critical_error_dialog') as mock_dialog:
        error_handler.handle_critical_error(Exception("Критическая ошибка"), "Тест")
        mock_dialog.assert_called_once()


def test_safe_execute():
    """Тест безопасного выполнения функций"""
    # Тест успешного выполнения
    result = safe_execute(lambda x: x * 2, 5, error_context="Тест умножения")
    assert result == 10
    
    # Тест выполнения с ошибкой
    def failing_function():
        raise ValueError("Тестовая ошибка")
    
    result = safe_execute(failing_function, error_context="Тест ошибки", default_return="fallback")
    assert result == "fallback"


def test_critical_safe_execute():
    """Тест безопасного выполнения критических функций"""
    # Тест успешного выполнения
    result = critical_safe_execute(lambda x: x * 2, 5, error_context="Тест умножения")
    assert result == 10
    
    # Тест выполнения с ошибкой
    def failing_function():
        raise ValueError("Критическая ошибка")
    
    result = critical_safe_execute(failing_function, error_context="Тест критической ошибки")
    assert result is None


def test_error_handler_decorator():
    """Тест декоратора обработки ошибок"""
    @error_handler_decorator(error_context="Тест декоратора", default_return="decorated_fallback")
    def decorated_function(should_fail=False):
        if should_fail:
            raise RuntimeError("Ошибка в декорированной функции")
        return "success"
    
    # Тест успешного выполнения
    result = decorated_function()
    assert result == "success"
    
    # Тест выполнения с ошибкой
    result = decorated_function(should_fail=True)
    assert result == "decorated_fallback"


def test_check_imports():
    """Тест проверки импортов"""
    # Тест с существующими модулями
    result = check_imports([('sys', 'sys'), ('os', 'os')])
    assert result is True
    
    # Тест с несуществующим модулем
    result = check_imports([('nonexistent_module', 'nonexistent_package')])
    assert result is False


def test_error_handler_callbacks():
    """Тест callback'ов ErrorHandler"""
    callback_called = False
    callback_error = None
    callback_context = None
    
    def test_callback(error, context):
        nonlocal callback_called, callback_error, callback_context
        callback_called = True
        callback_error = error
        callback_context = context
    
    # Регистрация callback
    error_handler.register_error_callback(test_callback)
    
    # Тест вызова callback
    test_error = Exception("Callback тест")
    error_handler.handle_error(test_error, "Callback контекст")
    
    assert callback_called
    assert callback_error == test_error
    assert callback_context == "Callback контекст"


def test_logger_error_handling():
    """Тест обработки ошибок в логгере"""
    # Тест создания директории с ошибкой прав доступа
    with patch('pathlib.Path.mkdir') as mock_mkdir:
        mock_mkdir.side_effect = PermissionError("Нет прав доступа")
        
        # Должно вернуть False при ошибке создания директории
        result = setup_logging()
        assert result is True  # Должен fallback на базовое логирование


if __name__ == "__main__":
    print("Запуск тестов обработки ошибок...")
    
    # Простые тесты без pytest
    try:
        test_error_handler_basic()
        print("✓ test_error_handler_basic - PASSED")
    except Exception as e:
        print(f"✗ test_error_handler_basic - FAILED: {e}")
    
    try:
        test_safe_execute()
        print("✓ test_safe_execute - PASSED")
    except Exception as e:
        print(f"✗ test_safe_execute - FAILED: {e}")
    
    try:
        test_critical_safe_execute()
        print("✓ test_critical_safe_execute - PASSED")
    except Exception as e:
        print(f"✗ test_critical_safe_execute - FAILED: {e}")
    
    try:
        test_error_handler_decorator()
        print("✓ test_error_handler_decorator - PASSED")
    except Exception as e:
        print(f"✗ test_error_handler_decorator - FAILED: {e}")
    
    try:
        test_check_imports()
        print("✓ test_check_imports - PASSED")
    except Exception as e:
        print(f"✗ test_check_imports - FAILED: {e}")
    
    try:
        test_error_handler_callbacks()
        print("✓ test_error_handler_callbacks - PASSED")
    except Exception as e:
        print(f"✗ test_error_handler_callbacks - FAILED: {e}")
    
    print("\nТестирование завершено!")

