# Улучшения обработки ошибок

## Обзор

В приложение добавлена комплексная система обработки ошибок, которая обеспечивает:

1. **Graceful shutdown** при критических ошибках
2. **Обработку import ошибок** qt_material с fallback
3. **Proper exception handling** во всех критичных местах
4. **Централизованную обработку ошибок** через ErrorHandler
5. **Улучшенное логирование** с обработкой ошибок

## Основные компоненты

### 1. main.py

#### Обработка import ошибок qt_material
```python
# Проверка qt_material с graceful fallback
qt_material_available = False
try:
    from qt_material import apply_stylesheet
    qt_material_available = True
except ImportError as e:
    print(f"Предупреждение: qt_material недоступен: {e}")
    print("Будет использована стандартная тема Qt")
```

#### Graceful shutdown при критических ошибках
```python
def graceful_shutdown(app: Optional[QApplication] = None, error_msg: str = None):
    """Graceful shutdown приложения с обработкой ошибок"""
    if error_msg:
        error_handler.handle_critical_error(Exception(error_msg), "Graceful shutdown")
    
    logging.info("Завершение работы приложения")
    
    if app and app.instance():
        try:
            app.quit()
        except Exception as e:
            logging.error(f"Ошибка при завершении Qt приложения: {e}")
    
    sys.exit(1)
```

#### Proper exception handling в apply_theme
```python
def apply_theme(app: QApplication, theme: str = "dark") -> bool:
    """Применение темы с улучшенной обработкой ошибок"""
    if not qt_material_available:
        logging.warning("qt_material недоступен, используется стандартная тема")
        try:
            app.setStyle('Fusion')
            return True
        except Exception as e:
            logging.error(f"Не удалось применить стандартную тему: {e}")
            return False
    
    # ... применение темы с обработкой ошибок
```

### 2. utils/error_handler.py

#### ErrorHandler класс
Централизованный обработчик ошибок с возможностью регистрации callback'ов:

```python
class ErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._error_callbacks = []
        self._critical_error_callbacks = []
    
    def handle_error(self, error: Exception, context: str = "", show_dialog: bool = True):
        """Обработка обычной ошибки"""
        
    def handle_critical_error(self, error: Exception, context: str = ""):
        """Обработка критической ошибки"""
```

#### Утилиты для безопасного выполнения
```python
def safe_execute(func: Callable, *args, error_context: str = "", 
                show_dialog: bool = True, default_return: Any = None, **kwargs):
    """Безопасное выполнение функции с обработкой ошибок"""

def critical_safe_execute(func: Callable, *args, error_context: str = "", **kwargs):
    """Безопасное выполнение критической функции с обработкой ошибок"""
```

#### Декораторы для автоматической обработки ошибок
```python
@error_handler_decorator(error_context="Операция с файлом", show_dialog=True)
def read_file(file_path: str):
    """Функция с автоматической обработкой ошибок"""

@critical_error_handler_decorator(error_context="Критическая операция")
def critical_operation():
    """Критическая функция с автоматической обработкой ошибок"""
```

### 3. utils/logger.py

#### Улучшенная настройка логирования
```python
def setup_logging(log_dir: str = None) -> bool:
    """Настройка системы логирования с обработкой ошибок"""
    try:
        # Создание директории с обработкой ошибок
        if not safe_create_directory(log_dir):
            print("Не удалось создать директорию для логов, используем текущую директорию")
            log_dir = Path.cwd()
        
        # Обработчик для файла с обработкой ошибок
        try:
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            # ...
        except PermissionError as e:
            print(f"Ошибка прав доступа при создании файла лога {log_file}: {e}")
        except OSError as e:
            print(f"Ошибка ОС при создании файла лога {log_file}: {e}")
```

## Типы обрабатываемых ошибок

### 1. ImportError
- **qt_material**: Graceful fallback на стандартную тему Qt
- **PySide6**: Критическая ошибка с информативным сообщением
- **Модули приложения**: Проверка всех критических зависимостей

### 2. PermissionError
- Создание директорий для логов
- Запись в файлы логов
- Операции с файлами

### 3. FileNotFoundError
- Отсутствующие файлы конфигурации
- Файлы логов

### 4. OSError
- Системные ошибки при работе с файлами
- Проблемы с сетью/портами

### 5. KeyboardInterrupt
- Graceful shutdown при Ctrl+C
- Корректное завершение Qt приложения

## Использование в коде

### Базовое использование ErrorHandler
```python
from utils.error_handler import error_handler

try:
    # Код, который может вызвать ошибку
    risky_operation()
except Exception as e:
    error_handler.handle_error(e, "Операция с устройством")
```

### Использование декораторов
```python
from utils.error_handler import error_handler_decorator

@error_handler_decorator(error_context="Сохранение настроек", show_dialog=True)
def save_settings(settings: dict):
    # Функция автоматически обрабатывает ошибки
    with open('settings.json', 'w') as f:
        json.dump(settings, f)
```

### Регистрация callback'ов
```python
def custom_error_handler(error: Exception, context: str):
    # Пользовательская обработка ошибок
    send_error_report(error, context)

error_handler.register_error_callback(custom_error_handler)
```

## Логирование ошибок

Все ошибки логируются с полной информацией:

```python
logging.error(f"Ошибка применения темы '{theme}': {e}")
logging.critical(error_msg, exc_info=True)  # С полным стеком вызовов
```

## Диалоги ошибок

При критических ошибках показываются информативные диалоги:

- **Обычные ошибки**: Warning иконка, кнопка OK
- **Критические ошибки**: Critical иконка, кнопка OK
- **Fallback**: Вывод в консоль при недоступности Qt

## Преимущества

1. **Надежность**: Приложение не падает при отсутствии qt_material
2. **Информативность**: Пользователь получает понятные сообщения об ошибках
3. **Логирование**: Все ошибки записываются в лог-файлы
4. **Graceful shutdown**: Корректное завершение при критических ошибках
5. **Централизация**: Единая точка обработки ошибок
6. **Расширяемость**: Возможность добавления пользовательских обработчиков

## Рекомендации по использованию

1. **Всегда используйте ErrorHandler** для критических операций
2. **Логируйте ошибки** с контекстом для отладки
3. **Предоставляйте fallback** для необязательных компонентов
4. **Тестируйте обработку ошибок** в различных сценариях
5. **Документируйте** специфичные для приложения ошибки

