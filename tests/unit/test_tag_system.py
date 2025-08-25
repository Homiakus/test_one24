"""
Unit тесты для системы тегов команд
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from core.tag_types import TagType, TagInfo, TagResult, ParsedCommand
from core.tag_manager import TagManager
from core.tag_validator import TagValidator
from core.tag_processor import TagProcessor, BaseTagProcessor
from core.tags.wanted_tag import WantedTag
from core.flag_manager import FlagManager
from ui.dialogs.tag_dialogs import TagDialogManager, WantedTagDialog


class TestTagTypes:
    """Тесты для типов данных тегов"""
    
    def test_tag_type_enum(self):
        """Тест enum TagType"""
        assert TagType.WANTED == TagType.WANTED
        assert TagType.WANTED.value == "wanted"
    
    def test_tag_info_dataclass(self):
        """Тест dataclass TagInfo"""
        tag_info = TagInfo(
            tag_type=TagType.WANTED,
            tag_name="_wanted",
            parameters={},
            position=10
        )
        assert tag_info.tag_type == TagType.WANTED
        assert tag_info.tag_name == "_wanted"
        assert tag_info.parameters == {}
        assert tag_info.position == 10
    
    def test_tag_result_dataclass(self):
        """Тест dataclass TagResult"""
        result = TagResult(
            success=True,
            should_continue=True,
            message="OK",
            data={"key": "value"}
        )
        assert result.success is True
        assert result.should_continue is True
        assert result.message == "OK"
        assert result.data == {"key": "value"}
    
    def test_parsed_command_dataclass(self):
        """Тест dataclass ParsedCommand"""
        tag_info = TagInfo(
            tag_type=TagType.WANTED,
            tag_name="_wanted",
            parameters={},
            position=10
        )
        parsed = ParsedCommand(
            base_command="test_command",
            tags=[tag_info],
            original_command="test_command_wanted"
        )
        assert parsed.base_command == "test_command"
        assert len(parsed.tags) == 1
        assert parsed.tags[0].tag_type == TagType.WANTED
        assert parsed.original_command == "test_command_wanted"


class TestTagManager:
    """Тесты для TagManager"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.tag_manager = TagManager()
        self.flag_manager = FlagManager()
    
    def test_parse_command_no_tags(self):
        """Тест парсинга команды без тегов"""
        result = self.tag_manager.parse_command("simple_command")
        assert result.base_command == "simple_command"
        assert len(result.tags) == 0
        assert result.original_command == "simple_command"
    
    def test_parse_command_with_wanted_tag(self):
        """Тест парсинга команды с тегом _wanted"""
        result = self.tag_manager.parse_command("test_command_wanted")
        assert result.base_command == "test_command"
        assert len(result.tags) == 1
        assert result.tags[0].tag_type == TagType.WANTED
        assert result.tags[0].tag_name == "_wanted"
        assert result.original_command == "test_command_wanted"
    
    def test_parse_command_multiple_tags(self):
        """Тест парсинга команды с несколькими тегами"""
        result = self.tag_manager.parse_command("test_command_wanted_another")
        assert result.base_command == "test_command"
        assert len(result.tags) == 2
        assert result.tags[0].tag_type == TagType.WANTED
        assert result.tags[1].tag_name == "_another"
    
    def test_has_tags(self):
        """Тест проверки наличия тегов"""
        assert self.tag_manager._has_tags("command_wanted") is True
        assert self.tag_manager._has_tags("simple_command") is False
        assert self.tag_manager._has_tags("command_wanted_another") is True
    
    def test_validate_tags(self):
        """Тест валидации тегов"""
        tag_info = TagInfo(
            tag_type=TagType.WANTED,
            tag_name="_wanted",
            parameters={},
            position=10
        )
        assert self.tag_manager.validate_tags([tag_info]) is True
    
    def test_process_tags(self):
        """Тест обработки тегов"""
        tag_info = TagInfo(
            tag_type=TagType.WANTED,
            tag_name="_wanted",
            parameters={},
            position=10
        )
        context = {"flag_manager": self.flag_manager}
        
        results = self.tag_manager.process_tags([tag_info], context)
        assert len(results) == 1
        assert isinstance(results[0], TagResult)


