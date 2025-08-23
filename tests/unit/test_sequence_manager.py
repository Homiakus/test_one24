"""
Unit тесты для sequence_manager с поддержкой условного выполнения
"""
import pytest
from unittest.mock import Mock, patch
from typing import Dict, List

from core.sequence_manager import (
    SequenceManager, CommandValidator, FlagManager, 
    ConditionalState, CommandType, ValidationResult
)


class TestFlagManager:
    """Тесты для FlagManager"""
    
    def test_flag_manager_initialization(self):
        """Тест инициализации FlagManager"""
        flag_manager = FlagManager()
        assert flag_manager.get_all_flags() == {}
    
    def test_set_and_get_flag(self):
        """Тест установки и получения флага"""
        flag_manager = FlagManager()
        flag_manager.set_flag("test_flag", True)
        assert flag_manager.get_flag("test_flag") is True
        assert flag_manager.get_flag("unknown_flag", False) is False
    
    def test_has_flag(self):
        """Тест проверки существования флага"""
        flag_manager = FlagManager()
        assert flag_manager.has_flag("test_flag") is False
        flag_manager.set_flag("test_flag", True)
        assert flag_manager.has_flag("test_flag") is True
    
    def test_clear_flag(self):
        """Тест очистки флага"""
        flag_manager = FlagManager()
        flag_manager.set_flag("test_flag", True)
        assert flag_manager.has_flag("test_flag") is True
        flag_manager.clear_flag("test_flag")
        assert flag_manager.has_flag("test_flag") is False
    
    def test_load_flags_from_config(self):
        """Тест загрузки флагов из конфигурации"""
        flag_manager = FlagManager()
        config = {
            "flags": {
                "flag1": True,
                "flag2": False,
                "flag3": "not_bool"  # Должен быть проигнорирован
            }
        }
        flag_manager.load_flags_from_config(config)
        assert flag_manager.get_flag("flag1") is True
        assert flag_manager.get_flag("flag2") is False
        assert flag_manager.has_flag("flag3") is False


class TestCommandValidator:
    """Тесты для CommandValidator"""
    
    def test_validate_wait_command_valid(self):
        """Тест валидации корректной wait команды"""
        validator = CommandValidator()
        result = validator.validate_command("wait 5")
        assert result.is_valid is True
        assert result.command_type == CommandType.WAIT
        assert result.parsed_data["wait_time"] == 5.0
    
    def test_validate_wait_command_invalid(self):
        """Тест валидации некорректной wait команды"""
        validator = CommandValidator()
        result = validator.validate_command("wait")
        assert result.is_valid is False
        assert "должна содержать время" in result.error_message
    
    def test_validate_if_command_valid(self):
        """Тест валидации корректной if команды"""
        validator = CommandValidator()
        result = validator.validate_command("if test_flag")
        assert result.is_valid is True
        assert result.command_type == CommandType.CONDITIONAL_IF
        assert result.parsed_data["flag_name"] == "test_flag"
    
    def test_validate_if_command_invalid(self):
        """Тест валидации некорректной if команды"""
        validator = CommandValidator()
        result = validator.validate_command("if")
        assert result.is_valid is False
        assert "должна содержать имя флага" in result.error_message
    
    def test_validate_else_command(self):
        """Тест валидации else команды"""
        validator = CommandValidator()
        result = validator.validate_command("else")
        assert result.is_valid is True
        assert result.command_type == CommandType.CONDITIONAL_ELSE
    
    def test_validate_endif_command(self):
        """Тест валидации endif команды"""
        validator = CommandValidator()
        result = validator.validate_command("endif")
        assert result.is_valid is True
        assert result.command_type == CommandType.CONDITIONAL_ENDIF
    
    def test_validate_stop_if_not_command_valid(self):
        """Тест валидации корректной stop_if_not команды"""
        validator = CommandValidator()
        result = validator.validate_command("stop_if_not test_flag")
        assert result.is_valid is True
        assert result.command_type == CommandType.STOP_IF_NOT
        assert result.parsed_data["flag_name"] == "test_flag"
    
    def test_validate_stop_if_not_command_invalid(self):
        """Тест валидации некорректной stop_if_not команды"""
        validator = CommandValidator()
        result = validator.validate_command("stop_if_not")
        assert result.is_valid is False
        assert "должна содержать имя флага" in result.error_message
    
    def test_validate_regular_command(self):
        """Тест валидации обычной команды"""
        validator = CommandValidator()
        result = validator.validate_command("test_command")
        assert result.is_valid is True
        assert result.command_type == CommandType.REGULAR
        assert result.parsed_data["command"] == "test_command"
    
    def test_validate_sequence_balanced_conditionals(self):
        """Тест валидации последовательности с сбалансированными условиями"""
        validator = CommandValidator()
        commands = ["if flag1", "command1", "else", "command2", "endif"]
        is_valid, errors = validator.validate_sequence(commands)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_sequence_unbalanced_conditionals(self):
        """Тест валидации последовательности с несбалансированными условиями"""
        validator = CommandValidator()
        commands = ["if flag1", "command1", "endif", "endif"]  # Лишний endif
        is_valid, errors = validator.validate_sequence(commands)
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_sequence_else_without_if(self):
        """Тест валидации последовательности с else без if"""
        validator = CommandValidator()
        commands = ["else", "command1", "endif"]
        is_valid, errors = validator.validate_sequence(commands)
        assert is_valid is False
        assert any("else без соответствующего if" in error for error in errors)


