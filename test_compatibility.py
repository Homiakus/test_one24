#!/usr/bin/env python3
"""
Тест совместимости MOTTO с существующими функциями

Проверяет, что все функции из старого config.toml корректно работают с новой MOTTO конфигурацией
"""

import unittest
import tomli
from core.motto import MOTTOParser


class TestMOTTOCompatibility(unittest.TestCase):
    """Тесты совместимости MOTTO"""
    
    def setUp(self):
        """Настройка тестов"""
        self.parser = MOTTOParser()
        
        # Загружаем конфигурации
        with open('config.toml', 'rb') as f:
            self.old_config = tomli.load(f)
        
        with open('config_motto_fixed.toml', 'rb') as f:
            self.new_config = tomli.load(f)
        
        # Загружаем через MOTTO парсер
        self.motto_config = self.parser.parse_config('config_motto_fixed.toml')
    
    def test_serial_default_compatibility(self):
        """Тест совместимости serial_default"""
        old_serial = self.old_config['serial_default']
        new_serial = self.new_config['serial_default']
        
        # Проверяем все поля
        self.assertEqual(old_serial['port'], new_serial['port'])
        self.assertEqual(old_serial['baudrate'], new_serial['baudrate'])
        self.assertEqual(old_serial['bytesize'], new_serial['bytesize'])
        self.assertEqual(old_serial['parity'], new_serial['parity'])
        self.assertEqual(old_serial['stopbits'], new_serial['stopbits'])
        self.assertEqual(old_serial['timeout'], new_serial['timeout'])
        
        print("✅ serial_default: полная совместимость")
    
    def test_wizard_compatibility(self):
        """Тест совместимости wizard"""
        old_wizard = self.old_config['wizard']
        new_wizard = self.new_config['wizard']
        
        # Проверяем количество шагов
        self.assertEqual(len(old_wizard['step']), len(new_wizard['step']))
        
        # Проверяем каждый шаг
        for i, (old_step, new_step) in enumerate(zip(old_wizard['step'], new_wizard['step'])):
            self.assertEqual(old_step['id'], new_step['id'])
            self.assertEqual(old_step['title'], new_step['title'])
            self.assertEqual(old_step['sequence'], new_step['sequence'])
            self.assertEqual(old_step['autoNext'], new_step['autoNext'])
            self.assertEqual(old_step['showBar'], new_step['showBar'])
        
        print("✅ wizard: полная совместимость")
    
    def test_commands_compatibility(self):
        """Тест совместимости команд"""
        old_buttons = self.old_config['buttons']
        new_commands = self.new_config['commands']
        
        # Проверяем количество команд
        self.assertEqual(len(old_buttons), len(new_commands))
        
        # Проверяем, что все команды из старого файла есть в новом
        for old_name, old_command in old_buttons.items():
            # Находим соответствующую новую команду
            found = False
            for new_name, new_command in new_commands.items():
                if new_command == old_command:
                    found = True
                    break
            
            self.assertTrue(found, f"Команда '{old_name}' не найдена в новом файле")
        
        print("✅ commands: полная совместимость")
    
    def test_sequences_compatibility(self):
        """Тест совместимости последовательностей"""
        old_sequences = self.old_config['sequences']
        new_sequences = self.new_config['sequences']
        
        # Проверяем количество последовательностей
        self.assertEqual(len(old_sequences), len(new_sequences))
        
        # Проверяем, что все последовательности есть
        for seq_name in old_sequences.keys():
            self.assertIn(seq_name, new_sequences)
        
        print("✅ sequences: полная совместимость")
    
    def test_sequence_execution(self):
        """Тест выполнения последовательностей"""
        # Проверяем, что можем получить последовательность
        og_sequence = self.motto_config.sequences['og']
        self.assertIsNotNone(og_sequence)
        self.assertEqual(og_sequence.name, 'og')
        self.assertIn('rright_up', og_sequence.steps)
        self.assertIn('multi_og', og_sequence.steps)
        
        # Проверяем политики и гварды
        self.assertEqual(og_sequence.policy, 'safe_retry')
        self.assertIn('no_alarms', og_sequence.guards)
        
        print("✅ sequence execution: корректная структура")
    
    def test_command_lookup(self):
        """Тест поиска команд"""
        # Проверяем, что можем найти команды
        commands = self.new_config['commands']
        
        # Проверяем несколько ключевых команд
        self.assertIn('multi_og', commands)
        self.assertIn('pump_on', commands)
        self.assertIn('kl1_on', commands)
        self.assertIn('home_multi', commands)
        
        # Проверяем значения команд
        self.assertEqual(commands['multi_og'], 'sm -8 * * * *')
        self.assertEqual(commands['pump_on'], 'pon 0')
        self.assertEqual(commands['kl1_on'], 'pon 1')
        
        print("✅ command lookup: корректный поиск")
    
    def test_wizard_menu_access(self):
        """Тест доступа к меню wizard"""
        wizard = self.new_config['wizard']
        
        # Проверяем главное меню
        main_menu = wizard['step'][0]
        self.assertEqual(main_menu['title'], 'Главное меню')
        self.assertEqual(main_menu['id'], 1)
        
        # Проверяем кнопки меню
        buttons = main_menu['buttons']
        self.assertEqual(len(buttons), 2)
        
        # Проверяем первую кнопку
        first_button = buttons[0]
        self.assertEqual(first_button['text'], '▶ Начать окраску и осаждение')
        self.assertEqual(first_button['next'], 2)
        
        print("✅ wizard menu: корректный доступ")
    
    def test_sequence_integration(self):
        """Тест интеграции последовательностей с wizard"""
        wizard = self.new_config['wizard']
        sequences = self.new_config['sequences']
        
        # Проверяем, что wizard ссылается на существующие последовательности
        for step in wizard['step']:
            if step['sequence']:
                seq_name = step['sequence']
                self.assertIn(seq_name, sequences, f"Последовательность '{seq_name}' не найдена")
        
        print("✅ sequence integration: корректные ссылки")
    
    def test_motto_parser_compatibility(self):
        """Тест совместимости с MOTTO парсером"""
        # Проверяем, что парсер корректно загружает конфигурацию
        self.assertIsNotNone(self.motto_config)
        self.assertEqual(self.motto_config.version, "1.1")
        
        # Проверяем основные секции
        self.assertGreater(len(self.motto_config.sequences), 0)
        self.assertGreater(len(self.motto_config.conditions), 0)
        self.assertGreater(len(self.motto_config.guards), 0)
        self.assertGreater(len(self.motto_config.policies), 0)
        
        print("✅ motto parser: корректная загрузка")
    
    def test_backward_compatibility(self):
        """Тест обратной совместимости"""
        # Проверяем, что старый код может работать с новым файлом
        # (если заменить config.toml на config_motto_fixed.toml)
        
        # Проверяем наличие всех необходимых секций
        required_sections = ['serial_default', 'wizard', 'sequences']
        for section in required_sections:
            self.assertIn(section, self.new_config)
        
        # Проверяем структуру wizard
        wizard = self.new_config['wizard']
        self.assertIn('step', wizard)
        self.assertIsInstance(wizard['step'], list)
        
        # Проверяем структуру sequences
        sequences = self.new_config['sequences']
        self.assertIsInstance(sequences, dict)
        
        print("✅ backward compatibility: полная совместимость")


if __name__ == '__main__':
    unittest.main(verbosity=2)