class TestTagValidator:
    """Тесты для TagValidator"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.validator = TagValidator()
    
    def test_validate_tag_name_valid(self):
        """Тест валидации корректного имени тега"""
        assert self.validator.validate_tag_name("_wanted") is True
        assert self.validator.validate_tag_name("_test_tag") is True
        assert self.validator.validate_tag_name("_tag123") is True
    
    def test_validate_tag_name_invalid(self):
        """Тест валидации некорректного имени тега"""
        assert self.validator.validate_tag_name("wanted") is False  # без подчеркивания
        assert self.validator.validate_tag_name("_") is False  # только подчеркивание
        assert self.validator.validate_tag_name("_123tag") is False  # начинается с цифры
    
    def test_validate_tag_type(self):
        """Тест валидации типа тега"""
        assert self.validator.validate_tag_type(TagType.WANTED) is True
        assert self.validator.validate_tag_type("invalid_type") is False
    
    def test_validate_tag(self):
        """Тест валидации тега"""
        tag_info = TagInfo(
            tag_type=TagType.WANTED,
            tag_name="_wanted",
            parameters={},
            position=10
        )
        assert self.validator.validate_tag(tag_info) is True
    
    def test_validate_command_with_tags(self):
        """Тест валидации команды с тегами"""
        assert self.validator.validate_command_with_tags("command_wanted") is True
        assert self.validator.validate_command_with_tags("simple_command") is True
        assert self.validator.validate_command_with_tags("command_invalid") is False


class TestWantedTag:
    """Тесты для WantedTag"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.wanted_tag = WantedTag()
        self.flag_manager = FlagManager()
    
    def test_process_wanted_false(self):
        """Тест обработки тега _wanted когда wanted=False"""
        self.flag_manager.set_flag('wanted', False)
        tag_info = TagInfo(
            tag_type=TagType.WANTED,
            tag_name="_wanted",
            parameters={},
            position=10
        )
        context = {"flag_manager": self.flag_manager}
        
        result = self.wanted_tag.process(tag_info, context)
        assert result.success is True
        assert result.should_continue is True
        assert "wanted=False" in result.message
    
    def test_process_wanted_true(self):
        """Тест обработки тега _wanted когда wanted=True"""
        self.flag_manager.set_flag('wanted', True)
        tag_info = TagInfo(
            tag_type=TagType.WANTED,
            tag_name="_wanted",
            parameters={},
            position=10
        )
        context = {"flag_manager": self.flag_manager}
        
        result = self.wanted_tag.process(tag_info, context)
        assert result.success is True
        assert result.should_continue is False
        assert "wanted=True" in result.message
        assert result.data.get("show_dialog") == "wanted"
    
    def test_validate(self):
        """Тест валидации тега"""
        tag_info = TagInfo(
            tag_type=TagType.WANTED,
            tag_name="_wanted",
            parameters={},
            position=10
        )
        assert self.wanted_tag.validate(tag_info) is True
    
    def test_get_supported_tag_types(self):
        """Тест получения поддерживаемых типов тегов"""
        supported = self.wanted_tag.get_supported_tag_types()
        assert TagType.WANTED in supported
        assert len(supported) == 1


