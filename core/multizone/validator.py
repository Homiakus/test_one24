"""
@file: multizone_validator.py
@description: Упрощенный валидатор мультизональных операций
@dependencies: multizone_types.py
@created: 2025-01-25
@updated: 2025-01-25 - Упрощение кода
"""

import re
import logging
from typing import Tuple, Optional
from .types import MultizoneCommand, MultizoneCommandType


class MultizoneValidator:
    """Упрощенный валидатор мультизональных команд"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.multizone_pattern = re.compile(r'^og_multizone-([a-zA-Z0-9_-]+)$')
    
    def validate_multizone_command(self, command: str) -> Tuple[bool, Optional[MultizoneCommand]]:
        """Валидация мультизональной команды"""
        match = self.multizone_pattern.match(command)
        if not match:
            return False, None
        
        base_command = match.group(1)
        multizone_command = MultizoneCommand(
            command_type=MultizoneCommandType.ZONE_EXECUTION,
            base_command=base_command,
            zone_mask=0,
            zones=[]
        )
        
        return True, multizone_command
    
    def validate_zone_mask(self, mask: int) -> bool:
        """Валидация битовой маски зон"""
        return 0 <= mask <= 15  # 4 бита = 0-15
    
    def validate_zone_list(self, zones: list) -> bool:
        """Валидация списка зон"""
        return (zones and 
                all(1 <= zone <= 4 for zone in zones) and 
                len(zones) == len(set(zones)))
