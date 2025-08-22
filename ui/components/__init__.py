"""
Компоненты пользовательского интерфейса
"""

from .event_bus import EventBus
from .navigation_manager import NavigationManager
from .page_manager import PageManager
from .connection_manager import ConnectionManager

__all__ = [
    'EventBus',
    'NavigationManager', 
    'PageManager',
    'ConnectionManager'
]
