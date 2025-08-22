"""
Integration tests for SerialManager class.
"""
import pytest
import serial
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from core.serial_manager import SerialManager


class TestSerialCommunication:
    """Test cases for SerialManager integration."""

    @pytest.fixture
    def serial_manager(self) -> SerialManager:
        """Create a SerialManager instance for testing."""
        return SerialManager()

    @pytest.fixture
    def mock_serial_port(self) -> Mock:
        """Create a mock serial port."""
        mock = Mock()
        mock.port = "COM1"
        mock.baudrate = 9600
        mock.is_open = False
        mock.open.return_value = None
        mock.close.return_value = None
        mock.write.return_value = 10
        mock.read.return_value = b"RESPONSE\n"
        mock.readline.return_value = b"LINE_RESPONSE\n"
        mock.in_waiting = 0
        mock.reset_input_buffer.return_value = None
        mock.reset_output_buffer.return_value = None
        return mock

    @pytest.fixture
    def test_serial_config(self) -> Dict[str, Any]:
        """Create test serial configuration."""
        return {
            "port": "COM1",
            "baudrate": 9600,
            "timeout": 1.0,
            "bytesize": serial.EIGHTBITS,
            "parity": serial.PARITY_NONE,
            "stopbits": serial.STOPBITS_ONE,
        }

    def test_serial_connection_establishment(self, serial_manager: SerialManager, mock_serial_port: Mock, test_serial_config: Dict[str, Any]):
        """Test establishing serial connection."""
        with patch('serial.Serial', return_value=mock_serial_port):
            with patch.object(serial_manager, 'get_available_ports', return_value=['COM1']):
                result = serial_manager.connect(test_serial_config["port"], test_serial_config["baudrate"])
                
                assert result is True
                assert serial_manager.is_connected is True
                mock_serial_port.open.assert_called_once()

    def test_serial_connection_failure(self, mock_serial_port: Mock, test_serial_config: Dict[str, Any]):
        """Test serial connection failure."""
        mock_serial_port.open.side_effect = serial.SerialException("Port not found")
        
        with patch('serial.Serial', return_value=mock_serial_port):
            manager = SerialManager()
            with patch.object(manager, 'get_available_ports', return_value=['COM1']):
                result = manager.connect(test_serial_config["port"], test_serial_config["baudrate"])
                
                assert result is False
                assert manager.is_connected is False

    def test_serial_disconnection(self, serial_manager: SerialManager, mock_serial_port: Mock, test_serial_config: Dict[str, Any]):
        """Test serial disconnection."""
        with patch('serial.Serial', return_value=mock_serial_port):
            with patch.object(serial_manager, 'get_available_ports', return_value=['COM1']):
                # First connect
                serial_manager.connect(test_serial_config["port"], test_serial_config["baudrate"])
                assert serial_manager.is_connected is True
                
                # Then disconnect
                serial_manager.disconnect()
                
                assert serial_manager.is_connected is False
                mock_serial_port.close.assert_called_once()

    def test_serial_send_command(self, serial_manager: SerialManager, mock_serial_port: Mock, test_serial_config: Dict[str, Any]):
        """Test sending command."""
        with patch('serial.Serial', return_value=mock_serial_port):
            with patch.object(serial_manager, 'get_available_ports', return_value=['COM1']):
                serial_manager.connect(test_serial_config["port"], test_serial_config["baudrate"])
                
                command = "TEST_CMD"
                result = serial_manager.send_command(command)
                
                assert result is True
                mock_serial_port.write.assert_called_once_with(f"{command}\n".encode())

    def test_serial_send_command_not_connected(self, serial_manager: SerialManager):
        """Test sending command when not connected."""
        command = "TEST_CMD"
        result = serial_manager.send_command(command)
        
        assert result is False

    def test_serial_get_port_info(self, serial_manager: SerialManager, mock_serial_port: Mock, test_serial_config: Dict[str, Any]):
        """Test getting port information."""
        with patch('serial.Serial', return_value=mock_serial_port):
            with patch.object(serial_manager, 'get_available_ports', return_value=['COM1']):
                serial_manager.connect(test_serial_config["port"], test_serial_config["baudrate"])
                
                info = serial_manager.get_port_info()
                
                assert info['connected'] is True
                assert info['port'] == 'COM1'
                assert info['baudrate'] == 9600

    def test_serial_get_port_info_not_connected(self, serial_manager: SerialManager):
        """Test getting port information when not connected."""
        info = serial_manager.get_port_info()
        
        assert info['connected'] is False
        assert info['port'] is None

    def test_serial_get_available_ports(self, serial_manager: SerialManager):
        """Test getting available ports."""
        with patch('serial.tools.list_ports.comports') as mock_comports:
            mock_port = Mock()
            mock_port.device = "COM1"
            mock_comports.return_value = [mock_port]
            
            ports = serial_manager.get_available_ports()
            
            assert "COM1" in ports

    def test_serial_connection_timeout(self, mock_serial_port: Mock, test_serial_config: Dict[str, Any]):
        """Test connection timeout."""
        mock_serial_port.open.side_effect = serial.SerialTimeoutException("Connection timeout")
        
        with patch('serial.Serial', return_value=mock_serial_port):
            manager = SerialManager()
            with patch.object(manager, 'get_available_ports', return_value=['COM1']):
                result = manager.connect(test_serial_config["port"], test_serial_config["baudrate"])
                
                assert result is False

    def test_serial_connection_port_not_found(self, test_serial_config: Dict[str, Any]):
        """Test connection when port is not found."""
        with patch('serial.Serial', side_effect=serial.SerialException("Port not found")):
            manager = SerialManager()
            with patch.object(manager, 'get_available_ports', return_value=[]):
                result = manager.connect(test_serial_config["port"], test_serial_config["baudrate"])
                
                assert result is False

    def test_serial_multiple_connections(self, serial_manager: SerialManager, mock_serial_port: Mock, test_serial_config: Dict[str, Any]):
        """Test multiple connection attempts."""
        with patch('serial.Serial', return_value=mock_serial_port):
            with patch.object(serial_manager, 'get_available_ports', return_value=['COM1']):
                # First connection
                result1 = serial_manager.connect(test_serial_config["port"], test_serial_config["baudrate"])
                assert result1 is True
                
                # Second connection (should return True as already connected)
                result2 = serial_manager.connect(test_serial_config["port"], test_serial_config["baudrate"])
                assert result2 is True

    def test_serial_reconnection(self, serial_manager: SerialManager, mock_serial_port: Mock, test_serial_config: Dict[str, Any]):
        """Test reconnection after disconnection."""
        with patch('serial.Serial', return_value=mock_serial_port):
            with patch.object(serial_manager, 'get_available_ports', return_value=['COM1']):
                # First connection
                result1 = serial_manager.connect(test_serial_config["port"], test_serial_config["baudrate"])
                assert result1 is True
                
                # Disconnect
                serial_manager.disconnect()
                assert serial_manager.is_connected is False
                
                # Reconnect
                result2 = serial_manager.connect(test_serial_config["port"], test_serial_config["baudrate"])
                assert result2 is True
                assert serial_manager.is_connected is True

    def test_serial_connection_with_custom_parameters(self, serial_manager: SerialManager, mock_serial_port: Mock):
        """Test connection with custom parameters."""
        with patch('serial.Serial', return_value=mock_serial_port):
            with patch.object(serial_manager, 'get_available_ports', return_value=['COM2']):
                result = serial_manager.connect("COM2", 115200, timeout=2.0, bytesize=serial.EIGHTBITS)
                
                assert result is True
                mock_serial_port.open.assert_called_once()

    def test_serial_connection_state_consistency(self, serial_manager: SerialManager, mock_serial_port: Mock, test_serial_config: Dict[str, Any]):
        """Test connection state consistency."""
        with patch('serial.Serial', return_value=mock_serial_port):
            with patch.object(serial_manager, 'get_available_ports', return_value=['COM1']):
                # Check initial state
                assert serial_manager.is_connected is False
                
                # Connect
                result = serial_manager.connect(test_serial_config["port"], test_serial_config["baudrate"])
                assert result is True
                assert serial_manager.is_connected is True
                
                # Check port info
                info = serial_manager.get_port_info()
                assert info['connected'] is True
                
                # Disconnect
                serial_manager.disconnect()
                assert serial_manager.is_connected is False
                
                # Check port info after disconnect
                info = serial_manager.get_port_info()
                assert info['connected'] is False
