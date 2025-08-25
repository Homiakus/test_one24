"""
Исполнитель команд
"""
import logging
import time
from typing import Optional, Dict, Any, Callable, List
from abc import ABC, abstractmethod

from .multizone_manager import MultizoneManager, ZoneStatus
from .tag_manager import TagManager
from .tag_types import TagResult


class CommandExecutor(ABC):
    """Абстрактный исполнитель команд"""

    def __init__(self, serial_manager, tag_manager: Optional[TagManager] = None, tag_dialog_manager: Optional['TagDialogManager'] = None):
        self.serial_manager = serial_manager
        self.tag_manager = tag_manager
        self.tag_dialog_manager = tag_dialog_manager
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
    
    def _has_tags(self, command: str) -> bool:
        """Проверить, содержит ли команда теги"""
        return '_' in command and any(part.startswith('_') for part in command.split())
    
    def _process_tags(self, command: str, context: Dict[str, Any]) -> bool:
        """
        Обработка тегов в команде
        
        Args:
            command: Команда с тегами
            context: Контекст выполнения
            
        Returns:
            True если можно продолжить выполнение
        """
        if not self.tag_manager or not self._has_tags(command):
            return True
        
        try:
            # Парсим команду с тегами
            parsed_command = self.tag_manager.parse_command(command)
            
            # Обрабатываем теги
            tag_results = self.tag_manager.process_tags(parsed_command.tags, context)
            
            for result in tag_results:
                if not result.success:
                    self.logger.error(f"Ошибка обработки тега: {result.message}")
                    return False
                
                if not result.should_continue:
                    # Нужно показать диалог
                    if result.data and result.data.get('show_dialog'):
                        if self.tag_dialog_manager:
                            dialog_result = self.tag_dialog_manager.show_tag_dialog(
                                result.data.get('dialog_type', 'unknown'),
                                parent=context.get('parent')
                            )
                            
                            if dialog_result == 'cancel':
                                self.logger.info("Пользователь отменил операцию")
                                return False
                            
                            # Пользователь подтвердил, продолжаем
                            self.logger.info("Пользователь подтвердил операцию, продолжаем выполнение")
                        else:
                            self.logger.warning("TagDialogManager не доступен, пропускаем диалог")
                    
                    return True  # Продолжаем выполнение после диалога
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки тегов: {e}")
            return False


class BasicCommandExecutor(CommandExecutor):
    """Базовый исполнитель команд"""

    def __init__(self, serial_manager, timeout: float = 5.0, multizone_manager: Optional[MultizoneManager] = None, 
                 tag_manager: Optional[TagManager] = None, tag_dialog_manager: Optional['TagDialogManager'] = None):
        super().__init__(serial_manager, tag_manager, tag_dialog_manager)
        self.timeout = timeout
        self.multizone_manager = multizone_manager

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

        # Проверяем мультизональные команды
        if command.startswith("og_multizone-"):
            return self._execute_multizone_command(command, **kwargs)

        # Обрабатываем теги перед выполнением команды
        if not self._process_tags(command, kwargs):
            self.logger.warning(f"Обработка тегов прервала выполнение команды: {command}")
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

    def _execute_multizone_command(self, command: str, **kwargs) -> bool:
        """
        Выполнение мультизональной команды
        
        Args:
            command: Мультизональная команда
            **kwargs: Дополнительные параметры
            
        Returns:
            True при успешном выполнении
        """
        if not self.multizone_manager:
            self.logger.error("MultizoneManager не инициализирован")
            return False

        try:
            # Извлекаем базовую команду
            base_command = command[13:]  # Убираем "og_multizone-"
            
            # Обрабатываем теги в базовой команде
            if not self._process_tags(base_command, kwargs):
                self.logger.warning(f"Обработка тегов прервала выполнение мультизональной команды: {command}")
                return False
            
            # Получаем активные зоны
            active_zones = self.multizone_manager.get_active_zones()
            if not active_zones:
                self.logger.warning(f"Мультизональная команда '{command}' пропущена: нет активных зон")
                return True

            self.logger.info(f"Выполнение мультизональной команды '{command}' для зон: {active_zones}")

            # Выполняем команду для каждой активной зоны
            for zone_id in active_zones:
                # Устанавливаем статус зоны "выполняется"
                self.multizone_manager.set_zone_status(zone_id, ZoneStatus.EXECUTING)
                
                # Отправляем команду установки маски для текущей зоны
                zone_mask = self.multizone_manager._get_zone_bit(zone_id)
                zone_mask_command = f"multizone {zone_mask:04b}"
                
                if not self.serial_manager.send_command(zone_mask_command):
                    self.logger.error(f"Ошибка установки маски для зоны {zone_id}")
                    self.multizone_manager.set_zone_status(zone_id, ZoneStatus.ERROR)
                    return False

                # Отправляем базовую команду
                if not self.serial_manager.send_command(base_command):
                    self.logger.error(f"Ошибка выполнения команды для зоны {zone_id}")
                    self.multizone_manager.set_zone_status(zone_id, ZoneStatus.ERROR)
                    return False

                # Устанавливаем статус зоны "завершено"
                self.multizone_manager.set_zone_status(zone_id, ZoneStatus.COMPLETED)
                self.logger.info(f"Команда выполнена для зоны {zone_id}")

            return True

        except Exception as e:
            self.logger.error(f"Ошибка выполнения мультизональной команды '{command}': {e}")
            return False


