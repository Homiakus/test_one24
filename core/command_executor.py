"""
Исполнитель команд
"""
import logging
import time
from typing import Optional, Dict, Any, Callable
from abc import ABC, abstractmethod


class CommandExecutor(ABC):
    """Абстрактный исполнитель команд"""

    def __init__(self, serial_manager):
        self.serial_manager = serial_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def execute(self, command: str, **kwargs) -> bool:
        """
        Выполнение команды

        Args:
            command: Команда для выполнения
            **kwargs: Дополнительные параметры

        Returns:
            True при успешном выполнении
        """
        pass

    def validate_command(self, command: str) -> bool:
        """
        Валидация команды

        Args:
            command: Команда для проверки

        Returns:
            True если команда валидна
        """
        return bool(command and command.strip())


class BasicCommandExecutor(CommandExecutor):
    """Базовый исполнитель команд"""

    def __init__(self, serial_manager, timeout: float = 5.0):
        super().__init__(serial_manager)
        self.timeout = timeout

    def execute(self, command: str, **kwargs) -> bool:
        """
        Выполнение команды через Serial

        Args:
            command: Команда для выполнения
            **kwargs: Дополнительные параметры

        Returns:
            True при успешном выполнении
        """
        if not self.validate_command(command):
            self.logger.error(f"Невалидная команда: {command}")
            return False

        if not self.serial_manager.is_connected:
            self.logger.error("Устройство не подключено")
            return False

        try:
            success = self.serial_manager.send_command(command)

            if success:
                self.logger.info(f"Команда выполнена: {command}")
            else:
                self.logger.error(f"Не удалось выполнить команду: {command}")

            return success

        except Exception as e:
            self.logger.error(f"Ошибка выполнения команды '{command}': {e}")
            return False


class InteractiveCommandExecutor(CommandExecutor):
    """Интерактивный исполнитель команд с ожиданием ответа"""

    def __init__(self, serial_manager, timeout: float = 10.0,
                 success_keywords: Optional[list] = None,
                 error_keywords: Optional[list] = None):
        super().__init__(serial_manager)
        self.timeout = timeout
        self.success_keywords = success_keywords or ['ok', 'complete', 'done']
        self.error_keywords = error_keywords or ['error', 'fail', 'err']

    def execute(self, command: str, **kwargs) -> bool:
        """
        Выполнение команды с ожиданием ответа

        Args:
            command: Команда для выполнения
            **kwargs: Дополнительные параметры

        Returns:
            True при успешном выполнении
        """
        if not self.validate_command(command):
            self.logger.error(f"Невалидная команда: {command}")
            return False

        if not self.serial_manager.is_connected:
            self.logger.error("Устройство не подключено")
            return False

        try:
            # Отправляем команду
            if not self.serial_manager.send_command(command):
                return False

            self.logger.info(f"Команда отправлена, ожидание ответа: {command}")

            # Ожидаем ответ
            return self._wait_for_response()

        except Exception as e:
            self.logger.error(f"Ошибка выполнения команды '{command}': {e}")
            return False

    def _wait_for_response(self) -> bool:
        """Ожидание ответа от устройства"""
        start_time = time.time()
        responses = []

        while time.time() - start_time < self.timeout:
            # Здесь должен быть механизм получения ответов
            # В реальной реализации это будет через сигналы или коллбэки
            time.sleep(0.1)

            # Имитация получения ответа (в реальности будет через сигналы)
            if hasattr(self.serial_manager, '_last_response'):
                response = self.serial_manager._last_response.lower()

                # Проверяем на успех
                if any(keyword in response for keyword in self.success_keywords):
                    self.logger.info(f"Получен успешный ответ: {response}")
                    return True

                # Проверяем на ошибку
                if any(keyword in response for keyword in self.error_keywords):
                    self.logger.error(f"Получена ошибка: {response}")
                    return False

        self.logger.warning("Таймаут ожидания ответа")
        return False


class CommandExecutorFactory:
    """Фабрика исполнителей команд"""

    EXECUTORS = {
        'basic': BasicCommandExecutor,
        'interactive': InteractiveCommandExecutor,
    }

    @classmethod
    def create_executor(cls, executor_type: str, serial_manager, **kwargs):
        """
        Создание исполнителя команд

        Args:
            executor_type: Тип исполнителя
            serial_manager: Менеджер Serial
            **kwargs: Дополнительные параметры

        Returns:
            Экземпляр исполнителя
        """
        executor_class = cls.EXECUTORS.get(executor_type)
        if executor_class:
            return executor_class(serial_manager, **kwargs)

        # По умолчанию используем базовый
        return BasicCommandExecutor(serial_manager, **kwargs)
