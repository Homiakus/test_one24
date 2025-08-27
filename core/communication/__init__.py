"""
Пакет для управления коммуникацией.

Этот пакет содержит модули для управления последовательными соединениями,
протоколами связи и потоками данных.
"""

from .connection import SerialConnection
from .protocol import SerialProtocol
from .threading import InterruptibleThread, ThreadManager
from .manager import SerialManager

__all__ = [
    # Connection
    'SerialConnection',
    
    # Protocol
    'SerialProtocol',
    
    # Threading
    'InterruptibleThread',
    'ThreadManager',
    
    # Manager
    'SerialManager'
]

