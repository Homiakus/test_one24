#!/usr/bin/env python3
"""
Тест для проверки исправления проблемы зависания при отправке команд.
"""

import sys
import time
import logging
from unittest.mock import patch, MagicMock

# Добавляем путь к модулям проекта
sys.path.insert(0, '.')

from core.serial_manager import SerialManager

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_send_command_timeout():
    """Тест таймаута отправки команды"""
    logger.info("Начало теста таймаута отправки команды")
    
    # Создаем менеджер
    manager = SerialManager()
    
    # Мокаем подключение
    with patch.object(manager, 'is_connected', True):
        # Мокаем порт, который будет блокироваться при записи
        class BlockingSerial:
            def __init__(self):
                self.is_open = True
                self.write_timeout = 1.0
            
            def write(self, data):
                time.sleep(5.0)  # Блокируемся на 5 секунд
                return len(data)
        
        # Устанавливаем мок порт
        with manager._lock:
            manager.port = BlockingSerial()
        
        start_time = time.time()
        
        # Пытаемся отправить команду
        result = manager.send_command("test command")
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Время выполнения отправки: {duration:.2f} секунд")
        
        # Проверяем что отправка не заняла больше 5 секунд
        assert duration < 5.0, f"Отправка заняла слишком много времени: {duration}s"
        
        # Проверяем что отправка не удалась из-за таймаута
        assert result == False, "Отправка должна была завершиться неудачей из-за таймаута"
        
        logger.info("Тест таймаута отправки команды пройден успешно")

def test_send_command_success():
    """Тест успешной отправки команды"""
    logger.info("Начало теста успешной отправки команды")
    
    # Создаем менеджер
    manager = SerialManager()
    
    # Мокаем подключение
    with patch.object(manager, 'is_connected', True):
        # Мокаем порт для успешной отправки
        class MockSerial:
            def __init__(self):
                self.is_open = True
                self.write_timeout = 1.0
            
            def write(self, data):
                return len(data)
        
        # Устанавливаем мок порт
        with manager._lock:
            manager.port = MockSerial()
        
        start_time = time.time()
        
        # Пытаемся отправить команду
        result = manager.send_command("test command")
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Время выполнения отправки: {duration:.2f} секунд")
        
        # Проверяем что отправка не заняла больше 3 секунд
        assert duration < 3.0, f"Отправка заняла слишком много времени: {duration}s"
        
        # Проверяем что отправка удалась
        assert result == True, "Отправка должна была завершиться успешно"
        
        logger.info("Тест успешной отправки команды пройден успешно")

def test_send_command_port_unavailable():
    """Тест отправки команды при недоступном порте"""
    logger.info("Начало теста отправки команды при недоступном порте")
    
    # Создаем менеджер
    manager = SerialManager()
    
    # Мокаем подключение
    with patch.object(manager, 'is_connected', True):
        # Мокаем недоступный порт
        class UnavailableSerial:
            def __init__(self):
                self.is_open = False
                self.write_timeout = 1.0
        
        # Устанавливаем мок порт
        with manager._lock:
            manager.port = UnavailableSerial()
        
        start_time = time.time()
        
        # Пытаемся отправить команду
        result = manager.send_command("test command")
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Время выполнения отправки: {duration:.2f} секунд")
        
        # Проверяем что отправка быстро завершилась
        assert duration < 1.0, f"Отправка заняла слишком много времени: {duration}s"
        
        # Проверяем что отправка не удалась
        assert result == False, "Отправка должна была завершиться неудачей"
        
        logger.info("Тест отправки команды при недоступном порте пройден успешно")

def test_send_command_not_connected():
    """Тест отправки команды без подключения"""
    logger.info("Начало теста отправки команды без подключения")
    
    # Создаем менеджер
    manager = SerialManager()
    
    # Мокаем отключенное состояние
    with patch.object(manager, 'is_connected', False):
        start_time = time.time()
        
        # Пытаемся отправить команду
        result = manager.send_command("test command")
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Время выполнения отправки: {duration:.2f} секунд")
        
        # Проверяем что отправка быстро завершилась
        assert duration < 0.1, f"Отправка заняла слишком много времени: {duration}s"
        
        # Проверяем что отправка не удалась
        assert result == False, "Отправка должна была завершиться неудачей"
        
        logger.info("Тест отправки команды без подключения пройден успешно")

if __name__ == "__main__":
    logger.info("Запуск тестов исправления проблемы зависания при отправке команд")
    
    try:
        test_send_command_timeout()
        test_send_command_success()
        test_send_command_port_unavailable()
        test_send_command_not_connected()
        
        logger.info("Все тесты пройдены успешно!")
        print("✅ Все тесты пройдены успешно!")
        
    except Exception as e:
        logger.error(f"Ошибка в тестах: {e}")
        print(f"❌ Ошибка в тестах: {e}")
        sys.exit(1)
