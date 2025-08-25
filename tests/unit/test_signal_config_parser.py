"""
Unit тесты для SignalConfigParser
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from config.signal_config_parser import SignalConfigParser
from core.signal_types import SignalMapping, SignalType


class TestSignalConfigParser:
    """Тесты для SignalConfigParser"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.parser = SignalConfigParser()

    def test_parse_config_file_success(self):
        """Тест успешного парсинга файла конфигурации"""
        config_content = '''
[buttons]
"Тест" = "test"

[signals]
"TEMP" = "temperature (float)"
"STATUS" = "device_status (string)"
"ERROR" = "error_code (int)"

[sequences]
test = ["test"]
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_content)
            config_path = Path(f.name)
        
        try:
            signals = self.parser.parse_config_file(config_path)
            
            assert len(signals) == 3
            assert "TEMP" in signals
            assert "STATUS" in signals
            assert "ERROR" in signals
            
            # Проверяем маппинги
            temp_mapping = signals["TEMP"]
            assert isinstance(temp_mapping, SignalMapping)
            assert temp_mapping.variable_name == "temperature"
            assert temp_mapping.signal_type == SignalType.FLOAT
            
            status_mapping = signals["STATUS"]
            assert status_mapping.variable_name == "device_status"
            assert status_mapping.signal_type == SignalType.STRING
            
            error_mapping = signals["ERROR"]
            assert error_mapping.variable_name == "error_code"
            assert error_mapping.signal_type == SignalType.INT
            
        finally:
            config_path.unlink()

    def test_parse_config_file_no_signals_section(self):
        """Тест парсинга файла без секции signals"""
        config_content = '''
[buttons]
"Тест" = "test"

[sequences]
test = ["test"]
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_content)
            config_path = Path(f.name)
        
        try:
            signals = self.parser.parse_config_file(config_path)
            assert len(signals) == 0
            
        finally:
            config_path.unlink()

    def test_parse_config_file_not_found(self):
        """Тест парсинга несуществующего файла"""
        config_path = Path("/nonexistent/config.toml")
        signals = self.parser.parse_config_file(config_path)
        assert len(signals) == 0

    def test_parse_signal_line_valid(self):
        """Тест парсинга валидной строки сигнала"""
        line = '"TEMP" = "temperature (float)"'
        result = self.parser._parse_signal_line(line, 1)
        
        assert result is not None
        signal_name, mapping = result
        
        assert signal_name == "TEMP"
        assert isinstance(mapping, SignalMapping)
        assert mapping.variable_name == "temperature"
        assert mapping.signal_type == SignalType.FLOAT

    def test_parse_signal_line_invalid_format(self):
        """Тест парсинга строки с неверным форматом"""
        line = 'TEMP = temperature (float)'
        result = self.parser._parse_signal_line(line, 1)
        assert result is None

    def test_parse_signal_line_invalid_signal_name(self):
        """Тест парсинга строки с неверным именем сигнала"""
        line = '"temp" = "temperature (float)"'  # строчные буквы
        result = self.parser._parse_signal_line(line, 1)
        assert result is None

    def test_parse_signal_line_invalid_mapping(self):
        """Тест парсинга строки с неверным маппингом"""
        line = '"TEMP" = "temperature (invalid_type)"'
        result = self.parser._parse_signal_line(line, 1)
        assert result is None

    def test_validate_signal_name_valid(self):
        """Тест валидации валидного имени сигнала"""
        valid_names = ["TEMP", "STATUS", "ERROR_CODE", "PRESSURE_1", "MODE_2"]
        
        for name in valid_names:
            assert self.parser._validate_signal_name(name) is True

    def test_validate_signal_name_invalid(self):
        """Тест валидации неверного имени сигнала"""
        invalid_names = [
            "",  # пустое
            "temp",  # строчные буквы
            "TEMP-1",  # дефис
            "TEMP.1",  # точка
            "TEMP 1",  # пробел
            "A" * 51,  # слишком длинное
        ]
        
        for name in invalid_names:
            assert self.parser._validate_signal_name(name) is False

    def test_validate_signal_config_valid(self):
        """Тест валидации валидной конфигурации сигналов"""
        signals = {
            "TEMP": SignalMapping("temperature", SignalType.FLOAT),
            "STATUS": SignalMapping("device_status", SignalType.STRING),
            "ERROR": SignalMapping("error_code", SignalType.INT),
        }
        
        errors = self.parser.validate_signal_config(signals)
        assert len(errors) == 0

    def test_validate_signal_config_duplicate_signals(self):
        """Тест валидации конфигурации с дублирующимися сигналами"""
        signals = {
            "TEMP": SignalMapping("temperature", SignalType.FLOAT),
            "TEMP": SignalMapping("temp", SignalType.FLOAT),  # дубликат
        }
        
        errors = self.parser.validate_signal_config(signals)
        assert len(errors) > 0
        assert any("дублирующиеся имена сигналов" in error for error in errors)

    def test_validate_signal_config_duplicate_variables(self):
        """Тест валидации конфигурации с дублирующимися переменными"""
        signals = {
            "TEMP": SignalMapping("temperature", SignalType.FLOAT),
            "STATUS": SignalMapping("temperature", SignalType.STRING),  # дубликат переменной
        }
        
        errors = self.parser.validate_signal_config(signals)
        assert len(errors) > 0
        assert any("дублирующиеся имена переменных" in error for error in errors)

    def test_validate_signal_config_invalid_signal_name(self):
        """Тест валидации конфигурации с неверным именем сигнала"""
        signals = {
            "temp": SignalMapping("temperature", SignalType.FLOAT),  # строчные буквы
        }
        
        errors = self.parser.validate_signal_config(signals)
        assert len(errors) > 0
        assert any("Неверное имя сигнала" in error for error in errors)

    def test_validate_signal_config_invalid_variable_name(self):
        """Тест валидации конфигурации с неверным именем переменной"""
        signals = {
            "TEMP": SignalMapping("1temperature", SignalType.FLOAT),  # начинается с цифры
        }
        
        errors = self.parser.validate_signal_config(signals)
        assert len(errors) > 0
        assert any("Неверное имя переменной" in error for error in errors)

    def test_create_default_config(self):
        """Тест создания конфигурации по умолчанию"""
        config = self.parser.create_default_config()
        
        assert "[signals]" in config
        assert '"TEMP"' in config
        assert '"STATUS"' in config
        assert '"ERROR"' in config
        assert "temperature (float)" in config
        assert "device_status (string)" in config
        assert "error_code (int)" in config

    def test_save_signals_config_success(self):
        """Тест успешного сохранения конфигурации сигналов"""
        signals = {
            "TEMP": SignalMapping("temperature", SignalType.FLOAT),
            "STATUS": SignalMapping("device_status", SignalType.STRING),
        }
        
        original_content = '''
[buttons]
"Тест" = "test"

[sequences]
test = ["test"]
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(original_content)
            config_path = Path(f.name)
        
        try:
            result = self.parser.save_signals_config(config_path, signals)
            assert result is True
            
            # Проверяем, что секция signals добавлена
            with open(config_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            
            assert "[signals]" in new_content
            assert '"TEMP"' in new_content
            assert '"STATUS"' in new_content
            assert "temperature (float)" in new_content
            assert "device_status (string)" in new_content
            
        finally:
            config_path.unlink()

    def test_save_signals_config_replace_existing(self):
        """Тест замены существующей секции signals"""
        signals = {
            "TEMP": SignalMapping("temperature", SignalType.FLOAT),
            "STATUS": SignalMapping("device_status", SignalType.STRING),
        }
        
        original_content = '''
