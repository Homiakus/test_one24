"""
Модуль для обработки ошибок и исключений
"""
import sys
import logging
import traceback
from typing import Optional, Callable, Any
from functools import wraps
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt


class ErrorHandler:
    """Класс для централизованной обработки ошибок"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._error_callbacks = []
        self._critical_error_callbacks = []
    
    def register_error_callback(self, callback: Callable[[Exception, str], None]):
        """Регистрация callback для обработки ошибок"""
        self._error_callbacks.append(callback)
    
    def register_critical_error_callback(self, callback: Callable[[Exception, str], None]):
        """Регистрация callback для обработки критических ошибок"""
        self._critical_error_callbacks.append(callback)
    
    def handle_error(self, error: Exception, context: str = "", show_dialog: bool = True):
        """
        Обработка ошибки
        
        Args:
            error: Исключение
            context: Контекст ошибки
            show_dialog: Показывать ли диалог ошибки
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        
        # Логирование ошибки
        self.logger.error(error_msg, exc_info=True)
        
        # Вызов зарегистрированных callback'ов
        for callback in self._error_callbacks:
            try:
                callback(error, context)
            except Exception as e:
                self.logger.error(f"Ошибка в callback обработки ошибки: {e}")
        
        # Показ диалога ошибки
        if show_dialog:
            self._show_error_dialog(error_msg)
    
    def handle_critical_error(self, error: Exception, context: str = ""):
        """
        Обработка критической ошибки
        
        Args:
            error: Исключение
            context: Контекст ошибки
        """
        error_msg = f"Критическая ошибка: {context}: {str(error)}" if context else f"Критическая ошибка: {str(error)}"
        
        # Логирование критической ошибки
        self.logger.critical(error_msg, exc_info=True)
        
        # Вызов зарегистрированных callback'ов
        for callback in self._critical_error_callbacks:
            try:
                callback(error, context)
            except Exception as e:
                self.logger.error(f"Ошибка в callback обработки критической ошибки: {e}")
        
        # Показ диалога критической ошибки
        self._show_critical_error_dialog(error_msg)
    
    def _show_error_dialog(self, message: str):
        """Показ диалога ошибки"""
        try:
            app = QApplication.instance()
            if app:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowTitle("Ошибка")
                msg_box.setText("Произошла ошибка")
                msg_box.setInformativeText(message)
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()
        except Exception as e:
            self.logger.error(f"Не удалось показать диалог ошибки: {e}")
            print(f"Ошибка: {message}")
    
    def _show_critical_error_dialog(self, message: str):
        """Показ диалога критической ошибки"""
        try:
            app = QApplication.instance()
            if app:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle("Критическая ошибка")
                msg_box.setText("Произошла критическая ошибка")
                msg_box.setInformativeText(message)
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()
        except Exception as e:
            self.logger.error(f"Не удалось показать диалог критической ошибки: {e}")
            print(f"Критическая ошибка: {message}")


# Глобальный экземпляр обработчика ошибок
error_handler = ErrorHandler()


def safe_execute(func: Callable, *args, error_context: str = "", 
                show_dialog: bool = True, default_return: Any = None, **kwargs):
    """
    Безопасное выполнение функции с обработкой ошибок
    
    Args:
        func: Функция для выполнения
        *args: Аргументы функции
        error_context: Контекст ошибки
        show_dialog: Показывать ли диалог ошибки
        default_return: Значение по умолчанию при ошибке
        **kwargs: Именованные аргументы функции
        
    Returns:
        Результат выполнения функции или default_return при ошибке
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(e, error_context, show_dialog)
        return default_return


def critical_safe_execute(func: Callable, *args, error_context: str = "", **kwargs):
    """
    Безопасное выполнение критической функции с обработкой ошибок
    
    Args:
        func: Функция для выполнения
        *args: Аргументы функции
        error_context: Контекст ошибки
        **kwargs: Именованные аргументы функции
        
    Returns:
        Результат выполнения функции или None при ошибке
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_critical_error(e, error_context)
        return None


def error_handler_decorator(error_context: str = "", show_dialog: bool = True, 
                          default_return: Any = None):
    """
    Декоратор для автоматической обработки ошибок
    
    Args:
        error_context: Контекст ошибки
        show_dialog: Показывать ли диалог ошибки
        default_return: Значение по умолчанию при ошибке
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return safe_execute(func, *args, error_context=error_context,
                              show_dialog=show_dialog, default_return=default_return, **kwargs)
        return wrapper
    return decorator


def critical_error_handler_decorator(error_context: str = ""):
    """
    Декоратор для автоматической обработки критических ошибок
    
    Args:
        error_context: Контекст ошибки
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return critical_safe_execute(func, *args, error_context=error_context, **kwargs)
        return wrapper
    return decorator


def graceful_shutdown(app: Optional[QApplication] = None, error_msg: str = None):
    """
    Graceful shutdown приложения с обработкой ошибок
    
    Args:
        app: Экземпляр QApplication (если доступен)
        error_msg: Сообщение об ошибке для отображения
    """
    if error_msg:
        error_handler.handle_critical_error(Exception(error_msg), "Graceful shutdown")
    
    # Логирование завершения
    logging.info("Завершение работы приложения")
    
    # Корректное завершение Qt приложения
    if app and app.instance():
        try:
            app.quit()
        except Exception as e:
            logging.error(f"Ошибка при завершении Qt приложения: {e}")
    
    sys.exit(1)


def check_imports(required_modules: list) -> bool:
    """
    Проверка доступности критических модулей
    
    Args:
        required_modules: Список кортежей (module_name, package_name)
        
    Returns:
        bool: True если все модули доступны
    """
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
        except ImportError as e:
            error_msg = f"Не удалось импортировать {module_name}: {e}"
            print(f"Критическая ошибка: {error_msg}")
            print(f"Убедитесь, что {package_name} установлен и доступен")
            return False
    return True


def safe_file_operation(operation: Callable, file_path: str, *args, **kwargs):
    """
    Безопасное выполнение операций с файлами
    
    Args:
        operation: Функция операции с файлом
        file_path: Путь к файлу
        *args: Аргументы операции
        **kwargs: Именованные аргументы операции
        
    Returns:
        Результат операции или None при ошибке
    """
    try:
        return operation(file_path, *args, **kwargs)
    except PermissionError as e:
        error_handler.handle_error(e, f"Ошибка прав доступа к файлу {file_path}")
    except FileNotFoundError as e:
        error_handler.handle_error(e, f"Файл не найден: {file_path}")
    except OSError as e:
        error_handler.handle_error(e, f"Ошибка ОС при работе с файлом {file_path}")
    except Exception as e:
        error_handler.handle_error(e, f"Неожиданная ошибка при работе с файлом {file_path}")
    
    return None