class InteractiveCommandExecutor(CommandExecutor):
    """Интерактивный исполнитель команд с ожиданием ответа"""

    def __init__(self, serial_manager, timeout: float = 10.0,
                 success_keywords: Optional[list] = None,
                 error_keywords: Optional[list] = None,
                 multizone_manager: Optional[MultizoneManager] = None,
                 tag_manager: Optional[TagManager] = None, tag_dialog_manager: Optional['TagDialogManager'] = None):
        super().__init__(serial_manager, tag_manager, tag_dialog_manager)
        self.timeout = timeout
        self.success_keywords = success_keywords or ['ok', 'complete', 'done']
        self.error_keywords = error_keywords or ['error', 'fail', 'err']
        self.multizone_manager = multizone_manager

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

        # Проверяем мультизональные команды
        if command.startswith("og_multizone-"):
            return self._execute_multizone_command(command, **kwargs)

        # Обрабатываем теги перед выполнением команды
        if not self._process_tags(command, kwargs):
            self.logger.warning(f"Обработка тегов прервала выполнение команды: {command}")
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

    def _execute_multizone_command(self, command: str, **kwargs) -> bool:
        """
        Выполнение мультизональной команды с ожиданием ответа
        
        Args:
            command: Мультизональная команда
            **kwargs: Дополнительные параметры
            
        Returns:
            True при успешном выполнении
        """
        if not self.multizone_manager:
            self.logger.error("MultizoneManager не инициализирован")
            return False

        try:
            # Извлекаем базовую команду
            base_command = command[13:]  # Убираем "og_multizone-"
            
            # Обрабатываем теги в базовой команде
            if not self._process_tags(base_command, kwargs):
                self.logger.warning(f"Обработка тегов прервала выполнение мультизональной команды: {command}")
                return False
            
            # Получаем активные зоны
            active_zones = self.multizone_manager.get_active_zones()
            if not active_zones:
                self.logger.warning(f"Мультизональная команда '{command}' пропущена: нет активных зон")
                return False

            self.logger.info(f"Выполнение мультизональной команды '{command}' для зон: {active_zones}")

            # Выполняем команду для каждой активной зоны
            for zone_id in active_zones:
                # Устанавливаем статус зоны "выполняется"
                self.multizone_manager.set_zone_status(zone_id, ZoneStatus.EXECUTING)
                
                # Отправляем команду установки маски для текущей зоны
                zone_mask = self.multizone_manager._get_zone_bit(zone_id)
                zone_mask_command = f"multizone {zone_mask:04b}"
                
                if not self.serial_manager.send_command(zone_mask_command):
                    self.logger.error(f"Ошибка установки маски для зоны {zone_id}")
                    self.multizone_manager.set_zone_status(zone_id, ZoneStatus.ERROR)
                    return False

                # Ожидаем ответа на команду маски
                if not self._wait_for_response():
                    self.logger.error(f"Таймаут ответа на команду маски для зоны {zone_id}")
                    self.multizone_manager.set_zone_status(zone_id, ZoneStatus.ERROR)
                    return False

                # Отправляем базовую команду
                if not self.serial_manager.send_command(base_command):
                    self.logger.error(f"Ошибка выполнения команды для зоны {zone_id}")
                    self.multizone_manager.set_zone_status(zone_id, ZoneStatus.ERROR)
                    return False

                # Ожидаем ответа на базовую команду
                if not self._wait_for_response():
                    self.logger.error(f"Таймаут ответа на команду для зоны {zone_id}")
                    self.multizone_manager.set_zone_status(zone_id, ZoneStatus.ERROR)
                    return False

                # Устанавливаем статус зоны "завершено"
                self.multizone_manager.set_zone_status(zone_id, ZoneStatus.COMPLETED)
                self.logger.info(f"Команда выполнена для зоны {zone_id}")

            return True

        except Exception as e:
            self.logger.error(f"Ошибка выполнения мультизональной команды '{command}': {e}")
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
    def create_executor(cls, executor_type: str, serial_manager, multizone_manager: Optional[MultizoneManager] = None, 
                       tag_manager: Optional[TagManager] = None, tag_dialog_manager: Optional['TagDialogManager'] = None, **kwargs):
        """
        Создание исполнителя команд

        Args:
            executor_type: Тип исполнителя
            serial_manager: Менеджер Serial
            multizone_manager: Менеджер мультизональных операций
            tag_manager: Менеджер тегов
            tag_dialog_manager: Менеджер диалогов тегов
            **kwargs: Дополнительные параметры

        Returns:
            Экземпляр исполнителя
        """
        executor_class = cls.EXECUTORS.get(executor_type)
        if executor_class:
            return executor_class(serial_manager, multizone_manager=multizone_manager, 
                                tag_manager=tag_manager, tag_dialog_manager=tag_dialog_manager, **kwargs)

        # По умолчанию используем базовый
        return BasicCommandExecutor(serial_manager, multizone_manager=multizone_manager, 
                                  tag_manager=tag_manager, tag_dialog_manager=tag_dialog_manager, **kwargs)
