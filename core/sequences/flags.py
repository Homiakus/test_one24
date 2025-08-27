"""
Модуль для управления глобальными флагами.

Содержит класс FlagManager для управления флагами, используемыми
в условном выполнении команд.
"""

import threading
from typing import Dict, Any


class FlagManager:
    """Менеджер глобальных флагов для условного выполнения"""
    
    def __init__(self):
        self._flags: Dict[str, bool] = {}
        self._lock = threading.Lock()
    
    def set_flag(self, flag_name: str, value: bool) -> None:
        """Установить значение флага"""
        with self._lock:
            self._flags[flag_name] = value
    
    def get_flag(self, flag_name: str, default: bool = False) -> bool:
        """Получить значение флага"""
        with self._lock:
            return self._flags.get(flag_name, default)
    
    def has_flag(self, flag_name: str) -> bool:
        """Проверить существование флага"""
        with self._lock:
            return flag_name in self._flags
    
    def clear_flag(self, flag_name: str) -> None:
        """Очистить флаг"""
        with self._lock:
            self._flags.pop(flag_name, None)
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Получить все флаги"""
        with self._lock:
            return self._flags.copy()
    
    def load_flags_from_config(self, config: Dict[str, Any]) -> None:
        """Загрузить флаги из конфигурации"""
        flags_section = config.get('flags', {})
        with self._lock:
            for flag_name, value in flags_section.items():
                if isinstance(value, bool):
                    self._flags[flag_name] = value
    
    def clear_all_flags(self) -> None:
        """Очистить все флаги"""
        with self._lock:
            self._flags.clear()
    
    def get_flags_count(self) -> int:
        """Получить количество флагов"""
        with self._lock:
            return len(self._flags)

