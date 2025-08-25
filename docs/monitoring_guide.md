# Руководство по системе мониторинга

## Обзор

Система мониторинга предоставляет комплексное решение для отслеживания работы приложения в production. Она включает в себя 4 основных компонента:

1. **PerformanceMonitor** - мониторинг производительности
2. **ErrorAlerter** - система уведомлений об ошибках
3. **HealthChecker** - проверка состояния системы
4. **UsageMetrics** - статистика использования

## Архитектура

```
MonitoringManager
├── PerformanceMonitor
│   ├── Системные метрики (CPU, память)
│   ├── Производительность команд
│   └── Время отклика UI
├── ErrorAlerter
│   ├── Уровни важности (INFO, WARNING, ERROR, CRITICAL)
│   ├── Эскалация уведомлений
│   └── Email уведомления
├── HealthChecker
│   ├── Проверка Serial соединения
│   ├── Системные ресурсы
│   └── Пользовательские проверки
└── UsageMetrics
    ├── Сессии пользователей
    ├── Статистика команд
    └── Аналитика использования
```

## Быстрый старт

### 1. Инициализация

```python
from monitoring import MonitoringManager
from utils.logger import Logger

# Создаем менеджер мониторинга
logger = Logger(__name__)
monitoring_manager = MonitoringManager(logger)

# Устанавливаем сервисы (если есть)
monitoring_manager.set_services(serial_manager, command_executor)

# Запускаем мониторинг
monitoring_manager.start_monitoring()
```

### 2. Запись событий

```python
# Запись выполнения команды
monitoring_manager.record_command_execution(
    command="move 10 0 0 0 0",
    execution_time=1.5,
    success=True
)

# Запись посещения страницы
monitoring_manager.record_page_visit("commands_page", duration=30.0)

# Запись выполнения последовательности
monitoring_manager.record_sequence_execution(
    sequence_name="coloring",
    success=True,
    duration=300.0
)
```

### 3. Отправка уведомлений

```python
from monitoring import AlertLevel

# Информационное уведомление
monitoring_manager.send_alert(
    level=AlertLevel.INFO,
    message="Пользователь зашел в систему",
    source="auth_system"
)

# Предупреждение
monitoring_manager.send_alert(
    level=AlertLevel.WARNING,
    message="Высокое использование CPU",
    source="performance_monitor",
    details={"cpu_percent": 85.0}
)

# Критическая ошибка
monitoring_manager.send_alert(
    level=AlertLevel.CRITICAL,
    message="Потеря соединения с устройством",
    source="serial_manager",
    details={"port": "COM4", "error": "Connection lost"}
)
```

## Компоненты системы

### PerformanceMonitor

Отслеживает производительность системы и приложения.

#### Основные возможности:
- Мониторинг CPU и использования памяти
- Время выполнения команд
- Время отклика UI
- Автоматический сбор метрик каждые 5 секунд

#### Использование:

```python
# Получение сводки системных метрик
summary = monitoring_manager.performance_monitor.get_system_metrics_summary(minutes=5)

# Получение производительности команд
command_summary = monitoring_manager.performance_monitor.get_command_performance_summary(minutes=5)

# Получение времени работы
uptime = monitoring_manager.performance_monitor.get_uptime()
```

### ErrorAlerter

Система уведомлений с поддержкой уровней важности и эскалации.

#### Уровни важности:
- **INFO** - информационные сообщения
- **WARNING** - предупреждения
- **ERROR** - ошибки
- **CRITICAL** - критические ошибки

#### Настройка email уведомлений:

```python
monitoring_manager.configure_email_alerts(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your_email@gmail.com",
    password="your_password",
    recipients=["admin@company.com", "support@company.com"]
)
```

#### Настройка эскалации:

```python
# Эскалация при превышении 5 ошибок в час
monitoring_manager.error_alerter.set_escalation_rule(
    AlertLevel.ERROR,
    {"max_alerts_per_hour": 5}
)
```

#### Подавление повторяющихся уведомлений:

```python
from datetime import timedelta

# Подавлять одинаковые уведомления на 1 час
monitoring_manager.error_alerter.set_suppression_rule(
    "Connection lost",
    timedelta(hours=1)
)
```

### HealthChecker

Проверяет состояние системы и компонентов.

#### Встроенные проверки:
- Системные ресурсы (CPU, память, диск)
- Сетевое соединение
- Serial соединение
- Исполнитель команд

#### Добавление пользовательских проверок:

```python
def custom_database_check():
    from monitoring.health_checker import HealthCheck, HealthStatus
    
    try:
        # Проверка базы данных
        # db.check_connection()
        return HealthCheck(
            name="database_connection",
            status=HealthStatus.HEALTHY,
            message="Database connection OK",
            timestamp=datetime.now()
        )
    except Exception as e:
        return HealthCheck(
            name="database_connection",
            status=HealthStatus.CRITICAL,
            message=f"Database connection failed: {e}",
            timestamp=datetime.now()
        )

monitoring_manager.health_checker.add_custom_check(
    "database",
    custom_database_check
)
```

#### Получение состояния:

```python
# Текущее состояние
current_health = monitoring_manager.health_checker.get_current_health()

# Сводка за период
health_summary = monitoring_manager.health_checker.get_health_summary(hours=24)
```

