#!/usr/bin/env python3
"""
Тест для проверки исправления проблемы зависания при подключении к Serial порту.
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

def test_serial_connection_timeout():
    """Тест таймаута подключения к Serial порту"""
    logger.info("Начало теста таймаута подключения к Serial порту")
    
    # Создаем менеджер
    manager = SerialManager()
    
    # Мокаем get_available_ports чтобы вернуть тестовый порт
    with patch.object(manager, 'get_available_ports', return_value=['COM1', 'COM4']):
        # Мокаем serial.Serial чтобы симулировать зависание
        with patch('serial.Serial') as mock_serial:
            # Симулируем зависание при создании объекта
            mock_serial.side_effect = Exception("Simulated hang")
            
            start_time = time.time()
            
            # Пытаемся подключиться
            result = manager.connect('COM4', baudrate=115200, timeout=1.0)
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"Время выполнения подключения: {duration:.2f} секунд")
            
            # Проверяем что подключение не заняло больше 10 секунд
            assert duration < 10.0, f"Подключение заняло слишком много времени: {duration}s"
            
            # Проверяем что подключение не удалось
            assert result == False, "Подключение должно было завершиться неудачей"
            
            logger.info("Тест таймаута подключения пройден успешно")

def test_serial_connection_success():
    """Тест успешного подключения к Serial порту"""
    logger.info("Начало теста успешного подключения к Serial порту")
    
    # Создаем менеджер
    manager = SerialManager()
    
    # Мокаем get_available_ports
    with patch.object(manager, 'get_available_ports', return_value=['COM1', 'COM4']):
        # Мокаем serial.Serial для успешного подключения
        with patch('serial.Serial') as mock_serial:
            mock_port = MagicMock()
            mock_port.is_open = True
            mock_serial.return_value = mock_port
            
            start_time = time.time()
            
            # Пытаемся подключиться
            result = manager.connect('COM4', baudrate=115200, timeout=1.0)
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"Время выполнения подключения: {duration:.2f} секунд")
            
            # Проверяем что подключение не заняло больше 10 секунд
            assert duration < 10.0, f"Подключение заняло слишком много времени: {duration}s"
            
            # Проверяем что подключение удалось
            assert result == True, "Подключение должно было завершиться успешно"
            
            logger.info("Тест успешного подключения пройден успешно")

def test_port_availability_check():
    """Тест проверки доступности порта"""
    logger.info("Начало теста проверки доступности порта")
    
    # Создаем менеджер
    manager = SerialManager()
    
    # Мокаем get_available_ports
    with patch.object(manager, 'get_available_ports', return_value=['COM1', 'COM4']):
        # Мокаем serial.Serial для проверки доступности
        with patch('serial.Serial') as mock_serial:
            mock_port = MagicMock()
            mock_serial.return_value = mock_port
            
            # Тестируем доступный порт
            result = manager.connect('COM4', baudrate=115200, timeout=1.0)
            
            # Проверяем что была вызвана проверка порта
            mock_serial.assert_called()
            
            logger.info("Тест проверки доступности порта пройден успешно")

if __name__ == "__main__":
    logger.info("Запуск тестов исправления проблемы зависания Serial")
    
    try:
        test_serial_connection_timeout()
        test_serial_connection_success()
        test_port_availability_check()
        
        logger.info("Все тесты пройдены успешно!")
        print("✅ Все тесты пройдены успешно!")
        
    except Exception as e:
        logger.error(f"Ошибка в тестах: {e}")
        print(f"❌ Ошибка в тестах: {e}")
        sys.exit(1)
