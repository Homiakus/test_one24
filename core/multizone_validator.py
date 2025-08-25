"""
@file: multizone_validator.py
@description: Валидация мультизональных операций
@dependencies: multizone_types.py
@created: 2025-01-25
"""

import re
import logging
from typing import Tuple, Optional, List
from .multizone_types import MultizoneCommand, MultizoneCommandType


class MultizoneValidator:
    """Валидатор мультизональных команд"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.multizone_pattern = re.compile(r'^og_multizone-([a-zA-Z0-9_-]+)$')
    
    def validate_multizone_command(self, command: str) -> Tuple[bool, Optional[MultizoneCommand]]:
        """Валидация мультизональной команды"""
        try:
            match = self.multizone_pattern.match(command)
            if not match:
                return False, None
            
            base_command = match.group(1)
            multizone_command = MultizoneCommand(
                command_type=MultizoneCommandType.ZONE_EXECUTION,
                base_command=base_command,
                zone_mask=0,  # Будет установлен позже
                zones=[]      # Будет установлен позже
            )
            
            return True, multizone_command
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации команды {command}: {e}")
            return False, None
    
    def validate_zone_mask(self, mask: int) -> bool:
        """Валидация битовой маски зон"""
        return 0 <= mask <= 15  # 4 бита = 0-15
    
    def validate_zone_list(self, zones: List[int]) -> bool:
        """Валидация списка зон"""
        if not zones:
            return False
        
        for zone in zones:
            if not 1 <= zone <= 4:
                return False
        
        return len(zones) == len(set(zones))  # Проверка уникальности