class TestFlagManager:
    """Тесты для FlagManager"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.flag_manager = FlagManager()
    
    def test_set_and_get_flag(self):
        """Тест установки и получения флага"""
        self.flag_manager.set_flag('test_flag', True)
        assert self.flag_manager.get_flag('test_flag') is True
        assert self.flag_manager.get_flag('nonexistent', False) is False
    
    def test_has_flag(self):
        """Тест проверки наличия флага"""
        self.flag_manager.set_flag('test_flag', True)
        assert self.flag_manager.has_flag('test_flag') is True
        assert self.flag_manager.has_flag('nonexistent') is False
    
    def test_remove_flag(self):
        """Тест удаления флага"""
        self.flag_manager.set_flag('test_flag', True)
        assert self.flag_manager.remove_flag('test_flag') is True
        assert self.flag_manager.has_flag('test_flag') is False
        assert self.flag_manager.remove_flag('nonexistent') is False
    
    def test_get_all_flags(self):
        """Тест получения всех флагов"""
        self.flag_manager.set_flag('flag1', True)
        self.flag_manager.set_flag('flag2', "value")
        flags = self.flag_manager.get_all_flags()
        assert 'flag1' in flags
        assert 'flag2' in flags
        assert flags['flag1'] is True
        assert flags['flag2'] == "value"
    
    def test_clear_flags(self):
        """Тест очистки всех флагов"""
        self.flag_manager.set_flag('test_flag', True)
        self.flag_manager.clear_flags()
        assert self.flag_manager.has_flag('test_flag') is False
        # Проверяем, что стандартные флаги переинициализированы
        assert self.flag_manager.has_flag('wanted') is True
    
    def test_toggle_flag(self):
        """Тест переключения булевого флага"""
        self.flag_manager.set_flag('test_flag', False)
        assert self.flag_manager.toggle_flag('test_flag') is True
        assert self.flag_manager.get_flag('test_flag') is True
        assert self.flag_manager.toggle_flag('test_flag') is False
        assert self.flag_manager.get_flag('test_flag') is False
    
    def test_increment_decrement_flag(self):
        """Тест увеличения и уменьшения числового флага"""
        self.flag_manager.set_flag('counter', 5)
        assert self.flag_manager.increment_flag('counter') == 6
        assert self.flag_manager.get_flag('counter') == 6
        assert self.flag_manager.decrement_flag('counter') == 5
        assert self.flag_manager.get_flag('counter') == 5


class TestTagDialogManager:
    """Тесты для TagDialogManager"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.dialog_manager = TagDialogManager()
    
    def test_get_supported_dialog_types(self):
        """Тест получения поддерживаемых типов диалогов"""
        types = self.dialog_manager.get_supported_dialog_types()
        assert 'wanted' in types
    
    @patch('ui.dialogs.tag_dialogs.WantedTagDialog')
    def test_show_tag_dialog_wanted(self, mock_dialog_class):
        """Тест показа диалога wanted"""
        mock_dialog = Mock()
        mock_dialog.show_dialog.return_value = "check_fluids"
        mock_dialog_class.return_value = mock_dialog
        
        result = self.dialog_manager.show_tag_dialog('wanted')
        assert result == "check_fluids"
        mock_dialog_class.assert_called_once()
        mock_dialog.show_dialog.assert_called_once()
    
    def test_show_tag_dialog_unknown(self):
        """Тест показа неизвестного диалога"""
        result = self.dialog_manager.show_tag_dialog('unknown')
        assert result is None
    
    @patch('ui.dialogs.tag_dialogs.WantedTagDialog')
    def test_show_tag_dialog_with_callback(self, mock_dialog_class):
        """Тест показа диалога с callback"""
        mock_dialog = Mock()
        mock_dialog.show_dialog.return_value = "check_fluids"
        mock_dialog_class.return_value = mock_dialog
        
        callback_called = False
        def test_callback(result):
            nonlocal callback_called
            callback_called = True
            assert result == "check_fluids"
        
        self.dialog_manager.on_wanted_dialog_result = test_callback
        result = self.dialog_manager.show_tag_dialog('wanted')
        
        assert result == "check_fluids"
        assert callback_called is True


class TestWantedTagDialog:
    """Тесты для WantedTagDialog"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.dialog = WantedTagDialog()
    
    def test_dialog_initialization(self):
        """Тест инициализации диалога"""
        assert self.dialog.result_action is None
        assert self.dialog.windowTitle() == "Проверка жидкостей"
    
    def test_get_result(self):
        """Тест получения результата"""
        assert self.dialog.get_result() is None
        self.dialog.result_action = "test"
        assert self.dialog.get_result() == "test"
    
    @patch('PySide6.QtWidgets.QDialog.exec')
    def test_show_dialog_check_fluids(self, mock_exec):
        """Тест показа диалога с выбором 'check_fluids'"""
        mock_exec.return_value = 1  # Accepted
        self.dialog.result_action = "check_fluids"
        
        result = self.dialog.show_dialog()
        assert result == "check_fluids"
    
    @patch('PySide6.QtWidgets.QDialog.exec')
    def test_show_dialog_cancel(self, mock_exec):
        """Тест показа диалога с отменой"""
        mock_exec.return_value = 0  # Rejected
        self.dialog.result_action = "cancel"
        
        result = self.dialog.show_dialog()
        assert result == "cancel"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
