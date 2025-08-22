"""
Common test fixtures and configuration.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Generator, Dict, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.interfaces import ISerialManager, ICommandExecutor
from core.di_container import DIContainer
from config.config_loader import ConfigLoader


@pytest.fixture
def temp_config_file() -> Generator[str, None, None]:
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write("""
[serial]
port = "COM1"
baudrate = 9600
timeout = 1.0

[ui]
theme = "dark"
language = "en"

[logging]
level = "INFO"
file = "test.log"
        """)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def mock_serial_interface() -> Mock:
    """Create a mock serial interface."""
    mock = Mock(spec=ISerialManager)
    mock.port = "COM1"
    mock.baudrate = 9600
    mock.is_open = False
    mock.open.return_value = None
    mock.close.return_value = None
    mock.write.return_value = 10
    mock.read.return_value = b"OK\n"
    mock.readline.return_value = b"OK\n"
    return mock


@pytest.fixture
def mock_command_interface() -> Mock:
    """Create a mock command interface."""
    mock = Mock(spec=ICommandExecutor)
    mock.execute_command.return_value = {"status": "success", "data": "test"}
    mock.validate_command.return_value = True
    return mock


@pytest.fixture
def di_container() -> DIContainer:
    """Create a DI container for testing."""
    container = DIContainer()
    return container


@pytest.fixture
def config_loader(temp_config_file: str) -> ConfigLoader:
    """Create a config loader with test configuration."""
    return ConfigLoader(temp_config_file)


@pytest.fixture
def test_data() -> Dict[str, Any]:
    """Provide test data for various tests."""
    return {
        "commands": [
            {"name": "test_cmd1", "code": "CMD1", "description": "Test command 1"},
            {"name": "test_cmd2", "code": "CMD2", "description": "Test command 2"},
        ],
        "sequences": [
            {
                "name": "test_sequence",
                "steps": [
                    {"command": "CMD1", "delay": 1.0},
                    {"command": "CMD2", "delay": 2.0},
                ]
            }
        ],
        "serial_settings": {
            "port": "COM1",
            "baudrate": 9600,
            "timeout": 1.0,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
        }
    }


@pytest.fixture
def qtbot(qtbot):
    """Enhanced qtbot fixture for UI testing."""
    return qtbot


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    yield
    
    # Cleanup after test
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    if "LOG_LEVEL" in os.environ:
        del os.environ["LOG_LEVEL"]


@pytest.fixture
def mock_file_system():
    """Mock file system operations."""
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.read_text') as mock_read, \
         patch('pathlib.Path.write_text') as mock_write:
        
        mock_exists.return_value = True
        mock_read.return_value = "test content"
        mock_write.return_value = None
        
        yield {
            'exists': mock_exists,
            'read_text': mock_read,
            'write_text': mock_write
        }


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    with patch('utils.logger.logger') as mock_log:
        mock_log.info.return_value = None
        mock_log.error.return_value = None
        mock_log.debug.return_value = None
        mock_log.warning.return_value = None
        
        yield mock_log
