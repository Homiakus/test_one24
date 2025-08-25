# Справочник API и интерфейсов

## 1. Обзор API

### 1.1 Структура API
Система предоставляет несколько уровней API:
- **Core API**: Основные интерфейсы для работы с оборудованием
- **UI API**: Интерфейсы пользовательского интерфейса
- **Monitoring API**: API для мониторинга и диагностики
- **Configuration API**: API для работы с конфигурацией

### 1.2 Типы API
- **Synchronous**: Синхронные вызовы для простых операций
- **Asynchronous**: Асинхронные вызовы для длительных операций
- **Event-based**: Событийно-ориентированные API через сигналы Qt

## 2. Core API

### 2.1 ISerialManager Interface

#### 2.1.1 Основные методы

```python
class ISerialManager(ABC):
    @abstractmethod
    def connect(self, port: str, baudrate: int = 115200, 
                timeout: float = 1.0, **kwargs: Any) -> bool:
        """
        Подключение к последовательному порту.
        
        Args:
            port: Имя порта (например, 'COM4' или '/dev/ttyUSB0')
            baudrate: Скорость передачи данных в бодах (по умолчанию 115200)
            timeout: Таймаут чтения в секундах (по умолчанию 1.0)
            **kwargs: Дополнительные параметры подключения
            
        Returns:
            True если подключение успешно, False в противном случае
            
        Raises:
            SerialException: При ошибке подключения к порту
            ValueError: При некорректных параметрах
            
        Example:
            >>> serial_manager = SerialManager()
            >>> success = serial_manager.connect("COM4", 115200, 2.0)
            >>> if success:
            ...     print("Подключено к COM4")
        """
        pass
```

#### 2.1.2 Методы управления соединением

```python
    @abstractmethod
    def disconnect(self) -> None:
        """
        Отключение от порта.
        
        Закрывает активное соединение и освобождает ресурсы.
        Безопасно вызывается даже если соединение уже закрыто.
        
        Example:
            >>> serial_manager.disconnect()
            >>> print("Отключено от порта")
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Проверка состояния подключения.
        
        Returns:
            True если подключение активно, False в противном случае
            
        Example:
            >>> if serial_manager.is_connected():
            ...     print("Порт активен")
            ... else:
            ...     print("Порт неактивен")
        """
        pass
```

#### 2.1.3 Методы отправки команд

```python
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
            ConnectionError: При отсутствии активного соединения
            
        Example:
            >>> if serial_manager.send_command("sm 0 0 0 0 0"):
            ...     print("Команда отправлена")
            ... else:
            ...     print("Ошибка отправки команды")
        """
        pass
    
    @abstractmethod
    def send_command_with_response(self, command: str, 
                                 timeout: float = 5.0) -> Optional[str]:
        """
        Отправка команды с ожиданием ответа.
        
        Args:
            command: Команда для отправки
            timeout: Таймаут ожидания ответа в секундах
            
        Returns:
            Ответ от устройства или None при ошибке
            
        Example:
            >>> response = serial_manager.send_command_with_response("status")
            >>> if response:
            ...     print(f"Ответ: {response}")
            ... else:
            ...     print("Нет ответа")
        """
        pass
```

#### 2.1.4 Методы получения информации

```python
    @abstractmethod
    def get_available_ports(self) -> List[str]:
        """
        Получение списка доступных портов.
        
        Returns:
            Список имен доступных последовательных портов
            
        Example:
            >>> ports = serial_manager.get_available_ports()
            >>> print(f"Доступные порты: {ports}")
        """
        pass
    
    @abstractmethod
    def get_port_info(self) -> Dict[str, Any]:
        """
        Получение информации о текущем порте.
        
        Returns:
            Словарь с информацией о порте:
            - port: имя порта
            - baudrate: скорость передачи
            - bytesize: размер байта
            - parity: четность
            - stopbits: стоп-биты
            - timeout: таймаут
            - status: статус соединения
            
        Example:
            >>> info = serial_manager.get_port_info()
            >>> print(f"Порт: {info['port']}, Скорость: {info['baudrate']}")
        """
        pass
```

