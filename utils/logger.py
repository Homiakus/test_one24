"""
Модуль настройки логирования
"""
import os
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Форматтер с цветным выводом для консоли"""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        try:
            log_color = self.COLORS.get(record.levelname, self.RESET)
            record.levelname = f"{log_color}{record.levelname}{self.RESET}"
            return super().format(record)
        except Exception as e:
            # Fallback на базовое форматирование при ошибке
            return f"{record.levelname} - {record.getMessage()}"


def safe_create_directory(path: Path) -> bool:
    """
    Безопасное создание директории с обработкой ошибок
    
    Args:
        path: Путь к директории
        
    Returns:
        bool: True если директория создана или существует
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except PermissionError as e:
        print(f"Ошибка прав доступа при создании директории {path}: {e}")
        return False
    except OSError as e:
        print(f"Ошибка ОС при создании директории {path}: {e}")
        return False
    except Exception as e:
        print(f"Неожиданная ошибка при создании директории {path}: {e}")
        return False


def setup_logging(log_dir: str = None) -> bool:
    """
    Настройка системы логирования с обработкой ошибок

    Args:
        log_dir: Директория для логов (по умолчанию - текущая)
        
    Returns:
        bool: True если логирование настроено успешно
    """
    try:
        if log_dir is None:
            log_dir = Path.cwd() / "logs"
        else:
            log_dir = Path(log_dir)

        # Создаем директорию для логов с обработкой ошибок
        if not safe_create_directory(log_dir):
            print("Не удалось создать директорию для логов, используем текущую директорию")
            log_dir = Path.cwd()

        # Имя файла лога с датой
        try:
            log_file = log_dir / f"app_{datetime.now():%Y%m%d}.log"
        except Exception as e:
            print(f"Ошибка создания имени файла лога: {e}")
            log_file = log_dir / "app.log"

        # Настройка корневого логгера
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # Очистка существующих обработчиков для избежания дублирования
        for handler in logger.handlers[:]:
            try:
                handler.close()
                logger.removeHandler(handler)
            except Exception as e:
                print(f"Ошибка при очистке обработчика: {e}")

        # Обработчик для файла с обработкой ошибок
        file_handler = None
        try:
            file_handler = logging.FileHandler(
                log_file, mode='a', encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except PermissionError as e:
            print(f"Ошибка прав доступа при создании файла лога {log_file}: {e}")
        except OSError as e:
            print(f"Ошибка ОС при создании файла лога {log_file}: {e}")
        except Exception as e:
            print(f"Неожиданная ошибка при создании файла лога: {e}")

        # Обработчик для консоли с обработкой ошибок
        console_handler = None
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        except Exception as e:
            print(f"Ошибка при создании консольного обработчика: {e}")

        # Проверяем, что хотя бы один обработчик добавлен
        if not logger.handlers:
            print("Не удалось создать ни одного обработчика логов")
            # Создаем базовый обработчик
            try:
                basic_handler = logging.StreamHandler(sys.stdout)
                basic_handler.setLevel(logging.INFO)
                basic_formatter = logging.Formatter('%(levelname)s - %(message)s')
                basic_handler.setFormatter(basic_formatter)
                logger.addHandler(basic_handler)
            except Exception as e:
                print(f"Не удалось создать базовый обработчик логов: {e}")
                return False

        # Логируем информацию о запуске
        try:
            logger.info(f"Логирование инициализировано. Файл: {log_file}")
            return True
        except Exception as e:
            print(f"Ошибка при логировании информации о запуске: {e}")
            return False

    except Exception as e:
        print(f"Критическая ошибка при настройке логирования: {e}")
        # Попытка создать минимальное логирование
        try:
            logging.basicConfig(
                level=logging.INFO,
                format='%(levelname)s - %(message)s',
                stream=sys.stdout
            )
            return True
        except Exception as basic_error:
            print(f"Не удалось создать даже базовое логирование: {basic_error}")
            return False


def get_logger(name: str) -> logging.Logger:
    """
    Получение логгера с обработкой ошибок
    
    Args:
        name: Имя логгера
        
    Returns:
        logging.Logger: Логгер или корневой логгер в случае ошибки
    """
    try:
        return logging.getLogger(name)
    except Exception as e:
        print(f"Ошибка при получении логгера '{name}': {e}")
        return logging.getLogger()


class Logger:
    """
    Класс-обертка для логгера для совместимости с модулями мониторинга
    """
    
    def __init__(self, name: str):
        """
        Инициализация логгера
        
        Args:
            name: Имя логгера
        """
        self.logger = get_logger(name)
    
    def debug(self, message: str, *args, **kwargs):
        """Логирование отладочного сообщения"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Логирование информационного сообщения"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Логирование предупреждения"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Логирование ошибки"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Логирование критической ошибки"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Логирование исключения"""
        self.logger.exception(message, *args, **kwargs)