class TestSequenceManager:
    """Тесты для SequenceManager"""
    
    @pytest.fixture
    def sample_config(self):
        """Фикстура с примером конфигурации"""
        return {
            "sequences": {
                "test_seq": ["command1", "command2"],
                "nested_seq": ["test_seq", "command3"],
                "conditional_seq": ["if flag1", "command1", "else", "command2", "endif"]
            },
            "buttons": {
                "button1": "cmd1",
                "button2": "cmd2"
            }
        }
    
    @pytest.fixture
    def sequence_manager(self, sample_config):
        """Фикстура с SequenceManager"""
        return SequenceManager(
            sample_config["sequences"],
            sample_config["buttons"]
        )
    
    def test_sequence_manager_initialization(self, sequence_manager):
        """Тест инициализации SequenceManager"""
        assert sequence_manager.sequences is not None
        assert sequence_manager.buttons_config is not None
        assert sequence_manager.flag_manager is not None
    
    def test_expand_simple_sequence(self, sequence_manager):
        """Тест разворачивания простой последовательности"""
        commands = sequence_manager.expand_sequence("test_seq")
        assert commands == ["command1", "command2"]
    
    def test_expand_nested_sequence(self, sequence_manager):
        """Тест разворачивания вложенной последовательности"""
        commands = sequence_manager.expand_sequence("nested_seq")
        assert commands == ["command1", "command2", "command3"]
    
    def test_expand_sequence_with_buttons(self, sequence_manager):
        """Тест разворачивания последовательности с кнопками"""
        sequence_manager.sequences["button_seq"] = ["button1", "button2"]
        commands = sequence_manager.expand_sequence("button_seq")
        assert commands == ["cmd1", "cmd2"]
    
    def test_expand_sequence_with_wait(self, sequence_manager):
        """Тест разворачивания последовательности с wait"""
        sequence_manager.sequences["wait_seq"] = ["wait 5", "command1"]
        commands = sequence_manager.expand_sequence("wait_seq")
        assert commands == ["wait 5", "command1"]
    
    def test_expand_sequence_with_conditionals(self, sequence_manager):
        """Тест разворачивания последовательности с условиями"""
        commands = sequence_manager.expand_sequence("conditional_seq")
        assert "if flag1" in commands
        assert "else" in commands
        assert "endif" in commands
    
    def test_validate_sequence_valid(self, sequence_manager):
        """Тест валидации корректной последовательности"""
        is_valid, errors = sequence_manager.validate_sequence("test_seq")
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_sequence_invalid(self, sequence_manager):
        """Тест валидации некорректной последовательности"""
        is_valid, errors = sequence_manager.validate_sequence("nonexistent_seq")
        assert is_valid is False
        assert len(errors) > 0
    
    def test_get_sequence_info(self, sequence_manager):
        """Тест получения информации о последовательности"""
        info = sequence_manager.get_sequence_info("test_seq")
        assert info["exists"] is True
        assert info["command_count"] == 2
        assert "command1" in info["commands"]
    
    def test_set_and_get_flag(self, sequence_manager):
        """Тест установки и получения флага"""
        sequence_manager.set_flag("test_flag", True)
        assert sequence_manager.get_flag("test_flag") is True
    
    def test_get_all_flags(self, sequence_manager):
        """Тест получения всех флагов"""
        sequence_manager.set_flag("flag1", True)
        sequence_manager.set_flag("flag2", False)
        flags = sequence_manager.get_all_flags()
        assert flags["flag1"] is True
        assert flags["flag2"] is False
    
    def test_load_flags_from_config(self, sequence_manager):
        """Тест загрузки флагов из конфигурации"""
        config = {"flags": {"config_flag": True}}
        sequence_manager.load_flags_from_config(config)
        assert sequence_manager.get_flag("config_flag") is True
    
    def test_extract_used_flags(self, sequence_manager):
        """Тест извлечения используемых флагов"""
        commands = ["if flag1", "command1", "stop_if_not flag2", "endif"]
        flags = sequence_manager._extract_used_flags(commands)
        assert "flag1" in flags
        assert "flag2" in flags
        assert len(flags) == 2


class TestConditionalState:
    """Тесты для ConditionalState"""
    
    def test_conditional_state_initialization(self):
        """Тест инициализации ConditionalState"""
        state = ConditionalState()
        assert state.in_conditional_block is False
        assert state.current_condition is True
        assert state.skip_until_endif is False
        assert state.condition_stack == []