### 2.2 ISequenceManager Interface

#### 2.2.1 Основные методы

```python
class ISequenceManager(ABC):
    @abstractmethod
    def execute_sequence(self, sequence_name: str) -> bool:
        """
        Выполнение последовательности команд.
        
        Args:
            sequence_name: Имя последовательности из конфигурации
            
        Returns:
            True если последовательность запущена, False в противном случае
            
        Raises:
            ValueError: При неизвестном имени последовательности
            RuntimeError: При ошибке выполнения
            
        Example:
            >>> success = sequence_manager.execute_sequence("coloring")
            >>> if success:
            ...     print("Последовательность 'coloring' запущена")
        """
        pass
    
    @abstractmethod
    def stop_sequence(self) -> None:
        """
        Остановка текущей последовательности.
        
        Безопасно останавливает выполнение и освобождает ресурсы.
        
        Example:
            >>> sequence_manager.stop_sequence()
            >>> print("Последовательность остановлена")
        """
        pass
```

#### 2.2.2 Методы управления последовательностями

```python
    @abstractmethod
    def get_sequences(self) -> Dict[str, List[str]]:
        """
        Получение списка доступных последовательностей.
        
        Returns:
            Словарь {имя_последовательности: [команды]}
            
        Example:
            >>> sequences = sequence_manager.get_sequences()
            >>> for name, commands in sequences.items():
            ...     print(f"{name}: {len(commands)} команд")
        """
        pass
    
    @abstractmethod
    def create_executor(self, sequence_name: str) -> 'CommandSequenceExecutor':
        """
        Создание исполнителя последовательности.
        
        Args:
            sequence_name: Имя последовательности
            
        Returns:
            Экземпляр CommandSequenceExecutor
            
        Example:
            >>> executor = sequence_manager.create_executor("coloring")
            >>> executor.execute_async()
        """
        pass
```

### 2.3 ICommandExecutor Interface

#### 2.3.1 Основные методы

```python
class ICommandExecutor(ABC):
    @abstractmethod
    def execute_command(self, command: str) -> bool:
        """
        Выполнение одиночной команды.
        
        Args:
            command: Команда для выполнения
            
        Returns:
            True если команда выполнена успешно
            
        Example:
            >>> executor = CommandExecutor()
            >>> success = executor.execute_command("sm 0 0 0 0 0")
        """
        pass
    
    @abstractmethod
    def execute_sequence(self, commands: List[str]) -> bool:
        """
        Выполнение последовательности команд.
        
        Args:
            commands: Список команд для выполнения
            
        Returns:
            True если все команды выполнены успешно
            
        Example:
            >>> commands = ["sm 0 0 0 0 0", "wait 2", "status"]
            >>> success = executor.execute_sequence(commands)
        """
        pass
```

## 3. UI API

### 3.1 MainWindow Class

#### 3.1.1 Основные методы

```python
class MainWindow(QMainWindow):
    def __init__(self):
        """
        Инициализация главного окна приложения.
        
        Создает все необходимые менеджеры и настраивает UI.
        """
        super().__init__()
        # ... инициализация
        
    def show_page(self, page_name: str) -> None:
        """
        Переключение на указанную страницу.
        
        Args:
            page_name: Имя страницы для отображения
            
        Example:
            >>> main_window.show_page("settings")
        """
        pass
```

#### 3.1.2 Сигналы

```python
    # Сигналы для уведомлений
    sequence_started = Signal(str)  # Последовательность запущена
    sequence_completed = Signal(str)  # Последовательность завершена
    sequence_error = Signal(str, str)  # Ошибка в последовательности
    connection_status_changed = Signal(bool)  # Изменение статуса соединения
```

### 3.2 Страницы приложения

#### 3.2.1 WizardPage