### UsageMetrics

Отслеживает использование приложения и аналитику.

#### Сессии пользователей:

```python
# Начало сессии
session_id = monitoring_manager.start_user_session("user123")

# Завершение сессии
monitoring_manager.end_user_session(session_id)
```

#### Аналитика:

```python
# Сводка использования
usage_summary = monitoring_manager.usage_metrics.get_usage_summary(hours=24)

# Анализ команд
command_analysis = monitoring_manager.usage_metrics.get_command_usage_analysis(days=7)

# Анализ сессий
session_analysis = monitoring_manager.usage_metrics.get_session_analysis(days=7)

# Анализ ошибок
error_analysis = monitoring_manager.usage_metrics.get_error_analysis(days=7)
```

## UI интерфейс

### Запуск страницы мониторинга:

```python
from ui.pages.monitoring_page import MonitoringPage

# Создание страницы
monitoring_page = MonitoringPage(monitoring_manager)
monitoring_page.show()
```

### Возможности UI:
- **Вкладка "Производительность"**: Системные метрики и производительность команд
- **Вкладка "Уведомления"**: Активные уведомления и их статус
- **Вкладка "Состояние"**: Результаты health checks
- **Вкладка "Использование"**: Статистика использования и популярные страницы

## Экспорт данных

### Автоматический экспорт:
- Происходит каждые 24 часа
- Сохраняется в `logs/monitoring/`
- Формат: JSON
- Автоматическая очистка старых файлов

### Ручной экспорт:

```python
# Экспорт всех данных
monitoring_manager.export_all_data()

# Получение данных для экспорта
export_data = monitoring_manager.performance_monitor.get_metrics_export()
```

## Конфигурация

### Настройка параметров:

```python
config = {
    "export_interval_hours": 12,  # Экспорт каждые 12 часов
    "retention_days": 14,         # Хранить данные 14 дней
    "performance_monitor": {
        "system_monitor_interval": 10.0,  # Обновление каждые 10 секунд
        "max_metrics_history": 5000       # Максимум 5000 метрик
    },
    "health_checker": {
        "check_interval": 60.0,           # Проверки каждую минуту
        "max_health_history": 1000        # Максимум 1000 записей
    }
}

monitoring_manager.set_monitoring_config(config)
```

### Получение текущей конфигурации:

```python
current_config = monitoring_manager.get_monitoring_config()
```

## Очистка данных

### Автоматическая очистка:
- Происходит при экспорте
- Удаляет данные старше retention_days

### Ручная очистка:

```python
# Очистка данных старше 7 дней
monitoring_manager.cleanup_old_data(days=7)
```

## Интеграция с существующим кодом

### В CommandExecutor:

```python
class CommandExecutor:
    def __init__(self, monitoring_manager):
        self.monitoring_manager = monitoring_manager
    
    def execute_command(self, command):
        start_time = time.time()
        try:
            result = self._send_command(command)
            execution_time = time.time() - start_time
            
            # Записываем в мониторинг
            self.monitoring_manager.record_command_execution(
                command, execution_time, True
            )
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Записываем ошибку
            self.monitoring_manager.record_command_execution(
                command, execution_time, False, str(e)
            )
            raise
```

### В UI страницах:

```python
class SomePage(BasePage):
    def __init__(self, monitoring_manager):
        super().__init__()
        self.monitoring_manager = monitoring_manager
        self.page_start_time = time.time()
    
    def closeEvent(self, event):
        # Записываем время посещения страницы
        duration = time.time() - self.page_start_time
        self.monitoring_manager.record_page_visit(
            "some_page", duration
        )
        super().closeEvent(event)
```

## Лучшие практики

### 1. Правильное использование уровней уведомлений:
- **INFO**: Обычные события (вход пользователя, успешные операции)
- **WARNING**: Потенциальные проблемы (высокое использование ресурсов)
- **ERROR**: Ошибки, которые не критичны (ошибки команд)
- **CRITICAL**: Критические ошибки (потеря соединения, сбои системы)

### 2. Настройка эскалации:
- Не настраивайте слишком низкие лимиты
- Используйте подавление для повторяющихся уведомлений
- Настройте email уведомления для критических ошибок

### 3. Мониторинг производительности:
- Регулярно проверяйте сводки производительности
- Обращайте внимание на команды с низкой успешностью
- Мониторьте использование системных ресурсов

### 4. Анализ использования:
- Используйте аналитику для понимания популярных функций
- Отслеживайте паттерны использования
- Анализируйте ошибки для улучшения UX

## Устранение неполадок

### Проблемы с производительностью:
1. Проверьте интервалы обновления метрик
2. Уменьшите размер истории данных
3. Настройте очистку старых данных

### Проблемы с уведомлениями:
1. Проверьте настройки SMTP
2. Убедитесь в правильности уровней важности
3. Проверьте правила подавления

### Проблемы с health checks:
1. Добавьте пользовательские проверки для проблемных компонентов
2. Настройте пороги для критических метрик
3. Проверьте доступность сервисов

## Заключение

Система мониторинга предоставляет мощные инструменты для отслеживания работы приложения в production. Правильное использование всех компонентов поможет обеспечить стабильную работу системы и быстрое реагирование на проблемы.

