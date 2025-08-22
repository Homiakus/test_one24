"""
Test utilities and helper functions for comprehensive testing.
"""
import pytest
import tempfile
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Generator, Optional
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import serial

from core.interfaces import ISerialManager, ICommandExecutor
from core.di_container import DIContainer


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_serial_config(port: str = "COM1", baudrate: int = 9600) -> Dict[str, Any]:
        """Create serial configuration for testing."""
        return {
            "port": port,
            "baudrate": baudrate,
            "timeout": 1.0,
            "bytesize": serial.EIGHTBITS,
            "parity": serial.PARITY_NONE,
            "stopbits": serial.STOPBITS_ONE,
        }
    
    @staticmethod
    def create_command_data(name: str = "test_cmd", code: str = "CMD1") -> Dict[str, Any]:
        """Create command data for testing."""
        return {
            "name": name,
            "code": code,
            "description": f"Test command {name}",
            "parameters": {"param1": "value1"},
            "timeout": 5.0,
        }
    
    @staticmethod
    def create_sequence_data(name: str = "test_sequence") -> Dict[str, Any]:
        """Create sequence data for testing."""
        return {
            "name": name,
            "description": f"Test sequence {name}",
            "steps": [
                {"command": "CMD1", "delay": 1.0, "description": "Step 1"},
                {"command": "CMD2", "delay": 2.0, "description": "Step 2"},
                {"command": "CMD3", "delay": 0.5, "description": "Step 3"},
            ]
        }
    
    @staticmethod
    def create_ui_config() -> Dict[str, Any]:
        """Create UI configuration for testing."""
        return {
            "theme": "dark",
            "language": "en",
            "window_size": [800, 600],
            "window_position": [100, 100],
            "auto_save": True,
            "auto_connect": False,
        }
    
    @staticmethod
    def create_logging_config() -> Dict[str, Any]:
        """Create logging configuration for testing."""
        return {
            "level": "DEBUG",
            "file": "test.log",
            "max_size": 1024 * 1024,  # 1MB
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        }


class MockFactory:
    """Factory for creating mock objects."""
    
    @staticmethod
    def create_serial_interface() -> Mock:
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
        mock.in_waiting = 0
        mock.reset_input_buffer.return_value = None
        mock.reset_output_buffer.return_value = None
        return mock
    
    @staticmethod
    def create_command_interface() -> Mock:
        """Create a mock command interface."""
        mock = Mock(spec=ICommandExecutor)
        mock.execute_command.return_value = {"status": "success", "data": "test"}
        mock.execute_command_async = AsyncMock(return_value={"status": "success", "data": "test"})
        mock.validate_command.return_value = True
        mock.get_command_info.return_value = {"name": "Test Command", "description": "Test"}
        mock.list_commands.return_value = ["CMD1", "CMD2", "CMD3"]
        return mock
    
    @staticmethod
    def create_di_container() -> DIContainer:
        """Create a DI container for testing."""
        return DIContainer()


class AsyncTestHelper:
    """Helper for async testing."""
    
    @staticmethod
    def run_async(coro):
        """Run an async coroutine in a test."""
        return asyncio.run(coro)
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout: float = 5.0):
        """Wait for a condition to be true."""
        start_time = asyncio.get_event_loop().time()
        while not condition_func():
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Condition not met within {timeout} seconds")
            await asyncio.sleep(0.1)
    
    @staticmethod
    async def wait_for_event(event, timeout: float = 5.0):
        """Wait for an event to be set."""
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Event not set within {timeout} seconds")


class FileTestHelper:
    """Helper for file-based testing."""
    
    @staticmethod
    def create_temp_file(content: str = "", suffix: str = ".txt") -> Generator[str, None, None]:
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    @staticmethod
    def create_temp_config_file(config: Dict[str, Any]) -> Generator[str, None, None]:
        """Create a temporary config file for testing."""
        import tomli
        
        config_content = tomli.dumps(config)
        yield from FileTestHelper.create_temp_file(config_content, ".toml")
    
    @staticmethod
    def create_temp_json_file(data: Dict[str, Any]) -> Generator[str, None, None]:
        """Create a temporary JSON file for testing."""
        json_content = json.dumps(data, indent=2)
        yield from FileTestHelper.create_temp_file(json_content, ".json")


class SerialTestHelper:
    """Helper for serial communication testing."""
    
    @staticmethod
    def mock_serial_port():
        """Create a mock serial port for testing."""
        mock_port = Mock(spec=serial.Serial)
        mock_port.port = "COM1"
        mock_port.baudrate = 9600
        mock_port.timeout = 1.0
        mock_port.is_open = False
        mock_port.open.return_value = None
        mock_port.close.return_value = None
        mock_port.write.return_value = 10
        mock_port.read.return_value = b"OK\n"
        mock_port.readline.return_value = b"OK\n"
        mock_port.in_waiting = 0
        mock_port.reset_input_buffer.return_value = None
        mock_port.reset_output_buffer.return_value = None
        return mock_port
    
    @staticmethod
    def simulate_serial_responses(mock_port: Mock, responses: List[bytes]):
        """Simulate serial responses."""
        mock_port.readline.side_effect = responses
    
    @staticmethod
    def simulate_serial_errors(mock_port: Mock, error_type: type, error_message: str):
        """Simulate serial errors."""
        mock_port.readline.side_effect = error_type(error_message)