```python
class WizardPage(QWidget):
    def __init__(self, step_config: Dict[str, Any]):
        """
        Страница мастера настройки.
        
        Args:
            step_config: Конфигурация шага мастера
        """
        super().__init__()
        
    def next_step(self) -> None:
        """Переход к следующему шагу."""
        pass
        
    def previous_step(self) -> None:
        """Переход к предыдущему шагу."""
        pass
```

#### 3.2.2 SettingsPage

```python
class SettingsPage(QWidget):
    def __init__(self):
        """Страница настроек приложения."""
        super().__init__()
        
    def save_settings(self) -> bool:
        """
        Сохранение настроек.
        
        Returns:
            True если настройки сохранены успешно
        """
        pass
        
    def load_settings(self) -> None:
        """Загрузка настроек из конфигурации."""
        pass
```

## 4. Monitoring API

### 4.1 IMonitoringManager Interface

```python
class IMonitoringManager(ABC):
    @abstractmethod
    def start_monitoring(self) -> None:
        """Запуск системы мониторинга."""
        pass
        
    @abstractmethod
    def stop_monitoring(self) -> None:
        """Остановка системы мониторинга."""
        pass
        
    @abstractmethod
    def get_system_health(self) -> Dict[str, Any]:
        """
        Получение состояния здоровья системы.
        
        Returns:
            Словарь с метриками здоровья системы
        """
        pass
```

### 4.2 HealthChecker

```python
class HealthChecker:
    def check_serial_connection(self) -> bool:
        """
        Проверка состояния Serial соединения.
        
        Returns:
            True если соединение здорово
        """
        pass
        
    def check_system_resources(self) -> Dict[str, Any]:
        """
        Проверка системных ресурсов.
        
        Returns:
            Словарь с метриками ресурсов
        """
        pass
```

### 4.3 PerformanceMonitor

```python
class PerformanceMonitor:
    def start_monitoring(self) -> None:
        """Запуск мониторинга производительности."""
        pass
        
    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Получение метрик производительности.
        
        Returns:
            Словарь с метриками производительности
        """
        pass
```

## 5. Configuration API

### 5.1 ConfigLoader

```python
class ConfigLoader:
    def __init__(self, config_path: Optional[str] = None):
        """
        Загрузчик конфигурации.
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        self.config_path = config_path or "config.toml"
        
    def load(self) -> Dict[str, Any]:
        """
        Загрузка конфигурации из файла.
        
        Returns:
            Словарь с конфигурацией
            
        Raises:
            FileNotFoundError: При отсутствии файла конфигурации
            ValueError: При ошибке парсинга TOML
        """
        pass
        
    def save(self, config: Dict[str, Any]) -> bool:
        """
        Сохранение конфигурации в файл.
        
        Args:
            config: Конфигурация для сохранения
            
        Returns:
            True если конфигурация сохранена успешно
        """
        pass
```

### 5.2 SettingsManager

```python
class SettingsManager:
    def __init__(self):
        """Менеджер настроек приложения."""
        self.settings = {}
        
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Получение значения настройки.
        
        Args:
            key: Ключ настройки
            default: Значение по умолчанию
            
        Returns:
            Значение настройки
        """
        pass
        
    def set_setting(self, key: str, value: Any) -> None:
        """
        Установка значения настройки.
        
        Args:
            key: Ключ настройки
            value: Значение настройки
        """
        pass
```

## 6. Error Handling API

### 6.1 ErrorHandler

```python
class ErrorHandler:
    def __init__(self):
        """Обработчик ошибок приложения."""
        self.logger = logging.getLogger(__name__)
        
    def handle_error(self, error: Exception, context: str = "") -> None:
        """
        Обработка ошибки.
        
        Args:
            error: Исключение для обработки
            context: Контекст возникновения ошибки
        """
        pass
        
    def graceful_shutdown(self, app: QApplication, message: str) -> None:
        """
        Graceful завершение приложения.
        
        Args:
            app: Экземпляр QApplication
            message: Сообщение о причине завершения
        """
        pass
```

## 7. Примеры использования API

### 7.1 Полный цикл работы с оборудованием

