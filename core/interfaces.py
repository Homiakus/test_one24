"""
Интерфейсы для всех сервисов приложения.

Этот модуль содержит абстрактные базовые классы (ABC) для всех основных
сервисов приложения, обеспечивая контракты для реализации и поддержку
dependency injection.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Protocol, Callable, Union
from dataclasses import dataclass

from .tag_types import TagType, TagInfo, TagResult, ParsedCommand
from .signal_types import SignalType, SignalInfo, SignalMapping, SignalValue, SignalResult


class ISerialManager(ABC):
    """
    Интерфейс для менеджера Serial соединения.
    
    Определяет контракт для работы с последовательными портами,
    включая подключение, отправку команд и получение информации о портах.
    """
    
    @abstractmethod
    def connect(self, port: str, baudrate: int = 115200, timeout: float = 1.0, **kwargs: Any) -> bool:
        """
        Подключение к Serial-порту.
        
        Args:
            port: Имя порта (например, 'COM4' или '/dev/ttyUSB0')
            baudrate: Скорость передачи данных в бодах
            timeout: Таймаут чтения в секундах
            **kwargs: Дополнительные параметры подключения
            
        Returns:
            True если подключение успешно, False в противном случае
            
        Raises:
            SerialException: При ошибке подключения к порту
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Отключение от порта.
        
        Закрывает активное соединение и освобождает ресурсы.
        """
        pass
    
    @abstractmethod
    def send_command(self, command: str) -> bool:
        """
        Отправка команды на устройство.
        
        Args:
            command: Команда для отправки (строка)
            
        Returns:
            True если команда отправлена успешно, False в противном случае
            
        Raises:
            SerialException: При ошибке отправки команды
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Проверка состояния подключения.
        
        Returns:
            True если подключение активно, False в противном случае
        """
        pass
    
    @abstractmethod
    def get_available_ports(self) -> List[str]:
        """
        Получение списка доступных портов.
        
        Returns:
            Список имен доступных последовательных портов
        """
        pass
    
    @abstractmethod
    def get_port_info(self) -> Dict[str, Any]:
        """
        Получение информации о текущем порте.
        
        Returns:
            Словарь с информацией о порте (имя, настройки, статус)
        """
        pass


class ICommandExecutor(ABC):
    """
    Интерфейс для исполнителя команд.
    
    Определяет контракт для выполнения команд на устройстве,
    включая валидацию и обработку результатов.
    """
    
    @abstractmethod
    def execute(self, command: str, **kwargs: Any) -> bool:
        """
        Выполнение команды на устройстве.
        
        Args:
            command: Команда для выполнения
            **kwargs: Дополнительные параметры выполнения
            
        Returns:
            True если команда выполнена успешно, False в противном случае
            
        Raises:
            CommandExecutionError: При ошибке выполнения команды
        """
        pass
    
    @abstractmethod
    def validate_command(self, command: str) -> bool:
        """
        Валидация команды перед выполнением.
        
        Args:
            command: Команда для валидации
            
        Returns:
            True если команда валидна, False в противном случае
        """
        pass


class ISequenceManager(ABC):
    """Интерфейс для менеджера последовательностей"""
    
    @abstractmethod
    def expand_sequence(self, sequence_name: str) -> List[str]:
        """Разворачивание последовательности в список команд"""
        pass
    
    @abstractmethod
    def validate_sequence(self, sequence_name: str) -> tuple[bool, List[str]]:
        """Валидация последовательности"""
        pass
    
    @abstractmethod
    def get_sequence_info(self, sequence_name: str) -> Dict[str, Any]:
        """Получение информации о последовательности"""
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """Очистка кеша"""
        pass


class IConfigLoader(ABC):
    """Интерфейс для загрузчика конфигурации"""
    
    @abstractmethod
    def load(self) -> Optional[Dict[str, Any]]:
        """Загрузка конфигурации"""
        pass
    
    @abstractmethod
    def save(self, config: Dict[str, Any]) -> bool:
        """Сохранение конфигурации"""
        pass
    
    @abstractmethod
    def reload(self) -> Optional[Dict[str, Any]]:
        """Перезагрузка конфигурации"""
        pass


class ISettingsManager(ABC):
    """Интерфейс для менеджера настроек"""
    
    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Получение настройки"""
        pass
    
    @abstractmethod
    def set_setting(self, key: str, value: Any) -> bool:
        """Установка настройки"""
        pass
    
    @abstractmethod
    def save_settings(self) -> bool:
        """Сохранение настроек"""
        pass
    
    @abstractmethod
    def load_settings(self) -> bool:
        """Загрузка настроек"""
        pass


