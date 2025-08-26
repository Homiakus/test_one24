"""
Ядро приложения - работа с устройством

Этот пакет содержит все основные компоненты системы:
- DI контейнер (core.di)
- Управление сигналами (core.signals)
- Управление тегами (core.tags)
- Управление мультизоной (core.multizone)
- Управление последовательностями (core.sequences)
- Управление связью (core.communication)
"""

# Экспорт основных пакетов
from . import di
from . import signals
from . import tags
from . import multizone
from . import sequences
from . import communication

# Экспорт интерфейсов
from .interfaces import *

# Экспорт основных компонентов
from .command_executor import CommandExecutor
from .flag_manager import FlagManager

__all__ = [
    # Пакеты
    'di',
    'signals', 
    'tags',
    'multizone',
    'sequences',
    'communication',
    
    # Основные компоненты
    'CommandExecutor',
    'FlagManager'
]
