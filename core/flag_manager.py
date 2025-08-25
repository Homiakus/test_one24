"""
Менеджер флагов и переменных
"""
import logging
from typing import Dict, Any, Optional
from threading import Lock


class FlagManager:
    """Менеджер глобальных флагов и переменных"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._flags: Dict[str, Any] = {}
        self._lock = Lock()
        
        # Инициализируем стандартные флаги
        self._init_default_flags()
    
    def _init_default_flags(self):
        """Инициализация стандартных флагов"""
        self.set_flag('wanted', False)
        self.logger.info("Инициализированы стандартные флаги")
    
    def set_flag(self, flag_name: str, value: Any) -> None:
        """
        Установить значение флага
        
        Args:
            flag_name: Имя флага
            value: Значение флага
        """
        with self._lock:
            self._flags[flag_name] = value
            self.logger.debug(f"Флаг {flag_name} установлен в {value}")
    
    def get_flag(self, flag_name: str, default: Any = None) -> Any:
        """
        Получить значение флага
        
        Args:
            flag_name: Имя флага
            default: Значение по умолчанию
            
        Returns:
            Значение флага
        """
        with self._lock:
            return self._flags.get(flag_name, default)
    
    def has_flag(self, flag_name: str) -> bool:
        """
        Проверить наличие флага
        
        Args:
            flag_name: Имя флага
            
        Returns:
            True если флаг существует
        """
        with self._lock:
            return flag_name in self._flags
    
    def remove_flag(self, flag_name: str) -> bool:
        """
        Удалить флаг
        
        Args:
            flag_name: Имя флага
            
        Returns:
            True если флаг был удален
        """
        with self._lock:
            if flag_name in self._flags:
                del self._flags[flag_name]
                self.logger.debug(f"Флаг {flag_name} удален")
                return True
            return False
    
    def get_all_flags(self) -> Dict[str, Any]:
        """
        Получить все флаги
        
        Returns:
            Словарь всех флагов
        """
        with self._lock:
            return self._flags.copy()
    
    def clear_flags(self) -> None:
        """Очистить все флаги"""
        with self._lock:
            self._flags.clear()
            self._init_default_flags()
            self.logger.info("Все флаги очищены и переинициализированы")
    
    def toggle_flag(self, flag_name: str) -> bool:
        """
        Переключить булевый флаг
        
        Args:
            flag_name: Имя флага
            
        Returns:
            Новое значение флага
        """
        with self._lock:
            current_value = self._flags.get(flag_name, False)
            new_value = not current_value
            self._flags[flag_name] = new_value
            self.logger.debug(f"Флаг {flag_name} переключен с {current_value} на {new_value}")
            return new_value
    
    def increment_flag(self, flag_name: str, step: int = 1) -> int:
        """
        Увеличить числовой флаг
        
        Args:
            flag_name: Имя флага
            step: Шаг увеличения
            
        Returns:
            Новое значение флага
        """
        with self._lock:
            current_value = self._flags.get(flag_name, 0)
            if isinstance(current_value, (int, float)):
                new_value = current_value + step
                self._flags[flag_name] = new_value
                self.logger.debug(f"Флаг {flag_name} увеличен с {current_value} до {new_value}")
                return new_value
            else:
                self.logger.warning(f"Флаг {flag_name} не является числовым")
                return current_value
    
    def decrement_flag(self, flag_name: str, step: int = 1) -> int:
        """
        Уменьшить числовой флаг
        
        Args:
            flag_name: Имя флага
            step: Шаг уменьшения
            
        Returns:
            Новое значение флага
        """
        return self.increment_flag(flag_name, -step)
