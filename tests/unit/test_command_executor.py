"""
Unit tests for BasicCommandExecutor class.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from core.command_executor import BasicCommandExecutor
from core.interfaces import ISerialManager


class TestBasicCommandExecutor:
    """Test cases for BasicCommandExecutor class."""

    @pytest.fixture
    def mock_serial_manager(self) -> Mock:
        """Create a mock serial manager."""
        mock = Mock(spec=ISerialManager)
        mock.is_connected = True
        mock.send_command.return_value = True
        return mock

    @pytest.fixture
    def command_executor(self, mock_serial_manager: Mock) -> BasicCommandExecutor:
        """Create a BasicCommandExecutor instance for testing."""
        return BasicCommandExecutor(mock_serial_manager)

    def test_init(self, mock_serial_manager: Mock):
        """Test BasicCommandExecutor initialization."""
        executor = BasicCommandExecutor(mock_serial_manager)
        assert executor.serial_manager == mock_serial_manager
        assert executor.timeout == 5.0

    def test_execute_command_success(self, command_executor: BasicCommandExecutor, mock_serial_manager: Mock):
        """Test successful command execution."""
        command = "TEST_CMD"
        
        result = command_executor.execute(command)
        
        assert result is True
        mock_serial_manager.send_command.assert_called_once_with(command)

    def test_execute_command_validation_failure(self, command_executor: BasicCommandExecutor):
        """Test command execution with validation failure."""
        command = ""
        result = command_executor.execute(command)
        
        assert result is False

    def test_execute_command_not_connected(self, mock_serial_manager: Mock):
        """Test command execution when not connected."""
        mock_serial_manager.is_connected = False
        executor = BasicCommandExecutor(mock_serial_manager)
        
        command = "TEST_CMD"
        result = executor.execute(command)
        
        assert result is False
        mock_serial_manager.send_command.assert_not_called()

    def test_execute_command_serial_error(self, command_executor: BasicCommandExecutor, mock_serial_manager: Mock):
        """Test command execution with serial error."""
        mock_serial_manager.send_command.return_value = False
        
        command = "ERROR_CMD"
        result = command_executor.execute(command)
        
        assert result is False

    def test_execute_command_exception(self, command_executor: BasicCommandExecutor, mock_serial_manager: Mock):
        """Test command execution with exception."""
        mock_serial_manager.send_command.side_effect = Exception("Serial error")
        
        command = "EXCEPTION_CMD"
        result = command_executor.execute(command)
        
        assert result is False

    def test_validate_command_valid(self, command_executor: BasicCommandExecutor):
        """Test command validation with valid command."""
        command = "VALID_CMD"
        result = command_executor.validate_command(command)
        assert result is True

    def test_validate_command_empty(self, command_executor: BasicCommandExecutor):
        """Test command validation with empty command."""
        command = ""
        result = command_executor.validate_command(command)
        assert result is False

    def test_validate_command_whitespace(self, command_executor: BasicCommandExecutor):
        """Test command validation with whitespace only."""
        command = "   "
        result = command_executor.validate_command(command)
        assert result is False

    def test_validate_command_none(self, command_executor: BasicCommandExecutor):
        """Test command validation with None."""
        command = None
        result = command_executor.validate_command(command)
        assert result is False

    @pytest.mark.parametrize("command,expected", [
        ("", False),
        ("   ", False),
        ("VALID_CMD", True),
        ("cmd_with_underscores", True),
        ("CMD123", True),
    ])
    def test_is_valid_command_format(self, command_executor: BasicCommandExecutor, command: str, expected: bool):
        """Test command format validation."""
        result = command_executor.validate_command(command)
        assert result == expected

    def test_execute_with_parameters(self, command_executor: BasicCommandExecutor, mock_serial_manager: Mock):
        """Test command execution with additional parameters."""
        command = "TEST_CMD"
        params = {"timeout": 10.0, "retry": 3}
        
        result = command_executor.execute(command, **params)
        
        assert result is True
        mock_serial_manager.send_command.assert_called_once_with(command)

    def test_timeout_initialization(self, mock_serial_manager: Mock):
        """Test timeout initialization."""
        executor = BasicCommandExecutor(mock_serial_manager, timeout=15.0)
        assert executor.timeout == 15.0

    def test_logging_on_success(self, command_executor: BasicCommandExecutor, mock_serial_manager: Mock):
        """Test logging on successful command execution."""
        command = "SUCCESS_CMD"
        
        with patch.object(command_executor.logger, 'info') as mock_info:
            command_executor.execute(command)
            
            mock_info.assert_called_once_with(f"Команда выполнена: {command}")

    def test_logging_on_failure(self, command_executor: BasicCommandExecutor, mock_serial_manager: Mock):
        """Test logging on failed command execution."""
        mock_serial_manager.send_command.return_value = False
        command = "FAIL_CMD"
        
        with patch.object(command_executor.logger, 'error') as mock_error:
            command_executor.execute(command)
            
            mock_error.assert_called_once_with(f"Не удалось выполнить команду: {command}")

    def test_logging_on_invalid_command(self, command_executor: BasicCommandExecutor):
        """Test logging on invalid command."""
        command = ""
        
        with patch.object(command_executor.logger, 'error') as mock_error:
            command_executor.execute(command)
            
            mock_error.assert_called_once_with(f"Невалидная команда: {command}")

    def test_logging_on_not_connected(self, mock_serial_manager: Mock):
        """Test logging when not connected."""
        mock_serial_manager.is_connected = False
        executor = BasicCommandExecutor(mock_serial_manager)
        command = "TEST_CMD"
        
        with patch.object(executor.logger, 'error') as mock_error:
            executor.execute(command)
            
            mock_error.assert_called_once_with("Устройство не подключено")