```python
from core.serial_manager import SerialManager
from core.sequence_manager import SequenceManager
from config.config_loader import ConfigLoader

def main():
    # Загрузка конфигурации
    config_loader = ConfigLoader()
    config = config_loader.load()
    
    # Инициализация менеджеров
    serial_manager = SerialManager()
    sequence_manager = SequenceManager(config.get('sequences', {}))
    
    try:
        # Подключение к оборудованию
        if serial_manager.connect("COM4", 115200):
            print("Подключено к оборудованию")
            
            # Выполнение последовательности
            if sequence_manager.execute_sequence("coloring"):
                print("Последовательность 'coloring' запущена")
                
                # Ожидание завершения
                executor = sequence_manager.create_executor("coloring")
                executor.wait_for_completion()
                print("Последовательность завершена")
            else:
                print("Ошибка запуска последовательности")
        else:
            print("Ошибка подключения к оборудованию")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        
    finally:
        # Отключение
        serial_manager.disconnect()
        print("Отключено от оборудования")

if __name__ == "__main__":
    main()
```

### 7.2 Асинхронное выполнение команд

```python
import asyncio
from core.serial_manager import SerialManager

async def async_command_execution():
    serial_manager = SerialManager()
    
    try:
        if serial_manager.connect("COM4"):
            # Асинхронная отправка команд
            commands = ["sm 0 0 0 0 0", "wait 2", "status"]
            
            for command in commands:
                if command.startswith("wait"):
                    # Ожидание
                    wait_time = int(command.split()[1])
                    await asyncio.sleep(wait_time)
                else:
                    # Отправка команды
                    success = serial_manager.send_command(command)
                    if not success:
                        print(f"Ошибка выполнения команды: {command}")
                        break
                        
            print("Все команды выполнены")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        
    finally:
        serial_manager.disconnect()

# Запуск асинхронной функции
asyncio.run(async_command_execution())
```

### 7.3 Мониторинг состояния системы

```python
from monitoring.monitoring_manager import MonitoringManager
import time

def monitor_system():
    monitoring_manager = MonitoringManager()
    monitoring_manager.start_monitoring()
    
    try:
        while True:
            # Получение метрик здоровья
            health = monitoring_manager.get_system_health()
            
            print(f"CPU: {health.get('cpu_usage', 0):.1f}%")
            print(f"Memory: {health.get('memory_usage', 0):.1f}%")
            print(f"Serial Status: {health.get('serial_status', 'Unknown')}")
            
            time.sleep(5)  # Обновление каждые 5 секунд
            
    except KeyboardInterrupt:
        print("Мониторинг остановлен")
        monitoring_manager.stop_monitoring()

if __name__ == "__main__":
    monitor_system()
```

## 8. Обработка ошибок

### 8.1 Типы ошибок

```python
class SerialConnectionError(Exception):
    """Ошибка подключения к Serial порту."""
    pass

class CommandExecutionError(Exception):
    """Ошибка выполнения команды."""
    pass

class SequenceExecutionError(Exception):
    """Ошибка выполнения последовательности."""
    pass

class ConfigurationError(Exception):
    """Ошибка конфигурации."""
    pass
```

### 8.2 Стратегии обработки

```python
def robust_command_execution(serial_manager, command, max_retries=3):
    """
    Надежное выполнение команды с повторными попытками.
    
    Args:
        serial_manager: Менеджер Serial соединения
        command: Команда для выполнения
        max_retries: Максимальное количество попыток
        
    Returns:
        True если команда выполнена успешно
    """
    for attempt in range(max_retries):
        try:
            if serial_manager.send_command(command):
                return True
            else:
                print(f"Попытка {attempt + 1} неудачна")
                
        except Exception as e:
            print(f"Ошибка в попытке {attempt + 1}: {e}")
            
        if attempt < max_retries - 1:
            time.sleep(1)  # Пауза перед повторной попыткой
            
    return False
```

---

**Документ**: Справочник API и интерфейсов  
**Версия**: 1.0.0  
**Дата**: 2024  
**Статус**: Утверждено

