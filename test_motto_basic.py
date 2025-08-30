"""
Базовые тесты для MOTTO системы

Тестирует основные компоненты:
- Парсинг конфигураций
- Валидацию
- Базовые структуры данных
"""

import unittest
from pathlib import Path
import tempfile
import tomli
import tomli_w

from core.motto import (
    MOTTOParser, MOTTOValidator, MOTTOConfig,
    Sequence, Condition, Guard, Policy
)


class TestMOTTOBasic(unittest.TestCase):
    """Базовые тесты MOTTO"""
    
    def setUp(self):
        """Настройка тестов"""
        self.parser = MOTTOParser()
        self.validator = MOTTOValidator()
        
        # Создаём временную конфигурацию для тестов
        self.test_config = {
            'version': '1.1',
            'vars': {
                'plant': 'A1',
                'line': 'stain-03'
            },
            'profiles': {
                'default': {
                    'env': {
                        'zones': '0010',
                        'max_temp_C': 42,
                        'wash_time_s': 30
                    }
                }
            },
            'sequences': {
                'test_sequence': {
                    'name': 'test_sequence',
                    'description': 'Тестовая последовательность',
                    'steps': ['step1', 'step2', 'step3']
                }
            },
            'conditions': {
                'test_condition': {
                    'expr': 'status("alarm") == 0'
                }
            },
            'guards': {
                'test_guard': {
                    'when': 'pre',
                    'condition': 'test_condition',
                    'on_fail': {'action': 'abort'}
                }
            }
        }
    
    def test_parser_creation(self):
        """Тест создания парсера"""
        self.assertIsNotNone(self.parser)
        self.assertEqual(len(self.parser._parsed_configs), 0)
    
    def test_validator_creation(self):
        """Тест создания валидатора"""
        self.assertIsNotNone(self.validator)
    
    def test_parse_simple_config(self):
        """Тест парсинга простой конфигурации"""
        # Создаём временный файл
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.toml', delete=False) as f:
            tomli_w.dump(self.test_config, f)
            config_path = f.name
        
        try:
            # Парсим конфигурацию
            config = self.parser.parse_config(config_path)
            
            # Проверяем результат
            self.assertIsNotNone(config)
            self.assertEqual(config.version, '1.1')
            self.assertEqual(config.vars['plant'], 'A1')
            self.assertEqual(config.vars['line'], 'stain-03')
            
            # Проверяем профили
            self.assertIn('default', config.profiles)
            profile = config.profiles['default']
            self.assertEqual(profile.name, 'default')
            self.assertEqual(profile.env['zones'], '0010')
            self.assertEqual(profile.env['max_temp_C'], 42)
            
            # Проверяем последовательности
            self.assertIn('test_sequence', config.sequences)
            sequence = config.sequences['test_sequence']
            self.assertEqual(sequence.name, 'test_sequence')
            self.assertEqual(sequence.description, 'Тестовая последовательность')
            self.assertEqual(len(sequence.steps), 3)
            
            # Проверяем условия
            self.assertIn('test_condition', config.conditions)
            condition = config.conditions['test_condition']
            self.assertEqual(condition.expr, 'status("alarm") == 0')
            
            # Проверяем гварды
            self.assertIn('test_guard', config.guards)
            guard = config.guards['test_guard']
            self.assertEqual(guard.condition, 'test_condition')
            self.assertEqual(guard.on_fail['action'], 'abort')
            
        finally:
            # Удаляем временный файл
            Path(config_path).unlink()
    
    def test_validate_config(self):
        """Тест валидации конфигурации"""
        config = MOTTOConfig()
        config.version = '1.1'
        
        # Добавляем тестовую последовательность
        sequence = Sequence(name='test')
        config.sequences['test'] = sequence
        
        # Валидируем
        result = self.validator.validate_config(config)
        
        # Проверяем результат
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_invalid_version(self):
        """Тест валидации неверной версии"""
        config = MOTTOConfig()
        config.version = '2.0'  # Неподдерживаемая версия
        
        result = self.validator.validate_config(config)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertIn('Неподдерживаемая версия', result.errors[0])
    
    def test_validate_empty_sequence(self):
        """Тест валидации пустой последовательности"""
        sequence = Sequence(name='')
        
        result = self.validator.validate_sequence(sequence)
        
        self.assertFalse(result.is_valid)
        self.assertIn('Отсутствует имя последовательности', result.errors[0])
    
    def test_parser_cache(self):
        """Тест кэширования парсера"""
        # Создаём временный файл
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.toml', delete=False) as f:
            tomli_w.dump(self.test_config, f)
            config_path = f.name
        
        try:
            # Парсим первый раз
            config1 = self.parser.parse_config(config_path)
            self.assertIsNotNone(config1)
            
            # Парсим второй раз (должен быть из кэша)
            config2 = self.parser.parse_config(config_path)
            self.assertIsNotNone(config2)
            
            # Проверяем, что это тот же объект (по содержимому)
            self.assertEqual(config1.version, config2.version)
            self.assertEqual(config1.vars, config2.vars)
            
            # Проверяем кэш
            cached = self.parser.get_cached_config(config_path)
            self.assertIsNotNone(cached)
            self.assertEqual(cached.version, config1.version)
            
            # Очищаем кэш
            self.parser.clear_cache(config_path)
            cached = self.parser.get_cached_config(config_path)
            self.assertIsNone(cached)
            
        finally:
            Path(config_path).unlink()
    
    def test_sequence_types(self):
        """Тест типов последовательностей"""
        from core.motto.types import SequenceType
        
        # Обычная последовательность
        sequence = Sequence(name='test', type=SequenceType.SEQUENCE)
        self.assertEqual(sequence.type, SequenceType.SEQUENCE)
        
        # Параллельная последовательность
        parallel = Sequence(name='parallel', type=SequenceType.PARALLEL)
        self.assertEqual(parallel.type, SequenceType.PARALLEL)
    
    def test_guard_types(self):
        """Тест типов гвардов"""
        from core.motto.types import GuardWhen
        
        # Pre-гвард
        pre_guard = Guard(name='pre', when=GuardWhen.PRE, condition='test')
        self.assertEqual(pre_guard.when, GuardWhen.PRE)
        
        # Post-гвард
        post_guard = Guard(name='post', when=GuardWhen.POST, condition='test')
        self.assertEqual(post_guard.when, GuardWhen.POST)


if __name__ == '__main__':
    unittest.main()