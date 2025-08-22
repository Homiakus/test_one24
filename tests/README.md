# Test Suite Documentation

## Overview

This directory contains comprehensive test coverage for the Arduino Control Panel application. The test suite is designed to ensure code quality, prevent regressions, and maintain high standards of reliability.

## Test Structure

```
tests/
├── conftest.py              # Common fixtures and configuration
├── unit/                    # Unit tests for core components
│   ├── test_command_executor.py
│   ├── test_di_container.py
│   ├── test_sequence_manager.py
│   └── ...
├── integration/             # Integration tests
│   ├── test_serial_communication.py
│   └── ...
├── ui/                      # UI tests with pytest-qt
│   ├── test_main_window.py
│   └── ...
├── fixtures/                # Test fixtures and data
├── utils/                   # Test utilities and helpers
│   └── test_helpers.py
└── README.md               # This file
```

## Test Categories

### 1. Unit Tests (`tests/unit/`)

Unit tests focus on testing individual components in isolation:

- **CommandExecutor**: Tests command execution, validation, and error handling
- **DIContainer**: Tests dependency injection, service registration, and resolution
- **SequenceManager**: Tests sequence management, execution, and validation
- **SerialManager**: Tests serial communication logic (mocked)
- **ConfigLoader**: Tests configuration loading and validation

### 2. Integration Tests (`tests/integration/`)

Integration tests verify how components work together:

- **Serial Communication**: Tests end-to-end serial communication with mocked hardware
- **Command Execution**: Tests command execution through the full stack
- **Sequence Execution**: Tests sequence execution with real dependencies

### 3. UI Tests (`tests/ui/`)

UI tests verify the user interface functionality:

- **MainWindow**: Tests window creation, event handling, and UI interactions
- **Widget Tests**: Tests individual UI components
- **User Interaction**: Tests mouse and keyboard interactions

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r requirements.txt
```

### Basic Test Execution

Run all tests:
```bash
pytest
```

Run specific test categories:
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# UI tests only
pytest tests/ui/
```

### Test Markers

Use pytest markers to run specific test types:

```bash
# Run unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Run UI tests
pytest -m ui

# Run serial communication tests
pytest -m serial

# Run Qt-specific tests
pytest -m qt

# Run slow tests
pytest -m slow
```

### Coverage Reports

Generate coverage reports:

```bash
# Generate coverage report
pytest --cov=core --cov=ui --cov=utils --cov=config --cov-report=html

# View coverage in terminal
pytest --cov=core --cov=ui --cov=utils --cov=config --cov-report=term-missing

# Generate XML coverage for CI
pytest --cov=core --cov=ui --cov=utils --cov=config --cov-report=xml
```

### Parallel Execution

Run tests in parallel for faster execution:

```bash
pytest -n auto  # Uses all available CPU cores
pytest -n 4     # Uses 4 parallel processes
```

## Test Configuration

### pytest.ini

The test configuration is defined in `pyproject.toml`:

- **Test paths**: `tests/`
- **Coverage**: 80% minimum coverage required
- **Markers**: Custom markers for different test types
- **Output**: HTML, XML, and terminal reports

### Coverage Configuration

Coverage settings:
- **Source**: `core`, `ui`, `utils`, `config`
- **Exclude**: Test files, cache directories, virtual environments
- **Minimum**: 80% coverage required

## Test Utilities

### TestDataFactory

Creates test data for various components:

```python
from tests.utils.test_helpers import TestDataFactory

# Create serial config
config = TestDataFactory.create_serial_config("COM1", 9600)

# Create command data
command = TestDataFactory.create_command_data("test_cmd", "CMD1")

# Create sequence data
sequence = TestDataFactory.create_sequence_data("test_sequence")
```

### MockFactory

Creates mock objects for testing:

```python
from tests.utils.test_helpers import MockFactory

# Create mock serial interface
mock_serial = MockFactory.create_serial_interface()

# Create mock command interface
mock_command = MockFactory.create_command_interface()

# Create DI container
container = MockFactory.create_di_container()
```