class ILogger(ABC):
    """Интерфейс для логгера"""
    
    @abstractmethod
    def debug(self, message: str) -> None:
        """Логирование отладочной информации"""
        pass
    
    @abstractmethod
    def info(self, message: str) -> None:
        """Логирование информационных сообщений"""
        pass
    
    @abstractmethod
    def warning(self, message: str) -> None:
        """Логирование предупреждений"""
        pass
    
    @abstractmethod
    def error(self, message: str) -> None:
        """Логирование ошибок"""
        pass
    
    @abstractmethod
    def critical(self, message: str) -> None:
        """Логирование критических ошибок"""
        pass


class IThreadManager(ABC):
    """Интерфейс для менеджера потоков"""
    
    @abstractmethod
    def start_thread(self, name: str, target: callable, **kwargs) -> Any:
        """Запуск потока"""
        pass
    
    @abstractmethod
    def stop_thread(self, name: str, timeout: float = None) -> bool:
        """Остановка потока"""
        pass
    
    @abstractmethod
    def stop_all_threads(self, timeout: float = 10.0) -> Dict[str, bool]:
        """Остановка всех потоков"""
        pass
    
    @abstractmethod
    def get_thread_info(self) -> Dict[str, Dict]:
        """Получение информации о потоках"""
        pass


class IEventBus(ABC):
    """Интерфейс для шины событий"""
    
    @abstractmethod
    def subscribe(self, event_type: str, callback: callable) -> None:
        """Подписка на событие"""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, callback: callable) -> None:
        """Отписка от события"""
        pass
    
    @abstractmethod
    def publish(self, event_type: str, data: Any = None) -> None:
        """Публикация события"""
        pass


class IConnectionManager(ABC):
    """Интерфейс для менеджера соединений"""
    
    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """Подключение"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Отключение"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Проверка подключения"""
        pass
    
    @abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """Получение информации о соединении"""
        pass


class INavigationManager(ABC):
    """Интерфейс для менеджера навигации"""
    
    @abstractmethod
    def navigate_to(self, page_name: str) -> bool:
        """Переход на страницу"""
        pass
    
    @abstractmethod
    def go_back(self) -> bool:
        """Возврат назад"""
        pass
    
    @abstractmethod
    def get_current_page(self) -> str:
        """Получение текущей страницы"""
        pass
    
    @abstractmethod
    def get_navigation_history(self) -> List[str]:
        """Получение истории навигации"""
        pass


class IPageManager(ABC):
    """Интерфейс для менеджера страниц"""
    
    @abstractmethod
    def register_page(self, name: str, page_class: type) -> None:
        """Регистрация страницы"""
        pass
    
    @abstractmethod
    def get_page(self, name: str) -> Optional[Any]:
        """Получение страницы"""
        pass
    
    @abstractmethod
    def create_page(self, name: str, **kwargs) -> Optional[Any]:
        """Создание страницы"""
        pass
    
    @abstractmethod
    def get_registered_pages(self) -> List[str]:
        """Получение списка зарегистрированных страниц"""
        pass


@dataclass
class ServiceRegistration:
    """
    Регистрация сервиса в DI контейнере.
    
    Attributes:
        interface: Интерфейс сервиса (абстрактный класс)
        implementation: Реализация сервиса (конкретный класс)
        singleton: True если сервис должен быть синглтоном
        factory: Фабричная функция для создания экземпляра
        dependencies: Словарь зависимостей {имя_параметра: имя_сервиса}
    """
    interface: type
    implementation: type
    singleton: bool = True
    factory: Optional[Callable[..., Any]] = None
    dependencies: Optional[Dict[str, str]] = None