[buttons]
"Тест" = "test"

[signals]
"OLD" = "old_var (string)"

[sequences]
test = ["test"]
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(original_content)
            config_path = Path(f.name)
        
        try:
            result = self.parser.save_signals_config(config_path, signals)
            assert result is True
            
            # Проверяем, что старая секция заменена
            with open(config_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            
            assert "[signals]" in new_content
            assert '"TEMP"' in new_content
            assert '"STATUS"' in new_content
            assert '"OLD"' not in new_content  # старая секция удалена
            
        finally:
            config_path.unlink()

    def test_extract_signals_section_success(self):
        """Тест извлечения секции signals"""
        content = '''
[buttons]
"Тест" = "test"

[signals]
"TEMP" = "temperature (float)"
"STATUS" = "device_status (string)"

[sequences]
test = ["test"]
'''
        
        section = self.parser._extract_signals_section(content)
        assert section is not None
        assert '"TEMP"' in section
        assert '"STATUS"' in section
        assert "temperature (float)" in section
        assert "device_status (string)" in section

    def test_extract_signals_section_not_found(self):
        """Тест извлечения секции signals когда она отсутствует"""
        content = '''
[buttons]
"Тест" = "test"

[sequences]
test = ["test"]
'''
        
        section = self.parser._extract_signals_section(content)
        assert section is None

    def test_parse_signals_section_with_comments(self):
        """Тест парсинга секции signals с комментариями"""
        section_content = '''
# Сигналы температуры
"TEMP" = "temperature (float)"

# Сигналы статуса
"STATUS" = "device_status (string)"

# Пустая строка

# Комментарий
'''
        
        signals = self.parser._parse_signals_section(section_content)
        
        assert len(signals) == 2
        assert "TEMP" in signals
        assert "STATUS" in signals

    def test_parse_signals_section_with_invalid_lines(self):
        """Тест парсинга секции signals с неверными строками"""
        section_content = '''
"TEMP" = "temperature (float)"
invalid_line
"STATUS" = "device_status (string)"
another_invalid_line
'''
        
        signals = self.parser._parse_signals_section(section_content)
        
        assert len(signals) == 2
        assert "TEMP" in signals
        assert "STATUS" in signals
