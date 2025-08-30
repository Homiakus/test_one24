#!/usr/bin/env python3
"""
Тест интеграции UI с MOTTO

Проверяет корректность интеграции MOTTO с пользовательским интерфейсом
"""

import unittest
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from core.motto.ui_integration import MOTTOUIIntegration, MOTTOConfigLoader


class TestUIIntegration(unittest.TestCase):
    """Тесты интеграции UI с MOTTO"""
    
    def setUp(self):
        """Настройка тестов"""
        self.config_file = 'config_motto_fixed.toml'
        
        # Проверяем наличие конфигурационного файла
        if not Path(self.config_file).exists():
            self.skipTest(f"Конфигурационный файл {self.config_file} не найден")
    
    def test_motto_ui_integration_initialization(self):
        """Тест инициализации MOTTO UI интеграции"""
        integration = MOTTOUIIntegration(self.config_file)
        
        # Проверяем, что интеграция инициализирована
        self.assertIsNotNone(integration)
        self.assertIsNotNone(integration.motto_config)
        self.assertEqual(integration.motto_config.version, "1.1")
        
        print("✅ MOTTO UI интеграция инициализирована корректно")
    
    def test_compatible_config_generation(self):
        """Тест генерации совместимой конфигурации"""
        integration = MOTTOUIIntegration(self.config_file)
        config = integration.get_compatible_config()
        
        # Проверяем наличие необходимых секций
        required_sections = ['buttons', 'sequences', 'serial_default', 'wizard']
        for section in required_sections:
            self.assertIn(section, config)
        
        # Проверяем, что секции не пустые
        self.assertGreater(len(config['buttons']), 0)
        self.assertGreater(len(config['sequences']), 0)
        
        print("✅ Совместимая конфигурация сгенерирована корректно")
    
    def test_buttons_for_ui(self):
        """Тест получения команд для UI"""
        integration = MOTTOUIIntegration(self.config_file)
        buttons = integration.get_buttons_for_ui()
        
        # Проверяем, что есть команды
        self.assertGreater(len(buttons), 0)
        
        # Проверяем несколько ключевых команд
        expected_commands = ['multi_og', 'pump_on', 'kl1_on']
        for cmd in expected_commands:
            if cmd in buttons:
                self.assertIsInstance(buttons[cmd], str)
                self.assertGreater(len(buttons[cmd]), 0)
        
        print("✅ Команды для UI получены корректно")
    
    def test_sequences_for_ui(self):
        """Тест получения последовательностей для UI"""
        integration = MOTTOUIIntegration(self.config_file)
        sequences = integration.get_sequences_for_ui()
        
        # Проверяем, что есть последовательности
        self.assertGreater(len(sequences), 0)
        
        # Проверяем несколько ключевых последовательностей
        expected_sequences = ['load_tubes', 'og', 'ea']
        for seq in expected_sequences:
            if seq in sequences:
                self.assertIsInstance(sequences[seq], list)
                self.assertGreater(len(sequences[seq]), 0)
        
        print("✅ Последовательности для UI получены корректно")
    
    def test_serial_settings(self):
        """Тест получения настроек Serial"""
        integration = MOTTOUIIntegration(self.config_file)
        settings = integration.get_serial_settings()
        
        # Проверяем наличие необходимых полей
        required_fields = ['port', 'baudrate', 'bytesize', 'parity', 'stopbits', 'timeout']
        for field in required_fields:
            self.assertIn(field, settings)
        
        # Проверяем типы значений
        self.assertIsInstance(settings['port'], str)
        self.assertIsInstance(settings['baudrate'], int)
        self.assertIsInstance(settings['timeout'], float)
        
        print("✅ Настройки Serial получены корректно")
    
    def test_wizard_steps(self):
        """Тест получения шагов wizard"""
        integration = MOTTOUIIntegration(self.config_file)
        steps = integration.get_wizard_steps()
        
        # Проверяем, что есть шаги
        self.assertIsInstance(steps, list)
        self.assertGreater(len(steps), 0)
        
        # Проверяем структуру первого шага
        first_step = steps[0]
        required_fields = ['id', 'title', 'buttons']
        for field in required_fields:
            self.assertIn(field, first_step)
        
        print("✅ Шаги wizard получены корректно")
    
    def test_motto_info(self):
        """Тест получения информации о MOTTO"""
        integration = MOTTOUIIntegration(self.config_file)
        info = integration.get_motto_info()
        
        # Проверяем наличие информации
        self.assertIsNotNone(info)
        self.assertIn('version', info)
        self.assertEqual(info['version'], "1.1")
        
        # Проверяем наличие статистики
        stats_fields = ['commands_count', 'sequences_count', 'conditions_count', 
                       'guards_count', 'policies_count']
        for field in stats_fields:
            self.assertIn(field, info)
            self.assertIsInstance(info[field], int)
        
        print("✅ Информация о MOTTO получена корректно")
    
    def test_sequence_execution(self):
        """Тест выполнения последовательности"""
        integration = MOTTOUIIntegration(self.config_file)
        
        # Тестируем выполнение последовательности без executor
        success = integration.execute_sequence_with_motto('load_tubes')
        self.assertTrue(success)
        
        print("✅ Выполнение последовательности работает корректно")
    
    def test_motto_config_loader(self):
        """Тест MOTTO ConfigLoader"""
        loader = MOTTOConfigLoader(self.config_file)
        
        # Проверяем, что loader инициализирован
        self.assertIsNotNone(loader)
        
        # Проверяем загрузку конфигурации
        config = loader.load()
        self.assertIsNotNone(config)
        self.assertIn('buttons', config)
        self.assertIn('sequences', config)
        
        # Проверяем информацию о MOTTO
        motto_info = loader.get_motto_info()
        self.assertIsNotNone(motto_info)
        self.assertIn('version', motto_info)
        
        print("✅ MOTTO ConfigLoader работает корректно")
    
    def test_config_file_detection(self):
        """Тест определения типа конфигурационного файла"""
        loader = MOTTOConfigLoader(self.config_file)
        
        # Проверяем, что файл определен как MOTTO
        self.assertTrue(loader._is_motto_config(self.config_file))
        
        # Проверяем обычный файл
        self.assertFalse(loader._is_motto_config('config.toml'))
        
        print("✅ Определение типа конфигурационного файла работает корректно")
    
    def test_sequence_execution_with_progress(self):
        """Тест выполнения последовательности с прогрессом"""
        integration = MOTTOUIIntegration(self.config_file)
        
        progress_messages = []
        
        def progress_callback(progress, message):
            progress_messages.append((progress, message))
        
        # Выполняем последовательность с callback
        success = integration.execute_sequence_with_motto(
            'load_tubes', 
            progress_callback=progress_callback
        )
        
        self.assertTrue(success)
        self.assertGreater(len(progress_messages), 0)
        
        # Проверяем, что прогресс увеличивается
        progress_values = [msg[0] for msg in progress_messages]
        self.assertEqual(progress_values[-1], 100)  # Последний прогресс должен быть 100%
        
        print("✅ Выполнение последовательности с прогрессом работает корректно")
    
    def test_guard_checking(self):
        """Тест проверки гвардов"""
        integration = MOTTOUIIntegration(self.config_file)
        
        # Получаем последовательность с гвардами
        sequence = integration.motto_config.sequences['og']
        guards = sequence.guards
        
        # Проверяем гварды
        success = integration._check_guards(guards)
        self.assertTrue(success)
        
        print("✅ Проверка гвардов работает корректно")
    
    def test_step_execution(self):
        """Тест выполнения отдельных шагов"""
        integration = MOTTOUIIntegration(self.config_file)
        
        # Тестируем команду
        success = integration._execute_step('multi_og')
        self.assertTrue(success)
        
        # Тестируем ожидание
        success = integration._execute_step('wait 1')
        self.assertTrue(success)
        
        # Тестируем неверную команду ожидания
        success = integration._execute_step('wait invalid')
        self.assertFalse(success)
        
        print("✅ Выполнение отдельных шагов работает корректно")