### AsyncTestHelper

Helper for async testing:

```python
from tests.utils.test_helpers import AsyncTestHelper

# Run async function
result = AsyncTestHelper.run_async(async_function())

# Wait for condition
await AsyncTestHelper.wait_for_condition(lambda: some_condition())
```

### UITestHelper

Helper for UI testing:

```python
from tests.utils.test_helpers import UITestHelper

# Create test app
app = UITestHelper.create_test_app()

# Wait for widget
UITestHelper.wait_for_widget(widget)

# Simulate user interaction
UITestHelper.simulate_user_interaction(widget, "click")
```

## CI/CD Integration

### GitHub Actions

The CI/CD pipeline includes:

1. **Test Matrix**: Tests on multiple OS and Python versions
2. **Linting**: Code quality checks with ruff and mypy
3. **Coverage**: Coverage reporting and badge generation
4. **Security**: Security checks with bandit and safety
5. **Documentation**: Automatic documentation building
6. **Deployment**: Automated releases and deployment

### Local CI

Run CI checks locally:

```bash
# Linting
ruff check .
mypy .

# Security checks
bandit -r .
safety check

# All tests with coverage
pytest --cov=core --cov=ui --cov=utils --cov=config --cov-report=html --cov-fail-under=80
```

## Best Practices

### Writing Tests

1. **Test Naming**: Use descriptive test names that explain what is being tested
2. **Arrange-Act-Assert**: Structure tests with clear sections
3. **Isolation**: Each test should be independent and not rely on other tests
4. **Mocking**: Use mocks for external dependencies
5. **Coverage**: Aim for high test coverage, especially for critical paths

### Example Test Structure

```python
def test_command_execution_success(self, command_executor, mock_interface):
    """Test successful command execution."""
    # Arrange
    command = "TEST_CMD"
    expected_result = {"status": "success", "data": "test"}
    mock_interface.execute_command.return_value = expected_result
    
    # Act
    result = command_executor.execute_command(command)
    
    # Assert
    assert result == expected_result
    mock_interface.execute_command.assert_called_once_with(command)
```

### Test Data Management

1. **Fixtures**: Use pytest fixtures for reusable test data
2. **Factories**: Use factory classes for creating test objects
3. **Cleanup**: Ensure proper cleanup of test resources
4. **Isolation**: Each test should have its own data

### Performance Testing

For performance-critical code:

```python
@pytest.mark.performance
def test_command_execution_performance(self, command_executor):
    """Test command execution performance."""
    from tests.utils.test_helpers import PerformanceTestHelper
    
    # Benchmark function
    stats = PerformanceTestHelper.benchmark_function(
        command_executor.execute_command, 
        iterations=1000, 
        command="TEST_CMD"
    )
    
    assert stats["mean"] < 0.001  # Should complete in less than 1ms
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in Python path
2. **Qt Tests**: Qt tests require a display (use Xvfb on headless systems)
3. **Serial Tests**: Serial tests use mocks, no real hardware needed
4. **Coverage**: Ensure all source files are included in coverage

### Debugging Tests

```bash
# Run tests with verbose output
pytest -v

# Run tests with print statements
pytest -s

# Run specific test with debugger
pytest tests/unit/test_command_executor.py::TestCommandExecutor::test_execute_command_success -s --pdb

# Run tests with coverage and show missing lines
pytest --cov=core --cov-report=term-missing
```

### Test Environment

For consistent test environment:

```bash
# Create virtual environment
python -m venv test_env
source test_env/bin/activate  # Linux/Mac
# or
test_env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

## Contributing

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Add appropriate markers for test categorization
3. Ensure tests are isolated and don't depend on each other
4. Add documentation for complex test scenarios
5. Update this README if adding new test categories or utilities

## Coverage Goals

- **Core Components**: 90%+ coverage
- **UI Components**: 80%+ coverage
- **Integration Tests**: 85%+ coverage
- **Overall Project**: 80%+ coverage

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-qt Documentation](https://pytest-qt.readthedocs.io/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
