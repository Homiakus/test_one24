"""
Unit tests for SequenceManager class.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any, List

from core.sequence_manager import SequenceManager
from core.interfaces import ICommandExecutor


class TestSequenceManager:
    """Test cases for SequenceManager class."""

    @pytest.fixture
    def mock_command_interface(self) -> Mock:
        """Create a mock command interface."""
        mock = Mock(spec=ICommandExecutor)
        mock.execute.return_value = True
        mock.execute_async = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def sequence_manager(self, mock_command_interface: Mock) -> SequenceManager:
        """Create a SequenceManager instance for testing."""
        config = {
            "test_sequence": ["CMD1", "CMD2", "CMD3"],
            "nested_sequence": ["BUTTON1", "CMD2", "nested_sequence2"],
            "nested_sequence2": ["CMD4", "CMD5"]
        }
        buttons_config = {
            "BUTTON1": "CMD1",
            "BUTTON2": "CMD2",
            "BUTTON3": "CMD3"
        }
        return SequenceManager(config, buttons_config)

    def test_init(self, mock_command_interface: Mock):
        """Test SequenceManager initialization."""
        config = {"test_seq": ["CMD1", "CMD2"]}
        buttons_config = {"BUTTON1": "CMD1"}
        
        manager = SequenceManager(config, buttons_config)
        assert manager.sequences == config
        assert manager.buttons_config == buttons_config

    def test_expand_sequence_simple(self, sequence_manager: SequenceManager):
        """Test expanding a simple sequence."""
        result = sequence_manager.expand_sequence("test_sequence")
        
        assert result == ["CMD1", "CMD2", "CMD3"]

    def test_expand_sequence_with_buttons(self, sequence_manager: SequenceManager):
        """Test expanding a sequence with button references."""
        config = {"button_sequence": ["BUTTON1", "BUTTON2"]}
        buttons_config = {"BUTTON1": "CMD1", "BUTTON2": "CMD2"}
        manager = SequenceManager(config, buttons_config)
        
        result = manager.expand_sequence("button_sequence")
        
        assert result == ["CMD1", "CMD2"]

    def test_expand_sequence_nested(self, sequence_manager: SequenceManager):
        """Test expanding a nested sequence."""
        result = sequence_manager.expand_sequence("nested_sequence")
        
        # Should expand to: CMD1 (from BUTTON1), CMD2, CMD4, CMD5 (from nested_sequence2)
        assert result == ["CMD1", "CMD2", "CMD4", "CMD5"]

    def test_expand_sequence_not_found(self, sequence_manager: SequenceManager):
        """Test expanding a non-existent sequence."""
        result = sequence_manager.expand_sequence("non_existent")
        
        assert result == []

    def test_validate_sequence_valid(self, sequence_manager: SequenceManager):
        """Test validating a valid sequence."""
        is_valid, errors = sequence_manager.validate_sequence("test_sequence")
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_sequence_invalid(self, sequence_manager: SequenceManager):
        """Test validating an invalid sequence."""
        # Create a sequence with invalid commands
        config = {"invalid_sequence": ["INVALID_CMD", "CMD2"]}
        buttons_config = {"BUTTON1": "CMD1"}
        manager = SequenceManager(config, buttons_config)
        
        is_valid, errors = manager.validate_sequence("invalid_sequence")
        
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_sequence_not_found(self, sequence_manager: SequenceManager):
        """Test validating a non-existent sequence."""
        is_valid, errors = sequence_manager.validate_sequence("non_existent")
        
        assert is_valid is False
        assert len(errors) > 0

    def test_get_sequence_info(self, sequence_manager: SequenceManager):
        """Test getting sequence information."""
        info = sequence_manager.get_sequence_info("test_sequence")
        
        assert isinstance(info, dict)
        assert "name" in info
        assert "commands" in info
        assert info["name"] == "test_sequence"

    def test_get_sequence_info_not_found(self, sequence_manager: SequenceManager):
        """Test getting info for non-existent sequence."""
        info = sequence_manager.get_sequence_info("non_existent")
        
        assert isinstance(info, dict)
        assert info.get("name") == "non_existent"
        assert info.get("commands") == []

    def test_clear_cache(self, sequence_manager: SequenceManager):
        """Test clearing the cache."""
        # First expand a sequence to populate cache
        sequence_manager.expand_sequence("test_sequence")
        
        # Clear cache
        sequence_manager.clear_cache()
        
        # Should still work after clearing cache
        result = sequence_manager.expand_sequence("test_sequence")
        assert result == ["CMD1", "CMD2", "CMD3"]

    def test_recursion_protection(self, sequence_manager: SequenceManager):
        """Test protection against recursive sequences."""
        # Create a recursive sequence
        config = {
            "recursive_seq": ["CMD1", "recursive_seq", "CMD2"]
        }
        buttons_config = {}
        manager = SequenceManager(config, buttons_config)
        
        result = manager.expand_sequence("recursive_seq")
        
        # Should handle recursion gracefully
        assert "CMD1" in result
        assert "CMD2" in result

    def test_wait_commands(self, sequence_manager: SequenceManager):
        """Test handling of wait commands."""
        config = {
            "wait_sequence": ["CMD1", "wait 1s", "CMD2"]
        }
        buttons_config = {}
        manager = SequenceManager(config, buttons_config)
        
        result = manager.expand_sequence("wait_sequence")
        
        assert "CMD1" in result
        assert "wait 1s" in result
        assert "CMD2" in result

    def test_mixed_commands(self, sequence_manager: SequenceManager):
        """Test handling of mixed command types."""
        config = {
            "mixed_sequence": ["BUTTON1", "wait 2s", "CMD2", "nested_sequence2"]
        }
        buttons_config = {"BUTTON1": "CMD1"}
        manager = SequenceManager(config, buttons_config)
        
        result = manager.expand_sequence("mixed_sequence")
        
        assert "CMD1" in result  # From BUTTON1
        assert "wait 2s" in result
        assert "CMD2" in result
        assert "CMD4" in result  # From nested_sequence2
        assert "CMD5" in result  # From nested_sequence2