def run_integration_demo():
    """Демонстрация интеграции"""
    print("🎯 ДЕМОНСТРАЦИЯ ИНТЕГРАЦИИ UI С MOTTO")
    print("=" * 60)
    
    try:
        # Создаем интеграцию
        integration = MOTTOUIIntegration('config_motto_fixed.toml')
        
        # Получаем информацию
        info = integration.get_motto_info()
        print(f"📊 MOTTO Информация:")
        print(f"  Версия: {info['version']}")
        print(f"  Команд: {info['commands_count']}")
        print(f"  Последовательностей: {info['sequences_count']}")
        print(f"  Условий: {info['conditions_count']}")
        print(f"  Гвардов: {info['guards_count']}")
        
        # Получаем команды
        buttons = integration.get_buttons_for_ui()
        print(f"\n🔧 Команды для UI ({len(buttons)}):")
        for name, command in list(buttons.items())[:5]:
            print(f"  {name}: {command}")
        
        # Получаем последовательности
        sequences = integration.get_sequences_for_ui()
        print(f"\n📋 Последовательности для UI ({len(sequences)}):")
        for name, steps in list(sequences.items())[:3]:
            print(f"  {name}: {len(steps)} шагов")
        
        # Получаем настройки Serial
        serial_settings = integration.get_serial_settings()
        print(f"\n🔌 Настройки Serial:")
        print(f"  Порт: {serial_settings['port']}")
        print(f"  Скорость: {serial_settings['baudrate']}")
        print(f"  Таймаут: {serial_settings['timeout']}с")
        
        # Тестируем выполнение последовательности
        print(f"\n🚀 Тестирование выполнения последовательности:")
        success = integration.execute_sequence_with_motto('load_tubes')
        print(f"  Результат: {'✅ Успешно' if success else '❌ Ошибка'}")
        
        print("\n✅ Демонстрация завершена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка в демонстрации: {e}")


if __name__ == '__main__':
    # Запускаем демонстрацию
    run_integration_demo()
    
    print("\n" + "=" * 60)
    print("🧪 ЗАПУСК ТЕСТОВ")
    
    # Запускаем тесты
    unittest.main(verbosity=2)