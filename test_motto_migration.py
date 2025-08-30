"""
Тест миграции MOTTO v1.0 → v1.1

Проверяет конвертацию существующих конфигураций в MOTTO формат
"""

import unittest
import tempfile
import tomli
import tomli_w
from pathlib import Path

from core.motto import MOTTOParser, CompatibilityAdapter


class TestMOTTOMigration(unittest.TestCase):
    """Тесты миграции MOTTO"""
    
    def setUp(self):
        """Настройка тестов"""
        self.parser = MOTTOParser()
        self.adapter = CompatibilityAdapter()
        
        # Создаём тестовую конфигурацию v1.0
        self.v1_config = {
            'buttons': {
                'Multi → OG': 'sm -8 * * * *',
                'Multi → продувка OG': 'sm -43 * * * *',
                'RRight → слив': 'sm * * 4 * *',
                'Хоминг Multi': 'sh 1 0 0 0 0',
                'KL1 включить': 'pon 1',
                'KL1 выключить': 'poff 1',
                'Насос включить': 'pon 0',
                'Насос выключить': 'poff 0'
            },
            'sequences': {
                'load_tubes': ['Clamp → сжать ', 'Clamp → разжать', 'RRight → предноль', 'wait 3', 'Хоминг RRight', 'RRight → загрузка пробирок'],
                'og': ['RRight → верх', 'Multi → OG', 'Насос включить', 'KL2 включить', 'wait 2', 'Multi → продувка OG', 'wait 3', 'KL2 выключить', 'Насос выключить', 'RRight → экспозиция', 'waste_out', 'waste']
            },
            'serial_default': {
                'port': 'COM4',
                'baudrate': 115200,
                'bytesize': 8,
                'parity': 'N',
                'stopbits': 1,
                'timeout': 1.0
            },
            'wizard': {
                'step': [
                    {
                        'id': 1,
                        'title': 'Главное меню',
                        'buttons': [
                            {'text': '▶ Начать окраску и осаждение', 'next': 2},
                            {'text': '▶ Начать промывку', 'next': 7}
                        ],
                        'sequence': '',
                        'autoNext': False,
                        'showBar': False
                    }
                ]
            }
        }
    
    def test_convert_v1_to_v1_1(self):
        """Тест конвертации v1.0 в v1.1"""
        # Конвертируем конфигурацию
        config = self.adapter.convert_v1_to_v1_1(self.v1_config)
        
        # Проверяем базовые поля
        self.assertEqual(config.version, "1.1")
        self.assertIn('plant', config.vars)
        self.assertIn('default_port', config.vars)
        self.assertEqual(config.vars['default_port'], 'COM4')
        
        # Проверяем профили
        self.assertIn('default', config.profiles)
        profile = config.profiles['default']
        self.assertEqual(profile['env']['port'], 'COM4')
        self.assertEqual(profile['env']['baudrate'], 115200)
        
        # Проверяем последовательности
        self.assertIn('load_tubes', config.sequences)
        self.assertIn('og', config.sequences)
        
        # Проверяем условия и гварды
        self.assertIn('no_alarms', config.conditions)
        self.assertIn('serial_connected', config.conditions)
        self.assertIn('no_alarms', config.guards)
        self.assertIn('serial_connected', config.guards)
        
        # Проверяем политики
        self.assertIn('safe_retry', config.policies)
        self.assertIn('fast_retry', config.policies)
        
        # Проверяем ресурсы
        self.assertIn('serial_port', config.resources)
        self.assertIn('pump', config.resources)
        
        # Проверяем события и обработчики
        self.assertIn('estop', config.events)
        self.assertIn('serial_error', config.events)
        self.assertIn('on_estop', config.handlers)
        self.assertIn('on_serial_error', config.handlers)
        
        # Проверяем метаданные
        self.assertIn('wizard', config.metadata)
        self.assertIn('serial_default', config.metadata)
    
    def test_normalize_command_name(self):
        """Тест нормализации имён команд"""
        # Тестируем различные варианты имён
        test_cases = [
            ('Multi → OG', 'multi_og'),
            ('RRight → слив', 'rright_drain'),
            ('Хоминг Multi', 'home_multi'),
            ('KL1 включить', 'kl1_on'),
            ('Насос выключить', 'pump_off'),
            ('Clamp → сжать ', 'clamp_close'),
            ('RRight → загрузка пробирок', 'rright_load_tubes')
        ]
        
        for input_name, expected_name in test_cases:
            normalized = self.adapter._normalize_command_name(input_name)
            self.assertEqual(normalized, expected_name)
    
    def test_convert_buttons(self):
        """Тест конвертации кнопок"""
        buttons = {
            'Multi → OG': 'sm -8 * * * *',
            'KL1 включить': 'pon 1',
            'Насос выключить': 'poff 0'
        }
        
        converted = self.adapter.convert_buttons(buttons)
        
        self.assertIn('multi_og', converted)
        self.assertIn('kl1_on', converted)
        self.assertIn('pump_off', converted)
        
        self.assertEqual(converted['multi_og'], 'sm -8 * * * *')
        self.assertEqual(converted['kl1_on'], 'pon 1')
        self.assertEqual(converted['pump_off'], 'poff 0')
    
    def test_convert_sequences(self):
        """Тест конвертации последовательностей"""
        commands = {
            'multi_og': 'sm -8 * * * *',
            'kl1_on': 'pon 1',
            'pump_on': 'pon 0',
            'rright_up': 'sm * * -53 * *'
        }
        
        sequences = {
            'test_seq': ['RRight → верх', 'Multi → OG', 'Насос включить', 'wait 5', 'KL1 включить']
        }
        
        converted = self.adapter._convert_sequences(sequences, commands)
        
        self.assertIn('test_seq', converted)
        sequence = converted['test_seq']
        
        # Проверяем, что шаги конвертированы правильно
        self.assertIn('rright_up', sequence.steps)
        self.assertIn('multi_og', sequence.steps)
        self.assertIn('pump_on', sequence.steps)
        self.assertIn('wait 5', sequence.steps)  # wait должен остаться как есть
        self.assertIn('kl1_on', sequence.steps)
        
        # Проверяем метаданные последовательности
        self.assertEqual(sequence.name, 'test_seq')
        self.assertEqual(sequence.policy, 'safe_retry')
        self.assertIn('no_alarms', sequence.guards)
    
    def test_migration_with_file(self):
        """Тест миграции с файлом"""
        # Создаём временный файл v1.0
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.toml', delete=False) as f:
            tomli_w.dump(self.v1_config, f)
            v1_file = f.name
        
        try:
            # Загружаем v1.0 конфигурацию
            with open(v1_file, 'rb') as f:
                v1_config = tomli.load(f)
            
            # Конвертируем в v1.1
            config = self.adapter.convert_v1_to_v1_1(v1_config)
            
            # Проверяем результат
            self.assertEqual(config.version, "1.1")
            self.assertIn('load_tubes', config.sequences)
            self.assertIn('og', config.sequences)
            
        finally:
            # Удаляем временные файлы
            Path(v1_file).unlink()
    
    def test_backward_compatibility(self):
        """Тест обратной совместимости"""
        # Конвертируем v1.0 в v1.1
        config = self.adapter.convert_v1_to_v1_1(self.v1_config)
        
        # Проверяем, что все оригинальные данные сохранены в метаданных
        self.assertIn('wizard', config.metadata)
        self.assertIn('serial_default', config.metadata)
        
        wizard = config.metadata['wizard']
        self.assertIn('step', wizard)
        self.assertEqual(len(wizard['step']), 1)
        self.assertEqual(wizard['step'][0]['id'], 1)
        self.assertEqual(wizard['step'][0]['title'], 'Главное меню')
        
        serial_default = config.metadata['serial_default']
        self.assertEqual(serial_default['port'], 'COM4')
        self.assertEqual(serial_default['baudrate'], 115200)
        self.assertEqual(serial_default['timeout'], 1.0)


if __name__ == '__main__':
    unittest.main()