class UITestHelper:
    """Helper for UI testing."""
    
    @staticmethod
    def create_test_app():
        """Create a test QApplication."""
        from PySide6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    @staticmethod
    def wait_for_widget(widget, timeout: int = 5000):
        """Wait for a widget to be visible."""
        from PySide6.QtCore import QTimer, QEventLoop
        
        timer = QTimer()
        timer.setSingleShot(True)
        
        def check_visible():
            if widget.isVisible():
                loop.quit()
            else:
                timer.start(100)
        
        loop = QEventLoop()
        timer.timeout.connect(check_visible)
        timer.start(100)
        
        if not widget.isVisible():
            loop.exec()
    
    @staticmethod
    def simulate_user_interaction(widget, interaction_type: str, **kwargs):
        """Simulate user interaction with a widget."""
        from PySide6.QtTest import QTest
        from PySide6.QtCore import Qt
        
        if interaction_type == "click":
            QTest.mouseClick(widget, Qt.LeftButton, **kwargs)
        elif interaction_type == "double_click":
            QTest.mouseDClick(widget, Qt.LeftButton, **kwargs)
        elif interaction_type == "right_click":
            QTest.mouseClick(widget, Qt.RightButton, **kwargs)
        elif interaction_type == "key_press":
            key = kwargs.get('key', Qt.Key_Enter)
            modifier = kwargs.get('modifier', Qt.NoModifier)
            QTest.keyPress(widget, key, modifier)
        elif interaction_type == "text_input":
            text = kwargs.get('text', 'test')
            QTest.keyClicks(widget, text)


class PerformanceTestHelper:
    """Helper for performance testing."""
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs) -> float:
        """Measure execution time of a function."""
        import time
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        return end_time - start_time
    
    @staticmethod
    async def measure_async_execution_time(coro) -> float:
        """Measure execution time of an async coroutine."""
        import time
        
        start_time = time.time()
        result = await coro
        end_time = time.time()
        
        return end_time - start_time
    
    @staticmethod
    def benchmark_function(func, iterations: int = 1000, *args, **kwargs) -> Dict[str, float]:
        """Benchmark a function over multiple iterations."""
        import time
        import statistics
        
        times = []
        for _ in range(iterations):
            start_time = time.time()
            func(*args, **kwargs)
            end_time = time.time()
            times.append(end_time - start_time)
        
        return {
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "std": statistics.stdev(times) if len(times) > 1 else 0,
            "total": sum(times),
        }


class MemoryTestHelper:
    """Helper for memory testing."""
    
    @staticmethod
    def get_memory_usage():
        """Get current memory usage."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
    
    @staticmethod
    def measure_memory_growth(func, *args, **kwargs) -> Dict[str, int]:
        """Measure memory growth during function execution."""
        import gc
        
        # Force garbage collection
        gc.collect()
        
        initial_memory = MemoryTestHelper.get_memory_usage()
        result = func(*args, **kwargs)
        final_memory = MemoryTestHelper.get_memory_usage()
        
        return {
            "initial": initial_memory,
            "final": final_memory,
            "growth": final_memory - initial_memory,
        }


class NetworkTestHelper:
    """Helper for network testing."""
    
    @staticmethod
    def mock_network_request(response_data: Dict[str, Any], status_code: int = 200):
        """Mock a network request."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = response_data
            mock_response.status_code = status_code
            mock_get.return_value = mock_response
            return mock_get
    
    @staticmethod
    def simulate_network_delay(delay: float = 1.0):
        """Simulate network delay."""
        import time
        time.sleep(delay)


class DatabaseTestHelper:
    """Helper for database testing."""
    
    @staticmethod
    def create_temp_database():
        """Create a temporary database for testing."""
        import sqlite3
        import tempfile
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_file.close()
        
        conn = sqlite3.connect(temp_file.name)
        
        yield conn
        
        conn.close()
        os.unlink(temp_file.name)
    
    @staticmethod
    def setup_test_tables(conn):
        """Setup test tables in database."""
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value REAL
            )
        """)
        
        conn.commit()


class ValidationTestHelper:
    """Helper for validation testing."""
    
    @staticmethod
    def test_validation_with_valid_data(validator_func, valid_data: List[Dict[str, Any]]):
        """Test validation with valid data."""
        for data in valid_data:
            assert validator_func(data) is True, f"Validation failed for valid data: {data}"
    
    @staticmethod
    def test_validation_with_invalid_data(validator_func, invalid_data: List[Dict[str, Any]]):
        """Test validation with invalid data."""
        for data in invalid_data:
            assert validator_func(data) is False, f"Validation passed for invalid data: {data}"
    
    @staticmethod
    def test_validation_errors(validator_func, invalid_data: List[Dict[str, Any]], expected_errors: List[str]):
        """Test validation error messages."""
        for data, expected_error in zip(invalid_data, expected_errors):
            try:
                validator_func(data)
                assert False, f"Validation should have failed for: {data}"
            except ValueError as e:
                assert expected_error in str(e), f"Expected error '{expected_error}' not found in '{str(e)}'"


# Pytest markers for different test types
pytest_plugins = [
    "pytest_asyncio",
    "pytest_cov",
    "pytest_mock",
]

# Custom markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as a UI test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "serial: mark test as serial communication test"
    )
    config.addinivalue_line(
        "markers", "qt: mark test as Qt-specific test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "memory: mark test as memory test"
    )
    config.addinivalue_line(
        "markers", "network: mark test as network test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as database test"
    )