class IDIContainer(ABC):
    """
    Интерфейс для DI контейнера.
    
    Определяет контракт для dependency injection контейнера,
    обеспечивающего управление зависимостями и жизненным циклом сервисов.
    """
    
    @abstractmethod
    def register(self, interface: type, implementation: type, 
                singleton: bool = True, factory: Optional[Callable[..., Any]] = None,
                dependencies: Optional[Dict[str, str]] = None) -> None:
        """
        Регистрация сервиса в контейнере.
        
        Args:
            interface: Интерфейс сервиса
            implementation: Реализация сервиса
            singleton: True если сервис должен быть синглтоном
            factory: Фабричная функция для создания экземпляра
            dependencies: Словарь зависимостей
        """
        pass
    
    @abstractmethod
    def resolve(self, interface: type) -> Any:
        """
        Разрешение зависимости по типу интерфейса.
        
        Args:
            interface: Тип интерфейса для разрешения
            
        Returns:
            Экземпляр реализации интерфейса
            
        Raises:
            ServiceNotFoundError: Если сервис не зарегистрирован
        """
        pass
    
    @abstractmethod
    def resolve_by_name(self, service_name: str) -> Any:
        """
        Разрешение зависимости по имени сервиса.
        
        Args:
            service_name: Имя зарегистрированного сервиса
            
        Returns:
            Экземпляр сервиса
            
        Raises:
            ServiceNotFoundError: Если сервис не найден
        """
        pass
    
    @abstractmethod
    def register_instance(self, interface: type, instance: Any) -> None:
        """
        Регистрация готового экземпляра сервиса.
        
        Args:
            interface: Интерфейс сервиса
            instance: Готовый экземпляр для регистрации
        """
        pass
    
    @abstractmethod
    def has_service(self, interface: type) -> bool:
        """
        Проверка наличия сервиса в контейнере.
        
        Args:
            interface: Тип интерфейса для проверки
            
        Returns:
            True если сервис зарегистрирован, False в противном случае
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """
        Очистка контейнера.
        
        Удаляет все зарегистрированные сервисы и экземпляры.
        """
        pass


class IMultizoneManager(ABC):
    """
    Интерфейс мультизонального менеджера.
    
    Определяет контракт для управления мультизональными операциями,
    включая установку зон, работу с битовыми масками и валидацию.
    """
    
    @abstractmethod
    def set_zones(self, zones: List[int]) -> bool:
        """
        Установка активных зон.
        
        Args:
            zones: Список номеров зон (1-4)
            
        Returns:
            True если зоны установлены успешно, False в противном случае
        """
        pass
    
    @abstractmethod
    def get_zone_mask(self) -> int:
        """
        Получение битовой маски зон.
        
        Returns:
            Битовая маска активных зон (0-15)
        """
        pass
    
    @abstractmethod
    def get_active_zones(self) -> List[int]:
        """
        Получение списка активных зон.
        
        Returns:
            Список номеров активных зон
        """
        pass
    
    @abstractmethod
    def is_zone_active(self, zone: int) -> bool:
        """
        Проверка активности зоны.
        
        Args:
            zone: Номер зоны для проверки
            
        Returns:
            True если зона активна, False в противном случае
        """
        pass
    
    @abstractmethod
    def validate_zones(self, zones: List[int]) -> bool:
        """
        Валидация выбора зон.
        
        Args:
            zones: Список зон для валидации
            
        Returns:
            True если зоны корректны, False в противном случае
        """
        pass


class ITagManager(ABC):
    """
    Интерфейс менеджера тегов команд.
    
    Определяет контракт для управления тегами команд,
    включая парсинг, валидацию и обработку тегов.
    """
    
    @abstractmethod
    def parse_command(self, command: str) -> ParsedCommand:
        """
        Парсинг команды с извлечением тегов.
        
        Args:
            command: Команда для парсинга
            
        Returns:
            Распарсенная команда с тегами
        """
        pass
    
    @abstractmethod
    def validate_tags(self, tags: List[TagInfo]) -> bool:
        """
        Валидация списка тегов.
        
        Args:
            tags: Список тегов для валидации
            
        Returns:
            True если все теги валидны, False в противном случае
        """
        pass
    
    @abstractmethod
    def process_tags(self, tags: List[TagInfo], context: Dict[str, Any]) -> List[TagResult]:
        """
        Обработка списка тегов.
        
        Args:
            tags: Список тегов для обработки
            context: Контекст выполнения (переменные, состояние)
            
        Returns:
            Список результатов обработки тегов
        """
        pass
    
    @abstractmethod
    def register_tag_processor(self, tag_type: TagType, processor: Callable) -> None:
        """
        Регистрация обработчика тега.
        
        Args:
            tag_type: Тип тега
            processor: Функция обработки тега
        """
        pass


class ITagProcessor(ABC):
    """
    Интерфейс обработчика тегов.
    
    Определяет контракт для обработки отдельных тегов,
    включая валидацию и выполнение логики тега.
    """
    
    @abstractmethod
    def process_tag(self, tag: TagInfo, context: Dict[str, Any]) -> TagResult:
        """
        Обработка отдельного тега.
        
        Args:
            tag: Информация о теге
            context: Контекст выполнения
            
        Returns:
            Результат обработки тега
        """
        pass
    
    @abstractmethod
    def validate_tag(self, tag: TagInfo) -> bool:
        """
        Валидация тега.
        
        Args:
            tag: Информация о теге
            
        Returns:
            True если тег валиден, False в противном случае
        """
        pass
    
    @abstractmethod
    def get_supported_tag_types(self) -> List[TagType]:
        """
        Получение поддерживаемых типов тегов.
        
        Returns:
            Список поддерживаемых типов тегов
        """
        pass


class IFlagManager(ABC):
    """
    Интерфейс менеджера флагов.
    
    Определяет контракт для управления глобальными флагами
    и переменными системы.
    """
    
    @abstractmethod
    def set_flag(self, flag_name: str, value: Any) -> None:
        """Установить значение флага"""
        pass
    
    @abstractmethod
    def get_flag(self, flag_name: str, default: Any = None) -> Any:
        """Получить значение флага"""
        pass
    
    @abstractmethod
    def has_flag(self, flag_name: str) -> bool:
        """Проверить наличие флага"""
        pass
    
    @abstractmethod
    def remove_flag(self, flag_name: str) -> bool:
        """Удалить флаг"""
        pass
    
    @abstractmethod
    def get_all_flags(self) -> Dict[str, Any]:
        """Получить все флаги"""
        pass
    
    @abstractmethod
    def clear_flags(self) -> None:
        """Очистить все флаги"""
        pass
    
    @abstractmethod
    def toggle_flag(self, flag_name: str) -> bool:
        """Переключить булевый флаг"""
        pass
    
    @abstractmethod
    def increment_flag(self, flag_name: str, step: int = 1) -> int:
        """Увеличить числовой флаг"""
        pass
    
    @abstractmethod
    def decrement_flag(self, flag_name: str, step: int = 1) -> int:
        """Уменьшить числовой флаг"""
        pass


class ITagValidator(ABC):
    """
    Интерфейс валидатора тегов.
    
    Определяет контракт для валидации тегов,
    включая проверку имен, типов и параметров.
    """
    
    @abstractmethod
    def validate_tag_name(self, tag_name: str) -> bool:
        """Валидация имени тега"""
        pass
    
    @abstractmethod
    def validate_tag_type(self, tag_type: TagType) -> bool:
        """Валидация типа тега"""
        pass
    
    @abstractmethod
    def validate_tag(self, tag: TagInfo) -> bool:
        """Валидация тега"""
        pass
    
    @abstractmethod
    def validate_tag_parameters(self, tag: TagInfo) -> bool:
        """Валидация параметров тега"""
        pass
    
    @abstractmethod
    def validate_tags(self, tags: List[TagInfo]) -> bool:
        """Валидация списка тегов"""
        pass
    
    @abstractmethod
    def validate_command_with_tags(self, command: str) -> bool:
        """Валидация команды с тегами"""
        pass
    
    @abstractmethod
    def get_supported_tag_types(self) -> List[TagType]:
        """Получить поддерживаемые типы тегов"""
        pass
    
    @abstractmethod
    def register_tag_type(self, tag_type: TagType, config: Dict[str, Any]) -> None:
        """Зарегистрировать новый тип тега"""
        pass


class ITagDialogManager(ABC):
    """
    Интерфейс менеджера диалогов тегов.
    
    Определяет контракт для управления и отображения
    диалогов, связанных с тегами команд.
    """
    
    @abstractmethod
    def show_tag_dialog(self, dialog_type: str, parent=None) -> Optional[str]:
        """Показать диалог тега"""
        pass
    
    @abstractmethod
    def get_supported_dialog_types(self) -> List[str]:
        """Получить поддерживаемые типы диалогов"""
        pass


class ISignalProcessor(ABC):
    """
    Интерфейс обработчика сигналов.
    
    Определяет контракт для обработки входящих сигналов UART,
    включая парсинг, валидацию и конвертацию данных.
    """
    
    @abstractmethod
    def process_signal(self, signal_name: str, value: str, signal_type: SignalType) -> SignalResult:
        """Обработать сигнал"""
        pass
    
    @abstractmethod
    def process_uart_data(self, data: str) -> List[SignalResult]:
        """Обработать данные UART"""
        pass
    
    @abstractmethod
    def validate_signal(self, signal_name: str, value: str, signal_type: SignalType) -> bool:
        """Валидировать сигнал"""
        pass
    
    @abstractmethod
    def convert_signal_value(self, value: str, signal_type: SignalType) -> Any:
        """Конвертировать значение сигнала"""
        pass


class ISignalValidator(ABC):
    """
    Интерфейс валидатора сигналов.
    
    Определяет контракт для валидации сигналов,
    включая проверку имен, типов и значений.
    """
    
    @abstractmethod
    def validate_signal_name(self, signal_name: str) -> bool:
        """Валидация имени сигнала"""
        pass
    
    @abstractmethod
    def validate_signal_type(self, signal_type: SignalType) -> bool:
        """Валидация типа сигнала"""
        pass
    
    @abstractmethod
    def validate_signal_value(self, value: Any, signal_type: SignalType) -> bool:
        """Валидация значения сигнала"""
        pass
    
    @abstractmethod
    def validate_signal_mapping(self, mapping: SignalMapping) -> bool:
        """Валидация маппинга сигнала"""
        pass
    
    @abstractmethod
    def validate_signal_config(self, config: Dict[str, str]) -> bool:
        """Валидация конфигурации сигналов"""
        pass


class ISignalManager(ABC):
    """
    Интерфейс менеджера сигналов.
    
    Определяет контракт для управления сигналами,
    включая регистрацию, обработку и мониторинг.
    """
    
    @abstractmethod
    def register_signal(self, signal_name: str, mapping: SignalMapping) -> bool:
        """Зарегистрировать сигнал"""
        pass
    
    @abstractmethod
    def unregister_signal(self, signal_name: str) -> bool:
        """Отменить регистрацию сигнала"""
        pass
    
    @abstractmethod
    def process_incoming_data(self, data: str) -> List[SignalResult]:
        """Обработать входящие данные"""
        pass
    
    @abstractmethod
    def get_signal_value(self, signal_name: str) -> Optional[SignalValue]:
        """Получить значение сигнала"""
        pass
    
    @abstractmethod
    def get_all_signal_values(self) -> Dict[str, SignalValue]:
        """Получить все значения сигналов"""
        pass
    
    @abstractmethod
    def get_signal_mappings(self) -> Dict[str, SignalMapping]:
        """Получить маппинги сигналов"""
        pass
    
    @abstractmethod
    def update_variable(self, variable_name: str, value: Any) -> bool:
        """Обновить переменную"""
        pass
    
    @abstractmethod
    def get_variable_value(self, variable_name: str) -> Optional[Any]:
        """Получить значение переменной"""
        pass
    
    @abstractmethod
    def get_all_variables(self) -> Dict[str, Any]:
        """Получить все переменные"""
        pass
